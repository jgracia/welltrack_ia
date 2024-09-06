from rest_framework import (generics)
from django.db.models import Q

from django.contrib.auth.models import User
from .serializers import EmployeeQuerySerializer

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
