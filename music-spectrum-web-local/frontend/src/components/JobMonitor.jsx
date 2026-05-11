import { useEffect, useState } from 'react';
import { api } from '../lib/api.js';
import JobBadge from './JobBadge.jsx';

export default function JobMonitor({ job, logs = [], onClose }) {
  const [logText, setLogText] = useState(logs.join('\n'));

  useEffect(() => setLogText(logs.join('\n')), [logs]);

  if (!job) return null;

  return (
    <div className="card" style={{ marginTop: 16 }}>
      <div className="row" style={{ alignItems: 'center' }}>
        <div style={{ flex: 1 }}>
          <h3 style={{ marginBottom: 4 }}>Job {job.id} <JobBadge status={job.status} /></h3>
          <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>{job.message || ''}</div>
        </div>
        <div className="row tight" style={{ flex: 0 }}>
          {job.status === 'rendering' && (
            <button className="danger small" onClick={() => api.jobCancel(job.id).catch(() => {})}>
              Batalkan
            </button>
          )}
          {job.status === 'done' && job.output_file && (
            <>
              <a className="button" href={`/api/outputs/${encodeURIComponent(job.output_file)}/download`}>
                <button className="primary small">Download</button>
              </a>
            </>
          )}
          {onClose && <button className="small ghost" onClick={onClose}>Tutup</button>}
        </div>
      </div>
      <div className="progress" style={{ marginTop: 12 }}>
        <div className="bar" style={{ width: `${Math.round((job.progress || 0) * 100)}%` }} />
      </div>
      <div style={{ marginTop: 8, fontSize: 12, color: 'var(--text-muted)' }}>
        Progress: {Math.round((job.progress || 0) * 100)}%
      </div>
      {logText && (
        <div className="log-panel" style={{ marginTop: 12 }}>
          {logText}
        </div>
      )}
    </div>
  );
}
