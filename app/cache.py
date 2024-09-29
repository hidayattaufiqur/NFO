from flask_caching import Cache

import logging

logger = logging.getLogger(__name__)
cache = None

def init_cache(app):
    global cache
    logger.info("initializing RedisCache")
    cache = Cache(app)

def get_cache():
    if not cache:
        raise RuntimeError("cache is not initialized")
    return cache
