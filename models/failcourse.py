from peewee import *
from utils.db import db
from models.user import User

class FailCourse(Model):
    user = ForeignKeyField(User, backref='stories')
    title = CharField()
    story = TextField()
    lesson = TextField()
    tags = CharField()

    class Meta:
        database = db
