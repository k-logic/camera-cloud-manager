const CameraList = {
  template: `
    <div>
      <div class="card-header">
        <h2>Cameras</h2>
      </div>
      <div class="card">
        <table v-if="cameras.length">
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
                <span class="status-badge" :class="c.is_active ? 'status-active' : 'status-inactive'">
                  {{ c.is_active ? "Active" : "Inactive" }}
                </span>
              </td>
              <td>
                <router-link :to="'/cameras/' + c.id" class="btn btn-sm">Detail</router-link>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-else style="color:#999">No cameras registered.</p>
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
      const res = await apiFetch(`/api/companies/${auth.companyId}/cameras`);
      if (res.ok) this.cameras = await res.json();
    },
  },
};
