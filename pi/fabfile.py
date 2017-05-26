from crypt import crypt
from getpass import getpass
from fabric.api import local, settings, abort, run, env, sudo, put, get, prefix
from fabric.context_managers import cd
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SUB_DOMAIN = "test"
PI_PASSWORD = "password"

env.hosts = ["%s:%s" % ("test.local", 22)]
env.user = "pi"
env.password = PI_PASSWORD


def change_password():
    env.password = "raspberry"
    crypted_password = crypt(PI_PASSWORD, 'salt')
    sudo('usermod --password %s %s' % (crypted_password, env.user), pty=False)


def update():
    change_password()
    # change_host_name()
    change_graphics_memory()
    add_stuff()


def change_host_name():
    sudo("sed -i 's/raspberrypi/%s.augment00.org/g' /etc/hosts" % SUB_DOMAIN)
    sudo("sed -i 's/raspberrypi/%s.augment00.org/g' /etc/hostname" % SUB_DOMAIN)


def change_graphics_memory():
    sudo('echo "gpu_mem=16" >> /boot/config.txt')


def add_stuff():
    sudo("mkdir -p /opt/augment00")
    put("setup_wifi.py", "/opt/augment00/setup_wifi.py", use_sudo=True)
    put("start.sh", "/opt/augment00/start.sh", use_sudo=True)
    sudo("chmod 755 /opt/augment00/start.sh")
    sudo ("rm /etc/rc.local")
    put("rc.local", "/etc/rc.local", use_sudo=True)
    sudo("chmod 755 /etc/rc.local")


def install_docker():
    # run("curl -sSL get.docker.com | sh")
    # run("sudo systemctl enable docker")
    # run("sudo usermod -aG docker pi")
    sudo("apt-get -y install python-pip")
    sudo("pip install docker-compose")

