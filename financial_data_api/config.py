# financial_data_api/config.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
YAHOO_FINANCE_API_LIMIT = 100  # Reduced from 2000 to be more conservative
SEC_EDGAR_API_LIMIT = 5  # Reduced from 10 to be more conservative

# Cache Configuration
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache_data')
os.makedirs(CACHE_DIR, exist_ok=True)

CACHE_EXPIRY = {
    'STOCK_PRICE': 60 * 60,  # 1 hour in seconds
    'HISTORICAL_DATA': 24 * 60 * 60,  # 24 hours in seconds
    'SEC_FILING': 7 * 24 * 60 * 60,  # 7 days in seconds
}

# MongoDB Configuration
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'tres_comas_capital')
MONGO_COLLECTION = {
    'STOCK_DATA': 'stock_data',
    'SEC_FILINGS': 'sec_filings',
    'OPTIONS_DATA': 'options_data'
}

# SEC EDGAR Configuration
SEC_EDGAR_USER_AGENT = os.environ.get(
    'SEC_EDGAR_USER_AGENT', 
    'Financial Data API (your.email@example.com)'
)