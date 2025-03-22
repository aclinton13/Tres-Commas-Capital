# financial_data_api/sec_edgar/models.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class SECFiling:
    """Model for SEC filing data"""

    ticker: str
    cik: str
    form: str
    accessionNumber: str
    filingDate: str
    primaryDocument: str
    content: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary"""
        return {
            "ticker": self.ticker,
            "cik": self.cik,
            "form": self.form,
            "accessionNumber": self.accessionNumber,
            "filingDate": self.filingDate,
            "primaryDocument": self.primaryDocument,
            "content": self.content,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SECFiling":
        """Create a model from a dictionary"""
        return cls(
            ticker=data.get("ticker", ""),
            cik=data.get("cik", ""),
            form=data.get("form", ""),
            accessionNumber=data.get("accessionNumber", ""),
            filingDate=data.get("filingDate", ""),
            primaryDocument=data.get("primaryDocument", ""),
            content=data.get("content"),
        )


@dataclass
class FinancialDataPoint:
    """Model for a single financial data point"""

    value: float
    end_date: str
    filing_date: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary"""
        return {
            "value": self.value,
            "end_date": self.end_date,
            "filing_date": self.filing_date,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FinancialDataPoint":
        """Create a model from a dictionary"""
        return cls(
            value=data.get("value", 0.0),
            end_date=data.get("end_date", ""),
            filing_date=data.get("filing_date", ""),
        )


@dataclass
class KeyFinancials:
    """Model for key financial data extracted from SEC filings"""

    ticker: str
    revenue: List[FinancialDataPoint] = field(default_factory=list)
    net_income: List[FinancialDataPoint] = field(default_factory=list)
    assets: List[FinancialDataPoint] = field(default_factory=list)
    liabilities: List[FinancialDataPoint] = field(default_factory=list)
    cash: List[FinancialDataPoint] = field(default_factory=list)
    eps: List[FinancialDataPoint] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary"""
        return {
            "ticker": self.ticker,
            "revenue": [item.to_dict() for item in self.revenue],
            "net_income": [item.to_dict() for item in self.net_income],
            "assets": [item.to_dict() for item in self.assets],
            "liabilities": [item.to_dict() for item in self.liabilities],
            "cash": [item.to_dict() for item in self.cash],
            "eps": [item.to_dict() for item in self.eps],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KeyFinancials":
        """Create a model from a dictionary"""
        financials = cls(ticker=data.get("ticker", ""))

        if "revenue" in data:
            financials.revenue = [
                FinancialDataPoint.from_dict(item) for item in data["revenue"]
            ]

        if "net_income" in data:
            financials.net_income = [
                FinancialDataPoint.from_dict(item) for item in data["net_income"]
            ]

        if "assets" in data:
            financials.assets = [
                FinancialDataPoint.from_dict(item) for item in data["assets"]
            ]

        if "liabilities" in data:
            financials.liabilities = [
                FinancialDataPoint.from_dict(item) for item in data["liabilities"]
            ]

        if "cash" in data:
            financials.cash = [
                FinancialDataPoint.from_dict(item) for item in data["cash"]
            ]

        if "eps" in data:
            financials.eps = [
                FinancialDataPoint.from_dict(item) for item in data["eps"]
            ]

        return financials
