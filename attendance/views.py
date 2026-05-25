from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import StreamingHttpResponse, JsonResponse, HttpResponse
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from datetime import datetime, timedelta
import cv2
import logging
import csv
import json

from students.models import ClassRoom, Student
from .models import AttendanceSession, AttendanceRecord
from .face_utils import load_known_faces, recognize_from_frame
from accounts.permissions import teacher_required, admin_required, can_manage_attendance

logger = logging.getLogger('attendance')

# Global camera instance
camera = None
camera_active = True
CAMERA_INDEX = 0



@teacher_required
def start_attendance(request, classroom_id):
    """Start a new attendance session."""
    try:
        classroom = get_object_or_404(ClassRoom, id=classroom_id)

        # Check teacher is assigned to this classroom (skip check for admins)
        if not request.user.is_admin():
            try:
                assigned = request.user.teacher_profile.assigned_classrooms.all()
                if classroom not in assigned:
                    messages.error(request, 'You are not assigned to this classroom.')
                    return redirect('students:classroom_list')
            except Exception:
                messages.error(request, 'Teacher profile not found.')
                return redirect('students:classroom_list')

        # Check if a session already exists for today
        today = timezone.now().date()
        existing_session = AttendanceSession.objects.filter(
            classroom=classroom,
            date=today
        ).first()

        if existing_session:
            messages.warning(request, f'A session for {classroom.name} already exists today. Resuming it.')
            return redirect('attendance:take_attendance', session_id=existing_session.id)

        # Create new session
        with transaction.atomic():
            session = AttendanceSession.objects.create(
                classroom=classroom,
                taken_by=request.user,
            )
            students = Student.objects.filter(classroom=classroom)
            for student in students:
                AttendanceRecord.objects.get_or_create(
                    session=session,
                    student=student,
                    defaults={"status": "ABSENT"},
                )

        logger.info(f"Started attendance session {session.id} for classroom {classroom.name} by {request.user.username}")
        messages.success(request, f"Attendance session started for {classroom.name}")
        return redirect("attendance:take_attendance", session_id=session.id)

    except Exception as e:
        logger.error(f"Error starting attendance session: {e}", exc_info=True)
        messages.error(request, f"Failed to start attendance session: {str(e)}")
        return redirect("students:classroom_list")

@teacher_required
def take_attendance(request, session_id):
    """Display attendance page with video feed."""
    try:
        session = get_object_or_404(AttendanceSession, id=session_id)
        return render(request, "attendance/take_attendance.html", {"session": session})
    except Exception as e:
        logger.error(f"Error in take_attendance: {e}")
        messages.error(request, "Error loading attendance session")
        return redirect("attendance:session_report_list")
@login_required
def process_frame(request, session_id):
    """Receive a frame from browser camera, run face recognition, return annotated frame."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        import base64
        import numpy as np

        data = json.loads(request.body)
        image_data = data.get('frame', '')

        # Strip data URL prefix
        if ',' in image_data:
            image_data = image_data.split(',')[1]

        # Decode base64 to OpenCV image
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return JsonResponse({'error': 'Invalid image'}, status=400)

        known_encodings, known_ids = load_known_faces()
        student_ids, annotated_frame = recognize_from_frame(frame, known_encodings, known_ids)

        # Update attendance records
        for sid in student_ids:
            try:
                student = Student.objects.get(id=sid)
                record, created = AttendanceRecord.objects.get_or_create(
                    session_id=session_id,
                    student=student,
                    defaults={'status': 'PRESENT', 'marked_by': None},
                )
                if not created and record.status != 'PRESENT':
                    record.status = 'PRESENT'
                    record.save(update_fields=['status'])
            except Student.DoesNotExist:
                pass

        # Encode annotated frame back to base64
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        annotated_b64 = base64.b64encode(buffer.tobytes()).decode('utf-8')

        return JsonResponse({
            'success': True,
            'annotated_frame': f'data:image/jpeg;base64,{annotated_b64}',
        })

    except Exception as e:
        logger.error(f"Error in process_frame: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def end_attendance(request, session_id):
    """End attendance session."""
    try:
        session = get_object_or_404(AttendanceSession, id=session_id)
        session.end_time = timezone.now()
        session.save()
       
        logger.info(f"Ended attendance session {session.id}")
        messages.success(request, "Attendance session ended")
        return redirect("attendance:attendance_detail", session_id=session.id)
    except Exception as e:
        logger.error(f"Error ending attendance session: {e}")
        messages.error(request, "Error ending attendance session")
        return redirect("attendance:session_report_list")

@login_required
def attendance_detail(request, session_id):
    """View attendance records for a session."""
    try:
        session = get_object_or_404(AttendanceSession, id=session_id)
        records = session.records.select_related("student").all()
        return render(
            request,
            "attendance/attendance_list.html",
            {"session": session, "records": records},
        )
    except Exception as e:
        logger.error(f"Error in attendance_detail: {e}")
        messages.error(request, "Error loading attendance details")
        return redirect("attendance:session_report_list")


@login_required
def update_record_status(request, record_id):
    """Update attendance status for a student."""
    try:
        if request.method == "POST":
            status = request.POST.get("status")
            if status not in dict(AttendanceRecord.STATUS_CHOICES):
                return JsonResponse({"success": False, "error": "Invalid status"}, status=400)

            record = get_object_or_404(AttendanceRecord, id=record_id)
            old_status = record.status
            record.status = status
            record.marked_by = request.user
            record.save()

            logger.info(f"Updated attendance record {record_id}: {old_status} -> {status} by {request.user.username}")
            return JsonResponse({"success": True})
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=400)
    except Exception as e:
        logger.error(f"Error updating record status: {e}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
def session_status(request, session_id):
    """Get session status with present students."""
    try:
        records = (
            AttendanceRecord.objects.filter(session_id=session_id, status="PRESENT")
            .select_related("student")
        )
        data = [
            {
                "id": r.id,
                "roll_no": r.student.roll_no,
                "name": r.student.name,
            }
            for r in records
        ]
        return JsonResponse({"present_students": data})
    except Exception as e:
        logger.error(f"Error in session_status: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def session_report_list(request):
    """List all attendance sessions."""
    try:
        if request.user.is_admin():
            sessions = AttendanceSession.objects.select_related(
                "classroom", "taken_by"
            ).order_by("-date", "-start_time")
        else:
            # Teachers only see sessions for their assigned classrooms
            try:
                assigned = request.user.teacher_profile.assigned_classrooms.all()
                sessions = AttendanceSession.objects.filter(
                    classroom__in=assigned
                ).select_related("classroom", "taken_by").order_by("-date", "-start_time")
            except Exception:
                sessions = AttendanceSession.objects.none()

        return render(request, "attendance/report_list.html", {"sessions": sessions})
    except Exception as e:
        logger.error(f"Error in session_report_list: {e}")
        messages.error(request, "Error loading attendance reports")
        return render(request, "attendance/report_list.html", {"sessions": []})

@login_required
def session_report_detail(request, session_id):
    """View detailed report for a session."""
    try:
        session = get_object_or_404(AttendanceSession, id=session_id)
        records = session.records.select_related("student").all()
        return render(
            request,
            "attendance/report.html",
            {"session": session, "records": records},
        )
    except Exception as e:
        logger.error(f"Error in session_report_detail: {e}")
        messages.error(request, "Error loading report details")
        return redirect("attendance:session_report_list")


# ===== ANALYTICS & EXPORT FEATURES =====

@teacher_required
def attendance_analytics(request):
    """Analytics dashboard with attendance statistics."""
    try:
        # Date range filter
        days = request.GET.get('days', '30')
        try:
            days = int(days)
        except ValueError:
            days = 30

        start_date = timezone.now().date() - timedelta(days=days)
        # Scope classrooms by role
        classroom_id = request.GET.get('classroom_id')

        if request.user.is_admin():
            
            classrooms = ClassRoom.objects.filter(id=classroom_id) if classroom_id else ClassRoom.objects.all()
            
                
        else:
    # Teacher — only assigned classrooms
            try:
                classrooms = request.user.teacher_profile.assigned_classrooms.all()
            except Exception:
                classrooms = ClassRoom.objects.none()
        # Query data
        sessions = AttendanceSession.objects.filter(
            date__gte=start_date
        ).select_related('classroom', 'taken_by')

        total_records = AttendanceRecord.objects.filter(
        session__date__gte=start_date,
        session__classroom__in=classrooms
        )

        # Statistics
        present_count = total_records.filter(status='PRESENT').count()
        absent_count = total_records.filter(status='ABSENT').count()
        late_count = total_records.filter(status='LATE').count()
        leave_count = total_records.filter(status='LEAVE').count()
        total_count = total_records.count()

        # Attendance rate
        attendance_rate = (present_count / total_count * 100) if total_count > 0 else 0

        # Per-classroom stats
        classroom_stats = []
        for classroom in classrooms:
            class_records = total_records.filter(session__classroom=classroom)
            class_present = class_records.filter(status='PRESENT').count()
            class_total = class_records.count()
            class_rate = (class_present / class_total * 100) if class_total > 0 else 0

            if class_total > 0:
                classroom_stats.append({
                    'name': classroom.name,
                    'present': class_present,
                    'absent': class_records.filter(status='ABSENT').count(),
                    'late': class_records.filter(status='LATE').count(),
                    'total': class_total,
                    'rate': round(class_rate, 2)
                })

        # Attendance trend (daily)
        daily_data = []
        for i in range(days, 0, -1):
            date = (timezone.now().date() - timedelta(days=i))
            day_records = total_records.filter(session__date=date)
            day_present = day_records.filter(status='PRESENT').count()
            if day_records.exists():
                daily_data.append({
                    'date': date.strftime('%m-%d'),
                    'present': day_present,
                    'total': day_records.count()
                })

        context = {
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,
            'leave_count': leave_count,
            'total_count': total_count,
            'attendance_rate': round(attendance_rate, 2),
            'classroom_stats': classroom_stats,
            'daily_data': json.dumps(daily_data),
            'sessions': sessions,
            'days': days,
            'all_classrooms': ClassRoom.objects.all(),   # for admin dropdown
            'selected_classroom_id': int(classroom_id) if classroom_id else None,
        }

        return render(request, 'attendance/analytics.html', context)

    except Exception as e:
        raise e
        # logger.error(f"Error in attendance_analytics: {e}")
        # messages.error(request, "Error loading analytics")
        # return redirect('attendance:session_report_list')


@teacher_required
def export_attendance_csv(request):
    """Export attendance records to CSV."""
    try:
        days = request.GET.get('days', '30')
        try:
            days = int(days)
        except ValueError:
            days = 30

        start_date = timezone.now().date() - timedelta(days=days)

        # Get records
        records = AttendanceRecord.objects.filter(
            session__date__gte=start_date
        ).select_related('student', 'session__classroom', 'marked_by')

        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="attendance_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Date', 'Session Time', 'Classroom', 'Roll No', 'Student Name',
            'Status', 'Marked By', 'Timestamp'
        ])

        for record in records:
            writer.writerow([
                record.session.date.strftime('%d-%m-%Y'),
                record.session.start_time.strftime('%H:%M') if record.session.start_time else '',
                record.session.classroom.name,
                record.student.roll_no,
                record.student.name,
                record.status,
                record.marked_by.get_full_name() if record.marked_by else 'Auto',
                record.timestamp.strftime('%d-%m-%Y %H:%M:%S'),
            ])

        return response

    except Exception as e:
        logger.error(f"Error in export_attendance_csv: {e}")
        messages.error(request, "Error exporting CSV")
        return redirect('attendance:session_report_list')


@teacher_required
def export_session_csv(request, session_id):
    """Export single session to CSV."""
    try:
        session = get_object_or_404(AttendanceSession, id=session_id)
        records = session.records.select_related('student')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="attendance_{session.classroom.name}_{session.date}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Session Report', session.classroom.name, session.date])
        writer.writerow([])
        writer.writerow(['Roll No', 'Student Name', 'Status', 'Timestamp'])

        for record in records:
            writer.writerow([
                record.student.roll_no,
                record.student.name,
                record.status,
                record.timestamp.strftime('%H:%M:%S'),
            ])

        return response

    except Exception as e:
        logger.error(f"Error in export_session_csv: {e}")
        messages.error(request, "Error exporting session")
        return redirect('attendance:session_report_list')


@login_required
def analytics_api_data(request):
    """API endpoint for chart data."""
    try:
        days = int(request.GET.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)

        # Status breakdown
        total_records = AttendanceRecord.objects.filter(
            session__date__gte=start_date
        )

        status_data = {
            'PRESENT': total_records.filter(status='PRESENT').count(),
            'ABSENT': total_records.filter(status='ABSENT').count(),
            'LATE': total_records.filter(status='LATE').count(),
            'LEAVE': total_records.filter(status='LEAVE').count(),
        }

        # Classroom breakdown
        classroom_data = {}
        for classroom in ClassRoom.objects.all():
            class_present = total_records.filter(
                session__classroom=classroom,
                status='PRESENT'
            ).count()
            class_total = total_records.filter(session__classroom=classroom).count()
            if class_total > 0:
                classroom_data[classroom.name] = {
                    'present': class_present,
                    'total': class_total,
                    'rate': round((class_present / class_total * 100), 2)
                }

        return JsonResponse({
            'status': 'success',
            'status_data': status_data,
            'classroom_data': classroom_data,
        })

    except Exception as e:
        logger.error(f"Error in analytics_api_data: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)})

