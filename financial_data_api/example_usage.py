# example_usage.py
import json

import pandas as pd

from financial_data_api import FinancialDataAPI


def main():
    # Initialize API
    api = FinancialDataAPI()

    # Get data for Apple
    print("Fetching data for AAPL...")
    aapl_data = api.get_stock_data("AAPL")

    # Print basic information
    print("\nBasic Information:")
    print(f"Name: {aapl_data['basic_info']['name']}")
    print(f"Sector: {aapl_data['basic_info']['sector']}")
    print(f"Industry: {aapl_data['basic_info']['industry']}")
    print(f"Market Cap: ${aapl_data['basic_info']['market_cap']:,}")
    print(f"P/E Ratio: {aapl_data['basic_info']['pe_ratio']}")
    print(f"52-Week High: ${aapl_data['basic_info']['fifty_two_week_high']}")
    print(f"52-Week Low: ${aapl_data['basic_info']['fifty_two_week_low']}")

    # Print implied volatility
    if aapl_data["implied_volatility"]:
        print("\nImplied Volatility:")
        print(f"Average IV: {aapl_data['implied_volatility']['average_iv'] * 100:.2f}%")

    # Print key financials
    if (
        aapl_data["sec_data"]["key_financials"]
        and aapl_data["sec_data"]["key_financials"]["revenue"]
    ):
        print("\nLatest Revenue:")
        latest_revenue = aapl_data["sec_data"]["key_financials"]["revenue"][0]
        print(f"Value: ${latest_revenue['value']:,}")
        print(f"Period Ending: {latest_revenue['end_date']}")
        print(f"Filing Date: {latest_revenue['filing_date']}")

    # Print recent 8-K filing information
    if aapl_data["sec_data"]["recent_8k"]:
        print("\nRecent 8-K Filings:")
        for i, filing in enumerate(aapl_data["sec_data"]["recent_8k"]):
            print(
                f"{i+1}. Filed on {filing['filingDate']} - Accession Number: {filing['accessionNumber']}"
            )

    print("\nData successfully saved to MongoDB.")


if __name__ == "__main__":
    main()
