const I18N = {
  fr: {
    title: 'Assistant',
    placeholder: 'Posez une question…',
    send: 'Envoyer',
    sources: 'Sources',
    empty: 'Posez une question sur la base documentaire.',
    error: 'Une erreur est survenue. Réessayez.',
    unauthorized: 'Clé API manquante ou invalide.',
    rateLimited: 'Trop de requêtes. Patientez un instant.',
    aria: 'Ouvrir le chat',
  },
  en: {
    title: 'Assistant',
    placeholder: 'Ask a question…',
    send: 'Send',
    sources: 'Sources',
    empty: 'Ask a question about the knowledge base.',
    error: 'Something went wrong. Try again.',
    unauthorized: 'Missing or invalid API key.',
    rateLimited: 'Too many requests. Please wait.',
    aria: 'Open chat',
  },
};

class RagServiceChat extends HTMLElement {
  static get observedAttributes() {
    return ['api-url', 'api-key', 'primary-color', 'position', 'lang', 'top-k'];
  }

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._state = {
      open: false,
      messages: [],
      loading: false,
      apiUrl: this.getAttribute('api-url') || 'http://localhost:8000',
      apiKey: this.getAttribute('api-key') || '',
      primaryColor: this.getAttribute('primary-color') || '#6C5CE7',
      position: this.getAttribute('position') || 'bottom-right',
      lang: this.getAttribute('lang') || 'fr',
      topK: parseInt(this.getAttribute('top-k') || '4', 10),
    };
  }

  connectedCallback() {
    this._render();
  }

  attributeChangedCallback(name, _oldValue, newValue) {
    if (name === 'top-k') {
      this._state.topK = parseInt(newValue || '4', 10);
    } else {
      const key = name.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
      this._state[key] = newValue;
    }
    if (this.isConnected) this._render();
  }

  _t(key) {
    const table = I18N[this._state.lang] || I18N.en;
    return table[key] || I18N.en[key];
  }

  _isRtl() {
    return ['ar', 'he', 'fa', 'ur'].includes(this._state.lang);
  }

  _styles() {
    return `
      :host {
        --primary: ${this._state.primaryColor};
        --bg: #ffffff;
        --text: #1a1a2e;
        --muted: #6b7280;
        --border: #e5e7eb;
        --radius: 16px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      }
      * { box-sizing: border-box; margin: 0; padding: 0; }
      .container {
        position: fixed;
        ${this._state.position === 'bottom-left' ? 'left: 20px;' : 'right: 20px;'}
        bottom: 20px;
        z-index: 2147483647;
        direction: ${this._isRtl() ? 'rtl' : 'ltr'};
      }
      .chat-button {
        width: 60px; height: 60px; border-radius: 50%;
        background: var(--primary); color: #fff; border: none;
        cursor: pointer; font-size: 26px; line-height: 60px;
        box-shadow: 0 4px 24px rgba(0,0,0,.16);
        transition: transform .15s ease;
      }
      .chat-button:hover { transform: scale(1.06); }
      .panel {
        display: ${this._state.open ? 'flex' : 'none'};
        flex-direction: column;
        position: absolute; bottom: 76px;
        ${this._state.position === 'bottom-left' ? 'left: 0;' : 'right: 0;'}
        width: 360px; max-width: calc(100vw - 40px); height: 520px; max-height: 70vh;
        background: var(--bg); color: var(--text);
        border: 1px solid var(--border); border-radius: var(--radius);
        box-shadow: 0 12px 48px rgba(0,0,0,.18); overflow: hidden;
      }
      .header {
        background: var(--primary); color: #fff;
        padding: 14px 16px; font-weight: 600; font-size: 15px;
      }
      .messages {
        flex: 1; overflow-y: auto; padding: 16px;
        display: flex; flex-direction: column; gap: 12px;
      }
      .empty { color: var(--muted); font-size: 14px; text-align: center; margin: auto; }
      .msg { max-width: 85%; padding: 10px 13px; border-radius: 14px; font-size: 14px; line-height: 1.45; white-space: pre-wrap; }
      .msg.user { align-self: flex-end; background: var(--primary); color: #fff; border-bottom-right-radius: 4px; }
      .msg.assistant { align-self: flex-start; background: #f3f4f6; color: var(--text); border-bottom-left-radius: 4px; }
      .msg.error { align-self: flex-start; background: #fee2e2; color: #991b1b; }
      .sources { margin-top: 8px; font-size: 12px; color: var(--muted); }
      .sources summary { cursor: pointer; user-select: none; }
      .sources li { margin: 4px 0; }
      .typing { align-self: flex-start; color: var(--muted); font-size: 14px; font-style: italic; }
      .composer { display: flex; gap: 8px; padding: 12px; border-top: 1px solid var(--border); }
      .composer input {
        flex: 1; padding: 10px 12px; border: 1px solid var(--border);
        border-radius: 10px; font-size: 14px; font-family: inherit; outline: none;
      }
      .composer input:focus { border-color: var(--primary); }
      .composer button {
        background: var(--primary); color: #fff; border: none;
        border-radius: 10px; padding: 0 16px; cursor: pointer; font-size: 14px; font-weight: 600;
      }
      .composer button:disabled { opacity: .5; cursor: not-allowed; }
    `;
  }

  _escape(text) {
    const div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
  }

  _messagesHtml() {
    if (this._state.messages.length === 0 && !this._state.loading) {
      return `<div class="empty">${this._escape(this._t('empty'))}</div>`;
    }
    const rows = this._state.messages.map((m) => {
      const cls = m.error ? 'error' : m.role;
      let html = `<div class="msg ${cls}">${this._escape(m.content)}</div>`;
      if (m.sources && m.sources.length > 0) {
        const items = m.sources
          .map((s) => `<li>${this._escape(s.doc_id)} — ${this._escape((s.text || '').slice(0, 120))}…</li>`)
          .join('');
        html += `<details class="sources"><summary>${this._escape(this._t('sources'))} (${m.sources.length})</summary><ul>${items}</ul></details>`;
      }
      return html;
    });
    if (this._state.loading) rows.push(`<div class="typing">…</div>`);
    return rows.join('');
  }

  _render() {
    this.shadowRoot.innerHTML = `
      <style>${this._styles()}</style>
      <div class="container">
        <div class="panel" part="panel">
          <div class="header" part="header">${this._escape(this._t('title'))}</div>
          <div class="messages">${this._messagesHtml()}</div>
          <form class="composer">
            <input type="text" autocomplete="off" placeholder="${this._escape(this._t('placeholder'))}" ${this._state.loading ? 'disabled' : ''} />
            <button type="submit" ${this._state.loading ? 'disabled' : ''}>${this._escape(this._t('send'))}</button>
          </form>
        </div>
        <button class="chat-button" part="button" aria-label="${this._escape(this._t('aria'))}">\u{1F4AC}</button>
      </div>
    `;
    this._bindEvents();
  }

  _bindEvents() {
    const button = this.shadowRoot.querySelector('.chat-button');
    if (button) button.addEventListener('click', () => this._toggle());
    const form = this.shadowRoot.querySelector('.composer');
    if (form) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const input = form.querySelector('input');
        const question = (input.value || '').trim();
        if (question) this._ask(question);
      });
    }
    const messages = this.shadowRoot.querySelector('.messages');
    if (messages) messages.scrollTop = messages.scrollHeight;
  }

  _toggle() {
    this._state.open = !this._state.open;
    this._render();
    if (this._state.open) {
      const input = this.shadowRoot.querySelector('.composer input');
      if (input) input.focus();
    }
  }

  async _ask(question) {
    this._state.messages.push({ role: 'user', content: question });
    this._state.loading = true;
    this._render();
    try {
      const headers = { 'Content-Type': 'application/json' };
      if (this._state.apiKey) headers['X-API-Key'] = this._state.apiKey;
      const res = await fetch(`${this._state.apiUrl}/rag/query`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ question, top_k: this._state.topK }),
      });
      if (!res.ok) {
        this._pushError(res.status);
        return;
      }
      const data = await res.json();
      this._state.messages.push({
        role: 'assistant',
        content: data.answer || '',
        sources: Array.isArray(data.sources) ? data.sources : [],
      });
    } catch (_err) {
      this._pushError(0);
    } finally {
      this._state.loading = false;
      this._render();
    }
  }

  _pushError(status) {
    let key = 'error';
    if (status === 401 || status === 422) key = 'unauthorized';
    else if (status === 429) key = 'rateLimited';
    this._state.messages.push({ role: 'assistant', content: this._t(key), error: true });
  }
}

customElements.define('rag-chat', RagServiceChat);
