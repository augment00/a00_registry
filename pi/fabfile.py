from crypt import crypt
from fabric.api import local, settings, abort, run, env, sudo, put, get, prefix
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

from config import PI_PASSWORD

env.hosts = ["%s:%s" % ("raspberrypi.local", 22)]
env.user = "pi"
env.password = PI_PASSWORD

BASE_VERSION = "0.0.1"
BOOTSTRAP_VERSION = "0.0.1"

JESSIE_VERSION = "2017-04-10-raspbian-jessie-lite"


############################################################################
##              Preparing the base disc image from jessie lite            ##
############################################################################

"""
    "sudo su"
    'wpa_passphrase "Container 20" "eggandchips" >> /etc/wpa_supplicant/wpa_supplicant.conf'
    "wpa_cli reconfigure"

    "raspi-config"

    Interfacing Options > SSH > Yes

    reboot

"""


def prepare_card():
    _change_password()
    _change_graphics_memory()
    _add_start_scripts()
    _install_docker()


def _change_password():
    env.password = "raspberry"
    crypted_password = crypt(PI_PASSWORD, 'salt')
    sudo('usermod --password %s %s' % (crypted_password, env.user), pty=False)


# def change_host_name():
#     sudo("sed -i 's/raspberrypi/raspberrypi.augment00.org/g' /etc/hosts")
#     sudo("sed -i 's/raspberrypi/raspberrypi.augment00.org/g' /etc/hostname")


def _change_graphics_memory():
    sudo('echo "gpu_mem=16" >> /boot/config.txt')


def _add_start_scripts():

    sudo("mkdir -p /opt/augment00")
    put("setup_wifi.py", "/opt/augment00/setup_wifi.py", use_sudo=True)
    put("start.sh", "/opt/augment00/start.sh", use_sudo=True)
    sudo("chmod 755 /opt/augment00/start.sh")

    ## add our own rc.local
    sudo("rm /etc/rc.local")
    put("rc.local", "/etc/rc.local", use_sudo=True)
    sudo("chmod 755 /etc/rc.local")
    sudo("chown root /etc/rc.local")
    sudo("chgrp root /etc/rc.local")



def _install_docker():

    # install docker
    run("curl -sSL get.docker.com | sh")

    # sets up service
    run("sudo systemctl enable docker")

    # allows pi use to use docker
    run("sudo usermod -aG docker pi")

    # installs cocker compose
    sudo("apt-get -y install python-pip")
    sudo("pip install docker-compose")

    # adds a copy of the docker.service file with the additional path for GOOGLE_APPLICATION_CREDENTIALS
    put("docker.service", "/lib/systemd/system/docker.service", use_sudo=True)
    sudo("chmod 644 /lib/systemd/system/docker.service")
    sudo("chown root /lib/systemd/system/docker.service")
    sudo("chgrp root /lib/systemd/system/docker.service")



############################################################################
##              Docker commands for building images                       ##
############################################################################

def docker_login(password):
    sudo ('docker login -u paulharter -p %s' % password)


def build_base():
    tag = BASE_VERSION
    put("docker", "~")
    sudo('docker build --no-cache=true -t="paulharter/augment00-bootstrap-base:%s" docker/bootstrap-base' % tag)
    sudo('docker push paulharter/augment00-bootstrap-base:%s' % tag)
    sudo('docker tag paulharter/augment00-bootstrap-base:%s paulharter/augment00-bootstrap-base:latest' % tag)
    sudo('docker push paulharter/augment00-bootstrap-base:latest')



def build_bootstrap():
    tag = BOOTSTRAP_VERSION
    put("docker", "~")
    sudo('docker build --no-cache=true -t="paulharter/augment00-bootstrap:%s" docker/bootstrap' % tag)
    sudo('docker push paulharter/augment00-bootstrap:%s' % tag)
    sudo('docker tag paulharter/augment00-bootstrap:%s paulharter/augment00-bootstrap:latest' % tag)
    sudo('docker push paulharter/augment00-bootstrap:latest')




















