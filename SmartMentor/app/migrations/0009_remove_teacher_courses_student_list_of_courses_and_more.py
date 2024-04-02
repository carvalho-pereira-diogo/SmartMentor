# Generated by Django 5.0.3 on 2024-04-01 16:37

import app.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_student_list_of_courses_alter_learningpath_teacher_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='teacher',
            name='courses',
        ),
        migrations.AddField(
            model_name='student',
            name='list_of_courses',
            field=models.ManyToManyField(related_name='students', through='app.LearningPath', to='app.course'),
        ),
        migrations.AddField(
            model_name='teacher',
            name='new_courses',
            field=models.ManyToManyField(related_name='new_teachers', to='app.course'),
        ),
        migrations.AlterField(
            model_name='learningpath',
            name='teacher',
            field=models.ForeignKey(default=app.models.get_default_teacher, on_delete=django.db.models.deletion.CASCADE, to='app.teacher'),
        ),
    ]
