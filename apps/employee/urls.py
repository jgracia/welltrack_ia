from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'employee'

urlpatterns = [
    # path('', views.employee_list, name='employee_list'),
    path('', login_required(views.EmployeeListView.as_view()),
         name='employee_list'),
    # path('new/', login_required(views.EmployeeNew.as_view()),
    #     name='employee_new'),
    # path('edit/<int:pk>', login_required(views.EmployeeEdit.as_view()),
    #      name='employee_edit'),
    path('signup/', login_required(views.signup), name='signup'),
    path('edit/<int:pk>', login_required(views.edit_employee), name='edit_employee'),
    path('profile/', login_required(views.profile), name='users-profile'),
    path('profile/edit/', login_required(views.edit_profile), name='edit_profile'),

    path('delete/<int:pk>', login_required(views.employee_delete),
         name='employee_delete'),

    # rutas área de trabajo
    path('worker_area', login_required(views.WorkerAreaListView.as_view()),
         name='worker_area_list'),
    path('worker_area/new/', login_required(views.WorkerAreaNew.as_view()),
         name='worker_area_new'),
    path('worker_area/edit/<int:pk>', login_required(views.WorkerAreaEdit.as_view()),
         name='worker_area_edit'),
    path('worker_area/delete/<int:pk>', login_required(views.worker_area_delete),
         name='worker_area_delete'),

    # rutas turnos de trabajo
    path('work_shift', login_required(views.WorkShiftListView.as_view()),
         name='work_shift_list'),
    path('work_shift/new/', login_required(views.WorkShiftNew.as_view()),
         name='work_shift_new'),
    path('work_shift/edit/<int:pk>', login_required(views.WorkShiftEdit.as_view()),
         name='work_shift_edit'),
    path('work_shift/delete/<int:pk>', login_required(views.work_shift_delete),
         name='work_shift_delete'),

    # ruta análisis de emociones
    # path('emotion_analysis', login_required(views.emotion_analysis), 
    #     name='emotion_analysis'),
    path('video_list', login_required(views.VideoListView.as_view()),
         name='video_list'),
    path('video/new/', login_required(views.VideoNew.as_view()),
         name='video_new'),
    path('video/edit/<int:pk>', login_required(views.VideoEdit.as_view()),
         name='video_edit'),
    path('video/delete/<int:pk>', login_required(views.video_delete),
         name='video_delete'),

    path('analyze_video', login_required(views.analyze_video),
         name='analyze_video'),
    path('analyze_video/task-status/<str:task_id>/', 
         views.analyze_video_task_status, name='analyze_video-task_status'),

    # rutas Analytics
    path('analytics', login_required(views.analytics), name='analytics'),
    # path('analytics', login_required(views.AnalyticsListView.as_view()),
    #     name='analytics'),

    path('get_worker_area_emotions/', login_required(views.get_worker_area_emotions),
         name='get_worker_area_emotions'),
    path('get_work_shift_emotions/', login_required(views.get_work_shift_emotions),
         name='get_work_shift_emotions'),
    path('get_hourly_emotions/', login_required(views.get_hourly_emotions),
         name='get_hourly_emotions'),
    path('get_employee_hourly_emotions/', login_required(views.get_employee_hourly_emotions),
         name='get_employee_hourly_emotions'),

    # rutas charts
    path('charts', login_required(views.charts), name='charts'),
    path('get_worker_area_chart_data/', 
         login_required(views.get_worker_area_chart_data),
         name='get_worker_area_chart_data'),
    path('get_work_shift_chart_data/', 
         login_required(views.get_work_shift_chart_data),
         name='get_work_shift_chart_data'),
    path('get_hour_chart_data/', 
         login_required(views.get_hour_chart_data),
         name='get_hour_chart_data'),
    path('get_employee_chart_data/', 
         login_required(views.get_employee_chart_data),
         name='get_employee_chart_data'),

    # rutas del usuario normal
    path('me', login_required(views.MeListView.as_view()), name="me"),
]
