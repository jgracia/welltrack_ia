from django.utils import timezone
from datetime import datetime
from collections import defaultdict

from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView, PasswordResetConfirmView
from django.contrib.auth import logout
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

from django.contrib.auth.decorators import login_required
# from apps.common.models import SystemSetting
from django.conf import settings

from .forms import RegistrationForm, LoginForm, UserPasswordResetForm, UserPasswordChangeForm, UserSetPasswordForm
from apps.employee.models import EmotionAnalysis, WorkerArea, WorkShift

# Create your views here.

'''
# cuenta por turno de trabajo y fecha
def index(request):
    if request.user.is_authenticated:
        current_year = datetime.now().year
        object_list = EmotionAnalysis.objects.filter(
            recorded_at__year=current_year)
        
        work_shift_emotions = defaultdict(lambda: defaultdict(
            lambda: defaultdict(int)))
        
        for obj in object_list:
            work_shift = str(obj.profile.work_shift)
            recorded_at = obj.recorded_at
            date = recorded_at.strftime('%Y-%m-%d')
            dominant_emotion = obj.emotions_detected['dominant_emotion']
            
            work_shift_emotions[work_shift][date][dominant_emotion] += 1
        
        # Convert defaultdict to a regular dict for the context
        work_shift_emotions = {shift: {date: dict(emotions) for date, emotions in dates.items()} for shift, dates in work_shift_emotions.items()}
        
        context = {
            'segment': 'index',
            'work_shift_emotions': work_shift_emotions
        }
        
        return render(request, 'home/index.html', context)
    else:
        print('\nnot logged in')
        context = {'segment': 'index'}
        return render(request, 'home/index.html', context)
'''


def index(request):
    if request.user.is_authenticated and request.user.is_staff:
        current_year = datetime.now().year
        object_list = EmotionAnalysis.objects.filter(recorded_at__year=current_year)
        
        work_shift_emotions = defaultdict(lambda: defaultdict(int))
        emotion_counts = defaultdict(int)
        total_emotions = 0
        positive_emotion_count = 0
        negative_emotion_count = 0

        for obj in object_list:
            work_shift = str(obj.profile.work_shift)
            dominant_emotion = obj.emotions_detected['dominant_emotion']
            work_shift_emotions[work_shift][dominant_emotion] += 1

            emotion_counts[dominant_emotion] += 1
            total_emotions += 1

            if dominant_emotion in ['happy', 'neutral']:
                positive_emotion_count += 1
            else:
                negative_emotion_count += 1
        
        # Convert defaultdict to a regular dict for the context
        work_shift_emotions = {shift: dict(emotions) for shift, emotions in work_shift_emotions.items()}

        # Obtener los totales
        total_active_employees = User.objects.filter(is_active=True).count()
        total_empleados_inactivos = User.objects.filter(is_active=False).count()
        total_videos_analyzed = EmotionAnalysis.objects.count()

        # Calculate the average dominant emotion
        if total_emotions > 0:
            dominant_emotion_name = max(emotion_counts, key=emotion_counts.get)
            dominant_emotion_count = emotion_counts[dominant_emotion_name]
            dominant_emotion_percentage = (dominant_emotion_count / total_emotions) * 100
            dominant_emotion_name = _(dominant_emotion_name)
            average_positive_emotion = (positive_emotion_count / total_emotions) * 100
            average_negative_emotion = (negative_emotion_count / total_emotions) * 100
        else:
            dominant_emotion_name = _('None')
            dominant_emotion_percentage = 0
            average_positive_emotion = 0
            average_negative_emotion = 0

        #current_date = datetime.now().date()
        #print("\n=> Current Date: ", current_date)
        #print()

        # day = timezone.now()
        # formatedDay = day.strftime("%Y-%m-%d")

        # Obtener la fecha y hora actual
        #now = datetime.now()
        
        # Ajustar la hora a las 00:00
        #start_of_day = datetime(now.year, now.month, now.day)

        #worker_area_list = WorkerArea.objects.all().values(
        #    'id', 'name').order_by('name')
        #work_shift_list = WorkShift.objects.all().values(
        #    'id', 'name').order_by('name')
        context = {
            'segment': 'index',
            #'current_date': current_date.strftime('%Y-%m-%d'),
            #'worker_area_list': worker_area_list,
            #'work_shift_list': work_shift_list,
            # 'start_date': formatedDay,
            # 'end_date': formatedDay,
            # 'start_date_time': day.strftime("%Y-%m-%d %H:%M"),
            # 'end_date_time': day.strftime("%Y-%m-%d %H:%M"),
            #'start_date_time': start_of_day.strftime("%Y-%m-%d %H:%M"),
            #'end_date_time': datetime.now().strftime("%Y-%m-%d %H:%M"),
            #'work_shift_emotions': work_shift_emotions,
            'total_employees': total_active_employees,
            'total_empleados_inactivos': total_empleados_inactivos,
            'total_videos_analyzed': total_videos_analyzed,
            'dominant_emotion_name': dominant_emotion_name,
            'dominant_emotion_percentage': round(dominant_emotion_percentage, 2),
            'average_positive_emotion': round(average_positive_emotion, 2),
            'average_negative_emotion': round(average_negative_emotion, 2)
        }
        
        return render(request, 'home/index.html', context)
    elif request.user.is_authenticated:
        return redirect('employee:me')

    #else:
    #    print('\nnot logged in')
    #    context = {'segment': 'index'}
    #    return render(request, 'home/index.html', context)



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
