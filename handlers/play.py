from handlers.base import AppHandler

game1=["Bengals",-1,"Cowboys"]
game2=["Redskins",-4,"Cardinals"]
game3=["Saints",-1,"Rams"]
games = [game1,game2,game3]
class Play(AppHandler):
	def get(self):
		self.render('play.html',games=games)