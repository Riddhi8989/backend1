from peewee import Model, CharField, TextField
from utils.db import db
from werkzeug.security import generate_password_hash, check_password_hash
import json

class User(Model):
    name = CharField()
    email = CharField(unique=True)
    password = CharField()
    bio = CharField(null=True)
    career = CharField(null=True)
    role = CharField(default='user')

    # New fields for full AI career data
    career_title = CharField(null=True)
    career_description = TextField(null=True)
    career_steps = TextField(null=True)       # JSON string
    career_pitfalls = TextField(null=True)    # JSON string
    career_resources = TextField(null=True)   # JSON string

    class Meta:
        database = db

    @classmethod
    def create_user(cls, data):
        return cls.create(
            name=data['name'],
            email=data['email'],
            password=generate_password_hash(data['password']),
            bio=data.get('bio', ''),
            career=data.get('career', ''),
            role=data.get('role', 'user')
        )

    @classmethod
    def authenticate(cls, email, password):
        user = cls.get_or_none(cls.email == email)
        if user and check_password_hash(user.password, password):
            return user
        return None

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "bio": self.bio,
            "career": self.career,
            "role": self.role,
            "career_title": self.career_title,
            "career_description": self.career_description,
            "career_steps": json.loads(self.career_steps) if self.career_steps else [],
            "career_pitfalls": json.loads(self.career_pitfalls) if self.career_pitfalls else [],
            "career_resources": json.loads(self.career_resources) if self.career_resources else []
        }
