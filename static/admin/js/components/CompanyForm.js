const CompanyForm = {
  template: `
    <div>
      <h2 style="margin-bottom:16px">{{ isEdit ? "Edit Company" : "New Company" }}</h2>
      <div class="card">
        <p v-if="error" class="error-msg">{{ error }}</p>
        <form @submit.prevent="submit">
          <div class="form-group">
            <label>Company Name</label>
            <input v-model="form.name" type="text" required>
          </div>
          <div class="form-actions">
            <button class="btn" type="submit">{{ isEdit ? "Update" : "Create" }}</button>
            <router-link to="/companies" class="btn btn-secondary">Cancel</router-link>
          </div>
        </form>
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
