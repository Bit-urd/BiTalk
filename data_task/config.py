"""
Configuration management for BiTalk data tasks
"""

import os
import json
from dataclasses import dataclass
from typing import Dict, List, Optional
import logging

@dataclass
class APIConfig:
    """API configuration"""
    news_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    github_token: Optional[str] = None
    covalent_api_key: Optional[str] = None
    coingecko_api_key: Optional[str] = None
    defillama_api_key: Optional[str] = None

@dataclass
class PathConfig:
    """Path configuration"""
    data_dir: str = "data"
    content_dir: str = "content"
    static_dir: str = "static"
    log_dir: str = "logs"

@dataclass
class ScrapingConfig:
    """Web scraping configuration"""
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    request_delay: float = 1.0
    max_retries: int = 3
    timeout: int = 30

@dataclass
class Config:
    """Main configuration class"""
    api: APIConfig
    paths: PathConfig
    scraping: ScrapingConfig
    debug: bool = False

def load_config() -> Config:
    """Load configuration from environment variables and config file"""
    
    # Load API keys from environment
    api_config = APIConfig(
        news_api_key=os.getenv("NEWS_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        github_token=os.getenv("GITHUB_TOKEN"),
        covalent_api_key=os.getenv("COVALENT_API_KEY"),
        coingecko_api_key=os.getenv("COINGECKO_API_KEY"),
        defillama_api_key=os.getenv("DEFILLAMA_API_KEY")
    )
    
    # Load path configuration
    paths_config = PathConfig(
        data_dir=os.getenv("DATA_DIR", "data"),
        content_dir=os.getenv("CONTENT_DIR", "content"),
        static_dir=os.getenv("STATIC_DIR", "static"),
        log_dir=os.getenv("LOG_DIR", "logs")
    )
    
    # Load scraping configuration
    scraping_config = ScrapingConfig(
        user_agent=os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
        request_delay=float(os.getenv("REQUEST_DELAY", "1.0")),
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        timeout=int(os.getenv("REQUEST_TIMEOUT", "30"))
    )
    
    return Config(
        api=api_config,
        paths=paths_config,
        scraping=scraping_config,
        debug=os.getenv("DEBUG", "false").lower() == "true"
    )

def setup_logging(log_dir: str = "logs", debug: bool = False) -> logging.Logger:
    """Setup logging configuration"""
    
    # Create log directory
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    log_level = logging.DEBUG if debug else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # File handler
    file_handler = logging.FileHandler(os.path.join(log_dir, 'data_tasks.log'))
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Root logger
    logger = logging.getLogger('data_task')
    logger.setLevel(log_level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Global configuration instance
config = load_config()
logger = setup_logging(config.paths.log_dir, config.debug)