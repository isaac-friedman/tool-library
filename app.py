import random
import string
import json
import httplib2
import requests

from flask import Flask, request, render_template, url_for, redirect, flash, \
    jsonify, make_response, session as login_session
from flask_sqlalchemy import SQLAlchemy

from oauth2client.client import flow_from_clientsecrets, FlowExchangeError


CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
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


@app.route('/')
@app.route('/login/')
# Create a state token and store it in the session for validation
def login():
    state = ''.join(random.choice(string.ascii_uppercase
                    + string.ascii_lowercase
                    + string.digits) for x in range(64))
    login_session['state'] = state
    return render_template("login.html", STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    print("Entered gconnect function")
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    print ("You have a code of: {0}".format(code))

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


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

    print(by_category)
    # return "<center><h1>WE'RE WORKING ON IT DAMMIT</h1></center>"
    return render_template("list.html", by_category=by_category)


@app.route('/tools/<int:category_id>/')
def list_category(category_id):
    cat = Category.query.filter_by(id=category_id).first()
    print(cat)
    tools = Tool.query.filter_by(category_id=category_id).all()
    print(tools)
    for tool in tools:
        print(tool.id)
        print(tool.description)
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
    print(tool.location)
    if request.method == 'POST':
        if request.form['name']:  # sanity check of form data
            tool.name = request.form['name']
            tool.description = request.form['description']
            tool.notes = request.form['notes']
            tool.location = request.form['location']

        print(tool.notes)
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
