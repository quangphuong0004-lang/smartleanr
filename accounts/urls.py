from django.urls import path
from django.views.generic import TemplateView
from .views import (RegisterView, LoginView, LogoutView, TokenRefreshView,
                    ChangePasswordView, ForgotPasswordView, ResetPasswordView,
                    ProfileView, VerifyEmailView)

app_name = 'accounts'

urlpatterns = [
    # html
    path('login/', TemplateView.as_view(template_name='accounts/login.html'), name='login-page'),
    path('register/', TemplateView.as_view(template_name='accounts/register.html'),name='register-page'),
    path('profile/', TemplateView.as_view(template_name='accounts/profile.html'), name='profile-page'),
    path('change-password/', TemplateView.as_view(template_name='accounts/change_password.html'), name='change-password-page'),
    path('forgot-password/', TemplateView.as_view(template_name='accounts/forgot_password.html'), name='forgot-password-page'),
    path('verify-email/<uuid:token>/', TemplateView.as_view(template_name='accounts/verify_email.html'), name='verify-email-page'),
    path('reset-password/', TemplateView.as_view(template_name='accounts/reset_password.html'), name='reset-password-page'),

    #api
    path('api/register/',  RegisterView.as_view(), name='register'),
    path('api/verify-email/<uuid:token>/', VerifyEmailView.as_view(), name='verify-email'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('api/profile/', ProfileView.as_view(),  name='profile'),
    path('api/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('api/forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('api/reset-password/', ResetPasswordView.as_view(), name='reset-password'),
]