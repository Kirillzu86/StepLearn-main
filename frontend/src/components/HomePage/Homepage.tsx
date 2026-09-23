import React, { useState, useEffect } from "react";
import axios from "axios";
import { API_URL } from "../../api/api";
import { Link, useLocation, useNavigate } from "react-router-dom";
import Header from "../Header/Header"; // <-- ИМПОРТ HEADER
import "./StyleHomePage.css"; 
import '../Sidebar/StyleSidebar.css'; 
import Sidebar from "../Sidebar/sidebar";
// --- Интерфейсы (должны совпадать с models.py в FastAPI) ---
interface Course {
    id: number;
    title: string;
    description: string;
    rating: number;
    price?: number;
    students_count: number;
    price_status: string;
    total_lessons: number;
    completed_lessons: number;
    progress_percentage: number;
}

// --- Вспомогательные Компоненты ---

// 1. Карточка Курса
interface CourseCardProps {
    course: Course;
}

function CourseCard({ course }: CourseCardProps) {
  return (
    // Используем Link для перехода на страницу CourseDetail
    <Link to={`/course/${course.id}`} className="course-card">
      <h3 className="card-title">{course.title}</h3>
      <p className="card-description">{course.description}</p>

      <div className="card-meta">
        <span>⭐ {course.rating.toFixed(1)}</span>
        <span>👤 {course.students_count.toLocaleString()}</span>
        {course.price_status === 'Enrolled' ? (
            <span className="price-status enrolled">Вы записаны</span>
        ) : (
            <span className={`price-status ${course.price && course.price > 0 ? 'paid' : 'free'}`}>
                {course.price && course.price > 0 ? `${course.price} ₽` : 'Бесплатно'}
            </span>
        )}
      </div>
      {/* Возвращаем прогресс-бар с проверкой на наличие данных */}
      {typeof course.progress_percentage === 'number' && (
        <>
          <div className="card-progress">
            <div style={{ width: `${course.progress_percentage}%` }} className="progress-bar"></div>
          </div>
          <div className="progress-text">
            {course.progress_percentage.toFixed(0)}% пройдено
          </div>
        </>
      )}
    </Link>
  );
}

// 2. Блок "Серия и ежедневная цель"
function StreakAndDailyBox() {
  return (
    <div className="streak-box">
      <div className="streak-header">
        <span className="streak-icon">🔥</span>
        <span className="streak-title">0 дней без перерыва</span>
      </div>
      <p className="streak-days">Рекорд: 3 дня</p>

      <div className="daily-goal-footer">
        <span className="goal-status">63 задания сегодня</span>
        <button className="start-button">Начать</button>
      </div>
    </div>
  );
}


// --- Главный Компонент Страницы ---
interface HomePageProps {
  theme: "dark" | "light";
  toggleTheme: () => void;
}

function HomePage({ theme, toggleTheme }: HomePageProps) {
  const [allCourses, setAllCourses] = useState<Course[]>([]);
  const [myCourses, setMyCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<{ id: number; username: string; email: string } | null>(null);
  const isDarkTheme = theme === "dark";
  const location = useLocation();
  const navigate = useNavigate();
  const [fetchTrigger, setFetchTrigger] = useState(0); // Состояние для ручного обновления

  const handleLogout = () => {
    localStorage.removeItem("currentUser");
    setCurrentUser(null);
    setMyCourses([]); // Очищаем курсы пользователя
    navigate('/'); // Перенаправляем на главную для полного обновления состояния
  };

  const refreshCourses = () => {
    setFetchTrigger(Date.now()); // Меняем состояние, чтобы вызвать useEffect
  };

  // Логика загрузки данных
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const timestamp = new Date().getTime();
        const config = {
          headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
          },
        };

        let user = null;
        try {
          const userStr = localStorage.getItem("currentUser");
          user = userStr ? JSON.parse(userStr) : null;
        } catch {
          user = null;
          localStorage.removeItem("currentUser");
        }

        // Всегда загружаем полный список курсов
        const base = API_URL.replace(/\/$/, '');
        const allCoursesPromise = axios
          .get<Course[]>(`${base}/api/v1/courses?_t=${timestamp}`, config)
          .catch((err) => {
            console.warn("Не удалось загрузить каталог курсов:", err);
            return { data: [] as Course[] };
          });

        // По возможности параллельно загружаем курсы пользователя
        let myCoursesPromise = Promise.resolve({ data: [] as Course[] });
        if (user && user.id) {
          myCoursesPromise = axios
            .get<Course[]>(`${base}/api/v1/users/${user.id}/courses?_t=${timestamp}`, config)
            .catch((err) => {
              console.warn("Не удалось загрузить курсы пользователя:", err);
              if (err?.response?.status === 404) {
                // Если пользователь не найден в БД — очищаем устаревшую сессию
                localStorage.removeItem("currentUser");
                setCurrentUser(null);
              }
              return { data: [] as Course[] };
            });
          setCurrentUser(user);
        } else {
          setCurrentUser(null);
          localStorage.removeItem("currentUser");
        }

        const [allCoursesResponse, myCoursesResponse] = await Promise.all([allCoursesPromise, myCoursesPromise]);

        // Устанавливаем оба состояния: полный каталог и курсы пользователя
        const all = allCoursesResponse.data || [];
        const my = myCoursesResponse.data || [];

        // Попытка сопоставить прогресс из localStorage (если есть)
        const userStrLocal = localStorage.getItem('currentUser');
        let progMap: Record<string, any> = {};
        if (userStrLocal) {
          try {
            const u = JSON.parse(userStrLocal);
            progMap = u.enrolledProgress || {};
          } catch (e) {
            progMap = {};
          }
        }

        const applyProgress = (courseList: any) => {
          // Защита от неожиданных ответов: если пришло не массив, пытаемся извлечь возможные поля или возвращаем пустой массив
          if (!Array.isArray(courseList)) {
            console.warn("applyProgress: expected array, got:", courseList);
            if (courseList && Array.isArray(courseList.data)) {
              courseList = courseList.data;
            } else if (courseList && Array.isArray(courseList.courses)) {
              courseList = courseList.courses;
            } else if (courseList && Array.isArray(courseList.results)) {
              courseList = courseList.results;
            } else {
              return [] as Course[];
            }
          }

          return courseList.map((c: Course) => {
            const saved = progMap[String(c.id)];
            if (saved && typeof saved.progress_percentage === 'number') {
              return { ...c, progress_percentage: saved.progress_percentage };
            }
            // Попробуем вычислить по полям, если доступны
            if (typeof c.completed_lessons === 'number' && typeof c.total_lessons === 'number' && c.total_lessons > 0) {
              const pct = Math.round((c.completed_lessons / c.total_lessons) * 100);
              return { ...c, progress_percentage: pct };
            }
            return c;
          });
        };

        setAllCourses(applyProgress(all));
        setMyCourses(applyProgress(my));
      } catch (err) {
        console.error("Ошибка загрузки данных:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [location, fetchTrigger]); // Добавляем fetchTrigger в зависимости

  // Фон страницы в той же стилистике, что и RegPage/LogPage
  const backgroundStyle: React.CSSProperties = {
    minHeight: "100vh",
    backgroundColor: isDarkTheme ? "#030712" : "#f8fafc",
    backgroundImage: isDarkTheme
      ? "radial-gradient(circle at 50% 0%, #3b82f640, #030712 35%)"
      : "radial-gradient(circle at 50% 0%, #e2e8f040, #f8fafc 35%)",
    animation: "pulse-spotlight 15s infinite ease-in-out",
  };

  if (loading) {
    return (
      <div style={backgroundStyle}>
        <div className="app-main-view">
          <Header />
          <div className="loading-state">Загрузка...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={backgroundStyle}>
        <div className="app-main-view">
          <Header />
          <div className="error-state">Ошибка: {error}</div>
        </div>
      </div>
    );
  }

  return (
    <div style={backgroundStyle}>
      <div className="app-main-view">
        <Header /> {/* <-- ВСТАВЛЕННЫЙ HEADER */}

        <div className="app-layout">
            <Sidebar />

          <div className="content-area">
            <div className="content-header">
              <h1 className="main-title">Моё обучение</h1>
              <div className="header-actions">
                
                <button
                  className="theme-toggle-btn"
                  type="button"
                  onClick={toggleTheme}
                  aria-label="Переключить тему"
                >
                  {isDarkTheme ? "" : ""}
                </button>
              </div>
            </div>

            {loading && <div className="loading-state">Загрузка...</div>}
            {error && <div className="error-state">{error}</div>}

            {!loading && !error && (
            <section className="dashboard-section">
              {/* Лента курсов */}
              <div className="course-list">
                {currentUser ? ( // --- Сценарий для залогиненного пользователя ---
                  <>
                    

                    {myCourses.length > 0 ? (
                      <>
                        
                        {myCourses.map((course) => (
                          <CourseCard key={`my-${course.id}`} course={course} />
                        ))}
                        <div style={{ marginTop: '20px' }}>
                            <Link to="/catalog" className="auth-link">Найти больше курсов в каталоге →</Link>
                        </div>
                      </>
                    ) : (
                        <div className="welcome-banner">
                            У вас пока нет активных курсов. <Link to="/catalog" className="auth-link">Перейти в каталог</Link>
                        </div>
                    )}
                  </>
                ) : ( // --- Сценарий для гостя ---
                  <>
                    <div className="welcome-banner">Чтобы записываться на курсы, <Link to="/login" className="auth-link">войдите в аккаунт</Link>. А пока просмотрите наш каталог.</div>
                    {allCourses.length > 0 ? allCourses.map((course) => (
                      <CourseCard key={course.id} course={course} />
                    )) : (
                      <div className="welcome-banner">Курсы скоро появятся!</div>
                    )}
                  </>
                )}
              </div>

              {/* Блок серии/цели */}
              <StreakAndDailyBox />
            </section>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default HomePage;