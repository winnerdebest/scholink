# Generated by Django 5.2.1 on 2025-05-17 11:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stu_main', '0016_alter_student_registration_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='parents',
            field=models.ManyToManyField(blank=True, related_name='children', to='stu_main.parent'),
        ),
    ]
