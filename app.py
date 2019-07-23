import random
import string
import json
import httplib2
import requests

from flask import Flask, request, render_template, url_for, redirect, flash, \
    jsonify, session as login_session
# from flask_sqlalchemy import SQLAlchemy
from db_setup import db, Category, Tool, User
from oauth2client import client

app = Flask(__name__)
CLIENT_ID = json.loads(open('client_secrets.json', 'r').
                       read())['web']['client_id']
CLIENT_SECRET = json.loads(open('client_secrets.json', 'r').
                           read())['web']['client_secret']
APPLICATION_NAME = "Tool Trackr"
# DB Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catalog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


def create_user():
    user = User(firstname=login_session['firstname'],
                lastname=login_session['lastname'],
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
        return """Possible Cross Site Request forgery. You are being
                  served this page as if it were a valid response but
                  will not be allowed to proceed."""
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
    # First the tokens needed to keep track of the user
    login_session['google_id'] = credentials.id_token['sub']
    login_session['access_token'] = credentials.access_token
    # Then the bare minimum necessary personal info for the profile
    login_session['email'] = credentials.id_token['email']
    login_session['firstname'] = credentials.id_token['given_name']
    login_session['lastname'] = credentials.id_token['family_name']
    # Check if we need to create a new user
    try:
        exists = User.query.filter_by(email=login_session['email']).first()
    except Exception:
        create_user()
    login_session['user_id'] = db.session.query(User.id).\
        filter_by(email=login_session['email']).\
        scalar()
    print(login_session)

    flash("You are now logged in as {0}. Success!"
          .format(login_session['firstname']))
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
    location_lookup = ['undefined', 'Home', 'Work', 'On loan', 'Unknown']
    # Users must log in to see this view.
    if login_session['access_token'] is None:
        return redirect(url_for("login"))

    tools = (db.session.query(Tool.id, Tool.name, Tool.description,
                              Tool.location, Tool.notes, Category.name)
             .join(Category, Tool.category_id == Category.id)
             .filter(Tool.user_id == login_session['user_id']).all())
    by_category = {}
    for tool in tools:
        if tool[5] not in by_category:
            by_category[tool[5]] = [[tool[0], tool[1], tool[2],
                                     location_lookup[tool[3]], tool[4]]]
        else:
            by_category[tool[5]].append([tool[0], tool[1], tool[2],
                                         location_lookup[tool[3]], tool[4]])
    print(by_category)
    return render_template("list.html", by_category=by_category)


@app.route('/tools/categories/<int:category_id>/')
def list_category(category_id):
    # Users must log in to see this view.
    if login_session['access_token'] is None:
        return redirect(url_for("login"))

    cat = Category.query.filter_by(id=category_id).first()
    tools = Tool.query.filter_by(category_id=category_id).all()

    return render_template("category.html", cat=cat, tools=tools)


@app.route('/tools/categories/')
def list_cats():
    # Users must log in to see this view.
    if login_session['access_token'] is None:
        return redirect(url_for("login"))

    cats = Category.query.all()
    return render_template("categories.html", cats=cats)


@app.route('/tools/new/', methods=['GET', 'POST'])
def new():
    # Users must log in to see this view.
    if login_session['access_token'] is None:
        return redirect(url_for("login"))

    print(login_session['user_id'])
    if request.method == 'POST':
        # Use of user_id from input is strictly temporary
        newTool = Tool(user_id=int(login_session['user_id']),
                       name=request.form['name'],
                       description=request.form['description'],
                       location=int(request.form['location']),
                       notes=request.form['notes'],
                       category_id=int(request.form['category']))
        db.session.add(newTool)
        db.session.commit()
        return redirect(url_for('all'))
    else:
        return render_template("new.html", user_id=login_session['user_id'])


@app.route('/tools/<int:tool_id>/edit/', methods=['GET', 'POST'])
def edit_tool(tool_id):
    # Users must log in to see this view.
    if login_session['access_token'] is None:
        return redirect(url_for("login"))

    tool = Tool.query.filter_by(id=tool_id).one()
    if request.method == 'POST':
        if request.form['name']:  # sanity check of form data
            # Check that user has permission to edit this tool.
            if login_session['user_id'] == tool.user_id:
                tool.name = request.form['name']
                tool.description = request.form['description']
                tool.notes = request.form['notes']
                tool.location = request.form['location']
                db.session.add(tool)
                db.session.commit()
            else:
                flash("""You do not have permission to edit this tool and you
                         could not have accessed it non-maliciously. You will
                         now be logged out.""")
                gdisconnect()
        return redirect(url_for('all'))
    else:
        return render_template("edit.html", tool=tool,
                               user_id=login_session['user_id'])


@app.route('/tools/<int:tool_id>/delete/', methods=['GET', 'POST'])
def delete_tool(tool_id):
    # Users must log in to see this view.
    if login_session['access_token'] is None:
        return redirect(url_for("login"))

    tool = Tool.query.filter_by(id=tool_id).one()
    if request.method == 'POST':
        if login_session['user_id'] == tool.user_id:
            db.session.delete(tool)
            db.session.commit()
            return redirect(url_for('all'))
        else:
            flash("""You do not have permission to edit this tool and you
                     could not have accessed it non-maliciously. You will
                     now be logged out.""")

            gdisconnect()
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
