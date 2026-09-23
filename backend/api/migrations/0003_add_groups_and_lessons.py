# Generated manually for StudyGroup, Lesson, GroupAccess and Progress

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_course_content_course_course_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('student', 'Студент'), ('teacher', 'Преподаватель'), ('admin', 'Администратор')], default='student', max_length=20),
        ),
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('content', models.TextField(blank=True, default='')),
                ('order', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lessons', to='api.course')),
            ],
            options={
                'ordering': ['order', 'id'],
            },
        ),
        migrations.AddConstraint(
            model_name='lesson',
            constraint=models.UniqueConstraint(fields=('course', 'order'), name='unique_course_lesson_order'),
        ),
        migrations.AddField(
            model_name='question',
            name='lesson',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='questions', to='api.lesson'),
        ),
        migrations.CreateModel(
            name='StudyGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('description', models.TextField(blank=True, null=True)),
                ('code', models.CharField(db_index=True, max_length=20, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('students', models.ManyToManyField(blank=True, related_name='study_groups', to=settings.AUTH_USER_MODEL)),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teaching_groups', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='GroupCourse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_courses', to='api.course')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_courses', to='api.studygroup')),
            ],
            options={
                'ordering': ['-assigned_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='groupcourse',
            constraint=models.UniqueConstraint(fields=('group', 'course'), name='unique_group_course'),
        ),
        migrations.CreateModel(
            name='GroupLessonAccess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_unlocked', models.BooleanField(default=False)),
                ('unlocked_at', models.DateTimeField(blank=True, null=True)),
                ('auto_unlock_when_all_pass', models.BooleanField(default=True, help_text='Автоматически открыть этот урок, когда вся группа пройдет предыдущий')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lesson_accesses', to='api.studygroup')),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_accesses', to='api.lesson')),
            ],
            options={
                'ordering': ['lesson__order', 'id'],
            },
        ),
        migrations.AddConstraint(
            model_name='grouplessonaccess',
            constraint=models.UniqueConstraint(fields=('group', 'lesson'), name='unique_group_lesson_access'),
        ),
        migrations.CreateModel(
            name='StudentLessonProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_completed', models.BooleanField(default=False)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_progresses', to='api.lesson')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lesson_progresses', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-completed_at', 'id'],
            },
        ),
        migrations.AddConstraint(
            model_name='studentlessonprogress',
            constraint=models.UniqueConstraint(fields=('user', 'lesson'), name='unique_user_lesson_progress'),
        ),
    ]
