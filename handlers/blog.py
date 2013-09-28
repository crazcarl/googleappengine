
from handlers.base import AppHandler
from google.appengine.ext import db



class BlogHandler(AppHandler):
	def get(self):
		bps = db.GqlQuery("Select * from Blog")
		self.render('base.html',bps=bps)
		#self.delete()  # uncomment to delete stuff.
	#this is for displaying your new post by itself
	def get_blog(self,bpid):
		key = db.Key.from_path('Blog',int(bpid))
		post = db.get(key)
		
		blogpost = post.blogpost
		blogsub = post.blogsub
		
		self.render('blog_single.html',blogpost=blogpost,blogsub=blogsub)
	def render_front(self):
		bps = db.GqlQuery("Select * from Blog")
		self.render('base.html',bps=bps)
	def delete(self):
		q = db.GqlQuery("SELECT * FROM Blog")
		results = q.fetch(100)
		for result in results:
			result.delete()
	

class NewBlogHandler(BlogHandler):
	def get(self):
		self.redirect_to('blog')
	def post(self):
		# Do fancy database stuff
		blogpost=self.request.get('content')
		blogsub=self.request.get('subject')
		if not blogpost or not blogsub:
			self.render_front()
		else:
			bp = Blog(blogpost=blogpost,blogsub=blogsub)
			bp.put()
			self.redirect_to('blog_single',bpid=bp.key().id())
			
class Blog(db.Model):
	blogpost = db.StringProperty(required = True)
	blogsub = db.StringProperty(required = False)
	created = db.DateTimeProperty(auto_now_add = True)
	