# financial_data_api/yahoo_finance/models.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class StockInfo:
    """Model for basic stock information"""

    symbol: str
    name: str = ""
    sector: str = ""
    industry: str = ""
    market_cap: float = 0.0
    pe_ratio: float = 0.0
    dividend_yield: float = 0.0
    beta: float = 0.0
    fifty_two_week_high: float = 0.0
    fifty_two_week_low: float = 0.0
    avg_volume: int = 0
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary"""
        return {
            "symbol": self.symbol,
            "name": self.name,
            "sector": self.sector,
            "industry": self.industry,
            "market_cap": self.market_cap,
            "pe_ratio": self.pe_ratio,
            "dividend_yield": self.dividend_yield,
            "beta": self.beta,
            "fifty_two_week_high": self.fifty_two_week_high,
            "fifty_two_week_low": self.fifty_two_week_low,
            "avg_volume": self.avg_volume,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StockInfo":
        """Create a model from a dictionary"""
        return cls(
            symbol=data.get("symbol", ""),
            name=data.get("name", ""),
            sector=data.get("sector", ""),
            industry=data.get("industry", ""),
            market_cap=data.get("market_cap", 0.0),
            pe_ratio=data.get("pe_ratio", 0.0),
            dividend_yield=data.get("dividend_yield", 0.0),
            beta=data.get("beta", 0.0),
            fifty_two_week_high=data.get("fifty_two_week_high", 0.0),
            fifty_two_week_low=data.get("fifty_two_week_low", 0.0),
            avg_volume=data.get("avg_volume", 0),
            last_updated=data.get("last_updated", datetime.now().isoformat()),
        )


@dataclass
class OptionContract:
    """Model for option contract data"""

    contractSymbol: str
    strike: float
    expiration: str
    type: str  # 'call' or 'put'
    lastPrice: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    change: float = 0.0
    percentChange: float = 0.0
    volume: int = 0
    openInterest: int = 0
    impliedVolatility: float = 0.0
    inTheMoney: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary"""
        return {
            "contractSymbol": self.contractSymbol,
            "strike": self.strike,
            "expiration": self.expiration,
            "type": self.type,
            "lastPrice": self.lastPrice,
            "bid": self.bid,
            "ask": self.ask,
            "change": self.change,
            "percentChange": self.percentChange,
            "volume": self.volume,
            "openInterest": self.openInterest,
            "impliedVolatility": self.impliedVolatility,
            "inTheMoney": self.inTheMoney,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], option_type: str) -> "OptionContract":
        """Create a model from a dictionary"""
        return cls(
            contractSymbol=data.get("contractSymbol", ""),
            strike=data.get("strike", 0.0),
            expiration=data.get("expiration", ""),
            type=option_type,
            lastPrice=data.get("lastPrice", 0.0),
            bid=data.get("bid", 0.0),
            ask=data.get("ask", 0.0),
            change=data.get("change", 0.0),
            percentChange=data.get("percentChange", 0.0),
            volume=data.get("volume", 0),
            openInterest=data.get("openInterest", 0),
            impliedVolatility=data.get("impliedVolatility", 0.0),
            inTheMoney=data.get("inTheMoney", False),
        )


@dataclass
class ImpliedVolatilityData:
    """Model for implied volatility data"""

    symbol: str
    timestamp: str
    average_iv: float
    expirations: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary"""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp,
            "average_iv": self.average_iv,
            "expirations": self.expirations,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImpliedVolatilityData":
        """Create a model from a dictionary"""
        return cls(
            symbol=data.get("symbol", ""),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            average_iv=data.get("average_iv", 0.0),
            expirations=data.get("expirations", {}),
        )
