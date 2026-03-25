from django.urls import path
from django.views.generic import TemplateView
from .views import ChatHistoryView
 
app_name = 'chat'
 
urlpatterns = [
    # Template
    path('courses/<uuid:course_id>/chat/',
         TemplateView.as_view(template_name='chat/room.html'),
         name='room'),
 
    # API
    path('api/courses/<uuid:course_id>/chat/history/',
         ChatHistoryView.as_view(), name='history'),
]