from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Answer,
    Course,
    Enrollment,
    GroupCourse,
    GroupLessonAccess,
    Lesson,
    Question,
    StudentLessonProgress,
    StudyGroup,
    User,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    fieldsets = UserAdmin.fieldsets + (
        ('StepLearn', {'fields': ('avatar_url', 'role')}),
    )


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ('order', 'title', 'description')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'price', 'rating')
    search_fields = ('title', 'description')
    inlines = [LessonInline, QuestionInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('id', 'course', 'order', 'title', 'created_at')
    list_filter = ('course',)
    search_fields = ('title', 'description', 'content')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'course', 'lesson', 'text')
    search_fields = ('text',)
    list_filter = ('course',)
    inlines = [AnswerInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'text', 'is_correct')
    list_filter = ('is_correct',)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'course', 'completed_lessons', 'progress_percentage', 'created_at')
    list_filter = ('course',)
    search_fields = ('user__username', 'user__email', 'course__title')


@admin.register(StudyGroup)
class StudyGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'teacher', 'created_at')
    search_fields = ('name', 'code', 'teacher__username')
    filter_horizontal = ('students',)


@admin.register(GroupCourse)
class GroupCourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'group', 'course', 'assigned_at')
    list_filter = ('group', 'course')


@admin.register(GroupLessonAccess)
class GroupLessonAccessAdmin(admin.ModelAdmin):
    list_display = ('id', 'group', 'lesson', 'is_unlocked', 'auto_unlock_when_all_pass', 'unlocked_at')
    list_filter = ('is_unlocked', 'auto_unlock_when_all_pass', 'group')


@admin.register(StudentLessonProgress)
class StudentLessonProgressAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'lesson', 'is_completed', 'completed_at')
    list_filter = ('is_completed', 'lesson__course')
    search_fields = ('user__username', 'lesson__title')
