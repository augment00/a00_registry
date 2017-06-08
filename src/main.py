import logging

from google.appengine.api import users

from flask import Flask, redirect, flash

from constants import *

app = Flask(__name__)

app.secret_key = FLASK_SECRET_KEY

from shared import render_login_template, with_person
from models import Person


@app.route('/', methods=["GET"])
def home():
    google_user = users.get_current_user()
    if google_user is not None:
        google_id = google_user.user_id()
        person = Person.with_google_id(google_id)
        if person is not None:
            return render_login_template("account.html", person=person)
        else:
            flash("choose a name and email to use with your augment00 account", "info")
            return redirect("/person/new")
    else:
        return render_login_template("intro.html")


@app.route('/about', methods=["GET"])
def about():
    google_user = users.get_current_user()
    if google_user is not None:
        google_id = google_user.user_id()
        person = Person.with_google_id(google_id)
    else:
        person = None

    return render_login_template("about.html", person=person)


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500