export function BrandMark() {
  return (
    <div className="brandMark" aria-label="商域图谱">
      <span className="brandGlyph" aria-hidden="true" data-testid="app-brand-icon">
        <svg viewBox="0 0 48 48" role="presentation" focusable="false">
          <defs>
            <linearGradient id="eeiMarkCore" x1="8" x2="40" y1="8" y2="40">
              <stop offset="0" stopColor="#8EE7C6" />
              <stop offset="0.52" stopColor="#4B8DFF" />
              <stop offset="1" stopColor="#F3B861" />
            </linearGradient>
          </defs>
          <path className="brandGlyphGrid" d="M14 17h13l7 7-7 7H14" />
          <path className="brandGlyphSpine" d="M15 24h21" />
          <circle className="brandGlyphNode primary" cx="14" cy="17" r="4.2" />
          <circle className="brandGlyphNode" cx="27" cy="17" r="3.2" />
          <circle className="brandGlyphNode primary" cx="36" cy="24" r="4.4" />
          <circle className="brandGlyphNode" cx="27" cy="31" r="3.2" />
          <circle className="brandGlyphNode primary" cx="14" cy="31" r="4.2" />
        </svg>
      </span>
      <span>
        <strong>商域图谱</strong>
        <small>EEI</small>
      </span>
    </div>
  );
}
