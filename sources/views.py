from typing import Any, Dict
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework import status

from alerts.services import ingest_standard_alert
from . import mappers


class AlertmanagerWebhook(APIView):
    authentication_classes: list = []
    permission_classes: list = []

    def post(self, request: Request) -> Response:
        payload: Dict[str, Any] = request.data or {}
        count = 0
        for normalized in mappers.map_alertmanager(payload):
            ingest_standard_alert(normalized)
            count += 1
        return Response({"ingested": count}, status=status.HTTP_202_ACCEPTED)


class ZabbixWebhook(APIView):
    authentication_classes: list = []
    permission_classes: list = []

    def post(self, request: Request) -> Response:
        payload: Dict[str, Any] = request.data or {}
        count = 0
        for normalized in mappers.map_zabbix(payload):
            ingest_standard_alert(normalized)
            count += 1
        return Response({"ingested": count}, status=status.HTTP_202_ACCEPTED)


class GrafanaWebhook(APIView):
    authentication_classes: list = []
    permission_classes: list = []

    def post(self, request: Request) -> Response:
        payload: Dict[str, Any] = request.data or {}
        count = 0
        for normalized in mappers.map_grafana(payload):
            ingest_standard_alert(normalized)
            count += 1
        return Response({"ingested": count}, status=status.HTTP_202_ACCEPTED)

