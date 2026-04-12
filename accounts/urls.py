# accounts/urls.py

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.dashboard, name='home'),

    # User Management
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/role/', views.user_role_update, name='user_role_update'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
]

