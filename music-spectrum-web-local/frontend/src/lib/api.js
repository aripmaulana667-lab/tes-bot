const BASE = '/api';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    let detail;
    try {
      detail = (await res.json()).detail;
    } catch {
      detail = await res.text();
    }
    throw new Error(detail || `${res.status} ${res.statusText}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  health: () => request('/health'),
  ffmpegStatus: () => request('/ffmpeg/status'),
  installFfmpeg: () => request('/ffmpeg/install', { method: 'POST' }),
  listAssets: (cat) => request(`/assets/${cat}`),
  uploadAsset: async (cat, file) => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${BASE}/assets/${cat}`, { method: 'POST', body: form });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail.detail || res.statusText);
    }
    return res.json();
  },
  deleteAsset: (cat, name) => request(`/assets/${cat}/${encodeURIComponent(name)}`, { method: 'DELETE' }),
  renderPreview: (body) => request('/render/preview', { method: 'POST', body: JSON.stringify(body) }),
  renderFull: (body) => request('/render/full', { method: 'POST', body: JSON.stringify(body) }),
  renderBatch: (body) => request('/render/batch', { method: 'POST', body: JSON.stringify(body) }),
  jobStatus: (id) => request(`/render/${id}/status`),
  jobLog: (id) => request(`/render/${id}/log`),
  jobCancel: (id) => request(`/render/${id}/cancel`, { method: 'POST' }),
  jobs: () => request('/render/jobs'),
  outputs: () => request('/outputs'),
  deleteOutput: (name) => request(`/outputs/${encodeURIComponent(name)}`, { method: 'DELETE' }),
  openOutputFolder: () => request('/outputs/open-folder', { method: 'POST' }),
};
