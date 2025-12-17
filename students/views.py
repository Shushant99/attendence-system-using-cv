from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Student, ClassRoom, Teacher
from .forms import StudentForm, ClassRoomForm, TeacherForm

from django.contrib import messages
from .encoding_utils import create_encodings_for_student
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def classroom_list(request):
    """List all classrooms"""
    classrooms = ClassRoom.objects.all()
    return render(request, 'students/classroom_list.html', {'classrooms': classrooms})


@login_required
def classroom_create(request):
    """Create new classroom"""
    if request.method == 'POST':
        form = ClassRoomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Classroom created successfully!')
            return redirect('students:classroom_list')
    else:
        form = ClassRoomForm()
    return render(request, 'students/classroom_form.html', {'form': form, 'title': 'Add Classroom'})


@login_required
def classroom_update(request, pk):
    """Update classroom"""
    classroom = get_object_or_404(ClassRoom, pk=pk)
    if request.method == 'POST':
        form = ClassRoomForm(request.POST, instance=classroom)
        if form.is_valid():
            form.save()
            messages.success(request, 'Classroom updated successfully!')
            return redirect('students:classroom_list')
    else:
        form = ClassRoomForm(instance=classroom)
    return render(request, 'students/classroom_form.html', {'form': form, 'title': 'Edit Classroom'})


@login_required
def classroom_delete(request, pk):
    """Delete classroom"""
    classroom = get_object_or_404(ClassRoom, pk=pk)
    if request.method == 'POST':
        classroom.delete()
        messages.success(request, 'Classroom deleted successfully!')
        return redirect('students:classroom_list')
    return render(request, 'students/classroom_confirm_delete.html', {'classroom': classroom})


@login_required
def student_list(request):
    """List all students"""
    students = Student.objects.all()
    return render(request, 'students/student_list.html', {'students': students})


@login_required
def student_create(request):
    """Create new student"""
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            print(f"\n[STUDENT SAVE] ID: {student.id}, Photo: {student.photo}")
            
            try:
                print(f"[ENCODING] Calling create_encodings_for_student({student.id})")
                create_encodings_for_student(student)
                print(f"[ENCODING] Success!")
            except Exception as e:
                print(f"[ENCODING ERROR] {e}")
                import traceback
                traceback.print_exc()
            
            messages.success(request, 'Student added successfully!')
            return redirect('students:student_list')
    else:
        form = StudentForm()
    return render(request, 'students/student_form.html', {'form': form, 'title': 'Add Student'})


@login_required
def student_update(request, pk):
    """Update student"""
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            student = form.save()
            print(f"\n[STUDENT UPDATE] ID: {student.id}, Photo: {student.photo}")
            
            try:
                print(f"[ENCODING] Calling create_encodings_for_student({student.id})")
                create_encodings_for_student(student)
                print(f"[ENCODING] Success!")
            except Exception as e:
                print(f"[ENCODING ERROR] {e}")
                import traceback
                traceback.print_exc()
            
            messages.success(request, 'Student updated successfully!')
            return redirect('students:student_list')
    else:
        form = StudentForm(instance=student)
    return render(request, 'students/student_form.html', {'form': form, 'title': 'Edit Student'})


@login_required
def student_delete(request, pk):
    """Delete student"""
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        student.delete()
        messages.success(request, 'Student deleted successfully!')
        return redirect('students:student_list')
    return render(request, 'students/student_confirm_delete.html', {'student': student})


@login_required
def teacher_list(request):
    """List all teachers"""
    teachers = Teacher.objects.all()
    return render(request, 'students/teacher_list.html', {'teachers': teachers})


@login_required
def teacher_create(request):
    """Add new teacher"""
    if request.method == 'POST':
        form = TeacherForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']

            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists')
                return render(request, 'students/teacher_form.html', {'form': form, 'title': 'Add New Teacher'})

            # 1) Create User
            user = User.objects.create_user(
                username=username,
                email=email,
                password='TempPass@123',  # temporary password
                first_name=first_name,
                last_name=last_name,
            )

            # 2) Create Teacher linked to this User
            teacher = form.save(commit=False)
            teacher.user = user
            teacher.save()

            messages.success(
                request,
                f'Teacher {user.get_full_name() or user.username} added. '
                f'Username: {username}, Temp password: TempPass@123'
            )
            return redirect('students:teacher_list')
    else:
        form = TeacherForm()

    return render(request, 'students/teacher_form.html', {'form': form, 'title': 'Add New Teacher'})

@login_required
def teacher_update(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == 'POST':
        form = TeacherForm(request.POST, instance=teacher)
        if form.is_valid():
            # update related User
            user = teacher.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.username = form.cleaned_data['username']
            user.save()

            # update Teacher
            form.save()
            messages.success(request, 'Teacher updated successfully!')
            return redirect('students:teacher_list')
    else:
        form = TeacherForm(instance=teacher)

    return render(request, 'students/teacher_form.html', {'form': form, 'title': 'Edit Teacher'})

@login_required
def teacher_delete(request, pk):
    """Delete teacher"""
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == 'POST':
        user = teacher.user
        teacher.delete()
        user.delete()
        messages.success(request, 'Teacher deleted successfully!')
        return redirect('students:teacher_list')
    
    return render(request, 'students/teacher_confirm_delete.html', {'teacher': teacher})