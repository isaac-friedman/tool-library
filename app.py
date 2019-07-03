from flask import Flask, request, render_template, url_for, redirect, flash, jsonify

from config import Config

app = Flask(__name__)

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
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
