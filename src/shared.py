from functools import wraps

from flask import Flask, render_template, redirect, request

from google.appengine.api import users

from models import Person




def render_login_template(template, **kwargs):

    user = users.get_current_user()
    if user:
        login_url = users.create_logout_url(request.url)
        url_linktext = 'logout'
    else:
        login_url = users.create_login_url(request.url)
        url_linktext = 'login'

    return render_template(template, login_url=login_url, url_linktext=url_linktext, **kwargs)


def with_person(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        google_user = users.get_current_user()
        if google_user is not None:
            google_id = google_user.user_id()
            person = Person.with_google_id(google_id)
            if person is None:
                return redirect("/")
            else:
                return func(*args, person=person, **kwargs)
        else:
            raise Exception("no google user in new_person")
    return decorated_view
