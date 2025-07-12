from peewee import *
from utils.db import db
from models.user import User
from models.question import Question

class Answer(Model):
    question = ForeignKeyField(Question, backref='answers')
    user = ForeignKeyField(User)
    text = TextField()

    class Meta:
        database = db
