#!/usr/bin/env python
"""
端到端流程验证脚本
测试从告警接收到通知发送的完整流程
"""

import os
import sys
import django
import json
from datetime import datetime
from typing import Dict, Any

# Django 环境初始化
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alert_engine.settings')
django.setup()

from alerts.models import AlertEvent, AlertGroup, AlertStatus, Severity
from rules.models import Rule
from knowledge.models import KBArticle
from alerts.services import ingest_standard_alert
from sources.mappers import map_alertmanager, map_zabbix, map_grafana
from rules.engine import evaluate_rules_on_event
from algorithms.dedupe import should_deduplicate
from algorithms.rca import simple_root_cause
from knowledge.services import suggest_articles


class E2ETestRunner:
    """端到端测试运行器"""
    
    def __init__(self):
        self.test_results = []
        
    def log(self, message: str, level: str = "INFO"):
        """记录测试日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        self.test_results.append({"time": timestamp, "level": level, "message": message})
    
    def setup_test_data(self):
        """准备测试数据"""
        self.log("=== 设置测试数据 ===")
        
        # 创建测试规则
        rule = Rule.objects.create(
            name="Critical Alert Rule",
            enabled=True,
            conditions=[
                {"path": "severity", "op": "eq", "value": "critical"},
                {"path": "labels.alertname", "op": "contains", "value": "disk"}
            ],
            actions=[
                {
                    "type": "email",
                    "to": ["ops@example.com"],
                    "subject": "[{{ severity }}] {{ title }}",
                    "body": "Alert: {{ description }}\nKB: {{ kb_articles }}"
                },
                {
                    "type": "webhook",
                    "url": "http://localhost:8080/webhook",
                    "json": {"text": "{{ title }}", "severity": "{{ severity }}"}
                }
            ],
            order=1
        )
        self.log(f"创建规则: {rule.name}")
        
        # 创建知识库文章
        kb = KBArticle.objects.create(
            title="Disk Space Issue Resolution",
            pattern="disk.*space|filesystem.*full",
            solution="1. Check disk usage with 'df -h'\n2. Clean temp files\n3. Check logs rotation",
            tags=["disk", "storage", "critical"],
            enabled=True,
            priority=10
        )
        self.log(f"创建知识库文章: {kb.title}")
        
        return rule, kb
    
    def test_alertmanager_flow(self):
        """测试 Prometheus/Alertmanager 告警流程"""
        self.log("\n=== 测试 Alertmanager 告警流程 ===")
        
        # 模拟 Alertmanager webhook payload
        payload = {
            "version": "4",
            "groupKey": "{}:{alertname=\"disk_space_low\"}",
            "status": "firing",
            "receiver": "alert-engine",
            "alerts": [
                {
                    "status": "firing",
                    "labels": {
                        "alertname": "disk_space_low",
                        "severity": "critical",
                        "instance": "server01.example.com",
                        "job": "node_exporter",
                        "namespace": "monitoring"
                    },
                    "annotations": {
                        "description": "Disk space is critically low on server01",
                        "summary": "Disk usage above 90%"
                    },
                    "startsAt": "2024-01-01T10:00:00Z",
                    "endsAt": "0001-01-01T00:00:00Z",
                    "generatorURL": "http://prometheus.example.com/graph?g0.expr=disk_usage"
                }
            ]
        }
        
        # 1. 数据映射
        self.log("步骤 1: 数据映射")
        normalized_alerts = list(map_alertmanager(payload))
        assert len(normalized_alerts) == 1, "映射失败"
        normalized = normalized_alerts[0]
        self.log(f"  源: {normalized['source']}, 标题: {normalized['title']}")
        
        # 2. 告警摄入
        self.log("步骤 2: 告警摄入")
        event = ingest_standard_alert(normalized)
        assert event.id is not None, "事件创建失败"
        self.log(f"  创建事件 ID: {event.id}, 指纹: {event.fingerprint[:8]}")
        
        # 3. 告警分组
        self.log("步骤 3: 告警分组")
        group = event.group
        assert group is not None, "分组失败"
        self.log(f"  分组 ID: {group.id}, 计数: {group.count}")
        
        # 4. 去重检测
        self.log("步骤 4: 去重检测")
        duplicate = should_deduplicate(event)
        self.log(f"  是否重复: {duplicate is not None}")
        
        # 5. 根因分析
        self.log("步骤 5: 根因分析")
        root_cause = simple_root_cause(event)
        self.log(f"  根因提示: {root_cause}")
        
        # 6. 知识库匹配
        self.log("步骤 6: 知识库匹配")
        articles = suggest_articles(event)
        self.log(f"  匹配文章数: {len(articles)}")
        for article in articles:
            self.log(f"    - {article.title}")
        
        # 7. 规则评估
        self.log("步骤 7: 规则评估")
        evaluate_rules_on_event(event)
        self.log("  规则评估完成（动作执行被模拟）")
        
        return event
    
    def test_zabbix_flow(self):
        """测试 Zabbix 告警流程"""
        self.log("\n=== 测试 Zabbix 告警流程 ===")
        
        payload = {
            "eventid": "12345",
            "event_value": "1",
            "severity": "High",
            "host": "db-server01",
            "subject": "Database connection pool exhausted",
            "message": "Connection pool is full, new connections are being rejected",
            "event_time": "2024-01-01T11:00:00Z",
            "trigger_name": "DB Connection Pool",
            "item_key": "db.connections.active"
        }
        
        normalized_alerts = list(map_zabbix(payload))
        assert len(normalized_alerts) == 1, "Zabbix 映射失败"
        
        event = ingest_standard_alert(normalized_alerts[0])
        self.log(f"  Zabbix 事件创建: ID={event.id}, 主机={event.resource}")
        
        return event
    
    def test_grafana_flow(self):
        """测试 Grafana 告警流程"""
        self.log("\n=== 测试 Grafana 告警流程 ===")
        
        payload = {
            "ruleId": 123,
            "ruleName": "API Response Time Alert",
            "state": "alerting",
            "message": "API response time is above threshold",
            "labels": {
                "severity": "warning",
                "service": "api-gateway",
                "instance": "api01.example.com"
            },
            "ruleUrl": "http://grafana.example.com/d/api-dashboard"
        }
        
        normalized_alerts = list(map_grafana(payload))
        assert len(normalized_alerts) == 1, "Grafana 映射失败"
        
        event = ingest_standard_alert(normalized_alerts[0])
        self.log(f"  Grafana 事件创建: ID={event.id}, 服务={event.service}")
        
        return event
    
    def test_deduplication(self):
        """测试去重功能"""
        self.log("\n=== 测试去重功能 ===")
        
        # 创建两个相同的告警
        alert_data = {
            "source": "test",
            "title": "Duplicate Test Alert",
            "severity": "warning",
            "labels": {"test": "dedup"},
            "description": "Testing deduplication"
        }
        
        event1 = ingest_standard_alert(alert_data)
        self.log(f"  第一个事件: ID={event1.id}")
        
        # 立即创建第二个相同告警
        event2 = ingest_standard_alert(alert_data)
        self.log(f"  第二个事件: ID={event2.id}")
        
        # 检查是否被识别为重复
        duplicate = should_deduplicate(event2)
        assert duplicate is not None, "去重检测失败"
        assert duplicate.id == event1.id, "去重识别错误"
        self.log(f"  去重成功: 事件 {event2.id} 被识别为 {event1.id} 的重复")
        
        # 检查分组计数
        group = event1.group
        group.refresh_from_db()
        self.log(f"  分组 {group.fingerprint[:8]} 计数: {group.count}")
    
    def test_resolution_flow(self):
        """测试告警解决流程"""
        self.log("\n=== 测试告警解决流程 ===")
        
        # 创建触发告警
        firing_data = {
            "source": "test",
            "title": "Resolution Test",
            "status": "firing",
            "severity": "critical",
            "labels": {"test": "resolution"}
        }
        
        firing_event = ingest_standard_alert(firing_data)
        group = firing_event.group
        self.log(f"  触发告警: ID={firing_event.id}, 组状态={group.status}")
        
        # 发送解决告警
        resolved_data = {**firing_data, "status": "resolved"}
        resolved_event = ingest_standard_alert(resolved_data)
        
        group.refresh_from_db()
        assert group.status == AlertStatus.RESOLVED, "组状态未更新"
        self.log(f"  解决告警: ID={resolved_event.id}, 组状态={group.status}")
    
    def print_summary(self):
        """打印测试摘要"""
        self.log("\n" + "="*50)
        self.log("测试摘要")
        self.log("="*50)
        
        # 统计数据库记录
        event_count = AlertEvent.objects.count()
        group_count = AlertGroup.objects.count()
        rule_count = Rule.objects.filter(enabled=True).count()
        kb_count = KBArticle.objects.filter(enabled=True).count()
        
        self.log(f"告警事件总数: {event_count}")
        self.log(f"告警分组总数: {group_count}")
        self.log(f"启用规则数: {rule_count}")
        self.log(f"知识库文章数: {kb_count}")
        
        # 严重级别分布
        self.log("\n严重级别分布:")
        for severity in Severity.choices:
            count = AlertEvent.objects.filter(severity=severity[0]).count()
            self.log(f"  {severity[1]}: {count}")
        
        # 状态分布
        self.log("\n状态分布:")
        for status in AlertStatus.choices:
            count = AlertEvent.objects.filter(status=status[0]).count()
            self.log(f"  {status[1]}: {count}")
    
    def cleanup(self):
        """清理测试数据"""
        self.log("\n=== 清理测试数据 ===")
        AlertEvent.objects.all().delete()
        AlertGroup.objects.all().delete()
        Rule.objects.all().delete()
        KBArticle.objects.all().delete()
        self.log("测试数据已清理")
    
    def run(self):
        """运行所有测试"""
        try:
            self.log("="*50)
            self.log("Alert Engine 端到端流程验证")
            self.log("="*50)
            
            # 准备测试数据
            self.setup_test_data()
            
            # 执行各项测试
            self.test_alertmanager_flow()
            self.test_zabbix_flow()
            self.test_grafana_flow()
            self.test_deduplication()
            self.test_resolution_flow()
            
            # 打印摘要
            self.print_summary()
            
            self.log("\n✅ 所有测试通过!")
            
        except Exception as e:
            self.log(f"❌ 测试失败: {str(e)}", "ERROR")
            import traceback
            traceback.print_exc()
        finally:
            # 清理
            self.cleanup()


if __name__ == "__main__":
    runner = E2ETestRunner()
    runner.run()
