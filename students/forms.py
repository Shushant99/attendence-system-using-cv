# students/forms.py

from django import forms
from django.contrib.auth.models import User
from .models import Student, ClassRoom, Teacher
from django.contrib.auth import get_user_model

User = get_user_model()

class TeacherForm(forms.ModelForm):
    """
    Form to add/edit teachers.
    Does NOT create or touch User; that is handled in the view.
    """
    first_name = forms.CharField(max_length=100, required=True, label='First Name')
    last_name = forms.CharField(max_length=100, required=False, label='Last Name')
    email = forms.EmailField(required=True)
    username = forms.CharField(max_length=150, required=True)

    class Meta:
        model = Teacher
        fields = ['employee_id', 'department', 'phone', 'qualification']
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'E.g., EMP001'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'E.g., Computer Science'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 XXXXXXXXXX'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'E.g., B.Tech, M.Tech'}),
        }

    def __init__(self, *args, **kwargs):
        # When editing, pre-fill extra fields from related user
        super().__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk and instance.user:
            self.fields['first_name'].initial = instance.user.first_name
            self.fields['last_name'].initial = instance.user.last_name
            self.fields['email'].initial = instance.user.email
            self.fields['username'].initial = instance.user.username

class StudentForm(forms.ModelForm):
    """Form to add/edit students"""
    class Meta:
        model = Student
        fields = ['roll_no', 'name', 'classroom', 'photo']
        widgets = {
            'roll_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'E.g., 001'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Student name'}),
            'classroom': forms.Select(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class ClassRoomForm(forms.ModelForm):
    """Form to add/edit classrooms"""
    class Meta:
        model = ClassRoom
        fields = ['name']  # Only 'name' field, removed 'section'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'E.g., CSE-1'}),
        }
