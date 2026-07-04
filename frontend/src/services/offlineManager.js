/**
 * Offline Support Module — IndexedDB persistence + local model management
 * Handles chat history, proactive alerts, and WebLLM model caching
 */

class OfflineManager {
  constructor() {
    this.db = null;
    this.isOnline = navigator.onLine;
    this.modelReady = false;
    this.syncQueue = [];

    window.addEventListener('online', () => this.onOnline());
    window.addEventListener('offline', () => this.onOffline());
  }

  /**
   * Initialize IndexedDB for persistent chat storage
   */
  async initialize() {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open('MapleJourney', 1);

      req.onerror = () => reject(req.error);
      req.onsuccess = () => {
        this.db = req.result;
        console.log('✅ IndexedDB initialized');
        resolve();
      };

      req.onupgradeneeded = (event) => {
        const db = event.target.result;

        // Chat messages store
        if (!db.objectStoreNames.contains('chat_messages')) {
          const chatStore = db.createObjectStore('chat_messages', {
            keyPath: 'id',
            autoIncrement: true,
          });
          chatStore.createIndex('session_id', 'session_id', { unique: false });
          chatStore.createIndex('created_at', 'created_at', { unique: false });
        }

        // Sync queue (for offline changes)
        if (!db.objectStoreNames.contains('sync_queue')) {
          db.createObjectStore('sync_queue', { keyPath: 'id', autoIncrement: true });
        }

        // Proactive alerts cache
        if (!db.objectStoreNames.contains('alerts')) {
          const alertStore = db.createObjectStore('alerts', {
            keyPath: 'id',
            autoIncrement: true,
          });
          alertStore.createIndex('user_id', 'user_id', { unique: false });
          alertStore.createIndex('severity', 'severity', { unique: false });
        }

        // Model metadata
        if (!db.objectStoreNames.contains('model_metadata')) {
          db.createObjectStore('model_metadata', { keyPath: 'key' });
        }
      };
    });
  }

  /**
   * Save a chat message locally for offline access
   */
  async saveChatMessageLocally(message) {
    if (!this.db) return;

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(['chat_messages'], 'readwrite');
      const store = tx.objectStore('chat_messages');
      const req = store.add({
        ...message,
        saved_offline: true,
        created_at: new Date().toISOString(),
      });

      req.onerror = () => reject(req.error);
      req.onsuccess = () => resolve(req.result);
    });
  }

  /**
   * Get all chat messages for a session (online or offline)
   */
  async getChatHistory(sessionId) {
    if (!this.db) return [];

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(['chat_messages'], 'readonly');
      const store = tx.objectStore('chat_messages');
      const index = store.index('session_id');
      const req = index.getAll(sessionId);

      req.onerror = () => reject(req.error);
      req.onsuccess = () => resolve(req.result);
    });
  }

  /**
   * Queue a message for sync when online
   */
  async queueForSync(message) {
    if (!this.db) return;

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(['sync_queue'], 'readwrite');
      const store = tx.objectStore('sync_queue');
      const req = store.add({
        ...message,
        queued_at: new Date().toISOString(),
      });

      req.onerror = () => reject(req.error);
      req.onsuccess = () => {
        this.syncQueue.push(req.result);
        resolve(req.result);
      };
    });
  }

  /**
   * Sync queued messages when back online
   */
  async syncQueuedMessages() {
    if (!this.db || !this.isOnline || this.syncQueue.length === 0) return;

    console.log(`Syncing ${this.syncQueue.length} queued messages...`);

    for (const itemId of this.syncQueue) {
      try {
        const tx = this.db.transaction(['sync_queue'], 'readonly');
        const store = tx.objectStore('sync_queue');
        const item = await new Promise((resolve, reject) => {
          const req = store.get(itemId);
          req.onerror = () => reject(req.error);
          req.onsuccess = () => resolve(req.result);
        });

        if (item) {
          // Send to cloud
          await fetch('/api/assistant/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(item),
          });

          // Remove from queue
          const delTx = this.db.transaction(['sync_queue'], 'readwrite');
          delTx.objectStore('sync_queue').delete(itemId);
        }
      } catch (err) {
        console.warn(`Failed to sync message ${itemId}:`, err);
      }
    }

    this.syncQueue = [];
    console.log('✅ Sync complete');
  }

  /**
   * Cache proactive alert
   */
  async cacheAlert(alert) {
    if (!this.db) return;

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(['alerts'], 'readwrite');
      const store = tx.objectStore('alerts');
      const req = store.add({
        ...alert,
        cached_at: new Date().toISOString(),
      });

      req.onerror = () => reject(req.error);
      req.onsuccess = () => resolve(req.result);
    });
  }

  /**
   * Get urgent alerts for current user
   */
  async getUrgentAlerts(userId) {
    if (!this.db) return [];

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(['alerts'], 'readonly');
      const store = tx.objectStore('alerts');
      const index = store.index('user_id');
      const req = index.getAll(userId);

      req.onerror = () => reject(req.error);
      req.onsuccess = () => {
        const alerts = req.result.filter(
          (a) => a.severity === 'critical' || a.severity === 'urgent'
        );
        resolve(alerts);
      };
    });
  }

  /**
   * Check if WebLLM model is ready
   */
  async checkModelStatus() {
    try {
      // This will be called by frontend to see if offline model is available
      // In production, this would check if Ollama or WebLLM is loaded
      return {
        ready: this.modelReady,
        model: 'phi-2',
        latency_ms: 800,
      };
    } catch (err) {
      console.error('Model status check failed:', err);
      return { ready: false };
    }
  }

  /**
   * Handle coming online
   */
  onOnline() {
    this.isOnline = true;
    console.log('🌐 Back online, syncing queued messages...');
    this.syncQueuedMessages();
  }

  /**
   * Handle going offline
   */
  onOffline() {
    this.isOnline = false;
    console.log('📴 Offline mode activated');
  }
}

// Singleton
export const offlineManager = new OfflineManager();
export default offlineManager;
