from handlers.base import AppHandler
import csv
import os
from main import root_dir

class Play(AppHandler):
	def get(self):
		self.render('play.html')
	def picks(self):
		#eventually use dates.txt to pick the right date, but for now:
		f = open(root_dir + '\Schedules\week1.txt')
		f_list = csv.reader(f)
		games=[]
		for row in f_list:
			#self.write(row)
			if row[0] <> "Team1":
				games.append(row)
		f.close()
		self.render('play_picks.html',games=games)

class PickHandler(AppHandler):
	def post(self):
		game1 = self.request.get('1')
		self.write(game1)

class AdminHandler(AppHandler):
	#use this to make sure the files load in correctly
	def testFiles(self):
		self.render('admin.html')