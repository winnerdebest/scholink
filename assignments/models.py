from django.db import models
from stu_main.models import *


class Assignment(models.Model):
    class_subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE, related_name='assignments', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.class_subject} ({self.class_subject})"

  
class StudentAssignmentRecord(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_type': 'student'}, related_name='assignment_records')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='student_records')
    responses = models.JSONField()
    score = models.FloatField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_submitted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.username} - {self.assignment.class_subject}"
