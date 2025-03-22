# financial_data_api/sec_edgar/api.py
import requests
import time
import logging
import traceback
from datetime import datetime
from sec_edgar_downloader import Downloader

from ..cache.manager import CacheManager
from ..validation.validator import DataValidator
from ..config import SEC_EDGAR_API_LIMIT, SEC_EDGAR_USER_AGENT

logger = logging.getLogger(__name__)

class SECEdgarAPI:
    def __init__(self):
        self.cache = CacheManager()
        self.validator = DataValidator()
        self.downloader = Downloader(SEC_EDGAR_USER_AGENT)
        self.last_request_time = 0
        self.base_url = "https://www.sec.gov/Archives/edgar/data"
        self.company_facts_url = "https://data.sec.gov/api/xbrl/companyfacts"
        self.headers = {
            "User-Agent": SEC_EDGAR_USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov"
        }
        logger.info("SEC Edgar API initialized")
    
    def _respect_rate_limit(self):
        """Ensure we don't exceed SEC's rate limit"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        # SEC enforces 10 requests per second limit
        wait_time = max(0, (1.0 / SEC_EDGAR_API_LIMIT) - elapsed)
        if wait_time > 0:
            time.sleep(wait_time)
        
        # Always add a small additional delay to be safe
        time.sleep(0.1)
        
        self.last_request_time = time.time()
    
    def get_cik_from_ticker(self, ticker):
        """Get CIK number from ticker symbol"""
        try:
            ticker = self.validator.validate_ticker(ticker)
            cache_key = f"cik_{ticker}"
            
            # Check cache first
            cached_data = self.cache.get(cache_key, 'SEC_FILING')
            if cached_data:
                logger.info(f"Using cached CIK for {ticker}")
                return cached_data
            
            # Respect rate limit
            self._respect_rate_limit()
            
            logger.info(f"Fetching CIK for {ticker} from SEC")
            # Query SEC for ticker to CIK mapping
            url = "https://www.sec.gov/files/company_tickers.json"
            
            try:
                response = requests.get(url, headers=self.headers)
                
                if response.status_code != 200:
                    logger.error(f"Failed to get company tickers: {response.status_code}")
                    return None
                
                companies = response.json()
            except Exception as e:
                logger.error(f"Error in SEC API request: {str(e)}")
                return None
            
            # Find the company with matching ticker
            cik = None
            for _, company in companies.items():
                if company.get('ticker', '').upper() == ticker:
                    # Format CIK to 10 digits with leading zeros
                    cik = str(company.get('cik_str', 0)).zfill(10)
                    break
            
            if cik:
                logger.info(f"Found CIK for {ticker}: {cik}")
                # Cache the result
                self.cache.set(cache_key, cik, 'SEC_FILING')
                return cik
            else:
                logger.warning(f"No CIK found for ticker {ticker}")
                return None
        except Exception as e:
            logger.error(f"Error getting CIK for {ticker}: {str(e)}")
            logger.debug(traceback.format_exc())
            return None
    
    def get_company_facts(self, ticker):
        """Get company facts from SEC EDGAR"""
        try:
            cik = self.get_cik_from_ticker(ticker)
            if not cik:
                logger.warning(f"Unable to get company facts: No CIK for {ticker}")
                return None
            
            cache_key = f"facts_{ticker}"
            
            # Check cache first
            cached_data = self.cache.get(cache_key, 'SEC_FILING')
            if cached_data:
                logger.info(f"Using cached company facts for {ticker}")
                return cached_data
            
            # Respect rate limit
            self._respect_rate_limit()
            
            logger.info(f"Fetching company facts for {ticker} (CIK: {cik})")
            # Query SEC for company facts
            url = f"{self.company_facts_url}/CIK{cik}.json"
            
            try:
                response = requests.get(url, headers=self.headers)
                
                if response.status_code == 404:
                    logger.warning(f"No company facts found for {ticker} (CIK: {cik})")
                    return None
                
                if response.status_code != 200:
                    logger.error(f"Failed to get company facts: {response.status_code}")
                    return None
                
                company_facts = response.json()
            except Exception as e:
                logger.error(f"Error in SEC API request: {str(e)}")
                return None
            
            # Cache the result
            self.cache.set(cache_key, company_facts, 'SEC_FILING')
            
            return company_facts
        except Exception as e:
            logger.error(f"Error getting company facts for {ticker}: {str(e)}")
            logger.debug(traceback.format_exc())
            return None
    
    def get_filings_metadata(self, ticker, form_type, count=10):
        """Get metadata about recent filings"""
        try:
            cik = self.get_cik_from_ticker(ticker)
            if not cik:
                logger.warning(f"Unable to get filings: No CIK for {ticker}")
                return None
            
            cache_key = f"filings_{ticker}_{form_type}_{count}"
            
            # Check cache first
            cached_data = self.cache.get(cache_key, 'SEC_FILING')
            if cached_data:
                logger.info(f"Using cached filings metadata for {ticker}")
                return cached_data
            
            # Respect rate limit
            self._respect_rate_limit()
            
            logger.info(f"Fetching {form_type} filings for {ticker} (CIK: {cik})")
            # Query SEC for filings
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            
            try:
                response = requests.get(url, headers=self.headers)
                
                if response.status_code == 404:
                    logger.warning(f"No submissions found for {ticker} (CIK: {cik})")
                    return []
                
                if response.status_code != 200:
                    logger.error(f"Failed to get filings: {response.status_code}")
                    return []
                
                filings_data = response.json()
            except Exception as e:
                logger.error(f"Error in SEC API request: {str(e)}")
                return []
            
            # Extract relevant filings
            recent_filings = []
            
            if 'filings' in filings_data and 'recent' in filings_data['filings']:
                recent = filings_data['filings']['recent']
                
                if not recent:
                    logger.warning(f"No recent filings found for {ticker}")
                    return []
                
                forms = recent.get('form', [])
                accession_numbers = recent.get('accessionNumber', [])
                filing_dates = recent.get('filingDate', [])
                primary_documents = recent.get('primaryDocument', [])
                
                for i in range(min(len(forms), len(accession_numbers), len(filing_dates))):
                    if forms[i] == form_type:
                        recent_filings.append({
                            'form': forms[i],
                            'accessionNumber': accession_numbers[i],
                            'filingDate': filing_dates[i],
                            'primaryDocument': primary_documents[i] if i < len(primary_documents) else '',
                            'ticker': ticker,
                            'cik': cik
                        })
                        
                        if len(recent_filings) >= count:
                            break
            
            # Cache the result
            self.cache.set(cache_key, recent_filings, 'SEC_FILING')
            
            if not recent_filings:
                logger.warning(f"No {form_type} filings found for {ticker}")
            else:
                logger.info(f"Found {len(recent_filings)} {form_type} filings for {ticker}")
            
            return recent_filings
        except Exception as e:
            logger.error(f"Error getting {form_type} filings for {ticker}: {str(e)}")
            logger.debug(traceback.format_exc())
            return []
    
    def get_recent_10k(self, ticker):
        """Get the most recent 10-K filing"""
        filings = self.get_filings_metadata(ticker, '10-K', count=1)
        if not filings or len(filings) == 0:
            logger.warning(f"No 10-K filings found for {ticker}")
            return None
        
        filing = filings[0]
        # For simplicity, we'll just return the metadata without downloading the content
        # Downloading and parsing the actual 10-K is complex and can be implemented separately
        return filing
    
    def get_recent_8k(self, ticker, count=5):
        """Get recent 8-K filings"""
        filings = self.get_filings_metadata(ticker, '8-K', count=count)
        if not filings:
            logger.warning(f"No 8-K filings found for {ticker}")
            return []
        
        # For simplicity, we'll just return the metadata without downloading the content
        return filings
    
    def extract_key_financials(self, ticker):
        """Extract key financial data from company facts"""
        try:
            facts = self.get_company_facts(ticker)
            if not facts or 'facts' not in facts:
                logger.warning(f"No company facts available for {ticker}")
                return None
            
            # Initialize simplified results
            financials = {
                'ticker': ticker,
                'revenue': [],
                'net_income': [],
                'eps': []
            }
            
            # US GAAP taxonomy
            if 'facts' in facts and 'us-gaap' in facts['facts']:
                us_gaap = facts['facts']['us-gaap']
                
                # Revenue
                for rev_key in ['Revenue', 'Revenues', 'SalesRevenueNet']:
                    if rev_key in us_gaap:
                        for unit in us_gaap[rev_key].get('units', {}):
                            for entry in us_gaap[rev_key]['units'][unit]:
                                if entry.get('form') == '10-K':
                                    financials['revenue'].append({
                                        'value': entry.get('val', 0),
                                        'end_date': entry.get('end', ''),
                                        'filing_date': entry.get('filed', '')
                                    })
                
                # Net Income
                if 'NetIncomeLoss' in us_gaap:
                    for unit in us_gaap['NetIncomeLoss'].get('units', {}):
                        for entry in us_gaap['NetIncomeLoss']['units'][unit]:
                            if entry.get('form') == '10-K':
                                financials['net_income'].append({
                                    'value': entry.get('val', 0),
                                    'end_date': entry.get('end', ''),
                                    'filing_date': entry.get('filed', '')
                                })
                
                # EPS
                if 'EarningsPerShareDiluted' in us_gaap:
                    for unit in us_gaap['EarningsPerShareDiluted'].get('units', {}):
                        for entry in us_gaap['EarningsPerShareDiluted']['units'][unit]:
                            if entry.get('form') == '10-K':
                                financials['eps'].append({
                                    'value': entry.get('val', 0),
                                    'end_date': entry.get('end', ''),
                                    'filing_date': entry.get('filed', '')
                                })
            
            # Sort data by filing date (most recent first)
            for key in financials:
                if key != 'ticker' and financials[key]:
                    financials[key] = sorted(
                        financials[key], 
                        key=lambda x: x['filing_date'] if x.get('filing_date') else '', 
                        reverse=True
                    )
            
            return financials
        except Exception as e:
            logger.error(f"Error extracting financials for {ticker}: {str(e)}")
            logger.debug(traceback.format_exc())
            return None