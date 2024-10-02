from rest_framework import (generics)
from django.db.models import Q
from django.http import JsonResponse

from django.contrib.auth.models import User
from .serializers import EmployeeQuerySerializer
from django.utils.translation import gettext_lazy as _

from collections import defaultdict
from apps.employee.models import EmotionAnalysis, Profile
from datetime import datetime

from django.utils.timezone import localtime  # Para ajustar la zona horaria local

# Create your views here.


class EmployeeQuery(generics.ListAPIView):
    serializer_class = EmployeeQuerySerializer

    def get_queryset(self):
        if self.request.method == 'GET':
            queryset = User.objects.filter(is_active=True).order_by('last_name')
            search_term = self.request.GET.get('q', None).upper()
            if search_term is not None:
                queryset = queryset.filter(
                    Q(first_name__contains=search_term)
                    | Q(last_name__contains=search_term))
            return queryset


def get_chart_data(request):
    """Devuelve datos para el gráfico."""
    current_year = datetime.now().year
    current_month = datetime.now().month
    object_list = EmotionAnalysis.objects.filter(recorded_at__year=current_year, recorded_at__month__lte=current_month)
    
    monthly_emotions = defaultdict(lambda: defaultdict(int))

    # Tomar las emociones de un solo registro
    if object_list.exists():
        all_emotions = object_list.first().emotions_detected.get('emotions', {}).keys()
    else:
        all_emotions = []

    # Inicializar monthly_emotions con ceros para todos los meses y emociones
    for month in range(1, current_month + 1):
        month_name = datetime(current_year, month, 1).strftime('%B')
        month_name = _(month_name)  # traduce el nombre del mes
        for emotion in all_emotions:
            monthly_emotions[month_name][emotion] = 0

    for obj in object_list:
        recorded_at = obj.recorded_at
        month = recorded_at.strftime('%B')
        month = _(month)  # traduce el nombre del mes
        dominant_emotion = obj.emotions_detected['dominant_emotion']
        monthly_emotions[month][dominant_emotion] += 1

    # Generar etiquetas solo hasta el mes actual
    labels = [
        _('January'),
        _('February'),
        _('March'),
        _('April'),
        _('May'),
        _('June'),
        _('July'),
        _('August'),
        _('September'),
        _('October'),
        _('November'),
        _('December')
    ][:current_month]

    datasets = []
    colors = ['#4bc0c0', '#007bff', '#FF8300', '#FF5733', '#C70039', '#900C3F', '#581845']

    # Crear datasets iterando sobre all_emotions
    for i, emotion in enumerate(all_emotions):
        data = [monthly_emotions[month].get(emotion, 0) for month in labels]
        # print(f"Emotion: {emotion}, Data: {data}")
        datasets.append({
            'label': _(emotion),
            'data': data,
            'fill': 'false',
            'borderColor': colors[i % len(colors)],
            'tension': 0.1
        })

    data = {
        'labels': labels,
        'datasets': datasets
    }

    return JsonResponse(data)


def get_hourly_chart_data(request, date):
    """Devuelve los datos para dos gráficos: uno por horas (solo horas con datos) y otro por áreas de trabajo con horas en el eje vertical."""
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    object_list = EmotionAnalysis.objects.filter(recorded_at__date=date_obj)

    # Para el gráfico por horas
    hourly_emotions = defaultdict(lambda: defaultdict(int))
    labels = [f'{str(i).zfill(2)}:00' for i in range(24)]  # Las horas del día
    all_emotions = set()

    # Para el gráfico por áreas
    area_hourly_emotions = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    all_areas = set()

    if object_list.exists():
        all_emotions = object_list.first().emotions_detected.get('emotions', {}).keys()
        all_areas = {obj.profile.worker_area.name for obj in object_list if obj.profile.worker_area}

    # Inicializar datos para ambos gráficos
    for hour in range(24):
        hour_label = f'{str(hour).zfill(2)}:00'
        for emotion in all_emotions:
            hourly_emotions[hour_label][emotion] = 0

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

            # Actualizar gráfico por horas
            hourly_emotions[hour][dominant_emotion] += 1

            # Actualizar gráfico por áreas
            area_hourly_emotions[area][hour][dominant_emotion] += 1

    # Filtrar horas con datos para el gráfico por horas
    labels_with_data = [hour for hour in labels if any(hourly_emotions[hour][emotion] > 0 for emotion in all_emotions)]

    # Crear datasets para el gráfico por horas
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
        data = [hourly_emotions[hour][emotion] for hour in labels_with_data]
        datasets.append({
            'label': _(emotion),
            'data': data,
            'fill': 'false',
            'borderColor': colors[i % len(colors)].replace('0.75', '1'),
            'backgroundColor': colors[i % len(colors)],
            'borderWidth': 1,
        })

    # Crear datasets para el gráfico por áreas (con horas en el eje vertical)
    area_datasets = []
    for i, emotion in enumerate(all_emotions):
        data = []
        for hour in labels_with_data:  # Horas como eje vertical
            total_emotion_by_hour = [area_hourly_emotions[area][hour][emotion] for area in sorted(all_areas)]
            data.append(total_emotion_by_hour)  # Datos para cada área en esa hora

        # Aplanamos el array de datos
        flattened_data = [item for sublist in data for item in sublist]
        area_datasets.append({
            'label': _(emotion),
            'data': flattened_data,
            'fill': 'false',
            'borderColor': colors[i % len(colors)].replace('0.75', '1'),
            'backgroundColor': colors[i % len(colors)],
            'borderWidth': 1,
        })

    # Empaquetar los datos de ambos gráficos
    data = {
        'hourly': {
            'labels': labels_with_data,   # Solo las horas con datos
            'datasets': datasets          # Datos filtrados por horas con datos
        },
        'by_area': {
            'labels': sorted(all_areas),  # Etiquetas para el gráfico por áreas (áreas en el eje horizontal)
            'datasets': area_datasets     # Datos filtrados por horas y emociones
        }
    }

    return JsonResponse(data)


def get_daily_chart_data(request):
    # Obtener la fecha actual
    current_day = datetime.now().date()

    # Obtener los registros de emociones del día actual
    object_list = EmotionAnalysis.objects.filter(recorded_at__date=current_day)

    # Inicializar estructuras de datos para almacenar emociones por turno y hora
    daily_emotions_by_shift = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    all_work_shifts = set()
    all_emotions = set()

    # Si hay registros, obtener las emociones detectadas y los turnos
    if object_list.exists():
        all_emotions = object_list.first().emotions_detected.get('emotions', {}).keys()
        all_work_shifts = {obj.profile.work_shift.name for obj in object_list if obj.profile.work_shift}

    # Agrupar las emociones detectadas por turno y hora (en intervalos de 1 hora)
    for obj in object_list:
        if obj.profile.work_shift:
            shift = obj.profile.work_shift.name

            # Convertir a hora local si es necesario
            recorded_at = localtime(obj.recorded_at)

            # Agrupar por la hora completa (ejemplo: 08:00-08:59)
            hour = f"{recorded_at.hour:02}:00"

            dominant_emotion = obj.emotions_detected['dominant_emotion']

            # Actualizar los datos de emociones detectadas por turno y hora
            daily_emotions_by_shift[shift][hour][dominant_emotion] += 1

    # Crear etiquetas combinadas de turno y hora
    labels_with_data = []
    for shift in sorted(all_work_shifts):
        for hour in range(24):
            hour_label = f'{str(hour).zfill(2)}:00-{str(hour).zfill(2)}:59'
            # Verificar si hay emociones detectadas en ese turno y hora
            if any(daily_emotions_by_shift[shift][f'{str(hour).zfill(2)}:00'][emotion] > 0 for emotion in all_emotions):
                labels_with_data.append(f'{shift} - [{hour_label}]')

    # Crear datasets para el gráfico con emociones por turno y hora
    daily_datasets = []
    colors = [
        'rgba(75, 192, 192, 0.75)',
        'rgba(0, 123, 255, 0.75)',
        'rgba(255, 131, 0, 0.75)',
        'rgba(255, 87, 51, 0.75)',
        'rgba(199, 0, 57, 0.75)',
        'rgba(144, 12, 63, 0.75)',
        'rgba(88, 24, 69, 0.75)'
    ]

    # Generar datasets para cada emoción detectada
    for i, emotion in enumerate(all_emotions):
        emotion_data = []
        for shift in sorted(all_work_shifts):
            for hour in range(24):
                hour_label = f'{str(hour).zfill(2)}:00'
                if f'{shift} - [{hour_label}-{str(hour).zfill(2)}:59]' in labels_with_data:
                    emotion_data.append(daily_emotions_by_shift[shift][hour_label][emotion])

        daily_datasets.append({
            'label': emotion,
            'data': emotion_data,
            'fill': 'false',
            'borderColor': colors[i % len(colors)].replace('0.75', '1'),
            'backgroundColor': colors[i % len(colors)],
            'borderWidth': 1,
        })

    # Empaquetar los datos para el gráfico diario
    data = {
        'labels': labels_with_data,
        'datasets': daily_datasets
    }

    return JsonResponse(data)
