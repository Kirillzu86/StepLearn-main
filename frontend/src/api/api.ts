// AI-GENERATED: Antigravity
import axios from "axios";

// Если VITE_API_URL задан (например, при деплое в Coolify), используем его.
// Если нет — в браузере берем текущий origin (window.location.origin).
export const API_URL = (() => {
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl && typeof window !== 'undefined') {
    const isLocalhostEnv = envUrl.includes('localhost') || envUrl.includes('127.0.0.1');
    const isRemoteBrowser = !['localhost', '127.0.0.1'].includes(window.location.hostname);
    if (isLocalhostEnv && isRemoteBrowser) {
      return window.location.origin;
    }
    return envUrl;
  }
  return envUrl || (typeof window !== 'undefined' ? window.location.origin : '');
})();

export const getBase = () => API_URL.replace(/\/$/, '');

// ==========================================
// Пользователи и курсы
// ==========================================

export async function getUsers() {
  const res = await fetch(`${getBase()}/users`);
  if (!res.ok) {
    throw new Error("Failed to fetch users");
  }
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

export async function fetchCourses(query?: string, timestamp?: number) {
  const urlStr = `${getBase()}/v1/courses`;
  try {
    const url = new URL(urlStr, typeof window !== 'undefined' ? window.location.origin : 'http://127.0.0.1:8000');
    if (timestamp) url.searchParams.set('_t', String(timestamp));
    if (query?.trim()) url.searchParams.set('q', query.trim());

    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), 8000);

    const res = await fetch(url.toString(), { signal: controller.signal });
    clearTimeout(id);

    if (!res.ok) {
      const body = await res.text().catch(() => '');
      throw new Error(`Error: ${res.status} ${body}`);
    }

    const data = await res.json();
    if (Array.isArray(data)) return data;
    if (data && Array.isArray(data.data)) return data.data;
    if (data && Array.isArray(data.results)) return data.results;
    if (data && Array.isArray(data.courses)) return data.courses;
    return [];
  } catch (e) {
    console.error("Fetch courses error:", e);
    throw e;
  }
}

export async function fetchCourseDetail(courseId: number, userId?: number) {
  const base = getBase();
  const userParam = userId ? `?user_id=${userId}` : "";
  const res = await axios.get(`${base}/v1/course/${courseId}${userParam}`);
  return res.data;
}

// ==========================================
// Группы (StudyGroups)
// ==========================================

export async function fetchGroups(teacherId?: number) {
  const base = getBase();
  const url = teacherId ? `${base}/v1/groups?teacher_id=${teacherId}` : `${base}/v1/groups`;
  const res = await axios.get(url);
  return Array.isArray(res.data) ? res.data : [];
}

export async function createGroup(data: { name: string; description?: string; teacher_id: number }) {
  const base = getBase();
  const res = await axios.post(`${base}/v1/groups`, data);
  return res.data;
}

export async function deleteGroup(groupId: number) {
  const base = getBase();
  const res = await axios.delete(`${base}/v1/groups/${groupId}`);
  return res.data;
}

export async function addStudentToGroup(groupId: number, payload: { username?: string; student_id?: number }) {
  const base = getBase();
  const res = await axios.post(`${base}/v1/groups/${groupId}/add-student`, payload);
  return res.data;
}

export async function removeStudentFromGroup(groupId: number, studentId: number) {
  const base = getBase();
  const res = await axios.post(`${base}/v1/groups/${groupId}/remove-student/${studentId}`);
  return res.data;
}

export async function joinGroupByCode(code: string, userId: number) {
  const base = getBase();
  const res = await axios.post(`${base}/v1/groups/join`, { code, user_id: userId });
  return res.data;
}

// ==========================================
// Назначение курсов и Cisco/Stepik Gating
// ==========================================

export async function assignCourseToGroup(groupId: number, courseId: number) {
  const base = getBase();
  const res = await axios.post(`${base}/v1/groups/${groupId}/assign-course`, { course_id: courseId });
  return res.data;
}

export async function fetchGroupProgressMatrix(groupId: number, courseId: number) {
  const base = getBase();
  const res = await axios.get(`${base}/v1/groups/${groupId}/progress/${courseId}`);
  return res.data;
}

export async function toggleGroupLessonAccess(
  groupId: number,
  lessonId: number,
  params: { is_unlocked?: boolean; auto_unlock_when_all_pass?: boolean }
) {
  const base = getBase();
  const res = await axios.post(`${base}/v1/groups/${groupId}/lessons/${lessonId}/toggle-access`, params);
  return res.data;
}

export async function completeLesson(lessonId: number, userId: number) {
  const base = getBase();
  const res = await axios.post(`${base}/v1/lessons/${lessonId}/complete`, { user_id: userId });
  return res.data;
}

export async function createCourseLesson(courseId: number, data: {
  title: string;
  content?: string;
  description?: string;
  order?: number;
  block_id?: number;
  lesson_type?: string;
  is_mandatory?: boolean;
}) {
  const base = getBase();
  const res = await axios.post(`${base}/v1/courses/${courseId}/lessons`, data);
  return res.data;
}

export async function deleteLesson(lessonId: number) {
  const base = getBase();
  const res = await axios.delete(`${base}/v1/lessons/${lessonId}`);
  return res.data;
}

// ==========================================
// Блоки курса и импорт Markdown
// ==========================================

export async function fetchCourseBlocks(courseId: number) {
  const base = getBase();
  const res = await axios.get(`${base}/v1/courses/${courseId}/blocks`);
  return res.data;
}

export async function createCourseBlock(courseId: number, data: { title: string; description?: string; order?: number }) {
  const base = getBase();
  const res = await axios.post(`${base}/v1/courses/${courseId}/blocks`, data);
  return res.data;
}

export async function importCourseMarkdown(courseId: number, data: { title?: string; content: string; block_id?: number }) {
  const base = getBase();
  const res = await axios.post(`${base}/v1/courses/${courseId}/import-markdown`, data);
  return res.data;
}

// ==========================================
// Экзамены
// ==========================================

export async function fetchBlockExam(blockId: number, userId?: number) {
  const base = getBase();
  const param = userId ? `?user_id=${userId}` : "";
  const res = await axios.get(`${base}/v1/blocks/${blockId}/exam${param}`);
  return res.data;
}

export async function createOrUpdateBlockExam(blockId: number, data: {
  title: string;
  description?: string;
  passing_score?: number;
  max_attempts?: number;
  questions?: Array<{ text: string; answers: Array<{ text: string; is_correct: boolean }> }>;
}) {
  const base = getBase();
  const res = await axios.post(`${base}/v1/blocks/${blockId}/exam`, data);
  return res.data;
}

export async function fetchExam(examId: number, userId?: number) {
  const base = getBase();
  const param = userId ? `?user_id=${userId}` : "";
  const res = await axios.get(`${base}/v1/exams/${examId}${param}`);
  return res.data;
}

export async function submitExam(examId: number, payload: {
  user_id: number;
  answers: Array<{ question_id: number; answer_id: number }>;
}) {
  const base = getBase();
  const res = await axios.post(`${base}/v1/exams/${examId}/submit`, payload);
  return res.data;
}

// ==========================================
// Кабинет преподавателя (Teacher Dashboard & Students)
// ==========================================

export async function fetchTeacherDashboard() {
  const base = getBase();
  const res = await axios.get(`${base}/v1/teacher/dashboard`);
  return res.data;
}

export async function fetchTeacherStudents(params?: { q?: string; group_id?: number }) {
  const base = getBase();
  const res = await axios.get(`${base}/v1/teacher/students`, { params });
  return res.data;
}

export async function quickCreateStudent(payload: { first_name: string; last_name: string; group_id?: number }) {
  const base = getBase();
  const res = await axios.post(`${base}/v1/teacher/students/quick-create`, payload);
  return res.data;
}

export async function fetchTeacherStudentDetail(studentId: number) {
  const base = getBase();
  const res = await axios.get(`${base}/v1/teacher/students/${studentId}`);
  return res.data;
}

export async function resetStudentPassword(studentId: number) {
  const base = getBase();
  const res = await axios.post(`${base}/v1/teacher/students/${studentId}/reset-password`);
  return res.data;
}

export async function resetStudentProgress(studentId: number, courseId?: number) {
  const base = getBase();
  const res = await axios.post(`${base}/v1/teacher/students/${studentId}/reset-progress`, { course_id: courseId });
  return res.data;
}

export async function toggleStudentStatus(studentId: number) {
  const base = getBase();
  const res = await axios.post(`${base}/v1/teacher/students/${studentId}/toggle-status`);
  return res.data;
}
