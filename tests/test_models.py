import unittest

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.ext import testbed

from models import Person, Entity, Name


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
        # Clear ndb's in-context cache between tests.
        # This prevents data from leaking between tests.
        # Alternatively, you could disable caching by
        # using ndb.get_context().set_cache_policy(False)
        ndb.get_context().clear_cache()


    def tearDown(self):
        self.testbed.deactivate()


    def testFindByEmail(self):
        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        found = Person.withEmail("paul@glowinthedark.co.uk")
        self.assertEqual(found.name, "paul")


    def testFindByName(self):
        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        found = Person.withName("paul")
        self.assertEqual(found.name, "paul")


    def testFindByGoogleId(self):
        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        found = Person.withGoogleId("123456789")
        self.assertEqual(found.name, "paul")


    def testFindByGoogleIdNotExisting(self):
        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        found = Person.withGoogleId("asdfghjk")
        self.assertTrue(found is None)


    def testAddNewEntity(self):
        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        entity = person.add_new_entity(name="elephant")


    def testAddConfigFile(self):
        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        entity = person.add_new_entity(name="elephant")
        entity.add_config_file("test text", "/etc/thing/config.py", "owner", "755")
        self.assertTrue(len(entity.config) == 1)
        self.assertEqual(entity.config[0].text, "test text")
        entity.add_config_file("another test text", "/etc/thing/config.py", "me", "755")
        self.assertTrue(len(entity.config) == 2)

