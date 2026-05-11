import { useMemo } from 'react';
import { useJobs } from '../hooks/useJobs.jsx';
import JobBadge from '../components/JobBadge.jsx';

export default function Preview() {
  const { list } = useJobs();
  const previews = useMemo(() => list.filter((j) => j.kind === 'preview' && j.output_file), [list]);

  return (
    <div>
      <div className="page-title">
        <div>
          <h1>Preview</h1>
          <div className="subtitle">Putar hasil preview 10 detik sebelum render full.</div>
        </div>
      </div>

      {previews.length === 0 ? (
        <div className="card">Belum ada preview. Buka <b>Single Render</b> lalu klik <i>Preview 10 detik</i>.</div>
      ) : (
        <div className="grid cols-2">
          {previews.map((p) => (
            <div className="card" key={p.id}>
              <div className="row" style={{ marginBottom: 8 }}>
                <strong style={{ flex: 1 }}>{p.output_file}</strong>
                <JobBadge status={p.status} />
              </div>
              <video controls src={`/storage/outputs/${encodeURIComponent(p.output_file)}`} />
              <div className="row" style={{ marginTop: 8 }}>
                <a href={`/api/outputs/${encodeURIComponent(p.output_file)}/download`}>
                  <button className="primary small">Download</button>
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
