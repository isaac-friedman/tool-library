import random
import string
import json
import httplib2
import requests

from flask import Flask, request, render_template, url_for, redirect, flash, \
    jsonify, make_response, session as login_session
from flask_sqlalchemy import SQLAlchemy

from oauth2client import client
from apiclient import discovery


CLIENT_ID = json.loads(open('client_secrets.json', 'r').
                       read())['web']['client_id']
CLIENT_SECRET = json.loads(open('client_secrets.json', 'r').
                           read())['web']['client_secret']
APPLICATION_NAME = "Tool Trackr"


app = Flask(__name__)
# DB Config
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
    location = db.Column(db.Integer, default=4)
    notes = db.Column(db.String(300))
    # All tools must belong to a user.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('tools'))
    # All tools must belong to a category.
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'),
                            nullable=False)
    category = db.relationship('Category', backref=db.backref('tools'))

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'location': self.location,
            'notes': self.notes,
            'user_id': self.user_id,
            'category_id': self.category_id,
        }


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


def get_user_id(email):
    try:
        user = User.query.filter_by(email=email).one()
        return user.email
    except NoResultFound:
        return None


def create_user(login_session):
    user = User(name=login_session['username'],
                email=login_session['email'])
    db.session.add(user)
    db.session.commit()
    return user.id


@app.route('/')
@app.route('/login/')
# Create a state token and store it in the session for validation
def login():
    state = ''.join(random.choice(string.ascii_uppercase
                    + string.ascii_lowercase
                    + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template("login.html", STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # If the request doesn't have `X-Requested-With` header, it could be a CSRF
    if not request.headers.get('X-Requested-With'):
        abort(403)
    CLIENT_SECRET_FILE = './client_secrets.json'

    # Obtain authorization code
    auth_code = request.data
    # Exchange auth code for access token, refresh token, and ID token
    credentials = client.credentials_from_clientsecrets_and_code(
        CLIENT_SECRET_FILE,
        ['https://www.googleapis.com/auth/drive.appdata', 'profile', 'email'],
        auth_code)

    # Call Google API
    http_auth = credentials.authorize(httplib2.Http())

    # Get profile info from ID token
    login_session['userid'] = credentials.id_token['sub']
    login_session['email'] = credentials.id_token['email']
    login_session['access_token'] = credentials.access_token
    flash("You are now logged in as {0}. Success!"
          .format(login_session['username']))
    return render_template("list.html")


@app.route('/disconnect')
def gdisconnect():

    if login_session['access_token'] is None:
        error_message = 'Current user not connected.'
        flash(error_message)
        return render_template('list.html')

    result = requests.post('https://accounts.google.com/o/oauth2/revoke',
                           params={'token': login_session['access_token']},
                           headers={'content-type':
                                    'application/x-www-form-urlencoded'})

    return render_template("login.html")


@app.route('/tools/')
def all():
    tools = db.session.query(Tool.id, Tool.name, Tool.description,
                             Category.name).join(Category,
                                                 Tool.category_id ==
                                                 Category.id).all()
    by_category = {}
    for tool in tools:
        if tool[3] not in by_category:
            by_category[tool[3]] = [[tool[0], tool[1], tool[2]]]
        else:
            by_category[tool[3]].append([tool[0], tool[1], tool[2]])

    return render_template("list.html", by_category=by_category)


@app.route('/tools/<int:category_id>/')
def list_category(category_id):
    cat = Category.query.filter_by(id=category_id).first()
    tools = Tool.query.filter_by(category_id=category_id).all()

    return render_template("category.html", cat=cat, tools=tools)


@app.route('/tools/categories/')
def list_cats():
    cats = Category.query.all()
    return render_template("categories.html", cats=cats)


@app.route('/tools/new/', methods=['GET', 'POST'])
def new():
    if request.method == 'POST':
        # Use of user_id from input is strictly temporary
        newTool = Tool(user_id=int(request.form['user_id']),
                       name=request.form['name'],
                       description=request.form['description'],
                       location=int(request.form['location']),
                       notes=request.form['notes'],
                       category_id=int(request.form['category']))
        db.session.add(newTool)
        db.session.commit()
        return redirect(url_for('all'))
    else:
        return render_template("new.html")


@app.route('/tools/<int:tool_id>/edit/', methods=['GET', 'POST'])
def edit_tool(tool_id):
    tool = Tool.query.filter_by(id=tool_id).one()

    if request.method == 'POST':
        if request.form['name']:  # sanity check of form data
            tool.name = request.form['name']
            tool.description = request.form['description']
            tool.notes = request.form['notes']
            tool.location = request.form['location']

        db.session.add(tool)
        db.session.commit()
        return redirect(url_for('all'))
    else:
        return render_template("edit.html", tool=tool)


@app.route('/tools/<int:tool_id>/delete/', methods=['GET', 'POST'])
def delete_tool(tool_id):
    tool = Tool.query.filter_by(id=tool_id).one()
    if request.method == 'POST':
        db.session.delete(tool)
        db.session.commit()
        return redirect(url_for('all'))
    else:
        return render_template('delete.html', name=tool.name, id=tool.id)


@app.route('/tools/json/')
def json_all():
    tools = Tool.query.all()
    return jsonify(Tools=[tool.serialize for tool in tools])


@app.route('/tools/<int:tool_id>/json/')
def json_one(tool_id):
    tool = Tool.query.filter_by(id=tool_id).one()
    return jsonify(tool.serialize)


if __name__ == '__main__':
    app.secret_key = '''One day a randomly generated 128-bit string
      will go here. Well, not *here* here because we'll use OAuth'''
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
