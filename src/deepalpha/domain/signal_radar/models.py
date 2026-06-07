"""信号趋势雷达领域模型"""
import datetime
from enum import Enum
from pydantic import BaseModel, Field


class SignalCategory(str, Enum):
    tech_concept = "tech_concept"
    infra_component = "infra_component"
    engineering_concept = "engineering_concept"


class RawSignalItem(BaseModel):
    ticker: str = Field(title="公司 ticker")
    source_type: str = Field(
        title="来源类型",
        description="earnings_call|capex|form_d|job_posting",
    )
    signal_date: datetime.date = Field(title="信号原始日期")
    doc_id: str = Field(title="原始文件唯一 ID")
    text_snippet: str = Field("", title="原文摘要（最多 2000 字符）")


class ExtractedTheme(BaseModel):
    name: str = Field(title="标准化主题名")
    category: SignalCategory = Field(title="主题类别")
    confidence: float = Field(ge=0.0, le=1.0, title="置信度")


class ThemeSignal(BaseModel):
    theme: ExtractedTheme = Field(title="提取的主题")
    source_type: str = Field(title="来源类型")
    ticker: str = Field(title="公司 ticker")


class DailyThemeScore(BaseModel):
    theme_name: str = Field(title="主题名")
    category: SignalCategory = Field(title="主题类别")
    score_date: datetime.date = Field(title="得分日期")
    base_score: float = Field(title="当日加权基础分")
    momentum: float = Field(title="当日动量系数")
    final_score: float = Field(title="当日最终分")
    cumulative_score: float = Field(title="历史累计分（截至当日）")
    company_count: int = Field(0, title="涉及公司数量")
    signal_breakdown: dict[str, float] = Field(
        default_factory=dict,
        title="各信号源分值明细",
    )
