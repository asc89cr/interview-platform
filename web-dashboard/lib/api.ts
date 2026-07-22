const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// ── Token storage ──────────────────────────────────────────────────────────────

export const auth = {
  getAccessToken: () =>
    typeof window !== "undefined" ? localStorage.getItem("access_token") : null,
  getRefreshToken: () =>
    typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null,
  setTokens: (access: string, refresh: string) => {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
  },
  clear: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  },
  isLoggedIn: () => Boolean(
    typeof window !== "undefined" && localStorage.getItem("access_token")
  ),
};

// ── Refresh logic ──────────────────────────────────────────────────────────────

let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    const refresh_token = auth.getRefreshToken();
    if (!refresh_token) throw new Error("No refresh token");

    const res = await fetch(`${API}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token }),
    });

    if (!res.ok) {
      auth.clear();
      window.location.href = "/login";
      throw new Error("Session expired");
    }

    const data = await res.json();
    auth.setTokens(data.access_token, data.refresh_token);
    return data.access_token as string;
  })().finally(() => { refreshPromise = null; });

  return refreshPromise;
}

// ── Core fetch wrapper ─────────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  retry = true,
): Promise<T> {
  const token = auth.getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API}${path}`, { ...init, headers });

  if (res.status === 401 && retry) {
    const newToken = await refreshAccessToken();
    return apiFetch<T>(path, {
      ...init,
      headers: { ...headers, Authorization: `Bearer ${newToken}` },
    }, false);
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ── Types ──────────────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface CandidateProfile {
  id: string;
  user_id: string;
  resume_url: string | null;
  parsed_resume: Record<string, unknown> | null;
  target_role: string | null;
  target_salary_usd: number | null;
  skills: string[];
  weak_areas: string[];
  custom_notes: string | null;
  updated_at: string;
}

export interface InterviewerProfile {
  id: string;
  user_id: string;
  name: string;
  company: string | null;
  role: string | null;
  interview_style: string;
  known_questions: string[];
  notes: string | null;
  created_at: string;
}

export interface Session {
  id: string;
  user_id: string;
  candidate_profile_id: string | null;
  interviewer_profile_id: string | null;
  status: "active" | "completed" | "analysing" | "analysed";
  started_at: string | null;
  ended_at: string | null;
  created_at: string;
}

export interface Turn {
  id: string;
  session_id: string;
  speaker: "Interviewer" | "Candidate";
  text: string;
  generated_answer: string | null;
  timestamp: string;
  audio_url: string | null;
}

export interface AttachedFile {
  id: string;
  session_id: string;
  label: string;
  file_url: string;
  file_type: string;
  uploaded_at: string;
}

export interface SessionDetail extends Session {
  turns: Turn[];
  attached_files: AttachedFile[];
}

export interface AnalysisReport {
  id: string;
  session_id: string;
  overall_score: number;
  category_scores: Record<string, number>;
  strengths: string[];
  weaknesses: string[];
  interviewer_intent_summary: string | null;
  recommended_practice: string[];
  pdf_report_url: string | null;
  created_at: string;
}

// ── Auth endpoints ─────────────────────────────────────────────────────────────

export const authApi = {
  register: (email: string, password: string, name: string) =>
    apiFetch<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, name }),
    }),

  login: (email: string, password: string) =>
    apiFetch<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  logout: (refresh_token: string) =>
    apiFetch<void>("/auth/logout", {
      method: "POST",
      body: JSON.stringify({ refresh_token }),
    }),
};

// ── Profile endpoints ──────────────────────────────────────────────────────────

export const profileApi = {
  getCandidate: () => apiFetch<CandidateProfile>("/profile/candidate"),

  updateCandidate: (data: Partial<CandidateProfile>) =>
    apiFetch<CandidateProfile>("/profile/candidate", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  getResumeUploadUrl: () =>
    apiFetch<{ url: string; fields: Record<string, string>; key: string }>(
      "/profile/candidate/resume",
      { method: "POST" }
    ),

  listInterviewers: () => apiFetch<InterviewerProfile[]>("/profile/interviewers"),

  createInterviewer: (data: Partial<InterviewerProfile>) =>
    apiFetch<InterviewerProfile>("/profile/interviewers", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateInterviewer: (id: string, data: Partial<InterviewerProfile>) =>
    apiFetch<InterviewerProfile>(`/profile/interviewers/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deleteInterviewer: (id: string) =>
    apiFetch<void>(`/profile/interviewers/${id}`, { method: "DELETE" }),
};

// ── Session endpoints ──────────────────────────────────────────────────────────

export const sessionApi = {
  list: () => apiFetch<Session[]>("/sessions"),

  create: (data: { candidate_profile_id?: string; interviewer_profile_id?: string }) =>
    apiFetch<Session>("/sessions", { method: "POST", body: JSON.stringify(data) }),

  get: (id: string) => apiFetch<SessionDetail>(`/sessions/${id}`),

  delete: (id: string) => apiFetch<void>(`/sessions/${id}`, { method: "DELETE" }),

  attachFile: (
    sessionId: string,
    label: string,
    filename: string,
    content_type: string
  ) =>
    apiFetch<{ file: AttachedFile; upload: { url: string; fields: Record<string, string>; key: string } }>(
      `/sessions/${sessionId}/files`,
      { method: "POST", body: JSON.stringify({ label, filename, content_type }) }
    ),

  getReport: (id: string) => apiFetch<AnalysisReport>(`/sessions/${id}/report`),
};

// ── Billing endpoints ──────────────────────────────────────────────────────────

export const billingApi = {
  createCheckout: (price_id: string) =>
    apiFetch<{ url: string }>("/billing/checkout", {
      method: "POST",
      body: JSON.stringify({ price_id }),
    }),

  createPortal: () =>
    apiFetch<{ url: string }>("/billing/portal", { method: "POST" }),

  getSubscription: () =>
    apiFetch<{ tier: string; sessions_used: number; sessions_limit: number | null }>(
      "/billing/subscription"
    ),
};

// ── S3 upload helper ───────────────────────────────────────────────────────────

export async function uploadToS3(
  presigned: { url: string; fields: Record<string, string> },
  file: File
): Promise<void> {
  const form = new FormData();
  Object.entries(presigned.fields).forEach(([k, v]) => form.append(k, v));
  form.append("file", file);

  const res = await fetch(presigned.url, { method: "POST", body: form });
  if (!res.ok) throw new Error("S3 upload failed");
}
