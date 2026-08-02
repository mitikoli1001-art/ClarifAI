import { useState } from "react";
import { api } from "../api";

export default function AuthBar({ user, token, onAuthed, onLogout }) {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState("login"); // 'login' | 'signup'
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "signup") {
        await api.signup(email, password);
      }
      const { access_token } = await api.login(email, password);
      onAuthed({ email }, access_token);
      setOpen(false);
      setPassword("");
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  if (user) {
    return (
      <div className="authbar">
        <span className="authbar-email mono">{user.email}</span>
        <button className="btn btn--ghost" onClick={onLogout}>
          Sign out
        </button>
      </div>
    );
  }

  return (
    <div className="authbar">
      {!open ? (
        <button className="btn btn--ghost" onClick={() => setOpen(true)}>
          Sign in
        </button>
      ) : (
        <form className="authbar-form" onSubmit={submit}>
          <input
            type="email"
            required
            placeholder="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input
            type="password"
            required
            minLength={6}
            placeholder="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button className="btn btn--primary" type="submit" disabled={busy}>
            {busy ? "..." : mode === "login" ? "Sign in" : "Create account"}
          </button>
          <button
            type="button"
            className="btn btn--ghost btn--small"
            onClick={() => setMode(mode === "login" ? "signup" : "login")}
          >
            {mode === "login" ? "New here?" : "Have an account?"}
          </button>
          {error && <span className="authbar-error">{error}</span>}
        </form>
      )}
    </div>
  );
}
