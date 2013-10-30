#from handlers.base import AppHandler
import csv
import os
from main import root_dir
from google.appengine.ext import db
import datetime
from handlers.signup import SignupHandler


class Play(SignupHandler):
	def get(self):
		self.render('play.html',user=self.user)
	def picks(self):
		if self.user:
			week=current_week(self)
			game_dir = os.path.join(root_dir, 'Schedules', 'week'+str(week)+'.txt')
			f = open(game_dir)
			f_list = csv.reader(f)
			games=[]
			for row in f_list:
				#self.write(row)
				if row[0] <> "Home":
					games.append(row)
			f.close()
			#this should also filter on week!
			picks = picked_this_week(self,week)
			if picks:
				message="You already made picks this week"
				current_picks = picks.picks
			else:
				message=None
				current_picks=[]
			if self.request.get('failed'):
				message="Complete picks and try again"
			self.render('play_picks.html',games=games,user=self.user,message=message,picks=current_picks)
		else:
			self.redirect_to('login',source='picks')
def current_week(self):
	#loop over dates.txt file and pick the current week
	#NEEDTO - localize this time (might be using GMT)
	today=datetime.date.today()
	date_file = os.path.join(root_dir, 'Schedules', 'dates.txt')
	f = open(date_file)
	f_list = csv.reader(f)
	week=[]
	for row in f_list:
		if row[0] == "Week":
			continue
		end_date_raw = row[2].split("/")
		end_date = datetime.date(int(end_date_raw[2]), int(end_date_raw[0]), int(end_date_raw[1]))
		if end_date > today:
			f.close()
			return row[0]
def picked_this_week(self,week):
	uid = float(self.user.key().id())
	return UserPicks.all().filter('user_id =', uid).filter('week =',week).get()
class PickHandler(Play):
	def post(self):
		if not self.user:
			self.redirect_to('login',source='picks')
		else:
			week = current_week(self)	
			picks = picked_this_week(self,week)
			if picks:
				if self.add_new_picks(week):
					picks.delete()
			else:
				#First time user is making picks
				self.add_new_picks(week)
				
	def add_new_picks(self,week):
		game_dir = os.path.join(root_dir, 'Schedules', 'week'+str(week)+'.txt')
		f = open(game_dir)
		f_list = csv.reader(f)
		picks=[]
		count=1
		failed = 0
		for row in f_list:
			if row[0] <> "Home":
				pick = self.request.get(str(count))
				if not pick:
					#handle this error better. Don't submit it without a warning.
					failed = 1
				else:
					pick = int(pick)
					#self.write("You picked " + row[pick-1] + " over " + row[pick % 2])
					picks.append(pick)
				count+=1
		tiebreak = self.request.get('tiebreak')
		#do some validation here to make sure it's a number
		if tiebreak:
			picks.append(int(tiebreak))
		else:
			failed = 1
		f.close()
		# Store picks
		if not failed:
			up = UserPicks(user_id=float(self.user.key().id()),
							picks = picks,
							week = week,
							username = self.user.username)
			up.put()
			self.redirect_to('results')
			return 1
		else:
			self.redirect_to('play',failed=1)
			return 0
class UserPicks(db.Model):
	#Change this to Long/Float
	user_id = db.FloatProperty(required = True)
	picks = db.ListProperty(required = True, item_type=int)
	created = db.DateTimeProperty(auto_now_add = True)
	#update to appropriate integer property
	week = db.StringProperty(required = True)
	username = db.StringProperty(required = True)

class AdminHandler(SignupHandler):
	#use this to make sure the files load in correctly
	def testFiles(self):
		self.render('admin.html')
class Results(SignupHandler):
	def get(self):
		if not self.user:
			self.redirect_to('login',source='picks')
		else:
			week=current_week(self)
			picks = UserPicks.all().filter('week =',week).run()
			#just added this so we don't run the db query again. test it out
			picks = list(picks)
			self.render('play_results.html',picks_list=picks,user=self.user)