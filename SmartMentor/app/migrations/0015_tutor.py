# Generated by Django 5.0.3 on 2024-04-05 13:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_option_question_somemodel_delete_tutor_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tutor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.CharField(default='Default description', max_length=200)),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tutors', to='app.teacher')),
            ],
        ),
    ]
