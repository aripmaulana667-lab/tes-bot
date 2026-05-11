import { useCallback, useEffect, useState } from 'react';
import { NavLink, Route, Routes } from 'react-router-dom';
import { api } from './lib/api.js';
import { ToastProvider } from './hooks/useToast.jsx';
import Dashboard from './pages/Dashboard.jsx';
import SingleRender from './pages/SingleRender.jsx';
import BatchRender from './pages/BatchRender.jsx';
import Preview from './pages/Preview.jsx';
import Output from './pages/Output.jsx';

export default function App() {
  const [ffmpeg, setFfmpeg] = useState(null);
  const [styles, setStyles] = useState([]);

  const refresh = useCallback(async () => {
    try {
      const [status, health] = await Promise.all([api.ffmpegStatus(), api.health()]);
      setFfmpeg(status);
      setStyles(health.spectrum_styles || []);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 15000);
    return () => clearInterval(t);
  }, [refresh]);

  return (
    <ToastProvider>
      <div className="app">
        <header className="header">
          <div className="brand">
            <div className="dot" />
            <div>
              <div>Music Spectrum Lyrics Studio</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 400 }}>Local FFmpeg renderer</div>
            </div>
          </div>
          <div>
            {ffmpeg?.available ? (
              <span className="status-pill ok"><span className="dot" /> FFmpeg: {ffmpeg.source}</span>
            ) : (
              <span className="status-pill err"><span className="dot" /> FFmpeg belum siap</span>
            )}
          </div>
        </header>

        <aside className="sidebar">
          <div className="nav-section">Menu</div>
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/single">Single Render</NavLink>
          <NavLink to="/batch">Batch Render</NavLink>
          <NavLink to="/preview">Preview</NavLink>
          <NavLink to="/output">Output</NavLink>
          <div className="footer" style={{ marginTop: 20 }}>
            v1.0.0 — lokal, offline-ready
          </div>
        </aside>

        <main className="content">
          <Routes>
            <Route path="/" element={<Dashboard ffmpeg={ffmpeg} onRefreshFfmpeg={refresh} />} />
            <Route path="/single" element={<SingleRender ffmpeg={ffmpeg} styles={styles} />} />
            <Route path="/batch" element={<BatchRender ffmpeg={ffmpeg} styles={styles} />} />
            <Route path="/preview" element={<Preview />} />
            <Route path="/output" element={<Output />} />
          </Routes>
        </main>
      </div>
    </ToastProvider>
  );
}
