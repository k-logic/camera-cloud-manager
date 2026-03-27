const CompanyForm = {
  template: `
    <div>
      <h4 class="mb-3">{{ isEdit ? "Edit Company" : "New Company" }}</h4>
      <div class="card">
        <div class="card-body">
          <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
          <form @submit.prevent="submit">
            <div class="mb-3">
              <label class="form-label">Company Name</label>
              <input v-model="form.name" type="text" class="form-control" required>
            </div>
            <div class="d-flex gap-2">
              <button class="btn btn-primary" type="submit">{{ isEdit ? "Update" : "Create" }}</button>
              <router-link to="/companies" class="btn btn-secondary">Cancel</router-link>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
  data() {
    return { form: { name: "" }, error: null };
  },
  computed: {
    isEdit() { return !!this.$route.params.id; },
  },
  async created() {
    if (this.isEdit) {
      const res = await apiFetch(`/api/companies/${this.$route.params.id}`);
      if (res.ok) this.form = await res.json();
    }
  },
  methods: {
    async submit() {
      this.error = null;
      const url = this.isEdit
        ? `/api/companies/${this.$route.params.id}`
        : "/api/companies";
      const method = this.isEdit ? "PUT" : "POST";
      const res = await apiFetch(url, {
        method,
        body: JSON.stringify({ name: this.form.name }),
      });
      if (res.ok) {
        this.$router.push("/companies");
      } else {
        const data = await res.json();
        this.error = data.detail || "Error";
      }
    },
  },
};
