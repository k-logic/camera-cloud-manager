const CompanyList = {
  template: `
    <div>
      <div class="card-header">
        <h2>Companies</h2>
        <router-link to="/companies/new" class="btn">+ New Company</router-link>
      </div>
      <div class="card">
        <table v-if="companies.length">
          <thead>
            <tr><th>ID</th><th>Name</th><th></th></tr>
          </thead>
          <tbody>
            <tr v-for="c in companies" :key="c.id">
              <td>{{ c.id }}</td>
              <td>{{ c.name }}</td>
              <td class="actions">
                <router-link :to="'/companies/' + c.id + '/cameras'" class="btn btn-sm">Cameras</router-link>
                <router-link :to="'/companies/' + c.id + '/edit'" class="btn btn-sm btn-secondary">Edit</router-link>
                <button @click="remove(c)" class="btn btn-sm btn-danger">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-else style="color:#999">No companies yet.</p>
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
      if (!confirm(`Delete "${c.name}"?`)) return;
      const res = await apiFetch(`/api/companies/${c.id}`, { method: "DELETE" });
      if (res.ok) await this.load();
    },
  },
};
