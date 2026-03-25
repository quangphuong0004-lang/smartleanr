from django.urls import path
from .views import (
    NotificationListView, NotificationReadView,
    NotificationReadAllView, NotificationDeleteView,
)
 
app_name = 'notifications'
 
urlpatterns = [
    path('api/notifications/', NotificationListView.as_view(), name='list'),
    path('api/notifications/read-all/', NotificationReadAllView.as_view(), name='read-all'),
    path('api/notifications/<uuid:pk>/', NotificationReadView.as_view(), name='read'),
    path('api/notifications/<uuid:pk>/delete/', NotificationDeleteView.as_view(), name='delete'),
]