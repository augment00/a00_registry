import unittest
import json

# from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.ext import testbed

from models import Person, Entity, Name
from utilities.firebase import create_custom_token
import utilities.keys as keys


class ModelsTestCase(unittest.TestCase):

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()

        self.policy = testbed.datastore_stub_util.PseudoRandomHRConsistencyPolicy(probability=0)
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub(consistency_policy=self.policy)
        self.testbed.init_memcache_stub()
        # Clear ndb's in-context cache between tests.
        # This prevents data from leaking between tests.
        # Alternatively, you could disable caching by
        # using ndb.get_context().set_cache_policy(False)
        ndb.get_context().clear_cache()


    def tearDown(self):
        self.testbed.deactivate()


    def testAddPerson(self):

        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        self.assertIsNotNone(person)
        key = person.key
        got = key.get()
        self.assertIsNotNone(got)


    def testAddPersonWithSameName(self):

        Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        self.assertRaises(Exception, Person.create, "paul", "paul2@glowinthedark.co.uk", "1234567890")


    def testChangeName(self):

        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        # self.assertEqual(1, len(Name.query().fetch(2)))
        self.assertEqual(person.name, "paul")
        person.name = "sol"
        self.assertEqual(person.name, "sol")

        name_key = ndb.Key(Name, "sol")
        existing_name = name_key.get()
        self.assertIsNotNone(existing_name)


    def testChangeNameFail(self):

        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        person2 = Person.create("sol", "sol@glowinthedark.co.uk", "987654321")
        # self.assertEqual(1, len(Name.query().fetch(2)))
        self.assertEqual(person.name, "paul")
        self.assertEqual(person2.name, "sol")

        self.assertRaises(Exception, person.set_name, "sol")


class ModelsTestCaseWithoutConsistancy(unittest.TestCase):

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()

        # self.policy = testbed.datastore_stub_util.PseudoRandomHRConsistencyPolicy(probability=0)
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_app_identity_stub()
        # Clear ndb's in-context cache between tests.
        # This prevents data from leaking between tests.
        # Alternatively, you could disable caching by
        # using ndb.get_context().set_cache_policy(False)
        ndb.get_context().clear_cache()


    def tearDown(self):
        self.testbed.deactivate()


    def testFindByEmail(self):
        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        found = Person.with_email("paul@glowinthedark.co.uk")
        self.assertEqual(found.name, "paul")


    def testFindByName(self):
        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        found = Person.with_name("paul")
        self.assertEqual(found.name, "paul")


    def testFindByGoogleId(self):
        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        found = Person.with_google_id("123456789")
        self.assertEqual(found.name, "paul")


    def testFindByGoogleIdNotExisting(self):
        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        found = Person.with_google_id("asdfghjk")
        self.assertTrue(found is None)


    def testAddNewEntity(self):
        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        entity = person.add_new_entity(name="elephant")


    def testpersonEntities(self):
        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        entity = person.add_new_entity(name="elephant")
        entities = person.entities
        self.assertTrue(len(entities) == 1)


    def testAddConfigFile(self):
        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        entity = person.add_new_entity(name="elephant")

        config_file = person.add_config_file("test", "a whole bunch of text", "a/path/file.txt")

        entity.add_config_file(config_file)
        self.assertTrue(len(entity.config) == 1)
        self.assertEqual(entity.config[0].get().text, "a whole bunch of text")
        entity.add_config_file(config_file)
        self.assertTrue(len(entity.config) == 1)

        config_file_2 = person.add_config_file("test2", "another a whole bunch of text", "a/path/file.txt")
        entity.add_config_file(config_file_2)
        self.assertTrue(len(entity.config) == 2)

        configs = person.configs
        self.assertTrue(len(configs) == 2)


    def testRemoveConfigFile(self):
        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        entity = person.add_new_entity(name="elephant")

        config_file = person.add_config_file("test", "a whole bunch of text", "a/path/file.txt")

        entity.add_config_file(config_file)
        self.assertTrue(len(entity.config) == 1)
        self.assertEqual(entity.config[0].get().text, "a whole bunch of text")
        entity.add_config_file(config_file)
        self.assertTrue(len(entity.config) == 1)

        config_file_2 = person.add_config_file("test2", "another a whole bunch of text", "a/path/file.txt")
        entity.add_config_file(config_file_2)
        self.assertTrue(len(entity.config) == 2)
        entity.remove_config_file(config_file_2)
        self.assertTrue(len(entity.config) == 1)


    def test_signing(self):

        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        entity = person.add_new_entity(name="elephant")
        url = "https://augment00.org/entity/12345678"
        salt = "asdfghjkl"
        sig = keys.sign_url(url, entity.private_key, salt)
        mine = keys.verify_sig(url, sig, entity.public_key, salt)
        self.assertTrue(mine)


    def test_signing_fails(self):

        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        entity = person.add_new_entity(name="elephant")
        url = "https://augment00.org/entity/12345678"
        salt = "asdfghjkl"
        sig = keys.sign_url(url, entity.private_key, salt)
        mine = keys.verify_sig(url, sig, entity.public_key, "123456")
        self.assertFalse(mine)


    def test_entity_json(self):

        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        entity = person.add_new_entity(name="elephant")
        config_file = person.add_config_file("test", "A whole bunch of text\nwith a line return", "a/path/file.txt")
        entity.add_config_file(config_file)
        as_json = entity.as_json()

        as_json_string = json.dumps(entity.as_json(), indent=4)

        loaded = json.loads(as_json_string)

        self.assertEqual(loaded["config"][0]["text"], "A whole bunch of text\nwith a line return")



    def test_config_templating(self):

        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        entity = person.add_new_entity(name="elephant")
        config_file = person.add_config_file("test", "A whole bunch of text\nwith uuid {{ uuid }}", "a/path/file.txt")
        entity.add_config_file(config_file)
        as_json = entity.as_json()

        as_json_string = json.dumps(entity.as_json(), indent=4)

        loaded = json.loads(as_json_string)

        self.assertEqual(loaded["config"][0]["text"], "A whole bunch of text\nwith uuid %s" % entity.key.id())


    def test_config_firebase(self):

        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        entity = person.add_new_entity(name="elephant")
        config_file = person.add_config_file("test", '{"firebase": "{{ firebase }}"}', "a/path/file.txt")
        entity.add_config_file(config_file)
        as_json = entity.as_json()

        as_json_string = json.dumps(entity.as_json(), indent=4)

        loaded = json.loads(as_json_string)

        as_json = json.loads(loaded["config"][0]["text"])


    def test_token(self):
        entity_uuid = "1020e9bd-cab6-4182-8b17-31d1b5851876"
        token = create_custom_token(entity_uuid)
