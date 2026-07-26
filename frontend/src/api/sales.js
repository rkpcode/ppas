import { apiFetch, apiFetchForm } from './client';

export async function parseVoice(audioBlob) {
  const formData = new FormData();
  formData.append('file', audioBlob, 'voice.webm');
  return apiFetchForm('/api/v1/sales/parse-voice', formData);
}

export async function parseVoiceText(text) {
  const formData = new FormData();
  formData.append('text', text);
  return apiFetchForm('/api/v1/sales/parse-voice', formData);
}

export async function confirmSale(payload) {
  return apiFetch('/api/v1/sales/confirm', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getSalesHistory(limit = 20) {
  return apiFetch(`/api/v1/sales/history?limit=${limit}`);
}
