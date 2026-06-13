# 财报电话会议日历功能 — 设计规格

**日期**：2026-06-13
**功能**：财报电话会议日历（Earnings Call Calendar）
**状态**：已确认，待实施

---

## 概述

新增独立页面 `/earnings`，左侧为月历视图，右侧展示所选日期下纳斯达克 100 成分股的财报电话会议详情。详情包括公司简介、主要产品、AI 摘要和完整中文翻译原文。

---

## 用户决策记录

| 问题 | 选择 |
|------|------|
| 页面布局 | 独立 `/earnings` 页面，与 `/radar` 并列于导航栏 |
| 日历范围 | 跨越过去与未来；有 transcript 则可查看，未来场次标注"即将召开" |
| 公司范围 | 纳斯达克 100（`config/nasdaq100_tickers.yaml`，共 103 家） |
| 翻译策略 | 点击时实时触发 MiniMax 翻译，结果缓存到 PostgreSQL |
| 公司简介来源 | FMP CompanyProfile（已有 `FMPCompanyLoader`） |
| 架构方案 | 方案二：完整六边形架构，新建独立 `earnings_call` domain |

---

## 架构设计

### 1. Domain 层

**新建** `src/deepalpha/domain/earnings_call/`

#### `models.py`

```python
class EarningsCallEvent(BaseModel):
    """日历上某场财报电话会议（可能尚未召开）"""
    symbol: str                    # 股票代码，如 AAPL
    company_name: str              # 公司名称
    date: datetime.date            # 会议日期
    year: int                      # 财年
    quarter: int                   # 季度 1-4
    has_transcript: bool           # 是否已有原文（date <= today）

class EarningsCallTranscript(BaseModel):
    """FMP API 返回的英文原文"""
    symbol: str
    year: int
    quarter: int
    date: datetime.date
    content: str                   # 英文全文

class EarningsCallDetail(BaseModel):
    """完整处理结果，翻译后缓存到 PostgreSQL"""
    symbol: str
    year: int
    quarter: int
    date: datetime.date
    company_name: str
    description_zh: str            # 公司简介（翻译自 FMP CompanyProfile.description）
    products_zh: str               # 主要产品（MiniMax 从 CompanyProfile.description 中提炼，FMP 无结构化产品字段）
    summary_zh: str                # AI 摘要（MiniMax 提炼，约 400 字）
    transcript_zh: str             # 完整原文中文翻译
    translated_at: datetime.datetime
```

#### `protocols.py`

```python
class AbstractEarningsCallLoader(Protocol):
    async def get_events(self, start: date, end: date) -> list[EarningsCallEvent]: ...
    async def get_transcript(self, symbol: str, year: int, quarter: int) -> EarningsCallTranscript | None: ...

class AbstractEarningsCallRepo(Protocol):
    async def get_detail(self, symbol: str, year: int, quarter: int) -> EarningsCallDetail | None: ...
    async def save_detail(self, detail: EarningsCallDetail) -> None: ...
```

---

### 2. Infrastructure 层

#### `FMPEarningsCallLoader`

**新建** `src/deepalpha/infrastructure/providers/fmp/loaders/earnings_call_loader.py`

- 继承 `BaseLoader`，实现 `AbstractEarningsCallLoader`
- `get_events(start, end)`：
  - 调用 FMP `/stable/earnings-calendar?from=&to=`
  - 过滤：只保留 `nasdaq100_tickers.yaml` 中的 symbol
  - 字段映射：`has_transcript = event.date <= datetime.date.today()`
- `get_transcript(symbol, year, quarter)`：
  - 调用 FMP `/stable/earning-call-transcript?symbol=&year=&quarter=`
  - 返回 `EarningsCallTranscript`，不存在时返回 `None`

#### `EarningsCallRepo`

**新建** `src/deepalpha/infrastructure/db/earnings_call_repo.py`

- 实现 `AbstractEarningsCallRepo`
- 操作 PostgreSQL 表 `earnings_call_details`
- 主键：`(symbol, year, quarter)`
- `get_detail()`：查询缓存，未命中返回 `None`
- `save_detail()`：upsert 写入

#### PostgreSQL 表结构

```sql
CREATE TABLE earnings_call_details (
    symbol          TEXT NOT NULL,
    year            INT  NOT NULL,
    quarter         INT  NOT NULL,
    date            DATE NOT NULL,
    company_name    TEXT NOT NULL,
    description_zh  TEXT NOT NULL,
    products_zh     TEXT NOT NULL,
    summary_zh      TEXT NOT NULL,
    transcript_zh   TEXT NOT NULL,
    translated_at   TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (symbol, year, quarter)
);
```

#### 翻译

复用现有 `src/deepalpha/infrastructure/providers/minimax/translator.py`，在 Service 层调用，无需新建文件。

---

### 3. Application 层

**新建** `src/deepalpha/application/services/earnings_call_service.py`

#### `get_calendar(start, end) -> dict[str, list[EarningsCallEvent]]`

```
loader.get_events(start, end)
→ 按 date 字符串分组
→ 返回 {"2026-06-14": [EarningsCallEvent, ...], ...}
```

#### `get_detail(symbol, year, quarter) -> EarningsCallDetail`

```
1. repo.get_detail(symbol, year, quarter)
   → 命中缓存：直接返回

2. 缓存未命中：
   a. loader.get_transcript(symbol, year, quarter)
      → 无 transcript（未来场次）：raise 404
   b. company_loader.get_profile(symbol)
      → 获取 CompanyProfile（description, products 字段）
   c. MiniMax 处理（可部分并发）：
      - 翻译 profile.description → description_zh
      - 从 profile.description 中提炼主要产品列表 → products_zh（FMP 无结构化产品字段，由 AI 提炼）
      - 生成 summary_zh（基于 transcript.content，约 400 字摘要）
      - 翻译 transcript.content → transcript_zh（全文，超长时分段翻译后拼接）
   d. 构建 EarningsCallDetail，repo.save_detail() 缓存
   e. 返回 EarningsCallDetail
```

**注意**：首次请求约需 30-90 秒（取决于 transcript 长度），前端需展示加载态。

---

### 4. API 路由层

**新建** `src/deepalpha/interface/web/routers/earnings_call.py`

```
GET /earnings-call/calendar
    ?start=2026-05-01&end=2026-07-31
    Response: dict[str, list[EarningsCallEvent]]
    说明：返回日期范围内有财报会议的公司，按日期分组

GET /earnings-call/detail/{symbol}
    ?year=2026&quarter=2
    Response: EarningsCallDetail
    说明：首次调用触发翻译（慢），后续命中缓存（快）
    错误：transcript 不存在时返回 404
```

- 在 `deps.py` 注入 `EarningsCallService`（需注入 loader、repo、company_loader、minimax_api_key）
- 在 `app.py` 注册 router，prefix `/earnings-call`

---

### 5. 前端页面

**新建** `frontend/app/(pages)/earnings/page.tsx`（Client Component）

#### 页面结构

```
顶部导航（AppShell 中新增"财报日历"链接）
└── 主体（flex，全高）
    ├── 左侧面板（固定 260px）
    │   ├── 月历组件（月份切换 + 日期格）
    │   │   ├── 有会议的日期：黄色圆点
    │   │   ├── 今天：蓝色圆圈
    │   │   └── 选中日期：黄色高亮
    │   └── 当日公司列表
    │       ├── 已翻译：绿色"已翻译"标签
    │       ├── 有原文未翻译：灰色"点击翻译"标签
    │       └── 未来场次：灰色"即将召开"标签
    └── 右侧详情面板（flex-1，可滚动）
        ├── 标题区（公司名 + ticker + 季度 + 翻译状态）
        ├── 公司简介卡片
        ├── 主要产品卡片（标签形式）
        ├── AI 摘要卡片（黄色底纹）
        ├── 分隔线（"完整原文（中文翻译）"）
        └── 完整原文区（可滚动）
```

#### 数据加载逻辑

- 进入页面：调用 `GET /earnings-call/calendar?start=&end=`（前后各一个月）
- 切换月份：重新调用 calendar API
- 点击公司：调用 `GET /earnings-call/detail/{symbol}?year=&quarter=`
  - 加载中：右侧显示骨架屏 + "翻译中，约 30-90 秒..."
  - 已有缓存：立即展示

#### 导航变更

在 `frontend/components/layout/AppShell.tsx` 中新增导航链接：
```tsx
<Link href="/earnings">财报日历</Link>
```

与现有"信号雷达"(`/radar`) 并列。

---

## 新增文件清单

| 文件 | 说明 |
|------|------|
| `src/deepalpha/domain/earnings_call/__init__.py` | 模块入口 |
| `src/deepalpha/domain/earnings_call/models.py` | 领域模型 |
| `src/deepalpha/domain/earnings_call/protocols.py` | 抽象接口 |
| `src/deepalpha/infrastructure/providers/fmp/loaders/earnings_call_loader.py` | FMP 数据加载 |
| `src/deepalpha/infrastructure/db/earnings_call_repo.py` | PG 缓存仓库 |
| `src/deepalpha/application/services/earnings_call_service.py` | 业务编排服务 |
| `src/deepalpha/interface/web/routers/earnings_call.py` | FastAPI 路由 |
| `frontend/app/(pages)/earnings/page.tsx` | 前端页面 |

## 修改文件清单

| 文件 | 修改内容 |
|------|----------|
| `src/deepalpha/interface/web/app.py` | 注册 earnings_call router |
| `src/deepalpha/interface/web/deps.py` | 注入 EarningsCallService |
| `src/deepalpha/application/agent/tools.py` | 在 Services 中增加 earnings_call 字段 |
| `frontend/components/layout/AppShell.tsx` | 新增"财报日历"导航链接 |
| `frontend/app/(pages)/layout.tsx` | 确认 layout 兼容新页面（通常无需改动） |

---

## 约束与边界

- 纳斯达克 100 范围固定，不做用户自定义（当前阶段）
- 未来场次（无 transcript）只显示基本信息，不触发翻译
- 翻译结果永久缓存，不设过期（transcript 内容不会变）
- transcript 全文可能超过 MiniMax 单次 token 限制（约 8000 字），超长时分段翻译后拼接
- 公司简介和主要产品直接取自 FMP CompanyProfile 字段，不额外调用 AI 生成
