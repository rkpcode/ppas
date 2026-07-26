const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export async function apiFetch(path, options = {}) {
  const token = localStorage.getItem('pdh_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    localStorage.removeItem('pdh_token');
    window.location.href = '/';
    return;
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }

  return res.json();
}

export async function apiFetchForm(path, formData) {
  const token = localStorage.getItem('pdh_token');
  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (res.status === 401) {
    localStorage.removeItem('pdh_token');
    window.location.href = '/';
    return;
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }

  return res.json();
}
