# financial_data_api/__init__.py
import logging
import os
from datetime import datetime
import time

from .yahoo_finance.api import YahooFinanceAPI
from .sec_edgar.api import SECEdgarAPI
from .cache.manager import CacheManager
from .utils.db_manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'financial_api.log'))
    ]
)

logger = logging.getLogger(__name__)

class FinancialDataAPI:
    def __init__(self):
        try:
            self.yahoo = YahooFinanceAPI()
            self.edgar = SECEdgarAPI()
            self.cache = CacheManager()
            self.db = DatabaseManager()
            logger.info("FinancialDataAPI initialized")
        except Exception as e:
            logger.error(f"Error initializing FinancialDataAPI: {str(e)}")
            raise
    
    def get_stock_data(self, ticker):
        """Get comprehensive stock data including price, financials, and filings"""
        ticker = ticker.upper()
        
        # Initialize response structure with defaults
        comprehensive_data = {
            'basic_info': {},
            'implied_volatility': None,
            'sec_data': {
                'recent_10k': None,
                'recent_8k': [],
                'key_financials': None
            },
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            # Get basic stock info
            logger.info(f"Getting ticker info for {ticker}")
            stock_info = self.yahoo.get_ticker_info(ticker)
            if stock_info:
                comprehensive_data['basic_info'] = stock_info
            
            time.sleep(2)  # Add delay between calls
            
            # Get historical price data (1 year)
            logger.info(f"Getting historical data for {ticker}")
            historical_data = self.yahoo.get_historical_data(ticker, period='1y')
            if historical_data is not None:
                comprehensive_data['historical_data'] = historical_data.to_dict() if hasattr(historical_data, 'to_dict') else None
            
            time.sleep(2)  # Add delay between calls
            
            # Get options data
            logger.info(f"Getting options data for {ticker}")
            options_data = self.yahoo.get_options_chain(ticker)
            if options_data:
                comprehensive_data['options_data'] = options_data
                self.db.save_options_data(ticker, options_data)
            
            time.sleep(2)  # Add delay between calls
            
            # Get implied volatility
            logger.info(f"Calculating implied volatility for {ticker}")
            iv_data = self.yahoo.calculate_implied_volatility(ticker)
            if iv_data:
                comprehensive_data['implied_volatility'] = iv_data
            
            time.sleep(2)  # Add delay between calls
            
            # Get SEC data
            logger.info(f"Getting 10-K filings for {ticker}")
            sec_filings_10k = self.edgar.get_recent_10k(ticker)
            if sec_filings_10k:
                comprehensive_data['sec_data']['recent_10k'] = sec_filings_10k
                self.db.save_sec_filing(sec_filings_10k)
            
            time.sleep(2)  # Add delay between calls
            
            logger.info(f"Getting 8-K filings for {ticker}")
            sec_filings_8k = self.edgar.get_recent_8k(ticker)
            if sec_filings_8k:
                comprehensive_data['sec_data']['recent_8k'] = sec_filings_8k
                for filing in sec_filings_8k:
                    if filing:
                        self.db.save_sec_filing(filing)
            
            time.sleep(2)  # Add delay between calls
            
            logger.info(f"Getting financial data for {ticker}")
            financial_data = self.edgar.extract_key_financials(ticker)
            if financial_data:
                comprehensive_data['sec_data']['key_financials'] = financial_data
            
            # Save data to database
            logger.info(f"Saving comprehensive data for {ticker}")
            self.db.save_stock_data(comprehensive_data)
            
            logger.info("Successfully retrieved comprehensive data")
            return comprehensive_data
        
        except Exception as e:
            logger.error(f"Error in get_stock_data: {str(e)}")
            # Still return the partial data we collected
            return comprehensive_data
    
    def clear_cache(self, pattern=None):
        """Clear cache data"""
        try:
            self.cache.clear(pattern)
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False