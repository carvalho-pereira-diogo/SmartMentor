from django.db import models
from django.contrib.auth.models import User

#Create me different models:
# We have a model Profile where Student is an extension of Profile:
# In Profile we have:
# username, fname, lname, email, role, password, date_created
# In Student we have:
# level
# Now we also have Course which is a model who is an ai agent who takes a pdf and generates a course
# Course and student are related by a many to many relationship
# There's an association class between Course and Student called learning path
# We also have a Quiz model which is a model that has a many to many relationship with Student
# We also have a tutor which can help a student out which is an ai agent 
# In the end we have a model called Teacher which is a normal profile and has only the ability to upload the pdf to the different Courses and Quizes and tutor

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
    
    def __str__(self):
        return self.profile.username
    
class Course(models.Model):
    name = models.CharField(max_length=50, default='course')
    pdf = models.FileField(upload_to='courses/', default='courses/default.pdf')
    pdf_name = models.CharField(max_length=50, default='pdf')
    students = models.ManyToManyField(Student, through='LearningPath', related_name='courses')
    time_created = models.DateTimeField(auto_now_add=True, null=True)
    Teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, null=True)
    
    def __str__(self):
        return self.name
    
class LearningPath(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    
    def __str__(self):
        return f'{self.student.profile.username} - {self.course.name}'
    
class Quiz(models.Model):
    name = models.CharField(max_length=50)
    students = models.ManyToManyField(Student)
    
    def __str__(self):
        return self.name
    
class Tutor(models.Model):
    name = models.CharField(max_length=50)
    pdf = models.FileField(upload_to='tutors/')
    
    def __str__(self):
        return self.name
    
class Teacher(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.profile.username
    