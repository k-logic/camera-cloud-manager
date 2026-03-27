const CameraList = {
  template: `
    <div>
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h4 class="mb-0">{{ companyName }} &mdash; Cameras</h4>
        <div class="d-flex gap-2">
          <button @click="openCreateDialog" class="btn btn-primary btn-sm">
            <i class="bi bi-plus-lg me-1"></i>New Camera
          </button>
          <router-link to="/companies" class="btn btn-secondary btn-sm">Back</router-link>
        </div>
      </div>
      <div class="card">
        <div class="table-responsive">
          <table v-if="cameras.length" class="table table-hover mb-0">
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
                  <span class="badge" :class="c.is_active ? 'bg-success' : 'bg-danger'">
                    {{ c.is_active ? "Active" : "Inactive" }}
                  </span>
                </td>
                <td>
                  <button @click="toggleActive(c)" class="btn btn-sm" :class="c.is_active ? 'btn-outline-secondary' : 'btn-outline-success'">
                    {{ c.is_active ? "Disable" : "Enable" }}
                  </button>
                </td>
                <td class="text-end">
                  <div class="d-flex gap-1 justify-content-end">
                    <router-link :to="'/cameras/' + c.id" class="btn btn-sm btn-primary">Detail</router-link>
                    <button @click="remove(c)" class="btn btn-sm btn-danger">Delete</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="!cameras.length" class="card-body text-muted">No cameras registered yet.</div>
      </div>

      <!-- Create Modal -->
      <div v-if="showCreate" class="modal d-block" tabindex="-1" style="background:rgba(0,0,0,.4)">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">New Camera</h5>
              <button type="button" class="btn-close" @click="showCreate=false"></button>
            </div>
            <div class="modal-body">
              <div v-if="createError" class="alert alert-danger py-2">{{ createError }}</div>
              <form @submit.prevent="create">
                <div class="mb-3">
                  <label class="form-label">Camera Name</label>
                  <input v-model="newName" type="text" class="form-control" required autofocus>
                </div>
                <div class="d-flex gap-2">
                  <button class="btn btn-primary" type="submit">Create</button>
                  <button type="button" class="btn btn-secondary" @click="showCreate=false">Cancel</button>
                </div>
              </form>
            </div>
          </div>
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
