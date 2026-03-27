const Login = {
  template: `
    <div class="login-container">
      <div class="login-box">
        <h2>Admin Console</h2>
        <p v-if="error" class="error-msg">{{ error }}</p>
        <form @submit.prevent="submit">
          <div class="form-group">
            <label>Username</label>
            <input v-model="username" type="text" autofocus>
          </div>
          <div class="form-group">
            <label>Password</label>
            <input v-model="password" type="password">
          </div>
          <button class="btn" style="width:100%" :disabled="loading">
            {{ loading ? "Logging in..." : "Login" }}
          </button>
        </form>
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
