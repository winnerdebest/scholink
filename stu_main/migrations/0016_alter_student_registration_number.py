# Generated by Django 5.2.1 on 2025-05-16 17:31

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stu_main', '0015_auto_20250516_1826'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='registration_number',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
