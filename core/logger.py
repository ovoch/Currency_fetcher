import logging 

def logger_config():
    logging.basicConfig(level = logging.DEBUG, format = "%(asctime)s %(levelname)s %(name)s %(message)s",handlers = [logging.StreamHandler()])

