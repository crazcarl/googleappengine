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
# On github.com at https://github.com/crazcarl/googleappengine

from webapp2 import WSGIApplication, Route
import re
import os
# Set useful fields
root_dir = os.path.dirname(__file__)
template_dir = os.path.join(root_dir, 'templates')
								
from google.appengine.ext import db



		
# Create the WSGI application and define route handlers
app = WSGIApplication([
	Route(r'/', handler='handlers.blog.BlogHandler', name='blog2'),
	Route(r'/blog', handler='handlers.blog.BlogHandler', name='blog'),
	Route(r'/newpost', handler='handlers.blog.NewBlogHandler', name='newblog2'),
	Route(r'/blog/newpost', handler='handlers.blog.NewBlogHandler', name='newblog'),
	Route(r'/blog/<bpid:\d+>', handler='handlers.blog.BlogHandler', name='blog_single', handler_method='get_blog'),
	Route(r'/play',handler='handlers.play.Play',name='play'),
	Route(r'/play/picks',handler='handlers.play.Play',name='picks',handler_method='picks'),
	Route(r'/play/makepicks',handler='handlers.play.PickHandler'),
	Route(r'/signup',handler='handlers.signup.Register', name='signup'),
	Route(r'/signup/welcome',handler='handlers.signup.WelcomeHandler', name='welcome', handler_method='welcome'),
	Route(r'/login',handler='handlers.signup.LoginHandler',name='login'),
	Route(r'/logout',handler='handlers.signup.LoginHandler',name='logout',handler_method='logout'),
	Route(r'/cleardb',handler='handlers.signup.ClearDB',name='cleardb'),
	Route(r'/blog.json',handler='handlers.blog.jsonHandler',name='jsonblog',handler_method='blog'),
	Route(r'/blog/<bpid:\d+>.json', handler='handlers.blog.jsonHandler', name='jsonbp', handler_method='bp'),
	Route(r'/.json',handler='handlers.blog.jsonHandler',name='jsonblog',handler_method='blog'),
	Route(r'/play/results',handler='handlers.play.ResultsHandler',name='results'),
	Route(r'/flush', handler='handlers.blog.BlogHandler', name='flush', handler_method='flush_cache'),
	Route(r'/admin',handler='handlers.play.AdminHandler', name='admin'),
	Route(r'/play/standings',handler='handlers.play.StandingsHandler', name='standings')
	#Route(r'/_edit/<wikiname>', handler='handlers.wiki.editHandler', name='wikiedit'),
	#Route(r'/_history/<wikiname>', handler='handlers.wiki.historyHandler', name='wikihistory'),
	#Route(r'/<wikiname:\w+>', handler='handlers.wiki.wikiHandler', name='wiki')
], debug=True)