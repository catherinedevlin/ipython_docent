import cgi
import datetime
import urllib
import webapp2
import jinja2
import os
import collections

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

from google.appengine.ext import db


class Student(db.Model):
    name = db.StringProperty()


class Exercise(db.Model):
    creation = db.DateTimeProperty(auto_now_add=True)
    function_name = db.StringProperty()


class Result(db.Model):    
    student = db.ReferenceProperty(Student, 
                                   collection_name = 'results')
    exercise = db.ReferenceProperty(Exercise,
                                    collection_name = 'results')   
    failure = db.BooleanProperty()
    source_code = db.StringProperty(multiline=True)
    date = db.DateTimeProperty(auto_now_add=True)


class Report(webapp2.RequestHandler):
    def get(self, workshop_name):
        workshop_key = db.Key.from_path('Workshop', workshop_name)
        template = jinja_environment.get_template('report.html')
        students = db.GqlQuery("SELECT * FROM Student "
                               "WHERE ANCESTOR IS :1 "
                               "ORDER BY name",
                               workshop_key)
        exercises = db.GqlQuery("SELECT * FROM Exercise "
                                "WHERE ANCESTOR IS :1 "
                                "ORDER BY creation",
                                workshop_key)
        data = collections.defaultdict(dict)
        for result in db.GqlQuery("SELECT * FROM Result "
                                  "WHERE ANCESTOR IS :1 ",
                                  workshop_key):
            data[result.student.name][result.exercise.function_name] = result
        template_values = dict(students=students,
                               exercises=exercises,
                               data=data)
        self.response.out.write(template.render(template_values))


class About(webapp2.RequestHandler):
    def get(self):
        template = jinja_environment.get_template('about.html')
        self.response.out.write(template.render({}))

class Record(webapp2.RequestHandler):
    def post(self):
        workshop_key = db.Key.from_path('Workshop', self.request.get('workshop_name'))
        student_name = self.request.get('student_name')
        student = db.GqlQuery("SELECT * FROM Student "
                              "WHERE ANCESTOR IS :1 "
                              "AND   name = :2", 
                               workshop_key, student_name).get()
        if not student:
            student = Student(parent=workshop_key)
            student.name = student_name
            student.put()
        
        function_name = self.request.get('function_name')
        exercise = db.GqlQuery("SELECT * FROM Exercise "
                               "WHERE ANCESTOR IS :1 "
                               "AND function_name = :2", 
                                workshop_key, function_name).get()
        if not exercise:
            exercise = Exercise(parent=workshop_key)
            exercise.function_name = function_name
            exercise.put()        

        # finding an existing result of student + exercise
        # is very close to impossible, thank you GAE
        keys = set(r.key() for r in student.results).intersection(set(r.key() for r in exercise.results))
        if keys:
            result = Result.get(keys.pop())
        else:
            result = Result(parent=workshop_key)
            result.student = student
            result.exercise = exercise
        result.failure = (self.request.get('failure') == 'True')
        result.source_code = self.request.get('source')
        result.put()

app = webapp2.WSGIApplication([
                               (r'/', About),
                               (r'/record', Record),
                               (r'/(\w+)', Report),
                              ],
                              debug=True)

