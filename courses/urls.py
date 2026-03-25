from django.urls import path
from django.views.generic import TemplateView
from .views import (
    CourseListView, CourseDetailView, MyCourseListView,
    EnrollView, EnrollmentManageView, LessonListView,
    LessonDetailView, LessonCompleteView, CourseProgressView,
    JoinByCodeView, CourseQRView, RegenerateCodeView
)
 
app_name = 'courses'

urlpatterns = [
    # Template
    path('', TemplateView.as_view(template_name='courses/list.html'), name='list'),
    path('my/', TemplateView.as_view(template_name='courses/my.html'), name='my'),
    path('create/', TemplateView.as_view(template_name='courses/create_edit.html'), name='create'),
    path('join/', TemplateView.as_view(template_name='courses/join.html'), name='join'),
    path('<uuid:pk>/', TemplateView.as_view(template_name='courses/detail.html'), name='detail'),
    path('<uuid:pk>/edit/', TemplateView.as_view(template_name='courses/create_edit.html'), name='edit'),
    path('<uuid:pk>/lessons/new/', TemplateView.as_view(template_name='courses/lesson_create_edit.html'), name='lesson-create'),
    path('<uuid:pk>/lessons/<uuid:lid>/edit/', TemplateView.as_view(template_name='courses/lesson_create_edit.html'), name='lesson-edit'),
    path('<uuid:pk>/lessons/<uuid:lid>/', TemplateView.as_view(template_name='courses/lesson_detail.html'), name='lesson'),
    path('<uuid:pk>/enrollments/', TemplateView.as_view(template_name='courses/enrollments.html'), name='enrollments-page'),

    #api
    path('api/', CourseListView.as_view(), name='course-list'),
    path('api/my/', MyCourseListView.as_view(), name='my-courses'),
    path('api/join/', JoinByCodeView.as_view(), name='join-by-code'),
    path('api/<uuid:pk>/', CourseDetailView.as_view(), name='course-detail'),
    path('api/<uuid:pk>/enroll/', EnrollView.as_view(), name='enroll'),
    path('api/<uuid:pk>/enrollments/', EnrollmentManageView.as_view(), name='enrollments'),
    path('api/<uuid:pk>/enrollments/<uuid:enroll_id>/', EnrollmentManageView.as_view(), name='enrollment-manage'),
    path('api/<uuid:pk>/lessons/', LessonListView.as_view(), name='lesson-list'),
    path('api/<uuid:pk>/lessons/<uuid:lesson_id>/', LessonDetailView.as_view(), name='lesson-detail'),
    path('api/<uuid:pk>/lessons/<uuid:lesson_id>/complete/', LessonCompleteView.as_view(), name='lesson-complete'),
    path('api/<uuid:pk>/progress/', CourseProgressView.as_view(), name='course-progress'),
    path('api/<uuid:pk>/qr/', CourseQRView.as_view(), name='course-qr'),
    path('api/<uuid:pk>/regenerate-code/', RegenerateCodeView.as_view(), name='regenerate-code'),
]
