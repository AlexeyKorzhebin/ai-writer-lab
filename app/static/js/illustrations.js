/* Illustration Prompt Generator — Alpine.js component */

function illustrationPanel(projectId) {
  return {
    open: false,
    sceneIdx: -1,
    templates: [],
    selectedTemplate: 'realistic_book',
    variants: [],
    selectedVariant: null,
    customDesc: '',
    generatedPrompt: '',
    loading: false,

    async init() {
      try { this.templates = await api('/illustration-templates'); } catch (_) {}
      window.addEventListener('open-illustrations', (e) => {
        this.sceneIdx = e.detail?.sceneIdx ?? -1;
        this.open = true;
        this.variants = [];
        this.generatedPrompt = '';
      });
    },

    async generateVariants() {
      if (this.sceneIdx < 0) { Toast.warning('Выберите сцену'); return; }
      this.loading = true;
      try {
        const res = await api(`/projects/${projectId}/narrative-spec/illustration-variants/${this.sceneIdx}`, { method: 'POST' });
        this.variants = res.variants || [];
        Toast.success('Варианты сгенерированы');
      } catch (e) { Toast.error(e.message); }
      this.loading = false;
    },

    async generatePrompt() {
      if (this.sceneIdx < 0) return;
      this.loading = true;
      const desc = this.selectedVariant
        ? `${this.selectedVariant.composition}. ${this.selectedVariant.lighting}. ${this.selectedVariant.key_details}`
        : this.customDesc;
      try {
        const res = await api(`/projects/${projectId}/narrative-spec/illustration-prompt/${this.sceneIdx}`, {
          method: 'POST',
          body: { template: this.selectedTemplate, description: desc }
        });
        this.generatedPrompt = res.prompt || '';
        Toast.success('Промпт сгенерирован');
      } catch (e) { Toast.error(e.message); }
      this.loading = false;
    },

    copyPrompt() {
      navigator.clipboard.writeText(this.generatedPrompt);
      Toast.success('Промпт скопирован');
    },

    async uploadImage() {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/png,image/jpeg,image/webp';
      input.onchange = async () => {
        const file = input.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        try {
          const res = await fetch(`/projects/${projectId}/illustrations/upload`, {
            method: 'POST', body: formData
          });
          const data = await res.json();
          Toast.success('Изображение загружено');
          window.dispatchEvent(new CustomEvent('chat-apply', {
            detail: { content: `\n![Иллюстрация](${data.path})\n`, mode: 'insert' }
          }));
        } catch (e) { Toast.error(e.message); }
      };
      input.click();
    }
  };
}

window.illustrationPanel = illustrationPanel;
