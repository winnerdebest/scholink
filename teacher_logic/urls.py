from django.urls import path
from .views import *

app_name = 'teacher'

urlpatterns = [
    path('', teacher_dashboard, name='teacher_dashboard'),
    path('teacher/class/<int:class_id>/', teacher_class_detail, name='teacher_class_detail'),
    path("subject/<int:class_subject_id>/", subject_detail_view, name="class_subject_detail"),
    # Activation toggle
    path("assignment/<int:assignment_id>/toggle/", toggle_assignment_active, name="toggle_assignment_active"),
    path("exam/<int:exam_id>/toggle/", toggle_exam_active, name="toggle_exam_active"),

     path('subjects/<int:class_subject_id>/term/<int:term_id>/create-exam/', create_exam, name='create_exam'),
    path('subjects/<int:class_subject_id>/term/<int:term_id>/create-assignment/', create_assignment, name='create_assignment'),
]
