# Generated by Django 5.2.1 on 2025-05-18 23:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academic_main', '0004_schoolpaymentinfo'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolpaymentinfo',
            name='bank_code',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='schoolpaymentinfo',
            name='flutterwave_subaccount_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='schoolpaymentinfo',
            name='split_percentage',
            field=models.PositiveIntegerField(default=98),
        ),
        migrations.AlterField(
            model_name='schoolpaymentinfo',
            name='provider',
            field=models.CharField(choices=[('flutterwave', 'Flutterwave'), ('bank_transfer', 'Bank Transfer')], max_length=20),
        ),
    ]
