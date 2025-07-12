from peewee import SqliteDatabase
import os

db = SqliteDatabase(os.path.join(os.getcwd(), 'failed.db'))
