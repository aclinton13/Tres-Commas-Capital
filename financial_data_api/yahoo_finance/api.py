# financial_data_api/yahoo_finance/api.py
import yfinance as yf
import pandas as pd
import time
from datetime import datetime, timedelta
import logging
import traceback

from ..cache.manager import CacheManager
from ..validation.validator import DataValidator
from ..config import YAHOO_FINANCE_API_LIMIT

logger = logging.getLogger(__name__)

class YahooFinanceAPI:
    def __init__(self):
        self.cache = CacheManager()
        self.validator = DataValidator()
        self.request_count = 0
        self.reset_time = datetime.now() + timedelta(hours=1)
        self.last_request_time = 0
    
    def _check_rate_limit(self):
        """Check if we're approaching the rate limit and implement backoff"""
        now = datetime.now()
        
        # Reset counter if an hour has passed
        if now >= self.reset_time:
            self.request_count = 0
            self.reset_time = now + timedelta(hours=1)
        
        # Always add a small delay between requests (at least 1 second)
        elapsed = time.time() - self.last_request_time
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        
        # Implement exponential backoff if we're making many requests
        if self.request_count > 5:
            # Calculate delay: starts at 1s, doubles every 5 requests, caps at 30s
            delay = min(30, 2 ** (self.request_count // 5))
            logger.info(f"Rate limiting: Waiting {delay} seconds before next request")
            time.sleep(delay)
        
        self.request_count += 1
        self.last_request_time = time.time()
    
    def get_ticker_info(self, ticker):
        """Get basic information about a ticker"""
        try:
            ticker = self.validator.validate_ticker(ticker)
            cache_key = f"ticker_info_{ticker}"
            
            # Check cache first
            cached_data = self.cache.get(cache_key, 'STOCK_PRICE')
            if cached_data:
                logger.info(f"Using cached ticker info for {ticker}")
                return cached_data
            
            # Check rate limit
            self._check_rate_limit()
            
            logger.info(f"Fetching ticker info for {ticker} from Yahoo Finance")
            # Get data from Yahoo Finance
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info or not isinstance(info, dict):
                logger.warning(f"Received empty or invalid info for {ticker}")
                return None
            
            # Validate and filter relevant information
            relevant_info = {
                'symbol': ticker,
                'name': info.get('shortName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', 0),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
                'avg_volume': info.get('averageVolume', 0),
                'last_updated': datetime.now().isoformat()
            }
            
            # Cache the results
            self.cache.set(cache_key, relevant_info, 'STOCK_PRICE')
            
            return relevant_info
        except Exception as e:
            logger.error(f"Error fetching ticker info for {ticker}: {str(e)}")
            logger.debug(traceback.format_exc())
            return None
    
    def get_historical_data(self, ticker, start_date=None, end_date=None, period='1y', interval='1d'):
        """Get historical price data for a ticker"""
        try:
            ticker = self.validator.validate_ticker(ticker)
            
            # If specific dates are provided, validate them
            if start_date or end_date:
                start_date, end_date = self.validator.validate_date_range(start_date, end_date)
                cache_key = f"historical_{ticker}_{start_date}_{end_date}_{interval}"
            else:
                # If using period instead
                cache_key = f"historical_{ticker}_{period}_{interval}"
            
            # Check cache first
            cached_data = self.cache.get(cache_key, 'HISTORICAL_DATA')
            if cached_data is not None:
                logger.info(f"Using cached historical data for {ticker}")
                return pd.DataFrame(cached_data)
            
            # Check rate limit
            self._check_rate_limit()
            
            logger.info(f"Fetching historical data for {ticker} from Yahoo Finance")
            # Get data from Yahoo Finance
            try:
                if start_date and end_date:
                    df = yf.download(ticker, start=start_date, end=end_date, interval=interval, progress=False)
                else:
                    df = yf.download(ticker, period=period, interval=interval, progress=False)
            except Exception as e:
                logger.error(f"YFinance download error: {str(e)}")
                return None
            
            # Validate data
            if df is None or df.empty:
                logger.warning(f"No historical data returned for {ticker}")
                return None
            
            df = self.validator.validate_historical_data(df)
            if df is None:
                return None
            
            # Reset index to make date a column
            df = df.reset_index()
            if 'Date' in df.columns:
                df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
            
            # Cache the results
            self.cache.set(cache_key, df.to_dict('records'), 'HISTORICAL_DATA')
            
            return df
        except Exception as e:
            logger.error(f"Error fetching historical data for {ticker}: {str(e)}")
            logger.debug(traceback.format_exc())
            return None
    
    def get_options_chain(self, ticker, expiration_date=None):
        """Get options chain for a ticker"""
        try:
            ticker = self.validator.validate_ticker(ticker)
            
            # Create cache key based on parameters
            cache_key = f"options_{ticker}"
            if expiration_date:
                cache_key += f"_{expiration_date}"
            
            # Check cache first
            cached_data = self.cache.get(cache_key, 'STOCK_PRICE')
            if cached_data:
                logger.info(f"Using cached options data for {ticker}")
                return cached_data
            
            # Check rate limit
            self._check_rate_limit()
            
            logger.info(f"Fetching options data for {ticker} from Yahoo Finance")
            # Get data from Yahoo Finance
            stock = yf.Ticker(ticker)
            
            # Get available expirations
            try:
                expirations = stock.options
                if not expirations:
                    logger.warning(f"No options available for {ticker}")
                    return None
            except Exception as e:
                logger.error(f"Error getting options expirations for {ticker}: {str(e)}")
                return None
            
            # Get specific expiration or all available
            options_data = {}
            
            if expiration_date:
                if expiration_date not in expirations:
                    logger.warning(f"Expiration date {expiration_date} not available for {ticker}")
                    return None
                
                try:
                    options = stock.option_chain(expiration_date)
                    options_data[expiration_date] = {
                        'calls': options.calls.to_dict('records') if not options.calls.empty else [],
                        'puts': options.puts.to_dict('records') if not options.puts.empty else []
                    }
                except Exception as e:
                    logger.error(f"Error getting options for {ticker} on {expiration_date}: {str(e)}")
                    return None
            else:
                # To avoid too many requests, just get the first expiration date
                try:
                    expiration_date = expirations[0]
                    options = stock.option_chain(expiration_date)
                    options_data[expiration_date] = {
                        'calls': options.calls.to_dict('records') if not options.calls.empty else [],
                        'puts': options.puts.to_dict('records') if not options.puts.empty else []
                    }
                except Exception as e:
                    logger.error(f"Error getting options for {ticker} on {expiration_date}: {str(e)}")
                    return None
            
            if not options_data:
                logger.warning(f"No valid options data retrieved for {ticker}")
                return None
            
            # Cache the results
            self.cache.set(cache_key, options_data, 'STOCK_PRICE')
            
            return options_data
        except Exception as e:
            logger.error(f"Error fetching options data for {ticker}: {str(e)}")
            logger.debug(traceback.format_exc())
            return None
    
    def calculate_implied_volatility(self, ticker):
        """Calculate implied volatility from options chains"""
        try:
            ticker = self.validator.validate_ticker(ticker)
            
            cache_key = f"iv_{ticker}"
            
            # Check cache first
            cached_data = self.cache.get(cache_key, 'STOCK_PRICE')
            if cached_data:
                logger.info(f"Using cached IV data for {ticker}")
                return cached_data
            
            # Get options data
            options_data = self.get_options_chain(ticker)
            if not options_data:
                logger.warning(f"No options data available to calculate IV for {ticker}")
                return None
            
            # Initialize result structure
            iv_data = {
                'symbol': ticker,
                'timestamp': datetime.now().isoformat(),
                'expirations': {},
                'average_iv': 0.0
            }
            
            all_ivs = []
            
            # Process each expiration date
            for date, chain in options_data.items():
                calls_iv = []
                puts_iv = []
                
                # Extract implied volatilities from calls
                if 'calls' in chain and chain['calls']:
                    for call in chain['calls']:
                        if isinstance(call, dict) and 'impliedVolatility' in call and call['impliedVolatility'] > 0:
                            calls_iv.append(call['impliedVolatility'])
                
                # Extract implied volatilities from puts
                if 'puts' in chain and chain['puts']:
                    for put in chain['puts']:
                        if isinstance(put, dict) and 'impliedVolatility' in put and put['impliedVolatility'] > 0:
                            puts_iv.append(put['impliedVolatility'])
                
                # Calculate average IVs
                avg_calls_iv = sum(calls_iv) / len(calls_iv) if calls_iv else 0
                avg_puts_iv = sum(puts_iv) / len(puts_iv) if puts_iv else 0
                avg_total_iv = (avg_calls_iv + avg_puts_iv) / 2 if (calls_iv or puts_iv) else 0
                
                if avg_total_iv > 0:
                    all_ivs.append(avg_total_iv)
                
                iv_data['expirations'][date] = {
                    'calls_iv': avg_calls_iv,
                    'puts_iv': avg_puts_iv,
                    'average_iv': avg_total_iv
                }
            
            # Calculate overall average IV across all expirations
            iv_data['average_iv'] = sum(all_ivs) / len(all_ivs) if all_ivs else 0
            
            # Cache the results
            self.cache.set(cache_key, iv_data, 'STOCK_PRICE')
            
            return iv_data
        except Exception as e:
            logger.error(f"Error calculating implied volatility for {ticker}: {str(e)}")
            logger.debug(traceback.format_exc())
            return None