const Dashboard = {
  template: `
    <div>
      <h2 style="margin-bottom:16px">Dashboard</h2>
      <div class="card">
        <p>Welcome, {{ username }}.</p>
        <p style="margin-top:8px; color:#666">Manage companies and cameras from the navigation above.</p>
      </div>
      <div class="stats-grid" v-if="stats">
        <div class="stat-card">
          <div class="stat-number">{{ stats.companies }}</div>
          <div class="stat-label">Companies</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ stats.cameras }}</div>
          <div class="stat-label">Total Cameras</div>
        </div>
      </div>
    </div>
  `,
  data() {
    return { stats: null };
  },
  setup() {
    const username = Vue.computed(() => auth.username);
    return { username };
  },
  async created() {
    const res = await apiFetch("/api/companies");
    if (res.ok) {
      const companies = await res.json();
      let totalCameras = 0;
      for (const c of companies) {
        const cres = await apiFetch(`/api/companies/${c.id}/cameras`);
        if (cres.ok) {
          const cameras = await cres.json();
          totalCameras += cameras.length;
        }
      }
      this.stats = { companies: companies.length, cameras: totalCameras };
    }
  },
};
