import { useEffect, useState } from "react";
import { api } from "../api";

export default function ContextStep({ token, disabled, onPlan }) {
  const [tab, setTab] = useState("predefined");
  const [predefined, setPredefined] = useState([]);
  const [mine, setMine] = useState([]);
  const [selectedKey, setSelectedKey] = useState("");
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [contextText, setContextText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.predefinedTemplates().then(setPredefined).catch(() => {});
  }, []);

  useEffect(() => {
    if (token) {
      api.myTemplates(token).then(setMine).catch(() => {});
    } else {
      setMine([]);
    }
  }, [token]);

  async function generate() {
    setError("");
    setBusy(true);
    try {
      let payload = {};
      if (tab === "predefined") {
        if (!selectedKey) throw new Error("Pick a use case first");
        payload = { predefined_key: selectedKey };
      } else if (tab === "custom") {
        if (!contextText.trim()) throw new Error("Describe how you'd like it cleaned");
        payload = { context_text: contextText.trim() };
      } else if (tab === "saved") {
        if (!selectedTemplateId) throw new Error("Pick a saved template first");
        payload = { template_id: Number(selectedTemplateId) };
      }
      await onPlan(payload);
    } catch (err) {
      setError(err.message || "Could not generate a plan");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={`context-step ${disabled ? "context-step--disabled" : ""}`}>
      <p className="eyebrow">Step 2</p>
      <h3>Tell it what "clean" means</h3>

      <div className="tabs" role="tablist">
        <button
          role="tab"
          aria-selected={tab === "predefined"}
          className={`tab ${tab === "predefined" ? "tab--active" : ""}`}
          onClick={() => setTab("predefined")}
        >
          Predefined use case
        </button>
        <button
          role="tab"
          aria-selected={tab === "custom"}
          className={`tab ${tab === "custom" ? "tab--active" : ""}`}
          onClick={() => setTab("custom")}
        >
          Describe in English
        </button>
        <button
          role="tab"
          aria-selected={tab === "saved"}
          className={`tab ${tab === "saved" ? "tab--active" : ""}`}
          onClick={() => setTab("saved")}
        >
          My saved templates {token ? `(${mine.length})` : ""}
        </button>
      </div>

      {tab === "predefined" && (
        <div className="predefined-list">
          {predefined.map((p) => (
            <label key={p.key} className={`predefined-card ${selectedKey === p.key ? "predefined-card--selected" : ""}`}>
              <input
                type="radio"
                name="predefined"
                value={p.key}
                checked={selectedKey === p.key}
                onChange={() => setSelectedKey(p.key)}
              />
              <div>
                <strong>{p.label}</strong>
                <p>{p.description}</p>
              </div>
            </label>
          ))}
        </div>
      )}

      {tab === "custom" && (
        <textarea
          className="context-textarea"
          rows={4}
          placeholder="e.g. Remove duplicate customer IDs, treat blank revenue as 0, standardize dates to YYYY-MM-DD, title-case customer names"
          value={contextText}
          onChange={(e) => setContextText(e.target.value)}
        />
      )}

      {tab === "saved" && (
        <div>
          {!token && <p className="upload-hint">Sign in to see and reuse your saved templates.</p>}
          {token && mine.length === 0 && <p className="upload-hint">No saved templates yet — clean a sheet and save its plan for next time.</p>}
          {token && mine.length > 0 && (
            <select
              className="template-select"
              value={selectedTemplateId}
              onChange={(e) => setSelectedTemplateId(e.target.value)}
            >
              <option value="">Choose a saved template...</option>
              {mine.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          )}
        </div>
      )}

      {error && <p className="field-error">{error}</p>}

      <button className="btn btn--primary" onClick={generate} disabled={disabled || busy}>
        {busy ? "Thinking..." : "Generate cleaning plan"}
      </button>
    </div>
  );
}
