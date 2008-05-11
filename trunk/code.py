import wsgiref.handlers
import logging
import traceback
from google.appengine.api import urlfetch
from google.appengine.ext import webapp

from birdnest import filter
from birdnest.filter import json

twitterAPI = "http://twitter.com/"

class BaseProxy(webapp.RequestHandler):
  def __init__(self):
    self.required_header = ['Authorization', 'User-Agent', 'X-Twitter-Client', 'X-Twitter-Client-URL', 'X-Twitter-Client-Version']

  def get(self, params):    
    url = twitterAPI + params
    headers = {}
    for header in self.required_header:
      if self.request.headers.has_key(header):
        headers[header] = self.request.headers[header]

    result = urlfetch.fetch(url, headers=headers)
    self.sendoutput(result)

  def sendoutput(self, result):
    if result.status_code == 200:
      self.response.headers = result.headers
      self.response.out.write(self.filter(result.content))
    else:
      self.error(result.status_code)
      self.response.out.write(result.content)

  def post(self, params):
    url = twitterAPI + params
    headers = {}
    for header in self.required_header:
      if self.request.headers.has_key(header):
        headers[header] = self.request.headers[header]
    try:
      result = urlfetch.fetch(url, payload=self.request.body, method=urlfetch.POST, headers=headers)
      self.sendoutput(result)
    except Exception, inst:
        self.error(500)
        logging.error("%s \n\n %s \n\n %s \n\n %s" % ( inst, self.request.headers, self.request.body, result.content))

class OptimizedProxy(BaseProxy):
  def __init__(self):
    BaseProxy.__init__(self)

  def sendoutput(self, result):

    if result.status_code == 200:
      self.response.headers = result.headers
      self.response.out.write(self.filter(result.content))
    elif result.status_code == 304:
      self.response.headers = result.headers
    else:
      logging.info(result.content)
      self.error(result.status_code)
      self.response.out.write('')
    
class TextOnlyProxy(OptimizedProxy):
  def __init__(self):
    OptimizedProxy.__init__(self)

class IncludeImageProxy(OptimizedProxy):
  def __init__(self):
    OptimizedProxy.__init__(self)

class NoFilterProxy(BaseProxy, filter.Filter):
  pass

class NoFilterOptimizedProxy(OptimizedProxy, filter.Filter):
  pass

class JSONStatusesIncludeImageProxy(TextOnlyProxy, json.StatusesIncludeImage):
  pass

class JSONStatusesTextOnlyProxy(TextOnlyProxy, json.StatusesTextOnly):
  pass

class JSONSingleStatusesIncludeImageProxy(TextOnlyProxy, json.SingleStatusesIncludeImage):
  pass

class JSONSingleStatusesTextOnlyProxy(TextOnlyProxy, json.SingleStatusesTextOnly):
  pass


class JSONDirectMessageTextOnlyProxy(TextOnlyProxy, json.DirectMessageTextOnly):
  pass

class JSONDirectMessageIncludeImageProxy(TextOnlyProxy, json.DirectMessageIncludeImage):
  pass

class JSONSingleDirectMessageTextOnlyProxy(TextOnlyProxy, json.SingleDirectMessageTextOnly):
  pass

class JSONSingleDirectMessageIncludeImageProxy(TextOnlyProxy, json.SingleDirectMessageIncludeImage):
  pass

def main():
  application = webapp.WSGIApplication([
    ('/api/(.*)', NoFilterProxy),

    ('/optimized/(.*)', NoFilterOptimizedProxy),

    ('/text/(public_timeline\.json)', JSONStatusesTextOnlyProxy),
    ('/text/(statuses/user_timeline\.json)', JSONStatusesTextOnlyProxy),
    ('/text/(statuses/friends_timeline\.json)', JSONStatusesTextOnlyProxy),
    ('/text/(statuses/replies\.json)', JSONStatusesTextOnlyProxy),
    ('/text/(statuses/update\.json)', JSONSingleStatusesTextOnlyProxy),
    ('/text/(direct_messages\.json)', JSONDirectMessageTextOnlyProxy),
    ('/text/(direct_messages/sent\.json)', JSONDirectMessageTextOnlyProxy),
    ('/text/(direct_messages/new\.json)', JSONSingleDirectMessageTextOnlyProxy),
    ('/text/(direct_messages/delete/\d+\.json)', JSONSingleDirectMessageTextOnlyProxy),
    ('/text/(.*)', NoFilterOptimizedProxy),

    ('/image/(public_timeline\.json)', JSONStatusesIncludeImageProxy),
    ('/image/(statuses/user_timeline\.json)', JSONStatusesIncludeImageProxy),
    ('/image/(statuses/friends_timeline\.json)', JSONStatusesIncludeImageProxy),
    ('/image/(statuses/replies\.json)', JSONStatusesIncludeImageProxy),
    ('/image/(statuses/update\.json)', JSONSingleStatusesIncludeImageProxy),
    ('/image/(direct_messages\.json)', JSONDirectMessageIncludeImageProxy),
    ('/image/(direct_messages/sent\.json)', JSONDirectMessageIncludeImageProxy),
    ('/image/(direct_messages/new\.json)', JSONSingleDirectMessageIncludeImageProxy),
    ('/image/(direct_messages/delete/\d+\.json)', JSONSingleDirectMessageIncludeImageProxy),
    ('/image/(.*)', NoFilterOptimizedProxy)],
    debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
  main()
