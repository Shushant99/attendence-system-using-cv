# attendance/urls.py

from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('classrooms/<int:classroom_id>/start/', views.start_attendance, name='start_session'),
    path('sessions/<int:session_id>/take/', views.take_attendance, name='take_attendance'),
    path('sessions/<int:session_id>/video/', views.video_feed, name='video_feed'),
    path('sessions/<int:session_id>/end/', views.end_attendance, name='end_attendance'),
    path('sessions/<int:session_id>/', views.attendance_detail, name='attendance_detail'),
    path('records/<int:record_id>/update/', views.update_record_status, name='update_record_status'),
    path('sessions/<int:session_id>/status/', views.session_status, name='session_status'),
    path('reports/', views.session_report_list, name='session_report_list'),
    path('reports/<int:session_id>/', views.session_report_detail, name='session_report_detail'),
]
