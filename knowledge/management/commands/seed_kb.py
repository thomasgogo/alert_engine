from django.core.management.base import BaseCommand
from knowledge.models import KBArticle


class Command(BaseCommand):
    help = "Seed a sample KB article for demo purposes"

    def handle(self, *args, **options):
        KBArticle.objects.get_or_create(
            title="CPU 高负载处理方法",
            pattern=r"CPU|cpu|HighLoad|高负载",
            defaults={
                "solution": "1) 登录主机查看 top; 2) 定位占用进程; 3) 检查最近发布/任务; 4) 视情况扩容或限流。",
                "tags": ["cpu", "performance"],
                "priority": 10,
            },
        )
        self.stdout.write(self.style.SUCCESS("Seeded demo KB article (idempotent)"))

