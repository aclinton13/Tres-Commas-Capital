# financial_data_api/utils/db_manager.py
from pymongo import MongoClient
import logging
from datetime import datetime

from ..config import MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.client = None
            cls._instance.db = None
            cls._instance.connect()
        return cls._instance
    
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(MONGO_URI)
            self.db = self.client[MONGO_DB_NAME]
            logger.info(f"Successfully connected to MongoDB: {MONGO_DB_NAME}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            self.client = None
            self.db = None
    
    def get_collection(self, collection_name):
        """Get a MongoDB collection"""
        if not self.db:
            logger.warning("No database connection. Attempting to reconnect.")
            self.connect()
            if not self.db:
                return None
        
        if collection_name not in MONGO_COLLECTION.values():
            logger.warning(f"Unknown collection: {collection_name}")
            return None
        
        return self.db[collection_name]
    
    def save_stock_data(self, data):
        """Save stock data to MongoDB"""
        try:
            if not data or not isinstance(data, dict):
                logger.warning("Invalid stock data format")
                return False
            
            # Ensure we have at least a symbol
            if 'basic_info' not in data or not data['basic_info']:
                logger.warning("Stock data missing basic_info")
                return False
                
            symbol = data['basic_info'].get('symbol', '')
            if not symbol:
                logger.warning("Stock data missing symbol")
                return False
            
            collection = self.get_collection(MONGO_COLLECTION['STOCK_DATA'])
            if not collection:
                return False
            
            # Check if document already exists
            existing = collection.find_one({'basic_info.symbol': symbol})
            
            if existing:
                # Update existing document
                result = collection.update_one(
                    {'basic_info.symbol': symbol},
                    {'$set': data}
                )
                success = result.modified_count > 0
            else:
                # Insert new document
                result = collection.insert_one(data)
                success = result.inserted_id is not None
            
            if success:
                logger.info(f"Successfully saved stock data for {symbol}")
            else:
                logger.warning(f"Failed to save stock data for {symbol}")
                
            return success
        except Exception as e:
            logger.error(f"Error saving stock data: {str(e)}")
            return False
    
    def save_sec_filing(self, filing):
        """Save SEC filing to MongoDB"""
        try:
            if not filing or not isinstance(filing, dict):
                logger.warning("Invalid SEC filing format")
                return False
            
            # Check for required fields
            if 'accessionNumber' not in filing:
                logger.warning("SEC filing missing accessionNumber")
                return False
            
            collection = self.get_collection(MONGO_COLLECTION['SEC_FILINGS'])
            if not collection:
                return False
            
            # Check if document already exists
            existing = collection.find_one({'accessionNumber': filing['accessionNumber']})
            
            if existing:
                # Update existing document
                result = collection.update_one(
                    {'accessionNumber': filing['accessionNumber']},
                    {'$set': filing}
                )
                success = result.modified_count > 0
            else:
                # Insert new document
                result = collection.insert_one(filing)
                success = result.inserted_id is not None
            
            if success:
                logger.info(f"Successfully saved SEC filing {filing['accessionNumber']}")
            else:
                logger.warning(f"Failed to save SEC filing {filing['accessionNumber']}")
                
            return success
        except Exception as e:
            logger.error(f"Error saving SEC filing: {str(e)}")
            return False
    
    def save_options_data(self, ticker, options_data):
        """Save options data to MongoDB"""
        try:
            if not options_data or not isinstance(options_data, dict):
                logger.warning("Invalid options data format")
                return False
            
            collection = self.get_collection(MONGO_COLLECTION['OPTIONS_DATA'])
            if not collection:
                return False
            
            # Create a document with ticker and timestamp
            document = {
                'symbol': ticker,
                'timestamp': datetime.now().isoformat(),
                'options': options_data
            }
            
            # Check if document already exists
            existing = collection.find_one({'symbol': ticker})
            
            if existing:
                # Update existing document
                result = collection.update_one(
                    {'symbol': ticker},
                    {'$set': document}
                )
                success = result.modified_count > 0
            else:
                # Insert new document
                result = collection.insert_one(document)
                success = result.inserted_id is not None
            
            if success:
                logger.info(f"Successfully saved options data for {ticker}")
            else:
                logger.warning(f"Failed to save options data for {ticker}")
                
            return success
        except Exception as e:
            logger.error(f"Error saving options data: {str(e)}")
            return False