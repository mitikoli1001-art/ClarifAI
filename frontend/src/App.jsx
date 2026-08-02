import { useState } from "react";
import "./App.css";
import ResolvingGrid from "./ResolvingGrid";
import AuthBar from "./components/AuthBar";
import UploadStep from "./components/UploadStep";
import SheetPreview from "./components/SheetPreview";
import ContextStep from "./components/ContextStep";
import PlanPreview from "./components/PlanPreview";
import ResultStep from "./components/ResultStep";
import { api } from "./api";

export default function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);

  const [preview, setPreview] = useState(null); // upload preview (file_token, schema)
  const [planData, setPlanData] = useState(null); // { plan, source }
  const [report, setReport] = useState(null); // quality report after execute

  function reset() {
    setPreview(null);
    setPlanData(null);
    setReport(null);
  }

  async function handleGeneratePlan(payload) {
    const res = await api.getPlan({ file_token: preview.file_token, ...payload });
    setPlanData(res);
  }

  return (
    <div className="page">
      <header className="site-header">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">◧</span>
          <span className="brand-name">ClarifAI</span>
        </div>
        <AuthBar
          user={user}
          token={token}
          onAuthed={(u, t) => {
            setUser(u);
            setToken(t);
          }}
          onLogout={() => {
            setUser(null);
            setToken(null);
          }}
        />
      </header>

      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">AI-planned, Pandas-executed</p>
          <h1>Messy spreadsheets, resolved.</h1>
          <p className="hero-sub">
            Describe your cleaning rules in plain English, or pick a use case. ClarifAI turns that
            into a structured plan and runs it deterministically with Pandas — no further changes needed.
          </p>
        </div>
        <ResolvingGrid />
      </section>

      <main className="tool">
        <div className="tool-inner">
          {!preview && <UploadStep onUploaded={setPreview} />}

          {preview && !planData && (
            <>
              <SheetPreview preview={preview} />
              <ContextStep token={token} onPlan={handleGeneratePlan} />
            </>
          )}

          {preview && planData && !report && (
            <>
              <SheetPreview preview={preview} />
              <PlanPreview
                token={token}
                fileToken={preview.file_token}
                plan={planData.plan}
                source={planData.source}
                onCleaned={setReport}
              />
            </>
          )}

          {report && <ResultStep fileToken={preview.file_token} report={report} onReset={reset} />}
        </div>
      </main>

      <footer className="site-footer">
        <span>ClarifAI — the AI decides the plan, Pandas executes it.</span>
      </footer>
    </div>
  );
}
