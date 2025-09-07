from rest_framework import generics
from .models import AlertEvent
from .serializers import AlertEventSerializer


class AlertEventListCreateView(generics.ListCreateAPIView):
    queryset = AlertEvent.objects.order_by('-created_at')
    serializer_class = AlertEventSerializer

