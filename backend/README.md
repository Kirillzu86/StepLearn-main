# StepLearn — Backend (Django REST Framework)

Полноценный бэкенд платформы онлайн-обучения StepLearn на Python 3, Django и Django REST Framework (DRF), совместимый с React/Vite фронтендом и Nginx/Docker/Coolify инфраструктурой.

---

## Что где находится (Архитектура проекта)

```text
backend/
├── Dockerfile                  # Multi-stage сборка Docker-образа для бэкенда
├── entrypoint.sh               # Скрипт ожидания PostgreSQL, авто-миграций и seed_demo
├── manage.py                   # Главная точка входа для команд управления Django
├── requirements.txt            # Зависимости Python (Django, DRF, psycopg, cors-headers, gunicorn и др.)
├── .env.example                # Пример переменных окружения
│
├── steplearn/                  # Главный конфигурационный пакет Django
│   ├── settings.py             # Настройки проекта (БД, CORS, ALLOWED_HOSTS, DRF, custom exception handler)
│   ├── urls.py                 # Корневые маршруты (включает api.urls как с префиксом /api/, так и без)
│   ├── asgi.py                 # ASGI-интерфейс для асинхронных серверов
│   └── wsgi.py                 # WSGI-интерфейс для Gunicorn / production
│
└── api/                        # Основное приложение платформы
    ├── models.py               # Модели БД: User, Course, Question, Answer, Enrollment (с прогрессом)
    ├── serializers.py          # DRF-сериализаторы (валидация, хеширование, вложенные вопросы/ответы)
    ├── views.py                # Контроллеры API (аутентификация, каталог, прогресс, профиль)
    ├── urls.py                 # Маршрутизация эндпоинтов API
    ├── exceptions.py           # Кастомный обработчик ошибок (гарантирует наличие поля detail для фронтенда)
    ├── migrations/             # Миграции схемы базы данных
    │   └── 0001_initial.py     # Начальная миграция всех моделей
    ├── management/
    │   └── commands/
    │       └── seed_demo.py    # Команда наполнения демо-данными (курсы, вопросы, студент, админ)
    └── tests/
        └── test_api.py         # Набор автотестов для всех сценариев API
```

---

## Модели базы данных (`api/models.py`)

1. **`User` (кастомная модель на базе `AbstractUser`)**:
   - `username`, `email` (уникальный), `password` (хешируется PBKDF2/SHA256).
   - `avatar_url` (ссылка или base64 аватарка до 5MB).
   - Свойство `.name` — возвращает имя или логин (для обратной совместимости с React фронтендом).
2. **`Course`**:
   - `title`, `description`, `price` (0 = бесплатно, >0 = платно).
   - `rating` (по умолчанию 4.5+).
   - `author` (связь с `User`, создавшим курс).
   - `students` (`ManyToMany` через таблицу `Enrollment`).
   - `created_at` (дата создания).
3. **`Question`**:
   - `course` (`ForeignKey` на курс).
   - `text` (текст вопроса теста).
4. **`Answer`**:
   - `question` (`ForeignKey` на вопрос).
   - `text` (текст ответа).
   - `is_correct` (булевый флаг правильности ответа).
5. **`Enrollment` (запись на курс и отслеживание прогресса)**:
   - `user`, `course` (уникальная пара `user + course`).
   - `current_index` (номер текущего вопроса).
   - `progress_percentage` (процент прохождения 0-100%).
   - `completed_lessons` (количество пройденных уроков/вопросов).
   - `correct_answers` (количество верных ответов).
   - `created_at`, `updated_at`.

---

## Доступные маршруты API

Все маршруты доступны **как с префиксом `/api/`, так и без него** (например, `/auth/login` и `/api/auth/login`), что предотвращает ошибки при проксировании через Nginx и при локальном Vite dev-сервере.

### Аутентификация и пользователи
| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/auth/register` (или `/api/auth/register`) | Регистрация (`username`, `email`, `password`) |
| `POST` | `/auth/login` (или `/api/auth/login`) | Вход по `login` (username или email) и `password` |
| `GET` | `/users` (или `/api/users`) | Список всех пользователей |
| `GET` | `/v1/users/{id}` (или `/api/v1/users/{id}`) | Данные пользователя |
| `PUT`/`PATCH` | `/v1/users/{id}` (или `/api/v1/users/{id}`) | Обновление профиля (`username`, `email`, `avatar_url`) |

### Курсы и каталог
| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/v1/courses` (или `/api/v1/courses`) | Каталог курсов (поддерживает поиск `?q=...`) |
| `POST` | `/v1/courses` (или `/api/v1/courses`, `/v1/courses/create`) | Создание курса с вложенными вопросами и ответами |
| `GET` | `/v1/course/{id}` (или `/api/v1/course/{id}`) | Детальная страница курса со списком вопросов и ответов |

### Запись на курс и прогресс обучения
| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/v1/enroll` (или `/api/v1/enroll`) | Запись пользователя на курс (`user_id`, `course_id`) |
| `GET` | `/v1/users/{id}/courses` (или `/api/v1/users/{id}/courses`) | Список курсов пользователя с его актуальным прогрессом |
| `POST` | `/v1/users/{id}/courses/{course_id}/progress` | Сохранение прогресса (`currentIndex`, `progress_percentage`, `correctAnswers`) |
| `GET` | `/v1/users/{id}/courses/{course_id}/progress` | Получение текущего прогресса по курсу |

---

## Формат ошибок

Все ошибки API (400, 404, 500) автоматически форматируются с гарантированным полем **`detail`** (через `api/exceptions.py`), что позволяет фронтенду корректно выводить понятный текст ошибки пользователю:
```json
{
  "detail": "Неверный логин или пароль"
}
```

---

## Локальный запуск (без Docker)

1. Активируйте виртуальное окружение:
   ```bash
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # или Linux/macOS:
   source .venv/bin/activate
   ```
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Создайте `.env` (или скопируйте `.env.example`):
   ```bash
   copy .env.example .env
   ```
4. Примените миграции:
   ```bash
   python manage.py migrate
   ```
5. Заполните базу демо-данными:
   ```bash
   python manage.py seed_demo
   ```
   *Создаются тестовые аккаунты:*
   - Студент: `student` / `secret123`
   - Администратор: `admin` / `admin123`
6. Запустите тесты:
   ```bash
   python manage.py test api --noinput
   ```
7. Запустите сервер разработки:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

---

## Запуск через Docker Compose

В корне проекта:
```bash
docker compose up --build -d
```
Бэкенд автоматически:
1. Дождется запуска PostgreSQL.
2. Применит все миграции.
3. Заполнит базу демо-данными `seed_demo`.
4. Запустит сервер на порту `8000`.
