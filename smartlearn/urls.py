"""
URL configuration for smartlearn project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('courses/', include('courses.urls', namespace='courses')),
    path('', include('quizzes.urls', namespace='quizzes')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('', include('notifications.urls', namespace='notifications')),
    path('', include('chat.urls', namespace='chat')),
    path('', include('ai_tutor.urls', namespace='ai_tutor')),
    
]+ static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])\
    + static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)

