from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import StreamingHttpResponse, JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
import cv2
import logging

from students.models import ClassRoom, Student
from .models import AttendanceSession, AttendanceRecord
from .face_utils import load_known_faces, recognize_from_frame

logger = logging.getLogger('attendance')

# Global camera instance
camera = None
CAMERA_INDEX = 0


def get_camera():
    """Get or create camera instance."""
    global camera
    try:
        if camera is None:
            camera = cv2.VideoCapture(CAMERA_INDEX)
            if not camera.isOpened():
                logger.error("Failed to open camera")
                return None
        return camera
    except Exception as e:
        logger.error(f"Error getting camera: {e}")
        return None


def gen_frames(session_id):
    """Generator function to stream video frames with face recognition."""
    cam = get_camera()
    if cam is None:
        logger.error(f"Camera not available for session {session_id}")
        return

    known_encodings, known_ids = load_known_faces()
    logger.info(f"Starting frame generation for session {session_id}")

    try:
        while True:
            success, frame = cam.read()
            if not success:
                logger.warning(f"Failed to read frame for session {session_id}")
                break

            try:
                student_ids, frame = recognize_from_frame(frame, known_encodings, known_ids)

                # Update attendance records for recognized students
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
                        logger.error(f"Student {sid} not found")
                    except Exception as e:
                        logger.error(f"Error updating attendance for student {sid}: {e}")

            except Exception as e:
                logger.error(f"Error in frame processing for session {session_id}: {e}")
                continue

            try:
                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    logger.warning("Failed to encode frame")
                    continue
                frame_bytes = buffer.tobytes()
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )
            except Exception as e:
                logger.error(f"Error encoding frame: {e}")
                continue

    except GeneratorExit:
        logger.info(f"Client disconnected from session {session_id}")
    except Exception as e:
        logger.error(f"Error in gen_frames for session {session_id}: {e}", exc_info=True)


@login_required
def start_attendance(request, classroom_id):
    """Start a new attendance session."""
    try:
        classroom = get_object_or_404(ClassRoom, id=classroom_id)

        with transaction.atomic():
            session = AttendanceSession.objects.create(
                classroom=classroom,
                taken_by=request.user,
            )
            # Pre-create ABSENT records for all students
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
        messages.error(request, "Failed to start attendance session")
        return redirect("students:classroom_list")


@login_required
def take_attendance(request, session_id):
    """Display attendance page with video feed."""
    try:
        session = get_object_or_404(AttendanceSession, id=session_id)
        return render(request, "attendance/take_attendance.html", {"session": session})
    except Exception as e:
        logger.error(f"Error in take_attendance: {e}")
        messages.error(request, "Error loading attendance session")
        return redirect("attendance:session_report_list")


def video_feed(request, session_id):
    """Stream video feed with face recognition."""
    try:
        session = get_object_or_404(AttendanceSession, id=session_id)
        return StreamingHttpResponse(
            gen_frames(session_id),
            content_type="multipart/x-mixed-replace; boundary=frame",
        )
    except Exception as e:
        logger.error(f"Error in video_feed: {e}")
        return JsonResponse({"error": "Failed to start video feed"}, status=500)


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
        sessions = (
            AttendanceSession.objects.select_related("classroom", "taken_by")
            .order_by("-date", "-start_time")
        )
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
