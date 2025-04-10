from django.db import models
from stu_main.models import *


class Exam(models.Model):
    class_subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE, related_name='exams', null=True, blank=True)
    duration_minutes = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.class_subject} ({self.class_subject})"


class Assignment(models.Model):
    class_subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE, related_name='assignments', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.class_subject} ({self.class_subject})"


class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions', blank=True, null=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='questions', blank=True, null=True)

    text = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='question_images/', blank=True, null=True)

    option_a_text = models.CharField(max_length=255, blank=True, null=True)
    option_a_image = models.ImageField(upload_to='answer_images/', blank=True, null=True)

    option_b_text = models.CharField(max_length=255, blank=True, null=True)
    option_b_image = models.ImageField(upload_to='answer_images/', blank=True, null=True)

    option_c_text = models.CharField(max_length=255, blank=True, null=True)
    option_c_image = models.ImageField(upload_to='answer_images/', blank=True, null=True)

    option_d_text = models.CharField(max_length=255, blank=True, null=True)
    option_d_image = models.ImageField(upload_to='answer_images/', blank=True, null=True)

    correct_answer = models.CharField(
        max_length=1,
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]
    )

    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_type': 'teacher'})

    def __str__(self):
        if self.text:
            return self.text[:50]
        return f"Image Question by {self.created_by.username}"


class StudentExamRecord(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_type': 'student'}, related_name='exam_records')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='student_records')
    responses = models.JSONField()  # Format: {"question_id": "A"}
    score = models.FloatField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_submitted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.username} - {self.exam.class_subject}"


class StudentAssignmentRecord(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_type': 'student'}, related_name='assignment_records')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='student_records')
    responses = models.JSONField()
    score = models.FloatField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_submitted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.username} - {self.assignment.class_subject}"
