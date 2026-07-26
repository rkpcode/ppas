import { apiFetch, apiFetchForm } from './client';

export async function parseReceipt(imageFile) {
  const formData = new FormData();
  formData.append('file', imageFile);
  return apiFetchForm('/api/v1/stock/parse-receipt', formData);
}

export async function parseStockVoice(audioBlob, text) {
  const formData = new FormData();
  if (audioBlob) formData.append('file', audioBlob);
  if (text) formData.append('text', text);
  return apiFetchForm('/api/v1/stock/parse-voice', formData);
}

export async function createMedicine(data) {
  return apiFetch('/api/v1/stock/medicines', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateMedicine(id, data) {
  return apiFetch(`/api/v1/stock/medicines/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function addBatch(medicineId, data) {
  return apiFetch(`/api/v1/stock/medicines/${medicineId}/batches`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateBatch(batchId, data) {
  return apiFetch(`/api/v1/stock/batches/${batchId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function confirmBulkStock(items) {
  return apiFetch('/api/v1/stock/confirm-bulk', {
    method: 'POST',
    body: JSON.stringify({ items }),
  });
}
