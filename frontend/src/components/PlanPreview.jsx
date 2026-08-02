import { useState } from "react";
import { api } from "../api";

const NULL_LABELS = {
  drop_row: "drop the row",
  fill_mean: "fill with the column mean",
  fill_median: "fill with the column median",
  fill_mode: "fill with the most common value",
  fill_value: "fill with a fixed value",
  fill_zero: "fill with 0",
  fill_unknown: "fill with 'Unknown'",
  leave: "leave as-is",
};

function ruleSummary(rule) {
  const bits = [];
  if (rule.dtype) bits.push(`cast to ${rule.dtype}`);
  if (rule.null_strategy) bits.push(NULL_LABELS[rule.null_strategy] || rule.null_strategy);
  if (rule.standardize_case) bits.push(`${rule.standardize_case}-case`);
  if (rule.trim_whitespace) bits.push("trim whitespace");
  if (rule.remove_special_chars) bits.push("strip special characters");
  if (rule.rename_to) bits.push(`rename to "${rule.rename_to}"`);
  return bits.join(" · ") || "no change";
}

export default function PlanPreview({ token, fileToken, plan, source, onCleaned }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [showSave, setShowSave] = useState(false);
  const [templateName, setTemplateName] = useState("");
  const [templateDesc, setTemplateDesc] = useState("");
  const [saveStatus, setSaveStatus] = useState("");

  async function runClean() {
    setBusy(true);
    setError("");
    try {
      const result = await api.executeClean(fileToken, plan);
      onCleaned(result);
    } catch (err) {
      setError(err.message || "Cleaning failed");
    } finally {
      setBusy(false);
    }
  }

  async function saveTemplate() {
    setSaveStatus("");
    try {
      await api.saveTemplate(token, {
        name: templateName,
        description: templateDesc,
        plan,
      });
      setSaveStatus("Saved. It'll show up under 'My saved templates' next time.");
      setShowSave(false);
    } catch (err) {
      setSaveStatus(err.message || "Could not save template");
    }
  }

  return (
    <div className="plan-preview">
      <p className="eyebrow">Step 3</p>
      <h3>Review the plan</h3>
      <p className="upload-hint">
        Source: <span className="mono">{source}</span> — Pandas will execute exactly this, deterministically.
      </p>

      <ul className="plan-list">
        <li>
          <strong>Duplicates:</strong>{" "}
          {plan.drop_duplicate_rows
            ? plan.duplicate_subset?.length
              ? `remove duplicates by ${plan.duplicate_subset.join(", ")}`
              : "remove full-row duplicates"
            : "keep duplicates"}
        </li>
        <li>
          <strong>Empty rows/columns:</strong>{" "}
          {[plan.drop_empty_rows && "empty rows dropped", plan.drop_empty_columns && "empty columns dropped"]
            .filter(Boolean)
            .join(", ") || "kept as-is"}
        </li>
        <li>
          <strong>Column names:</strong>{" "}
          {plan.standardize_column_names ? "standardized to snake_case" : "left as uploaded"}
        </li>
        {plan.drop_columns?.length > 0 && (
          <li>
            <strong>Dropped columns:</strong> {plan.drop_columns.join(", ")}
          </li>
        )}
        {plan.column_rules?.map((rule) => (
          <li key={rule.column}>
            <strong className="mono">{rule.column}</strong>: {ruleSummary(rule)}
          </li>
        ))}
        {plan.outlier_handling && plan.outlier_handling !== "none" && (
          <li>
            <strong>Outliers:</strong> {plan.outlier_handling === "clip_iqr" ? "clipped to IQR bounds" : "removed via IQR"}
          </li>
        )}
      </ul>

      {plan.notes && <p className="plan-notes mono">{plan.notes}</p>}

      {error && <p className="field-error">{error}</p>}

      <div className="plan-actions">
        <button className="btn btn--primary" onClick={runClean} disabled={busy}>
          {busy ? "Cleaning..." : "Clean it"}
        </button>
        {token && (
          <button className="btn btn--ghost" onClick={() => setShowSave((s) => !s)}>
            Save as template
          </button>
        )}
      </div>

      {showSave && (
        <div className="save-template-form">
          <input
            placeholder="Template name"
            value={templateName}
            onChange={(e) => setTemplateName(e.target.value)}
          />
          <input
            placeholder="Short description (optional)"
            value={templateDesc}
            onChange={(e) => setTemplateDesc(e.target.value)}
          />
          <button className="btn btn--primary btn--small" onClick={saveTemplate} disabled={!templateName.trim()}>
            Save
          </button>
        </div>
      )}
      {saveStatus && <p className="upload-hint">{saveStatus}</p>}
    </div>
  );
}
