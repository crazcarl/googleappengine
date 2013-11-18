from handlers.signup import SignupHandler
from google.appengine.ext import db
from google.appengine.api import memcache
import json
import time



class BlogHandler(SignupHandler):
	def get(self):
		bps = self.get_bps()
		secs = memcache.get("timer")
		if not secs:
			secs = 0
		else:
			secs = time.time() - secs
		self.render('base.html',bps=bps,secs=secs)
	#this is for displaying your new post by itself
	def get_blog(self,bpid):
		key = db.Key.from_path('Blog',int(bpid))
		post = memcache.get(str(bpid))
		if not post:
			post = db.get(key)
			if post:
				memcache.set(str(bpid),post)
				memcache.set("timer"+str(bpid),time.time())
		secs = memcache.get("timer"+str(bpid))
		if not secs:
			secs = 0
		else:
			secs = time.time() - secs
		blogpost = post.blogpost
		blogsub = post.blogsub
		self.render('blog_single.html',blogpost=blogpost,blogsub=blogsub,secs=secs)
	def get_bps(self,update = False):
		key = 'top'
		bps = memcache.get(key)
		if bps is None or update:
			bps = db.GqlQuery("Select * from Blog")
			bps = list(bps)
			memcache.set(key,bps)
			secs = time.time()
			memcache.set("timer",secs)
		return bps
	def flush_cache(self):
		memcache.flush_all()
		self.redirect_to('blog')
class NewBlogHandler(BlogHandler):
	def get(self):
		self.redirect_to('blog')
	def post(self):
		blogpost=self.request.get('content')
		blogsub=self.request.get('subject')
		if not blogpost or not blogsub:
			self.redirect_to('blog')
		else:
			bp = Blog(blogpost=blogpost,blogsub=blogsub)
			bp.put()
			#update main page cache
			bps = self.get_bps(update=True)
			bpkey = bp.key().id()
			memcache.set(str(bpkey),bp)
			memcache.set("timer"+str(bpkey),time.time())
			self.redirect_to('blog_single',bpid=bpkey)
class jsonHandler(BlogHandler):
	def blog(self):
		self.response.headers['Content-Type'] = "application/json"
		json_out = {}
		bps = db.GqlQuery("Select * from Blog")
		if bps:
			json_out["posts"] = []
			count=0
			for bp in bps:
				post = {}
				post["content"] = bp.blogpost
				post["subject"] = bp.blogsub
				json_out["posts"].append(post)
				count=count+1
			self.write(json.dumps(json_out))
	def bp(self,bpid):
		self.response.headers['Content-Type'] = "application/json"
		json_out ={}
		key = db.Key.from_path('Blog',int(bpid))
		post = db.get(key)
		if post:
			json_out["content"] = post.blogpost
			json_out["subject"] = post.blogsub
			self.write(json.dumps(json_out))
	
class Blog(db.Model):
	blogpost = db.StringProperty(required = True)
	blogsub = db.StringProperty(required = False)
	created = db.DateTimeProperty(auto_now_add = True)
	