import unittest
import urllib
import os
import shutil
from urlparse import urlparse
import json

from google.appengine.ext import ndb
from google.appengine.ext import testbed

import api

from models import Person

from augment00_bootstrap import main as bootstrap

THIS_DIR = os.path.dirname(__file__)
TEMP_DIR = os.path.join(THIS_DIR, "data", "temp")

class TestEntityApi(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.app = api.app.test_client()
        ndb.get_context().clear_cache()

        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
        os.makedirs(TEMP_DIR)


    def tearDown(self):
        self.testbed.deactivate()


    def test_entity_get_config(self):
        person = Person.create("paul", "paul@glowinthedark.co.uk", "123456789")
        entity, private_pem = person.add_new_entity(name="elephant")
        config_file = person.add_config_file("test", "A whole bunch of text\nwith a line return", "a/path/file.txt")
        entity.add_config_file(config_file)

        entity_uuid = entity.key.id()

        creds = {
            "private_key": private_pem,
            "entity_uuid": entity_uuid,
            "url": "http://augment00.org/api/config/%s" % entity_uuid
        }

        url = bootstrap.config_url(creds)
        # strip off the fron for testing with app
        pp = urlparse(url)
        url = "%s?%s" % (pp.path, pp.query)

        response = self.app.get(url)
        self.assertEqual(response.status_code, 200)

        as_dict = json.loads(response.data)

        self.assertEqual(as_dict["config"], [{u'text': u'A whole bunch of text\nwith a line return', u'path': u'a/path/file.txt'}])


    def test_write_files(self):

        config = [{u'text': u'A whole bunch of text\nwith a line return', u'path': u'a/path/file.txt'}]
        bootstrap.write_config_files(config, TEMP_DIR, "paul", 0755)
        filepath = os.path.join(TEMP_DIR, u'a/path/file.txt')
        self.assertTrue(os.path.exists(filepath))