# Generated by Django 5.0.3 on 2024-04-02 01:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_remove_teacher_courses_student_list_of_courses_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='progress',
            field=models.IntegerField(default=0),
        ),
    ]
