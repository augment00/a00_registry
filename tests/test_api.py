import unittest
import json

# from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.ext import testbed

from models import Person, Entity, Name



import api


class ApiTestCase(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.app = api.app.test_client()
        ndb.get_context().clear_cache()


    def tearDown(self):
        self.testbed.deactivate()


    def testAddEntity(self):
        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        found = Person.with_email("paul@glowinthedark.co.uk")
        self.assertEqual(found.name, "paul")

        self.assertTrue(person.api_key is not None)

        data = {
            "user_id": person.get_google_id(),
            "api_key": person.api_key,
            "name": "test",
            "description": "fishcakes"
        }

        url = "/api/new-entity"

        rsp = self.app.post(url, data=json.dumps(data))
        self.assertTrue(rsp.status_code == 201)

        entity_uuid = rsp.data
        entity = Entity.get_by_id(entity_uuid)
        self.assertTrue(entity is not None)

        return person, entity


    def testAddValue(self):
        person, entity = self.testAddEntity()

        entity_uuid = entity.key.id()


        data = {
            "user_id": person.get_google_id(),
            "api_key": person.api_key,
            "name": "test",
            "value": "fishfinger"
        }

        url = "/api/entity/%s/add-value" % entity_uuid

        rsp = self.app.post(url, data=json.dumps(data))
        print rsp.status_code
        self.assertTrue(rsp.status_code == 200)

        entity = Entity.get_by_id(entity_uuid)

        self.assertEqual(entity.template_values["test"], "fishfinger")


    def testSendCommand(self):

        person, entity = self.testAddEntity()

        entity_uuid = entity.key.id()


        data = {
            "user_id": person.get_google_id(),
            "api_key": person.api_key,
            "name": "test",
            "value": "fishfinger"
        }

        url = "/api/entity/%s/add-value" % entity_uuid

        rsp = self.app.post(url, data=json.dumps(data))
        print rsp.status_code
        self.assertTrue(rsp.status_code == 200)

        entity = Entity.get_by_id(entity_uuid)

        self.assertEqual(entity.template_values["test"], "fishfinger")



