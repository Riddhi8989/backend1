from peewee import *
from utils.db import db
from models.user import User

class Question(Model):
    user = ForeignKeyField(User, backref='questions')
    text = TextField()

    class Meta:
        database = db
