import { useEffect, useMemo, useState } from 'react';
import { createWS } from '../lib/ws.js';
import { api } from '../lib/api.js';

export function useJobs() {
  const [jobs, setJobs] = useState({});
  const [logs, setLogs] = useState({});

  useEffect(() => {
    let cancelled = false;
    api.jobs().then((items) => {
      if (cancelled) return;
      const map = {};
      items.forEach((j) => { map[j.id] = j; });
      setJobs(map);
    }).catch(() => {});

    const close = createWS((msg) => {
      if (msg.type === 'snapshot') {
        const map = {};
        (msg.jobs || []).forEach((j) => { map[j.id] = j; });
        setJobs(map);
      } else if (msg.type === 'job') {
        setJobs((cur) => ({ ...cur, [msg.job.id]: msg.job }));
        if (msg.log) {
          setLogs((cur) => {
            const next = (cur[msg.job.id] || []).concat([msg.log]);
            return { ...cur, [msg.job.id]: next.slice(-500) };
          });
        }
      }
    });

    return () => { cancelled = true; close(); };
  }, []);

  const list = useMemo(() => Object.values(jobs).sort((a, b) => b.created_at - a.created_at), [jobs]);
  return { jobs, list, logs };
}
