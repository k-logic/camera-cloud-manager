const Login = {
  template: `
    <div class="d-flex vh-100 justify-content-center align-items-center bg-light">
      <div class="card shadow-sm" style="width:100%;max-width:400px">
        <div class="card-body p-4">
          <h4 class="text-center mb-4">Admin Console</h4>
          <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
          <form @submit.prevent="submit">
            <div class="mb-3">
              <label class="form-label">Username</label>
              <input v-model="username" type="text" class="form-control" autofocus>
            </div>
            <div class="mb-3">
              <label class="form-label">Password</label>
              <input v-model="password" type="password" class="form-control">
            </div>
            <button class="btn btn-primary w-100" :disabled="loading">
              {{ loading ? "Logging in..." : "Login" }}
            </button>
          </form>
        </div>
      </div>
    </div>
  `,
  data() {
    return { username: "", password: "", error: null, loading: false };
  },
  methods: {
    async submit() {
      this.error = null;
      this.loading = true;
      try {
        const res = await fetch("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: this.username, password: this.password }),
        });
        if (!res.ok) {
          this.error = "Invalid username or password";
          return;
        }
        const data = await res.json();
        if (!data.is_admin) {
          this.error = "Admin access required";
          return;
        }
        auth.setTokens(data.access_token, data.refresh_token, this.username, true);
        this.$router.push("/");
      } catch {
        this.error = "Connection error";
      } finally {
        this.loading = false;
      }
    },
  },
};
