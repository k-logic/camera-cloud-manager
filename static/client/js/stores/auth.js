const authState = Vue.reactive({
  accessToken: localStorage.getItem("access_token") || null,
  refreshToken: localStorage.getItem("refresh_token") || null,
  username: localStorage.getItem("username") || null,
  companyId: localStorage.getItem("company_id") || null,
});

const auth = {
  get isLoggedIn() { return !!authState.accessToken; },
  get username() { return authState.username; },
  get companyId() { return authState.companyId; },
  get accessToken() { return authState.accessToken; },
  get refreshToken() { return authState.refreshToken; },

  setTokens(access, refresh, username, companyId) {
    authState.accessToken = access;
    authState.refreshToken = refresh;
    authState.username = username;
    authState.companyId = companyId;
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
    localStorage.setItem("username", username);
    localStorage.setItem("company_id", String(companyId));
  },

  clear() {
    authState.accessToken = null;
    authState.refreshToken = null;
    authState.username = null;
    authState.companyId = null;
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("username");
    localStorage.removeItem("company_id");
  },

  async tryRefresh() {
    if (!authState.refreshToken) return false;
    try {
      const res = await fetch("/api/auth/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: authState.refreshToken }),
      });
      if (!res.ok) { this.clear(); return false; }
      const data = await res.json();
      authState.accessToken = data.access_token;
      localStorage.setItem("access_token", data.access_token);
      return true;
    } catch {
      this.clear();
      return false;
    }
  },
};
