from django.urls import path
from .views import AlertEventListCreateView

urlpatterns = [
    path('', AlertEventListCreateView.as_view(), name='alert-list-create'),
]

