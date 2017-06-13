#!/bin/sh

python /opt/augment00/wifi.py
docker run --privileged -v /etc/opt/augment00:/etc/opt/augment00 --rm paulharter/augment00-bootstrap:latest
docker-compose -f /etc/opt/augment00/docker-compose.yml pull
docker-compose -f /etc/opt/augment00/docker-compose.yml up -d --force-recreate
