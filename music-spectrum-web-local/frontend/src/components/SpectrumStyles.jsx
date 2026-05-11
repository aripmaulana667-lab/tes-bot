const PREVIEWS = {
  neon_bar_smooth: 'linear-gradient(90deg,#00FFE0,#FF00C8)',
  aurora_bars: 'linear-gradient(90deg,#00FFAA,#00C0FF,#C080FF)',
  soft_white_minimal: 'linear-gradient(90deg,#ffffff,#dedede)',
  fire_pulse: 'linear-gradient(90deg,#FF3000,#FF8800,#FFD800)',
  ocean_wave: 'linear-gradient(90deg,#0080FF,#00C8FF,#80FFFF)',
  purple_dream: 'linear-gradient(90deg,#6020FF,#B060FF,#FF80FF)',
  green_matrix: 'linear-gradient(90deg,#00FF40,#80FF80)',
  gold_luxury: 'linear-gradient(90deg,#FFC020,#FFE080,#FFFFE0)',
  candy_pop: 'linear-gradient(90deg,#FF60C0,#FFE060,#60E0FF)',
  thin_cinematic: 'linear-gradient(90deg,#F0F0F0,#A0A0FF)',
  bass_heavy: 'linear-gradient(90deg,#FF2050,#FFB050)',
  pastel_smooth: 'linear-gradient(90deg,#FFC0E0,#C0E0FF,#C0FFD0)',
  frequency_classic: 'linear-gradient(90deg,#ff0000,#ffff00,#00ff00,#00ffff,#0000ff,#ff00ff)',
  frequency_glow: 'linear-gradient(90deg,#ff00ff,#00ffff,#ffff00)',
  rainbow_energy: 'linear-gradient(90deg,#ff0000,#ff7f00,#ffff00,#00ff00,#0000ff,#8b00ff)',
};

export default function SpectrumStyles({ styles, value, onChange }) {
  if (!styles?.length) return null;
  return (
    <div className="spectrum-styles">
      {styles.map((s) => (
        <button
          key={s.key}
          type="button"
          className={`style ${value === s.key ? 'active' : ''}`}
          onClick={() => onChange(s.key)}
        >
          <div className="preview" style={{ background: PREVIEWS[s.key] || PREVIEWS.neon_bar_smooth }} />
          <div className="name">{s.label}</div>
          <div className="desc">{s.description}</div>
        </button>
      ))}
    </div>
  );
}
