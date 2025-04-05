from django.contrib import admin
from django.utils.html import format_html
from .models import *


# Inline Question Admin to display questions inside Exam and Assignment
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1  # Allows adding multiple questions at once
    fields = ('text', 'image', 'option_a_text', 'option_a_image', 
              'option_b_text', 'option_b_image', 'option_c_text', 'option_c_image', 
              'option_d_text', 'option_d_image', 'correct_answer')
    readonly_fields = ('display_image',)
    
    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100"/>', obj.image.url)
        return "No Image"
    display_image.short_description = "Question Image"

# Register Exam model with inline questions
@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'assigned_class', 'start_time', 'end_time', 'is_active')
    list_filter = ('teacher', 'assigned_class', 'is_active')
    search_fields = ('title', 'teacher__username')
    inlines = [QuestionInline]

# Register Assignment model with inline questions
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'assigned_class', 'due_date', 'is_active')
    list_filter = ('teacher', 'assigned_class', 'is_active')
    search_fields = ('title', 'teacher__username')
    inlines = [QuestionInline]

# Register Question model separately (optional)
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'exam', 'assignment', 'created_by', 'correct_answer')
    list_filter = ('exam', 'assignment', 'created_by')
    search_fields = ('text', 'created_by__username')

# Student Exam Record (read-only responses)
@admin.register(StudentExamRecord)
class StudentExamRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'score', 'submitted_at', 'is_submitted')
    list_filter = ('exam', 'is_submitted')
    search_fields = ('student__username', 'exam__title')
    readonly_fields = ('responses', 'score', 'submitted_at')

# Student Assignment Record (read-only responses)
@admin.register(StudentAssignmentRecord)
class StudentAssignmentRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'score', 'submitted_at', 'is_submitted')
    list_filter = ('assignment', 'is_submitted')
    search_fields = ('student__username', 'assignment__title')
    readonly_fields = ('responses', 'score', 'submitted_at')
