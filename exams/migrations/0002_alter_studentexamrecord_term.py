# Generated by Django 4.2.16 on 2025-04-10 14:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academic_main', '0001_initial'),
        ('exams', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentexamrecord',
            name='term',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='exam_records', to='academic_main.term'),
        ),
    ]
