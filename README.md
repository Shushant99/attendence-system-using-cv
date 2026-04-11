# Smart Attendance System (Django + Face Recognition)

A web-based attendance system that uses real-time webcam-based face recognition to automatically mark students as present. Features include teacher and admin dashboards for manual attendance management, comprehensive reporting, and automated absence tracking.

## 🚀 Features

- **Automated Face Recognition**: Real-time facial recognition to mark attendance
- **Student Management**: Manage student data with classroom mapping
- **Multi-user Support**: Separate portals for admins and teachers
- **Live Camera Integration**: Direct webcam feed for attendance capture
- **Manual Adjustments**: Teachers can manually edit attendance records
- **Attendance Reports**: Comprehensive session and student attendance reports
- **Automated Absence Tracking**: Auto-mark students absent after session ends
- **Database Logging**: Complete audit trail of attendance changes

## 📋 Prerequisites

- **Python**: 3.8+ (3.10+ recommended)
- **Webcam**: For face recognition
- **Database**: SQLite (default) or PostgreSQL
- **OS Support**: Windows, macOS, Linux

## 🔧 Installation & Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd attendence-system-using-cv
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration (Optional)

Create a `.env` file in the project root for environment-specific settings:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
```

### 5. Database Setup

```bash
# Create database tables
python manage.py makemigrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser

# (Optional) Load sample data
python manage.py loaddata sample_data  # if sample data exists
```

### 6. Run Development Server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## 📁 Project Structure

```
attendence-system-using-cv/
├── smart_attendance/          # Main project configuration
│   ├── settings.py           # Django settings
│   ├── urls.py               # URL routing
│   ├── logging_config.py      # Logging configuration
│   └── wsgi.py               # WSGI entry point
├── accounts/                  # User authentication app
│   ├── models.py             # User model
│   ├── views.py              # Authentication views
│   ├── forms.py              # Registration/Login forms
│   └── urls.py               # Account URLs
├── students/                  # Student management app
│   ├── models.py             # Student, Classroom, Teacher models
│   ├── views.py              # CRUD views for students/classrooms
│   ├── forms.py              # Student/Classroom forms
│   ├── encoding_utils.py      # Face encoding utilities
│   └── urls.py               # Student URLs
├── attendance/               # Attendance tracking app
│   ├── models.py             # AttendanceSession, AttendanceRecord models
│   ├── views.py              # Attendance views
│   ├── face_utils.py         # Face recognition utilities
│   ├── urls.py               # Attendance URLs
│   └── templatetags/         # Custom template filters
├── templates/                # HTML templates
│   ├── base.html             # Base template
│   ├── dashboard.html        # Dashboard
│   ├── navbar.html           # Navigation
│   ├── accounts/             # Auth templates
│   ├── students/             # Student management templates
│   └── attendance/           # Attendance templates
├── static/                   # Static files (CSS, JS)
│   ├── css/styles.css        # Styling
│   └── js/attendance.js      # JavaScript functions
├── media/                    # User-uploaded files (photos, encodings)
├── logs/                     # Application logs
├── db.sqlite3                # SQLite database
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🏃 Usage Guide

### Admin Portal

1. Log in with superuser credentials
2. Manage students, classrooms, and teachers
3. View all attendance records
4. Generate reports

### Teacher Portal

1. Log in with teacher account
2. Start attendance session for a classroom
3. Monitor real-time face recognition
4. Manually edit attendance if needed
5. End session and view report

### Taking Attendance

1. Navigate to "Start Attendance"
2. Select classroom
3. Allow camera access
4. System automatically recognizes and marks students present
5. Can manually adjust attendance before ending session

## 🗄️ Database Models

### Student

- `roll_no`: Student roll number (unique)
- `name`: Student name
- `classroom`: Foreign key to ClassRoom
- `photo`: Student photo for face recognition

### Classroom

- `name`: Classroom name (unique)
- `created_at`: Creation timestamp

### AttendanceSession

- `classroom`: Foreign key to ClassRoom
- `date`: Session date
- `start_time`: Session start time
- `end_time`: Session end time
- `taken_by`: Teacher who started session

### AttendanceRecord

- `session`: Foreign key to AttendanceSession
- `student`: Foreign key to Student
- `status`: Present/Absent/Late/Leave
- `timestamp`: When record was created
- `marked_by`: User who manually marked (if applicable)

### Teacher

- `user`: OneToOne relationship with User
- `employee_id`: Unique employee ID
- `department`: Department
- `phone`: Contact number
- `qualification`: Academic qualification

## ⚙️ Configuration

### Face Recognition Settings

Edit in `attendance/face_utils.py`:

```python
MODEL_NAME = "Facenet"           # Model for embeddings
DIST_THRESHOLD = 0.65            # Distance threshold for recognition
```

### Logging

Logs are stored in the `logs/` directory:

- `debug.log`: Detailed debug information
- `attendance.log`: Attendance-related events
- `face_recognition.log`: Face recognition details

## 📊 Features in Detail

### Face Recognition Pipeline

1. **Capture**: Webcam captures live video frames
2. **Detection**: Haar Cascade detects faces in frames
3. **Embedding**: DeepFace generates embeddings using Facenet model
4. **Matching**: Cosine similarity compares with stored encodings
5. **Mark**: Matching students marked present automatically

### Manual Adjustments

Teachers can manually change attendance status:

- Present → Absent
- Absent → Present/Leave/Late
- Changes are logged with timestamp and user info

## 🔍 Troubleshooting

### Camera Not Working

- Check camera permissions
- Ensure camera is not in use by other applications
- Restart the development server

### Low Recognition Accuracy

- Ensure good lighting conditions
- Use clear, frontal photos during student registration
- Adjust `DIST_THRESHOLD` in face_utils.py

### Database Errors

```bash
# Reset database (WARNING: Deletes all data)
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### Missing Dependencies

```bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

## 🚀 Deployment

### Production Setup

1. Set `DEBUG=False` in settings.py
2. Configure `ALLOWED_HOSTS` with your domain
3. Use PostgreSQL instead of SQLite
4. Set secure `SECRET_KEY`
5. Use gunicorn as WSGI server:
   ```bash
   gunicorn smart_attendance.wsgi
   ```

### Environment Variables

Create `.env` file and load with `python-dotenv`:

```
DEBUG=False
SECRET_KEY=your-very-secure-key
ALLOWED_HOSTS=example.com,www.example.com
DATABASE_URL=postgresql://user:password@localhost/dbname
```

## 📝 API Endpoints

### Attendance

- `GET /attendance/sessions/` - List all sessions
- `GET /attendance/session/<id>/` - Session details
- `POST /attendance/session/<id>/end/` - End session
- `POST /attendance/record/<id>/update-status/` - Update record status
- `GET /attendance/video-feed/<session_id>/` - Video stream

### Students

- `GET /students/` - List students
- `POST /students/create/` - Create student
- `GET /students/<id>/` - Student details
- `POST /students/<id>/update/` - Update student
- `DELETE /students/<id>/delete/` - Delete student

## 🔐 Security Considerations

- Never commit `.env` files or secrets
- Rotate `SECRET_KEY` in production
- Use HTTPS in production
- Implement CSRF protection (already enabled)
- Validate all user inputs
- Use strong passwords
- Implement rate limiting for API endpoints
- Regular database backups

## 📦 Dependencies

See `requirements.txt` for complete list. Key packages:

- Django 4.2 - Web framework
- OpenCV - Computer vision
- DeepFace - Face recognition
- Pillow - Image processing
- djangorestframework - API framework

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📧 Contact & Support

For issues, questions, or suggestions:

- Open an issue on GitHub
- Contact: [your-email@example.com]

## 🎯 Future Enhancements

- [ ] Mobile app for attendance review
- [ ] Advanced analytics and attendance insights
- [ ] SMS/Email notifications
- [ ] Multi-camera support
- [ ] Attendance export to Excel/PDF
- [ ] Biometric attendance integration
- [ ] Real-time attendance dashboard
- [ ] Student mobile app for verification
- [ ] Historical analysis and patterns
- [ ] Export to third-party systems

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [OpenCV Documentation](https://docs.opencv.org/)
- [DeepFace Repository](https://github.com/serengp/deepface)
- [Face Recognition Guide](https://face-recognition.readthedocs.io/)

---

**Last Updated**: April 2026
**Version**: 1.0.0
