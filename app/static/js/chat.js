/* AI Chat Panel — Alpine.js component */

function chatPanel(projectId) {
  return {
    messages: [],
    input: '',
    loading: false,
    taskName: 'Общий чат',
    sceneIdx: -1,
    showRefs: false,
    refQuery: '',
    budgetPct: 0,

    refTypes: [
      { type: 'scene', label: 'Сцена', prefix: '@scene:' },
      { type: 'char', label: 'Персонаж', prefix: '@char:' },
      { type: 'world', label: 'Мир', prefix: '@world' },
      { type: 'location', label: 'Локация', prefix: '@location:' },
      { type: 'plot', label: 'Сюжет', prefix: '@plot' },
      { type: 'structure', label: 'Структура', prefix: '@structure' },
      { type: 'prev', label: 'Пред. сцена', prefix: '@prev' },
      { type: 'style', label: 'Стиль', prefix: '@style' },
      { type: 'all-chars', label: 'Все персонажи', prefix: '@all-chars' },
    ],

    async init() {
      await this.loadMessages();
    },

    async loadMessages() {
      try {
        this.messages = await api(`/projects/${projectId}/chat/messages?task_name=${encodeURIComponent(this.taskName)}`);
      } catch (e) {
        this.messages = [];
      }
    },

    onInput(e) {
      const val = e.target.value;
      const cursor = e.target.selectionStart;
      const before = val.substring(0, cursor);
      const atMatch = before.match(/@(\w*)$/);
      if (atMatch) {
        this.showRefs = true;
        this.refQuery = atMatch[1].toLowerCase();
      } else {
        this.showRefs = false;
      }
    },

    insertRef(ref) {
      const textarea = this.$refs.chatInput;
      const cursor = textarea.selectionStart;
      const before = textarea.value.substring(0, cursor).replace(/@\w*$/, '');
      const after = textarea.value.substring(cursor);
      this.input = before + ref.prefix + ' ' + after;
      this.showRefs = false;
      this.$nextTick(() => textarea.focus());
    },

    get filteredRefs() {
      if (!this.refQuery) return this.refTypes;
      return this.refTypes.filter(r =>
        r.label.toLowerCase().includes(this.refQuery) ||
        r.type.includes(this.refQuery)
      );
    },

    async send() {
      if (!this.input.trim() || this.loading) return;

      const msg = this.input.trim();
      this.input = '';
      this.messages.push({ role: 'user', content: msg });
      this.loading = true;

      const assistantMsg = { role: 'assistant', content: '' };
      this.messages.push(assistantMsg);
      this.scrollToBottom();

      try {
        const response = await fetch(`/projects/${projectId}/chat/send`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: msg,
            task_name: this.taskName,
            scene_idx: this.sceneIdx,
          }),
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.content) {
                  assistantMsg.content += data.content;
                  this.scrollToBottom();
                }
                if (data.error) {
                  Toast.error(data.error);
                }
              } catch (_) {}
            }
          }
        }
      } catch (e) {
        Toast.error('Ошибка: ' + e.message);
        assistantMsg.content = 'Ошибка соединения. Попробуйте снова.';
      }

      this.loading = false;
      this.scrollToBottom();
    },

    scrollToBottom() {
      this.$nextTick(() => {
        const el = this.$refs.chatMessages;
        if (el) el.scrollTop = el.scrollHeight;
      });
    },

    quickAction(action) {
      const actions = {
        generate: 'Сгенерируй текст для текущей сцены',
        continue: 'Продолжи текст с того места, где остановились',
        dialogue: 'Добавь диалог между персонажами текущей сцены',
        setting: 'Опиши обстановку и атмосферу текущей сцены',
        review: 'Сделай ревью текущей сцены: оцени качество, укажи сильные и слабые стороны',
        illustrate: 'Предложи визуальное описание для иллюстрации текущей сцены',
      };
      this.input = actions[action] || action;
      this.send();
    },

    async newTask() {
      const name = prompt('Название новой задачи:', 'Новая задача');
      if (!name) return;
      try {
        await api(`/projects/${projectId}/chat/new-task`, { method: 'POST', body: { task_name: name } });
        this.taskName = name;
        this.messages = [];
        Toast.success(`Задача "${name}" создана`);
      } catch (e) { Toast.error(e.message); }
    },

    applyToEditor(content, mode = 'replace') {
      window.dispatchEvent(new CustomEvent('chat-apply', { detail: { content, mode } }));
      Toast.success('Текст применён к редактору');
    },

    copyToClipboard(text) {
      navigator.clipboard.writeText(text);
      Toast.success('Скопировано');
    },

    formatMessage(content) {
      if (!content) return '';
      return content
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code class="px-1 rounded bg-gray-100 dark:bg-gray-800 text-sm">$1</code>')
        .replace(/\n/g, '<br>');
    }
  };
}

window.chatPanel = chatPanel;
