import requests_shim as requests
import json
import config_local


class AivenAuthException(Exception):
    pass


def auth(func):
    def func_wrapper(instance, *args, **kwargs):
        try:
            return func(instance, *args, **kwargs)
        except AivenAuthException:
            instance.authenticate()
            return func(instance, *args, **kwargs)
    return func_wrapper


class AivenInfluxService(object):


    def __init__(self, project_name, service_name, email, password):

        self.project_name = project_name
        self.service_name = service_name
        self.email = email
        self.password = password
        self.access_token = None


    def db_names(self):

        info = self.get_info()
        return info["service"]["databases"]


    def headers(self):

        return {
            "content-type": "application/json",
            "Authorization": "aivenv1 %s" % self.access_token
        }

    @auth
    def get_info(self):

        url = "https://api.aiven.io/v1beta/project/%s/service/%s" % (self.project_name, self.service_name)
        rsp = requests.get(url, headers=self.headers())

        if rsp.status_code == 200:
            return rsp.json()
        if rsp.status_code == 401:
            print "auth fail"
            raise AivenAuthException("auth fail")

        return None


    def ensure_db(self, db_name):

        existing_dbs = self.db_names()

        if not db_name in existing_dbs:
            return self.create_new_db(db_name)

        return True

    @auth
    def delete_db(self, db_name):

        url = "https://api.aiven.io/v1beta/project/%s/service/%s/db/%s" % (self.project_name, self.service_name, db_name)
        rsp = requests.delete(url, headers=self.headers())

        if rsp.status_code == 200:
            return True
        if rsp.status_code == 403:
            return True
        if rsp.status_code == 401:
            raise AivenAuthException("auth fail")

        return False


    @auth
    def delete_user(self, user_name):

        url= "https://api.aiven.io/v1beta/project/%s/service/%s/user/%s" % (self.project_name, self.service_name, user_name)

        rsp = requests.delete(url, headers=self.headers())

        if rsp.status_code == 200:
            return True
        if rsp.status_code == 401:
            raise AivenAuthException("auth fail")

        return False


    def get_user(self, user_name):

        info = self.get_info()
        users = info["service"]["users"]

        for user in users:
            if user["username"] == user_name:
                return user

        return None


    @auth
    def new_user(self, user_name):

        url= "https://api.aiven.io/v1beta/project/%s/service/%s/user" % (self.project_name, self.service_name)

        data = {
            "username": user_name
        }

        rsp = requests.post(url, json=data, headers=self.headers())
        print rsp.status_code
        print rsp.content

        if rsp.status_code == 200:
            return rsp.json()
        if rsp.status_code == 403:
            return {}
        if rsp.status_code == 401:
            raise AivenAuthException("auth fail")

        return None

    @auth
    def create_new_db(self, db_name):

        url = "https://api.aiven.io/v1beta/project/%s/service/%s/db" % (self.project_name, self.service_name)

        data = {
            "database": db_name
        }

        rsp = requests.post(url, json=data, headers=self.headers())

        if rsp.status_code == 200:
          return True
        if rsp.status_code == 401:
            raise AivenAuthException("auth fail")

        return False


    def authenticate(self):

        url = "https://api.aiven.io/v1beta/userauth"

        data = {
          "email": self.email,
          "password": self.password
        }

        headers = {"content-type": "application/json"}

        rsp = requests.post(url, json=data, headers=headers)

        if rsp.status_code == 200:
            self.access_token = rsp.json()["token"]

        else:
            raise Exception("failed to get aiven access token")


    def influx_password_for_entity(self, entity_uuid):

        self.new_user(entity_uuid)
        user = self.get_user(entity_uuid)
        return user["password"]


def add_influx_password(entity):

    if hasattr(config_local, "AIVEN_PROJECT"):

        if entity.template_values is None:
            entity.template_values = {}

        if entity.template_values.get("influx_password") is None:
            aiven_service = AivenInfluxService(config_local.AIVEN_PROJECT,
                                               config_local.AIVEN_SERVICE,
                                               config_local.AIVEN_EMAIL,
                                               config_local.AIVEN_PASSWORD)

            entity_uuid = entity.key.id()
            entity.template_values["influx_password"] = aiven_service.influx_password_for_entity(entity_uuid)
            entity.put()


