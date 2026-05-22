# DeepAlpha L0/L1/L2 Data Pipeline

量化研究平台的数据管道，支持批量和实时流处理。

## 架构

- **L0**: 数据源 (FMP, FRED, Crawlers)
- **L1**: 接入层 (Airflow, Kafka)
- **L2**: 清洗处理 (Polars, Faust, FinBERT)
- **L3**: 存储 (Parquet + DuckDB, Elasticsearch)

## 快速开始

### 1. 安装依赖

```bash
pip install -e ".[dev]"
```

### 2. 配置

```bash
cp docker/.env.example .env
# 编辑 .env 填入 API Key
```

### 3. 启动服务

```bash
cd docker
docker compose up -d
```

### 4. 运行测试

```bash
pytest tests/ -v
```

## 项目结构

```
deepalpha/
├── src/deepalpha/
│   ├── base/           # 基类
│   ├── sources/        # L0 数据源插件
│   ├── processors/     # L1/L2 处理插件
│   └── api/            # Data API Service
├── frontend/admin/     # 管理后台
├── docker/             # Docker 配置
└── tests/              # 测试
```

## 管理后台

访问 http://localhost:3000 查看统一监控中心。

## API 文档

- Data API: http://localhost:8000/docs
- Airflow: http://localhost:8080
- Kafka UI: http://localhost:8090
- Kibana: http://localhost:5601
- Grafana: http://localhost:3000
