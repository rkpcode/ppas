import { apiFetch } from './client';

function extractErrorMsg(err, defaultMsg) {
  if (!err) return defaultMsg;
  if (typeof err.detail === 'string') return err.detail;
  if (Array.isArray(err.detail) && err.detail.length > 0) {
    return err.detail[0].msg || err.detail[0].detail || defaultMsg;
  }
  if (err.message) return err.message;
  return defaultMsg;
}

export async function login(username, password) {
  const form = new URLSearchParams();
  form.append('username', username);
  form.append('password', password);

  const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
  const res = await fetch(`${BASE_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form.toString(),
  });

  if (!res.ok) {
    if (res.status === 503) {
      throw new Error('Server update chal raha hai, please wait 1-2 minutes.');
    }
    const err = await res.json().catch(() => null);
    throw new Error(extractErrorMsg(err, 'Login failed'));
  }

  const data = await res.json();
  return data;
}

export async function getMe() {
  return apiFetch('/api/v1/auth/me');
}

export async function register(userData) {
  const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
  const res = await fetch(`${BASE_URL}/api/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData),
  });

  if (!res.ok) {
    if (res.status === 503) {
      throw new Error('Server update chal raha hai, please wait 1-2 minutes.');
    }
    const err = await res.json().catch(() => null);
    throw new Error(extractErrorMsg(err, 'Registration failed'));
  }

  return res.json();
}
