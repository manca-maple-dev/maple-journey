import { useState, useCallback } from 'react';
import { API } from '../lib/api';

/**
 * React hook for crisis detection and escalation
 * Handles immediate safety checks before sending messages to LLM
 */
export const useCrisisHandler = () => {
  const [crisisDetected, setCrisisDetected] = useState(false);
  const [crisisInfo, setCrisisInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Check message for crisis language
  const checkForCrisis = useCallback(async (message, country = 'canada') => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API}/assistant/crisis-check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          country,
        }),
      });

      if (!response.ok) throw new Error('Crisis check failed');

      const data = await response.json();

      if (data.crisis_detected) {
        setCrisisDetected(true);
        setCrisisInfo(data);
        return data;
      } else {
        setCrisisDetected(false);
        setCrisisInfo(null);
        return null;
      }
    } catch (err) {
      setError(err.message);
      // Fail safe: assume crisis if check fails
      return { crisis_detected: true, error: err.message };
    } finally {
      setLoading(false);
    }
  }, []);

  // Clear crisis state (e.g., after user acknowledges help)
  const clearCrisisState = useCallback(() => {
    setCrisisDetected(false);
    setCrisisInfo(null);
    setError(null);
  }, []);

  return {
    crisisDetected,
    crisisInfo,
    loading,
    error,
    checkForCrisis,
    clearCrisisState,
  };
};

export default useCrisisHandler;
