from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import StreamingHttpResponse, JsonResponse
from django.utils import timezone
import cv2
from django.db import transaction
from students.models import ClassRoom, Student
from .models import AttendanceSession, AttendanceRecord
from .face_utils import load_known_faces, recognize_from_frame


# One global camera instance (simple for dev)
camera = cv2.VideoCapture(0)


def gen_frames(session_id):
    known_encodings, known_ids = load_known_faces()
    while True:
        success, frame = camera.read()
        if not success:
            break

        student_ids, frame = recognize_from_frame(frame, known_encodings, known_ids)

        for sid in student_ids:
            student = Student.objects.get(id=sid)
            record, created = AttendanceRecord.objects.get_or_create(
                session_id=session_id,
                student=student,
                defaults={'status': 'PRESENT'},
            )
            if not created and record.status != 'PRESENT':
                record.status = 'PRESENT'
                record.save(update_fields=['status'])

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )
@login_required
def start_attendance(request, classroom_id):
    classroom = get_object_or_404(ClassRoom, id=classroom_id)
    session = AttendanceSession.objects.create(
        classroom=classroom,
        taken_by=request.user,
    )
    # pre-create ABSENT records for all students in the class
    for student in Student.objects.filter(classroom=classroom):
        AttendanceRecord.objects.get_or_create(
            session=session,
            student=student,
            defaults={"status": "ABSENT"},
        )
    print(f"[SESSION START] Session {session.id} for classroom {classroom.id}")
    return redirect("attendance:take_attendance", session_id=session.id)


@login_required
def take_attendance(request, session_id):
    session = get_object_or_404(AttendanceSession, id=session_id)
    return render(request, "attendance/take_attendance.html", {"session": session})


def video_feed(request, session_id):
    return StreamingHttpResponse(
        gen_frames(session_id),
        content_type="multipart/x-mixed-replace; boundary=frame",
    )


@login_required
def end_attendance(request, session_id):
    session = get_object_or_404(AttendanceSession, id=session_id)
    session.end_time = timezone.now()
    session.save()
    return redirect("attendance:attendance_detail", session_id=session.id)


@login_required
def attendance_detail(request, session_id):
    session = get_object_or_404(AttendanceSession, id=session_id)
    records = session.records.select_related("student").all()
    return render(
        request,
        "attendance/attendance_list.html",
        {"session": session, "records": records},
    )


@login_required
def update_record_status(request, record_id):
    if request.method == "POST":
        status = request.POST.get("status")
        record = get_object_or_404(AttendanceRecord, id=record_id)
        record.status = status
        record.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)


@login_required
def session_status(request, session_id):
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


@login_required
def session_report_list(request):
    sessions = (
        AttendanceSession.objects.select_related("classroom", "taken_by")
        .order_by("-date", "-start_time")
    )
    return render(request, "attendance/report_list.html", {"sessions": sessions})


@login_required
def session_report_detail(request, session_id):
    session = get_object_or_404(AttendanceSession, id=session_id)
    records = session.records.select_related("student").all()
    return render(
        request,
        "attendance/report.html",
        {"session": session, "records": records},
    )
def gen_frames(session_id):
    known_encodings, known_ids = load_known_faces()
    while True:
        success, frame = camera.read()
        if not success:
            break

        student_ids, frame = recognize_from_frame(frame, known_encodings, known_ids)

        for sid in student_ids:
            student = Student.objects.get(id=sid)
            record, created = AttendanceRecord.objects.get_or_create(
                session_id=session_id,
                student=student,
                defaults={'status': 'PRESENT'},
            )
            if not created and record.status != 'PRESENT':
                record.status = 'PRESENT'
                record.save(update_fields=['status'])

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
        )