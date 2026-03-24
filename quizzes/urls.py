from django.urls import path
from django.views.generic import TemplateView
from .views import (
    QuizListView, QuizDetailView,
    QuestionListView, QuestionDetailView,
    QuizStartView, QuizSubmitView,
    QuizResultView, QuizAttemptsView,
)

app_name = 'quizzes'

urlpatterns = [
    # Template pages
    path('courses/<uuid:course_pk>/quizzes/',
         TemplateView.as_view(template_name='quizzes/list.html'),
         name='list'),

    path('courses/<uuid:course_pk>/quizzes/create/',
         TemplateView.as_view(template_name='quizzes/create_edit.html'),
         name='create'),

    path('courses/<uuid:course_pk>/quizzes/<uuid:quiz_pk>/',
         TemplateView.as_view(template_name='quizzes/detail.html'),
         name='detail'),

    path('courses/<uuid:course_pk>/quizzes/<uuid:quiz_pk>/edit/',
         TemplateView.as_view(template_name='quizzes/create_edit.html'),
         name='edit'),

    path('courses/<uuid:course_pk>/quizzes/<uuid:quiz_pk>/take/',
         TemplateView.as_view(template_name='quizzes/take.html'),
         name='take'),

    path('courses/<uuid:course_pk>/quizzes/<uuid:quiz_pk>/result/<uuid:attempt_pk>/',
         TemplateView.as_view(template_name='quizzes/result.html'),
         name='result'),

    # API
    path('api/courses/<uuid:course_pk>/quizzes/',
         QuizListView.as_view(), name='quiz-list'),

    path('api/courses/<uuid:course_pk>/quizzes/<uuid:quiz_pk>/',
         QuizDetailView.as_view(), name='quiz-detail'),

    path('api/courses/<uuid:course_pk>/quizzes/<uuid:quiz_pk>/questions/',
         QuestionListView.as_view(), name='question-list'),

    path('api/courses/<uuid:course_pk>/quizzes/<uuid:quiz_pk>/questions/<uuid:question_pk>/',
         QuestionDetailView.as_view(), name='question-detail'),

    path('api/courses/<uuid:course_pk>/quizzes/<uuid:quiz_pk>/start/',
         QuizStartView.as_view(), name='quiz-start'),

    path('api/courses/<uuid:course_pk>/quizzes/<uuid:quiz_pk>/attempts/<uuid:attempt_pk>/submit/',
         QuizSubmitView.as_view(), name='quiz-submit'),

    path('api/courses/<uuid:course_pk>/quizzes/<uuid:quiz_pk>/attempts/<uuid:attempt_pk>/result/',
         QuizResultView.as_view(), name='quiz-result'),

    path('api/courses/<uuid:course_pk>/quizzes/<uuid:quiz_pk>/attempts/',
         QuizAttemptsView.as_view(), name='quiz-attempts'),
]