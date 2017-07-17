import os

APPLICATION_MODE_TEST = "test"
APPLICATION_MODE_DEVELOPMENT = "development"
APPLICATION_MODE_PRODUCTION = "production"

APPLICATION_MODE = None

def application_mode():

    global APPLICATION_MODE

    if APPLICATION_MODE is None:

        server_software = os.environ.get("SERVER_SOFTWARE")

        if server_software is None:
            APPLICATION_MODE = APPLICATION_MODE_PRODUCTION
        elif server_software.startswith("Development"):
            APPLICATION_MODE = APPLICATION_MODE_DEVELOPMENT
        else:
            APPLICATION_MODE = APPLICATION_MODE_PRODUCTION

    print "mode: ", APPLICATION_MODE
    return APPLICATION_MODE