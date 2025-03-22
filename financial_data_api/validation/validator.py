# financial_data_api/validation/validator.py
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DataValidator:
    @staticmethod
    def validate_ticker(ticker):
        """Validate stock ticker"""
        if not ticker or not isinstance(ticker, str):
            raise ValueError("Ticker must be a non-empty string")
        return ticker.upper()
    
    @staticmethod
    def validate_date_range(start_date, end_date):
        """Validate date range for historical data"""
        try:
            start = pd.to_datetime(start_date) if start_date else pd.to_datetime('2000-01-01')
            end = pd.to_datetime(end_date) if end_date else datetime.now()
            
            if start > end:
                logger.warning("Start date is after end date. Swapping dates.")
                start, end = end, start
            
            return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
        except Exception as e:
            logger.error(f"Invalid date format: {str(e)}")
            raise ValueError(f"Invalid date format: {str(e)}")
    
    @staticmethod
    def validate_historical_data(df):
        """Validate historical price data"""
        if df is None or df.empty:
            logger.warning("Historical data is empty")
            return None
        
        try:
            # Check for required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                logger.warning(f"Missing required columns in historical data: {missing_columns}")
                return None
            
            # Check for NaN values
            if df[required_columns].isna().any().any():
                logger.warning("NaN values found in historical data, attempting to fill")
                # Fill NaN values with appropriate methods
                df['Close'] = df['Close'].fillna(method='ffill')
                df['Open'] = df['Open'].fillna(df['Close'])
                df['High'] = df['High'].fillna(df[['Open', 'Close']].max(axis=1))
                df['Low'] = df['Low'].fillna(df[['Open', 'Close']].min(axis=1))
                df['Volume'] = df['Volume'].fillna(0)
            
            return df
        except Exception as e:
            logger.error(f"Error validating historical data: {str(e)}")
            return None
    
    @staticmethod
    def validate_options_data(options):
        """Validate options data"""
        if not options or not isinstance(options, dict):
            logger.warning("Options data is invalid or empty")
            return None
        
        try:
            valid_options = {}
            for date, chain in options.items():
                # Validate calls and puts
                if ('calls' in chain and isinstance(chain['calls'], list) and len(chain['calls']) > 0) or \
                   ('puts' in chain and isinstance(chain['puts'], list) and len(chain['puts']) > 0):
                    valid_options[date] = chain
            
            if not valid_options:
                logger.warning("No valid options data found")
                return None
                
            return valid_options
        except Exception as e:
            logger.error(f"Error validating options data: {str(e)}")
            return None
    
    @staticmethod
    def validate_sec_filing(filing):
        """Validate SEC filing data"""
        if not filing or not isinstance(filing, dict):
            logger.warning("SEC filing data is invalid or empty")
            return None
        
        try:
            required_fields = ['accessionNumber', 'filingDate', 'form', 'primaryDocument']
            
            if not all(field in filing for field in required_fields):
                missing = [f for f in required_fields if f not in filing]
                logger.warning(f"SEC filing missing required fields: {missing}")
                return None
            
            return filing
        except Exception as e:
            logger.error(f"Error validating SEC filing: {str(e)}")
            return None