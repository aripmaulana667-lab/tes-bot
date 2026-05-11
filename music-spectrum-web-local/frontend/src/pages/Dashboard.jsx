import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api.js';
import { useToast } from '../hooks/useToast.jsx';
import { useJobs } from '../hooks/useJobs.jsx';
import JobBadge from '../components/JobBadge.jsx';

export default function Dashboard({ ffmpeg, onRefreshFfmpeg }) {
  const [installing, setInstalling] = useState(false);
  const [counts, setCounts] = useState({ music: 0, lyrics: 0, backgrounds: 0, logos: 0, outputs: 0 });
  const { list } = useJobs();
  const toast = useToast();

  const reload = async () => {
    try {
      const [m, l, b, lg, o] = await Promise.all([
        api.listAssets('music'),
        api.listAssets('lyrics'),
        api.listAssets('backgrounds'),
        api.listAssets('logos'),
        api.outputs(),
      ]);
      setCounts({ music: m.length, lyrics: l.length, backgrounds: b.length, logos: lg.length, outputs: o.length });
    } catch { /* ignore */ }
  };
  useEffect(() => { reload(); }, []);

  const onInstall = async () => {
    setInstalling(true);
    try {
      const res = await api.installFfmpeg();
      toast?.({ kind: 'success', title: 'FFmpeg siap', message: res.status?.version || 'Berhasil dipasang.' });
      onRefreshFfmpeg?.();
    } catch (e) {
      toast?.({ kind: 'error', title: 'Instalasi gagal', message: e.message });
    }
    setInstalling(false);
  };

  return (
    <div>
      <div className="page-title">
        <div>
          <h1>Dashboard</h1>
          <div className="subtitle">Ringkasan status aplikasi dan akses cepat.</div>
        </div>
      </div>

      <div className="grid cols-2">
        <div className="card">
          <h3>Status FFmpeg</h3>
          {!ffmpeg ? (
            <div className="subtitle">Memuat ...</div>
          ) : ffmpeg.available ? (
            <>
              <div className="row"><JobBadge status="done" /> <span>{ffmpeg.source.toUpperCase()}</span></div>
              <div style={{ marginTop: 8, fontSize: 12, color: 'var(--text-muted)' }}>{ffmpeg.path}</div>
              <div style={{ marginTop: 4, fontSize: 12, color: 'var(--text-muted)' }}>{ffmpeg.version}</div>
            </>
          ) : (
            <>
              <div className="row"><JobBadge status="failed" /> <span>FFmpeg belum tersedia</span></div>
              <div style={{ marginTop: 8, fontSize: 12, color: 'var(--text-muted)' }}>{ffmpeg.error}</div>
              <button className="primary" disabled={installing} onClick={onInstall} style={{ marginTop: 12 }}>
                {installing ? 'Mengunduh FFmpeg portable ...' : 'Install FFmpeg portable'}
              </button>
            </>
          )}
        </div>

        <div className="card">
          <h3>Storage lokal</h3>
          <table>
            <tbody>
              <tr><td>Musik</td><td>{counts.music}</td></tr>
              <tr><td>Lirik</td><td>{counts.lyrics}</td></tr>
              <tr><td>Background</td><td>{counts.backgrounds}</td></tr>
              <tr><td>Logo</td><td>{counts.logos}</td></tr>
              <tr><td>Output</td><td>{counts.outputs}</td></tr>
            </tbody>
          </table>
        </div>

        <div className="card">
          <h3>Aksi cepat</h3>
          <div className="row">
            <Link to="/single"><button className="primary">Single Render</button></Link>
            <Link to="/batch"><button>Batch Render</button></Link>
            <Link to="/output"><button>Buka Output</button></Link>
          </div>
          <div style={{ marginTop: 12 }}>
            <button className="ghost" onClick={() => api.openOutputFolder().catch(() => {})}>
              Buka folder output di Explorer
            </button>
          </div>
        </div>

        <div className="card">
          <h3>Job terbaru</h3>
          {list.length === 0 ? (
            <div className="subtitle">Belum ada job render.</div>
          ) : (
            <table>
              <thead><tr><th>ID</th><th>Tipe</th><th>Status</th><th>Pesan</th></tr></thead>
              <tbody>
                {list.slice(0, 6).map((j) => (
                  <tr key={j.id}>
                    <td>{j.id}</td>
                    <td>{j.kind}</td>
                    <td><JobBadge status={j.status} /></td>
                    <td>{j.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
