# Alert Engine 架构分析报告

## 一、功能对比分析

根据代码审查，alert-engine 系统功能与图片中展示的数据处理引擎架构基本一致，以下是详细对比：

### ✅ 已实现的核心功能

| 图片功能模块 | 代码实现情况 | 实现位置 |
|------------|------------|---------|
| **监控工具集成** | ✅ 已实现 | `sources/` 模块 |
| - Zabbix | ✅ 支持 | `sources/mappers.py:map_zabbix()` |
| - Prometheus (Alertmanager) | ✅ 支持 | `sources/mappers.py:map_alertmanager()` |
| - Grafana | ✅ 支持 | `sources/mappers.py:map_grafana()` |
| - 华为云等 | ⚠️ 可扩展 | 通过添加新的 mapper 实现 |
| **数据标准化** | ✅ 已实现 | `sources/mappers.py` |
| **规则引擎** | ✅ 已实现 | `rules/engine.py` |
| **告警汇聚** | ✅ 已实现 | `alerts/services.py` (AlertGroup) |
| **智能算法** | ⚠️ 部分实现 | `algorithms/` 模块 |
| - 去重 | ✅ 已实现 | `algorithms/dedupe.py` |
| - 根因定位 | ⚠️ 基础实现 | `algorithms/rca.py` (简单实现) |
| **知识库** | ✅ 已实现 | `knowledge/` 模块 |
| **协作流转** | ✅ 已实现 | `workflows/` + `actions/` |
| **通知必达** | ✅ 已实现 | `actions/handlers.py` |

### ⚠️ 差异和待改进项

1. **根因定位算法**: 当前实现较为简单，仅基于 service/namespace 标签
2. **解决方案推荐**: 知识库匹配基于正则，可考虑引入 AI/ML
3. **问题处理流程**: Ticket 系统基础，缺少完整的工单流转状态机

## 二、代码质量评估

### 优点
1. **模块化设计清晰**: 各功能模块职责分明
2. **Django 最佳实践**: 使用了信号、事务、ORM 等特性
3. **扩展性良好**: 新数据源和动作类型易于添加
4. **数据一致性**: 使用事务和锁保证数据完整性

### 改进建议
1. **异步处理**: 规则评估可改为异步，提高吞吐量
2. **缓存机制**: 添加 Redis 缓存热点数据
3. **监控指标**: 添加 Prometheus metrics 暴露系统指标
4. **错误处理**: 加强异常处理和重试机制
5. **测试覆盖**: 需要添加单元测试和集成测试

## 三、系统架构UML图

### 3.1 组件图

```plantuml
@startuml
!define RECTANGLE class

package "Alert Engine System" {
  
  package "Data Sources Layer" {
    [Prometheus/Alertmanager] as AM
    [Zabbix Monitor] as ZB
    [Grafana Alerts] as GF
    [Other Sources] as OS
  }
  
  package "Ingestion Layer" {
    [Source Views] as SV
    [Data Mappers] as DM
    [Alert Service] as AS
  }
  
  package "Processing Layer" {
    [Rule Engine] as RE
    [Deduplication] as DD
    [Root Cause Analysis] as RCA
    [Knowledge Base] as KB
  }
  
  package "Storage Layer" {
    database "PostgreSQL/SQLite" {
      [AlertEvent]
      [AlertGroup] 
      [Rule]
      [KBArticle]
      [Ticket]
    }
  }
  
  package "Action Layer" {
    [Email Handler] as EH
    [Webhook Handler] as WH
    [Ticket Creator] as TC
  }
  
  AM --> SV : HTTP POST
  ZB --> SV : HTTP POST
  GF --> SV : HTTP POST
  OS --> SV : HTTP POST
  
  SV --> DM : normalize
  DM --> AS : ingest
  AS --> AlertEvent : create
  AS --> AlertGroup : update
  
  AlertEvent --> RE : signal
  RE --> DD : check
  RE --> RCA : analyze
  RE --> KB : suggest
  
  RE --> EH : execute
  RE --> WH : execute
  RE --> TC : execute
}

@enduml
```

### 3.2 序列图 - 告警处理流程

```plantuml
@startuml
actor "Monitoring Tool" as MT
participant "Webhook View" as WV
participant "Mapper" as MP
participant "Alert Service" as AS
participant "Database" as DB
participant "Signal Handler" as SH
participant "Rule Engine" as RE
participant "Dedupe Algorithm" as DD
participant "Knowledge Base" as KB
participant "Action Handler" as AH
actor "Operator" as OP

MT -> WV: POST /sources/{source}/
WV -> MP: map_{source}(payload)
MP -> WV: normalized_data
WV -> AS: ingest_standard_alert(data)

AS -> AS: compute_fingerprint()
AS -> DB: get_or_create AlertGroup
AS -> DB: create AlertEvent
DB -> AS: event

AS -> SH: post_save signal
SH -> DD: should_deduplicate(event)
alt Not Duplicate
  DD -> SH: None
  SH -> RE: evaluate_rules_on_event(event)
  
  RE -> DB: fetch enabled Rules
  loop for each matching rule
    RE -> KB: suggest_articles(event)
    KB -> RE: articles[]
    RE -> AH: run_action(action, event)
    AH -> OP: send notification
  end
else Is Duplicate
  DD -> SH: existing_event
  SH -> SH: skip processing
end

WV -> MT: {"ingested": count}

@enduml
```

### 3.3 类图 - 核心模型

```plantuml
@startuml
class AlertEvent {
  - id: int
  - source: str
  - external_id: str
  - status: AlertStatus
  - severity: Severity
  - title: str
  - description: str
  - labels: JSON
  - annotations: JSON
  - fingerprint: str
  - starts_at: datetime
  - ends_at: datetime
  - resource: str
  - service: str
  - metric: str
  - namespace: str
  - generator_url: URL
  - created_at: datetime
  - updated_at: datetime
  + save()
}

class AlertGroup {
  - id: int
  - fingerprint: str
  - status: AlertStatus
  - count: int
  - first_seen: datetime
  - last_seen: datetime
}

class Rule {
  - id: int
  - name: str
  - enabled: bool
  - conditions: JSON[]
  - actions: JSON[]
  - order: int
}

class KBArticle {
  - id: int
  - title: str
  - pattern: str
  - solution: str
  - tags: JSON[]
  - enabled: bool
  - priority: int
}

class Ticket {
  - id: int
  - title: str
  - status: AlertStatus
  - assignee: str
  - notes: str
  - created_at: datetime
  - updated_at: datetime
}

enum AlertStatus {
  FIRING
  RESOLVED
  ACKED
}

enum Severity {
  CRITICAL
  HIGH
  WARNING
  INFO
  OK
}

AlertEvent "n" --> "1" AlertGroup : belongs to
Ticket "n" --> "1" AlertGroup : references
AlertEvent ..> AlertStatus : uses
AlertEvent ..> Severity : uses
Ticket ..> AlertStatus : uses

@enduml
```

### 3.4 活动图 - 规则引擎处理流程

```plantuml
@startuml
start
:接收 AlertEvent;

:获取所有启用的规则;

while (还有规则?) is (是)
  :获取下一条规则;
  
  :评估条件;
  note right
    条件类型:
    - eq: 相等
    - neq: 不相等
    - contains: 包含
    - regex: 正则匹配
    - in: 在列表中
  end note
  
  if (所有条件都匹配?) then (是)
    :查询知识库文章;
    :构建上下文数据;
    
    while (还有动作?) is (是)
      :渲染模板变量;
      
      if (动作类型?) then (email)
        :发送邮件通知;
      elseif (webhook)
        :调用Webhook;
      else (unknown)
        :记录警告日志;
      endif
    endwhile (否)
  else (否)
    :跳过该规则;
  endif
  
endwhile (否)

stop
@enduml
```

## 四、流程验证脚本

创建一个端到端的验证脚本来测试整个流程：
