const CameraDetail = {
  template: `
    <div v-if="camera">
      <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
        <h4 v-if="!editingName" class="mb-0" @dblclick="startEditName" style="cursor:pointer" title="Double-click to edit">{{ camera.name }}</h4>
        <div v-else class="d-flex align-items-center gap-2">
          <input v-model="editName" @keyup.enter="saveName" @keyup.escape="editingName=false" ref="nameInput" class="form-control" style="font-size:1.2em;font-weight:bold;max-width:300px">
          <button class="btn btn-primary btn-sm" @click="saveName">Save</button>
          <button class="btn btn-secondary btn-sm" @click="editingName=false">Cancel</button>
        </div>
        <router-link to="/" class="btn btn-secondary btn-sm">
          <i class="bi bi-arrow-left me-1"></i>Back
        </router-link>
      </div>

      <!-- Camera Info -->
      <div class="card mb-3">
        <div class="card-body">
          <h6 class="card-title">Camera Info</h6>
          <div class="row g-3">
            <div class="col-6 col-md-3">
              <small class="text-muted d-block">ID</small>
              <span>{{ camera.id }}</span>
            </div>
            <div class="col-6 col-md-3">
              <small class="text-muted d-block">Camera Key</small>
              <span class="d-flex align-items-center gap-1 flex-wrap">
                <code class="camera-key">{{ camera.camera_key }}</code>
                <button @click="copyKey" class="btn btn-outline-secondary" style="padding:1px 6px;font-size:0.75em">Copy</button>
              </span>
            </div>
            <div class="col-6 col-md-3">
              <small class="text-muted d-block">Connection</small>
              <span v-if="camera.status" class="badge" :class="camera.status.is_online ? 'bg-success' : 'bg-danger'">
                {{ camera.status.is_online ? "Online" : "Offline" }}
              </span>
              <span v-else class="badge bg-secondary">Unknown</span>
            </div>
            <div class="col-6 col-md-3">
              <small class="text-muted d-block">Created</small>
              <span>{{ formatDate(camera.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Stream Control -->
      <div class="card mb-3">
        <div class="card-body">
          <h6 class="card-title">Stream Control</h6>
          <div class="row g-3 mb-3">
            <div class="col-6 col-md-3">
              <small class="text-muted d-block">Desired State</small>
              <span class="badge" :class="settings.stream_running ? 'bg-success' : 'bg-danger'">
                {{ settings.stream_running ? "Running" : "Stopped" }}
              </span>
            </div>
            <div class="col-6 col-md-3">
              <small class="text-muted d-block">Actual State</small>
              <span v-if="camera.status" class="badge" :class="camera.status.stream_running ? 'bg-success' : 'bg-danger'">
                {{ camera.status.stream_running ? "Running" : "Stopped" }}
              </span>
              <span v-else class="badge bg-secondary">Unknown</span>
            </div>
          </div>
          <div v-if="controlMsg" class="alert py-2" :class="controlMsgType === 'ok' ? 'alert-success' : 'alert-danger'">{{ controlMsg }}</div>
          <div class="d-flex gap-2 flex-wrap">
            <button class="btn btn-success btn-sm" @click="streamControl(true)" :disabled="settings.stream_running">
              <i class="bi bi-play-fill me-1"></i>Start
            </button>
            <button class="btn btn-secondary btn-sm" @click="streamControl(false)" :disabled="!settings.stream_running">
              <i class="bi bi-stop-fill me-1"></i>Stop
            </button>
          </div>
        </div>
      </div>

      <!-- Stream Settings -->
      <div class="card mb-3">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h6 class="card-title mb-0">Stream Settings</h6>
            <span class="version-badge">v{{ settings.settings_version }}</span>
          </div>
          <div class="row g-3 mb-3">
            <div class="col-sm-6 col-md-3">
              <label class="form-label">Camera Input</label>
              <select v-model="settingsForm.capture_resolution" @change="saveSettings" class="form-select form-select-sm">
                <option value="1280x720">HD (1280x720)</option>
                <option value="1920x1080">Full HD (1920x1080)</option>
                <option value="3840x2160">4K (3840x2160)</option>
              </select>
            </div>
            <div class="col-sm-6 col-md-3">
              <label class="form-label">Output Resolution</label>
              <select v-model="settingsForm.output_resolution" @change="saveSettings" class="form-select form-select-sm">
                <option value="1920x1080">Full HD (1920x1080)</option>
              </select>
            </div>
            <div class="col-sm-6 col-md-3">
              <label class="form-label">FPS</label>
              <select v-model.number="settingsForm.fps" @change="saveSettings" class="form-select form-select-sm">
                <option :value="30">30</option>
                <option :value="60">60</option>
              </select>
            </div>
            <div class="col-sm-6 col-md-3">
              <label class="form-label">Bitrate (kbps)</label>
              <input v-model.number="settingsForm.bitrate" type="number" min="800" max="50000" @change="saveSettings" class="form-control form-control-sm">
            </div>
          </div>
          <div class="mb-3">
            <label class="form-label">Stream URL</label>
            <input v-model="settingsForm.stream_url" type="text" placeholder="rtmp://..." @change="saveSettings" class="form-control form-control-sm">
          </div>
          <div v-if="settingsMsg" class="alert py-2" :class="settingsMsgType === 'ok' ? 'alert-success' : 'alert-danger'">{{ settingsMsg }}</div>
        </div>
      </div>

      <!-- Device Status -->
      <div class="card mb-3">
        <div class="card-body">
          <h6 class="card-title">Device Status</h6>
          <div v-if="camera.status" class="row g-3">
            <div class="col-6 col-md-3">
              <small class="text-muted d-block">Online</small>
              <span class="badge" :class="camera.status.is_online ? 'bg-success' : 'bg-danger'">
                {{ camera.status.is_online ? "Online" : "Offline" }}
              </span>
            </div>
            <div class="col-6 col-md-3">
              <small class="text-muted d-block">Stream</small>
              <span class="badge" :class="camera.status.stream_running ? 'bg-success' : 'bg-danger'">
                {{ camera.status.stream_running ? "Running" : "Stopped" }}
              </span>
            </div>
            <div class="col-6 col-md-3" v-if="camera.status.last_seen">
              <small class="text-muted d-block">Last Seen</small>
              <span>{{ formatDate(camera.status.last_seen) }}</span>
            </div>
            <div class="col-6 col-md-3" v-if="camera.status.cpu_usage != null">
              <small class="text-muted d-block">CPU</small>
              <span>{{ camera.status.cpu_usage }}%</span>
            </div>
            <div class="col-6 col-md-3" v-if="camera.status.gpu_usage != null">
              <small class="text-muted d-block">GPU</small>
              <span>{{ camera.status.gpu_usage }}%</span>
            </div>
            <div class="col-6 col-md-3" v-if="camera.status.temperature != null">
              <small class="text-muted d-block">Temp</small>
              <span>{{ camera.status.temperature }}\u00b0C</span>
            </div>
            <div class="col-6 col-md-3" v-if="camera.status.mem_used != null">
              <small class="text-muted d-block">Memory</small>
              <span>{{ camera.status.mem_used }} / {{ camera.status.mem_total }} MB</span>
            </div>
            <div class="col-6 col-md-3" v-if="camera.status.uptime != null">
              <small class="text-muted d-block">Uptime</small>
              <span>{{ formatUptime(camera.status.uptime) }}</span>
            </div>
          </div>
          <p v-else class="text-muted mb-0">No status data yet. Camera has not connected.</p>
        </div>
      </div>
    </div>
    <div v-else class="card"><div class="card-body">Loading...</div></div>
  `,
  data() {
    return {
      camera: null,
      settings: {},
      settingsForm: { camera_source: "mipi", capture_resolution: "1920x1080", output_resolution: "1920x1080", fps: 30, bitrate: 4000, stream_url: "" },
      settingsMsg: null,
      settingsMsgType: "ok",
      controlMsg: null,
      controlMsgType: "ok",
      editingName: false,
      editName: "",
      keyCopied: false,
      _pollTimer: null,
    };
  },
  async created() {
    await this.load();
    this._pollTimer = setInterval(() => this.refreshStatus(), 2000);
  },
  beforeUnmount() {
    if (this._pollTimer) clearInterval(this._pollTimer);
  },
  methods: {
    async refreshStatus() {
      const res = await apiFetch(`/api/cameras/${this.$route.params.id}`);
      if (res.ok) {
        const data = await res.json();
        this.camera.status = data.status;
        if (data.settings) {
          this.settings = data.settings;
        }
      }
    },
    copyKey() {
      navigator.clipboard.writeText(this.camera.camera_key);
      this.keyCopied = true;
      setTimeout(() => { this.keyCopied = false; }, 2000);
    },
    startEditName() {
      this.editName = this.camera.name;
      this.editingName = true;
      this.$nextTick(() => { if (this.$refs.nameInput) this.$refs.nameInput.focus(); });
    },
    async saveName() {
      if (!this.editName.trim()) return;
      const res = await apiFetch(`/api/cameras/${this.camera.id}`, {
        method: "PUT",
        body: JSON.stringify({ name: this.editName.trim() }),
      });
      if (res.ok) {
        this.camera.name = this.editName.trim();
        this.editingName = false;
      }
    },
    async load() {
      const res = await apiFetch(`/api/cameras/${this.$route.params.id}`);
      if (res.ok) {
        this.camera = await res.json();
        if (this.camera.settings) {
          this.settings = this.camera.settings;
          this.settingsForm = {
            camera_source: this.settings.camera_source || "mipi",
            capture_resolution: `${this.settings.width}x${this.settings.height}`,
            output_resolution: `${this.settings.output_width}x${this.settings.output_height}`,
            fps: this.settings.fps,
            bitrate: this.settings.bitrate,
            stream_url: this.settings.stream_url || "",
          };
        }
      }
    },
    async streamControl(start) {
      this.controlMsg = null;
      const res = await apiFetch(`/api/cameras/${this.$route.params.id}/settings`, {
        method: "PUT",
        body: JSON.stringify({ stream_running: start }),
      });
      if (res.ok) {
        const updated = await res.json();
        this.settings = updated;
        this.controlMsg = start ? "Start command issued" : "Stop command issued";
        this.controlMsgType = "ok";
      } else {
        const data = await res.json();
        this.controlMsg = data.detail || "Error";
        this.controlMsgType = "error";
      }
    },
    async saveSettings() {
      this.settingsMsg = null;
      const [cw, ch] = this.settingsForm.capture_resolution.split("x").map(Number);
      const [ow, oh] = this.settingsForm.output_resolution.split("x").map(Number);
      const body = {
        camera_source: this.settingsForm.camera_source,
        width: cw,
        height: ch,
        output_width: ow,
        output_height: oh,
        fps: this.settingsForm.fps,
        bitrate: this.settingsForm.bitrate,
        stream_url: this.settingsForm.stream_url || null,
      };
      const res = await apiFetch(`/api/cameras/${this.$route.params.id}/settings`, {
        method: "PUT",
        body: JSON.stringify(body),
      });
      if (res.ok) {
        const updated = await res.json();
        this.settings = updated;
        this.settingsMsg = `Settings saved (v${updated.settings_version})`;
        this.settingsMsgType = "ok";
      } else {
        const data = await res.json();
        this.settingsMsg = data.detail || "Error saving settings";
        this.settingsMsgType = "error";
      }
    },
    formatDate(dt) {
      if (!dt) return "-";
      return new Date(dt).toLocaleString("ja-JP");
    },
    formatUptime(seconds) {
      const h = Math.floor(seconds / 3600);
      const m = Math.floor((seconds % 3600) / 60);
      return `${h}h ${m}m`;
    },
  },
};
