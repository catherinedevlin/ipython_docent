import cgi
import datetime
import urllib
import webapp2

from google.appengine.ext import db


class Challenge(db.Model):
    student = db.StringProperty()
    name = db.StringProperty()
    failure = db.BooleanProperty()
    source_code = db.StringProperty(multiline=True)
    date = db.DateTimeProperty(auto_now_add=True)


class Report(webapp2.RequestHandler):
    def get(self):
        self.response.out.write('<ul>')
        challenges = db.GqlQuery("SELECT * FROM Challenge")
        for challenge in challenges:
            self.response.out.write('<li>%s</li>' % challenge.failure)
        self.response.out.write('</ul>')

class Record(webapp2.RequestHandler):
    def post(self):
        workshop = db.Key.from_path('Workshop', self.request.get('workshop_name'))
        challenge = Challenge(parent=workshop)
        challenge.name = self.request.get('name')
        challenge.failure = (self.request.get('failure') == 'True')
        challenge.source_code = self.request.get('source')
        challenge.student = self.request.get('student_name')
        challenge.put()


app = webapp2.WSGIApplication([('/', Report),
                               ('/record', Record),
                              ],
                              debug=True)
