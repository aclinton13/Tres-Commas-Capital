# financial_data_api/cache/manager.py
import time
import logging
from diskcache import Cache

from ..config import CACHE_DIR, CACHE_EXPIRY

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        try:
            self.cache = Cache(CACHE_DIR)
            logger.info(f"Cache initialized at {CACHE_DIR}")
        except Exception as e:
            logger.error(f"Error initializing cache: {str(e)}")
            self.cache = None
    
    def get(self, key, cache_type='STOCK_PRICE'):
        """Get data from cache if it exists and is not expired"""
        if not self.cache:
            return None
            
        try:
            data = self.cache.get(key)
            if data is None:
                return None
            
            # Check if data is expired
            expiry_time = CACHE_EXPIRY.get(cache_type, 3600)  # Default 1 hour
            if time.time() - data['timestamp'] > expiry_time:
                logger.debug(f"Cache expired for {key}")
                return None
            
            logger.debug(f"Cache hit for {key}")
            return data['value']
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
            return None
    
    def set(self, key, value, cache_type='STOCK_PRICE'):
        """Store data in cache with timestamp"""
        if not self.cache:
            return False
            
        try:
            data = {
                'timestamp': time.time(),
                'value': value
            }
            self.cache.set(key, data)
            logger.debug(f"Cache set for {key}")
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
            return False
    
    def clear(self, pattern=None):
        """Clear entire cache or by pattern"""
        if not self.cache:
            return False
            
        try:
            if pattern:
                # This is a simple implementation
                keys_to_delete = [k for k in self.cache if pattern in str(k)]
                for key in keys_to_delete:
                    self.cache.delete(key)
                logger.info(f"Cleared {len(keys_to_delete)} cache entries matching '{pattern}'")
            else:
                self.cache.clear()
                logger.info("Cleared entire cache")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False