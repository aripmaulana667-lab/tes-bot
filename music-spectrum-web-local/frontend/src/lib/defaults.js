export const defaultRenderForm = () => ({
  music_file: '',
  output_name: '',
  preview_seconds: 10,
  lyrics: {
    file: '',
    offset_ms: 0,
    font: 'Arial',
    font_size: 36,
    bottom_margin: 80,
    color: '#FFFFFF',
    outline_color: '#000000',
    outline_size: 2,
    shadow_color: '#000000',
    shadow_size: 1,
    opacity: 1.0,
    fade_ms: 250,
  },
  spectrum: { style: 'neon_bar_smooth', height: 180, density: 80, opacity: 0.9 },
  logo: { file: '', circle: true, position: 'top_right', size: 128, opacity: 1.0, margin: 24 },
  background: { mode: 'single', files: [], slideshow_duration: 4.0, randomize: false, dark_overlay: 0.35, blur: 0 },
  render: { resolution: '1280x720', fps: 30, crf: 24, preset: 'veryfast' },
});

export const defaultBatchForm = () => {
  const base = defaultRenderForm();
  return {
    music_dir: 'music',
    lyrics_dir: 'lyrics',
    background_dir: 'backgrounds',
    match_mode: 'sequence',
    multi_background: false,
    lyrics: base.lyrics,
    spectrum: base.spectrum,
    logo: base.logo,
    background: base.background,
    render: base.render,
  };
};
