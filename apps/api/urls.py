from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

app_name = 'api'

urlpatterns = [
    path('employee_apiview', login_required(views.EmployeeQuery.as_view()),),
    path('get_chart_data/', login_required(views.get_chart_data), 
         name="get_chart_data"),
]
