import logging
import json


from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.ext import ndb


from flask import Flask, request, redirect, flash

from constants import *

app = Flask(__name__)

app.secret_key = FLASK_SECRET_KEY

from models import Person, Entity, ConfigFile
from forms import PersonForm, EntityForm, ConfigForm
from shared import render_login_template, with_person
from augment_exceptions import NonUniqueException


@app.route('/person/new', methods=["POST", "GET"])
def new_person():
    google_user = users.get_current_user()
    if google_user is not None:
        google_id = google_user.user_id()
        existing_user = Person.with_google_id(google_id)
        if existing_user is None:
            form = PersonForm(request.form)
            if request.method == 'POST':
                email = form.email.data
                name = form.name.data
                try:
                    Person.create(name, email, google_id)
                    flash("New account created.", "success")
                    return redirect("/")
                except NonUniqueException as e:
                    flash("Failed to create new account. %s" % e.message, "warning")
                    return redirect("/")
            else:
                return render_login_template("account-form.html", form=form)
        else:
            flash("Welcome back", "info")
            return redirect("/")
    else:
        return redirect("/")



@app.route('/person/update', methods=["POST", "GET"])
@with_person
def update_person(person=None):

    form = PersonForm(request.form, name=person.name, email=person.email)
    if request.method == 'POST':
        email = form.email.data
        name = form.name.data
        try:
            person.name = name
            person.email = email

            return redirect("/person/account")
        except NonUniqueException as e:
            flash("We couldn't update your account account. %s" % e.message, "warning")
            redirect("/person/new")
    else:
        return render_login_template("account-form.html", form=form)



@app.route('/person/delete', methods=["POST"])
@with_person
def delete_person(person=None):
    person.remove()
    return redirect("/")


## CRUD for entities

@app.route('/entity/new', methods=["POST", "GET"])
@with_person
def new_entity(person=None):
    form = EntityForm(request.form)

    form.configs.choices = [(c.key, c.name) for c in person.configs]

    if request.method == 'POST':

        entity, private_key = person.add_new_entity(name=form.name.data,
                                       description=form.description.data
                                       )
        entity_uuid = entity.key.id()
        memcache.add(entity_uuid, private_key, time=5, namespace="private")
        flash("Take a copy of the credentials below as you won't see them again", "info")
        return redirect("/entity/%s" % entity_uuid)
    else:
        return render_login_template("entity-form.html", form=form)


def _allowed_entity(entity_uuid, person):

    entity = Entity.get_by_id(entity_uuid)
    if entity is None:
        flash("We couldn't find this entity", "warning")
        return None, redirect("/")
    else:
        if entity.person_key == person.key:
            return entity, None
        else:
            flash("You can only see your own entities", "info")
            return None, redirect("/")



@app.route('/entity/<entity_uuid>', methods=["GET"])
@with_person
def entity(entity_uuid, person=None):

    entity, rsp = _allowed_entity(entity_uuid, person)
    if entity is None:
        return rsp

    private_key = memcache.get(entity_uuid, namespace="private")
    path = "/api/config/%s" % entity.key.id()
    base = URL_BASE
    if private_key is not None:
        creds_json = {
            "entity_uuid": entity_uuid,
            "private_key": private_key,
            "url": "%s%s" % (base, path)
        }
        creds = json.dumps(creds_json, indent=4)
    else:
        creds = None

    tag = entity_uuid[:8]

    return render_login_template("entity.html", entity=entity, person=person, creds=creds, tag=tag)



@app.route('/entity/<entity_uuid>/update', methods=["POST", "GET"])
@with_person
def update_entity(entity_uuid, person=None):

    entity, rsp = _allowed_entity(entity_uuid, person)
    if entity is None:
        return rsp

    form = EntityForm(request.form,
                      name=entity.name,
                      description=entity.description
                      )
    form.configs.choices = [(c.key.id(), c.name) for c in person.configs]

    if request.method == 'POST':
        entity.config = [ndb.Key("ConfigFile", k, parent=person.key) for k in form.configs.data]
        entity.name = form.name.data
        entity.description = form.description.data
        entity.put()

        return redirect("/entity/%s" % entity_uuid)
    else:
        return render_login_template("entity-form.html", form=form)


@app.route('/entity/<entity_uuid>/delete', methods=["POST"])
@with_person
def delete_entity(entity_uuid, person=None):

    entity, rsp = _allowed_entity(entity_uuid, person)
    if entity is None:
        return rsp

    entity.key.delete()
    return redirect("/")


@app.route('/entity/<entity_uuid>/regenerate', methods=["POST"])
@with_person
def regenerate(entity_uuid, person=None):

    entity, rsp = _allowed_entity(entity_uuid, person)
    if entity is None:
        return rsp

    private_key = entity.regenerate_keys()
    memcache.add(entity_uuid, private_key, time=5, namespace="private")
    flash("Take a copy of the credentials below as you won't see them again", "info")
    return redirect("/entity/%s" % entity_uuid)


## CRUD for config


def _allowed_config(config_uuid, person):
    config_file = ConfigFile.get_by_id(config_uuid, parent=person.key)
    if config_file is None:
        flash("We couldn't find this config file", "warning")
        return None, redirect("/")
    else:
        if config_file.key.parent() == person.key:
            return config_file, None
        else:
            flash("You can only see your own config files", "warning")
            return redirect("/")


@app.route('/config/<config_uuid>', methods=["POST", "GET"])
@with_person
def config(config_uuid, person=None):

    config_file, rsp = _allowed_config(config_uuid, person)
    if config_file is None:
        return rsp

    return render_login_template("config-file.html", config=config_file, person=person)


@app.route('/config/<config_uuid>/update', methods=["POST", "GET"])
@with_person
def update_config(config_uuid, person=None):

    config_file, rsp = _allowed_config(config_uuid, person)
    if config_file is None:
        return rsp

    form = ConfigForm(request.form,
                      name=config_file.name,
                      path=config_file.path,
                      file_text=config_file.text
                      )

    if request.method == 'POST':
        config_file.name = form.name.data
        config_file.path = form.path.data
        config_file.text = form.file_text.data
        config_file.put()

        return redirect("/config/%s" % config_uuid)
    else:
        return render_login_template("config-form.html", form=form, config=config_file)


@app.route('/config/<config_uuid>/delete', methods=["POST"])
@with_person
def delete_config(config_uuid, person=None):

    config_file, rsp = _allowed_config(config_uuid, person)
    if config_file is None:
        return rsp

    config_file.key.delete()

    return redirect("/")


@app.route('/config/new', methods=["POST", "GET"])
@with_person
def new_config(person=None):

    form = ConfigForm(request.form)

    if request.method == 'POST':

        config = person.add_config_file(form.name.data,
                                        form.file_text.data,
                                        form.path.data
                                        )

        config_uuid = config.key.id()
        return redirect("/config/%s" % config_uuid)

    else:
        return render_login_template("config-form.html", form=form)






@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500














