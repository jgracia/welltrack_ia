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

'''
def get_chart_data(request):
    """Devuelve datos para el gráfico."""
    
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
    ]

    datasets = [
        {
            'label': 'Triste',
            'data': [65, 59, 80, 81, 56, 55, 40],
            'fill': 'false',
            'borderColor': 'rgb(75, 192, 192)',
            # 'borderColor': "#007bff",
            'tension': 0.1
        },
        {
            'label': 'Miedo',
            'data': [10, 25, 30, 25, 75, 6, 15],
            'fill': 'false',
            # 'borderColor': 'rgb(75, 192, 192)',
            'borderColor': "#007bff",
            'tension': 0.1
        },
        {
            'label': 'Enojado',
            'data': [2, 5, 40, 15, 40, 25, 30],
            'fill': 'false',
            # 'borderColor': 'rgb(75, 192, 192)',
            'borderColor': "#FF8300",
            'tension': 0.1
        },
    ]

    data = {
        'labels': labels,
        'datasets': datasets
    }

    return JsonResponse(data)
'''


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

    """print("\n=> Labels")
    print(labels)
    print()

    print("\n=> All emotions")
    print(all_emotions)
    print()

    print("=> Monthly emotions")
    print(monthly_emotions)
    print()"""

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
    
    """print("=> Datasets...")
    print(datasets)
    print()"""

    data = {
        'labels': labels,
        'datasets': datasets
    }

    return JsonResponse(data)


'''
# retorna todas las horas del dia
def get_hourly_chart_data(request, date):
    """Devuelve datos para el gráfico por horas en un día específico."""
    print("\n=> Current Date from Frontend: ", date)
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    object_list = EmotionAnalysis.objects.filter(recorded_at__date=date_obj)
    
    hourly_emotions = defaultdict(lambda: defaultdict(int))

    # Tomar las emociones de un solo registro
    if object_list.exists():
        all_emotions = object_list.first().emotions_detected.get('emotions', {}).keys()
    else:
        all_emotions = []

    # Inicializar hourly_emotions con ceros para todas las horas y emociones
    for hour in range(24):
        hour_label = f'{str(hour).zfill(2)}:00'
        for emotion in all_emotions:
            hourly_emotions[hour_label][emotion] = 0

    for obj in object_list:
        recorded_at = obj.recorded_at
        hour = recorded_at.strftime('%H:00')
        dominant_emotion = obj.emotions_detected['dominant_emotion']
        hourly_emotions[hour][dominant_emotion] += 1

    # Generar etiquetas para las 24 horas
    labels = [f'{str(hour).zfill(2)}:00' for hour in range(24)]

    datasets = []
    colors = ['#4bc0c0', '#007bff', '#FF8300', '#FF5733', '#C70039', '#900C3F', '#581845']

    # Crear datasets iterando sobre all_emotions
    for i, emotion in enumerate(all_emotions):
        data = [hourly_emotions[hour].get(emotion, 0) for hour in labels]
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
'''

'''
def get_hourly_chart_data(request, date):
    """Devuelve datos para el gráfico por horas en un día específico.

    Elimina las horas donde no existen datos.
    """
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    object_list = EmotionAnalysis.objects.filter(recorded_at__date=date_obj)
    
    hourly_emotions = defaultdict(lambda: defaultdict(int))

    # Tomar las emociones de un solo registro
    if object_list.exists():
        all_emotions = object_list.first().emotions_detected.get('emotions', {}).keys()
    else:
        all_emotions = []

    # Inicializar hourly_emotions con ceros para todas las horas y emociones
    for hour in range(24):
        hour_label = f'{str(hour).zfill(2)}:00'
        for emotion in all_emotions:
            hourly_emotions[hour_label][emotion] = 0

    for obj in object_list:
        recorded_at = obj.recorded_at
        hour = recorded_at.strftime('%H:00')
        dominant_emotion = obj.emotions_detected['dominant_emotion']
        hourly_emotions[hour][dominant_emotion] += 1

    # Filtrar etiquetas y datos para eliminar horas sin información
    labels = []
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

    for hour in range(24):
        hour_label = f'{str(hour).zfill(2)}:00'
        if any(hourly_emotions[hour_label].values()):
            labels.append(hour_label)

    # Crear datasets iterando sobre all_emotions
    for i, emotion in enumerate(all_emotions):
        data = [hourly_emotions[hour].get(emotion, 0) for hour in labels]
        datasets.append({
            'label': _(emotion),
            'data': data,
            'fill': 'false',
            'borderColor': colors[i % len(colors)].replace('0.75', '1'),  # Full opacity for borderColor
            'backgroundColor': colors[i % len(colors)],  # Transparency for backgroundColor
            'borderWidth': 1,
            #'tension': 0.1
        })

    data = {
        'labels': labels,
        'datasets': datasets
    }

    return JsonResponse(data)
'''

'''
def get_hourly_chart_data(request, date):
    """Devuelve datos para los gráficos por horas y por área en un día específico."""
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    object_list = EmotionAnalysis.objects.filter(recorded_at__date=date_obj)
    
    hourly_emotions = defaultdict(lambda: defaultdict(int))
    hourly_emotions_by_area = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    # Tomar las emociones de un solo registro
    if object_list.exists():
        all_emotions = object_list.first().emotions_detected.get('emotions', {}).keys()
        all_areas = Profile.objects.filter(emotionanalysis__in=object_list).values_list('worker_area__name', flat=True).distinct()
    else:
        all_emotions = []
        all_areas = []

    # Inicializar hourly_emotions y hourly_emotions_by_area con ceros para todas las horas, áreas y emociones
    for hour in range(24):
        hour_label = f'{str(hour).zfill(2)}:00'
        for emotion in all_emotions:
            hourly_emotions[hour_label][emotion] = 0
        for area in all_areas:
            for emotion in all_emotions:
                hourly_emotions_by_area[hour_label][area][emotion] = 0

    for obj in object_list:
        recorded_at = obj.recorded_at
        hour = recorded_at.strftime('%H:00')
        dominant_emotion = obj.emotions_detected['dominant_emotion']
        area = obj.profile.worker_area.name if obj.profile.worker_area else 'Unknown'
        hourly_emotions[hour][dominant_emotion] += 1
        hourly_emotions_by_area[hour][area][dominant_emotion] += 1

    # Filtrar etiquetas y datos para eliminar horas sin información
    labels = []
    datasets_hourly = []
    datasets_by_area = []
    colors = [
        'rgba(75, 192, 192, 0.5)',  # #4bc0c0
        'rgba(0, 123, 255, 0.5)',   # #007bff
        'rgba(255, 131, 0, 0.5)',   # #FF8300
        'rgba(255, 87, 51, 0.5)',   # #FF5733
        'rgba(199, 0, 57, 0.5)',    # #C70039
        'rgba(144, 12, 63, 0.5)',   # #900C3F
        'rgba(88, 24, 69, 0.5)'     # #581845
    ]

    for hour in range(24):
        hour_label = f'{str(hour).zfill(2)}:00'
        if any(hourly_emotions[hour_label].values()):
            labels.append(hour_label)

    # Crear datasets para el gráfico por horas
    for i, emotion in enumerate(all_emotions):
        data = [hourly_emotions[hour].get(emotion, 0) for hour in labels]
        datasets_hourly.append({
            'label': _(emotion),
            'data': data,
            'backgroundColor': colors[i % len(colors)],
            'borderColor': colors[i % len(colors)].replace('0.5', '1'),
            'borderWidth': 1
        })

    # Crear datasets para el gráfico por área
    for i, area in enumerate(all_areas):
        for j, emotion in enumerate(all_emotions):
            data = [hourly_emotions_by_area[hour][area].get(emotion, 0) for hour in labels]
            datasets_by_area.append({
                'label': f'{_(emotion)} ({area})',
                'data': data,
                'backgroundColor': colors[j % len(colors)],
                'borderColor': colors[j % len(colors)].replace('0.5', '1'),
                'borderWidth': 1
            })

    data = {
        'labels': labels,
        'datasets_hourly': datasets_hourly,
        'datasets_by_area': datasets_by_area
    }

    return JsonResponse(data)
'''


'''
def get_hourly_chart_data(request, date):
    """Devuelve datos para los gráficos por horas y áreas de trabajo en un día específico."""
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    object_list = EmotionAnalysis.objects.filter(recorded_at__date=date_obj)
    
    hourly_emotions = defaultdict(lambda: defaultdict(int))
    area_emotions = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    # Tomar las emociones de un solo registro para inicializar las llaves
    if object_list.exists():
        all_emotions = object_list.first().emotions_detected.get('emotions', {}).keys()
    else:
        all_emotions = []

    # Inicializar hourly_emotions y area_emotions con ceros
    for hour in range(24):
        hour_label = f'{str(hour).zfill(2)}:00'
        for emotion in all_emotions:
            hourly_emotions[hour_label][emotion] = 0
    
    # Procesar los datos por hora y por área de trabajo
    for obj in object_list:
        recorded_at = obj.recorded_at
        hour = recorded_at.strftime('%H:00')
        dominant_emotion = obj.emotions_detected['dominant_emotion']
        worker_area = obj.profile.worker_area.name if obj.profile.worker_area else 'Unknown Area'
        
        hourly_emotions[hour][dominant_emotion] += 1
        area_emotions[worker_area][hour][dominant_emotion] += 1

    # Filtrar etiquetas y datos para eliminar horas sin información
    labels = []
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

    # Crear etiquetas para las horas
    for hour in range(24):
        hour_label = f'{str(hour).zfill(2)}:00'
        if any(hourly_emotions[hour_label].values()):
            labels.append(hour_label)

    # Crear datasets por emoción
    for i, emotion in enumerate(all_emotions):
        data = [hourly_emotions[hour].get(emotion, 0) for hour in labels]
        datasets.append({
            'label': _(emotion),
            'data': data,
            'fill': 'false',
            'borderColor': colors[i % len(colors)].replace('0.75', '1'),  # Full opacity for borderColor
            'backgroundColor': colors[i % len(colors)],  # Transparency for backgroundColor
            'borderWidth': 1,
        })

    # Preparar los datos por área de trabajo
    area_labels = list(area_emotions.keys())
    area_datasets = []

    for i, emotion in enumerate(all_emotions):
        for area in area_labels:
            data = [area_emotions[area][hour].get(emotion, 0) for hour in labels]
            area_datasets.append({
                'label': f"{_(emotion)} ({area})",
                'data': data,
                'fill': 'false',
                'borderColor': colors[i % len(colors)].replace('0.75', '1'),  # Full opacity for borderColor
                'backgroundColor': colors[i % len(colors)],  # Transparency for backgroundColor
                'borderWidth': 1,
            })

    data = {
        'hourly': {
            'labels': labels,
            'datasets': datasets
        },
        'by_area': {
            'labels': labels,
            'datasets': area_datasets
        }
    }

    return JsonResponse(data)
'''

'''
# funcion perfecta por area
def get_hourly_chart_data(request, date):
    """Devuelve los datos para dos gráficos: uno por horas (solo horas con datos) y otro por áreas de trabajo."""
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

    # Crear datasets para el gráfico por áreas
    area_datasets = []
    for i, emotion in enumerate(all_emotions):
        data = []
        for area in sorted(all_areas):
            total_emotion_by_area = sum(area_hourly_emotions[area][hour].get(emotion, 0) for hour in area_hourly_emotions[area])
            data.append(total_emotion_by_area)

        area_datasets.append({
            'label': _(emotion),
            'data': data,
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
            'labels': sorted(all_areas),  # Etiquetas para el gráfico por áreas
            'datasets': area_datasets     # Datos para el gráfico por áreas
        }
    }

    return JsonResponse(data)
'''


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
