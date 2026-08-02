import { useRef, useState } from "react";
import { api } from "../api";

export default function UploadStep({ onUploaded }) {
  const inputRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);

  async function handleFile(file) {
    if (!file) return;
    setError("");
    setBusy(true);
    try {
      const preview = await api.uploadFile(file);
      onUploaded(preview);
    } catch (err) {
      setError(err.message || "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className={`upload-drop ${dragOver ? "upload-drop--over" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        handleFile(e.dataTransfer.files?.[0]);
      }}
    >
      <p className="eyebrow">Step 1</p>
      <h3>Feed it a worksheet</h3>
      <p className="upload-hint">Drop an .xlsx or .xls file here, or choose one from your computer.</p>
      <input
        ref={inputRef}
        type="file"
        accept=".xlsx,.xls"
        style={{ display: "none" }}
        onChange={(e) => handleFile(e.target.files?.[0])}
      />
      <button
        className="btn btn--primary"
        onClick={() => inputRef.current?.click()}
        disabled={busy}
      >
        {busy ? "Reading sheet..." : "Choose file"}
      </button>
      {error && <p className="field-error">{error}</p>}
    </div>
  );
}
