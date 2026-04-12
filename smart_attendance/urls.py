# smart_attendance/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('accounts.urls', 'accounts'), namespace='accounts')),  # Removed the import home
    path('students/', include(('students.urls', 'students'), namespace='students')),
    path('attendance/', include(('attendance.urls', 'attendance'), namespace='attendance')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
