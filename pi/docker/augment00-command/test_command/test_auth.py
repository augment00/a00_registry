import unittest
import os
import json
import base64
import requests
from augment00_command import auth


CREDS_PATH = os.path.join(os.path.dirname(__file__), "augment00_creds_12518459.json")
FIRE_BASE_HOST = "project00-msme.firebaseio.com"

class ModelsTestCase(unittest.TestCase):

    # def setUp(self):
    #     # First, create an instance of the Testbed class.
    #
    #
    #
    # def tearDown(self):
    #     self.testbed.deactivate()


    def testAuth(self):

        print CREDS_PATH

        with open(CREDS_PATH) as f:
            creds = json.loads(f.read())

        config = auth.get_config(creds, "000000007cc9f7e9")

        print "config: ", config

        if config is not None:

            config_files = config["config"]

            for config_file in config_files:
                if config_file["path"].endswith("env"):
                    env = config_file["text"]
                    print env

            lines = env.split("\n")

            for line in lines:
                if "FIREBASE_TOKEN" in line:
                    access_token = line[line.find("=")+1:]

            print "****************"
            print "access_token: ", access_token
            print "****************"

        parts = access_token.split(".")

        for part in parts:
            print base64.b64decode(part)



        # firebase_url = auth.firebase_url(FIRE_BASE_HOST, "/channels/12518459-bda0-4401-9779-41d0aac0b780.json", access_token)
        #
        # rsp = requests.get(firebase_url)
        #
        # print rsp.content
        #
        # self.assertEqual(rsp.status_code, 200)
        #
        # print rsp.json()
        #
        self.fail()

