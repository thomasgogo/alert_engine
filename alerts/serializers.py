from rest_framework import serializers
from .models import AlertEvent


class AlertEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertEvent
        fields = '__all__'

