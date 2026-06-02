# accounts/permissions.py
"""
Permission decorators and utilities for role-based access control.
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied

def admin_required(view_func):
    """Decorator to require admin role."""
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_admin():
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapped_view

def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_admin():   # uses is_admin() which checks role AND is_superuser
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapped_view

def teacher_required(view_func):
    """Decorator to require teacher role."""
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_teacher() and not request.user.is_admin():
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapped_view


def parent_required(view_func):
    """Decorator to require parent role."""
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_parent():
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapped_view


def role_required(*roles):
    """Decorator to require one of multiple roles."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if request.user.role not in roles and not request.user.is_admin():
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('accounts:dashboard')
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


class PermissionMixin:
    """Mixin to check user permissions in class-based views."""

    required_role = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        if self.required_role:
            if not self._has_permission(request.user):
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('accounts:dashboard')

        return super().dispatch(request, *args, **kwargs)

    def _has_permission(self, user):
        """Check if user has required role."""
        if isinstance(self.required_role, (list, tuple)):
            return user.role in self.required_role or user.is_admin()
        return user.role == self.required_role or user.is_admin()


# Permission utility functions
def can_manage_attendance(user):
    """Check if user can manage attendance."""
    return user.is_admin() or user.is_teacher()


def can_manage_students(user):
    """Check if user can manage student records."""
    return user.is_admin()


def can_view_reports(user):
    """Check if user can view reports."""
    return user.is_admin() or user.is_teacher()


def can_view_analytics(user):
    """Check if user can view analytics."""
    return user.is_admin() or user.is_teacher()
