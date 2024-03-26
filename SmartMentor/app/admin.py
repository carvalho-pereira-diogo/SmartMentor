from django.contrib import admin
from django.utils.html import format_html
from .models import *

admin.site.register(Profile)

class StudentAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'level')

    # Using a method to safely access the username
    def get_username(self, obj):
        return obj.profile.user.username if obj.profile and obj.profile.user else 'No User'
    get_username.short_description = 'Username'  # Column header

    search_fields = ('profile__user__username', 'level')
    
admin.site.register(Student, StudentAdmin)

class TeacherAdmin(admin.ModelAdmin):
    list_display = ('get_username',)

    def get_username(self, obj):
        return obj.profile.user.username if obj.profile and obj.profile.user else 'No User'
    get_username.short_description = 'Username'

    search_fields = ('profile__user__username',)

admin.site.register(Teacher, TeacherAdmin)

class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'pdf_link')

    def pdf_link(self, obj):
        return format_html('<a href="{0}">PDF</a>', obj.pdf.url)
    pdf_link.short_description = 'PDF'

    search_fields = ('name',)
    
admin.site.register(Course, CourseAdmin)

class LearningPathAdmin(admin.ModelAdmin):
    list_display = ('student', 'course')

    search_fields = ('student__profile__user__username', 'course__name')
    
admin.site.register(LearningPath, LearningPathAdmin)

# provided with a pdf from teacher and can be taken by the student
class TutorAdmin(admin.ModelAdmin):
    list_display = ('name', 'pdf_link')

    def pdf_link(self, obj):
        return format_html('<a href="{0}">PDF</a>', obj.pdf.url)
    pdf_link.short_description = 'PDF'

    search_fields = ('name',)
    
admin.site.register(Tutor, TutorAdmin)

class QuizAdmin(admin.ModelAdmin):
    list_display = ('name',)

    search_fields = ('name',)
    
admin.site.register(Quiz, QuizAdmin)

