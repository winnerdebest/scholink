from django.db import models
from stu_main.models import *



# This is the question model Which can either be a picture or text
class Question(models.Model):
    exam = models.ForeignKey('Exam', on_delete=models.CASCADE, related_name='questions', blank=True, null=True)
    assignment = models.ForeignKey('Assignment', on_delete=models.CASCADE, related_name='questions', blank=True, null=True)
    
    text = models.TextField(blank=True, null=True)  # Can be a text question
    image = models.ImageField(upload_to='question_images/', blank=True, null=True)  # Can be an image question

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
        return self.text[:50] if self.text else "Image-based Question"




#This is the exam model 
class Exam(models.Model):
    title = models.CharField(max_length=255)
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_type': 'teacher'})
    assigned_class = models.ForeignKey(Class, on_delete=models.CASCADE)
    duration_minutes = models.PositiveIntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

#This is the assignment model
class Assignment(models.Model):
    title = models.CharField(max_length=255)
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_type': 'teacher'})
    assigned_class = models.ForeignKey(Class, on_delete=models.CASCADE)
    due_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title



#Student exam record model
class StudentExamRecord(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_type': 'student'})
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    responses = models.JSONField()  # Stores answers as {"Q1": "A", "Q2": "C", ...}
    score = models.FloatField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_submitted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.username} - {self.exam.title}"


#Student assignment record model
class StudentAssignmentRecord(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_type': 'student'})
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    responses = models.JSONField()
    score = models.FloatField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_submitted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"


