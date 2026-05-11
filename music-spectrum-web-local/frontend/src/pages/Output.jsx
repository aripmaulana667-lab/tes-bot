import { useEffect, useState } from 'react';
import { api } from '../lib/api.js';
import { useToast } from '../hooks/useToast.jsx';

function bytesToReadable(n) {
  if (!n) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0; let v = n;
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i += 1; }
  return `${v.toFixed(1)} ${units[i]}`;
}

export default function Output() {
  const [items, setItems] = useState([]);
  const [active, setActive] = useState(null);
  const toast = useToast();

  const reload = async () => {
    try { setItems(await api.outputs()); } catch (e) { toast?.({ kind: 'error', title: 'Gagal memuat', message: e.message }); }
  };
  useEffect(() => { reload(); }, []);

  const remove = async (name) => {
    if (!confirm(`Hapus ${name}?`)) return;
    try {
      await api.deleteOutput(name);
      toast?.({ kind: 'success', title: 'Dihapus', message: name });
      reload();
    } catch (e) {
      toast?.({ kind: 'error', title: 'Gagal hapus', message: e.message });
    }
  };

  return (
    <div>
      <div className="page-title">
        <div>
          <h1>Output</h1>
          <div className="subtitle">Daftar video hasil render di storage/outputs.</div>
        </div>
        <div className="row tight">
          <button onClick={reload}>Muat ulang</button>
          <button onClick={() => api.openOutputFolder().catch(() => {})}>Buka folder</button>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="card">Belum ada file output.</div>
      ) : (
        <div className="grid cols-2">
          <div className="card">
            <h3>Daftar file</h3>
            <table>
              <thead><tr><th>Nama</th><th>Ukuran</th><th></th></tr></thead>
              <tbody>
                {items.map((it) => (
                  <tr key={it.name}>
                    <td><a href="#" onClick={(e) => { e.preventDefault(); setActive(it.name); }}>{it.name}</a></td>
                    <td>{bytesToReadable(it.size)}</td>
                    <td className="row tight">
                      <a href={`/api/outputs/${encodeURIComponent(it.name)}/download`}>
                        <button className="small">Download</button>
                      </a>
                      <button className="small danger" onClick={() => remove(it.name)}>Hapus</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {active && (
            <div className="card">
              <h3>{active}</h3>
              <video controls src={`/storage/outputs/${encodeURIComponent(active)}`} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
