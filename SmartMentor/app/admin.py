from django.contrib import admin
from django.utils.html import format_html, mark_safe
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
    list_display = ('name', 'teacher', 'pdf_link')

    def pdf_link(self, obj):
        links = []
        for pdf in obj.pdfs.all():
            links.append(format_html('<a href="{0}">PDF</a>', pdf.file.url))
        return mark_safe("<br>".join(links))
    pdf_link.short_description = 'PDF Link'

admin.site.register(Course, CourseAdmin)

admin.site.register(LearningPath)

class QuizAdmin(admin.ModelAdmin):
    list_display = ('name',)

    search_fields = ('name',)

admin.site.register(Quiz, QuizAdmin)
admin.site.register(QuizEnrollment)
admin.site.register(QuizScore)

class PDFAdmin(admin.ModelAdmin):
    list_display = ('file', 'uploaded_by')

    search_fields = ('file', 'uploaded_by')

admin.site.register(PDF, PDFAdmin)

