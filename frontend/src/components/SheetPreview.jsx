export default function SheetPreview({ preview }) {
  if (!preview) return null;
  const nullEntries = Object.entries(preview.null_counts).filter(([, n]) => n > 0);

  return (
    <div className="sheet-preview">
      <div className="sheet-preview-stats">
        <div>
          <span className="stat-num">{preview.rows}</span>
          <span className="stat-label">rows</span>
        </div>
        <div>
          <span className="stat-num">{preview.columns}</span>
          <span className="stat-label">columns</span>
        </div>
        <div>
          <span className="stat-num" style={{ color: nullEntries.length ? "var(--messy)" : "var(--clarity)" }}>
            {nullEntries.length}
          </span>
          <span className="stat-label">columns with nulls</span>
        </div>
      </div>
      <div className="sheet-preview-cols mono">
        {preview.column_names.map((c) => (
          <span key={c} className="col-chip">
            {c}
          </span>
        ))}
      </div>
    </div>
  );
}
