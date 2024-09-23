from django.db.models import Q
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView
from django.utils.translation import gettext_lazy as _
from http import HTTPStatus  # enviar estado error en ajax
from django.db.models.deletion import RestrictedError
from django.contrib.auth.models import User
from django.utils.timezone import localtime  # Para ajustar la zona horaria local

from .models import (
    Profile,
    WorkerArea,
    WorkShift,
    EmotionAnalysis
)

from .forms import (
    WorkerAreaForm,
    WorkShiftForm,
    # EmployeeForm
    SignUpForm,
    UpdateProfileForm,
    UpdateUserForm,
    EmotionAnalysisForm
)

# paquetes para el algoritmo
from django.conf import settings
import os
import cv2
from collections import defaultdict
import time
from deepface import DeepFace
from datetime import datetime

# paquetes para barra de progreso
from celery.result import AsyncResult
import json
from .task import analyze_video_task
# Create your views here.

'''
def employee_list(request):
    context = {'segment': 'employee'}
    template = loader.get_template('employee/employee_list.html')
    return HttpResponse(template.render(context, request))
'''


class MixinFormInvalid:
    def form_invalid(self, form):
        response = super().form_invalid(form)
        is_ajax = self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            return JsonResponse(form.errors, status=400)
        else:
            return response


class EmployeeListView(ListView):
    """Devuelve lista de perfiles de empeados."""

    template_name = 'employee/employee_list.html'

    def get_queryset(self):
        employee_list = Profile.objects.filter(user__is_active=True)
        return employee_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segment"] = 'employee'
        return context


'''
class EmployeeNew(SuccessMessageMixin, MixinFormInvalid, CreateView):
    model = User
    template_name = "employee/employee_form.html"
    context_object_name = "obj"
    form_class = EmployeeForm
    success_url = reverse_lazy("employee:employee_list")
    success_message = _("Success: The new employee was created successfully.")


class EmployeeEdit(SuccessMessageMixin, MixinFormInvalid, UpdateView):
    model = User
    template_name = "employee/employee_form.html"
    context_object_name = "obj"
    form_class = EmployeeForm
    success_url = reverse_lazy("employee:employee_list")
    success_message = _("Success: Employee successfully modified.")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            is_ajax = self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            if is_ajax:
                return JsonResponse({
                    'success': True,
                })
            else:
                return response

        except Exception as e:
            # logging.error("Error: " + str(e))
            # print("\n-> Error al guardar reforma...")
            return JsonResponse({
                'status': HTTPStatus.INTERNAL_SERVER_ERROR.value,
                # 'message': _(str(err))
                'message': str(e),
            }, status=500)
'''


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()  # load the profile instance created by the signal
            user.profile.birth_date = form.cleaned_data.get('birth_date')
            user.profile.identity_document = form.cleaned_data.get('identity_document')
            user.profile.work_shift = form.cleaned_data.get('work_shift')
            user.profile.worker_area = form.cleaned_data.get('worker_area')
            user.save()
            # raw_password = form.cleaned_data.get('password1')
            # user = authenticate(username=user.username, password=raw_password)
            # login(request, user)
            return redirect('employee:employee_list')
    else:
        form = SignUpForm()
    return render(request, 'employee/signup.html', {'form': form})


def edit_employee(request, pk):
    print("\n=> Parpam pk = ", pk)

    employee = User.objects.get(pk=pk)
    if request.method == 'POST':
        user_form = UpdateUserForm(request.POST, instance=employee)
        profile_form = UpdateProfileForm(
            request.POST, request.FILES, instance=employee.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            # messages.success(request, 'Tu perfil se actualizo con exito')
            messages.add_message(request, messages.INFO,
                                 _('The employee was successfully updated!'))
            return redirect(to='employee:employee_list')
        else:
            # invalid form ajax
            return JsonResponse(user_form.errors, status=400)

    else:
        user_form = UpdateUserForm(instance=employee)
        profile_form = UpdateProfileForm(instance=employee.profile)

    return render(request, 'employee/update_employee_form.html', {
        'user_form': user_form, 'profile_form': profile_form, 'pk': pk})


def profile(request):
    return render(request, 'employee/profile.html', {})


def edit_profile(request):
    if request.method == 'POST':
        user_form = UpdateUserForm(request.POST, instance=request.user)
        profile_form = UpdateProfileForm(
            request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            # messages.success(request, 'Tu perfil se actualizo con exito')
            messages.add_message(request, messages.INFO,
                                 _('Your profile is successfully updated!'))
            return redirect(to='employee:users-profile')
        else:
            # invalid form ajax
            return JsonResponse(user_form.errors, status=400)

    else:
        user_form = UpdateUserForm(instance=request.user)
        profile_form = UpdateProfileForm(instance=request.user.profile)

    return render(request, 'employee/update_profile_form.html', {
        'user_form': user_form, 'profile_form': profile_form})


def employee_delete(request, pk):
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            user = User.objects.get(pk=pk)

            try:
                user.delete()

                messages.add_message(request, messages.INFO,
                                     _('Record deleted successfully.'))

                return JsonResponse({
                    'success': True,
                })

            except RestrictedError as err:
                response = JsonResponse({'status': 'false',
                                         'message': str(err)
                                         }, status=500)
                return response


class WorkerAreaListView(ListView):
    """Devuelve lista de áreas de trabajo."""

    template_name = 'employee/worker_area/worker_area_list.html'

    def get_queryset(self):
        worker_area_list = WorkerArea.objects.all()
        return worker_area_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segment"] = 'worker-area'
        return context


class WorkerAreaNew(SuccessMessageMixin, MixinFormInvalid, CreateView):
    model = WorkerArea
    template_name = "employee/worker_area/worker_area_form.html"
    context_object_name = "obj"
    form_class = WorkerAreaForm
    success_url = reverse_lazy("employee:worker_area_list")
    success_message = _("Success: The new workspace was created successfully.")


class WorkerAreaEdit(SuccessMessageMixin, MixinFormInvalid, UpdateView):
    model = WorkerArea
    template_name = "employee/worker_area/worker_area_form.html"
    context_object_name = "obj"
    form_class = WorkerAreaForm
    success_url = reverse_lazy("employee:worker_area_list")
    success_message = _("Success: Work area successfully modified.")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            is_ajax = self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            if is_ajax:
                return JsonResponse({
                    'success': True,
                })
            else:
                return response

        except Exception as e:
            # logging.error("Error: " + str(e))
            # print("\n-> Error al guardar reforma...")
            return JsonResponse({
                'status': HTTPStatus.INTERNAL_SERVER_ERROR.value,
                # 'message': _(str(err))
                'message': str(e),
            }, status=500)


def worker_area_delete(request, pk):
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            area = WorkerArea.objects.get(pk=pk)

            try:
                area.delete()

                messages.add_message(request, messages.INFO,
                                     _('Record deleted successfully.'))

                return JsonResponse({
                    'success': True,
                })

            except RestrictedError as err:
                response = JsonResponse({'status': 'false',
                                         'message': str(err)
                                         }, status=500)
                return response


class WorkShiftListView(ListView):
    """Devuelve lista de turnos de trabajo."""

    template_name = 'employee/work_shift/work_shift_list.html'

    def get_queryset(self):
        work_shift_list = WorkShift.objects.all()
        return work_shift_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segment"] = 'work-shift'
        return context


class WorkShiftNew(SuccessMessageMixin, MixinFormInvalid, CreateView):
    model = WorkShift
    template_name = "employee/work_shift/work_shift_form.html"
    context_object_name = "obj"
    form_class = WorkShiftForm
    success_url = reverse_lazy("employee:work_shift_list")
    success_message = _("Success: The new work shift was created successfully.")


class WorkShiftEdit(SuccessMessageMixin, MixinFormInvalid, UpdateView):
    model = WorkShift
    template_name = "employee/work_shift/work_shift_form.html"
    context_object_name = "obj"
    form_class = WorkShiftForm
    success_url = reverse_lazy("employee:work_shift_list")
    success_message = _("Success: The work shift was successfully modified.")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            is_ajax = self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            if is_ajax:
                return JsonResponse({
                    'success': True,
                })
            else:
                return response

        except Exception as e:
            # logging.error("Error: " + str(e))
            # print("\n-> Error al guardar reforma...")
            return JsonResponse({
                'status': HTTPStatus.INTERNAL_SERVER_ERROR.value,
                # 'message': _(str(err))
                'message': str(e),
            }, status=500)


def work_shift_delete(request, pk):
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            work_shift = WorkShift.objects.get(pk=pk)

            try:
                work_shift.delete()

                messages.add_message(request, messages.INFO,
                                     _('Record deleted successfully.'))

                return JsonResponse({
                    'success': True,
                })

            except RestrictedError as err:
                response = JsonResponse({'status': 'false',
                                         'message': str(err)
                                         }, status=500)
                return response


'''
def emotion_analysis(request):
    context = {
        
    }
    return render(request, 'employee/emotion_analysis/index.html', context)
'''


class VideoListView(ListView):
    """Devuelve lista de videos recolectados."""

    template_name = 'employee/video/video_list.html'

    def get_queryset(self):
        video_list = EmotionAnalysis.objects.all()
        return video_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segment"] = 'emotion-video'
        return context


'''
class VideoNew(SuccessMessageMixin, MixinFormInvalid, CreateView):
    model = EmotionAnalysis
    template_name = "employee/video/video_form.html"
    context_object_name = "obj"
    form_class = EmotionAnalysisForm
    success_url = reverse_lazy("employee:video_list")
    success_message = _("Success: The new video was created successfully.")
'''


'''
class VideoNew(SuccessMessageMixin, MixinFormInvalid, CreateView):
    model = EmotionAnalysis
    template_name = "employee/video/video_form.html"
    context_object_name = "obj"
    form_class = EmotionAnalysisForm
    success_url = reverse_lazy("employee:video_list")
    success_message = _("Success: The new video was created successfully.")

    def form_valid(self, form):
        response = super().form_valid(form)

        # Ruta completa del archivo de video subido
        video_path = os.path.join(settings.MEDIA_ROOT, self.object.video_file.name)

        try:
            # Procesar el video con el algoritmo DeepFace
            # Aquí podrías extraer frames del video y analizarlos.
            # Ejemplo de cómo podrías analizar un frame del video:
            # frame = extraer_frame(video_path)
            # result = DeepFace.analyze(frame, actions=['emotion'])

            # Aquí se debe agregar el código para extraer frames y procesarlos con DeepFace
            # Por ejemplo, podrías iterar sobre los frames y obtener el análisis de emociones.

            result_summary, analysis_time, dominant_emotion, \
                frame_count, duration = analyze_emotions(video_path)

            # Guardar los resultados en el campo 'emotions_detected'
            # 'result_summary' tiene que ser un JSON válido
            self.object.emotions_detected = result_summary  
            self.object.save()

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e),
            }, status=500)

        is_ajax = self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            data = {
                'success': True,
            }
            return JsonResponse(data)
        else:
            return response
'''


class VideoNew(SuccessMessageMixin, MixinFormInvalid, CreateView):
    model = EmotionAnalysis
    template_name = "employee/video/video_form.html"
    context_object_name = "obj"
    form_class = EmotionAnalysisForm
    success_url = reverse_lazy("employee:video_list")
    success_message = _("Success: The new video was created successfully.")

    def form_valid(self, form):
        response = super().form_valid(form)
        pk = form.instance.pk

        # Añadir el mensaje de exito
        messages.add_message(self.request, messages.INFO, 
                             _("Successfully submitted data"))

        # Verificar si es una solicitud AJAX
        is_ajax = self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            data = {
                'success': True,
                'message': _("Successfully submitted data"),
                'pk': pk,
            }
            return JsonResponse(data)
        else:
            return response


'''
def analyze_video(request, pk):
    """Analiza el video subido."""
    print("\n=> Parámetro recibido de frontend: ", pk)

    video_obj = EmotionAnalysis.objects.get(pk=pk)
    video_path = os.path.join(settings.MEDIA_ROOT, video_obj.video_file.name)
    print("Video Path: ", video_path)

    return JsonResponse({
        'success': True,
        'message': _("Video successfully analyzed."),
    })
'''


def analyze_video(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        video_id = data["video_id"]

        task = analyze_video_task.apply_async(
            args=[video_id])
        return JsonResponse({"task_id": task.id}, status=202)

'''
def analyze_video_task_status(request, task_id):
    task = AsyncResult(task_id)
    if task.state == 'FAILURE':
        response_data = {
            'state': task.state,
            'result': str(task.result),  # Convertir el error a string para evitar problemas de serialización
        }
    elif task.state == 'PROGRESS':
        response_data = {
            'state': task.state,
            'result': task.info  # `task.info` debe contener el progreso
        }
    else:
        response_data = {
            'state': task.state,
            'result': task.result,
        }
    return JsonResponse(response_data)
'''


def analyze_video_task_status(request, task_id):
    task = AsyncResult(task_id)
    
    if task.state == 'FAILURE':
        error_message = str(task.result) if task.result else 'Unknown error'
        response_data = {
            'state': task.state,
            'result': {
                'error': error_message
            }
        }
    
    elif task.state == 'PROGRESS':
        progress_info = task.info if task.info else {'percent': 0}
        response_data = {
            'state': task.state,
            'result': progress_info
        }
    
    else:
        response_data = {
            'state': task.state,
            'result': task.result
        }
    
    return JsonResponse(response_data, safe=False)


def analyze_emotions(video_path):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    aggregated_emotions = defaultdict(float)
    frame_count = 0
    valid_frame_count = 0
    dominant_frame = None
    dominant_emotion = None

    start_time = time.time()  # Tiempo de inicio

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % 30 == 0:  # Procesar cada 30 cuadros (aproximadamente 1 segundo a 30 fps)
            try:
                result = DeepFace.analyze(frame, actions=['emotion'])
                if isinstance(result, list):
                    for face in result:
                        if 'emotion' in face:
                            for emotion, score in face['emotion'].items():
                                aggregated_emotions[emotion] += score
                            valid_frame_count += 1
                            # Verificar si este frame tiene la emoción dominante
                            current_dominant_emotion = max(face['emotion'], key=face['emotion'].get)
                            if dominant_emotion is None or face['emotion'][current_dominant_emotion] > face['emotion'][dominant_emotion]:
                                dominant_emotion = current_dominant_emotion
                                dominant_frame = frame
                else:
                    aggregated_emotions['error'] = 'Unexpected result structure'
            except Exception as e:
                aggregated_emotions['error'] = str(e)
        frame_count += 1

    end_time = time.time()  # Tiempo de fin
    duration = end_time - start_time  # Duración en segundos

    cap.release()

    # Calcular el promedio de las emociones
    if valid_frame_count > 0:
        for emotion in aggregated_emotions:
            aggregated_emotions[emotion] /= valid_frame_count
        dominant_emotion = max(aggregated_emotions, key=aggregated_emotions.get)
    else:
        aggregated_emotions = {'error': 'No valid frames processed'}
        dominant_emotion = 'unknown'

    analysis_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    result_summary = {
        'emotions': aggregated_emotions,
        'dominant_emotion': dominant_emotion
    }

    return result_summary, analysis_time, dominant_emotion, frame_count, duration


class VideoEdit(SuccessMessageMixin, MixinFormInvalid, UpdateView):
    model = EmotionAnalysis
    template_name = "employee/video/video_form.html"
    context_object_name = "obj"
    form_class = EmotionAnalysisForm
    success_url = reverse_lazy("employee:video_list")
    success_message = _("Success: The video was successfully modified.")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            is_ajax = self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            if is_ajax:
                return JsonResponse({
                    'success': True,
                })
            else:
                return response

        except Exception as e:
            # logging.error("Error: " + str(e))
            # print("\n-> Error al guardar reforma...")
            return JsonResponse({
                'status': HTTPStatus.INTERNAL_SERVER_ERROR.value,
                # 'message': _(str(err))
                'message': str(e),
            }, status=500)


def video_delete(request, pk):
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            video = EmotionAnalysis.objects.get(pk=pk)

            try:
                video.delete()

                messages.add_message(request, messages.INFO,
                                     _('Record deleted successfully.'))

                return JsonResponse({
                    'success': True,
                })

            except RestrictedError as err:
                response = JsonResponse({'status': 'false',
                                         'message': str(err)
                                         }, status=500)
                return response


'''
def analytics(request):
    context = {
        'segment': 'analytics'
    }
    return render(request, 'employee/analytics/index.html', context)
'''


class AnalyticsListView(ListView):
    # model = EmotionAnalysis
    template_name = 'employee/analytics/analytics_list.html'

    def get_queryset(self):
        query = self.request.GET.get("q", '')
        queryset = EmotionAnalysis.objects.all()
        if query:
            queryset = queryset.filter(profile=query)

        return queryset
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segment"] = 'analytics'
        return context


def analytics(request):
    '''object_list = EmotionAnalysis.objects.all()
    area_emotions = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))
    work_shift_emotions = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))
    hourly_emotions = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    employee_hourly_emotions = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))

    for obj in object_list:
        area = str(obj.profile.worker_area)
        work_shift = str(obj.profile.work_shift)
        recorded_at = obj.recorded_at
        employee = str(obj.profile.user.username)
        date = recorded_at.strftime('%Y-%m-%d')
        hour = recorded_at.strftime('%H:00')
        dominant_emotion = obj.emotions_detected['dominant_emotion']

        # Asegurarse de que area_emotions[area][date][hour] sea un diccionario
        if hour not in area_emotions[area][date]:
            area_emotions[area][date][hour] = defaultdict(int)
        area_emotions[area][date][hour][dominant_emotion] += 1

        if hour not in work_shift_emotions[work_shift][date]:
            work_shift_emotions[work_shift][date][hour] = defaultdict(int)
        work_shift_emotions[work_shift][date][hour][dominant_emotion] += 1

        if hour not in hourly_emotions[date]:
            hourly_emotions[date][hour] = defaultdict(int)
        hourly_emotions[date][hour][dominant_emotion] += 1

        if hour not in employee_hourly_emotions[employee][date]:
            employee_hourly_emotions[employee][date][hour] = defaultdict(int)
        employee_hourly_emotions[employee][date][hour][dominant_emotion] += 1

    area_emotions = {area: {date: {hour: dict(emotions) for hour, emotions in hours.items()} for date, hours in dates.items()} for area, dates in area_emotions.items()}
    work_shift_emotions = {shift: {date: {hour: dict(emotions) for hour, emotions in hours.items()} for date, hours in dates.items()} for shift, dates in work_shift_emotions.items()}
    hourly_emotions = {date: {hour: dict(emotions) for hour, emotions in hours.items()} for date, hours in hourly_emotions.items()}
    employee_hourly_emotions = {employee: {date: {hour: dict(emotions) for hour, emotions in hours.items()} for date, hours in dates.items()} for employee, dates in employee_hourly_emotions.items()}'''

    # day = timezone.now()
    # formatedDay = day.strftime("%Y-%m-%d")

    current_date = datetime.now().date()
    # Obtener la fecha y hora actual
    now = datetime.now()
    
    # Ajustar la hora a las 00:00
    start_of_day = datetime(now.year, now.month, now.day)

    worker_area_list = WorkerArea.objects.all().values('id', 'name').order_by('name')
    work_shift_list = WorkShift.objects.all().values('id', 'name').order_by('name')

    print()
    print("=> area")
    print(work_shift_list)
    print()

    context = {
        'segment': 'analytics',
        #'area_emotions': area_emotions,
        #'work_shift_emotions': work_shift_emotions,
        #'hourly_emotions': hourly_emotions,
        #'employee_hourly_emotions': employee_hourly_emotions
        'worker_area_list': worker_area_list,
        'work_shift_list': work_shift_list,
        'current_date': current_date.strftime('%Y-%m-%d'),
        'start_date_time': start_of_day.strftime("%Y-%m-%d %H:%M"),
        'end_date_time': datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    return render(request, 'employee/analytics/analytics_list.html', context)


def get_worker_area_emotions(request):
    """Devuelve lista de emociones por area de trabajo."""
    data = json.loads(request.body)
    worker_area = data["worker_area"]
    start_date = data["start_date"]
    end_date = data["end_date"]

    """print("\n-> Parametros recibidos")
    print("worker_area = %s" % worker_area)  # 2
    print("start_date = %s" % start_date)  # 2024-09-06
    print("end_date = %s" % end_date)  # 2024-09-06
    print("\n")"""

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        if worker_area == '0':  # todas las áreas de trabajo
            print("\n=> Filtro todas las áreas")
            object_list = EmotionAnalysis.objects.filter(
                recorded_at__range=(start_date, end_date)
            ).order_by('profile__worker_area__name', 'recorded_at')
        else:
            print(f"\n=>Filtro áreas {worker_area}")
            object_list = EmotionAnalysis.objects.filter(
                profile__worker_area_id=worker_area,
                recorded_at__range=(start_date, end_date)
            ).order_by('recorded_at')

        area_emotions = defaultdict(lambda: defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))))

        for obj in object_list:
            area = str(obj.profile.worker_area)
            # recorded_at = obj.recorded_at
            recorded_at = localtime(obj.recorded_at)  # Convertir a hora local
            date = recorded_at.strftime('%Y-%m-%d')
            hour = recorded_at.strftime('%H:00')
            dominant_emotion = obj.emotions_detected['dominant_emotion']

            # Asegurarse de que area_emotions[area][date][hour] sea un diccionario
            if hour not in area_emotions[area][date]:
                area_emotions[area][date][hour] = defaultdict(int)
            area_emotions[area][date][hour][dominant_emotion] += 1

        area_emotions = {
            area: {
                date: {
                    hour: dict(emotions) for hour, emotions in hours.items()
                } for date, hours in dates.items()
            } for area, dates in area_emotions.items()
        }
        return JsonResponse({
                            'success': True,
                            'area_emotions': area_emotions})
    else:
        return JsonResponse({
            'status': _("Failure"),
            'message': _("Incorrect request"),
        }, status=500)


'''
# funciona prefecto, no coincide con hora de base de datos
def get_worker_area_chart_data(request):
    data = json.loads(request.body)
    worker_area_id = data["worker_area"]
    start_date = data["start_date"]
    end_date = data["end_date"]

    # date_obj = datetime.strptime(date, '%Y-%m-%d')
    object_list = EmotionAnalysis.objects.filter(
        recorded_at__date__range=(start_date, end_date))

    # Si se ha proporcionado un área específica, filtrar por ella
    if worker_area_id and worker_area_id != '0':
        object_list = object_list.filter(profile__worker_area__id=worker_area_id)

    # Inicializar las estructuras de datos
    area_hourly_emotions = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    all_areas = set()
    all_emotions = set()

    if object_list.exists():
        # Obtener las emociones detectadas y las áreas de trabajo
        all_emotions = object_list.first().emotions_detected.get('emotions', {}).keys()
        all_areas = {obj.profile.worker_area.name for obj in object_list if obj.profile.worker_area}

    # Inicializar los datos para todas las combinaciones de áreas y horas
    for area in all_areas:
        for hour in range(24):
            hour_label = f'{str(hour).zfill(2)}:00'
            for emotion in all_emotions:
                area_hourly_emotions[area][hour_label][emotion] = 0

    # Procesar los datos de los objetos obtenidos
    for obj in object_list:
        if obj.profile.worker_area:
            area = obj.profile.worker_area.name
            recorded_at = obj.recorded_at
            hour = recorded_at.strftime('%H:00')
            dominant_emotion = obj.emotions_detected['dominant_emotion']

            # Actualizar los datos por área y hora
            area_hourly_emotions[area][hour][dominant_emotion] += 1

    # Crear etiquetas combinadas de área y hora
    labels_with_data = []
    for area in sorted(all_areas):
        for hour in range(24):
            hour_label = f'{str(hour).zfill(2)}:00'
            # Si hay datos en esa área y hora
            if any(area_hourly_emotions[area][hour_label][emotion] > 0 for emotion in all_emotions):
                labels_with_data.append(f'{area} - {hour_label}')

    # Crear datasets para el gráfico por áreas (con emociones)
    area_datasets = []
    colors = [
        'rgba(75, 192, 192, 0.75)',  # #4bc0c0
        'rgba(0, 123, 255, 0.75)',   # #007bff
        'rgba(255, 131, 0, 0.75)',   # #FF8300
        'rgba(255, 87, 51, 0.75)',   # #FF5733
        'rgba(199, 0, 57, 0.75)',    # #C70039
        'rgba(144, 12, 63, 0.75)',   # #900C3F
        'rgba(88, 24, 69, 0.75)'     # #581845
    ]

    # Crear un dataset para cada emoción
    for i, emotion in enumerate(all_emotions):
        emotion_data = []
        for area in sorted(all_areas):
            for hour in range(24):
                hour_label = f'{str(hour).zfill(2)}:00'
                if f'{area} - {hour_label}' in labels_with_data:
                    emotion_data.append(area_hourly_emotions[area][hour_label][emotion])

        area_datasets.append({
            'label': _(emotion),
            'data': emotion_data,
            'fill': 'false',
            'borderColor': colors[i % len(colors)].replace('0.75', '1'),
            'backgroundColor': colors[i % len(colors)],
            'borderWidth': 1,
        })

    # Empaquetar los datos para el gráfico por áreas
    data = {
        'labels': labels_with_data,  # Etiquetas con área y hora
        'datasets': area_datasets    # Datos de emociones por área y hora
    }

    return JsonResponse(data)
'''


def get_worker_area_chart_data(request):
    data = json.loads(request.body)
    worker_area_id = data["worker_area"]
    start_date = data["start_date"]
    end_date = data["end_date"]

    object_list = EmotionAnalysis.objects.filter(
        recorded_at__date__range=(start_date, end_date)
    )

    # Si se ha proporcionado un área específica, filtrar por ella
    if worker_area_id and worker_area_id != '0':
        object_list = object_list.filter(profile__worker_area__id=worker_area_id)

    # Inicializar las estructuras de datos
    area_hourly_emotions = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    all_areas = set()
    all_emotions = set()

    if object_list.exists():
        # Obtener las emociones detectadas y las áreas de trabajo
        all_emotions = object_list.first().emotions_detected.get('emotions', {}).keys()
        all_areas = {obj.profile.worker_area.name for obj in object_list if obj.profile.worker_area}

    # Inicializar los datos para todas las combinaciones de áreas y horas
    for area in all_areas:
        for hour in range(24):
            hour_label = f'{str(hour).zfill(2)}:00-{str(hour).zfill(2)}:59'  # Formato [HH:00-HH:59]
            for emotion in all_emotions:
                area_hourly_emotions[area][hour_label][emotion] = 0

    # Procesar los datos de los objetos obtenidos
    for obj in object_list:
        if obj.profile.worker_area:
            area = obj.profile.worker_area.name
            recorded_at = localtime(obj.recorded_at)  # Convertir a hora local
            hour = recorded_at.strftime('%H:00-%H:59')  # Ajustar el formato [HH:00-HH:59]
            dominant_emotion = obj.emotions_detected['dominant_emotion']

            # Actualizar los datos por área y hora
            area_hourly_emotions[area][hour][dominant_emotion] += 1

    # Crear etiquetas combinadas de área y hora con el nuevo formato
    labels_with_data = []
    for area in sorted(all_areas):
        for hour in range(24):
            hour_label = f'{str(hour).zfill(2)}:00-{str(hour).zfill(2)}:59'
            # Si hay datos en esa área y hora
            if any(area_hourly_emotions[area][hour_label][emotion] > 0 for emotion in all_emotions):
                labels_with_data.append(f'{area} - [{hour_label}]')  # Agregar corchetes [HH:00-HH:59]

    # Crear datasets para el gráfico por áreas (con emociones)
    area_datasets = []
    colors = [
        'rgba(75, 192, 192, 0.75)',  # #4bc0c0
        'rgba(0, 123, 255, 0.75)',   # #007bff
        'rgba(255, 131, 0, 0.75)',   # #FF8300
        'rgba(255, 87, 51, 0.75)',   # #FF5733
        'rgba(199, 0, 57, 0.75)',    # #C70039
        'rgba(144, 12, 63, 0.75)',   # #900C3F
        'rgba(88, 24, 69, 0.75)'     # #581845
    ]

    # Crear un dataset para cada emoción
    for i, emotion in enumerate(all_emotions):
        emotion_data = []
        for area in sorted(all_areas):
            for hour in range(24):
                hour_label = f'{str(hour).zfill(2)}:00-{str(hour).zfill(2)}:59'  # Usar el formato [HH:00-HH:59]
                if f'{area} - [{hour_label}]' in labels_with_data:
                    emotion_data.append(area_hourly_emotions[area][hour_label][emotion])

        area_datasets.append({
            'label': _(emotion),
            'data': emotion_data,
            'fill': 'false',
            'borderColor': colors[i % len(colors)].replace('0.75', '1'),
            'backgroundColor': colors[i % len(colors)],
            'borderWidth': 1,
        })

    # Empaquetar los datos para el gráfico por áreas
    data = {
        'labels': labels_with_data,  # Etiquetas con área y hora [HH:00-HH:59]
        'datasets': area_datasets    # Datos de emociones por área y hora
    }

    return JsonResponse(data)


def get_work_shift_emotions(request):
    """Devuelve lista de emociones por turno de trabajo."""
    data = json.loads(request.body)
    work_shift = data["work_shift"]
    start_date = data["start_date"]
    end_date = data["end_date"]

    """print("\n-> Parametros recibidos")
    print("work_shift = %s" % work_shift)  # 2
    print("start_date = %s" % start_date)  # 2024-09-06
    print("end_date = %s" % end_date)  # 2024-09-06
    print("\n")"""

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        if work_shift == '0':  # todas las áreas de trabajo
            print("\n=> Filtro todos los turnos")
            object_list = EmotionAnalysis.objects.filter(
                recorded_at__range=(start_date, end_date)
            ).order_by('profile__work_shift__name', 'recorded_at')
        else:
            print(f"\n=>Filtro turno {work_shift}")
            object_list = EmotionAnalysis.objects.filter(
                profile__work_shift_id=work_shift,
                recorded_at__range=(start_date, end_date)
            ).order_by('recorded_at')

        work_shift_emotions = defaultdict(lambda: defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))))

        for obj in object_list:
            work_shift = str(obj.profile.work_shift)
            # recorded_at = obj.recorded_at
            recorded_at = localtime(obj.recorded_at)  # Convertir a hora local
            date = recorded_at.strftime('%Y-%m-%d')
            hour = recorded_at.strftime('%H:00')
            dominant_emotion = obj.emotions_detected['dominant_emotion']

            # Asegurarse de que work_shift_emotions[work_shift][date][hour] sea un diccionario
            if hour not in work_shift_emotions[work_shift][date]:
                work_shift_emotions[work_shift][date][hour] = defaultdict(int)
            work_shift_emotions[work_shift][date][hour][dominant_emotion] += 1

        work_shift_emotions = {
            shift: {
                date: {
                    hour: dict(emotions) for hour, emotions in hours.items()
                } for date, hours in dates.items()
            } for shift, dates in work_shift_emotions.items()
        }

        return JsonResponse({
                            'success': True,
                            'work_shift_emotions': work_shift_emotions})
    else:
        return JsonResponse({
            'status': _("Failure"),
            'message': _("Incorrect request"),
        }, status=500)


'''
def get_work_shift_chart_data(request):
    data = json.loads(request.body)
    work_shift_id = data["work_shift"]
    start_date = data["start_date"]
    end_date = data["end_date"]

    # Obtener los registros de emociones dentro del rango de fechas
    object_list = EmotionAnalysis.objects.filter(
        recorded_at__date__range=(start_date, end_date))

    # Si se ha proporcionado un turno de trabajo específico, filtrar por él
    if work_shift_id and work_shift_id != '0':
        try:
            work_shift = WorkShift.objects.get(id=work_shift_id)
            print(f"Work Shift ID: {work_shift_id}, Start: {work_shift.start_time}, End: {work_shift.end_time}")
        except WorkShift.DoesNotExist:
            return JsonResponse({'error': 'Turno de trabajo no válido.'}, status=400)

        shift_start = work_shift.start_time
        shift_end = work_shift.end_time

        # Verificar si el turno cruza la medianoche o no
        if shift_start > shift_end:
            print(f"Turno cruza la medianoche: {work_shift.name}")
            object_list = object_list.filter(
                Q(recorded_at__time__gte=shift_start) |
                Q(recorded_at__time__lt=shift_end),
                profile__work_shift=work_shift
            )
        else:
            print(f"Turno no cruza la medianoche: {work_shift.name}")
            object_list = object_list.filter(
                recorded_at__time__range=(shift_start, shift_end),
                profile__work_shift=work_shift
            )

        # Verificar cuántos registros se obtienen después de aplicar el filtro
        print(f"Registros después de aplicar el filtro para el turno {work_shift.name}: {object_list.count()}")

    # Si no se especifica un turno o se seleccionan todos los turnos (work_shift_id = 0)
    print(f"Total de registros obtenidos: {object_list.count()}")

    # Inicializar las estructuras de datos
    work_shift_hourly_emotions = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    all_work_shifts = set()
    all_emotions = set()

    if object_list.exists():
        # Obtener las emociones detectadas y los turnos de trabajo
        all_emotions = object_list.first().emotions_detected.get('emotions', {}).keys()
        all_work_shifts = {obj.profile.work_shift.name for obj in object_list if obj.profile.work_shift}

    # Inicializar los datos para todas las combinaciones de turnos y horas
    for shift in all_work_shifts:
        for hour in range(24):
            hour_label = f'{str(hour).zfill(2)}:00'
            for emotion in all_emotions:
                work_shift_hourly_emotions[shift][hour_label][emotion] = 0

    # Procesar los datos de los objetos obtenidos
    for obj in object_list:
        if obj.profile.work_shift:
            shift = obj.profile.work_shift.name
            recorded_at = obj.recorded_at
            hour = recorded_at.strftime('%H:00')
            dominant_emotion = obj.emotions_detected['dominant_emotion']

            # Actualizar los datos por turno y hora
            work_shift_hourly_emotions[shift][hour][dominant_emotion] += 1

    # Crear etiquetas combinadas de turno y hora
    labels_with_data = []
    for shift in sorted(all_work_shifts):
        for hour in range(24):
            hour_label = f'{str(hour).zfill(2)}:00'
            # Si hay datos en ese turno y hora
            if any(work_shift_hourly_emotions[shift][hour_label][emotion] > 0 for emotion in all_emotions):
                labels_with_data.append(f'{shift} - {hour_label}')

    # Crear datasets para el gráfico por turnos (con emociones)
    work_shift_datasets = []
    colors = [
        'rgba(75, 192, 192, 0.75)',  # #4bc0c0
        'rgba(0, 123, 255, 0.75)',   # #007bff
        'rgba(255, 131, 0, 0.75)',   # #FF8300
        'rgba(255, 87, 51, 0.75)',   # #FF5733
        'rgba(199, 0, 57, 0.75)',    # #C70039
        'rgba(144, 12, 63, 0.75)',   # #900C3F
        'rgba(88, 24, 69, 0.75)'     # #581845
    ]

    # Crear un dataset para cada emoción
    for i, emotion in enumerate(all_emotions):
        emotion_data = []
        for shift in sorted(all_work_shifts):
            for hour in range(24):
                hour_label = f'{str(hour).zfill(2)}:00'
                if f'{shift} - {hour_label}' in labels_with_data:
                    emotion_data.append(work_shift_hourly_emotions[shift][hour_label][emotion])

        work_shift_datasets.append({
            'label': emotion,
            'data': emotion_data,
            'fill': 'false',
            'borderColor': colors[i % len(colors)].replace('0.75', '1'),
            'backgroundColor': colors[i % len(colors)],
            'borderWidth': 1,
        })

    # Empaquetar los datos para el gráfico por turnos
    data = {
        'labels': labels_with_data,  # Etiquetas con turno y hora
        'datasets': work_shift_datasets  # Datos de emociones por turno y hora
    }

    return JsonResponse(data)
'''


# función perfecta coincide con las horas de la base de datos
def get_work_shift_chart_data(request):
    data = json.loads(request.body)
    work_shift_id = data["work_shift"]
    start_date = data["start_date"]
    end_date = data["end_date"]

    # Obtener los registros de emociones dentro del rango de fechas
    object_list = EmotionAnalysis.objects.filter(
        recorded_at__date__range=(start_date, end_date))

    # Si se ha proporcionado un turno de trabajo específico, filtrar por él
    if work_shift_id and work_shift_id != '0':
        try:
            work_shift = WorkShift.objects.get(id=work_shift_id)
            shift_start = work_shift.start_time
            shift_end = work_shift.end_time
        except WorkShift.DoesNotExist:
            return JsonResponse({'error': 'Turno de trabajo no válido.'}, status=400)

        # Verificar si el turno cruza la medianoche o no
        if shift_start > shift_end:
            object_list = object_list.filter(
                Q(recorded_at__time__gte=shift_start) |
                Q(recorded_at__time__lt=shift_end),
                profile__work_shift=work_shift
            )
        else:
            object_list = object_list.filter(
                recorded_at__time__range=(shift_start, shift_end),
                profile__work_shift=work_shift
            )

    # Inicializar las estructuras de datos
    work_shift_hourly_emotions = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    all_work_shifts = set()
    all_emotions = set()

    if object_list.exists():
        all_emotions = object_list.first().emotions_detected.get('emotions', {}).keys()
        all_work_shifts = {obj.profile.work_shift.name for obj in object_list if obj.profile.work_shift}

    # Ajustar horas y agruparlas por rangos de 1 hora
    for obj in object_list:
        if obj.profile.work_shift:
            shift = obj.profile.work_shift.name

            # Convertir a la hora local si es necesario
            recorded_at = localtime(obj.recorded_at)

            # Agrupar por la hora completa (ej. 08:00-08:59)
            hour = f"{recorded_at.hour:02}:00"

            dominant_emotion = obj.emotions_detected['dominant_emotion']

            # Actualizar los datos por turno y hora
            work_shift_hourly_emotions[shift][hour][dominant_emotion] += 1

    # Crear etiquetas combinadas de turno y hora
    labels_with_data = []
    for shift in sorted(all_work_shifts):
        for hour in range(24):
            # hour_label = f'{str(hour).zfill(2)}:00'
            # if any(work_shift_hourly_emotions[shift][hour_label][emotion] > 0 for emotion in all_emotions):
            #    labels_with_data.append(f'{shift} - {hour_label}')

            # HORAS CON INTERVALO COMPLETO
            hour_label = f'{str(hour).zfill(2)}:00-{str(hour).zfill(2)}:59'  # Modificamos para mostrar el rango de horas
            # Si hay datos en ese turno y hora
            if any(work_shift_hourly_emotions[shift][f'{str(hour).zfill(2)}:00'][emotion] > 0 for emotion in all_emotions):
                labels_with_data.append(f'{shift} - [{hour_label}]')  # Añadimos los corchetes para el formato [HH:00-HH:59]

    # Crear datasets para el gráfico por turnos (con emociones)
    work_shift_datasets = []
    colors = [
        'rgba(75, 192, 192, 0.75)',  # #4bc0c0
        'rgba(0, 123, 255, 0.75)',   # #007bff
        'rgba(255, 131, 0, 0.75)',   # #FF8300
        'rgba(255, 87, 51, 0.75)',   # #FF5733
        'rgba(199, 0, 57, 0.75)',    # #C70039
        'rgba(144, 12, 63, 0.75)',   # #900C3F
        'rgba(88, 24, 69, 0.75)'     # #581845
    ]

    for i, emotion in enumerate(all_emotions):
        emotion_data = []
        for shift in sorted(all_work_shifts):
            for hour in range(24):
                hour_label = f'{str(hour).zfill(2)}:00'
                # if f'{shift} - {hour_label}' in labels_with_data:
                #    emotion_data.append(work_shift_hourly_emotions[shift][hour_label][emotion])
                
                # Generar el rango horario [HH:00-HH:59]
                hour_label = f'{str(hour).zfill(2)}:00-{str(hour).zfill(2)}:59'
                # Verificar si la etiqueta con formato [shift - [HH:00-HH:59]] existe en labels_with_data
                if f'{shift} - [{hour_label}]' in labels_with_data:
                    emotion_data.append(work_shift_hourly_emotions[shift][f'{str(hour).zfill(2)}:00'][emotion])

        work_shift_datasets.append({
            'label': emotion,
            'data': emotion_data,
            'fill': 'false',
            'borderColor': colors[i % len(colors)].replace('0.75', '1'),
            'backgroundColor': colors[i % len(colors)],
            'borderWidth': 1,
        })

    # Empaquetar los datos para el gráfico por turnos
    data = {
        'labels': labels_with_data,  # Etiquetas con turno y hora
        'datasets': work_shift_datasets  # Datos de emociones por turno y hora
    }

    return JsonResponse(data)


def get_hour_chart_data(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        start_date_time = data.get('start_date_time')
        end_date_time = data.get('end_date_time')

        # Obtener los datos filtrados por el rango de fecha y hora
        object_list = EmotionAnalysis.objects.filter(
            recorded_at__range=(start_date_time, end_date_time)
        )

        # Inicializar las estructuras de datos
        hourly_emotions_by_date = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        all_emotions = set()

        if object_list.exists():
            all_emotions = object_list.first().emotions_detected.get('emotions', {}).keys()

        # Procesar los datos de los objetos obtenidos
        for obj in object_list:
            recorded_at = localtime(obj.recorded_at)  # Convertir a hora local
            date_label = recorded_at.strftime('%Y-%m-%d')
            hour_label = recorded_at.strftime('%H:00-%H:59')
            dominant_emotion = obj.emotions_detected['dominant_emotion']

            # Actualizar los datos por fecha y hora
            hourly_emotions_by_date[date_label][hour_label][dominant_emotion] += 1

        # Crear etiquetas combinadas de fecha y hora
        labels_with_data = []
        for date in sorted(hourly_emotions_by_date.keys()):
            for hour in sorted(hourly_emotions_by_date[date].keys()):
                labels_with_data.append(f'{date} - [{hour}]')

        # Crear datasets para el gráfico por emociones
        datasets = []
        colors = [
            'rgba(75, 192, 192, 0.75)',  # #4bc0c0
            'rgba(0, 123, 255, 0.75)',   # #007bff
            'rgba(255, 131, 0, 0.75)',   # #FF8300
            'rgba(255, 87, 51, 0.75)',   # #FF5733
            'rgba(199, 0, 57, 0.75)',    # #C70039
            'rgba(144, 12, 63, 0.75)',   # #900C3F
            'rgba(88, 24, 69, 0.75)'     # #581845
        ]

        for i, emotion in enumerate(all_emotions):
            emotion_data = []
            for date in sorted(hourly_emotions_by_date.keys()):
                for hour in sorted(hourly_emotions_by_date[date].keys()):
                    emotion_data.append(hourly_emotions_by_date[date][hour].get(emotion, 0))

            datasets.append({
                'label': emotion,
                'data': emotion_data,
                'fill': 'false',
                'borderColor': colors[i % len(colors)].replace('0.75', '1'),
                'backgroundColor': colors[i % len(colors)],
                'borderWidth': 1,
            })

        # Empaquetar los datos para el gráfico
        data = {
            'labels': labels_with_data,  # Etiquetas con fecha y hora
            'datasets': datasets         # Datos de emociones por fecha y hora
        }

        return JsonResponse(data)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)


def get_employee_chart_data(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data["employee"]
        start_date = data["start_date"]
        end_date = data["end_date"]

        # Filtrar los datos por perfil del empleado (que está relacionado con el modelo User)
        object_list = EmotionAnalysis.objects.filter(
            profile__user_id=user_id,  # Filtrar por la lista de empleados a través del perfil
            recorded_at__range=(start_date, end_date)  # Filtrar por rango de fecha y hora
        )

        # Inicializar las estructuras de datos
        hourly_emotions_by_date = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        all_emotions = set()

        if object_list.exists():
            all_emotions = object_list.first().emotions_detected.get('emotions', {}).keys()

        # Procesar los datos de los objetos obtenidos
        for obj in object_list:
            recorded_at = localtime(obj.recorded_at)  # Convertir a hora local
            date_label = recorded_at.strftime('%Y-%m-%d')
            hour_label = recorded_at.strftime('%H:00-%H:59')
            dominant_emotion = obj.emotions_detected['dominant_emotion']

            # Actualizar los datos por fecha y hora
            hourly_emotions_by_date[date_label][hour_label][dominant_emotion] += 1

        # Crear etiquetas combinadas de fecha y hora
        labels_with_data = []
        for date in sorted(hourly_emotions_by_date.keys()):
            for hour in sorted(hourly_emotions_by_date[date].keys()):
                labels_with_data.append(f'{date} - {hour}')

        # Crear datasets para el gráfico por emociones
        datasets = []
        colors = [
            'rgba(75, 192, 192, 0.75)',  # #4bc0c0
            'rgba(0, 123, 255, 0.75)',   # #007bff
            'rgba(255, 131, 0, 0.75)',   # #FF8300
            'rgba(255, 87, 51, 0.75)',   # #FF5733
            'rgba(199, 0, 57, 0.75)',    # #C70039
            'rgba(144, 12, 63, 0.75)',   # #900C3F
            'rgba(88, 24, 69, 0.75)'     # #581845
        ]

        for i, emotion in enumerate(all_emotions):
            emotion_data = []
            for date in sorted(hourly_emotions_by_date.keys()):
                for hour in sorted(hourly_emotions_by_date[date].keys()):
                    emotion_data.append(hourly_emotions_by_date[date][hour].get(emotion, 0))

            datasets.append({
                'label': emotion,
                'data': emotion_data,
                'fill': 'false',
                'borderColor': colors[i % len(colors)].replace('0.75', '1'),
                'backgroundColor': colors[i % len(colors)],
                'borderWidth': 1,
            })

        # Empaquetar los datos para el gráfico
        data = {
            'labels': labels_with_data,  # Etiquetas con fecha y hora
            'datasets': datasets         # Datos de emociones por fecha y hora
        }

        return JsonResponse(data)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)


def get_hourly_emotions(request):
    """Devuelve lista de emociones por horas trabajo."""
    data = json.loads(request.body)
    start_date_time = data["start_date_time"]
    end_date_time = data["end_date_time"]

    print("\n-> Parametros recibidos")
    print("start_date = %s" % start_date_time)  # 2024-09-06T19:41
    print("end_date = %s" % end_date_time)  # 2024-09-06T19:41
    print("\n")

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        # Convertir las cadenas de fecha y hora a objetos datetime
        start_datetime = datetime.strptime(start_date_time, '%Y-%m-%dT%H:%M')
        end_datetime = datetime.strptime(end_date_time, '%Y-%m-%dT%H:%M')

        object_list = EmotionAnalysis.objects.filter(
            recorded_at__range=(start_datetime, end_datetime)
        ).order_by('recorded_at')

        hourly_emotions = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

        for obj in object_list:
            # recorded_at = obj.recorded_at
            recorded_at = localtime(obj.recorded_at)  # Convertir a hora local
            date = recorded_at.strftime('%Y-%m-%d')
            hour = recorded_at.strftime('%H:00')
            dominant_emotion = obj.emotions_detected['dominant_emotion']

            # Asegurarse de que hourly_emotions[date][hour] sea un diccionario
            if hour not in hourly_emotions[date]:
                hourly_emotions[date][hour] = defaultdict(int)
            hourly_emotions[date][hour][dominant_emotion] += 1

        hourly_emotions = {
            date: {
                hour: dict(emotions) for hour, emotions in hours.items()
            } for date, hours in hourly_emotions.items()
        }

        return JsonResponse({
                            'success': True,
                            'hourly_emotions': hourly_emotions})
    else:
        return JsonResponse({
            'status': _("Failure"),
            'message': _("Incorrect request"),
        }, status=500)


def get_employee_hourly_emotions(request):
    """Devuelve lista de emociones de cada empleado por horas."""
    data = json.loads(request.body)
    user_id = data["employee"]
    start_date = data["start_date"]
    end_date = data["end_date"]

    print("\n-> Parametros recibidos")
    print("empoyee = %s" % user_id)
    print("start_date = %s" % start_date)  # 2024-09-06
    print("end_date = %s" % end_date)  # 2024-09-06
    print("\n")

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        print(f"\n=>Filtro empleado {user_id}")
        object_list = EmotionAnalysis.objects.filter(
            profile__user_id=user_id,  # Filtrar por la lista de empleados a través del perfil
            recorded_at__range=(start_date, end_date)
        ).order_by('profile__user__username', 'recorded_at')

        employee_hourly_emotions = defaultdict(lambda: defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))))

        for obj in object_list:
            employee = str(obj.profile.user.username)
            # recorded_at = obj.recorded_at
            recorded_at = localtime(obj.recorded_at)  # Convertir a hora local
            date = recorded_at.strftime('%Y-%m-%d')
            hour = recorded_at.strftime('%H:00')
            dominant_emotion = obj.emotions_detected['dominant_emotion']

            # Asegurarse de que employee_hourly_emotions[employee][date][hour] sea un diccionario
            if hour not in employee_hourly_emotions[employee][date]:
                employee_hourly_emotions[employee][date][hour] = defaultdict(int)
            employee_hourly_emotions[employee][date][hour][dominant_emotion] += 1

        employee_hourly_emotions = {
            employee: {
                date: {
                    hour: dict(emotions) for hour, emotions in hours.items()
                } for date, hours in dates.items()
            } for employee, dates in employee_hourly_emotions.items()
        }
        return JsonResponse({
                            'success': True,
                            'employee_hourly_emotions': employee_hourly_emotions})
    else:
        return JsonResponse({
            'status': _("Failure"),
            'message': _("Incorrect request"),
        }, status=500)


class MeListView(ListView):
    """Devuelve lista de videos del usuario."""

    template_name = 'employee/member/me_video_list.html'

    def get_queryset(self):
        profile = self.request.user.profile

        video_list = EmotionAnalysis.objects.filter(
            profile=profile).order_by('recorded_at')
        return video_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segment"] = 'me'
        return context


def charts(request):
    """Vita de gráficos personalizados."""
    current_date = datetime.now().date()
    # Obtener la fecha y hora actual
    now = datetime.now()
    
    # Ajustar la hora a las 00:00
    start_of_day = datetime(now.year, now.month, now.day)

    worker_area_list = WorkerArea.objects.all().values('id', 'name').order_by('name')
    work_shift_list = WorkShift.objects.all().values('id', 'name').order_by('name')

    context = {
        'segment': 'charts',
        'worker_area_list': worker_area_list,
        'current_date': current_date.strftime('%Y-%m-%d'),
        'work_shift_list': work_shift_list,
        'start_date_time': start_of_day.strftime("%Y-%m-%d %H:%M"),
        'end_date_time': datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    return render(request, 'employee/charts/charts_list.html', context)
