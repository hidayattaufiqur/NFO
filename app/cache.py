from flask_caching import Cache
from app.logger import get_logger

logger = get_logger(__name__)
cache = None

def init_cache(app):
    global cache
    logger.info("initializing RedisCache")
    cache = Cache(app)

def get_cache():
    if not cache:
        raise RuntimeError("cache is not initialized")
    return cache
