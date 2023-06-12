# This file is to set up the various tables  in SQL

# Importing the app, db and login_manager from the __init__.py
from tracker import app
from tracker import db
from tracker import login_manager

# Import User specific features
from sqlalchemy.orm import relationship
from flask_login import UserMixin


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(30), default="Pending Verification", nullable=False)
    username = db.Column(db.String(30), unique=True, nullable=False)
    first_name = db.Column(db.String(50), unique=False, nullable=False)
    surname = db.Column(db.String(50), unique=False, nullable=False)
    password = db.Column(db.String(180), unique=False, nullable=False)
    email = db.Column(db.String(180))
    start_datetime = db.Column(db.DateTime, nullable=False)
    comments = db.relationship("Comments", back_populates="parent_user")
    bugs = db.relationship("Bug", back_populates="parent_user")


@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(user_id)


class Bug(db.Model):
    __tablename__ = "bugs"
    id = db.Column(db.Integer, primary_key=True)
    bug = db.Column(db.String(140), unique=False, nullable=False)
    description = db.Column(db.Text, unique=False, nullable=True)
    urgency = db.Column(db.String(140), unique=False, nullable=False)
    status = db.Column(db.String(140), default="Pending Assignment", unique=False, nullable=False)
    task = db.Column(db.String(140), unique=False, nullable=True)
    project = db.Column(db.String(140), unique=False, nullable=False)
    start_datetime = db.Column(db.DateTime, nullable=False)
    update_datetime = db.Column(db.DateTime, nullable=False)
    comments = db.relationship("Comments", back_populates="parent_bug")
    parent_user = db.relationship("User", back_populates="bugs")
    parent_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))


class Comments(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    parent_bug = db.relationship("Bug", back_populates="comments")
    parent_bug_id = db.Column(db.Integer, db.ForeignKey("bugs.id"))
    parent_user = relationship("User", back_populates="comments")
    parent_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    start_datetime = db.Column(db.DateTime, nullable=False)
    update_datetime = db.Column(db.DateTime, nullable=False)


with app.app_context():
    db.create_all()
    db.session.commit()
    
    