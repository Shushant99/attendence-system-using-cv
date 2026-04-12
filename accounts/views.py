# accounts/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from .permissions import admin_required
from .forms import LoginForm, RegisterForm

User = get_user_model()

@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful! Please login.')
            return redirect('accounts:login')
        else:
            return render(request, 'accounts/register.html', {'form': form})
    else:
        form = RegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name or user.username}!')
            return redirect('accounts:dashboard')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required(login_url='accounts:login')
@require_http_methods(["GET"])
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('accounts:login')


@login_required(login_url='accounts:login')
def dashboard(request):
    """Main dashboard after login"""
    context = {
        'user': request.user,
    }
    return render(request, 'dashboard.html', context)


# ===== USER MANAGEMENT & ROLE MANAGEMENT =====

@admin_required
def user_list(request):
    """List all users with their roles."""
    users = User.objects.all().order_by('-date_joined')
    context = {
        'users': users,
    }
    return render(request, 'accounts/user_list.html', context)


@admin_required
@require_http_methods(["GET", "POST"])
def user_role_update(request, user_id):
    """Update user role."""
    user = get_object_or_404(User, id=user_id)

    # Prevent admin from changing their own role
    if user == request.user:
        messages.error(request, 'You cannot change your own role.')
        return redirect('accounts:user_list')

    if request.method == 'POST':
        new_role = request.POST.get('role')

        if new_role not in dict(User.ROLE_CHOICES):
            messages.error(request, 'Invalid role selected.')
            return redirect('accounts:user_list')

        old_role = user.role
        user.role = new_role
        user.save()

        messages.success(request, f'{user.username} role changed from {old_role} to {new_role}')
        return redirect('accounts:user_list')

    context = {
        'user': user,
        'role_choices': User.ROLE_CHOICES,
    }
    return render(request, 'accounts/user_role_update.html', context)


@admin_required
@require_http_methods(["POST"])
def user_delete(request, user_id):
    """Delete a user."""
    user = get_object_or_404(User, id=user_id)

    # Prevent admin from deleting themselves
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('accounts:user_list')

    username = user.username
    user.delete()
    messages.success(request, f'User {username} has been deleted.')
    return redirect('accounts:user_list')

