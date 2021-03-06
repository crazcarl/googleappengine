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
from google.appengine.api import mail


ARIZONA = pytz.timezone('US/Arizona')

class Play(SignupHandler):
	def get(self):
		self.render('play.html',user=self.user)
	def picks(self):
		if not self.user:
			self.redirect_to('login',source='picks')
			return None
		week = current_week(self)
		if not week or week==0:
			self.redirect_to('play')
			return None
			
		# See if user already picked this week
		picks = picked_this_week(self,week)
		if picks:
			message="You already made picks this week"
			current_picks = picks.picks
		else:
			message=None
			current_picks=[]
		
		# get current schedule
		sched = get_sched(self,week)
		if self.request.get('failed'):
			message="Complete picks and try again"
		if not sched:
			message ="No schedule loaded for this week, yet"
		
		# see if picks are valid this week
		cur_time = datetime.datetime.now(ARIZONA)
		cutoff_date = current_week(self,return_val=1)
		view_only = 0#picks_enabled(self,cutoff_date)
		
		self.render('play_picks.html',games=sched,user=self.user,message=message,picks=current_picks,time=cur_time,week=week,cutoff=cutoff_date,vo=view_only)
		

# returns: 0 - picks are enabled (before 7pm on the cutoff date passed in)
#		   1 - picks are disabled (after 7pm)
def picks_enabled(self,cutoff_date):
		today = datetime.datetime.now(ARIZONA)
		# first check day
		if today.date() < cutoff_date:
			return 0
		elif today == cutoff_date:
			# then check time
			cutoff = datetime.datetime(cutoff_date.year,cutoff_date.month,cutoff_date.day,7,0,0,tzinfo=ARIZONA)
			if today < cutoff:
				return 0
			else:
				return 1
		else:
			return 1

#return_val: 0 - returns current week (integer)
#			 1 - returns picks cutoff day for current week
def current_week(self,update = False,return_val = 0):
	# we'll first get the current day
	today2 = datetime.datetime.now(ARIZONA)
	y = today2.year
	m = today2.month
	d = today2.day
	today = datetime.date(y,m,d)
	
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
	
	# Compare current day to weeks list
	if weeks:
		for i in weeks:
			if i.end >= today and i.start <= today:
				if return_val == 0:
					return i.week
				elif return_val == 1:
					return i.cutoff
	return 0

#Grabs  schedule based on week parameter (required).
def get_sched(self,week):
	if not week:
		return None
	sched = memcache.get("week"+str(week))
	if not sched:
		sched = Schedule.all().filter("week =",int(week)).fetch(20)
		if sched:
			memcache.set("week"+str(week),sched)
	return sched

#Determine if user has picked this week to display results in play/picks
def picked_this_week(self,week):
	picks = memcache.get(str(self.user.username)+"week"+str(week))
	if not picks:
		uid = float(self.user.key().id())
		picks = UserPicks.all().filter('user_id =', uid).filter('week =',week).get()
	if picks:
		memcache.set(str(self.user.username)+"week"+str(week),picks)
	return picks

#Handles submission of picks.
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
		
		# Can I just get the count of how many games there are instead of the full schedule?
		sched = get_sched(self,current_week(self))
		
		# Get the picks
		for row in sched:
			pick = self.request.get(str(count))
			if not pick:
				#handle this error better. Don't submit it without a warning.
				failed = 1
			else:
				picks.append(pick)
			count+=1
		
		# get the tiebreak
		tiebreak = self.request.get('tiebreak')
		#do some validation here to make sure it's a number
		try:
			tiebreak = int(tiebreak) + 0
		except ValueError:
			tiebreak = 0
		picks.append(str(tiebreak))
		
		# Store picks
		if not failed:
			up = UserPicks(user_id=float(self.user.key().id()),
							picks = picks,
							week = week,
							username = self.user.username)
			up.put()
			if self.user.username == "winner":
				calc_results(self,week,up)
			memcache.set(str(self.user.username)+"week"+str(week),up)
			self.redirect_to('results')
			####TESTING EMAIL
			#self.emailPicks(up)
			######
			return 1
		else:
			self.redirect_to('play',failed=1)
			return 0
		
	def emailPicks(self,user_picks):
		mail.send_mail(sender="Pick Em <crazcarl@gmail.com>",
              to=self.user.email,
              subject="Picks",
              body="Thanks for submitting your picks!")
			  
#Manually set the admin flag to 1 for a user to make them an admin and have access to this menu.
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
	def post(self):
		if not self.user.admin:
			self.redirect_to('play')
			return None
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
				cutoff_date = date[3].split("/")
				cutoff = datetime.date(int(cutoff_date[2]),int(cutoff_date[0]),int(cutoff_date[1]))
				weeks = Weeks(week=week,start=start,end=end,cutoff=cutoff)
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

# Handles Results (showing who picked each team for each game)
class ResultsHandler(SignupHandler):
	# Loops over users and finds who picked (and didn't) in UserPicks DB for current week
	def get(self):
		if not self.user:
			self.redirect_to('login',source='picks')
			return None
		week=current_week(self)
		usernames = []
		users = User.all().fetch(1000)
		users = list(users)
		for u in users:
			usernames.append(u.username)
		
		# Grab Picks for current week
		picks = memcache.get("week"+str(week)+"picks")
		if not picks:
			picks = UserPicks.all().filter('week = ',week).fetch(1000)
			memcache.set("week"+str(week)+"picks",list(picks))
		
		# Remove winner from picks and generate list of users who did not submit picks
		for p in picks:
			if p.username == "winner":
				picks.remove(p)
			if p.username in usernames:
				usernames.remove(p.username)
		
		self.display_results(picks,usernames,week)
	
	# Renders the play_results.html file to show what users picked for each game
	# 	picks - files from the UserPicks DB for the current week
	#	nopicks - list of names of users that did not pick this week
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
		self.render('play_results.html',results=games,user=self.user,no_picks_list=nopicks,week=week)

# Handles the standings page (how many wins/losses by user by week)
class StandingsHandler(SignupHandler):
	def get(self):
		if not self.user:
			self.redirect_to('play')
			return None	
			
		week = current_week(self)
		results = []
		
		# How many weeks worth of standings will we have?
		winner = User.by_name("winner")
		weeks = UserPicks.all().filter('user_id =', float(winner.key().id())).order("-week").get()
		if not weeks:
			return None
		weeks = weeks.week
		
		#grab the results for each week to add to the standings
		for w in range(1,weeks+1):
			results.append(fetch_results(self,w))
		results = map(list, zip(*results))
		self.render('play_standings.html',results=results,user=self.user,weeks=weeks)
		
# Grabs the results for building the standings
def fetch_results(self,week,update = False):
	results = ""
	if update <> True:
		results = memcache.get("week"+str(week)+"results")
	if not results:
		results = Results.all().filter('week =',week).order("user_id").fetch(100)
		memcache.set("week"+str(week)+"results",results)
	return results

# We calculate the results when the "winner" picks are loaded
def calc_results(self,week,w_picks = None):
	#need something to delete out old picks if need to be updated
	if not w_picks:
		winner = User.by_name("winner")
		w_picks = UserPicks.all().filter('user_id =', float(winner.key().id())).filter('week =',week).get()
	if not w_picks:
		return None
	#get the number of games in the week for no picks case
	games = len(w_picks.picks)
	results = {}
	top_wins = 0
	winner_list = []
	users = User.all().fetch(100)
	for u in users:
		if u.username == "winner":
			continue
		u_picks = memcache.get(str(u.username)+"week"+str(week))
		if not u_picks:
			u_picks = UserPicks.all().filter('user_id =', float(u.key().id())).filter('week =',week).get()
		if u_picks:
			(wins,losses) = compare_picks(self,w_picks.picks,u_picks.picks)
			tb = abs(int(u_picks.picks[-1]) - int(w_picks.picks[-1]))
		else:
			#no picks for this week, zero wins
			wins = 0
			losses = games
			tb = 0
		results = Results(wins=wins,losses=losses,user_id=float(u.key().id()),week=week,tb=tb)
		results.put()
		if wins >= top_wins:
			if wins == top_wins:
				winner_list.append([results,tb])
			else:
				top_wins = wins
				winner_list = [[results,tb]]
	#just for testing
	u_winner = winner_list[0][0]
	u_winner = Results(wins=u_winner.wins,losses=u_winner.losses,user_id=u_winner.user_id,week=week,tb=tb,winner=1)
	u_winner.put()
	if len(winner_list) > 1:
		#do tb case
		for u in winner_list:
			#fix this later
			pass
	return fetch_results(self,week,update = True)

# Compare "winner" picks to user picks
def compare_picks(self,winner_picks,player_picks):
	(wins,losses) = 0,0
	for pick in player_picks:
		if pick in winner_picks:
			wins += 1
		else:
			losses += 1
	return (wins,losses)

##### Models ######		
class Results(db.Model):
	week = db.IntegerProperty(required = True)
	user_id = db.FloatProperty(required = True)
	wins = db.IntegerProperty(required = True)
	losses = db.IntegerProperty(required = True)
	tb = db.IntegerProperty(default = 0)
	winner = db.IntegerProperty(default = 0)
	#put method here to get username
class UserPicks(db.Model):
	user_id = db.FloatProperty(required = True)
	picks = db.ListProperty(required = True, item_type=str)
	created = db.DateTimeProperty(auto_now_add = True)
	week = db.IntegerProperty(required = True)
	username = db.StringProperty(required = True)
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
	cutoff = db.DateProperty(required = True) 