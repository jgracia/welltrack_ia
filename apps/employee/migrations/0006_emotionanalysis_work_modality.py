# Generated by Django 5.1 on 2024-09-18 21:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0005_emotionanalysis'),
    ]

    operations = [
        migrations.AddField(
            model_name='emotionanalysis',
            name='work_modality',
            field=models.CharField(choices=[('onsite', 'Onsite'), ('remote', 'Remote')], default='onsite', help_text='Work modality (onsite, remote)', max_length=10, verbose_name='Work modality'),
        ),
    ]
