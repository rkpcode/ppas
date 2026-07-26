import { apiFetch } from './client';

export async function getInventory(search = '') {
  const query = search ? `?search=${encodeURIComponent(search)}` : '';
  return apiFetch(`/api/v1/inventory/${query}`);
}
