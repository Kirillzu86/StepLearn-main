import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Студент'),
        ('teacher', 'Преподаватель'),
        ('admin', 'Администратор'),
    ]
    email = models.EmailField(unique=True)
    avatar_url = models.TextField(blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

    class Meta:
        ordering = ['id']

    @property
    def name(self):
        return self.get_full_name() or self.username

    @property
    def is_teacher_or_admin(self):
        return self.role in ['teacher', 'admin'] or self.is_staff or self.is_superuser

    def __str__(self):
        return self.username


class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.PositiveIntegerField(default=0)
    rating = models.FloatField(default=4.5)
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authored_courses',
    )
    students = models.ManyToManyField(
        User,
        through='Enrollment',
        related_name='enrolled_courses',
        blank=True,
    )
    content = models.TextField(blank=True, null=True)
    course_type = models.CharField(max_length=20, default='quiz')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, default='')
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']
        constraints = [
            models.UniqueConstraint(fields=['course', 'order'], name='unique_course_lesson_order'),
        ]

    def __str__(self):
        return f'{self.course.title} - #{self.order} {self.title}'


class Question(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='questions')
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name='questions')
    text = models.TextField()

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.text[:80]


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.text[:80]


class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    current_index = models.PositiveIntegerField(default=0)
    progress_percentage = models.PositiveIntegerField(default=0)
    completed_lessons = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'course'], name='unique_user_course'),
        ]
        ordering = ['id']

    def __str__(self):
        return f'{self.user} -> {self.course}'


class StudyGroup(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    code = models.CharField(max_length=20, unique=True, db_index=True)
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teaching_groups',
    )
    students = models.ManyToManyField(
        User,
        related_name='study_groups',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.code})'

    @classmethod
    def generate_code(cls):
        import random, string
        chars = string.ascii_uppercase + string.digits
        for _ in range(10):
            code = 'GRP-' + ''.join(random.choices(chars, k=5))
            if not cls.objects.filter(code=code).exists():
                return code
        return f'GRP-{uuid.uuid4().hex[:6].upper()}'


class GroupCourse(models.Model):
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='group_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='group_courses')
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-assigned_at']
        constraints = [
            models.UniqueConstraint(fields=['group', 'course'], name='unique_group_course'),
        ]

    def __str__(self):
        return f'{self.group.name} -> {self.course.title}'


class GroupLessonAccess(models.Model):
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='lesson_accesses')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='group_accesses')
    is_unlocked = models.BooleanField(default=False)
    unlocked_at = models.DateTimeField(null=True, blank=True)
    auto_unlock_when_all_pass = models.BooleanField(
        default=True,
        help_text='Автоматически открыть этот урок, когда вся группа пройдет предыдущий',
    )

    class Meta:
        ordering = ['lesson__order', 'id']
        constraints = [
            models.UniqueConstraint(fields=['group', 'lesson'], name='unique_group_lesson_access'),
        ]

    def __str__(self):
        status = 'OPEN' if self.is_unlocked else 'LOCKED'
        return f'[{status}] {self.group.name} - {self.lesson.title}'


class StudentLessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progresses')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='student_progresses')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-completed_at', 'id']
        constraints = [
            models.UniqueConstraint(fields=['user', 'lesson'], name='unique_user_lesson_progress'),
        ]

    def __str__(self):
        return f'{self.user.username} -> {self.lesson.title}: {"Done" if self.is_completed else "In progress"}'
