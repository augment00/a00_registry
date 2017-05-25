
import uuid
from Crypto.PublicKey import RSA
from google.appengine.ext import ndb
from google.appengine.api import users


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
        person_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, REGISTRY_DOMAIN))
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
    def withEmail(cls, email):
        key = ndb.Key(Email, email)
        return cls.query(cls.email_key == key).get()

    @classmethod
    def withName(cls, name):
        key = ndb.Key(Name, name)
        return cls.query(cls.name_key == key).get()

    @classmethod
    def withGoogleId(cls, google_id):
        key = ndb.Key(GoogleId, google_id)
        return cls.query(cls.google_id_key == key).get()

    @staticmethod
    def _new_unique_key(attribute_class, new_value):

        new_attribute_key = ndb.Key(attribute_class, new_value)
        existing_attribute_obj = new_attribute_key.get()

        if existing_attribute_obj is not None:
            raise Exception("The value %s for %s is adready in use" % (new_value, attribute_class))
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
        entity = Entity.create(self.key, **kwargs)
        return entity


    name = property(get_name, set_name)
    email = property(get_email, set_email)
    google_id = property(get_google_id)


class ConfigFile(ndb.Model):

    text = ndb.TextProperty()
    path = ndb.StringProperty()
    owner = ndb.StringProperty()
    mod = ndb.StringProperty()


class Entity(ndb.Model):

    name = ndb.StringProperty()
    short_description = ndb.StringProperty()
    long_description = ndb.TextProperty()
    url = ndb.StringProperty()
    image_url = ndb.StringProperty()

    created = ndb.DateTimeProperty(auto_now_add=True)
    person_key = ndb.KeyProperty(kind="Person", required=True)
    public_key = ndb.TextProperty()
    private_key = ndb.TextProperty()

    config = ndb.StructuredProperty(ConfigFile, repeated=True)


    def add_config_file(self, text, path, owner, mod):
        config_file = ConfigFile(text=text, path=path, owner=owner, mod=mod)
        self.config.append(config_file)
        self.put()


    def remove_config_file(self, index):
        del self.config[index]
        self.put()


    @classmethod
    def create(cls, person_key, **kwargs):

        key = RSA.generate(4096)
        pubkey = key.publickey()

        private_key = key.exportKey('PEM')
        public_key = pubkey.exportKey('OpenSSH')

        entity_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, REGISTRY_DOMAIN))
        entity = cls(id=entity_uuid,
                     person_key=person_key,
                     private_key=private_key,
                     public_key=public_key,
                     **kwargs)
        entity.put()

        return entity








