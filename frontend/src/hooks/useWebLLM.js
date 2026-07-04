import { useState, useEffect, useCallback } from 'react';
import { getWebLLMClient } from '../services/webllmClient';
import { useAuth } from '../context/AuthContext';

/**
 * Hook for managing WebLLM local model lifecycle
 * Handles initialization, status tracking, and inference
 */
export const useWebLLM = () => {
  const { user } = useAuth();
  const [status, setStatus] = useState('uninitialized');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const webllm = getWebLLMClient();

  // Initialize model on first load
  useEffect(() => {
    const init = async () => {
      try {
        setStatus('initializing');
        const result = await webllm.initialize((progressUpdate) => {
          setProgress(progressUpdate.progress || 0);
          setStatus(progressUpdate.status);
        });

        if (result.status === 'ready') {
          setStatus('ready');
          setProgress(100);
        } else {
          setStatus('fallback_to_cloud');
        }
      } catch (err) {
        console.error('WebLLM init error:', err);
        setError(err.message);
        setStatus('fallback_to_cloud');
      }
    };

    // Only initialize if user exists and model not already initialized
    if (user && status === 'uninitialized') {
      init();
    }
  }, [user, webllm, status]);

  const generate = useCallback(
    async (systemPrompt, userMessage, options = {}) => {
      if (status !== 'ready') {
        throw new Error('WebLLM not ready');
      }

      try {
        setIsGenerating(true);
        const response = await webllm.generate(systemPrompt, userMessage, {
          temperature: 0.3,
          topP: 0.92,
          maxTokens: 1024,
          ...options,
        });

        return response;
      } finally {
        setIsGenerating(false);
      }
    },
    [status, webllm]
  );

  const checkStatus = useCallback(async () => {
    return await webllm.checkStatus();
  }, [webllm]);

  return {
    status,
    progress,
    error,
    isGenerating,
    isReady: status === 'ready',
    generate,
    checkStatus,
  };
};

export default useWebLLM;
