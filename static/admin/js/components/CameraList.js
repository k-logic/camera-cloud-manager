const CameraList = {
  template: `
    <div>
      <div class="card-header">
        <h2>{{ companyName }} — Cameras</h2>
        <div style="display:flex;gap:8px">
          <button @click="openCreateDialog" class="btn">+ New Camera</button>
          <router-link to="/companies" class="btn btn-secondary">Back</router-link>
        </div>
      </div>
      <div class="card">
        <table v-if="cameras.length">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Status</th>
              <th>Active</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in cameras" :key="c.id">
              <td>{{ c.id }}</td>
              <td>
                <router-link :to="'/cameras/' + c.id">{{ c.name }}</router-link>
              </td>
              <td>
                <span class="status-badge" :class="c.is_active ? 'status-active' : 'status-inactive'">
                  {{ c.is_active ? "Active" : "Inactive" }}
                </span>
              </td>
              <td>
                <button @click="toggleActive(c)" class="btn btn-sm" :class="c.is_active ? 'btn-secondary' : ''">
                  {{ c.is_active ? "Disable" : "Enable" }}
                </button>
              </td>
              <td class="actions">
                <router-link :to="'/cameras/' + c.id" class="btn btn-sm">Detail</router-link>
                <button @click="remove(c)" class="btn btn-sm btn-danger">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-else style="color:#999">No cameras registered yet.</p>
      </div>

      <!-- Create Dialog -->
      <div v-if="showCreate" class="modal-overlay" @click.self="showCreate=false">
        <div class="modal-box">
          <h3>New Camera</h3>
          <p v-if="createError" class="error-msg">{{ createError }}</p>
          <form @submit.prevent="create">
            <div class="form-group">
              <label>Camera Name</label>
              <input v-model="newName" type="text" required autofocus>
            </div>
            <div class="form-actions">
              <button class="btn" type="submit">Create</button>
              <button type="button" class="btn btn-secondary" @click="showCreate=false">Cancel</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      cameras: [],
      companyName: "",
      showCreate: false,
      newName: "",
      createError: null,
    };
  },
  computed: {
    companyId() { return this.$route.params.companyId; },
  },
  async created() {
    await this.load();
  },
  methods: {
    async load() {
      const res = await apiFetch(`/api/companies/${this.companyId}/cameras`);
      if (res.ok) this.cameras = await res.json();
      // Get company name
      const cres = await apiFetch(`/api/companies/${this.companyId}`);
      if (cres.ok) {
        const company = await cres.json();
        this.companyName = company.name;
      }
    },
    openCreateDialog() {
      this.newName = "";
      this.createError = null;
      this.showCreate = true;
    },
    async create() {
      this.createError = null;
      const res = await apiFetch(`/api/companies/${this.companyId}/cameras`, {
        method: "POST",
        body: JSON.stringify({ name: this.newName }),
      });
      if (res.ok) {
        this.showCreate = false;
        await this.load();
      } else {
        const data = await res.json();
        this.createError = data.detail || "Error";
      }
    },
    async toggleActive(c) {
      await apiFetch(`/api/cameras/${c.id}`, {
        method: "PUT",
        body: JSON.stringify({ is_active: !c.is_active }),
      });
      await this.load();
    },
    async remove(c) {
      if (!confirm(`Delete camera "${c.name}"?`)) return;
      const res = await apiFetch(`/api/cameras/${c.id}`, { method: "DELETE" });
      if (res.ok) await this.load();
    },
  },
};
