from google.appengine.ext import db

class Category(db.Model):
	username=db.StringProperty(required=True)
	categoryname=db.StringProperty(required=True)
	items=db.StringListProperty()
	expirydate = db.DateTimeProperty()

class Vote(db.Model):
	username=db.StringProperty(required=True)
	categoryname=db.StringProperty(required=True)
	itemname=db.StringProperty(required=True)
	wins=db.IntegerProperty()
	loss=db.IntegerProperty()

class Comments(db.Model):
	owner=db.StringProperty(required=True)
	username=db.StringProperty(required=True)
	categoryname=db.StringProperty(required=True)
	itemname=db.StringProperty(required=True)
	comment=db.StringProperty()	
