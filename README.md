# Augment00 Registry

There are several distinct bits of code here (I will probably split them out soon).

There is a registry web app where all clients are registered.
This provides both the source of truth for info about clients and a file based configuration service to bootstrap and configure clients.
There are scripts to build the SD card that goes in the Raspberry Pis and some sample USB configuration files.

The plan is that all clients are plug-and-play with a USB attached to each desk that provides minimal credentials and configuration.
The Raspberry Pis will be given a base images on sd cards that has just jessie lite, docker/compose and a simple startup script.
All applications are to be downloaded as docker images and all further configuration pulled from the regisrty service.
This will make possible:

- Plug-and-play provisioning without the need for keyboards/screen etc
- Over the air updating of both code and configuration
- Simple ongoing support and maintenance

## Registry

The registry app is a Google App Engine app that provides the core registration and configuration services used by Augment00 clients.
This is in the src folder and the readme is here [src/README.md](src/README.md)

## Raspberry Pi

Augment00 uses Raspberry Pis as its main processors in clients. scripts for building prepared SD cards and docker images are ing the pi
folder and the readme in here [pi/readme.md](pi/readme.md)

## USB configuration

There is an example set of configuration files in the usb folder

![augment00 services](docs/IMG_1477.PNG)
