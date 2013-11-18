from handlers.signup import SignupHandler
from google.appengine.ext import db
from google.appengine.api import memcache



class wikiHandler(SignupHandler):
	def get(self,wikiname):
		#check to see if one exists
		wiki = wiki = Wiki.all().filter('name =', wikiname).order("-created").get()
		if not wiki:
			if self.user:
				self.redirect_to('wikiedit',wikiname=wikiname)
			else:
				self.redirect_to('blog2')
		else:
			self.render('wiki.html',wiki=wiki,wikiname=wikiname)
	
class editHandler(wikiHandler):	
	def get(self,wikiname):
		if self.user:
			self.render('wikiedit.html',wikiname=wikiname)
		else:
			self.redirect_to('blog2')
	def post(self,wikiname):
		if not self.user:
			self.redirect_to('blog2')
			return None
		text=self.request.get('content')
		if not text:
			self.redirect_to('wikiedit',wikiname=wikiname)
		else:
			wiki = Wiki(name=wikiname,text=text)
			wiki.put()
			self.redirect_to('wiki',wikiname=wikiname)
class historyHandler(wikiHandler):
	def get(self,wikiname):
		wiki = Wiki.all().filter('name =', wikiname).fetch(100)
		wiki = list(wiki)
		if len(wiki)>0:
			self.render('wikihistory.html',wiki=wiki)
		else:
			self.redirect_to('wiki',wikiname=wikiname)
class Wiki(db.Model):
	text = db.TextProperty(required = True)
	name = db.StringProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)