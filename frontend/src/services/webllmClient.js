/**
 * WebLLM Integration — Client-side local model initialization and inference
 * Handles model download, caching, and fallback to cloud when needed
 */

class WebLLMClient {
  constructor() {
    this.engine = null;
    this.modelReady = false;
    this.downloadProgress = 0;
    this.downloadError = null;
    this.device = this.detectDevice();
    this.initialized = false;
  }

  /**
   * Detect optimal device (GPU vs CPU)
   */
  detectDevice() {
    // Check if WebGPU is available
    if (typeof navigator !== 'undefined' && navigator.gpu) {
      return 'gpu';
    }
    // Check for WASM support (CPU fallback)
    return 'wasm';
  }

  /**
   * Initialize WebLLM — downloads model if needed
   * Shows progress to user
   */
  async initialize(onProgress = null) {
    if (this.initialized) {
      return { status: 'ready', model: 'Phi-2' };
    }

    try {
      console.log(`Initializing WebLLM on ${this.device}...`);

      // Dynamically import @mlc-ai/web-llm
      const { Model, ChatInterface } = await import('@mlc-ai/web-llm');

      // Model to use
      const model_id = 'Phi-2-q4f32_1-MLC';

      // Initialize with progress tracking
      this.engine = new ChatInterface(model_id, {
        appConfig: {
          logitProcs: 'default',
        },
        useGPU: this.device === 'gpu',
      });

      // Download model (will be cached by browser)
      await this.engine.forwardTokensAndSample([], {
        temperature: 0.3,
        topP: 0.92,
        maxGenLen: 1,
      });

      // Small forward pass to initialize
      this.modelReady = true;
      this.initialized = true;

      console.log('✅ WebLLM initialized successfully');
      if (onProgress) onProgress({ status: 'ready', progress: 100 });

      return { status: 'ready', model: 'Phi-2', device: this.device };
    } catch (err) {
      this.downloadError = err.message;
      console.error('WebLLM init failed:', err);

      // Fallback to cloud
      if (onProgress) {
        onProgress({
          status: 'fallback_to_cloud',
          error: err.message,
        });
      }

      return {
        status: 'fallback_to_cloud',
        error: err.message,
        reason: 'Could not initialize local model',
      };
    }
  }

  /**
   * Generate text locally using initialized model
   */
  async generate(
    systemPrompt,
    userMessage,
    {
      temperature = 0.3,
      topP = 0.92,
      maxTokens = 1024,
      onToken = null,
    } = {}
  ) {
    if (!this.engine || !this.modelReady) {
      throw new Error('WebLLM not ready');
    }

    try {
      // Format messages
      const messages = [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userMessage },
      ];

      // Generate with streaming
      let response = '';

      const stream = await this.engine.generate(messages, {
        temperature,
        topP,
        maxGenLen: maxTokens,
      });

      // Stream tokens
      for await (const chunk of stream) {
        response += chunk;
        if (onToken) onToken(chunk);
      }

      return response;
    } catch (err) {
      console.error('Generation failed:', err);
      throw err;
    }
  }

  /**
   * Check status without full initialization
   */
  async checkStatus() {
    return {
      initialized: this.initialized,
      modelReady: this.modelReady,
      device: this.device,
      downloadProgress: this.downloadProgress,
      error: this.downloadError,
    };
  }

  /**
   * Clear model from memory
   */
  async cleanup() {
    if (this.engine) {
      // WebLLM will clean up on page unload
      this.engine = null;
      this.modelReady = false;
      this.initialized = false;
    }
  }
}

// Singleton
let webLLMInstance = null;

export function getWebLLMClient() {
  if (!webLLMInstance) {
    webLLMInstance = new WebLLMClient();
  }
  return webLLMInstance;
}

export default WebLLMClient;
