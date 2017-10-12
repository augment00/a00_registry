import logging
import json
from functools import wraps

from google.appengine.ext import ndb

from flask import Flask, request
app = Flask(__name__)

from models import Entity, Person
from utilities import firebase, keys

from constants import *


def is_signed(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        path = request.path
        print path
        sig = request.values.get("sig")
        if sig is None:
            print "no sig"
            return ("Permission denied", 401, {})
        parts = path.split("/")
        entity_uuid = parts[-2]
        key = ndb.Key("Entity", entity_uuid)
        entity = key.get()
        if entity is None:
            return ("Not found", 403, {})
        ok = keys.verify_sig(path, sig, entity.public_key)
        if not ok:
            print "not ok"
            return ("Permission denied", 401, {})
        return func(*args, entity=entity, **kwargs)
    return decorated_view


def with_api_key(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        as_json = request.get_json(force=True)
        if as_json is None:
            print "no json"
            return ("Permission denied, no json data", 401, {})
        google_id = as_json.get("user_id")
        api_key = as_json.get("api_key")
        if google_id is None or api_key is None:
            return ("Permission denied", 401, {})

        person = Person.with_google_id(google_id)
        if person is None:
            return ("Permission denied", 401, {})

        if person.api_key != api_key:
            return ("Permission denied", 401, {})

        return func(*args, person=person, **kwargs)
    return decorated_view


@app.route('/api/config/<entity_uuid>/<nonce>', methods=["GET"])
@is_signed
def api_config(entity_uuid, nonce, entity=None):

    serial = request.values.get("serial")
    if entity.serial is not None and serial != entity.serial:
        return ("Conflict - Serial doesn't match", 409, {})
    else:
        if entity.serial is None:
            entity.serial = serial
            entity.put()

        return json.dumps(entity.as_json())


@app.route('/api/firebase-token/<entity_uuid>/<nonce>', methods=["GET"])
@is_signed
def api_token(entity_uuid, nonce, entity=None):

    data = {
        "entity_uuid": entity_uuid,
        "firebase_custom_token": firebase.create_custom_token(entity_uuid)
    }

    return json.dumps(data)


@app.route('/api/schema/<entity_uuid>', methods=["POST"])
def set_entity_schema(entity_uuid):
    key = ndb.Key("Entity", entity_uuid)
    entity = key.get()
    if entity is None:
        return "not found", 403
    else:
        as_json = request.get_json(force=True)
        entity.schema = as_json
        entity.put()
        return "ok", 200


############################################################



@app.route('/api/new-entity', methods=["POST"])
@with_api_key
def new_entity(person=None):
    as_json = request.get_json(force=True)
    entity = Entity.create(person.key, name=as_json["name"])
    entity_uuid = entity.key.id()
    return entity_uuid, 201


@app.route('/api/entity/<entity_uuid>/schema', methods=["GET"])
@with_api_key
def get_entity_schema(entity_uuid, person=None):

    key = ndb.Key("Entity", entity_uuid)
    entity = key.get()

    if entity is None:
        return "not found", 403

    if entity.person_key != person.key:
        return ("Permission denied", 401, {})

    return json.dumps(entity.schema), 200


@app.route('/api/entity/<entity_uuid>/add-value', methods=["POST"])
@with_api_key
def add_value(entity_uuid, person=None):

    key = ndb.Key("Entity", entity_uuid)
    entity = key.get()

    if entity.person_key != person.key:
        return ("Permission denied", 401, {})

    as_json = request.get_json(force=True)

    value_name = as_json["name"]
    value = as_json["value"]

    if value_name == "name":
        entity.name = value
    else:
        entity.template_values[value_name] = value

    entity.put()
    return "ok", 200


@app.route('/api/entity/<entity_uuid>/send-command', methods=["POST"])
@with_api_key
def send_command(entity_uuid, person=None):

    key = ndb.Key("Entity", entity_uuid)
    entity = key.get()

    if entity.person_key != person.key:
        return ("Permission denied", 401, {})

    as_json = request.get_json(force=True)

    if not frozenset(as_json["rpc"].keys()) == {"method", "params"}:

        return ("Malformed request", 400, {})

    firebase_service = firebase.get_service()
    firebase_service.send_message(entity_uuid, command_json=as_json["rpc"])

    return "ok", 200


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500