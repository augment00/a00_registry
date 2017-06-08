
import random
from urlparse import urlparse
import keys
import urllib
import os
import json
import requests
import shutil
import subprocess
from pwd import getpwnam

ALPHA_NUMERIC = "abcdefghijklmnopqrstuvwxyz0123456789"

MOUNT_DIR = "/mnt/usb"
USB_CONFIG_FOLDER = os.path.join(MOUNT_DIR, "augment00")
AUGMENT00_CREDS_PATH = os.path.join(USB_CONFIG_FOLDER, "augment00.json")
CONFIG_DIR = "/etc/opt/augemnt00"
CONFIG_OWNER = "pi"
DOCKER_COMPOSE_FILEPATH = os.path.join(CONFIG_DIR, "docker-compose.yml")


def generateNewRandomAlphaNumeric(length):
    random.seed()
    values = []
    for i in range(length):
        values.append(random.choice(ALPHA_NUMERIC))
    return "".join(values)


def run_docker_compose():

    if os.path.exists(DOCKER_COMPOSE_FILEPATH):
        cmd = "docker-compose -f %s pull" % DOCKER_COMPOSE_FILEPATH
        subprocess.call(cmd, shell=True)
        cmd = "docker-compose up -f %s -d --force-recreate --remove-orphans" % DOCKER_COMPOSE_FILEPATH
        subprocess.call(cmd, shell=True)



def update_config():

    if not os.path.exists(AUGMENT00_CREDS_PATH):
        return

    with open(AUGMENT00_CREDS_PATH, "r") as f:
        creds = json.loads(f.read())

    url = config_url(creds)
    rsp = requests.get(url)

    if rsp.status_code == 200:
        if os.path.exists(CONFIG_DIR):
            shutil.rmtree(CONFIG_DIR)
        os.makedirs(CONFIG_DIR)
        config = rsp.json()
        write_config_files(config, CONFIG_DIR, CONFIG_OWNER, 0755)



def write_config_files(config, base_dir, owner, mode):

    for config_file in config:
        path = config_file["path"]
        path = path[1:] if path.startswith("/") else path
        dst_file_path = os.path.join(base_dir, path)
        dir = os.path.dirname(dst_file_path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        if os.path.exists(dst_file_path):
            os.remove(dst_file_path)
        with open(dst_file_path, "w") as f:
            f.write(config_file["text"])
        os.chmod(dst_file_path, mode)
        uid = getpwnam(owner).pw_uid
        gid = getpwnam(owner).pw_gid
        os.chown(dst_file_path, uid, gid)


def config_url(creds):
    src_url = creds["url"]
    private_pem = creds["private_key"]
    parsed = urlparse(src_url)
    nonced_path = "%s/%s" % (parsed.path, generateNewRandomAlphaNumeric(20))
    sig = keys.sign_url(nonced_path, private_pem)
    query = urllib.urlencode({"sig": sig})
    url = "%s://%s%s?%s" % (parsed.scheme, parsed.netloc, nonced_path, query)
    return url




if __name__ == '__main__':
    update_config()
    run_docker_compose()