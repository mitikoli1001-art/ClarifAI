const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch (_) {
      /* ignore parse errors */
    }
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  base: API_BASE,

  async signup(email, password) {
    const res = await fetch(`${API_BASE}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    return handle(res);
  },

  async login(email, password) {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
    });
    return handle(res);
  },

  async uploadFile(file) {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE}/files/upload`, {
      method: "POST",
      body: form,
    });
    return handle(res);
  },

  async predefinedTemplates() {
    const res = await fetch(`${API_BASE}/templates/predefined`);
    return handle(res);
  },

  async myTemplates(token) {
    const res = await fetch(`${API_BASE}/templates/mine`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return handle(res);
  },

  async saveTemplate(token, payload) {
    const res = await fetch(`${API_BASE}/templates/save`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });
    return handle(res);
  },

  async getPlan({ file_token, context_text, predefined_key, template_id }) {
    const res = await fetch(`${API_BASE}/clean/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file_token, context_text, predefined_key, template_id }),
    });
    return handle(res);
  },

  async executeClean(file_token, plan) {
    const res = await fetch(`${API_BASE}/clean/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file_token, plan }),
    });
    return handle(res);
  },

  downloadUrl(file_token) {
    return `${API_BASE}/clean/download/${file_token}`;
  },
};
