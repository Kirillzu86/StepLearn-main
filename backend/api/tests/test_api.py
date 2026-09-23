from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from api.models import Answer, Course, Enrollment, Question


class StepLearnAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='student', email='student@example.com', password='secret123'
        )
        self.course = Course.objects.create(title='Python', description='Basics', price=0)
        question = Question.objects.create(course=self.course, text='2 + 2 = ?')
        Answer.objects.create(question=question, text='4', is_correct=True)
        Answer.objects.create(question=question, text='5', is_correct=False)

    def test_register_hashes_password(self):
        response = self.client.post('/api/auth/register', {
            'username': 'newuser', 'email': 'new@example.com', 'password': 'secret123'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        user = get_user_model().objects.get(username='newuser')
        self.assertNotEqual(user.password, 'secret123')
        self.assertTrue(user.check_password('secret123'))
        self.assertIn('name', response.data)

    def test_register_duplicate_returns_detail(self):
        response = self.client.post('/auth/register', {
            'username': 'student', 'email': 'other@example.com', 'password': 'secret123'
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('detail', response.data)

    def test_login_by_username_and_email(self):
        # Username
        resp1 = self.client.post('/auth/login', {
            'login': 'student', 'password': 'secret123'
        }, format='json')
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp1.data['username'], 'student')

        # Email
        resp2 = self.client.post('/api/auth/login', {
            'login': 'student@example.com', 'password': 'secret123'
        }, format='json')
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.data['email'], 'student@example.com')

    def test_login_invalid_password_returns_detail(self):
        response = self.client.post('/auth/login', {
            'login': 'student', 'password': 'wrongpassword'
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('detail', response.data)

    def test_users_list_and_detail(self):
        # GET /users without /api/
        resp1 = self.client.get('/users')
        self.assertEqual(resp1.status_code, 200)
        self.assertTrue(len(resp1.data) >= 1)

        # GET /v1/users/{id}
        resp2 = self.client.get(f'/v1/users/{self.user.id}')
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.data['username'], 'student')

        # PUT /api/v1/users/{id}
        resp3 = self.client.put(f'/api/v1/users/{self.user.id}', {
            'email': 'updated@example.com'
        }, format='json')
        self.assertEqual(resp3.status_code, 200)
        self.assertEqual(resp3.data['email'], 'updated@example.com')

    def test_course_list_and_catalog_fields(self):
        Enrollment.objects.create(user=self.user, course=self.course)

        # Free course
        response = self.client.get('/api/v1/courses')
        self.assertEqual(response.status_code, 200)
        item = [c for c in response.data if c['id'] == self.course.id][0]
        self.assertEqual(item['students_count'], 1)
        self.assertEqual(item['price_status'], 'Free')
        self.assertEqual(item['total_lessons'], 1)
        self.assertIn('rating', item)

        # Paid course
        paid = Course.objects.create(title='Django Pro', description='Advanced', price=1500)
        resp_paid = self.client.get('/v1/courses')
        paid_item = [c for c in resp_paid.data if c['id'] == paid.id][0]
        self.assertEqual(paid_item['price_status'], 'Paid')

    def test_course_detail_contains_nested_answers(self):
        response = self.client.get(f'/api/v1/course/{self.course.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['questions']), 1)
        self.assertEqual(len(response.data['questions'][0]['answers']), 2)

    def test_course_create_with_questions(self):
        payload = {
            'title': 'New JavaScript Course',
            'description': 'JS from scratch',
            'price': 500,
            'author_id': self.user.id,
            'questions': [
                {
                    'text': 'What is typeof null?',
                    'answers': [
                        {'text': 'object', 'is_correct': True},
                        {'text': 'null', 'is_correct': False},
                    ]
                }
            ]
        }
        response = self.client.post('/api/v1/courses', payload, format='json')
        self.assertEqual(response.status_code, 200)
        new_course_id = response.data['id']

        detail_resp = self.client.get(f'/api/v1/course/{new_course_id}')
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(len(detail_resp.data['questions']), 1)
        self.assertEqual(len(detail_resp.data['questions'][0]['answers']), 2)

    def test_enroll_and_user_courses_progress(self):
        payload = {'user_id': self.user.id, 'course_id': self.course.id}
        first = self.client.post('/api/v1/enroll', payload, format='json')
        second = self.client.post('/v1/enroll', payload, format='json')
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(self.user.enrollments.count(), 1)

        # POST progress
        prog_resp = self.client.post(
            f'/api/v1/users/{self.user.id}/courses/{self.course.id}/progress',
            {'currentIndex': 1, 'progress_percentage': 100, 'correctAnswers': 1},
            format='json',
        )
        self.assertEqual(prog_resp.status_code, 200)
        self.assertEqual(prog_resp.data['progress_percentage'], 100)

        # GET progress
        get_prog = self.client.get(
            f'/v1/users/{self.user.id}/courses/{self.course.id}/progress'
        )
        self.assertEqual(get_prog.status_code, 200)
        self.assertEqual(get_prog.data['progress_percentage'], 100)

        # Check user courses reflects progress
        uc_resp = self.client.get(f'/api/v1/users/{self.user.id}/courses')
        self.assertEqual(uc_resp.status_code, 200)
        self.assertEqual(uc_resp.data[0]['progress_percentage'], 100)
        self.assertEqual(uc_resp.data[0]['price_status'], 'Enrolled')

    def test_create_and_get_markdown_course_without_questions(self):
        payload = {
            'title': 'Markdown Only Course',
            'description': 'Pure text guide without quiz',
            'price': 0,
            'course_type': 'text',
            'content': '# Introduction\n\nThis is a long markdown text.\n\n## Section 1\nDetails here.',
            'questions': []
        }
        create_resp = self.client.post('/api/v1/courses', payload, format='json')
        self.assertEqual(create_resp.status_code, 200)
        course_id = create_resp.data['id']
        self.assertEqual(create_resp.data['course_type'], 'text')

        # Get course detail
        detail_resp = self.client.get(f'/api/v1/course/{course_id}')
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(detail_resp.data['course_type'], 'text')
        self.assertIn('Introduction', detail_resp.data['content'])
        self.assertEqual(len(detail_resp.data['questions']), 0)

        # Get course in list - should have sections count as total_lessons
        list_resp = self.client.get('/api/v1/courses')
        self.assertEqual(list_resp.status_code, 200)
        item = [c for c in list_resp.data if c['id'] == course_id][0]
        self.assertTrue(item['total_lessons'] >= 1)
        self.assertTrue(item['has_content'])

