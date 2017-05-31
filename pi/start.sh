#!/bin/sh

mkdir -p /opt/augment00/secrets
cp /mnt/usb/augment00/docker-compose.yml /opt/augment00/docker-compose.yml
cp /mnt/usb/augment00/augment00.env /opt/augment00/augment00.env
cp /mnt/usb/augment00/google_creds.json /opt/augment00/secrets/google_creds.json
cd /opt/augment00
docker-compose pull
docker-compose up