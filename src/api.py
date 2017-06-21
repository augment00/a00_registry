import logging
import json
from functools import wraps

from google.appengine.ext import ndb

from flask import Flask, request
app = Flask(__name__)

from models import Entity
import firebase
import keys


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


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500