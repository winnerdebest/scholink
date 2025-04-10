# Generated by Django 4.2.16 on 2025-04-09 16:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('exams', '0003_remove_assignment_assigned_class_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentassignmentrecord',
            name='student',
            field=models.ForeignKey(limit_choices_to={'user_type': 'student'}, on_delete=django.db.models.deletion.CASCADE, related_name='assignment_records', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='studentexamrecord',
            name='student',
            field=models.ForeignKey(limit_choices_to={'user_type': 'student'}, on_delete=django.db.models.deletion.CASCADE, related_name='exam_records', to=settings.AUTH_USER_MODEL),
        ),
    ]
