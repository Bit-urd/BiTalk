"""
Utility functions for BiTalk data tasks
"""

import requests
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from functools import wraps
import hashlib

logger = logging.getLogger('data_task.utils')

class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.calls = []
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = datetime.now()
        # Remove calls older than 1 minute
        self.calls = [call_time for call_time in self.calls if now - call_time < timedelta(minutes=1)]
        
        if len(self.calls) >= self.calls_per_minute:
            # Calculate wait time
            oldest_call = min(self.calls)
            wait_time = 60 - (now - oldest_call).total_seconds()
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds")
                time.sleep(wait_time)
        
        self.calls.append(now)

class Cache:
    """Simple file-based cache"""
    
    def __init__(self, cache_dir: str = "cache", ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.ttl_hours = ttl_hours
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> str:
        """Get cache file path for a key"""
        # Create safe filename from key
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{safe_key}.json")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)
            
            # Check if cache is still valid
            cached_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cached_time > timedelta(hours=self.ttl_hours):
                os.remove(cache_path)
                return None
            
            return cached_data['data']
        except Exception as e:
            logger.warning(f"Error reading cache for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache"""
        cache_path = self._get_cache_path(key)
        
        try:
            cached_data = {
                'timestamp': datetime.now().isoformat(),
                'data': value
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cached_data, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Error writing cache for key {key}: {e}")

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator to retry function on failure"""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = delay * (backoff ** attempt)
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {wait_time:.1f}s")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
            
            raise last_exception
        
        return wrapper
    return decorator

def safe_request(url: str, headers: Optional[Dict] = None, params: Optional[Dict] = None, 
                timeout: int = 30, rate_limiter: Optional[RateLimiter] = None) -> Optional[requests.Response]:
    """Make a safe HTTP request with error handling"""
    
    if rate_limiter:
        rate_limiter.wait_if_needed()
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {url}: {e}")
        return None

def ensure_directory(path: str) -> None:
    """Ensure directory exists"""
    os.makedirs(path, exist_ok=True)
    logger.debug(f"Ensured directory exists: {path}")

def save_json(data: Any, file_path: str) -> None:
    """Save data as JSON with error handling"""
    try:
        ensure_directory(os.path.dirname(file_path))
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Saved JSON data to {file_path}")
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")
        raise

def load_json(file_path: str) -> Optional[Any]:
    """Load JSON data with error handling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug(f"Loaded JSON data from {file_path}")
        return data
    except FileNotFoundError:
        logger.warning(f"JSON file not found: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
        return None

def save_markdown(content: str, file_path: str) -> None:
    """Save markdown content with error handling"""
    try:
        ensure_directory(os.path.dirname(file_path))
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Saved markdown to {file_path}")
    except Exception as e:
        logger.error(f"Error saving markdown to {file_path}: {e}")
        raise

def format_currency(amount: float, symbol: str = "$") -> str:
    """Format currency amount"""
    if amount >= 1e9:
        return f"{symbol}{amount/1e9:.1f}B"
    elif amount >= 1e6:
        return f"{symbol}{amount/1e6:.1f}M"
    elif amount >= 1e3:
        return f"{symbol}{amount/1e3:.1f}K"
    else:
        return f"{symbol}{amount:.2f}"

def format_percentage(value: float) -> str:
    """Format percentage value"""
    return f"{value:.2%}"

def get_time_ago(dt: datetime) -> str:
    """Convert datetime to 'time ago' format"""
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds >= 3600:
        return f"{diff.seconds // 3600}h ago"
    elif diff.seconds >= 60:
        return f"{diff.seconds // 60}m ago"
    else:
        return "Just now"

def clean_filename(filename: str) -> str:
    """Clean filename for safe file operations"""
    import re
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove consecutive underscores
    filename = re.sub(r'_{2,}', '_', filename)
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    return filename

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    from urllib.parse import urlparse
    return urlparse(url).netloc

def validate_address(address: str) -> bool:
    """Validate Ethereum address format"""
    import re
    return bool(re.match(r'^0x[a-fA-F0-9]{40}$', address))

# Global instances
default_cache = Cache()
default_rate_limiter = RateLimiter(calls_per_minute=60)