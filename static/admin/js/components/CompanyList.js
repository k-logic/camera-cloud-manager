const CompanyList = {
  template: `
    <div>
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h4 class="mb-0">Companies</h4>
        <router-link to="/companies/new" class="btn btn-primary btn-sm">
          <i class="bi bi-plus-lg me-1"></i>New Company
        </router-link>
      </div>
      <div class="card">
        <div class="table-responsive">
          <table v-if="companies.length" class="table table-hover mb-0">
            <thead>
              <tr><th>ID</th><th>Name</th><th></th></tr>
            </thead>
            <tbody>
              <tr v-for="c in companies" :key="c.id">
                <td>{{ c.id }}</td>
                <td>{{ c.name }}</td>
                <td class="text-end">
                  <div class="d-flex gap-1 justify-content-end">
                    <router-link :to="'/companies/' + c.id + '/cameras'" class="btn btn-sm btn-primary">
                      <i class="bi bi-camera-video me-1"></i>Cameras
                    </router-link>
                    <router-link :to="'/companies/' + c.id + '/edit'" class="btn btn-sm btn-secondary">Edit</router-link>
                    <button @click="remove(c)" class="btn btn-sm btn-danger">Delete</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="!companies.length" class="card-body text-muted">No companies yet.</div>
      </div>
    </div>
  `,
  data() {
    return { companies: [] };
  },
  async created() {
    await this.load();
  },
  methods: {
    async load() {
      const res = await apiFetch("/api/companies");
      if (res.ok) this.companies = await res.json();
    },
    async remove(c) {
      if (!confirm(\`Delete "\${c.name}"?\`)) return;
      const res = await apiFetch(\`/api/companies/\${c.id}\`, { method: "DELETE" });
      if (res.ok) await this.load();
    },
  },
};
