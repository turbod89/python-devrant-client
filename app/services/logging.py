import logging

logging.basicConfig(level=logging.DEBUG, filename='debug.log', filemode='a')


def getLogger(name="dev-rant-client"):
    return logging.getLogger(name)
