const CameraDetail = {
  template: `
    <div v-if="camera">
      <div class="card-header">
        <h2 v-if="!editingName" @dblclick="startEditName" style="cursor:pointer" title="Double-click to edit">{{ camera.name }}</h2>
        <div v-else style="display:flex;align-items:center;gap:8px">
          <input v-model="editName" @keyup.enter="saveName" @keyup.escape="editingName=false" ref="nameInput" class="form-control" style="font-size:1.4em;font-weight:bold;padding:4px 8px;width:300px">
          <button class="btn" @click="saveName">Save</button>
          <button class="btn btn-secondary" @click="editingName=false">Cancel</button>
        </div>
        <router-link :to="'/companies/' + camera.company_id + '/cameras'" class="btn btn-secondary">Back to Cameras</router-link>
      </div>

      <!-- Camera Info -->
      <div class="card">
        <h3 class="section-title">Camera Info</h3>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">ID</span>
            <span>{{ camera.id }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Camera Key</span>
            <span style="display:flex;align-items:center;gap:6px">
              <code class="camera-key">{{ camera.camera_key }}</code>
              <button @click="copyKey" class="btn btn-secondary" style="padding:2px 8px;font-size:0.8em">Copy</button>
            </span>
          </div>
          <div class="info-item">
            <span class="info-label">Connection</span>
            <span v-if="camera.status" class="status-badge" :class="camera.status.is_online ? 'status-active' : 'status-inactive'">
              {{ camera.status.is_online ? "Online" : "Offline" }}
            </span>
            <span v-else class="status-badge" style="background:#888">Unknown</span>
          </div>
          <div class="info-item">
            <span class="info-label">Created</span>
            <span>{{ formatDate(camera.created_at) }}</span>
          </div>
        </div>
      </div>

      <!-- Stream Control -->
      <div class="card">
        <h3 class="section-title">Stream Control</h3>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">Desired State</span>
            <span class="status-badge" :class="settings.stream_running ? 'status-active' : 'status-inactive'">
              {{ settings.stream_running ? "Running" : "Stopped" }}
            </span>
          </div>
          <div class="info-item">
            <span class="info-label">Actual State</span>
            <span v-if="camera.status" class="status-badge" :class="camera.status.stream_running ? 'status-active' : 'status-inactive'">
              {{ camera.status.stream_running ? "Running" : "Stopped" }}
            </span>
            <span v-else class="status-badge" style="background:#888">Unknown</span>
          </div>
        </div>
        <p v-if="controlMsg" :class="controlMsgType === 'ok' ? 'success-msg' : 'error-msg'">{{ controlMsg }}</p>
        <div class="form-actions" style="gap:8px; display:flex">
          <button class="btn" @click="streamControl(true)" :disabled="settings.stream_running">Start</button>
          <button class="btn btn-secondary" @click="streamControl(false)" :disabled="!settings.stream_running">Stop</button>
          <button class="btn btn-danger" @click="reboot" style="margin-left:auto">Reboot</button>
        </div>
      </div>

      <!-- Settings -->
      <div class="card">
        <div class="card-header" style="margin-bottom:12px">
          <h3 class="section-title" style="margin:0">Stream Settings</h3>
          <span class="version-badge">v{{ settings.settings_version }}</span>
        </div>
        <div class="settings-grid">
            <div class="form-group">
              <label>Camera Input</label>
              <select v-model="settingsForm.capture_resolution" @change="saveSettings">
                <option value="1280x720">HD (1280x720)</option>
                <option value="1920x1080">Full HD (1920x1080)</option>
                <option value="3840x2160">4K (3840x2160)</option>
              </select>
            </div>
            <div class="form-group">
              <label>Output Resolution</label>
              <select v-model="settingsForm.output_resolution" @change="saveSettings">
                <option value="1920x1080">Full HD (1920x1080)</option>
              </select>
            </div>
            <div class="form-group">
              <label>FPS</label>
              <select v-model.number="settingsForm.fps" @change="saveSettings">
                <option :value="30">30</option>
                <option :value="60">60</option>
              </select>
            </div>
            <div class="form-group">
              <label>Bitrate (kbps)</label>
              <input v-model.number="settingsForm.bitrate" type="number" min="800" max="50000" @change="saveSettings">
            </div>
          </div>
          <div class="form-group">
            <label>Stream URL</label>
            <input v-model="settingsForm.stream_url" type="text" placeholder="rtmp://..." @change="saveSettings">
          </div>
          <p v-if="settingsMsg" :class="settingsMsgType === 'ok' ? 'success-msg' : 'error-msg'">{{ settingsMsg }}</p>
      </div>

      <!-- Status -->
      <div class="card">
        <h3 class="section-title">Device Status</h3>
        <div v-if="camera.status">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">Online</span>
              <span class="status-badge" :class="camera.status.is_online ? 'status-active' : 'status-inactive'">
                {{ camera.status.is_online ? "Online" : "Offline" }}
              </span>
            </div>
            <div class="info-item">
              <span class="info-label">Stream</span>
              <span class="status-badge" :class="camera.status.stream_running ? 'status-active' : 'status-inactive'">
                {{ camera.status.stream_running ? "Running" : "Stopped" }}
              </span>
            </div>
            <div class="info-item" v-if="camera.status.last_seen">
              <span class="info-label">Last Seen</span>
              <span>{{ formatDate(camera.status.last_seen) }}</span>
            </div>
            <div class="info-item" v-if="camera.status.cpu_usage != null">
              <span class="info-label">CPU</span>
              <span>{{ camera.status.cpu_usage }}%</span>
            </div>
            <div class="info-item" v-if="camera.status.gpu_usage != null">
              <span class="info-label">GPU</span>
              <span>{{ camera.status.gpu_usage }}%</span>
            </div>
            <div class="info-item" v-if="camera.status.temperature != null">
              <span class="info-label">Temp</span>
              <span>{{ camera.status.temperature }}\u00b0C</span>
            </div>
            <div class="info-item" v-if="camera.status.mem_used != null">
              <span class="info-label">Memory</span>
              <span>{{ camera.status.mem_used }} / {{ camera.status.mem_total }} MB</span>
            </div>
            <div class="info-item" v-if="camera.status.uptime != null">
              <span class="info-label">Uptime</span>
              <span>{{ formatUptime(camera.status.uptime) }}</span>
            </div>
          </div>
        </div>
        <p v-else style="color:#999">No status data yet. Camera has not connected.</p>
      </div>
    </div>
    <div v-else class="card">
      <p>Loading...</p>
    </div>
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
    async deleteCamera() {
      if (!confirm(`"${this.camera.name}" を削除しますか？`)) return;
      const res = await apiFetch(`/api/cameras/${this.camera.id}`, { method: "DELETE" });
      if (res.ok) {
        this.$router.push(`/companies/${this.camera.company_id}/cameras`);
      }
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
    async reboot() {
      if (!confirm("Reboot this camera?")) return;
      this.controlMsg = null;
      const res = await apiFetch(`/api/cameras/${this.$route.params.id}/reboot`, {
        method: "POST",
      });
      if (res.ok) {
        this.controlMsg = "Reboot command issued";
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
