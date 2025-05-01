from django.contrib import admin
from .models import *


admin.site.register(Term)
admin.site.register(ActiveTerm)

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'principal', 'email')