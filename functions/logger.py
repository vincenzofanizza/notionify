import logging

logger = logging.getLogger(__name__)

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)