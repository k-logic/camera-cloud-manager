async function apiFetch(url, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (auth.accessToken) {
    headers["Authorization"] = `Bearer ${auth.accessToken}`;
  }

  let res = await fetch(url, { ...options, headers });

  if (res.status === 401 && auth.refreshToken) {
    const refreshed = await auth.tryRefresh();
    if (refreshed) {
      headers["Authorization"] = `Bearer ${auth.accessToken}`;
      res = await fetch(url, { ...options, headers });
    }
  }

  if (res.status === 401) {
    auth.clear();
    window.location.hash = "#/login";
  }

  return res;
}
