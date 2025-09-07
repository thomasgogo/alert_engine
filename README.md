# Alert Engine

一个基于Django的智能告警管理系统，用于统一处理来自多个监控系统的告警。

## 功能特性

- **多数据源支持**: 支持Prometheus/Alertmanager、Zabbix、Grafana等监控系统
- **告警分组**: 自动将相关告警分组管理
- **智能去重**: 基于指纹识别的告警去重机制
- **规则引擎**: 灵活的规则配置，支持自定义告警处理逻辑
- **知识库**: 内置知识库，提供告警处理建议
- **工作流**: 支持自定义告警处理工作流
- **多种通知方式**: 支持邮件、Webhook等多种通知渠道

## 项目结构

```
alert-engine/
├── alert_engine/       # Django项目配置
├── alerts/            # 告警管理核心模块
├── rules/             # 规则引擎
├── knowledge/         # 知识库
├── workflows/         # 工作流管理
├── sources/           # 数据源映射
├── actions/           # 动作执行器
├── algorithms/        # 算法模块（去重、根因分析等）
└── core/             # 核心基础模块
```

## 快速开始

### 环境要求

- Python 3.8+
- Django 4.2+

### 安装步骤

1. 克隆项目
```bash
git clone https://github.com/thomasgogo/alert_engine.git
cd alert_engine
```

2. 创建虚拟环境
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置必要的环境变量
```

5. 数据库迁移
```bash
python manage.py migrate
```

6. 创建超级用户
```bash
python manage.py createsuperuser
```

7. 运行开发服务器
```bash
python manage.py runserver
```

访问 http://127.0.0.1:8000/admin/ 进入管理后台

## API 使用示例

### 接收 Alertmanager 告警

```bash
curl -X POST http://localhost:8000/api/sources/alertmanager/webhook/ \
  -H "Content-Type: application/json" \
  -d '{
    "version": "4",
    "alerts": [{
      "status": "firing",
      "labels": {
        "alertname": "HighCPU",
        "severity": "warning",
        "instance": "server01"
      },
      "annotations": {
        "description": "CPU usage is above 80%"
      }
    }]
  }'
```

### 查询告警列表

```bash
curl http://localhost:8000/api/alerts/events/
```

## 主要模块说明

### Alerts（告警管理）
- AlertEvent: 单个告警事件
- AlertGroup: 告警分组
- 支持告警状态管理（firing/resolved）

### Rules（规则引擎）
- 基于条件匹配的规则系统
- 支持多种动作（邮件、Webhook等）
- 优先级和顺序控制

### Knowledge（知识库）
- 基于模式匹配的知识库
- 自动建议解决方案
- 支持标签和优先级

### Sources（数据源）
- 支持多种监控系统的数据格式
- 统一的数据映射层
- 可扩展的适配器模式

### Algorithms（算法）
- 告警去重算法
- 根因分析
- 智能分组

## 配置说明

### 环境变量

在 `.env` 文件中配置：

```env
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=alerts@example.com
```

### 规则配置

规则支持以下条件操作符：
- `eq`: 等于
- `ne`: 不等于
- `gt`: 大于
- `lt`: 小于
- `contains`: 包含
- `in`: 在列表中

### 动作类型

- `email`: 发送邮件通知
- `webhook`: 调用Webhook
- `slack`: Slack通知（需配置）
- `sms`: 短信通知（需配置）

## 开发指南

### 运行测试

```bash
python manage.py test
```

### 批量数据导入

使用提供的脚本导入测试数据：

```bash
python bulk_data_import.py --count 1000 --batch-size 100
```

### 端到端测试

```bash
python test_e2e_flow.py
```

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 联系方式

- GitHub: [thomasgogo](https://github.com/thomasgogo)
