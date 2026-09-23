// Если VITE_API_URL пустой, берем корень сайта (в dev работает Vite proxy, в prod — Nginx).
export const API_URL = import.meta.env.VITE_API_URL || (typeof window !== 'undefined' ? window.location.origin : '');

const getBase = () => API_URL.replace(/\/$/, '');

export async function getUsers() {
  const res = await fetch(`${getBase()}/api/users`); 
  if (!res.ok) {
    throw new Error("Failed to fetch users");
  }
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

export async function fetchCourses(query?: string, timestamp?: number) {
  const urlStr = `${getBase()}/api/v1/courses`;
  
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
    if (Array.isArray(data)) {
      return data;
    }
    if (data && Array.isArray(data.data)) {
      return data.data;
    }
    if (data && Array.isArray(data.results)) {
      return data.results;
    }
    if (data && Array.isArray(data.courses)) {
      return data.courses;
    }
    return [];
  } catch (e) {
    console.error("Fetch courses error:", e);
    throw e;
  }
}
