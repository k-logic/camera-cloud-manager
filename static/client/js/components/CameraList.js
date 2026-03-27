const CameraList = {
  template: `
    <div>
      <h4 class="mb-3">Cameras</h4>
      <div class="card">
        <div class="table-responsive">
          <table v-if="cameras.length" class="table table-hover mb-0">
            <thead>
              <tr>
                <th>Name</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in cameras" :key="c.id">
                <td>{{ c.name }}</td>
                <td>
                  <span class="badge" :class="c.is_active ? 'bg-success' : 'bg-danger'">
                    {{ c.is_active ? "Active" : "Inactive" }}
                  </span>
                </td>
                <td class="text-end">
                  <router-link :to="'/cameras/' + c.id" class="btn btn-sm btn-primary">Detail</router-link>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="!cameras.length" class="card-body text-muted">No cameras registered.</div>
      </div>
    </div>
  `,
  data() {
    return { cameras: [] };
  },
  async created() {
    await this.load();
  },
  methods: {
    async load() {
      const res = await apiFetch(\`/api/companies/\${auth.companyId}/cameras\`);
      if (res.ok) this.cameras = await res.json();
    },
  },
};
