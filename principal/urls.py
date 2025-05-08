from django.urls import path
from .views import *

app_name = 'principal'


urlpatterns = [
    path("", principal_dashboard, name="principal_dashboard"),
    path("register-student/", create_student, name="create_student"),
    path("edit-student/<int:pk>/", edit_student, name="edit_student"),
    path("delete-student/<int:pk>/", delete_student, name="delete_student"),
    path('student-list/', student_list, name='student_list'),

    path("register-teacher/", create_teacher, name="create_teacher"),
    path("edit-teacher/<int:pk>/", edit_teacher, name="edit_teacher"),
    path("delete-teacher/<int:pk>/", delete_teacher, name="delete_teacher"),
    path('teacher-list/', teacher_list, name='teacher_list'),
    path('class-list/', class_list, name='class_list'),
    path('subject-list/',subject_list, name='subject_list'),


    path("subjects/", subject_list, name="subject_list"),
    path("subjects/create/", create_subject, name="create_subject"),
    path("subjects/<int:subject_id>/edit/", edit_subject, name="edit_subject"),
    path("subjects/<int:subject_id>/delete/", delete_subject, name="delete_subject"),

    path('create-class/', create_class, name="create_class"),
    path('class-list/', class_list, name="class_list"),
    path("classes/<int:class_id>/", class_detail, name="class_detail"),

    path("classes/<int:class_id>/assign-subject/", assign_subject_to_class, name="assign_subject"),
    path("class-subjects/<int:classsubject_id>/edit/", edit_class_subject, name="edit_class_subject"),
    path("class-subjects/<int:classsubject_id>/delete/", delete_class_subject, name="delete_class_subject"),
    path("classes/<int:class_id>/edit/", edit_class, name="edit_class"),
    path("classes/<int:class_id>/delete/", delete_class, name="delete_class"),

    path("grade_customize/", grade_customize, name="grade_customize"),
    path("settings/", settings_view, name="settings")
]
