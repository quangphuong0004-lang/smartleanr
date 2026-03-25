from django.urls import path
from django.views.generic import TemplateView
from .views import SessionListView, SessionDetailView, ChatView
 
app_name = 'ai_tutor'
 
urlpatterns = [
    # Template
    path('ai-tutor/',
         TemplateView.as_view(template_name='ai_tutor/index.html'),
         name='index'),
 
    # API
    path('api/ai-tutor/sessions/',
         SessionListView.as_view(), name='session-list'),
 
    path('api/ai-tutor/sessions/<uuid:session_id>/',
         SessionDetailView.as_view(), name='session-detail'),
 
    path('api/ai-tutor/sessions/<uuid:session_id>/chat/',
         ChatView.as_view(), name='chat'),
]