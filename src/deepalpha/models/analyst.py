import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class AnalystRating(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: datetime.date = Field(title="评级日期", description="分析师发布评级的日期")
    rating: str | None = Field(None, title="综合评级", description="综合买卖评级，如 S+、A、B")
    rating_recommendation: str | None = Field(None, title="评级建议", description="Strong Buy / Buy / Hold / Sell")
    rating_score: int | None = Field(None, title="评级分数", description="数值化评级，1=强买 5=强卖")


class PriceTarget(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    symbol: str = Field(title="股票代码", description="交易所上市代码")
    last_month: float | None = Field(None, title="近月均价目标", description="近一个月分析师目标价均值（美元）")
    last_quarter: float | None = Field(None, title="近季均价目标", description="近一季度分析师目标价均值（美元）")
    last_year: float | None = Field(None, title="近年均价目标", description="近一年分析师目标价均值（美元）")
    all_time: float | None = Field(None, title="全期均价目标", description="全部历史分析师目标价均值（美元）")


class Estimate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    symbol: str = Field(title="股票代码", description="交易所上市代码")
    date: datetime.date = Field(title="预测日期", description="预期数据对应的财报期末日期")
    estimated_revenue_avg: float | None = Field(None, title="营收共识预测", description="分析师营收预测均值（美元）")
    estimated_eps_avg: float | None = Field(None, title="EPS 共识预测", description="分析师 EPS 预测均值（美元）")
    number_analyst_estimated_revenue: int | None = Field(None, title="营收预测人数", description="参与营收预测的分析师数量")
