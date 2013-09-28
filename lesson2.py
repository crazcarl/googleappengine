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
#FINISHED LESSON 2 Saved File
import webapp2

form="""
<form method="post"> 
	<div><h2>Sign up!</h2></div>
	<label>
		Username:
		<input type="text" name="username" value=%(un)s>%(uError)s
	</label><br>
	<label>
		Password
		<input type="password" name="password">%(pError)s
	</label><br>
	<label>
		Password Verify
		<input type="password" name="verify">%(vError)s
	</label><br>
	<label>
		Email
		<input type="email" name="email" value=%(em)s>%(eError)s
	</label><br>
	<input type="submit" value="Submit"></input>
</form>
"""

import re
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
P_RE = re.compile(r"^.{3,20}$")
E_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write(form)
class TestHandler(webapp2.RequestHandler):
	def post(self):
		#q = self.request.get("q")
		#self.response.out.write(q)
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.out.write(self.request)
class Rot13Handler(webapp2.RequestHandler):
	def get(self):
		self.response.write(form % "")
	def rot13(self,texts):
		newtext = ""
		for char in texts:
			if char.isalpha():
				charVal = ord(char) + 13
				if (charVal > 90 and charVal <=103) or charVal > 122:
					charVal -= 26
				newChr = chr(charVal)
				newtext += newChr
			else:
				newtext += char
		return newtext
	def post(self):
		texts = self.request.get('text')
		if not texts:
			self.response.write(form)
		else:
			texts = self.rot13(texts)
			self.response.write(form % texts)
class VerifyHandler(webapp2.RequestHandler):
	def verifyE(self,email):
		return E_RE.match(email)
	def verifyN(self,name):
		return USER_RE.match(name)
	def verifyP(self,pw):
		return P_RE.match(pw)
	def get(self):
		self.response.write(form % {"eError":"","uError":"","pError":"","vError":"","un":"","em":""})
	def post(self):
		uName=self.request.get('username')
		pw=self.request.get('password')
		vPw=self.request.get('verify')
		email=self.request.get('email')
		error=0
		eError=""
		uError=""
		pError=""
		vError=""
		if not self.verifyE(email):
			eError = "Invalid Email"
			error=1
		if not self.verifyN(uName):
			uError = "Invalid Name"
			error=1
		if not self.verifyP(pw):
			pError = "Invalid PW"
			error=1
		if pw != vPw:
			vError = "Passwords do not match"
			error=1
		if error==1:
			#write screen with errors
			self.response.write(form %{"eError":eError,"uError":uError,"pError":pError,"vError":vError,"un":uName,"em":email	})
		else:
			self.redirect('/verify/success?username=' + uName)

class success(webapp2.RequestHandler):
	def get(self):
		uName = self.request.get('username')
		self.response.write("Welcome " + uName)
app = webapp2.WSGIApplication([
    ('/', MainHandler),('/testform',TestHandler),('/rot13',Rot13Handler),('/verify',VerifyHandler),('/verify/success',success),
], debug=True)
