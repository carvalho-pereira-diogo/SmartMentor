from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=10, default='user')
    fname = models.CharField(max_length=50, default='fname')
    lname = models.CharField(max_length=50, default='lname')
    email = models.EmailField(max_length=50, default='email')
    role = models.CharField(max_length=10, default='student')
    date_created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.username
    
class Student(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    level = models.CharField(max_length=10, default='beginner')
    list_of_courses = models.ManyToManyField('Course', related_name='students', through='LearningPath')

    def __str__(self):
        return self.profile.username
    
class PDF(models.Model):
    file = models.FileField(upload_to='pdfs/')
    uploaded_by = models.ForeignKey('Teacher', on_delete=models.CASCADE)

    def __str__(self):
        return self.file.name

    
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, default=1)
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    pdfs = models.ManyToManyField(PDF, related_name='teachers')
    courses_list = models.ManyToManyField('Course', related_name='courses', through='LearningPath')

    def __str__(self):
        return self.profile.username

    @staticmethod
    def get_default_teacher():
        default_teacher = Teacher.objects.first()
        return default_teacher.id if default_teacher else None
    
class Course(models.Model):
    name = models.CharField(max_length=50, default='course')
    description = models.CharField(max_length=200, default='Default description')
    progress = models.IntegerField(default=0)
    pdfs = models.ForeignKey(PDF, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    time_created = models.DateTimeField(auto_now_add=True, null=True)
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, related_name='courses', default=Teacher.get_default_teacher)

    def __str__(self):
        return self.name
    
class SomeModel(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, default=Teacher.get_default_teacher, null=True)

class LearningPath(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, default=Teacher.get_default_teacher, null=True)
    
    def __str__(self):
        return f'{self.student.profile.username} - {self.course.name}'

from django.db import models

class Quiz(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=200, default='Default description')

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=512)

class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=512)
    is_correct = models.BooleanField(default=False)
    
    
    
# Create me a model for my chatbot and view called Tutor

class Tutor(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=200, default='Default description')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='tutors')
    
    def __str__(self):
        return self.name
