from rest_framework import serializers
from django.contrib.auth.models import User


class FullNameFieldEmployee(serializers.Field):
    def to_representation(self, value):
        return f"{value.first_name} {value.last_name}"


class EmployeeQuerySerializer(serializers.ModelSerializer):
    # metodo para renombrar campos para utilizar en Virtual Select JS
    value = serializers.IntegerField(source='id')
    # label = serializers.CharField(source='descripcion')
    label = FullNameFieldEmployee(source='*')

    class Meta:
        model = User
        fields = ('value', 'label', )
