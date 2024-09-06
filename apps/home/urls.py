from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    # Index
    path('', login_required(views.index), name="index"),

    # Dashboard
    # path('dashboard/', views.dashboard, name="dashboard"),

    
    path('accounts/login/', auth_views.LoginView.as_view(
      template_name='accounts/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(
        template_name='accounts/logged_out.html'), name='logout'),
    path('accounts/password-change/', 
         views.UserPasswordChangeView.as_view(), name='password_change'),
    path('accounts/password-change-done/', 
         auth_views.PasswordChangeDoneView.as_view(
            template_name='accounts/password-change-done.html'), 
         name="password_change_done"),
    path('accounts/password-reset/', views.UserPasswordResetView.as_view(), name="password_reset"),
    path('accounts/password-reset-confirm/<uidb64>/<token>/',
         views.UserPasswordResetConfirmView.as_view(), 
         name="password_reset_confirm"),
    path('accounts/password-reset-done/', 
         auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password-reset-done.html'), 
         name='password_reset_done'),
    path('accounts/password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password-reset-complete.html'), 
         name='password_reset_complete'),
    path('accounts/lock/', views.lock, name="lock"),
    path('error/404/', views.error_404, name="error_404"),
    path('error/500/', views.error_500, name="error_500"),
]
