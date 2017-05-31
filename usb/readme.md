# Augment00 USB Configuration

Augment00 will use a usb attached to each client item that will provide all the necessary configuration for provisioning and updating clients.

Augment00 clients will have fully plug-and-play configuration without use of a screen or keyboard.

Provisioning will be a matter of inserting a micro sd burnt with our base image, and the desk's usb key and turning it on.

All software updates will be automatic.

## USB key

The augment00 folder adjacent holds four files for configuring a client.
These ones are only examples and don't contain the actual secrects etc necessary. Tallk to Paul to get real ones.

- **augment00.env** holds envars to be passed into the docker containers
- **docker-compose.yml** is the Docker Compose file that will run
- **google_creds.json** are a set or google cloud credentails for logging services
- **wifi.json** hold the login details for the wifi

It is planned that the registration service, when ready, will deliver most of these files invisibly.
The wifi.json file will remain the others being replaced with a single augment00 credentials file.