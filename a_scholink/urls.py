from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('academic_main.urls')),
    path('students/', include('stu_main.urls')),
    path('admin/', admin.site.urls),
    path('exam/', include('exams.urls')),
    path('teacher/', include('teacher_logic.urls')),
    path('assignments/', include('assignments.urls')),
    path('principal/', include('principal.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)