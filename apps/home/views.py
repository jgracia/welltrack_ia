from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView, PasswordResetConfirmView
from django.contrib.auth import logout
from django.utils.translation import gettext_lazy as _

from django.contrib.auth.decorators import login_required
# from apps.common.models import SystemSetting
from django.conf import settings

from .forms import RegistrationForm, LoginForm, UserPasswordResetForm, UserPasswordChangeForm, UserSetPasswordForm

# Create your views here.


def index(request):
    if request.user.is_authenticated:

        context = {'segment': 'index'}
        
        return render(request, 'home/index.html', context)
    else:
        print('\nnot logged in')
        context = {'segment': 'index'}
        return render(request, 'home/index.html', context)


'''
def dashboard(request):
    context = {
        #'parent': 'dashboard',
        'segment': 'dashboard'
    }
    return render(request, 'home/dashboard.html', context)
'''


class UserPasswordChangeView(PasswordChangeView):
    """Cambia la clave de usuario."""

    template_name = 'accounts/password-change.html'
    form_class = UserPasswordChangeForm


class UserPasswordResetView(PasswordResetView):
    """Resetea la clave de usuario."""

    template_name = 'accounts/forgot-password.html'
    form_class = UserPasswordResetForm


class UserPasswordResetConfirmView(PasswordResetConfirmView):
    """Confirma cambio de clave de usuario."""

    template_name = 'accounts/reset-password.html'
    form_class = UserSetPasswordForm


# Extra
def lock(request):
    return render(request, 'accounts/lock.html')


def error_404(request):
    return render(request, 'accounts/404.html')


def error_500(request):
    return render(request, 'accounts/500.html')


def handler404(request, exception=None):
    return render(request, 'accounts/404.html')


def handler403(request, exception=None):
    return render(request, 'accounts/403.html')


def handler500(request, exception=None):
    return render(request, 'accounts/500.html')
