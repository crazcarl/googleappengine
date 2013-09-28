#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from webapp2 import WSGIApplication, Route
import re
import os
# Set useful fields
root_dir = os.path.dirname(__file__)
template_dir = os.path.join(root_dir, 'templates')

								
from google.appengine.ext import db

# def render_str(template,**params):
#	t = jinja_env.get_template(template)
#	return t.render(params)
#	
#class MainHandler(webapp2.RequestHandler):
#	def write(self,*a,**kw):
#		self.response.out.write(*a,**kw)	
#	def get(self):
#		rs = render_str('play.html')
#		self.response.out.write(rs)
#		
#
#class success(webapp2.RequestHandler):
#	def get(self):
#		self.render('play.html')


		
# Create the WSGI application and define route handlers
app = WSGIApplication([
	Route(r'/blog', handler='handlers.blog.BlogHandler', name='blog'),
	Route(r'/blog/newpost', handler='handlers.blog.NewBlogHandler', name='newblog'),
	Route(r'/blog/<bpid:\d+>', handler='handlers.blog.BlogHandler', name='blog_single', handler_method='get_blog'),
	Route(r'/play',handler='handlers.play.Play',name='play')
], debug=True)