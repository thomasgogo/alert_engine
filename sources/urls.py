from django.urls import path
from .views import AlertmanagerWebhook, ZabbixWebhook, GrafanaWebhook

urlpatterns = [
    path('alertmanager/', AlertmanagerWebhook.as_view(), name='webhook-alertmanager'),
    path('zabbix/', ZabbixWebhook.as_view(), name='webhook-zabbix'),
    path('grafana/', GrafanaWebhook.as_view(), name='webhook-grafana'),
]

