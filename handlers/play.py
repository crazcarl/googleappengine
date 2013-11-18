#from handlers.base import AppHandler
import csv
import os
from main import root_dir
from google.appengine.ext import db
import datetime
from handlers.signup import SignupHandler
from google.appengine.api import memcache
from handlers.signup import User
from pytz.gae import pytz

class Play(SignupHandler):
	def get(self):
		self.render('play.html',user=self.user)
	def picks(self):
		if not self.user:
			self.redirect_to('login',source='picks')
			return None
		week = int(current_week(self))
		if not week or week==0:
			self.redirect_to('play')
			return None
		#this tag needs improvement
		picks = picked_this_week(self,week)
		if picks:
			message="You already made picks this week"
			current_picks = picks.picks
		else:
			message=None
			current_picks=[]
		sched = get_sched(self,week)
		if self.request.get('failed'):
			message="Complete picks and try again"
		if sched:
			arizona = pytz.timezone('US/Arizona')
			time = datetime.datetime.now(arizona)
			self.render('play_picks.html',games=sched,user=self.user,message=message,picks=current_picks,time=time,week=week)
		else:
			self.render('play.html',user=self.user)
def current_week(self,update = False):
	# we'll first get the current day
	today=datetime.date.today()
	# 1. check the weeks cache if update is False. If there, return current week
	if memcache.get("weeks") and not update:
		#loop over cache and find week
		weeks = memcache.get("weeks")
	else:
		# 2. else, hit the DB.
		weeks = db.GqlQuery("Select * from Weeks")
		if weeks:
			weeks = list(weeks)
			memcache.set("weeks",weeks)
	if weeks:
		for i in weeks:
			if i.end > today and i.start <= today:
				return i.week
	return 0

def get_sched(self,week):
	if not week:
		return None
	sched = memcache.get("week"+str(week))
	if not sched:
		sched = Schedule.all().filter("week =",int(week)).fetch(20)
		if sched:
			memcache.set("week"+str(week),sched)
	return sched
def picked_this_week(self,week):
	picks = memcache.get(str(self.user.username)+"week"+str(week))
	if not picks:
		uid = float(self.user.key().id())
		picks = UserPicks.all().filter('user_id =', uid).filter('week =',week).get()
	if picks:
		memcache.set(str(self.user.username)+"week"+str(week),picks)
	return picks
class PickHandler(Play):
	def post(self):
		if not self.user:
			self.redirect_to('login',source='picks')
			return None
		week = current_week(self)	
		picks = picked_this_week(self,week)
		if picks:
			if self.add_new_picks(week):
				picks.delete()
		else:
			#First time user is making picks
			self.add_new_picks(week)
				
	def add_new_picks(self,week):
		picks = []
		count = 1
		failed = 0
		sched = get_sched(self,current_week(self))
		for row in sched:
			pick = self.request.get(str(count))
			if not pick:
				#handle this error better. Don't submit it without a warning.
				failed = 1
			else:
				picks.append(pick)
			count+=1
		tiebreak = self.request.get('tiebreak')
		#do some validation here to make sure it's a number
		if tiebreak:
			picks.append(str(tiebreak))
		else:
			failed = 1
		# Store picks
		if not failed:
			up = UserPicks(user_id=float(self.user.key().id()),
							picks = picks,
							week = week,
							username = self.user.username)
			up.put()
			memcache.set(str(self.user.username)+"week"+str(week),up)
			self.redirect_to('results')
			return 1
		else:
			self.redirect_to('play',failed=1)
			return 0
class UserPicks(db.Model):
	#Change this to Long/Float
	user_id = db.FloatProperty(required = True)
	picks = db.ListProperty(required = True, item_type=str)
	created = db.DateTimeProperty(auto_now_add = True)
	week = db.IntegerProperty(required = True)
	username = db.StringProperty(required = True)

class AdminHandler(SignupHandler):
	def get(self):
		admin = 0
		cur_week = current_week(self)
		if self.user:
			admin = self.user.admin
		if not admin:
			self.redirect_to('play')
			return None
		else:
			self.render('admin.html',user=self.user,message="the current week is " + str(cur_week))
	#use this to make sure the files load in correctly
	def testFiles(self):
		self.render('admin.html')
	def loadFile(self):
		pass
	def post(self):
		#handles admin tasks
		type=self.request.get('type')
		if type=="loaddates":
			#Hit DB to look for weeks, if so delete
			weeks = Weeks.all().fetch(25)
			if weeks:
				for w in weeks:
					w.delete()
			#(Re)load
			dates=self.request.get('dates')
			dates = dates.splitlines()
			wk_cache = []
			for date in dates:
				date = date.split(",")
				# need to: also handle blank lines here
				if date[0] == "Week":
					continue
				week = int(date[0])
				start_date = date[1].split("/")
				start = datetime.date(int(start_date[2]),int(start_date[0]),int(start_date[1]))
				end_date = date[2].split("/")
				end = datetime.date(int(end_date[2]),int(end_date[0]),int(end_date[1]))
				weeks = Weeks(week=week,start=start,end=end)
				weeks.put()
				wk_cache.append(weeks)
			memcache.set("weeks",wk_cache)
			self.render('admin.html',message="Date file loaded",user=self.user)
		elif type=="loadweek":
			#determine current week
			cur_week = current_week(self)
			if not cur_week or cur_week == 0:
				self.redirect_to('admin')
			#
			week = self.request.get('week')
			week = week.splitlines()
			cur_sched = Schedule.all().filter("week =",int(cur_week)).fetch(100)
			for cs in cur_sched:
				cs.delete()
			sched_cache = []
			for game in week:
				game = game.split(",")
				if game[0] == "Home":
					continue
				home_team = game[0]
				away_team = game[1]
				line = float(game[2])
				if len(game) > 3:
					special = game[3]
				else:
					special = ""
				schedule = Schedule(week=cur_week,home_team=home_team,away_team=away_team,line=line,special=special)
				schedule.put()
				sched_cache.append(schedule)
			memcache.set('week'+str(cur_week),sched_cache)
			self.render('admin.html',message="week file loaded",user=self.user)
class Schedule(db.Model):
	week = db.IntegerProperty(required = True)
	home_team = db.StringProperty(required = True)
	away_team = db.StringProperty(required = True)
	line = db.FloatProperty(required = True)
	special = db.StringProperty()
class Weeks(db.Model):
	week = db.IntegerProperty(required = True)
	start = db.DateProperty(required = True)
	end = db.DateProperty(required = True)
	
class ResultsHandler(SignupHandler):
	def get(self):
		if not self.user:
			self.redirect_to('login',source='picks')
			return None
		week=current_week(self)
		picks_list = []
		no_picks_list = []
		users = User.all().fetch(1000)
		for user in users:
			picks=memcache.get(user.username+"week"+str(week))
			if not picks:
				picks = UserPicks.all().filter('user_id =', float(user.key().id())).filter('week =',week).get()
				if picks:
					memcache.set(user.username+"week"+str(week),picks)
				else:
					no_picks_list.append(user)
			if picks:
				picks_list.append(picks)
		self.display_results(picks_list,no_picks_list,week)
	def display_results(self,picks,nopicks,week):
		#get teams array
		schedule = Schedule.all().filter("week =",week).fetch(20)
		schedule = list(schedule)
		games = {}
		i = 1
		#on results.html, build hash table for results
		for s in schedule:
			games[i] = {}
			ht=s.home_team
			at=s.away_team
			games[i][ht] = []
			games[i][at] = []
			for p in picks:
				if ht in p.picks:
					user=User.by_id(int(p.user_id))
					games[i][ht].append(user.username)
				elif at in p.picks:
					user=User.by_id(int(p.user_id))
					games[i][at].append(user.username)
			games[i][at] = ', '.join([un for un in games[i][at]])
			games[i][ht] = ', '.join([un for un in games[i][ht]])
			i += 1
		self.render('play_results.html',results=games,user=self.user,no_picks_list=nopicks)
class StandingsHandler(SignupHandler):
	def get(self):
		week = current_week(self)
		results = []
		if not self.user:
			self.redirect_to('play')
			return None
		for w in range(1,week):
			results.append(week)
			r = len(results)-1
			#see if the results are in memcache
			results[r] = memcache.get("week"+str(w)+"results")
			#if not, see if the results are in the DB
			if not results[r]:
				results[r] = Results.all().filter("week =",week).get()
				if results:
					memcache.set("week"+str(w)+"results",results[r])
			#if not, calculate the results
			if not results[r]:
				results[r] = self.calc_results(w)
			if not results[r]:
				#something went wrooonng!
				return None
		self.render('play_standings.html',results=results,user=self.user)
	def calc_results(self,week):
		#for each user, calculate the number of wins and losses.
		users = User.all().fetch(1000)
		users = list(users)
		winner = User.by_name("winner")
		w_picks = UserPicks.all().filter('user_id =', float(winner.key().id())).filter('week =',week).get()
		if not w_picks:
			return None
		#get the number of games in the week for no picks case
		games = len(w_picks.picks)
		results = {}
		for u in users:
			if u.username == "winner":
				continue
			picks = memcache.get(str(u.username)+"week"+str(week))
			if not picks:
				picks = UserPicks.all().filter('user_id =',float(u.key().id())).filter('week =',week).get()
			if picks:
				(wins,losses) = self.compare_picks(w_picks.picks,picks.picks)
			else:
				#handle for no picks case
				wins = 0
				losses = games
			results[u.username] = (wins,losses)
		#cache results
		return results
	def compare_picks(self,winner_picks,player_picks):
		(wins,losses) = 0,0
		for pick in player_picks:
			if pick in winner_picks:
				wins += 1
			else:
				losses += 1
		return (wins,losses)
class Results(db.Model):
	week = db.IntegerProperty(required = True)
	user_id = db.FloatProperty(required = True)
	wins = db.IntegerProperty(required = True)
	losses = db.IntegerProperty(required = True)
	#need tb in case two people tie and need to determine by mnf score
	#will do this manually for now
	tb = db.IntegerProperty(default = 0)