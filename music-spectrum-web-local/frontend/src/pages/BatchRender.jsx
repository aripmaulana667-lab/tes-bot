import { useEffect, useState } from 'react';
import { api } from '../lib/api.js';
import { defaultBatchForm } from '../lib/defaults.js';
import { useToast } from '../hooks/useToast.jsx';
import { useJobs } from '../hooks/useJobs.jsx';
import SpectrumStyles from '../components/SpectrumStyles.jsx';
import JobBadge from '../components/JobBadge.jsx';
import JobMonitor from '../components/JobMonitor.jsx';

export default function BatchRender({ styles, ffmpeg }) {
  const [form, setForm] = useState(defaultBatchForm);
  const [batchJobId, setBatchJobId] = useState(null);
  const { jobs, list, logs } = useJobs();
  const toast = useToast();

  useEffect(() => {
    try {
      const saved = localStorage.getItem('msls.batchForm');
      if (saved) setForm(JSON.parse(saved));
    } catch { /* ignore */ }
  }, []);
  useEffect(() => {
    try { localStorage.setItem('msls.batchForm', JSON.stringify(form)); } catch { /* ignore */ }
  }, [form]);

  const set = (path, value) => {
    setForm((f) => {
      const next = structuredClone(f);
      const keys = path.split('.');
      let cur = next;
      for (let i = 0; i < keys.length - 1; i += 1) cur = cur[keys[i]];
      cur[keys[keys.length - 1]] = value;
      return next;
    });
  };

  const start = async () => {
    if (!ffmpeg?.available) {
      toast?.({ kind: 'error', title: 'FFmpeg belum siap', message: 'Install FFmpeg dulu.' });
      return;
    }
    try {
      const job = await api.renderBatch(form);
      setBatchJobId(job.id);
      toast?.({ kind: 'success', title: 'Batch dimulai', message: `Job ${job.id}` });
    } catch (e) {
      toast?.({ kind: 'error', title: 'Gagal batch', message: e.message });
    }
  };

  const parent = batchJobId ? jobs[batchJobId] : null;
  const children = parent ? list.filter((j) => j.parent_id === parent.id) : [];

  return (
    <div>
      <div className="page-title">
        <div>
          <h1>Batch Render</h1>
          <div className="subtitle">Render banyak lagu sekaligus dari folder lokal.</div>
        </div>
        <button className="primary" onClick={start}>Mulai batch</button>
      </div>

      <div className="grid cols-2">
        <div className="card">
          <h3>1. Folder</h3>
          <div className="field">
            <label>Folder musik (nama subfolder di storage/music atau path absolut)</label>
            <input value={form.music_dir} onChange={(e) => set('music_dir', e.target.value)} />
          </div>
          <div className="field">
            <label>Folder lirik</label>
            <input value={form.lyrics_dir} onChange={(e) => set('lyrics_dir', e.target.value)} />
          </div>
          <div className="field">
            <label>Folder background</label>
            <input value={form.background_dir} onChange={(e) => set('background_dir', e.target.value)} />
          </div>
        </div>

        <div className="card">
          <h3>2. Mode pencocokan background</h3>
          <div className="field">
            <label>Mode</label>
            <select value={form.match_mode} onChange={(e) => set('match_mode', e.target.value)}>
              <option value="sequence">Sesuai urutan file</option>
              <option value="by_name">Sesuai nama musik</option>
              <option value="random">Random</option>
            </select>
          </div>
          {(form.match_mode !== 'by_name') && (
            <div className="field">
              <label>
                <input type="checkbox" checked={form.multi_background}
                  onChange={(e) => set('multi_background', e.target.checked)} /> Banyak background per video (slideshow)
              </label>
            </div>
          )}
          <div className="row">
            <div className="field">
              <label>Durasi tiap gambar (detik)</label>
              <input type="number" min="0.5" step="0.5"
                value={form.background.slideshow_duration}
                onChange={(e) => set('background.slideshow_duration', Number(e.target.value))} />
            </div>
            <div className="field">
              <label>Dark overlay ({Math.round(form.background.dark_overlay * 100)}%)</label>
              <input type="range" min="0" max="0.8" step="0.05"
                value={form.background.dark_overlay}
                onChange={(e) => set('background.dark_overlay', Number(e.target.value))} />
            </div>
            <div className="field">
              <label>Blur ({form.background.blur})</label>
              <input type="range" min="0" max="20" step="1"
                value={form.background.blur}
                onChange={(e) => set('background.blur', Number(e.target.value))} />
            </div>
          </div>
        </div>

        <div className="card">
          <h3>3. Spectrum & lirik</h3>
          <SpectrumStyles styles={styles} value={form.spectrum.style} onChange={(v) => set('spectrum.style', v)} />
          <div className="row" style={{ marginTop: 12 }}>
            <div className="field">
              <label>Ukuran font lirik</label>
              <input type="number" value={form.lyrics.font_size}
                onChange={(e) => set('lyrics.font_size', Number(e.target.value))} />
            </div>
            <div className="field">
              <label>Warna lirik</label>
              <input type="color" value={form.lyrics.color}
                onChange={(e) => set('lyrics.color', e.target.value)} />
            </div>
            <div className="field">
              <label>Offset (ms)</label>
              <input type="number" value={form.lyrics.offset_ms}
                onChange={(e) => set('lyrics.offset_ms', Number(e.target.value))} />
            </div>
          </div>
        </div>

        <div className="card">
          <h3>4. Render</h3>
          <div className="row">
            <div className="field">
              <label>Resolusi</label>
              <select value={form.render.resolution} onChange={(e) => set('render.resolution', e.target.value)}>
                <option value="1280x720">1280×720 (720p)</option>
                <option value="1920x1080">1920×1080 (1080p)</option>
                <option value="720x1280">720×1280 (vertikal HD)</option>
                <option value="1080x1920">1080×1920 (vertikal FHD)</option>
                <option value="1080x1080">1080×1080 (square)</option>
              </select>
            </div>
            <div className="field">
              <label>FPS</label>
              <select value={form.render.fps} onChange={(e) => set('render.fps', Number(e.target.value))}>
                <option value={24}>24</option>
                <option value={30}>30</option>
                <option value={60}>60</option>
              </select>
            </div>
            <div className="field">
              <label>Preset</label>
              <select value={form.render.preset} onChange={(e) => set('render.preset', e.target.value)}>
                <option value="ultrafast">ultrafast</option>
                <option value="veryfast">veryfast</option>
                <option value="faster">faster</option>
                <option value="fast">fast</option>
                <option value="medium">medium</option>
              </select>
            </div>
            <div className="field">
              <label>CRF ({form.render.crf})</label>
              <input type="range" min="14" max="35" step="1"
                value={form.render.crf}
                onChange={(e) => set('render.crf', Number(e.target.value))} />
            </div>
          </div>
        </div>
      </div>

      {parent && (
        <JobMonitor job={parent} logs={logs[parent.id] || []} onClose={() => setBatchJobId(null)} />
      )}

      {parent && children.length > 0 && (
        <div className="card" style={{ marginTop: 16 }}>
          <h3>Antrian batch</h3>
          <table>
            <thead><tr><th>Musik</th><th>Status</th><th>Pesan</th><th>Output</th></tr></thead>
            <tbody>
              {children.map((c) => (
                <tr key={c.id}>
                  <td>{c.music_file || c.id}</td>
                  <td><JobBadge status={c.status} /></td>
                  <td>{c.message}{c.error ? ` — ${c.error}` : ''}</td>
                  <td>
                    {c.output_file ? (
                      <a href={`/api/outputs/${encodeURIComponent(c.output_file)}/download`}>
                        <button className="small">Download</button>
                      </a>
                    ) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
