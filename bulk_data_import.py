#!/usr/bin/env python
"""
批量数据导入脚本
模拟生成并导入10万条告警数据用于测试
"""

import os
import sys
import django
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

# Django 环境初始化
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alert_engine.settings')
django.setup()

from alerts.models import AlertEvent, AlertGroup, AlertStatus, Severity
from rules.models import Rule
from knowledge.models import KBArticle
from alerts.services import ingest_standard_alert
from sources.mappers import map_alertmanager, map_zabbix, map_grafana

class BulkDataGenerator:
    """批量数据生成器"""
    
    def __init__(self, total_records: int = 100000):
        self.total_records = total_records
        self.start_time = datetime.now()
        self.batch_size = 1000  # 每批次处理的记录数
        
        # 预定义的数据模板
        self.severities = ['critical', 'warning', 'info', 'low']
        self.sources = ['prometheus', 'zabbix', 'grafana', 'cloudwatch', 'custom']
        self.services = [
            'api-gateway', 'database', 'cache-server', 'message-queue',
            'web-server', 'load-balancer', 'storage', 'cdn', 'monitoring'
        ]
        self.resources = [
            f'server{i:03d}.example.com' for i in range(1, 101)
        ]
        self.alert_types = [
            ('CPU Usage High', 'CPU usage above threshold'),
            ('Memory Usage High', 'Memory usage critical'),
            ('Disk Space Low', 'Disk space running out'),
            ('Network Latency', 'High network latency detected'),
            ('Service Down', 'Service health check failed'),
            ('Database Connection', 'Database connection pool exhausted'),
            ('API Response Time', 'API response time exceeded'),
            ('Error Rate High', 'Error rate above threshold'),
            ('SSL Certificate', 'SSL certificate expiring soon'),
            ('Backup Failed', 'Backup job failed')
        ]
        
        self.namespaces = ['production', 'staging', 'development', 'testing']
        self.regions = ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1']
        
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def generate_alertmanager_payload(self, index: int) -> Dict[str, Any]:
        """生成 Alertmanager 格式的告警数据"""
        alert_type = random.choice(self.alert_types)
        severity = random.choice(self.severities)
        instance = random.choice(self.resources)
        namespace = random.choice(self.namespaces)
        service = random.choice(self.services)
        
        # 随机生成时间，分布在过去30天内
        start_time = datetime.now() - timedelta(days=random.randint(0, 30))
        
        return {
            "version": "4",
            "groupKey": f"{{}}:{{alertname=\"{alert_type[0].replace(' ', '_').lower()}\"}}",
            "status": random.choice(["firing", "resolved"]),
            "receiver": "alert-engine",
            "alerts": [
                {
                    "status": random.choice(["firing", "resolved"]),
                    "labels": {
                        "alertname": f"{alert_type[0].replace(' ', '_').lower()}_{index}",
                        "severity": severity,
                        "instance": instance,
                        "job": service,
                        "namespace": namespace,
                        "region": random.choice(self.regions),
                        "env": namespace,
                        "team": random.choice(['ops', 'dev', 'sre', 'platform']),
                        "component": random.choice(['frontend', 'backend', 'database', 'cache'])
                    },
                    "annotations": {
                        "description": f"{alert_type[1]} on {instance} - Alert #{index}",
                        "summary": alert_type[0],
                        "runbook": f"https://wiki.example.com/runbook/{alert_type[0].replace(' ', '-').lower()}",
                        "dashboard": f"https://grafana.example.com/d/dashboard-{random.randint(1, 100)}"
                    },
                    "startsAt": start_time.isoformat() + "Z",
                    "endsAt": "0001-01-01T00:00:00Z" if random.random() > 0.3 else (start_time + timedelta(hours=random.randint(1, 24))).isoformat() + "Z",
                    "generatorURL": f"http://prometheus.example.com/graph?g0.expr=alert_{index}"
                }
            ]
        }
    
    def generate_zabbix_payload(self, index: int) -> Dict[str, Any]:
        """生成 Zabbix 格式的告警数据"""
        alert_type = random.choice(self.alert_types)
        host = random.choice(self.resources)
        
        severity_map = {
            'critical': 'Disaster',
            'warning': 'High',
            'info': 'Average',
            'low': 'Information'
        }
        severity = random.choice(list(severity_map.keys()))
        
        return {
            "eventid": str(100000 + index),
            "event_value": random.choice(["0", "1"]),
            "severity": severity_map[severity],
            "host": host,
            "subject": f"{alert_type[0]} - Event #{index}",
            "message": f"{alert_type[1]} detected on {host}",
            "event_time": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat() + "Z",
            "trigger_name": alert_type[0],
            "item_key": f"system.{alert_type[0].replace(' ', '.').lower()}",
            "trigger_id": str(random.randint(1000, 9999))
        }
    
    def generate_grafana_payload(self, index: int) -> Dict[str, Any]:
        """生成 Grafana 格式的告警数据"""
        alert_type = random.choice(self.alert_types)
        service = random.choice(self.services)
        instance = random.choice(self.resources)
        
        return {
            "ruleId": 1000 + index,
            "ruleName": f"{alert_type[0]} Rule #{index}",
            "state": random.choice(["alerting", "ok"]),
            "message": f"{alert_type[1]} - Grafana Alert #{index}",
            "labels": {
                "severity": random.choice(self.severities),
                "service": service,
                "instance": instance,
                "datacenter": random.choice(['dc1', 'dc2', 'dc3']),
                "cluster": random.choice(['cluster-a', 'cluster-b', 'cluster-c'])
            },
            "ruleUrl": f"http://grafana.example.com/d/dashboard-{random.randint(1, 50)}/alert-{index}",
            "evalMatches": [
                {
                    "value": random.uniform(50, 100),
                    "metric": alert_type[0].replace(' ', '_').lower(),
                    "tags": {"host": instance}
                }
            ]
        }
    
    def generate_custom_payload(self, index: int) -> Dict[str, Any]:
        """生成自定义格式的告警数据（直接标准化格式）"""
        alert_type = random.choice(self.alert_types)
        
        return {
            "source": random.choice(self.sources),
            "title": f"{alert_type[0]} - Custom Alert #{index}",
            "severity": random.choice(self.severities),
            "status": random.choice(["firing", "resolved"]),
            "service": random.choice(self.services),
            "resource": random.choice(self.resources),
            "labels": {
                "alertname": f"custom_alert_{index}",
                "environment": random.choice(self.namespaces),
                "priority": random.choice(['P1', 'P2', 'P3', 'P4']),
                "owner": random.choice(['team-a', 'team-b', 'team-c']),
                "category": random.choice(['infrastructure', 'application', 'security', 'performance'])
            },
            "description": f"{alert_type[1]} - Detailed description for alert #{index}",
            "occurred_at": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat() + "Z"
        }
    
    def process_batch(self, start_index: int, batch_size: int) -> int:
        """处理一批数据"""
        success_count = 0
        
        for i in range(start_index, min(start_index + batch_size, self.total_records)):
            try:
                # 随机选择数据源类型
                source_type = random.choice(['alertmanager', 'zabbix', 'grafana', 'custom'])
                
                if source_type == 'alertmanager':
                    payload = self.generate_alertmanager_payload(i)
                    normalized_alerts = list(map_alertmanager(payload))
                elif source_type == 'zabbix':
                    payload = self.generate_zabbix_payload(i)
                    normalized_alerts = list(map_zabbix(payload))
                elif source_type == 'grafana':
                    payload = self.generate_grafana_payload(i)
                    normalized_alerts = list(map_grafana(payload))
                else:
                    # 自定义格式，直接使用标准化数据
                    normalized_alerts = [self.generate_custom_payload(i)]
                
                # 摄入告警
                for normalized in normalized_alerts:
                    event = ingest_standard_alert(normalized)
                    success_count += 1
                    
            except Exception as e:
                self.log(f"处理记录 {i} 失败: {str(e)}", "ERROR")
        
        return success_count
    
    def run_sequential(self):
        """顺序执行导入"""
        self.log(f"开始顺序导入 {self.total_records} 条告警数据...")
        
        total_success = 0
        for batch_start in range(0, self.total_records, self.batch_size):
            batch_end = min(batch_start + self.batch_size, self.total_records)
            self.log(f"处理批次: {batch_start + 1} - {batch_end}")
            
            success = self.process_batch(batch_start, self.batch_size)
            total_success += success
            
            # 显示进度
            progress = (batch_end / self.total_records) * 100
            elapsed = (datetime.now() - self.start_time).total_seconds()
            rate = total_success / elapsed if elapsed > 0 else 0
            
            self.log(f"进度: {progress:.1f}% | 成功: {total_success} | 速率: {rate:.0f} 条/秒")
        
        return total_success
    
    def run_parallel(self, workers: int = 4):
        """并行执行导入"""
        self.log(f"开始并行导入 {self.total_records} 条告警数据 (工作线程: {workers})...")
        
        total_success = 0
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []
            
            for batch_start in range(0, self.total_records, self.batch_size):
                future = executor.submit(self.process_batch, batch_start, self.batch_size)
                futures.append(future)
            
            # 等待所有任务完成
            for i, future in enumerate(as_completed(futures)):
                success = future.result()
                total_success += success
                
                progress = ((i + 1) / len(futures)) * 100
                elapsed = (datetime.now() - self.start_time).total_seconds()
                rate = total_success / elapsed if elapsed > 0 else 0
                
                self.log(f"批次完成: {i + 1}/{len(futures)} | 进度: {progress:.1f}% | 成功: {total_success} | 速率: {rate:.0f} 条/秒")
        
        return total_success
    
    def print_statistics(self):
        """打印统计信息"""
        self.log("\n" + "="*60)
        self.log("数据导入统计")
        self.log("="*60)
        
        # 统计数据库记录
        event_count = AlertEvent.objects.count()
        group_count = AlertGroup.objects.count()
        
        self.log(f"告警事件总数: {event_count:,}")
        self.log(f"告警分组总数: {group_count:,}")
        
        # 严重级别分布
        self.log("\n严重级别分布:")
        for severity in Severity.choices:
            count = AlertEvent.objects.filter(severity=severity[0]).count()
            percentage = (count / event_count * 100) if event_count > 0 else 0
            self.log(f"  {severity[1]:10s}: {count:8,} ({percentage:5.2f}%)")
        
        # 状态分布
        self.log("\n状态分布:")
        for status in AlertStatus.choices:
            count = AlertEvent.objects.filter(status=status[0]).count()
            percentage = (count / event_count * 100) if event_count > 0 else 0
            self.log(f"  {status[1]:10s}: {count:8,} ({percentage:5.2f}%)")
        
        # 数据源分布
        self.log("\n数据源分布:")
        from django.db.models import Count
        source_stats = AlertEvent.objects.values('source').annotate(count=Count('id')).order_by('-count')[:10]
        for stat in source_stats:
            percentage = (stat['count'] / event_count * 100) if event_count > 0 else 0
            self.log(f"  {stat['source']:15s}: {stat['count']:8,} ({percentage:5.2f}%)")
        
        # 时间分布
        self.log("\n时间分布:")
        now = datetime.now()
        ranges = [
            ("最近1小时", timedelta(hours=1)),
            ("最近24小时", timedelta(days=1)),
            ("最近7天", timedelta(days=7)),
            ("最近30天", timedelta(days=30))
        ]
        
        for label, delta in ranges:
            count = AlertEvent.objects.filter(occurred_at__gte=now - delta).count()
            percentage = (count / event_count * 100) if event_count > 0 else 0
            self.log(f"  {label:10s}: {count:8,} ({percentage:5.2f}%)")
        
        # 执行时间
        elapsed = (datetime.now() - self.start_time).total_seconds()
        self.log(f"\n总执行时间: {elapsed:.2f} 秒")
        self.log(f"平均速率: {event_count / elapsed:.0f} 条/秒" if elapsed > 0 else "N/A")
    
    def setup_initial_data(self):
        """设置初始数据（规则和知识库）"""
        self.log("设置初始数据...")
        
        # 创建一些示例规则
        rules = [
            {
                "name": "Critical Alert Notification",
                "conditions": [
                    {"path": "severity", "op": "eq", "value": "critical"}
                ],
                "actions": [
                    {
                        "type": "email",
                        "to": ["oncall@example.com"],
                        "subject": "[CRITICAL] {{ title }}",
                        "body": "{{ description }}"
                    }
                ]
            },
            {
                "name": "Database Alert Handler",
                "conditions": [
                    {"path": "service", "op": "eq", "value": "database"},
                    {"path": "severity", "op": "in", "value": ["critical", "warning"]}
                ],
                "actions": [
                    {
                        "type": "webhook",
                        "url": "http://localhost:8080/database-alerts",
                        "json": {"alert": "{{ title }}", "severity": "{{ severity }}"}
                    }
                ]
            }
        ]
        
        for rule_data in rules:
            rule, created = Rule.objects.get_or_create(
                name=rule_data["name"],
                defaults={
                    "enabled": True,
                    "conditions": rule_data["conditions"],
                    "actions": rule_data["actions"],
                    "order": 1
                }
            )
            if created:
                self.log(f"  创建规则: {rule.name}")
        
        # 创建知识库文章
        kb_articles = [
            {
                "title": "High CPU Usage Resolution",
                "pattern": "cpu.*high|processor.*usage",
                "solution": "1. Check top processes\n2. Review recent deployments\n3. Scale resources if needed"
            },
            {
                "title": "Database Connection Issues",
                "pattern": "database.*connection|db.*pool",
                "solution": "1. Check connection pool settings\n2. Review database load\n3. Restart connection pool"
            },
            {
                "title": "Disk Space Management",
                "pattern": "disk.*space|filesystem.*full",
                "solution": "1. Clean temporary files\n2. Review log rotation\n3. Archive old data"
            }
        ]
        
        for kb_data in kb_articles:
            kb, created = KBArticle.objects.get_or_create(
                title=kb_data["title"],
                defaults={
                    "pattern": kb_data["pattern"],
                    "solution": kb_data["solution"],
                    "tags": ["auto-generated"],
                    "enabled": True,
                    "priority": 5
                }
            )
            if created:
                self.log(f"  创建知识库: {kb.title}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='批量导入告警数据')
    parser.add_argument('--count', type=int, default=100000, help='要生成的告警数量 (默认: 100000)')
    parser.add_argument('--batch-size', type=int, default=1000, help='批次大小 (默认: 1000)')
    parser.add_argument('--parallel', action='store_true', help='使用并行处理')
    parser.add_argument('--workers', type=int, default=4, help='并行工作线程数 (默认: 4)')
    parser.add_argument('--no-setup', action='store_true', help='跳过初始数据设置')
    
    args = parser.parse_args()
    
    # 创建生成器
    generator = BulkDataGenerator(total_records=args.count)
    generator.batch_size = args.batch_size
    
    try:
        # 设置初始数据
        if not args.no_setup:
            generator.setup_initial_data()
        
        # 执行导入
        if args.parallel:
            total_success = generator.run_parallel(workers=args.workers)
        else:
            total_success = generator.run_sequential()
        
        # 打印统计
        generator.print_statistics()
        
        generator.log(f"\n✅ 成功导入 {total_success:,} 条告警数据!")
        
    except KeyboardInterrupt:
        generator.log("\n⚠️ 导入被用户中断", "WARNING")
        generator.print_statistics()
    except Exception as e:
        generator.log(f"\n❌ 导入失败: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
