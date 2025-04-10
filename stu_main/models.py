from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    USER_TYPES = (
        ('admin', 'Admin'),
        ('principal', 'Principal'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='student')


class Class(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class ClassSubject(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    school_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="class_subjects")
    teacher = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'user_type': 'teacher'}
    )

    class Meta:
        unique_together = ('subject', 'school_class')

    def __str__(self):
        return f"{self.subject.name} - {self.school_class.name}"


class Guardian(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.phone_number}"


class Student(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="student_profile")
    photo = models.ImageField(upload_to="student_photos/", blank=True, null=True)
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)
    guardians = models.ManyToManyField(Guardian, related_name="students")
    student_class = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students"
    )

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.student_class}"


class StudentPost(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(Student, related_name="liked_posts", blank=True)
    dislikes = models.ManyToManyField(Student, related_name="disliked_posts", blank=True)

    def __str__(self):
        return f"Post by {self.student.user.get_full_name()}"

    def total_likes(self):
        return self.likes.count()

    def total_dislikes(self):
        return self.dislikes.count()
