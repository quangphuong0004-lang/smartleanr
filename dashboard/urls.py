from django.urls import path
from django.views.generic import TemplateView
from .views import DashboardView

app_name = 'dashboard'

urlpatterns = [
    # Template
    path('', TemplateView.as_view(template_name='dashboard/index.html'), name='index'),
    # API
    path('api/', DashboardView.as_view(), name='dashboard-api'),
]