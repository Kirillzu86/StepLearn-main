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
  getUsers,
} from "../../api/api";
import "./StyleAdminPanel.css";

interface AdminPanelProps {
  theme: "dark" | "light";
  toggleTheme: () => void;
}

export default function AdminPanel({ theme, toggleTheme }: AdminPanelProps) {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<"groups" | "gating" | "lessons">("gating");

  // Данные групп и курсов
  const [groups, setGroups] = useState<any[]>([]);
  const [courses, setCourses] = useState<any[]>([]);
  const [allUsers, setAllUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Выбранная группа и курс для вкладки Gating
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);
  const [matrixData, setMatrixData] = useState<any>(null);
  const [matrixLoading, setMatrixLoading] = useState(false);

  // Модальные окна
  const [showCreateGroupModal, setShowCreateGroupModal] = useState(false);
  const [newGroupName, setNewGroupName] = useState("");
  const [newGroupDesc, setNewGroupDesc] = useState("");

  const [showAddStudentModal, setShowAddStudentModal] = useState(false);
  const [selectedStudentToAdd, setSelectedStudentToAdd] = useState("");
  const [targetGroupId, setTargetGroupId] = useState<number | null>(null);

  const [showAssignCourseModal, setShowAssignCourseModal] = useState(false);
  const [courseToAssign, setCourseToAssign] = useState<number | null>(null);

  const [showCreateLessonModal, setShowCreateLessonModal] = useState(false);
  const [newLessonTitle, setNewLessonTitle] = useState("");
  const [newLessonContent, setNewLessonContent] = useState("");
  const [newLessonDesc, setNewLessonDesc] = useState("");

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
      const [groupsData, coursesData, usersData] = await Promise.all([
        fetchGroups(userId),
        fetchCourses(),
        getUsers().catch(() => []),
      ]);
      setGroups(groupsData);
      setCourses(coursesData);
      setAllUsers(usersData);

      if (groupsData.length > 0) {
        setSelectedGroupId(groupsData[0].id);
        if (groupsData[0].courses && groupsData[0].courses.length > 0) {
          setSelectedCourseId(groupsData[0].courses[0].id);
        } else if (coursesData.length > 0) {
          setSelectedCourseId(coursesData[0].id);
        }
      }
    } catch (e) {
      console.error("Ошибка загрузки данных админ-панели:", e);
    } finally {
      setLoading(false);
    }
  };

  // Загрузка матрицы успеваемости группы по курсу
  useEffect(() => {
    if (selectedGroupId && selectedCourseId) {
      loadMatrix(selectedGroupId, selectedCourseId);
    } else {
      setMatrixData(null);
    }
  }, [selectedGroupId, selectedCourseId]);

  const loadMatrix = async (groupId: number, courseId: number) => {
    setMatrixLoading(true);
    try {
      const data = await fetchGroupProgressMatrix(groupId, courseId);
      setMatrixData(data);
    } catch (e) {
      console.error("Ошибка загрузки матрицы:", e);
      setMatrixData(null);
    } finally {
      setMatrixLoading(false);
    }
  };

  // Переключение блокировки урока для всей группы (Stepik / Cisco)
  const handleToggleAccess = async (lessonId: number, currentUnlocked: boolean) => {
    if (!selectedGroupId) return;
    try {
      await toggleGroupLessonAccess(selectedGroupId, lessonId, {
        is_unlocked: !currentUnlocked,
      });
      // Обновляем матрицу
      if (selectedCourseId) {
        loadMatrix(selectedGroupId, selectedCourseId);
      }
    } catch (e) {
      alert("Не удалось изменить статус доступа");
    }
  };

  // Переключение авто-открытия
  const handleToggleAutoUnlock = async (lessonId: number, currentAuto: boolean) => {
    if (!selectedGroupId) return;
    try {
      await toggleGroupLessonAccess(selectedGroupId, lessonId, {
        auto_unlock_when_all_pass: !currentAuto,
      });
      if (selectedCourseId) {
        loadMatrix(selectedGroupId, selectedCourseId);
      }
    } catch (e) {
      alert("Ошибка изменения флага авто-открытия");
    }
  };

  // Создание новой группы
  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newGroupName.trim() || !currentUser) return;
    try {
      const created = await createGroup({
        name: newGroupName.trim(),
        description: newGroupDesc.trim(),
        teacher_id: currentUser.id,
      });
      setGroups([created, ...groups]);
      setSelectedGroupId(created.id);
      setShowCreateGroupModal(false);
      setNewGroupName("");
      setNewGroupDesc("");
    } catch (e) {
      alert("Ошибка создания группы");
    }
  };

  // Добавление студента в группу
  const handleAddStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetGroupId || !selectedStudentToAdd.trim()) return;
    try {
      const updated = await addStudentToGroup(targetGroupId, { username: selectedStudentToAdd.trim() });
      setGroups(groups.map((g) => (g.id === targetGroupId ? updated : g)));
      setShowAddStudentModal(false);
      setSelectedStudentToAdd("");
      if (selectedGroupId === targetGroupId && selectedCourseId) {
        loadMatrix(selectedGroupId, selectedCourseId);
      }
    } catch (e: any) {
      alert(e.response?.data?.detail || "Не удалось добавить студента");
    }
  };

  // Удаление студента
  const handleRemoveStudent = async (groupId: number, studentId: number) => {
    if (!confirm("Удалить студента из этой группы?")) return;
    try {
      const updated = await removeStudentFromGroup(groupId, studentId);
      setGroups(groups.map((g) => (g.id === groupId ? updated : g)));
      if (selectedGroupId === groupId && selectedCourseId) {
        loadMatrix(selectedGroupId, selectedCourseId);
      }
    } catch (e) {
      alert("Ошибка удаления студента");
    }
  };

  // Назначение курса группе
  const handleAssignCourse = async () => {
    if (!selectedGroupId || !courseToAssign) return;
    try {
      await assignCourseToGroup(selectedGroupId, courseToAssign);
      setSelectedCourseId(courseToAssign);
      setShowAssignCourseModal(false);
      if (currentUser) loadInitialData(currentUser.id);
    } catch (e) {
      alert("Ошибка назначения курса группе");
    }
  };

  // Создание нового урока/модуля
  const handleCreateLesson = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourseId || !newLessonTitle.trim()) return;
    try {
      await createCourseLesson(selectedCourseId, {
        title: newLessonTitle.trim(),
        content: newLessonContent,
        description: newLessonDesc.trim(),
      });
      setShowCreateLessonModal(false);
      setNewLessonTitle("");
      setNewLessonContent("");
      setNewLessonDesc("");
      if (selectedGroupId) {
        loadMatrix(selectedGroupId, selectedCourseId);
      }
    } catch (e) {
      alert("Ошибка добавления урока");
    }
  };

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const currentSelectedGroup = groups.find((g) => g.id === selectedGroupId);

  return (
    <div className="admin-container" data-theme={theme}>
      {/* Шапка */}
      <header className="admin-header">
        <div className="admin-title-area">
          <Link to="/" className="btn-secondary" style={{ padding: "0.4rem 0.8rem", fontSize: "0.9rem" }}>
            <FiArrowLeft /> На сайт
          </Link>
          <h1 style={{ margin: 0, fontSize: "1.3rem" }}>Учительская панель</h1>
          <span className="admin-badge">Stepik & Cisco Mode</span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <span>
            Преподаватель: <strong>{currentUser?.name || currentUser?.username}</strong>
          </span>
          <button className="btn-secondary" onClick={toggleTheme}>
            {theme === "dark" ? "☀️ Светлая" : "🌙 Тёмная"}
          </button>
        </div>
      </header>

      {/* Вкладки навигации */}
      <nav className="admin-nav-tabs">
        <button
          className={`admin-tab-btn ${activeTab === "gating" ? "active" : ""}`}
          onClick={() => setActiveTab("gating")}
        >
          <FiLock /> Доступ к материалам (Stepik / Cisco)
        </button>
        <button
          className={`admin-tab-btn ${activeTab === "groups" ? "active" : ""}`}
          onClick={() => setActiveTab("groups")}
        >
          <FiUsers /> Учебные группы ({groups.length})
        </button>
        <button
          className={`admin-tab-btn ${activeTab === "lessons" ? "active" : ""}`}
          onClick={() => setActiveTab("lessons")}
        >
          <FiBookOpen /> Конструктор модулей курса
        </button>
      </nav>

      {/* Контент */}
      <main className="admin-content">
        {loading ? (
          <div style={{ textAlign: "center", padding: "3rem" }}>Загрузка панели...</div>
        ) : (
          <>
            {/* ============================================================ */}
            {/* ВКЛАДКА 1: УПРАВЛЕНИЕ ДОСТУПОМ (STEPIK / CISCO GATING)       */}
            {/* ============================================================ */}
            {activeTab === "gating" && (
              <div>
                {/* Панель выбора группы и курса */}
                <div className="gating-header">
                  <div className="selectors-row">
                    <div>
                      <label style={{ display: "block", fontSize: "0.85rem", color: "#94a3b8", marginBottom: "0.25rem" }}>
                        Выберите учебную группу:
                      </label>
                      <select
                        className="admin-select"
                        value={selectedGroupId || ""}
                        onChange={(e) => {
                          const gid = Number(e.target.value);
                          setSelectedGroupId(gid);
                          const g = groups.find((item) => item.id === gid);
                          if (g?.courses?.length > 0) {
                            setSelectedCourseId(g.courses[0].id);
                          }
                        }}
                      >
                        {groups.map((g) => (
                          <option key={g.id} value={g.id}>
                            {g.name} ({g.students_count} студентов)
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label style={{ display: "block", fontSize: "0.85rem", color: "#94a3b8", marginBottom: "0.25rem" }}>
                        Выберите курс:
                      </label>
                      <select
                        className="admin-select"
                        value={selectedCourseId || ""}
                        onChange={(e) => setSelectedCourseId(Number(e.target.value))}
                      >
                        {courses.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.title}
                          </option>
                        ))}
                      </select>
                    </div>

                    <button
                      className="btn-secondary"
                      style={{ marginTop: "1.2rem" }}
                      onClick={() => setShowAssignCourseModal(true)}
                    >
                      <FiPlus /> Назначить курс группе
                    </button>
                  </div>

                  <button
                    className="btn-secondary"
                    onClick={() => selectedGroupId && selectedCourseId && loadMatrix(selectedGroupId, selectedCourseId)}
                  >
                    <FiRefreshCw /> Обновить успеваемость
                  </button>
                </div>

                {matrixLoading ? (
                  <div style={{ textAlign: "center", padding: "2rem" }}>Загрузка матрицы успеваемости...</div>
                ) : !matrixData ? (
                  <div style={{ textAlign: "center", padding: "3rem", background: "rgba(30,41,59,0.5)", borderRadius: "1rem" }}>
                    <p style={{ fontSize: "1.1rem" }}>Курс ещё не назначен этой группе или в нем нет модулей.</p>
                    <button className="btn-primary" onClick={() => setShowAssignCourseModal(true)}>
                      Назначить выбранный курс группе
                    </button>
                  </div>
                ) : (
                  <div>
                    {/* Список модулей с кнопками открытия для всей группы */}
                    <div style={{ marginBottom: "2rem" }}>
                      <h2 style={{ fontSize: "1.2rem", marginBottom: "1rem" }}>
                        Модули курса: {matrixData.course?.title} (Группа: {matrixData.group?.name})
                      </h2>

                      {matrixData.lessons?.length === 0 ? (
                        <p style={{ color: "#94a3b8" }}>В этом курсе пока нет отдельных модулей.</p>
                      ) : (
                        matrixData.lessons.map((lesson: any) => (
                          <div
                            key={lesson.lesson_id}
                            className={`lesson-access-card ${lesson.is_unlocked ? "unlocked" : "locked"}`}
                          >
                            <div className="lesson-card-top">
                              <div>
                                <h3 style={{ margin: "0 0 0.3rem 0", fontSize: "1.1rem" }}>
                                  Модуль {lesson.order}: {lesson.title}
                                </h3>
                                <span className={`lesson-status-badge ${lesson.is_unlocked ? "open" : "closed"}`}>
                                  {lesson.is_unlocked ? (
                                    <>
                                      <FiUnlock /> Открыт для всей группы
                                    </>
                                  ) : (
                                    <>
                                      <FiLock /> Заблокирован для группы
                                    </>
                                  )}
                                </span>
                              </div>

                              <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
                                {/* Переключатель авто-открытия */}
                                <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem", cursor: "pointer" }}>
                                  <input
                                    type="checkbox"
                                    checked={lesson.auto_unlock_when_all_pass}
                                    onChange={() => handleToggleAutoUnlock(lesson.lesson_id, lesson.auto_unlock_when_all_pass)}
                                  />
                                  <span>Авто-открытие при 100% сдачи</span>
                                </label>

                                {/* Кнопка ручного открытия/закрытия */}
                                <button
                                  className={lesson.is_unlocked ? "btn-secondary" : "btn-primary"}
                                  onClick={() => handleToggleAccess(lesson.lesson_id, lesson.is_unlocked)}
                                >
                                  {lesson.is_unlocked ? (
                                    <>
                                      <FiLock /> Закрыть доступ
                                    </>
                                  ) : (
                                    <>
                                      <FiUnlock /> Открыть для группы
                                    </>
                                  )}
                                </button>
                              </div>
                            </div>

                            {/* Прогресс группы */}
                            <div>
                              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", color: "#cbd5e1" }}>
                                <span>
                                  Сдали: <strong>{lesson.completed_students_count}</strong> из {lesson.total_students_count} студентов ({lesson.completion_rate}%)
                                </span>
                                {lesson.all_passed && (
                                  <span style={{ color: "#34d399", fontWeight: 700 }}>
                                    ✓ Вся группа завершила этот модуль!
                                  </span>
                                )}
                              </div>
                              <div className="progress-bar-container">
                                <div
                                  className={`progress-bar-fill ${lesson.all_passed ? "" : "partial"}`}
                                  style={{ width: `${lesson.completion_rate}%` }}
                                />
                              </div>
                            </div>
                          </div>
                        ))
                      )}
                    </div>

                    {/* Матрица студентов: кто конкретно сдал каждый модуль */}
                    <div>
                      <h2 style={{ fontSize: "1.2rem", marginBottom: "0.75rem" }}>
                        Матрица сдачи модулей студентами группы ({matrixData.total_students} чел.)
                      </h2>
                      <div className="matrix-table-container">
                        <table className="matrix-table">
                          <thead>
                            <tr>
                              <th>Студент</th>
                              {matrixData.lessons?.map((l: any) => (
                                <th key={l.lesson_id}>
                                  Модуль {l.order}
                                </th>
                              ))}
                              <th>Общий прогресс</th>
                            </tr>
                          </thead>
                          <tbody>
                            {matrixData.students?.map((s: any) => (
                              <tr key={s.id}>
                                <td>
                                  <strong>{s.name || s.username}</strong>
                                  <div style={{ fontSize: "0.8rem", color: "#64748b" }}>@{s.username}</div>
                                </td>
                                {matrixData.lessons?.map((l: any) => {
                                  const done = s.lessons?.[l.lesson_id];
                                  return (
                                    <td key={l.lesson_id}>
                                      {done ? (
                                        <span className="status-check">
                                          <FiCheckCircle /> Сдано
                                        </span>
                                      ) : (
                                        <span className="status-wait">⏳ В процессе</span>
                                      )}
                                    </td>
                                  );
                                })}
                                <td>
                                  <strong>{s.overall_progress}%</strong>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ============================================================ */}
            {/* ВКЛАДКА 2: УПРАВЛЕНИЕ УЧЕБНЫМИ ГРУППАМИ                      */}
            {/* ============================================================ */}
            {activeTab === "groups" && (
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
                  <h2 style={{ fontSize: "1.25rem", margin: 0 }}>Учебные группы</h2>
                  <button className="btn-primary" onClick={() => setShowCreateGroupModal(true)}>
                    <FiPlus /> Создать новую группу
                  </button>
                </div>

                <div className="admin-grid">
                  {groups.map((group) => (
                    <div key={group.id} className="admin-card">
                      <div className="card-header">
                        <div>
                          <h3 className="card-title">{group.name}</h3>
                          <span
                            className="code-pill"
                            onClick={() => copyCode(group.code)}
                            title="Нажмите, чтобы скопировать инвайт-код"
                          >
                            <FiCopy /> {group.code} {copiedCode === group.code ? "(Скопировано!)" : ""}
                          </span>
                        </div>
                        <button
                          className="btn-danger"
                          onClick={() => {
                            if (confirm(`Удалить группу «${group.name}»?`)) {
                              deleteGroup(group.id).then(() => setGroups(groups.filter((g) => g.id !== group.id)));
                            }
                          }}
                        >
                          <FiTrash2 />
                        </button>
                      </div>

                      <p style={{ color: "#94a3b8", fontSize: "0.9rem", margin: "0.5rem 0 1rem" }}>
                        {group.description || "Без описания"}
                      </p>

                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                        <span style={{ fontSize: "0.9rem", fontWeight: 600 }}>
                          Студенты ({group.students?.length || 0}):
                        </span>
                        <button
                          className="btn-secondary"
                          style={{ padding: "0.3rem 0.6rem", fontSize: "0.8rem" }}
                          onClick={() => {
                            setTargetGroupId(group.id);
                            setShowAddStudentModal(true);
                          }}
                        >
                          <FiUserPlus /> Добавить
                        </button>
                      </div>

                      {/* Список студентов */}
                      <div style={{ maxHeight: "180px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                        {group.students?.length === 0 ? (
                          <div style={{ color: "#64748b", fontSize: "0.85rem" }}>В группе пока нет студентов.</div>
                        ) : (
                          group.students?.map((s: any) => (
                            <div
                              key={s.id}
                              style={{
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                                padding: "0.35rem 0.5rem",
                                background: "rgba(15, 23, 42, 0.4)",
                                borderRadius: "0.4rem",
                                fontSize: "0.85rem",
                              }}
                            >
                              <span>{s.name || s.username} (@{s.username})</span>
                              <button
                                style={{ background: "none", border: "none", color: "#f87171", cursor: "pointer" }}
                                onClick={() => handleRemoveStudent(group.id, s.id)}
                                title="Удалить из группы"
                              >
                                &times;
                              </button>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ============================================================ */}
            {/* ВКЛАДКА 3: КОНСТРУКТОР МОДУЛЕЙ И УРОКОВ                      */}
            {/* ============================================================ */}
            {activeTab === "lessons" && (
              <div>
                <div className="gating-header">
                  <div>
                    <label style={{ display: "block", fontSize: "0.85rem", color: "#94a3b8", marginBottom: "0.25rem" }}>
                      Выберите курс для добавления модулей:
                    </label>
                    <select
                      className="admin-select"
                      value={selectedCourseId || ""}
                      onChange={(e) => setSelectedCourseId(Number(e.target.value))}
                    >
                      {courses.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.title}
                        </option>
                      ))}
                    </select>
                  </div>

                  <button className="btn-primary" onClick={() => setShowCreateLessonModal(true)}>
                    <FiPlus /> Добавить новый модуль к курсу
                  </button>
                </div>

                <div>
                  <h3>Модули выбранного курса:</h3>
                  {matrixData?.lessons?.length === 0 ? (
                    <p style={{ color: "#94a3b8" }}>У этого курса пока нет модулей. Создайте первый модуль!</p>
                  ) : (
                    matrixData?.lessons?.map((l: any) => (
                      <div key={l.lesson_id} className="lesson-access-card" style={{ borderLeft: "4px solid #6366f1" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <div>
                            <h4 style={{ margin: "0 0 0.25rem 0", fontSize: "1.05rem" }}>
                              Модуль {l.order}: {l.title}
                            </h4>
                          </div>
                          <button
                            className="btn-danger"
                            onClick={() => {
                              if (confirm(`Удалить модуль «${l.title}»?`)) {
                                deleteLesson(l.lesson_id).then(() => {
                                  if (selectedGroupId && selectedCourseId) {
                                    loadMatrix(selectedGroupId, selectedCourseId);
                                  }
                                });
                              }
                            }}
                          >
                            <FiTrash2 /> Удалить
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* ============================================================ */}
      {/* МОДАЛЬНЫЕ ОКНА                                              */}
      {/* ============================================================ */}

      {/* Модалка: Создание группы */}
      {showCreateGroupModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 style={{ marginTop: 0 }}>Создать новую учебную группу</h3>
            <form onSubmit={handleCreateGroup}>
              <div className="form-group">
                <label>Название группы:</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="например, Группа Cisco-102 или ИВТ-21"
                  value={newGroupName}
                  onChange={(e) => setNewGroupName(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label>Описание (необязательно):</label>
                <textarea
                  className="form-input"
                  style={{ minHeight: "80px" }}
                  placeholder="Краткое описание группы"
                  value={newGroupDesc}
                  onChange={(e) => setNewGroupDesc(e.target.value)}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem" }}>
                <button type="button" className="btn-secondary" onClick={() => setShowCreateGroupModal(false)}>
                  Отмена
                </button>
                <button type="submit" className="btn-primary">
                  Создать группу
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Модалка: Добавление студента */}
      {showAddStudentModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 style={{ marginTop: 0 }}>Добавить студента в группу</h3>
            <form onSubmit={handleAddStudent}>
              <div className="form-group">
                <label>Выберите или введите логин студента:</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Логин (username), например: student1"
                  value={selectedStudentToAdd}
                  onChange={(e) => setSelectedStudentToAdd(e.target.value)}
                  list="registered-students"
                  required
                />
                <datalist id="registered-students">
                  {allUsers.map((u) => (
                    <option key={u.id} value={u.username}>
                      {u.name} ({u.email})
                    </option>
                  ))}
                </datalist>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem" }}>
                <button type="button" className="btn-secondary" onClick={() => setShowAddStudentModal(false)}>
                  Отмена
                </button>
                <button type="submit" className="btn-primary">
                  Добавить
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Модалка: Назначение курса группе */}
      {showAssignCourseModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 style={{ marginTop: 0 }}>Назначить курс группе</h3>
            <p style={{ color: "#94a3b8", fontSize: "0.9rem" }}>
              Группа: <strong>{currentSelectedGroup?.name}</strong>
            </p>

            <div className="form-group">
              <label>Выберите курс:</label>
              <select
                className="form-input"
                value={courseToAssign || ""}
                onChange={(e) => setCourseToAssign(Number(e.target.value))}
              >
                <option value="">-- Выберите курс --</option>
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.title}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem" }}>
              <button type="button" className="btn-secondary" onClick={() => setShowAssignCourseModal(false)}>
                Отмена
              </button>
              <button
                type="button"
                className="btn-primary"
                disabled={!courseToAssign}
                onClick={handleAssignCourse}
              >
                Назначить курс
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Модалка: Создание нового модуля */}
      {showCreateLessonModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: "650px" }}>
            <h3 style={{ marginTop: 0 }}>Добавить модуль к курсу</h3>
            <form onSubmit={handleCreateLesson}>
              <div className="form-group">
                <label>Название модуля:</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="например, Модуль 4: Безопасность и списки доступа ACL"
                  value={newLessonTitle}
                  onChange={(e) => setNewLessonTitle(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label>Краткое описание:</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Краткое описание модуля"
                  value={newLessonDesc}
                  onChange={(e) => setNewLessonDesc(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Текст материала (Markdown):</label>
                <textarea
                  className="form-input"
                  style={{ minHeight: "150px", fontFamily: "monospace" }}
                  placeholder="# Заголовок темы&#10;&#10;Текст материала..."
                  value={newLessonContent}
                  onChange={(e) => setNewLessonContent(e.target.value)}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem" }}>
                <button type="button" className="btn-secondary" onClick={() => setShowCreateLessonModal(false)}>
                  Отмена
                </button>
                <button type="submit" className="btn-primary">
                  Сохранить модуль
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
