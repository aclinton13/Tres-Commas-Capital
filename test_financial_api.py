# test_financial_api.py
from financial_data_api import FinancialDataAPI
import logging
import time
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_yahoo_finance():
    print("\n=== Testing Yahoo Finance API ===")
    api = FinancialDataAPI()
    
    # Test getting ticker info
    print("\nTesting get_ticker_info for AAPL:")
    try:
        info = api.yahoo.get_ticker_info("AAPL")
        if info:
            print(f"Company Name: {info.get('name', 'N/A')}")
            print(f"Sector: {info.get('sector', 'N/A')}")
            print(f"Market Cap: ${info.get('market_cap', 0):,}")
        else:
            print("No ticker info retrieved")
    except Exception as e:
        print(f"Error getting ticker info: {str(e)}")
        print(traceback.format_exc())
    
    time.sleep(3)  # Add delay between API calls
    
    # Test getting historical data
    print("\nTesting get_historical_data for AAPL (last 5 days):")
    try:
        hist_data = api.yahoo.get_historical_data("AAPL", period="5d")
        if hist_data is not None and not hist_data.empty:
            print(hist_data.head())
        else:
            print("No historical data retrieved")
    except Exception as e:
        print(f"Error getting historical data: {str(e)}")
        print(traceback.format_exc())
    
    time.sleep(3)  # Add delay between API calls
    
    # Test getting options data
    print("\nTesting get_options_chain for AAPL:")
    try:
        options = api.yahoo.get_options_chain("AAPL")
        if options:
            print(f"Available expiration dates: {list(options.keys())}")
            first_date = list(options.keys())[0]
            print(f"Number of call options for {first_date}: {len(options[first_date].get('calls', []))}")
        else:
            print("No options data retrieved")
    except Exception as e:
        print(f"Error getting options data: {str(e)}")
        print(traceback.format_exc())

def test_sec_edgar():
    print("\n=== Testing SEC EDGAR API ===")
    api = FinancialDataAPI()
    
    # Test getting CIK
    print("\nTesting get_cik_from_ticker for AAPL:")
    try:
        cik = api.edgar.get_cik_from_ticker("AAPL")
        print(f"CIK for AAPL: {cik}")
    except Exception as e:
        print(f"Error getting CIK: {str(e)}")
        print(traceback.format_exc())
    
    time.sleep(3)  # Add delay between API calls
    
    # Test getting filings metadata
    print("\nTesting get_filings_metadata for AAPL (latest 10-K):")
    try:
        filings = api.edgar.get_filings_metadata("AAPL", "10-K", count=1)
        if filings and len(filings) > 0:
            print(f"Filing Date: {filings[0].get('filingDate', 'N/A')}")
            print(f"Accession Number: {filings[0].get('accessionNumber', 'N/A')}")
        else:
            print("No filings metadata retrieved")
    except Exception as e:
        print(f"Error getting filings metadata: {str(e)}")
        print(traceback.format_exc())
    
    time.sleep(3)  # Add delay between API calls
    
    # Test getting key financials
    print("\nTesting extract_key_financials for AAPL:")
    try:
        financials = api.edgar.extract_key_financials("AAPL")
        if financials and financials.get('revenue') and len(financials['revenue']) > 0:
            latest = financials['revenue'][0]
            print(f"Latest Revenue: ${latest.get('value', 0):,}")
            print(f"Period End Date: {latest.get('end_date', 'N/A')}")
        else:
            print("No financial data retrieved")
    except Exception as e:
        print(f"Error getting financial data: {str(e)}")
        print(traceback.format_exc())

def test_comprehensive_data():
    print("\n=== Testing Comprehensive Data Retrieval ===")
    api = FinancialDataAPI()
    
    print("\nTesting get_stock_data for AAPL:")
    try:
        data = api.get_stock_data("AAPL")
        print("Successfully retrieved comprehensive data")
        print(f"Basic Info: {data.get('basic_info', {}).get('name', 'N/A')}")
        print(f"Has IV Data: {'Yes' if data.get('implied_volatility') else 'No'}")
        print(f"Has SEC Data: {'Yes' if data.get('sec_data') else 'No'}")
    except Exception as e:
        print(f"Error retrieving comprehensive data: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    print("Starting Financial Data API Tests")
    
    try:
        test_yahoo_finance()
        time.sleep(5)  # Add substantial delay between test sections
    except Exception as e:
        print(f"Yahoo Finance API test failed: {str(e)}")
    
    try:
        test_sec_edgar()
        time.sleep(5)  # Add substantial delay between test sections
    except Exception as e:
        print(f"SEC EDGAR API test failed: {str(e)}")
    
    try:
        test_comprehensive_data()
    except Exception as e:
        print(f"Comprehensive data test failed: {str(e)}")
    
    print("\nTests completed")