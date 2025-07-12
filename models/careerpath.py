from peewee import *
from utils.db import db

class CareerPath(Model):
    title = CharField()
    steps = TextField()
    pitfalls = TextField()
    resources = TextField()

    class Meta:
        database = db
