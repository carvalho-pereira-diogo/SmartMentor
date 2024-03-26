from django.contrib import admin
from django.utils.html import format_html
from .models import Profile, Student, Teacher

class StudentAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'level')

    # Using a method to safely access the username
    def get_username(self, obj):
        return obj.profile.user.username if obj.profile and obj.profile.user else 'No User'
    get_username.short_description = 'Username'  # Column header

    search_fields = ('profile__user__username', 'level')

class TeacherAdmin(admin.ModelAdmin):
    list_display = ('get_username',)

    def get_username(self, obj):
        return obj.profile.user.username if obj.profile and obj.profile.user else 'No User'
    get_username.short_description = 'Username'

    search_fields = ('profile__user__username',)

admin.site.register(Profile)
admin.site.register(Student, StudentAdmin)
admin.site.register(Teacher, TeacherAdmin)
