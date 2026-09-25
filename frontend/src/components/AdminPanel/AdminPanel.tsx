// AI-GENERATED: Antigravity
import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  FiUsers,
  FiLock,
  FiUnlock,
  FiCheckCircle,
  FiPlus,
  FiTrash2,
  FiCopy,
  FiBookOpen,
  FiArrowLeft,
  FiUserPlus,
  FiRefreshCw,
  FiActivity,
  FiAward,
  FiKey,
  FiFileText,
  FiUploadCloud,
  FiCheck,
  FiAlertCircle,
  FiEye,
} from "react-icons/fi";
import {
  fetchGroups,
  createGroup,
  deleteGroup,
  addStudentToGroup,
  removeStudentFromGroup,
  assignCourseToGroup,
  fetchGroupProgressMatrix,
  toggleGroupLessonAccess,
  fetchCourses,
  createCourseLesson,
  deleteLesson,
  fetchTeacherDashboard,
  fetchTeacherStudents,
  quickCreateStudent,
  fetchTeacherStudentDetail,
  resetStudentPassword,
  resetStudentProgress,
  toggleStudentStatus,
  createCourseBlock,
  importCourseMarkdown,
  createOrUpdateBlockExam,
  fetchBlockExam,
} from "../../api/api";
import "./StyleAdminPanel.css";

interface AdminPanelProps {
  theme: "dark" | "light";
  toggleTheme: () => void;
}

export default function AdminPanel({ theme, toggleTheme }: AdminPanelProps) {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<"dashboard" | "students" | "groups" | "gating" | "courses">("dashboard");

  // Статистика дашборда
  const [dashboardStats, setDashboardStats] = useState<any>(null);

  // Студенты
  const [students, setStudents] = useState<any[]>([]);
  const [studentsLoading, setStudentsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedStudentDetail, setSelectedStudentDetail] = useState<any>(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);

  // Модалка быстрого создания студента (Раздел 3 плана)
  const [showQuickCreateModal, setShowQuickCreateModal] = useState(false);
  const [studentFirstName, setStudentFirstName] = useState("");
  const [studentLastName, setStudentLastName] = useState("");
  const [studentGroupId, setStudentGroupId] = useState<number | "">("");
  const [createdStudentResult, setCreatedStudentResult] = useState<any>(null);
  const [copiedData, setCopiedData] = useState(false);

  // Сброс пароля
  const [newPasswordAlert, setNewPasswordAlert] = useState<{ username: string; pass: string } | null>(null);

  // Группы и курсы
  const [groups, setGroups] = useState<any[]>([]);
  const [courses, setCourses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Gating / Матрица
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);
  const [matrixData, setMatrixData] = useState<any>(null);
  const [matrixLoading, setMatrixLoading] = useState(false);

  // Конструктор курсов / Импорт Markdown
  const [selectedCourseForEdit, setSelectedCourseForEdit] = useState<number | null>(null);
  const [showAddBlockModal, setShowAddBlockModal] = useState(false);
  const [newBlockTitle, setNewBlockTitle] = useState("");
  const [newBlockDesc, setNewBlockDesc] = useState("");

  const [showMarkdownImportModal, setShowMarkdownImportModal] = useState(false);
  const [importLessonTitle, setImportLessonTitle] = useState("");
  const [importLessonContent, setImportLessonContent] = useState("");
  const [importBlockId, setImportBlockId] = useState<number | "">("");

  // Экзамен блока
  const [showExamModal, setShowExamModal] = useState(false);
  const [examBlockId, setExamBlockId] = useState<number | null>(null);
  const [examTitle, setExamTitle] = useState("");
  const [examScore, setExamScore] = useState(70);
  const [examAttempts, setExamAttempts] = useState(3);
  const [examQuestionText, setExamQuestionText] = useState("");
  const [examAnswers, setExamAnswers] = useState([
    { text: "", is_correct: true },
    { text: "", is_correct: false },
    { text: "", is_correct: false },
    { text: "", is_correct: false },
  ]);

  // Модальные окна групп
  const [showCreateGroupModal, setShowCreateGroupModal] = useState(false);
  const [newGroupName, setNewGroupName] = useState("");
  const [newGroupDesc, setNewGroupDesc] = useState("");
  const [showAssignCourseModal, setShowAssignCourseModal] = useState(false);
  const [courseToAssign, setCourseToAssign] = useState<number | null>(null);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  useEffect(() => {
    const raw = localStorage.getItem("currentUser");
    if (!raw) {
      navigate("/login");
      return;
    }
    const user = JSON.parse(raw);
    setCurrentUser(user);

    loadInitialData(user.id);
  }, [navigate]);

  const loadInitialData = async (userId: number) => {
    setLoading(true);
    try {
      const [groupsData, coursesData, statsData] = await Promise.all([
        fetchGroups(userId).catch(() => []),
        fetchCourses().catch(() => []),
        fetchTeacherDashboard().catch(() => null),
      ]);
      setGroups(groupsData);
      setCourses(coursesData);
      setDashboardStats(statsData);

      if (groupsData.length > 0) {
        setSelectedGroupId(groupsData[0].id);
        if (groupsData[0].courses && groupsData[0].courses.length > 0) {
          setSelectedCourseId(groupsData[0].courses[0].id);
        } else if (coursesData.length > 0) {
          setSelectedCourseId(coursesData[0].id);
        }
      }
      if (coursesData.length > 0) {
        setSelectedCourseForEdit(coursesData[0].id);
      }
    } catch (e) {
      console.error("Ошибка загрузки данных админ-панели:", e);
    } finally {
      setLoading(false);
    }
  };

  // Загрузка студентов при переключении на вкладку "students"
  useEffect(() => {
    if (activeTab === "students") {
      loadStudents();
    }
  }, [activeTab]);

  const loadStudents = async () => {
    setStudentsLoading(true);
    try {
      const data = await fetchTeacherStudents({ q: searchQuery });
      setStudents(data);
    } catch (e) {
      console.error("Ошибка загрузки студентов:", e);
    } finally {
      setStudentsLoading(false);
    }
  };

  // Матрица успеваемости
  useEffect(() => {
    if (selectedGroupId && selectedCourseId && activeTab === "gating") {
      loadMatrix(selectedGroupId, selectedCourseId);
    }
  }, [selectedGroupId, selectedCourseId, activeTab]);

  const loadMatrix = async (groupId: number, courseId: number) => {
    setMatrixLoading(true);
    try {
      const data = await fetchGroupProgressMatrix(groupId, courseId);
      setMatrixData(data);
    } catch (e) {
      setMatrixData(null);
    } finally {
      setMatrixLoading(false);
    }
  };

  const handleToggleAccess = async (lessonId: number, currentUnlocked: boolean) => {
    if (!selectedGroupId) return;
    try {
      await toggleGroupLessonAccess(selectedGroupId, lessonId, {
        is_unlocked: !currentUnlocked,
      });
      if (selectedCourseId) loadMatrix(selectedGroupId, selectedCourseId);
    } catch (e) {
      alert("Не удалось изменить статус доступа");
    }
  };

  // 1. Быстрое создание студента (Раздел 3 плана)
  const handleQuickCreateStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!studentFirstName.trim() || !studentLastName.trim()) {
      alert("Введите имя и фамилию студента");
      return;
    }
    try {
      const res = await quickCreateStudent({
        first_name: studentFirstName.trim(),
        last_name: studentLastName.trim(),
        group_id: studentGroupId ? Number(studentGroupId) : undefined,
      });
      setCreatedStudentResult(res);
      setStudentFirstName("");
      setStudentLastName("");
      setStudentGroupId("");
      loadStudents();
      fetchTeacherDashboard().then(setDashboardStats).catch(() => {});
    } catch (e) {
      alert("Ошибка при создании студента");
    }
  };

  const copyStudentCredentials = () => {
    if (!createdStudentResult) return;
    const text = `Логин: ${createdStudentResult.username}\nПароль: ${createdStudentResult.password}`;
    navigator.clipboard.writeText(text);
    setCopiedData(true);
    setTimeout(() => setCopiedData(false), 2500);
  };

  // 2. Сброс пароля студента
  const handleResetPassword = async (studentId: number) => {
    if (!window.confirm("Сгенерировать новый пароль для этого студента?")) return;
    try {
      const res = await resetStudentPassword(studentId);
      setNewPasswordAlert({ username: res.username, pass: res.new_password });
    } catch (e) {
      alert("Ошибка при сбросе пароля");
    }
  };

  // 3. Сброс прогресса студента
  const handleResetProgress = async (studentId: number) => {
    if (!window.confirm("Сбросить весь прогресс обучения этого студента?")) return;
    try {
      await resetStudentProgress(studentId);
      alert("Прогресс студента успешно сброшен");
      loadStudents();
    } catch (e) {
      alert("Ошибка при сбросе прогресса");
    }
  };

  // 4. Блокировка / разблокировка
  const handleToggleStudentStatus = async (studentId: number) => {
    try {
      const res = await toggleStudentStatus(studentId);
      alert(`Студент теперь: ${res.status_text}`);
      loadStudents();
    } catch (e) {
      alert("Не удалось изменить статус студента");
    }
  };

  // 5. Просмотр подробного профиля студента (Раздел 22 плана)
  const handleViewStudentDetail = async (studentId: number) => {
    try {
      const data = await fetchTeacherStudentDetail(studentId);
      setSelectedStudentDetail(data);
      setDetailModalOpen(true);
    } catch (e) {
      alert("Ошибка загрузки данных студента");
    }
  };

  // 6. Создание группы
  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newGroupName.trim()) return;
    try {
      const g = await createGroup({
        name: newGroupName.trim(),
        description: newGroupDesc.trim(),
        teacher_id: currentUser.id,
      });
      setGroups([...groups, g]);
      setShowCreateGroupModal(false);
      setNewGroupName("");
      setNewGroupDesc("");
      fetchTeacherDashboard().then(setDashboardStats).catch(() => {});
    } catch (e) {
      alert("Ошибка при создании группы");
    }
  };

  // 7. Создание блока курса
  const handleCreateBlock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourseForEdit || !newBlockTitle.trim()) return;
    try {
      await createCourseBlock(selectedCourseForEdit, {
        title: newBlockTitle.trim(),
        description: newBlockDesc.trim(),
      });
      setShowAddBlockModal(false);
      setNewBlockTitle("");
      setNewBlockDesc("");
      alert("Блок успешно создан!");
      fetchCourses().then(setCourses).catch(() => {});
    } catch (e) {
      alert("Ошибка создания блока");
    }
  };

  // 8. Импорт урока из Markdown
  const handleImportMarkdown = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourseForEdit || !importLessonContent.trim()) {
      alert("Вставьте текст Markdown");
      return;
    }
    try {
      await importCourseMarkdown(selectedCourseForEdit, {
        title: importLessonTitle.trim() || undefined,
        content: importLessonContent.trim(),
        block_id: importBlockId ? Number(importBlockId) : undefined,
      });
      setShowMarkdownImportModal(false);
      setImportLessonTitle("");
      setImportLessonContent("");
      setImportBlockId("");
      alert("Урок из Markdown успешно добавлен в курс!");
      fetchCourses().then(setCourses).catch(() => {});
    } catch (e) {
      alert("Ошибка при импорте Markdown");
    }
  };

  return (
    <div className="admin-container">
      {/* Шапка */}
      <header className="admin-header">
        <div className="admin-title-area">
          <Link to="/" className="btn-back">
            <FiArrowLeft /> На платформу
          </Link>
          <h2>Панель преподавателя StepLearn</h2>
          <span className="admin-badge">Преподаватель</span>
        </div>

        <div className="admin-user-info">
          <span>{currentUser?.name || currentUser?.username}</span>
        </div>
      </header>

      {/* Вкладки навигации */}
      <nav className="admin-nav-tabs">
        <button
          className={`admin-tab-btn ${activeTab === "dashboard" ? "active" : ""}`}
          onClick={() => setActiveTab("dashboard")}
        >
          <FiActivity /> Dashboard
        </button>
        <button
          className={`admin-tab-btn ${activeTab === "students" ? "active" : ""}`}
          onClick={() => setActiveTab("students")}
        >
          <FiUsers /> Студенты
        </button>
        <button
          className={`admin-tab-btn ${activeTab === "groups" ? "active" : ""}`}
          onClick={() => setActiveTab("groups")}
        >
          <FiUsers /> Группы
        </button>
        <button
          className={`admin-tab-btn ${activeTab === "gating" ? "active" : ""}`}
          onClick={() => setActiveTab("gating")}
        >
          <FiCheckCircle /> Мониторинг успеваемости
        </button>
        <button
          className={`admin-tab-btn ${activeTab === "courses" ? "active" : ""}`}
          onClick={() => setActiveTab("courses")}
        >
          <FiBookOpen /> Управление курсами и Markdown
        </button>
      </nav>

      {/* Контент вкладки */}
      <main className="admin-content">
        {/* 1. DASHBOARD */}
        {activeTab === "dashboard" && (
          <div className="dashboard-view animate-fade-in">
            <div className="dashboard-stats-grid">
              <div className="stat-card">
                <div className="stat-icon" style={{ background: "rgba(99, 102, 241, 0.2)", color: "#818cf8" }}>
                  <FiUsers />
                </div>
                <div>
                  <span className="stat-label">Всего студентов</span>
                  <h3 className="stat-value">{dashboardStats?.total_students ?? 0}</h3>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon" style={{ background: "rgba(16, 185, 129, 0.2)", color: "#34d399" }}>
                  <FiUsers />
                </div>
                <div>
                  <span className="stat-label">Учебных групп</span>
                  <h3 className="stat-value">{dashboardStats?.total_groups ?? 0}</h3>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon" style={{ background: "rgba(245, 158, 11, 0.2)", color: "#fbbf24" }}>
                  <FiBookOpen />
                </div>
                <div>
                  <span className="stat-label">Курсов в системе</span>
                  <h3 className="stat-value">{dashboardStats?.total_courses ?? 0}</h3>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon" style={{ background: "rgba(236, 72, 153, 0.2)", color: "#f472b6" }}>
                  <FiActivity />
                </div>
                <div>
                  <span className="stat-label">Активных за неделю</span>
                  <h3 className="stat-value">{dashboardStats?.active_students ?? 0}</h3>
                </div>
              </div>
            </div>

            <div className="quick-actions-box">
              <h3>Быстрые действия</h3>
              <div className="actions-buttons-row">
                <button className="btn-primary" onClick={() => setShowQuickCreateModal(true)}>
                  <FiUserPlus /> Создать студента
                </button>
                <button className="btn-secondary" onClick={() => setShowCreateGroupModal(true)}>
                  <FiPlus /> Создать группу
                </button>
                <button className="btn-secondary" onClick={() => setActiveTab("courses")}>
                  <FiUploadCloud /> Импортировать урок Markdown
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 2. СТУДЕНТЫ */}
        {activeTab === "students" && (
          <div className="students-view animate-fade-in">
            <div className="students-toolbar">
              <input
                type="text"
                placeholder="Поиск по имени, логину или email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && loadStudents()}
                className="search-input"
              />
              <button className="btn-primary" onClick={() => setShowQuickCreateModal(true)}>
                <FiUserPlus /> Создать студента
              </button>
            </div>

            {newPasswordAlert && (
              <div className="alert-success-banner">
                <FiCheckCircle /> Новый пароль для <strong>{newPasswordAlert.username}</strong>:{" "}
                <code>{newPasswordAlert.pass}</code>
                <button onClick={() => setNewPasswordAlert(null)} style={{ marginLeft: "auto" }}>
                  ✕
                </button>
              </div>
            )}

            {studentsLoading ? (
              <div className="loading-spinner">Загрузка студентов...</div>
            ) : (
              <div className="table-responsive">
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th>Студент</th>
                      <th>Логин</th>
                      <th>Группа</th>
                      <th>Курсов</th>
                      <th>Средний прогресс</th>
                      <th>Активность</th>
                      <th>Статус</th>
                      <th>Действия</th>
                    </tr>
                  </thead>
                  <tbody>
                    {students.map((st) => (
                      <tr key={st.id}>
                        <td>
                          <strong>{st.name}</strong>
                          <div style={{ fontSize: "0.8rem", color: "#64748b" }}>{st.email}</div>
                        </td>
                        <td><code>{st.username}</code></td>
                        <td><span className="badge-group">{st.group_name}</span></td>
                        <td>{st.courses_count}</td>
                        <td>
                          <div className="progress-cell">
                            <div className="progress-bar-sm">
                              <div style={{ width: `${st.avg_progress}%` }} className="progress-fill"></div>
                            </div>
                            <span>{st.avg_progress}%</span>
                          </div>
                        </td>
                        <td style={{ fontSize: "0.85rem", color: "#94a3b8" }}>
                          {st.last_activity ? new Date(st.last_activity).toLocaleDateString() : "Не заходил"}
                        </td>
                        <td>
                          <span className={`status-pill ${st.is_active ? "active" : "blocked"}`}>
                            {st.is_active ? "Активен" : "Заблокирован"}
                          </span>
                        </td>
                        <td>
                          <div className="table-actions">
                            <button
                              className="action-btn"
                              title="Подробный прогресс"
                              onClick={() => handleViewStudentDetail(st.id)}
                            >
                              <FiEye />
                            </button>
                            <button
                              className="action-btn"
                              title="Сгенерировать новый пароль"
                              onClick={() => handleResetPassword(st.id)}
                            >
                              <FiKey />
                            </button>
                            <button
                              className="action-btn"
                              title="Сбросить прогресс"
                              onClick={() => handleResetProgress(st.id)}
                            >
                              <FiRefreshCw />
                            </button>
                            <button
                              className="action-btn danger"
                              title={st.is_active ? "Заблокировать" : "Разблокировать"}
                              onClick={() => handleToggleStudentStatus(st.id)}
                            >
                              {st.is_active ? <FiLock /> : <FiUnlock />}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* 3. ГРУППЫ */}
        {activeTab === "groups" && (
          <div className="groups-view animate-fade-in">
            <div className="section-header-row">
              <h3>Учебные группы</h3>
              <button className="btn-primary" onClick={() => setShowCreateGroupModal(true)}>
                <FiPlus /> Создать группу
              </button>
            </div>

            <div className="admin-grid">
              {groups.map((g) => (
                <div key={g.id} className="admin-card">
                  <div className="card-top">
                    <h4>{g.name}</h4>
                    <span className="code-chip" onClick={() => {
                      navigator.clipboard.writeText(g.code);
                      setCopiedCode(g.code);
                      setTimeout(() => setCopiedCode(null), 2000);
                    }}>
                      {copiedCode === g.code ? "Скопировано!" : g.code} <FiCopy />
                    </span>
                  </div>
                  <p className="card-desc">{g.description || "Без описания"}</p>
                  <div className="card-meta-line">
                    <span>👥 Студентов: {g.students_count}</span>
                    <span>📚 Курсов: {g.courses?.length || 0}</span>
                  </div>
                  <div className="card-footer-btns">
                    <button
                      className="btn-sm-primary"
                      onClick={() => {
                        setSelectedGroupId(g.id);
                        setActiveTab("gating");
                      }}
                    >
                      Матрица прогресса
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 4. МОНИТОРИНГ УСПЕВАЕМОСТИ (GATING) */}
        {activeTab === "gating" && (
          <div className="gating-view animate-fade-in">
            <div className="gating-selectors">
              <div>
                <label>Группа:</label>
                <select
                  value={selectedGroupId || ""}
                  onChange={(e) => setSelectedGroupId(Number(e.target.value))}
                >
                  {groups.map((g) => (
                    <option key={g.id} value={g.id}>{g.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label>Курс:</label>
                <select
                  value={selectedCourseId || ""}
                  onChange={(e) => setSelectedCourseId(Number(e.target.value))}
                >
                  {courses.map((c) => (
                    <option key={c.id} value={c.id}>{c.title}</option>
                  ))}
                </select>
              </div>
            </div>

            {matrixLoading ? (
              <div className="loading-spinner">Загрузка матрицы успеваемости...</div>
            ) : matrixData ? (
              <div className="matrix-table-container">
                <table className="matrix-table">
                  <thead>
                    <tr>
                      <th className="sticky-col">Студент</th>
                      {matrixData.lessons?.map((l: any) => (
                        <th key={l.lesson_id} className="lesson-col-header">
                          <div className="lesson-th-title">#{l.order} {l.title}</div>
                          <div className="lesson-th-stat">
                            Сдали: {l.completed_students_count} / {l.total_students_count} ({l.completion_rate}%)
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {matrixData.students?.map((st: any) => (
                      <tr key={st.id}>
                        <td className="sticky-col student-name-cell">
                          <strong>{st.name}</strong>
                          <span className="student-overall-pct">{st.overall_progress}%</span>
                        </td>
                        {matrixData.lessons?.map((l: any) => {
                          const isDone = st.lessons[l.lesson_id];
                          return (
                            <td key={l.lesson_id} className={`matrix-cell ${isDone ? "done" : "pending"}`}>
                              {isDone ? "✅" : "⏳"}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state">Выберите группу и курс для просмотра матрицы</div>
            )}
          </div>
        )}

        {/* 5. УПРАВЛЕНИЕ КУРСАМИ И MARKDOWN */}
        {activeTab === "courses" && (
          <div className="courses-view animate-fade-in">
            <div className="courses-editor-header">
              <div className="course-select-box">
                <label>Редактируемый курс:</label>
                <select
                  value={selectedCourseForEdit || ""}
                  onChange={(e) => setSelectedCourseForEdit(Number(e.target.value))}
                >
                  {courses.map((c) => (
                    <option key={c.id} value={c.id}>{c.title} ({c.category})</option>
                  ))}
                </select>
              </div>

              <div className="header-actions">
                <button className="btn-secondary" onClick={() => setShowAddBlockModal(true)}>
                  <FiPlus /> Создать блок
                </button>
                <button className="btn-primary" onClick={() => setShowMarkdownImportModal(true)}>
                  <FiUploadCloud /> Импортировать Markdown-урок
                </button>
              </div>
            </div>

            <div className="course-content-tree">
              <h4>Структура уроков курса</h4>
              <p style={{ color: "#94a3b8" }}>
                Уроки поддерживают форматирование Markdown (заголовки, код, таблицы, списки).
              </p>
            </div>
          </div>
        )}
      </main>

      {/* МОДАЛЬНОЕ ОКНО: Быстрое создание студента (Раздел 3 плана) */}
      {showQuickCreateModal && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <h3>Создать аккаунт студента</h3>
            <p className="modal-subtitle">
              Система автоматически сгенерирует уникальный логин и надежный пароль для студента.
            </p>

            {createdStudentResult ? (
              <div className="credentials-result-box animate-fade-in">
                <div className="success-badge">✅ Студент успешно создан!</div>
                <div className="cred-row">
                  <span>ФИО:</span>
                  <strong>{createdStudentResult.first_name} {createdStudentResult.last_name}</strong>
                </div>
                <div className="cred-row">
                  <span>Логин:</span>
                  <code>{createdStudentResult.username}</code>
                </div>
                <div className="cred-row">
                  <span>Пароль:</span>
                  <code>{createdStudentResult.password}</code>
                </div>
                {createdStudentResult.group_name && (
                  <div className="cred-row">
                    <span>Группа:</span>
                    <strong>{createdStudentResult.group_name}</strong>
                  </div>
                )}

                <button className="btn-copy-creds" onClick={copyStudentCredentials}>
                  {copiedData ? <><FiCheck /> Скопировано в буфер!</> : <><FiCopy /> Скопировать данные студента</>}
                </button>

                <button
                  className="btn-secondary full-width"
                  style={{ marginTop: "1rem" }}
                  onClick={() => {
                    setCreatedStudentResult(null);
                    setShowQuickCreateModal(false);
                  }}
                >
                  Закрыть
                </button>
              </div>
            ) : (
              <form onSubmit={handleQuickCreateStudent}>
                <div className="form-group">
                  <label>Имя студента *</label>
                  <input
                    type="text"
                    required
                    placeholder="Например, Магамет"
                    value={studentFirstName}
                    onChange={(e) => setStudentFirstName(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>Фамилия студента *</label>
                  <input
                    type="text"
                    required
                    placeholder="Например, Дзангиев"
                    value={studentLastName}
                    onChange={(e) => setStudentLastName(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>Учебная группа (опционально)</label>
                  <select
                    value={studentGroupId}
                    onChange={(e) => setStudentGroupId(e.target.value ? Number(e.target.value) : "")}
                  >
                    <option value="">Без группы</option>
                    {groups.map((g) => (
                      <option key={g.id} value={g.id}>{g.name}</option>
                    ))}
                  </select>
                </div>

                <div className="modal-actions">
                  <button type="button" className="btn-secondary" onClick={() => setShowQuickCreateModal(false)}>
                    Отмена
                  </button>
                  <button type="submit" className="btn-primary">
                    Сгенерировать аккаунт
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* МОДАЛЬНОЕ ОКНО: Карточка конкретного студента (Раздел 22 плана) */}
      {detailModalOpen && selectedStudentDetail && (
        <div className="modal-backdrop">
          <div className="modal-card wide-modal">
            <div className="student-profile-header">
              <h3>{selectedStudentDetail.name}</h3>
              <span className="badge-group">
                {selectedStudentDetail.group?.name || "Без группы"}
              </span>
            </div>

            <div className="detail-sections-grid">
              <div className="detail-col">
                <h4>Курсы и прогресс</h4>
                {selectedStudentDetail.courses?.length > 0 ? (
                  selectedStudentDetail.courses.map((c: any) => (
                    <div key={c.course_id} className="student-course-item">
                      <div className="course-item-header">
                        <strong>{c.course_title}</strong>
                        <span>{c.progress_percentage}%</span>
                      </div>
                      <div className="progress-bar-sm">
                        <div style={{ width: `${c.progress_percentage}%` }} className="progress-fill"></div>
                      </div>
                      <div className="course-item-sub">
                        Пройдено: {c.completed_lessons} / {c.total_lessons} уроков
                      </div>
                      <div className="course-item-current">
                        Текущий урок: <em>{c.current_lesson}</em>
                      </div>
                    </div>
                  ))
                ) : (
                  <p style={{ color: "#94a3b8" }}>Нет назначенных курсов</p>
                )}
              </div>

              <div className="detail-col">
                <h4>Результаты экзаменов</h4>
                {selectedStudentDetail.exams?.length > 0 ? (
                  selectedStudentDetail.exams.map((ex: any, idx: number) => (
                    <div key={idx} className="exam-result-item">
                      <strong>{ex.exam_title}</strong>: {ex.score}% (
                      <span className={ex.passed ? "text-success" : "text-danger"}>
                        {ex.passed ? "Сдан" : "Не сдан"}
                      </span>
                      )
                    </div>
                  ))
                ) : (
                  <p style={{ color: "#94a3b8" }}>Экзамены еще не сдавались</p>
                )}

                <h4 style={{ marginTop: "1.5rem" }}>История обучения</h4>
                <ul className="learning-history-list">
                  {selectedStudentDetail.learning_history?.map((h: any, idx: number) => (
                    <li key={idx}>
                      {new Date(h.completed_at).toLocaleDateString()} — {h.lesson_title} ✅
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setDetailModalOpen(false)}>
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}

      {/* МОДАЛЬНОЕ ОКНО: Создание группы */}
      {showCreateGroupModal && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <h3>Создание новой учебной группы</h3>
            <form onSubmit={handleCreateGroup}>
              <div className="form-group">
                <label>Название группы *</label>
                <input
                  type="text"
                  required
                  placeholder="Например, Python-01"
                  value={newGroupName}
                  onChange={(e) => setNewGroupName(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Описание</label>
                <textarea
                  placeholder="Направление, расписание или цель группы..."
                  value={newGroupDesc}
                  onChange={(e) => setNewGroupDesc(e.target.value)}
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowCreateGroupModal(false)}>
                  Отмена
                </button>
                <button type="submit" className="btn-primary">
                  Создать
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* МОДАЛЬНОЕ ОКНО: Создание блока */}
      {showAddBlockModal && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <h3>Создать модуль/блок курса</h3>
            <form onSubmit={handleCreateBlock}>
              <div className="form-group">
                <label>Название блока *</label>
                <input
                  type="text"
                  required
                  placeholder="Например, Блок 1. Основы Python"
                  value={newBlockTitle}
                  onChange={(e) => setNewBlockTitle(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Описание блока</label>
                <textarea
                  placeholder="Краткое описание тем модуля..."
                  value={newBlockDesc}
                  onChange={(e) => setNewBlockDesc(e.target.value)}
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowAddBlockModal(false)}>
                  Отмена
                </button>
                <button type="submit" className="btn-primary">
                  Создать блок
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* МОДАЛЬНОЕ ОКНО: Импорт урока из Markdown (Раздел 28 плана) */}
      {showMarkdownImportModal && (
        <div className="modal-backdrop">
          <div className="modal-card wide-modal">
            <h3>Импорт урока из Markdown (.md)</h3>
            <p className="modal-subtitle">
              Вставьте текст в формате Markdown. Если заголовок не указан, он будет автоматически извлечен из первой строки с #.
            </p>
            <form onSubmit={handleImportMarkdown}>
              <div className="form-group">
                <label>Название урока (опционально)</label>
                <input
                  type="text"
                  placeholder="Оставьте пустым для авто-извлечения из текста"
                  value={importLessonTitle}
                  onChange={(e) => setImportLessonTitle(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Текст Markdown *</label>
                <textarea
                  required
                  rows={10}
                  placeholder="# Мой урок&#10;&#10;Текст урока...&#10;&#10;```python&#10;print('Hello!')&#10;```"
                  value={importLessonContent}
                  onChange={(e) => setImportLessonContent(e.target.value)}
                  style={{ fontFamily: "monospace", fontSize: "0.9rem" }}
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowMarkdownImportModal(false)}>
                  Отмена
                </button>
                <button type="submit" className="btn-primary">
                  Импортировать урок
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
