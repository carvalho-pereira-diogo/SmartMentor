from django import forms
from .models import Profile, Student, Course, LearningPath, Quiz, Tutor, Teacher

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = '__all__'
        
class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'
        
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = '__all__'
        
class LearningPathForm(forms.ModelForm):
    class Meta:
        model = LearningPath
        fields = '__all__'
        
class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = '__all__'
        
class TutorForm(forms.ModelForm):
    class Meta:
        model = Tutor
        fields = '__all__'
        
class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = '__all__'
        
class UploadFileForm(forms.Form):
    file = forms.FileField()