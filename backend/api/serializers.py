import base64
import binascii

from rest_framework import serializers

from .models import Answer, Course, Enrollment, Question, User


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'email', 'avatar_url']


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)

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
        fields = ['username', 'email', 'avatar_url']
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
            'avatar_url': {'required': False, 'allow_null': True},
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


class AnswerInputSerializer(serializers.Serializer):
    text = serializers.CharField()
    is_correct = serializers.BooleanField(default=False)


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'answers']


class QuestionInputSerializer(serializers.Serializer):
    text = serializers.CharField()
    answers = AnswerInputSerializer(many=True, required=False, default=list)


class CourseSerializer(serializers.ModelSerializer):
    author_id = serializers.IntegerField(source='author.id', read_only=True, allow_null=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'price', 'rating', 'author_id', 'content', 'course_type', 'created_at']


class CourseWithQuestionsSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    author_id = serializers.IntegerField(source='author.id', read_only=True, allow_null=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'price', 'rating', 'author_id', 'content', 'course_type', 'questions']


class CourseCreateSerializer(serializers.ModelSerializer):
    questions = QuestionInputSerializer(many=True, required=False, default=list)
    author_id = serializers.IntegerField(required=False, allow_null=True)
    content = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    course_type = serializers.CharField(required=False, default='quiz')

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'price', 'author_id', 'content', 'course_type', 'questions']
        read_only_fields = ['id']

    def create(self, validated_data):
        questions = validated_data.pop('questions', [])
        author_id = validated_data.pop('author_id', None)
        if author_id:
            validated_data['author'] = User.objects.filter(pk=author_id).first()

        if validated_data.get('content') and not questions:
            validated_data['course_type'] = 'text'

        course = Course.objects.create(**validated_data)
        for q_data in questions:
            answers = q_data.pop('answers', [])
            question = Question.objects.create(course=course, **q_data)
            Answer.objects.bulk_create([
                Answer(question=question, **answer_data) for answer_data in answers
            ])
        return course


class EnrollmentProgressSerializer(serializers.Serializer):
    currentIndex = serializers.IntegerField(required=False)
    current_index = serializers.IntegerField(required=False)
    progress_percentage = serializers.IntegerField(required=False)
    correctAnswers = serializers.IntegerField(required=False)
    correct_answers = serializers.IntegerField(required=False)
    completed_lessons = serializers.IntegerField(required=False)
