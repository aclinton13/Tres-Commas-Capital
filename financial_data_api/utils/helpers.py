# financial_data_api/utils/helpers.py
import json
import logging
import os
import re
from datetime import datetime, timedelta

import pandas as pd

logger = logging.getLogger(__name__)


def setup_logging(log_file=None, level=logging.INFO):
    """Set up logging configuration"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    handlers = [logging.StreamHandler()]

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(level=level, format=log_format, handlers=handlers)


def ensure_directory_exists(directory_path):
    """Ensure a directory exists, create it if it doesn't"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        logger.info(f"Created directory: {directory_path}")


def safe_json_loads(json_str, default=None):
    """Safely parse JSON string"""
    try:
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"JSON parsing error: {str(e)}")
        return default


def safe_float(value, default=0.0):
    """Safely convert a value to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """Safely convert a value to int"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def format_date(date_str, input_format="%Y-%m-%d", output_format="%Y-%m-%d"):
    """Format a date string from one format to another"""
    try:
        return datetime.strptime(date_str, input_format).strftime(output_format)
    except (ValueError, TypeError):
        return None


def extract_ticker_from_filename(filename):
    """Extract ticker symbol from a filename"""
    # Common pattern: something_TICKER_something
    match = re.search(r"_([A-Z]{1,5})_", filename.upper())
    if match:
        return match.group(1)
    return None


def calculate_moving_average(data, window):
    """Calculate moving average on a pandas Series"""
    if isinstance(data, pd.Series):
        return data.rolling(window=window).mean()
    return None


def calculate_rsi(data, window=14):
    """Calculate Relative Strength Index on a pandas Series"""
    if not isinstance(data, pd.Series):
        return None

    # Calculate daily price changes
    delta = data.diff()

    # Separate gains and losses
    gains = delta.copy()
    losses = delta.copy()
    gains[gains < 0] = 0
    losses[losses > 0] = 0
    losses = abs(losses)

    # Calculate average gains and losses
    avg_gain = gains.rolling(window=window).mean()
    avg_loss = losses.rolling(window=window).mean()

    # Calculate relative strength
    rs = avg_gain / avg_loss

    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_bollinger_bands(data, window=20, num_std=2):
    """Calculate Bollinger Bands on a pandas Series"""
    if not isinstance(data, pd.Series):
        return None

    # Calculate moving average
    middle_band = data.rolling(window=window).mean()

    # Calculate standard deviation
    std_dev = data.rolling(window=window).std()

    # Calculate upper and lower bands
    upper_band = middle_band + (std_dev * num_std)
    lower_band = middle_band - (std_dev * num_std)

    return {
        "middle_band": middle_band,
        "upper_band": upper_band,
        "lower_band": lower_band,
    }


def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    if not isinstance(data, pd.Series):
        return None

    # Calculate EMAs
    ema_fast = data.ewm(span=fast_period, adjust=False).mean()
    ema_slow = data.ewm(span=slow_period, adjust=False).mean()

    # Calculate MACD line
    macd_line = ema_fast - ema_slow

    # Calculate signal line
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

    # Calculate histogram
    histogram = macd_line - signal_line

    return {"macd_line": macd_line, "signal_line": signal_line, "histogram": histogram}


def calculate_option_greeks(
    stock_price,
    strike_price,
    time_to_expiry,
    risk_free_rate,
    implied_volatility,
    dividend_yield=0.0,
):
    """
    Calculate option Greeks (Delta, Gamma, Theta, Vega) using Black-Scholes model

    Note: This is a simplified implementation and may not be suitable for all option types
    """
    try:
        import numpy as np
        from scipy.stats import norm

        # Convert time to expiry to years if given in days
        if time_to_expiry > 1:  # Assuming days
            time_to_expiry = time_to_expiry / 365.0

        # Convert percentages to decimals
        if implied_volatility > 1:
            implied_volatility = implied_volatility / 100.0

        if risk_free_rate > 1:
            risk_free_rate = risk_free_rate / 100.0

        if dividend_yield > 1:
            dividend_yield = dividend_yield / 100.0

        # Calculate d1 and d2
        d1 = (
            np.log(stock_price / strike_price)
            + (risk_free_rate - dividend_yield + 0.5 * implied_volatility**2)
            * time_to_expiry
        ) / (implied_volatility * np.sqrt(time_to_expiry))
        d2 = d1 - implied_volatility * np.sqrt(time_to_expiry)

        # Calculate option price
        call_price = stock_price * np.exp(-dividend_yield * time_to_expiry) * norm.cdf(
            d1
        ) - strike_price * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2)
        put_price = strike_price * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(
            -d2
        ) - stock_price * np.exp(-dividend_yield * time_to_expiry) * norm.cdf(-d1)

        # Calculate Greeks for call options
        call_delta = np.exp(-dividend_yield * time_to_expiry) * norm.cdf(d1)
        put_delta = -np.exp(-dividend_yield * time_to_expiry) * norm.cdf(-d1)

        gamma = (
            np.exp(-dividend_yield * time_to_expiry)
            * norm.pdf(d1)
            / (stock_price * implied_volatility * np.sqrt(time_to_expiry))
        )

        call_theta = (
            -stock_price
            * implied_volatility
            * np.exp(-dividend_yield * time_to_expiry)
            * norm.pdf(d1)
            / (2 * np.sqrt(time_to_expiry))
            - risk_free_rate
            * strike_price
            * np.exp(-risk_free_rate * time_to_expiry)
            * norm.cdf(d2)
            + dividend_yield
            * stock_price
            * np.exp(-dividend_yield * time_to_expiry)
            * norm.cdf(d1)
        )
        put_theta = (
            -stock_price
            * implied_volatility
            * np.exp(-dividend_yield * time_to_expiry)
            * norm.pdf(d1)
            / (2 * np.sqrt(time_to_expiry))
            + risk_free_rate
            * strike_price
            * np.exp(-risk_free_rate * time_to_expiry)
            * norm.cdf(-d2)
            - dividend_yield
            * stock_price
            * np.exp(-dividend_yield * time_to_expiry)
            * norm.cdf(-d1)
        )

        vega = (
            stock_price
            * np.exp(-dividend_yield * time_to_expiry)
            * norm.pdf(d1)
            * np.sqrt(time_to_expiry)
        )

        return {
            "call_price": call_price,
            "put_price": put_price,
            "call_delta": call_delta,
            "put_delta": put_delta,
            "gamma": gamma,
            "call_theta": call_theta / 365.0,  # Convert to daily theta
            "put_theta": put_theta / 365.0,  # Convert to daily theta
            "vega": vega / 100.0,  # Convert to 1% volatility change
        }
    except ImportError:
        logger.warning("scipy not installed, unable to calculate option Greeks")
        return None
    except Exception as e:
        logger.error(f"Error calculating option Greeks: {str(e)}")
        return None


def extract_text_from_html(html_content):
    """Extract text from HTML content"""
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()

        # Get text
        text = soup.get_text()

        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())

        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))

        # Drop blank lines
        text = "\n".join(chunk for chunk in chunks if chunk)

        return text
    except ImportError:
        logger.warning("BeautifulSoup not installed, returning raw HTML")
        return html_content
    except Exception as e:
        logger.error(f"Error extracting text from HTML: {str(e)}")
        return html_content
