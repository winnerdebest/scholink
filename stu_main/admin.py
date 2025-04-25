from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Class, Guardian, Student, StudentPost,
    Subject, ClassSubject
)

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'user_type', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('user_type', 'is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type', 'is_staff', 'is_active')
        }),
    )
    search_fields = ('username', 'email')
    ordering = ('username',)

class ClassAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class GuardianAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'email')
    search_fields = ('name', 'email', 'phone_number')

class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_class', 'phone_number')
    search_fields = ('user__username', 'phone_number')
    list_filter = ('student_class',)

class StudentPostAdmin(admin.ModelAdmin):
    list_display = ('student', 'created_at', 'total_likes',)
    search_fields = ('student__user__username', 'content')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')

class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ('subject', 'school_class', 'teacher')
    list_filter = ('school_class', 'subject')
    search_fields = ('subject__name', 'school_class__name', 'teacher__username')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Class, ClassAdmin)
admin.site.register(Guardian, GuardianAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(StudentPost, StudentPostAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(ClassSubject, ClassSubjectAdmin)
