import json
import base64
import time
import datetime
import httplib2

from google.appengine.api import app_identity


from constants import FIREBASE_URL

_FIREBASE_SCOPES = [
    'https://www.googleapis.com/auth/firebase.database',
    'https://www.googleapis.com/auth/userinfo.email']

_IDENTITY_ENDPOINT = ('https://identitytoolkit.googleapis.com/google.identity.identitytoolkit.v1.IdentityToolkit')


def create_custom_token(uid, valid_minutes=60):
    """Create a secure token for the given id.

    This method is used to create secure custom JWT tokens to be passed to
    clients. It takes a unique id (uid) that will be used by Firebase's
    security rules to prevent unauthorized access. In this case, the uid will
    be the channel id which is a combination of user_id and game_key
    """

    # use the app_identity service from google.appengine.api to get the
    # project's service account email automatically
    client_email = app_identity.get_service_account_name()

    # print "client_email: ", client_email

    now = int(time.time())
    # encode the required claims
    # per https://firebase.google.com/docs/auth/server/create-custom-tokens
    payload = base64.b64encode(json.dumps({
        'iss': client_email,
        'sub': client_email,
        'aud': _IDENTITY_ENDPOINT,
        'uid': uid,  # the important parameter, as it will be the channel id
        'iat': now,
        'exp': now + (valid_minutes * 60),
    }))
    # add standard header to identify this as a JWT
    header = base64.b64encode(json.dumps({'typ': 'JWT', 'alg': 'RS256'}))
    to_sign = '{}.{}'.format(header, payload)
    # Sign the jwt using the built in app_identity service
    return '{}.{}'.format(to_sign, base64.b64encode(app_identity.sign_blob(to_sign)[1]))



def _get_http():
    from oauth2client.client import GoogleCredentials
    # from oauth2client.client import GoogleCredentials
    """Provides an authed http object."""
    http = httplib2.Http()
    # Use application default credentials to make the Firebase calls
    # https://firebase.google.com/docs/reference/rest/database/user-auth
    creds = GoogleCredentials.get_application_default().create_scoped(_FIREBASE_SCOPES)
    creds.authorize(http)
    return http



def firebase_put(path, value=None):
    """Writes data to Firebase.

    An HTTP PUT writes an entire object at the given database path. Updates to
    fields cannot be performed without overwriting the entire object

    Args:
        path - the url to the Firebase object to write.
        value - a json string.
    """
    response, content = _get_http().request(path, method='PUT', body=value)
    return json.loads(content)



def send_message(u_id, command_json=None):

    url = '{}/channels/{}.json'.format(FIREBASE_URL, u_id)

    dt = datetime.datetime.now()
    ts = dt.strftime("%Y%m%d-%H%M%S-%f")
    message_json = {
        ts: command_json
    }

    message =  json.dumps(message_json, indent=4)

    if message:
        return _get_http().request(url, 'PATCH', body=message)
    else:
        return _get_http().request(url, 'DELETE')