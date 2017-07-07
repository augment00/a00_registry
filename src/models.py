
import uuid
from Crypto.PublicKey import RSA
from google.appengine.ext import ndb
from google.appengine.api import users
from base64 import b64encode, b64decode
from jinja2 import Template

from utilities import firebase, keys

from augment_exceptions import NonUniqueException
from constants import *


class Name(ndb.Model):
    pass


class Email(ndb.Model):
    pass


class GoogleId(ndb.Model):
    pass


class Person(ndb.Model):
    name_key = ndb.KeyProperty(kind="Name", required=True)
    email_key = ndb.KeyProperty(kind="Email", required=True)
    google_id_key = ndb.KeyProperty(kind="GoogleId")


    @classmethod
    def create(cls, name, email, google_id):
        name_key = cls._new_unique_key(Name, name)
        email_key = cls._new_unique_key(Email, email)
        google_id_key = cls._new_unique_key(GoogleId, google_id)
        person_uuid = str(uuid.uuid4())
        person = cls(name_key=name_key, email_key=email_key, google_id_key=google_id_key, id=person_uuid)
        person.put()
        return person

    def get_name(self):
        return self.name_key.id()

    def set_name(self, new_name):
        self._set_unique_attribute(Name, "name_key", new_name)

    def get_email(self):
        return self.email_key.id()

    def set_email(self, new_email):
        self._set_unique_attribute(Email, "email_key", new_email)

    def get_google_id(self):
        return self.google_id_key.id()

    @classmethod
    def with_email(cls, email):
        key = ndb.Key(Email, email)
        return cls.query(cls.email_key == key).get()

    @classmethod
    def with_name(cls, name):
        key = ndb.Key(Name, name)
        return cls.query(cls.name_key == key).get()

    @classmethod
    def with_google_id(cls, google_id):
        key = ndb.Key(GoogleId, google_id)
        return cls.query(cls.google_id_key == key).get()

    @staticmethod
    def _new_unique_key(attribute_class, new_value):

        new_attribute_key = ndb.Key(attribute_class, new_value)
        existing_attribute_obj = new_attribute_key.get()

        if existing_attribute_obj is not None:
            raise NonUniqueException("The value %s for %s is adready in use" % (new_value, attribute_class))
        else:
            new_attribute_obj = attribute_class(key=new_attribute_key)
            new_attribute_obj.put()

        return new_attribute_key


    @ndb.transactional(xg=True)
    def _set_unique_attribute(self, attribute_class, attribute_key_name, new_value):

        current_attribute_key = getattr(self, attribute_key_name)
        current_value = current_attribute_key.id()

        if current_value == new_value:
            return

        new_attribute_key = self._new_unique_key(attribute_class, new_value)
        current_attribute_key.delete()
        setattr(self, attribute_key_name, new_attribute_key)
        self.put()


    def add_new_entity(self, **kwargs):
        entity, private_key = Entity.create(self.key, **kwargs)
        return entity, private_key


    @property
    def entities(self):
        return [e for e in Entity.query(Entity.person_key == self.key).iter()]

    @property
    def configs(self):
        return [c for c in ConfigFile.query(ancestor=self.key).iter()]


    def remove(self):
        ndb.delete_multi(ConfigFile.query(ancestor=self.key).iter(keys_only=True))
        ndb.delete_multi(Entity.query(Entity.person_key == self.key).iter(keys_only=True))
        self.name_key.delete()
        self.email_key.delete()
        self.google_id_key.delete()
        self.key.delete()

    def add_config_file(self, name, text, path):

        config_uuid = str(uuid.uuid4())

        config_file = ConfigFile(id=config_uuid,
                                 parent=self.key,
                                 name=name,
                                 text=text,
                                 path=path)
        config_file.put()
        return config_file


    name = property(get_name, set_name)
    email = property(get_email, set_email)
    google_id = property(get_google_id)


class ConfigFile(ndb.Model):

    name = ndb.StringProperty()
    text = ndb.TextProperty()
    path = ndb.StringProperty()

    def as_json(self, entity):

        entity_uuid = entity.key.id()
        template_values = entity.template_values

        template = Template(self.text)

        return {
            "text": template.render(uuid=entity_uuid, **template_values),
            "path": self.path
        }


class Entity(ndb.Model):

    name = ndb.StringProperty()
    description = ndb.TextProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    person_key = ndb.KeyProperty(kind="Person", required=True)
    public_key = ndb.TextProperty()
    serial = ndb.StringProperty()
    config = ndb.KeyProperty(ConfigFile, repeated=True)
    template_values = ndb.JsonProperty(default={})


    def as_json(self):

        entity_uuid = self.key.id()

        return {
            "name": self.name,
            "description": self.description,
            "created": str(self.created),
            "person_key": self.person_key.id(),
            "public_key": self.public_key,
            "config": [c.get().as_json(self) for c in self.config]
        }

    @property
    def config_files(self):
        configs = [c.get() for c in self.config]
        return configs

    def add_config_file(self, config_file):
        key = config_file.key
        if not key in self.config:
            self.config.append(key)
            self.put()


    def remove_config_file(self, config_file):
        key = config_file.key
        if key in self.config:
            self.config.remove(key)
            self.put()


    def regenerate_keys(self):
        public, private = keys.newkeys(2048)
        private_key = private.exportKey('PEM')
        self.public_key = public.exportKey('PEM')
        self.put()

        return private_key

    @classmethod
    def create(cls, person_key, **kwargs):

        public, private = keys.newkeys(2048)
        private_key = private.exportKey('PEM')
        public_key = public.exportKey('PEM')

        entity_uuid = str(uuid.uuid4())
        entity = cls(id=entity_uuid,
                     person_key=person_key,
                     public_key=public_key,
                     **kwargs)
        entity.put()

        return entity, private_key








