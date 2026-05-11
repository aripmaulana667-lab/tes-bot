import { useEffect, useRef, useState } from 'react';
import { api } from '../lib/api.js';
import { useToast } from '../hooks/useToast.jsx';

export default function FilePicker({
  category, value, onChange, accept, label, multi = false, values = [], onValuesChange,
}) {
  const [items, setItems] = useState([]);
  const [over, setOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const ref = useRef(null);
  const toast = useToast();

  const reload = async () => {
    try { setItems(await api.listAssets(category)); } catch { /* ignore */ }
  };

  useEffect(() => { reload(); }, [category]);

  const upload = async (file) => {
    setUploading(true);
    try {
      const data = await api.uploadAsset(category, file);
      await reload();
      if (multi) {
        onValuesChange?.([...(values || []), data.name]);
      } else {
        onChange?.(data.name);
      }
      toast?.({ kind: 'success', title: 'Berhasil', message: `${data.name} terunggah.` });
    } catch (e) {
      toast?.({ kind: 'error', title: 'Gagal unggah', message: e.message });
    }
    setUploading(false);
  };

  const handleFiles = async (files) => {
    for (const f of files) {
      await upload(f);
    }
  };

  return (
    <div className="field">
      <label>{label}</label>
      <div
        className={`dropzone ${over ? 'over' : ''} ${(value || (multi && values?.length)) ? 'has-file' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setOver(true); }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setOver(false);
          if (e.dataTransfer.files?.length) handleFiles([...e.dataTransfer.files]);
        }}
        onClick={() => ref.current?.click()}
        role="button"
      >
        {uploading
          ? 'Mengunggah ...'
          : multi
            ? (values?.length ? <span className="name">{values.length} file dipilih</span> : 'Drop / klik untuk unggah (bisa multi)')
            : (value ? <span className="name">{value}</span> : 'Drop file atau klik untuk pilih')}
        <input
          ref={ref}
          type="file"
          accept={accept}
          multiple={multi}
          style={{ display: 'none' }}
          onChange={(e) => { if (e.target.files?.length) handleFiles([...e.target.files]); }}
        />
      </div>

      {items.length > 0 && (
        <select
          style={{ marginTop: 8 }}
          value={multi ? '' : (value || '')}
          onChange={(e) => {
            if (!e.target.value) return;
            if (multi) {
              if (!values?.includes(e.target.value)) onValuesChange?.([...(values || []), e.target.value]);
            } else {
              onChange?.(e.target.value);
            }
          }}
        >
          <option value="">— Pilih dari folder {category} —</option>
          {items.map((it) => (
            <option key={it.name} value={it.name}>{it.name}</option>
          ))}
        </select>
      )}

      {multi && values?.length > 0 && (
        <div className="file-list" style={{ marginTop: 8 }}>
          {values.map((n) => (
            <div className="row" key={n}>
              <span style={{ flex: 1 }}>{n}</span>
              <button className="ghost small" onClick={() => onValuesChange?.(values.filter((x) => x !== n))}>Hapus</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
