/* Scene Editor — Alpine.js component with autosave */

function sceneEditor(projectId) {
  return {
    content: '',
    sceneIdx: -1,
    sceneTitle: '',
    saving: false,
    saved: true,
    lastSaved: null,
    dirty: false,
    wordCount: 0,
    _debounceTimer: null,

    init() {
      window.addEventListener('scene-select', (e) => {
        this.loadScene(e.detail.index, e.detail.scene);
      });
      window.addEventListener('chat-apply', (e) => {
        this.applyFromChat(e.detail.content, e.detail.mode);
      });
      window.addEventListener('shortcut-save', () => this.save());
      window.addEventListener('shortcut-generate', () => this.generate());
      window.addEventListener('shortcut-illustrate', () => {
        window.dispatchEvent(new CustomEvent('open-illustrations', { detail: { sceneIdx: this.sceneIdx } }));
      });
    },

    loadScene(idx, scene) {
      if (this.dirty) this.save();
      this.sceneIdx = idx;
      this.sceneTitle = scene.title || `Сцена ${idx + 1}`;
      this.content = scene.content || '';
      this.dirty = false;
      this.saved = true;
      this.updateWordCount();
    },

    onInput() {
      this.dirty = true;
      this.saved = false;
      this.updateWordCount();
      clearTimeout(this._debounceTimer);
      this._debounceTimer = setTimeout(() => this.save(), 3000);
    },

    updateWordCount() {
      this.wordCount = this.content.trim() ? this.content.trim().split(/\s+/).length : 0;
    },

    async save() {
      if (!this.dirty || this.sceneIdx < 0) return;
      this.saving = true;
      try {
        await api(`/projects/${projectId}/narrative-spec`, {
          method: 'PUT',
          body: { scenes: [{ order: this.sceneIdx, content: this.content }] }
        });
        this.dirty = false;
        this.saved = true;
        this.lastSaved = new Date().toLocaleTimeString();
      } catch (e) {
        Toast.error('Ошибка сохранения: ' + e.message);
      }
      this.saving = false;
    },

    async generate() {
      if (this.sceneIdx < 0) { Toast.warning('Выберите сцену'); return; }
      const p = Toast.progress('Генерация сцены...');
      try {
        const res = await api(`/projects/${projectId}/narrative-spec/generate-scene/${this.sceneIdx}`, { method: 'POST' });
        if (res.content) {
          this.content = res.content;
          this.dirty = true;
          this.onInput();
          p.done('Сцена сгенерирована');
        } else if (res.error) {
          p.fail(res.error);
        }
      } catch (e) { p.fail(e.message); }
    },

    applyFromChat(text, mode) {
      if (mode === 'replace') {
        this.content = text;
      } else if (mode === 'insert') {
        const textarea = this.$refs.editorTextarea;
        if (textarea) {
          const pos = textarea.selectionStart;
          this.content = this.content.slice(0, pos) + text + this.content.slice(pos);
        } else {
          this.content += '\n' + text;
        }
      }
      this.dirty = true;
      this.saved = false;
      this.updateWordCount();
    },

    get saveStatus() {
      if (this.saving) return 'Сохранение...';
      if (this.saved) return this.lastSaved ? `Сохранено ${this.lastSaved}` : 'Сохранено';
      return 'Не сохранено';
    },

    get saveStatusIcon() {
      if (this.saving) return '⏳';
      if (this.saved) return '✓';
      return '⚠';
    }
  };
}

window.sceneEditor = sceneEditor;
