"""
Before Starting Package needed to be installed
1) pip install flask
2) pip install peewee
3) pip install flask-login
4) pip install flask-bcrypt (It uses the blue fish cipher)
5) pip install flask-wtf
"""


import datetime

from flask_bcrypt import generate_password_hash
from flask_login import UserMixin

"""Flask have an ecosystem where package gets installed to this ext(external area)
module. and inside of that we get the package.
Read About UserMixin - 'http://flask-login.readthedocs.org/en/latest/#your-user-class'
"""

from peewee import *
from playhouse.migrate import *

DATABASE = SqliteDatabase("social.db")
migrator = SqliteMigrator(DATABASE)


class User(UserMixin, Model):
    """Parent class can be more than one"""

    username = CharField(unique=True)
    email = CharField(unique=True)
    password = CharField(max_length=100)
    joined_at = DateTimeField(default=datetime.datetime.now)
    is_admin = BooleanField(default=False)
    photo = CharField(default="/static/img/someguy.jpg")

    class Meta:
        database = DATABASE
        order_by = ("-joined_at",)

    def get_posts(self):
        return Post.select().where(Post.user == self)

    def get_stream(self):
        return Post.select().where((Post.user << self.following()), (Post.user == self))

    def following(self):
        """The users we are following"""
        return (
            User.select()
            .join(Relationship, on=Relationship.to_user)
            .where(Relationship.from_user == self)
        )

    def followers(self):
        """Users Following the current user"""
        return (
            User.select()
            .join(Relationship, on=Relationship.from_user)
            .where(Relationship.to_user == self)
        )

    @classmethod
    def create_user(cls, username, email, password, admin=False, photo=None):
        """cls here is being user. so cls.create is kind of user.create"""
        try:
            with DATABASE.transaction():
                cls.create(
                    username=username,
                    email=email,
                    password=generate_password_hash(password),
                    is_admin=admin,
                    photo=photo,
                )
        except IntegrityError:
            raise ValueError("User already exists")


class Post(Model):
    timestamp = DateTimeField(default=datetime.datetime.now)
    user = ForeignKeyField(User, related_name="posts")
    content = TextField()

    class Meta:
        database = DATABASE
        order_by = ("-timestamp",)


class Relationship(Model):
    from_user = ForeignKeyField(User, related_name="relationships")
    to_user = ForeignKeyField(User, related_name="related_to")

    class Meta:
        database = DATABASE
        indexes = ((("from_user", "to_user"), True),)


class Project(Model):
    project_id = IntegerField(unique=True)
    from_user = ForeignKeyField(User, related_name="created_by")
    description = CharField(2048)
    name = CharField(2048)

    class Meta:
        database = DATABASE

    @classmethod
    def create_project(
        cls, project_id, description, from_user, name, admin=False, photo=None
    ):
        """cls here is s user. so cls.create is kind of user.create"""
        try:
            with DATABASE.transaction():
                cls.create(
                    project_id=project_id,
                    from_user=from_user,
                    description=description,
                    name=name,
                )
        except IntegrityError:
            print("User exists")


class Idea(Model):
    id = CharField(1024, unique=True)
    from_user = CharField()
    for_project = IntegerField()
    description = CharField(2048)
    title = CharField(2048)


    class Meta:
        database = DATABASE

    @classmethod
    def create_idea(
        cls, for_project, from_user_id, description, id, title
    ):
        try:
            with DATABASE.transaction():
                cls.create(
                    id=id,
                    from_user_id=from_user_id,
                    description=description,
                    title=title,
                    for_project=for_project
                )
        except IntegrityError:
            print("User exists")


def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, Post, Relationship, Project, Idea], safe=True)
    DATABASE.close()
