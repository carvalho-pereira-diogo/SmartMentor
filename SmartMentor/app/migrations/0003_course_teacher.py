# Generated by Django 5.0.3 on 2024-03-26 22:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_course_pdf_name_course_time_created_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='Teacher',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='app.teacher'),
        ),
    ]
