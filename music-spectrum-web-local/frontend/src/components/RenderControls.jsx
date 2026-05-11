import FilePicker from './FilePicker.jsx';
import SpectrumStyles from './SpectrumStyles.jsx';

export default function RenderControls({ form, setForm, styles }) {
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

  return (
    <div className="grid cols-2">
      <div className="card">
        <h3>1. Sumber</h3>
        <FilePicker
          category="music"
          value={form.music_file}
          onChange={(v) => set('music_file', v)}
          label="File musik (mp3/wav/flac)"
          accept="audio/*"
        />
        <FilePicker
          category="lyrics"
          value={form.lyrics.file}
          onChange={(v) => set('lyrics.file', v)}
          label="File lirik .lrc"
          accept=".lrc,.txt"
        />
        <FilePicker
          category="logos"
          value={form.logo.file}
          onChange={(v) => set('logo.file', v)}
          label="Logo (opsional)"
          accept="image/*"
        />
      </div>

      <div className="card">
        <h3>2. Background</h3>
        <div className="field">
          <label>Mode</label>
          <select value={form.background.mode} onChange={(e) => set('background.mode', e.target.value)}>
            <option value="single">Single background</option>
            <option value="multiple">Banyak background (slideshow)</option>
          </select>
        </div>
        <FilePicker
          category="backgrounds"
          multi={form.background.mode === 'multiple'}
          value={form.background.files[0]}
          onChange={(v) => set('background.files', v ? [v] : [])}
          values={form.background.files}
          onValuesChange={(v) => set('background.files', v)}
          label="File background (gambar/video)"
          accept="image/*,video/*"
        />
        <div className="row">
          <div className="field">
            <label>Durasi tiap gambar (detik)</label>
            <input type="number" min="0.5" step="0.5"
              value={form.background.slideshow_duration}
              onChange={(e) => set('background.slideshow_duration', Number(e.target.value))} />
          </div>
          <div className="field" style={{ alignSelf: 'end' }}>
            <label>
              <input type="checkbox" checked={form.background.randomize}
                onChange={(e) => set('background.randomize', e.target.checked)} /> Acak background
            </label>
          </div>
        </div>
        <div className="row">
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
        <h3>3. Lirik</h3>
        <div className="row">
          <div className="field">
            <label>Offset (ms)</label>
            <input type="number" value={form.lyrics.offset_ms}
              onChange={(e) => set('lyrics.offset_ms', Number(e.target.value))} />
          </div>
          <div className="field">
            <label>Font</label>
            <input value={form.lyrics.font} onChange={(e) => set('lyrics.font', e.target.value)} />
          </div>
        </div>
        <div className="row">
          <div className="field">
            <label>Ukuran font</label>
            <input type="number" value={form.lyrics.font_size}
              onChange={(e) => set('lyrics.font_size', Number(e.target.value))} />
          </div>
          <div className="field">
            <label>Jarak bawah</label>
            <input type="number" value={form.lyrics.bottom_margin}
              onChange={(e) => set('lyrics.bottom_margin', Number(e.target.value))} />
          </div>
        </div>
        <div className="row">
          <div className="field">
            <label>Warna</label>
            <input type="color" value={form.lyrics.color}
              onChange={(e) => set('lyrics.color', e.target.value)} />
          </div>
          <div className="field">
            <label>Outline</label>
            <input type="color" value={form.lyrics.outline_color}
              onChange={(e) => set('lyrics.outline_color', e.target.value)} />
          </div>
          <div className="field">
            <label>Shadow</label>
            <input type="color" value={form.lyrics.shadow_color}
              onChange={(e) => set('lyrics.shadow_color', e.target.value)} />
          </div>
        </div>
        <div className="row">
          <div className="field">
            <label>Opacity ({Math.round(form.lyrics.opacity * 100)}%)</label>
            <input type="range" min="0.2" max="1" step="0.05"
              value={form.lyrics.opacity}
              onChange={(e) => set('lyrics.opacity', Number(e.target.value))} />
          </div>
          <div className="field">
            <label>Fade (ms)</label>
            <input type="number" min="0" value={form.lyrics.fade_ms}
              onChange={(e) => set('lyrics.fade_ms', Number(e.target.value))} />
          </div>
        </div>
      </div>

      <div className="card">
        <h3>4. Spectrum</h3>
        <SpectrumStyles styles={styles} value={form.spectrum.style} onChange={(v) => set('spectrum.style', v)} />
        <div className="row" style={{ marginTop: 12 }}>
          <div className="field">
            <label>Tinggi spectrum ({form.spectrum.height} px)</label>
            <input type="range" min="60" max="300" step="10"
              value={form.spectrum.height}
              onChange={(e) => set('spectrum.height', Number(e.target.value))} />
          </div>
          <div className="field">
            <label>Kepadatan ({form.spectrum.density})</label>
            <input type="range" min="20" max="240" step="2"
              value={form.spectrum.density}
              onChange={(e) => set('spectrum.density', Number(e.target.value))} />
          </div>
          <div className="field">
            <label>Opacity ({Math.round(form.spectrum.opacity * 100)}%)</label>
            <input type="range" min="0.2" max="1" step="0.05"
              value={form.spectrum.opacity}
              onChange={(e) => set('spectrum.opacity', Number(e.target.value))} />
          </div>
        </div>
      </div>

      <div className="card">
        <h3>5. Logo</h3>
        <div className="row">
          <div className="field">
            <label>Posisi</label>
            <select value={form.logo.position} onChange={(e) => set('logo.position', e.target.value)}>
              <option value="top_left">Kiri atas</option>
              <option value="top_right">Kanan atas</option>
              <option value="top_center">Atas tengah</option>
              <option value="bottom_left">Kiri bawah</option>
              <option value="bottom_right">Kanan bawah</option>
            </select>
          </div>
          <div className="field" style={{ alignSelf: 'end' }}>
            <label>
              <input type="checkbox" checked={form.logo.circle}
                onChange={(e) => set('logo.circle', e.target.checked)} /> Logo bulat
            </label>
          </div>
        </div>
        <div className="row">
          <div className="field">
            <label>Ukuran ({form.logo.size} px)</label>
            <input type="range" min="48" max="320" step="4"
              value={form.logo.size}
              onChange={(e) => set('logo.size', Number(e.target.value))} />
          </div>
          <div className="field">
            <label>Opacity ({Math.round(form.logo.opacity * 100)}%)</label>
            <input type="range" min="0.2" max="1" step="0.05"
              value={form.logo.opacity}
              onChange={(e) => set('logo.opacity', Number(e.target.value))} />
          </div>
          <div className="field">
            <label>Margin (px)</label>
            <input type="number" min="0" value={form.logo.margin}
              onChange={(e) => set('logo.margin', Number(e.target.value))} />
          </div>
        </div>
      </div>

      <div className="card">
        <h3>6. Render</h3>
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
        </div>
        <div className="row">
          <div className="field">
            <label>CRF ({form.render.crf})</label>
            <input type="range" min="14" max="35" step="1"
              value={form.render.crf}
              onChange={(e) => set('render.crf', Number(e.target.value))} />
            <div className="help">Lebih kecil = lebih bagus. 24-28 cocok untuk laptop kentang.</div>
          </div>
          <div className="field">
            <label>Durasi preview (detik)</label>
            <input type="number" min="3" max="60" step="1"
              value={form.preview_seconds}
              onChange={(e) => set('preview_seconds', Number(e.target.value))} />
          </div>
        </div>
      </div>
    </div>
  );
}
