import { useEffect, useState } from 'react';
import { api } from '../lib/api.js';
import { defaultRenderForm } from '../lib/defaults.js';
import RenderControls from '../components/RenderControls.jsx';
import JobMonitor from '../components/JobMonitor.jsx';
import { useToast } from '../hooks/useToast.jsx';
import { useJobs } from '../hooks/useJobs.jsx';

export default function SingleRender({ ffmpeg, styles }) {
  const [form, setForm] = useState(defaultRenderForm);
  const [previewJobId, setPreviewJobId] = useState(null);
  const [fullJobId, setFullJobId] = useState(null);
  const toast = useToast();
  const { jobs, logs } = useJobs();

  // Load persisted form
  useEffect(() => {
    try {
      const saved = localStorage.getItem('msls.singleForm');
      if (saved) setForm(JSON.parse(saved));
    } catch { /* ignore */ }
  }, []);
  useEffect(() => {
    try { localStorage.setItem('msls.singleForm', JSON.stringify(form)); } catch { /* ignore */ }
  }, [form]);

  const validate = () => {
    if (!form.music_file) return 'Pilih file musik dulu.';
    if (!ffmpeg?.available) return 'FFmpeg belum tersedia. Install dulu dari Dashboard.';
    return null;
  };

  const submit = async (kind) => {
    const err = validate();
    if (err) { toast?.({ kind: 'error', title: 'Belum lengkap', message: err }); return; }
    try {
      const fn = kind === 'preview' ? api.renderPreview : api.renderFull;
      const job = await fn(form);
      if (kind === 'preview') setPreviewJobId(job.id);
      else setFullJobId(job.id);
      toast?.({ kind: 'success', title: 'Render dimulai', message: `Job ${job.id}` });
    } catch (e) {
      toast?.({ kind: 'error', title: 'Gagal render', message: e.message });
    }
  };

  const previewJob = previewJobId ? jobs[previewJobId] : null;
  const fullJob = fullJobId ? jobs[fullJobId] : null;

  return (
    <div>
      <div className="page-title">
        <div>
          <h1>Single Render</h1>
          <div className="subtitle">Atur lirik, spectrum, dan background untuk satu lagu.</div>
        </div>
        <div className="row tight">
          <button onClick={() => submit('preview')}>Preview 10 detik</button>
          <button className="primary" onClick={() => submit('full')}>Render full</button>
        </div>
      </div>

      <RenderControls form={form} setForm={setForm} styles={styles} />

      {previewJob && (
        <JobMonitor job={previewJob} logs={logs[previewJob.id] || []} onClose={() => setPreviewJobId(null)} />
      )}
      {fullJob && (
        <JobMonitor job={fullJob} logs={logs[fullJob.id] || []} onClose={() => setFullJobId(null)} />
      )}
    </div>
  );
}
