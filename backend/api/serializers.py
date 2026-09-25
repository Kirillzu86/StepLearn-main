# AI-GENERATED: Antigravity
import base64
import binascii
import random
import string

from rest_framework import serializers

from .models import (
    Answer,
    Course,
    CourseBlock,
    Enrollment,
    Exam,
    ExamAttempt,
    GroupCourse,
    GroupLessonAccess,
    Lesson,
    Question,
    StudentLessonProgress,
    StudyGroup,
    User,
)


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    is_teacher_or_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'name', 'first_name', 'last_name', 'email',
            'avatar_url', 'role', 'is_teacher_or_admin', 'is_staff', 'last_activity'
        ]


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(max_length=150, required=False, default='')
    last_name = serializers.CharField(max_length=150, required=False, default='')
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default='student', required=False)

    def validate_username(self, value):
        value = value.strip()
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Пользователь с таким именем уже существует')
        return value

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует')
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    login = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        login = attrs['login'].strip()
        password = attrs['password']
        user = User.objects.filter(email__iexact=login).first() or User.objects.filter(username__iexact=login).first()
        if not user or not user.check_password(password) or not user.is_active:
            raise serializers.ValidationError('Неверный логин или пароль')
        attrs['user'] = user
        return attrs


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'avatar_url', 'role']
        extra_kwargs = {
            'username': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'email': {'required': False},
            'avatar_url': {'required': False, 'allow_null': True},
            'role': {'required': False},
        }

    def validate_username(self, value):
        value = value.strip()
        qs = User.objects.filter(username__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Пользователь с таким именем уже существует')
        return value

    def validate_email(self, value):
        value = value.strip().lower()
        qs = User.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует')
        return value

    def validate_avatar_url(self, value):
        if not value:
            return value
        if isinstance(value, str) and value.startswith('data:') and ';base64,' in value:
            try:
                decoded = base64.b64decode(value.split(',', 1)[1], validate=True)
            except (IndexError, binascii.Error):
                raise serializers.ValidationError('Неверный формат изображения')
            if len(decoded) > 5 * 1024 * 1024:
                raise serializers.ValidationError('Размер аватара не должен превышать 5MB')
        return value


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text', 'is_correct']


class StudentAnswerSerializer(serializers.ModelSerializer):
    """Скрывает правильный ответ для студента во время тестирования"""
    class Meta:
        model = Answer
        fields = ['id', 'text']


class AnswerInputSerializer(serializers.Serializer):
    text = serializers.CharField()
    is_correct = serializers.BooleanField(default=False)


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'answers', 'lesson_id', 'exam_id']


class StudentQuestionSerializer(serializers.ModelSerializer):
    answers = StudentAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'answers']


class QuestionInputSerializer(serializers.Serializer):
    text = serializers.CharField()
    lesson_id = serializers.IntegerField(required=False, allow_null=True)
    exam_id = serializers.IntegerField(required=False, allow_null=True)
    answers = AnswerInputSerializer(many=True, required=False, default=list)


class ExamSerializer(serializers.ModelSerializer):
    questions_count = serializers.IntegerField(source='questions.count', read_only=True)
    block_title = serializers.CharField(source='block.title', read_only=True, default='')

    class Meta:
        model = Exam
        fields = [
            'id', 'course_id', 'block_id', 'block_title', 'title',
            'description', 'passing_score', 'max_attempts', 'questions_count', 'created_at'
        ]


class ExamDetailSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()
    block_title = serializers.CharField(source='block.title', read_only=True, default='')

    class Meta:
        model = Exam
        fields = [
            'id', 'course_id', 'block_id', 'block_title', 'title',
            'description', 'passing_score', 'max_attempts', 'questions', 'created_at'
        ]

    def get_questions(self, obj):
        request = self.context.get('request')
        is_teacher = request and request.user.is_authenticated and (request.user.is_teacher_or_admin)
        if is_teacher:
            return QuestionSerializer(obj.questions.all(), many=True).data
        return StudentQuestionSerializer(obj.questions.all(), many=True).data


class ExamAttemptSerializer(serializers.ModelSerializer):
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = ExamAttempt
        fields = ['id', 'user_id', 'user_name', 'exam_id', 'exam_title', 'score', 'passed', 'completed_at']


class LessonSerializer(serializers.ModelSerializer):
    course_id = serializers.IntegerField(source='course.id', read_only=True)
    block_title = serializers.CharField(source='block.title', read_only=True, default=None)
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = [
            'id', 'course_id', 'block_id', 'block_title', 'title', 'description',
            'content', 'lesson_type', 'is_mandatory', 'order', 'questions', 'created_at'
        ]


class CourseBlockSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    exam = ExamSerializer(read_only=True)
    lessons_count = serializers.IntegerField(source='lessons.count', read_only=True)

    class Meta:
        model = CourseBlock
        fields = ['id', 'course_id', 'title', 'description', 'order', 'lessons_count', 'lessons', 'exam', 'created_at']


class CourseSerializer(serializers.ModelSerializer):
    author_id = serializers.IntegerField(source='author.id', read_only=True, allow_null=True)
    author_name = serializers.CharField(source='author.name', read_only=True, default='')
    lessons_count = serializers.IntegerField(source='lessons.count', read_only=True)
    blocks_count = serializers.IntegerField(source='blocks.count', read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'price', 'rating', 'category', 'level',
            'status', 'cover_image', 'author_id', 'author_name', 'content', 'course_type',
            'blocks_count', 'lessons_count', 'created_at'
        ]


class CourseWithDetailsSerializer(serializers.ModelSerializer):
    blocks = CourseBlockSerializer(many=True, read_only=True)
    lessons = LessonSerializer(many=True, read_only=True)
    author_id = serializers.IntegerField(source='author.id', read_only=True, allow_null=True)
    author_name = serializers.CharField(source='author.name', read_only=True, default='')

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'price', 'rating', 'category', 'level',
            'status', 'cover_image', 'author_id', 'author_name', 'content', 'course_type',
            'blocks', 'lessons'
        ]


class CourseCreateSerializer(serializers.ModelSerializer):
    author_id = serializers.IntegerField(required=False, allow_null=True)
    category = serializers.CharField(required=False, default='Программирование')
    level = serializers.CharField(required=False, default='beginner')
    status = serializers.CharField(required=False, default='published')
    cover_image = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'price', 'author_id', 'category',
            'level', 'status', 'cover_image', 'content', 'course_type'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        author_id = validated_data.pop('author_id', None)
        if author_id:
            validated_data['author'] = User.objects.filter(pk=author_id).first()
        return Course.objects.create(**validated_data)


class QuickCreateStudentSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    group_id = serializers.IntegerField(required=False, allow_null=True)

    def create(self, validated_data):
        first_name = validated_data['first_name'].strip()
        last_name = validated_data['last_name'].strip()
        group_id = validated_data.get('group_id')

        # Генерируем уникальный логин student_XXXX
        for _ in range(100):
            num = random.randint(1000, 9999)
            username = f'student_{num}'
            if not User.objects.filter(username=username).exists():
                break
        else:
            username = f'student_{random.randint(10000, 99999)}'

        # Генерируем читаемый надежный пароль
        chars = string.ascii_letters + string.digits
        password = ''.join(random.choices(chars, k=8))
        email = f'{username}@steplearn.local'

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='student',
        )

        group = None
        if group_id:
            group = StudyGroup.objects.filter(pk=group_id).first()
            if group:
                group.students.add(user)

        return {
            'user': UserSerializer(user).data,
            'username': username,
            'password': password,
            'first_name': first_name,
            'last_name': last_name,
            'group_id': group.id if group else None,
            'group_name': group.name if group else None,
        }


class EnrollmentProgressSerializer(serializers.Serializer):
    currentIndex = serializers.IntegerField(required=False)
    current_index = serializers.IntegerField(required=False)
    progress_percentage = serializers.IntegerField(required=False)
    correctAnswers = serializers.IntegerField(required=False)
    correct_answers = serializers.IntegerField(required=False)
    completed_lessons = serializers.IntegerField(required=False)


class GroupLessonAccessSerializer(serializers.ModelSerializer):
    lesson_id = serializers.IntegerField(source='lesson.id', read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    lesson_order = serializers.IntegerField(source='lesson.order', read_only=True)

    class Meta:
        model = GroupLessonAccess
        fields = [
            'id', 'lesson_id', 'lesson_title', 'lesson_order',
            'is_unlocked', 'unlocked_at', 'auto_unlock_when_all_pass'
        ]


class StudyGroupSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    teacher_id = serializers.IntegerField(source='teacher.id', read_only=True)
    students_count = serializers.IntegerField(source='students.count', read_only=True)
    students = UserSerializer(many=True, read_only=True)
    courses = serializers.SerializerMethodField()

    class Meta:
        model = StudyGroup
        fields = [
            'id', 'name', 'description', 'code', 'teacher_id', 'teacher_name',
            'students_count', 'students', 'courses', 'created_at'
        ]

    def get_courses(self, obj):
        return [
            {
                'id': gc.course.id,
                'title': gc.course.title,
                'assigned_at': gc.assigned_at,
                'lessons_count': gc.course.lessons.count()
            }
            for gc in obj.group_courses.select_related('course').all()
        ]
