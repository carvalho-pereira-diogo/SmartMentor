from app.models import *
from django.db import connection
from pprint import pprint

def run ():
    # Get the teachers with the different courses
    #Add courses to the teachers

# Get the first teacher
    teacher = Teacher.objects.first()
    # Get the first course
    course = Course.objects.first()
    # Add the course to the teacher
    teacher.courses.add(course)
    # Get the second course
    course2 = Course.objects.all()[1]
    # Add the second course to the teacher
    teacher.courses.add(course2)
    
    
    teachers = Teacher.objects.all()
    for teacher in teachers:
        print(f'{teacher.profile.username} - {teacher.courses.all()}')
        
