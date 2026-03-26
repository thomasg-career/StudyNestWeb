const BASE_URL = "https://studynestweb.onrender.com/api";

function getToken() {
  return localStorage.getItem("token");
}

function setToken(token) {
  localStorage.setItem("token", token);
}

function clearToken() {
  localStorage.removeItem("token");
}

export async function apiFetch(endpoint, options = {}) {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { "Authorization": `Bearer ${token}` } : {}),
    ...(options.headers || {})
  };

  const response = await fetch(BASE_URL + endpoint, {
    ...options,
    headers
  });

  const raw = await response.text();
  const data = raw ? JSON.parse(raw) : null;

  if (!response.ok) {
    if (response.status === 401) {
      clearToken();
      if (!window.location.pathname.endsWith("index.html")) {
        window.location.href = "index.html";
      }
    }
    console.error("API ERROR:", data);
    throw new Error((data && data.error) || "API failed");
  }

  return data;
}

window.StudyNestAPI = {
  BASE_URL,
  apiFetch,
  getToken,
  setToken,
  clearToken
};

export { BASE_URL, clearToken, getToken, setToken };
