from django.db import models


class KBArticle(models.Model):
    title = models.CharField(max_length=200)
    pattern = models.CharField(max_length=500, help_text="Regex to match title or labels")
    solution = models.TextField()
    tags = models.JSONField(default=list, blank=True)
    enabled = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "kb_article"
        ordering = ["-priority", "id"]

    def __str__(self) -> str:
        return self.title

