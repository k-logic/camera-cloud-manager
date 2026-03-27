const { createApp, computed } = Vue;
const { createRouter, createWebHashHistory } = VueRouter;

const routes = [
  { path: "/login", component: Login },
  { path: "/", component: Dashboard },
  { path: "/cameras/:id", component: CameraDetail },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

router.beforeEach((to) => {
  if (to.path !== "/login" && !auth.isLoggedIn) {
    return "/login";
  }
});

const app = createApp({
  setup() {
    const isLoggedIn = computed(() => auth.isLoggedIn);
    const username = computed(() => auth.username);
    return { isLoggedIn, username };
  },
  methods: {
    logout() {
      auth.clear();
      this.$router.push("/login");
    },
  },
});

app.use(router);
app.mount("#app");
