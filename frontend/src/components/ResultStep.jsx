import { api } from "../api";

export default function ResultStep({ fileToken, report, onReset }) {
  const downloadUrl = api.downloadUrl(fileToken);

  return (
    <div className="result-step">
      <p className="eyebrow">Step 4</p>
      <h3>Cleaned. No further changes needed.</h3>

      <div className="result-grid">
        <div className="result-card">
          <span className="stat-num">{report.rows_before}</span>
          <span className="stat-arrow">→</span>
          <span className="stat-num" style={{ color: "var(--clarity)" }}>{report.rows_after}</span>
          <span className="stat-label">rows</span>
        </div>
        <div className="result-card">
          <span className="stat-num">{report.columns_before}</span>
          <span className="stat-arrow">→</span>
          <span className="stat-num" style={{ color: "var(--clarity)" }}>{report.columns_after}</span>
          <span className="stat-label">columns</span>
        </div>
        <div className="result-card">
          <span className="stat-num" style={{ color: "var(--flag)" }}>{report.duplicates_removed}</span>
          <span className="stat-label">duplicate rows removed</span>
        </div>
      </div>

      {Object.keys(report.columns_renamed).length > 0 && (
        <div className="result-detail">
          <strong>Renamed:</strong>{" "}
          <span className="mono">
            {Object.entries(report.columns_renamed).map(([a, b]) => `${a} → ${b}`).join(", ")}
          </span>
        </div>
      )}
      {report.columns_dropped.length > 0 && (
        <div className="result-detail">
          <strong>Dropped:</strong> <span className="mono">{report.columns_dropped.join(", ")}</span>
        </div>
      )}

      <div className="result-actions">
        <a className="btn btn--primary" href={downloadUrl} download="cleaned_data.xlsx">
          Download cleaned .xlsx
        </a>
        <button className="btn btn--ghost" onClick={onReset}>
          Clean another sheet
        </button>
      </div>
    </div>
  );
}
