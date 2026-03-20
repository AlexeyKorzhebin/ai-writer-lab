/* Scene Tree — Alpine.js component with drag & drop */

function sceneTree(projectId, scenes) {
  return {
    scenes: scenes || [],
    selectedIdx: -1,
    editingTitle: null,

    init() {
      this.$nextTick(() => this.initSortable());
    },

    initSortable() {
      const el = this.$refs.treeList;
      if (!el || !window.Sortable) return;
      Sortable.create(el, {
        animation: 150,
        handle: '.drag-handle',
        ghostClass: 'opacity-30',
        onEnd: (evt) => {
          const item = this.scenes.splice(evt.oldIndex, 1)[0];
          this.scenes.splice(evt.newIndex, 0, item);
          this.reorder();
        }
      });
    },

    selectScene(idx) {
      this.selectedIdx = idx;
      window.dispatchEvent(new CustomEvent('scene-select', { detail: { index: idx, scene: this.scenes[idx] } }));
    },

    getStatus(scene) {
      if (!scene.content && !scene.summary) return 'empty';
      if (scene.content && scene.content.length > 500) return 'edited';
      return 'draft';
    },

    getStatusClass(scene) {
      const s = this.getStatus(scene);
      return { 'empty': 'status-empty', 'draft': 'status-draft', 'edited': 'status-edited', 'hq': 'status-hq' }[s] || 'status-empty';
    },

    wordCount(scene) {
      if (!scene.content) return 0;
      return scene.content.split(/\s+/).filter(Boolean).length;
    },

    async addScene() {
      const title = `Сцена ${this.scenes.length + 1}`;
      try {
        const res = await api(`/projects/${projectId}/narrative-spec`, { method: 'PUT', body: {
          scenes: [...this.scenes.map((s, i) => ({ ...s, order: i })), { title, order: this.scenes.length, participants: [], purpose: '', emotional_state: '', content: null, summary: null }]
        }});
        Toast.success('Сцена добавлена');
        window.location.reload();
      } catch (e) {
        Toast.error(e.message);
      }
    },

    async reorder() {
      const updated = this.scenes.map((s, i) => ({ ...s, order: i }));
      try {
        await api(`/projects/${projectId}/narrative-spec`, { method: 'PUT', body: { scenes: updated } });
      } catch (e) {
        Toast.error('Ошибка сортировки');
      }
    },

    startEditTitle(idx) {
      this.editingTitle = idx;
      this.$nextTick(() => {
        const input = this.$refs[`titleInput${idx}`];
        if (input) input.focus();
      });
    },

    async finishEditTitle(idx) {
      this.editingTitle = null;
    }
  };
}

window.sceneTree = sceneTree;
