#!/usr/bin/env python3
"""
生成 PlantUML 架构图
"""

import os
from pathlib import Path

# UML 图表定义
UML_DIAGRAMS = {
    "component_diagram": """@startuml
!define RECTANGLE class
title Alert Engine 系统组件图

package "Alert Engine System" {
  
  package "数据源层 (Data Sources)" #LightBlue {
    [Prometheus/Alertmanager] as AM
    [Zabbix Monitor] as ZB
    [Grafana Alerts] as GF
    [华为云/阿里云] as CLOUD
    [Other Sources] as OS
  }
  
  package "接入层 (Ingestion)" #LightGreen {
    [Source Views\\n数据接收] as SV
    [Data Mappers\\n数据映射] as DM
    [Alert Service\\n告警服务] as AS
  }
  
  package "处理层 (Processing)" #LightYellow {
    [Rule Engine\\n规则引擎] as RE
    [Deduplication\\n告警去重] as DD
    [Root Cause Analysis\\n根因定位] as RCA
    [Knowledge Base\\n知识库] as KB
  }
  
  package "存储层 (Storage)" #LightGray {
    database "PostgreSQL/SQLite" {
      [AlertEvent\\n告警事件]
      [AlertGroup\\n告警分组] 
      [Rule\\n规则配置]
      [KBArticle\\n知识文章]
      [Ticket\\n工单]
    }
  }
  
  package "动作层 (Actions)" #LightCoral {
    [Email Handler\\n邮件通知] as EH
    [Webhook Handler\\nWebhook] as WH
    [Ticket Creator\\n工单创建] as TC
  }
  
  AM --> SV : HTTP POST
  ZB --> SV : HTTP POST
  GF --> SV : HTTP POST
  CLOUD --> SV : HTTP POST
  OS --> SV : HTTP POST
  
  SV --> DM : 标准化
  DM --> AS : 摄入
  AS --> AlertEvent : 创建
  AS --> AlertGroup : 更新
  
  AlertEvent --> RE : 信号触发
  RE --> DD : 去重检查
  RE --> RCA : 根因分析
  RE --> KB : 知识匹配
  
  RE --> EH : 执行
  RE --> WH : 执行
  RE --> TC : 执行
}

note bottom
  功能对比：
  ✅ 监控工具集成
  ✅ 数据标准化
  ✅ 规则引擎
  ✅ 告警汇聚
  ✅ 去重算法
  ⚠️ 根因定位（基础实现）
  ✅ 知识库
  ✅ 协作流转
  ✅ 通知必达
end note

@enduml""",

    "sequence_diagram": """@startuml
title 告警处理序列图

actor "监控工具" as MT
participant "Webhook视图" as WV
participant "数据映射器" as MP
participant "告警服务" as AS
database "数据库" as DB
participant "信号处理" as SH
participant "规则引擎" as RE
participant "去重算法" as DD
participant "知识库" as KB
participant "动作处理" as AH
actor "运维人员" as OP

autonumber

MT -> WV: POST /sources/{source}/
activate WV
WV -> MP: map_{source}(payload)
activate MP
MP --> WV: 标准化数据
deactivate MP

WV -> AS: ingest_standard_alert(data)
activate AS

AS -> AS: compute_fingerprint()
note right: 计算告警指纹\\n基于source+labels+metric

AS -> DB: get_or_create AlertGroup
activate DB
DB --> AS: group
deactivate DB

AS -> DB: create AlertEvent
activate DB
DB --> AS: event
deactivate DB

AS -> SH: post_save signal
deactivate AS
activate SH

SH -> DD: should_deduplicate(event)
activate DD

alt 非重复告警
  DD --> SH: None
  deactivate DD
  SH -> RE: evaluate_rules_on_event(event)
  activate RE
  
  RE -> DB: 获取启用的规则
  activate DB
  DB --> RE: rules[]
  deactivate DB
  
  loop 匹配的规则
    RE -> KB: suggest_articles(event)
    activate KB
    KB --> RE: articles[]
    deactivate KB
    
    RE -> AH: run_action(action, event)
    activate AH
    AH -> OP: 发送通知
    deactivate AH
  end
  deactivate RE
  
else 重复告警
  DD --> SH: existing_event
  deactivate DD
  SH -> SH: 跳过处理
  note right: 60秒内的重复告警\\n将被忽略
end

deactivate SH

WV --> MT: {"ingested": count}
deactivate WV

@enduml""",

    "class_diagram": """@startuml
title 核心数据模型类图

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
  --
  + save()
  + compute_fingerprint()
}

class AlertGroup {
  - id: int
  - fingerprint: str [unique]
  - status: AlertStatus
  - count: int
  - first_seen: datetime
  - last_seen: datetime
  --
  + increment_count()
  + update_status()
}

class Rule {
  - id: int
  - name: str
  - enabled: bool
  - conditions: JSON[]
  - actions: JSON[]
  - order: int
  --
  + match(event: AlertEvent): bool
  + execute_actions(event: AlertEvent)
}

class KBArticle {
  - id: int
  - title: str
  - pattern: str
  - solution: str
  - tags: JSON[]
  - enabled: bool
  - priority: int
  --
  + matches(event: AlertEvent): bool
}

class Ticket {
  - id: int
  - title: str
  - status: AlertStatus
  - assignee: str
  - notes: str
  - created_at: datetime
  - updated_at: datetime
  --
  + assign(user: str)
  + add_note(text: str)
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
Rule "n" ..> "n" AlertEvent : processes
KBArticle "n" ..> "n" AlertEvent : suggests for

note right of AlertEvent
  核心告警事件模型
  包含所有告警元数据
end note

note right of AlertGroup
  告警分组
  相同指纹的告警聚合
end note

note right of Rule
  规则引擎配置
  条件匹配和动作执行
end note

@enduml""",

    "activity_diagram": """@startuml
title 规则引擎处理活动图

start

:接收 AlertEvent;
note right: 从信号处理器触发

:获取所有启用的规则;
note left
  按 order 字段排序
  只获取 enabled=True
end note

while (还有未处理的规则?) is (是)
  :获取下一条规则;
  
  :评估所有条件;
  note right
    条件操作符:
    * eq: 相等
    * neq: 不相等
    * contains: 包含
    * regex: 正则匹配
    * in: 在列表中
  end note
  
  if (所有条件都匹配?) then (是)
    :查询知识库文章;
    note left: 基于正则匹配\\ntitle和labels
    
    :构建上下文数据;
    note right
      包含:
      - 告警字段
      - 知识库文章
      - 元数据
    end note
    
    partition "执行动作" {
      while (还有动作?) is (是)
        :渲染模板变量;
        note left: 使用Django模板引擎
        
        if (动作类型?) then (email)
          :发送邮件通知;
          note right
            收件人: action.to[]
            主题: 渲染后的subject
            正文: 渲染后的body
          end note
        elseif (webhook)
          :调用Webhook;
          note right
            URL: action.url
            JSON: 渲染后的payload
            超时: 10秒
          end note
        else (unknown)
          :记录警告日志;
        endif
      endwhile (否)
    }
  else (否)
    :跳过该规则;
  endif
  
endwhile (否)

:返回处理结果;

stop

@enduml""",

    "deployment_diagram": """@startuml
title 部署架构图

node "监控系统" as monitoring {
  component [Prometheus] as prom
  component [Zabbix] as zab
  component [Grafana] as graf
}

node "Alert Engine 服务器" as server {
  component [Django App] as django {
    [Sources API]
    [Rules Engine]
    [Alert Service]
    [Knowledge Base]
  }
  
  database "SQLite/PostgreSQL" as db {
    [告警数据]
    [规则配置]
    [知识库]
  }
}

node "通知渠道" as channels {
  component [Email Server] as email
  component [Slack/Teams] as chat
  component [PagerDuty] as pager
}

cloud "云服务" as cloud {
  component [华为云] as hw
  component [阿里云] as ali
}

monitoring --> server : HTTP Webhooks
cloud --> server : HTTP Webhooks
server --> channels : 通知发送
django --> db : ORM

note bottom of server
  可部署方式:
  - Docker容器
  - Kubernetes Pod
  - 虚拟机
  - 物理服务器
end note

@enduml"""
}

def save_diagrams():
    """保存所有 UML 图表到文件"""
    output_dir = Path("uml_diagrams")
    output_dir.mkdir(exist_ok=True)
    
    print("生成 UML 图表文件...")
    print("=" * 50)
    
    for name, content in UML_DIAGRAMS.items():
        file_path = output_dir / f"{name}.puml"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ 已生成: {file_path}")
    
    print("\n" + "=" * 50)
    print("所有 UML 图表已生成！")
    print("\n使用方法:")
    print("1. 安装 PlantUML: brew install plantuml")
    print("2. 生成 PNG: plantuml uml_diagrams/*.puml")
    print("3. 或使用在线工具: http://www.plantuml.com/plantuml")
    
    # 生成 README
    readme_path = output_dir / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("""# Alert Engine UML 图表

## 图表列表

1. **component_diagram.puml** - 系统组件图
   - 展示系统各层架构和组件关系

2. **sequence_diagram.puml** - 告警处理序列图
   - 展示告警从接收到处理的完整流程

3. **class_diagram.puml** - 核心类图
   - 展示主要数据模型和关系

4. **activity_diagram.puml** - 规则引擎活动图
   - 展示规则评估和执行流程

5. **deployment_diagram.puml** - 部署架构图
   - 展示系统部署架构和外部集成

## 生成图片

### 方法 1: 使用 PlantUML 命令行

```bash
# 安装 PlantUML
brew install plantuml

# 生成所有图表
plantuml *.puml

# 生成特定格式
plantuml -tpng *.puml  # PNG格式
plantuml -tsvg *.puml  # SVG格式
```

### 方法 2: 使用在线工具

访问 [PlantUML Online](http://www.plantuml.com/plantuml) 并粘贴 .puml 文件内容

### 方法 3: VS Code 插件

安装 PlantUML 插件，直接在编辑器中预览和导出

## 架构总结

Alert Engine 实现了图片中展示的数据处理引擎的核心功能：

- ✅ **监控工具集成**: 支持 Prometheus, Zabbix, Grafana
- ✅ **数据标准化**: 统一的告警数据模型
- ✅ **规则引擎**: 灵活的条件匹配和动作执行
- ✅ **告警汇聚**: 基于指纹的分组聚合
- ✅ **智能去重**: 时间窗口内的重复检测
- ⚠️ **根因定位**: 基础实现，需要增强
- ✅ **知识库**: 正则匹配的解决方案推荐
- ✅ **协作流转**: 工单系统支持
- ✅ **通知必达**: 邮件和Webhook通知
""")
    
    print(f"\n✅ README 已生成: {readme_path}")

if __name__ == "__main__":
    save_diagrams()
