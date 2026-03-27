const Dashboard = {
  template: `
    <div>
      <h4 class="mb-4">Dashboard</h4>
      <div class="card mb-4">
        <div class="card-body">
          <p class="mb-0">Welcome, <strong>{{ username }}</strong>.</p>
        </div>
      </div>
      <div class="row g-3" v-if="stats">
        <div class="col-sm-6 col-md-4">
          <div class="card text-center">
            <div class="card-body">
              <div class="fs-2 fw-bold text-primary">{{ stats.companies }}</div>
              <div class="text-muted">Companies</div>
            </div>
          </div>
        </div>
        <div class="col-sm-6 col-md-4">
          <div class="card text-center">
            <div class="card-body">
              <div class="fs-2 fw-bold text-primary">{{ stats.cameras }}</div>
              <div class="text-muted">Total Cameras</div>
            </div>
          </div>
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
