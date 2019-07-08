from flask import Flask, request, render_template, url_for, redirect, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
# from db_setup import Category, User, Tool
# from config import Config

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catalog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(20), nullable=False)
    lastname = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'email': self.email,
        }


class Tool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(300))
    '''
    Possible values:
        1- home
        2- work
        3- on loan
        4- unknown
    '''
    location = db.Column(db.Integer, default=1)
    notes = db.Column(db.String(300))
    # All tools must belong to a user.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('tools'))
    # All tools must belong to a category.
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'),
    nullable=False)
    category = db.relationship('Category', backref=db.backref('tools'))


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(300))

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
        }


@app.route('/')
@app.route('/login/')
def login():
    return "This will be the login page."


@app.route('/tools/')
def all():
    return "This page will list all of the logged-in user's tools."


@app.route('/tools/<int:category_id>/')
def list_category(category_id):
    return "This page will list all of a user's tools of the specified category."


@app.route('/tools/categories/')
def list_cats():
    cats = Category.query.all()
    print(cats)
    return "IT DIDN'T eRROR! reJOIcE"


@app.route('/tools/new/')
def new():
    return "Future New Tool Form"


@app.route('/tools/<int:tool_id>/edit/')
def edit_tool(tool_id):
    return "Future Edit form for existing tools"


@app.route('/tools/<int:tool_id>/delete/')
def delete(tool_id):
    return "Future delete form for existing tools"


if __name__ == '__main__':
    app.secret_key = '''One day a randomly generated 128-bit string
      will go here. Well, not *here* here because we'll use OAuth'''
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
