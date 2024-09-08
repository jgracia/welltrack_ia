from rest_framework import (generics)
from django.db.models import Q
from django.http import JsonResponse

from django.contrib.auth.models import User
from .serializers import EmployeeQuerySerializer
from django.utils.translation import gettext_lazy as _

from collections import defaultdict
from apps.employee.models import EmotionAnalysis
from datetime import datetime

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
