#!/bin/sh

mkdir -p /opt/augment00
cp /mnt/usb/augment00/docker-compose.yml /opt/augment00/docker-compose.yml
cp /mnt/usb/augment00/augment00.env /opt/augment00/augment00.env
cd /opt/augment00
docker-compose pull
docker-compose up