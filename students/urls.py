from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Classrooms
    path('classrooms/', views.classroom_list, name='classroom_list'),
    path('classrooms/create/', views.classroom_create, name='classroom_create'),
    path('classrooms/<int:pk>/update/', views.classroom_update, name='classroom_update'),
    path('classrooms/<int:pk>/delete/', views.classroom_delete, name='classroom_delete'),
    
    # Students
    path('', views.student_list, name='student_list'),
    path('create/', views.student_create, name='student_create'),
    path('<int:pk>/update/', views.student_update, name='student_update'),
    path('<int:pk>/delete/', views.student_delete, name='student_delete'),
    
    # Teachers
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/create/', views.teacher_create, name='teacher_create'),
    path('teachers/<int:pk>/assign-classrooms/', views.teacher_assign_classrooms, name='teacher_assign_classrooms'),
    path('teachers/<int:pk>/update/', views.teacher_update, name='teacher_update'),
    path('teachers/<int:pk>/delete/', views.teacher_delete, name='teacher_delete'),
    path('teachers/<int:pk>/change-password/', views.teacher_change_password, name='teacher_change_password'),
    path('teachers/<int:pk>/impersonate/', views.teacher_impersonate, name='teacher_impersonate'),
    path('impersonate/stop/', views.impersonate_stop, name='impersonate_stop')
]