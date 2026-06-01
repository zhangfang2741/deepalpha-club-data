"""财务领域模型（domain 层）"""

import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class IncomeStatement(BaseModel):
    """利润表（损益表）数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: datetime.date = Field(title="报告日期", description="财务报告截止日期")
    period: str = Field(title="报告期", description="annual / Q1 / Q2 / Q3 / Q4")
    revenue: float | None = Field(None, title="营业收入", description="总营收（美元）")
    gross_profit: float | None = Field(None, title="毛利润", description="营收减去销售成本")
    operating_income: float | None = Field(None, title="营业利润", description="扣除经营费用后的利润")
    net_income: float | None = Field(None, title="净利润", description="最终归属股东利润（美元）")
    eps: float | None = Field(None, title="每股收益", description="基本 EPS（美元）")
    eps_diluted: float | None = Field(None, title="稀释每股收益", description="稀释后 EPS（美元）")
    ebitda: float | None = Field(None, title="EBITDA", description="息税折旧摊销前利润（美元）")


class BalanceSheet(BaseModel):
    """资产负债表数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: datetime.date = Field(title="报告日期", description="资产负债表截止日期")
    period: str = Field(title="报告期", description="annual / Q1 / Q2 / Q3 / Q4")
    total_assets: float | None = Field(None, title="总资产", description="资产总计（美元）")
    total_liabilities: float | None = Field(None, title="总负债", description="负债合计（美元）")
    total_stockholders_equity: float | None = Field(None, title="股东权益", description="净资产（美元）")
    cash_and_cash_equivalents: float | None = Field(None, title="现金及等价物", description="货币资金（美元）")
    total_debt: float | None = Field(None, title="总债务", description="长短期债务合计（美元）")
    net_debt: float | None = Field(None, title="净债务", description="总债务减现金（美元）")


class CashFlow(BaseModel):
    """现金流量表数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: datetime.date = Field(title="报告日期", description="现金流量表截止日期")
    period: str = Field(title="报告期", description="annual / Q1 / Q2 / Q3 / Q4")
    operating_cash_flow: float | None = Field(None, title="经营活动现金流", description="核心运营产生的现金（美元）")
    capital_expenditure: float | None = Field(None, title="资本支出", description="购置固定资产等投资支出（美元）")
    free_cash_flow: float | None = Field(None, title="自由现金流", description="经营现金流减资本支出（美元）")
    dividends_paid: float | None = Field(None, title="已支付股息", description="向股东支付的现金股息（美元）")


class FinancialRatio(BaseModel):
    """财务比率数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: datetime.date = Field(title="报告日期", description="财务比率计算基准日期")
    period: str = Field(title="报告期", description="annual / Q1 / Q2 / Q3 / Q4")
    current_ratio: float | None = Field(None, title="流动比率", description="流动资产/流动负债")
    gross_profit_margin: float | None = Field(None, title="毛利率", description="毛利润/营收")
    operating_profit_margin: float | None = Field(None, title="营业利润率", description="营业利润/营收")
    net_profit_margin: float | None = Field(None, title="净利润率", description="净利润/营收")
    return_on_equity: float | None = Field(None, title="净资产收益率", description="ROE = 净利润/股东权益")
    return_on_assets: float | None = Field(None, title="总资产收益率", description="ROA = 净利润/总资产")
    debt_equity_ratio: float | None = Field(None, title="资产负债率", description="总债务/股东权益")


class KeyMetrics(BaseModel):
    """关键财务指标数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: datetime.date = Field(title="报告日期", description="关键指标计算基准日期")
    period: str = Field(title="报告期", description="annual / Q1 / Q2 / Q3 / Q4")
    pe_ratio: float | None = Field(None, title="市盈率", description="Price/Earnings")
    price_to_book: float | None = Field(None, title="市净率", description="Price/Book Value")
    price_to_sales: float | None = Field(None, title="市销率", description="Price/Sales")
    ev_to_ebitda: float | None = Field(None, title="EV/EBITDA", description="企业价值/EBITDA")
    free_cash_flow_per_share: float | None = Field(None, title="每股自由现金流", description="FCF/总股数（美元）")
    earnings_yield: float | None = Field(None, title="盈利收益率", description="EPS/Price，市盈率的倒数")


class Valuation(BaseModel):
    """估值数据"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    symbol: str = Field(title="股票代码", description="交易所上市代码")
    dcf: float | None = Field(None, title="DCF 内在价值", description="现金流折现法估算的每股内在价值（美元）")
    stock_price: float | None = Field(None, title="当前股价", description="估值时的市场价格（美元）")
