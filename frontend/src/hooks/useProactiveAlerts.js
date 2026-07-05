import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { API } from '../lib/api';

/**
 * Hook for displaying proactive deadline alerts in chat
 * Fetches alerts and displays them naturally in conversation flow
 */
export const useProactiveAlerts = () => {
  const { user } = useAuth();
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [nextAlert, setNextAlert] = useState(null);

  // Fetch urgent alerts on mount
  useEffect(() => {
    if (!user?._id) return;

    const fetchAlerts = async () => {
      try {
        setLoading(true);
        const res = await fetch(`${API}/assistant/proactive-alerts`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('mj_token')}`,
          },
        });
        const data = await res.json();
        setAlerts(data.alerts || []);

        // Get the next urgent alert
        const urgent = data.alerts?.find(
          (a) => a.severity === 'critical' || a.severity === 'urgent'
        );
        if (urgent) {
          setNextAlert(urgent);
        }
      } catch (err) {
        console.error('Failed to fetch proactive alerts:', err);
      } finally {
        setLoading(false);
      }
    };

    // Fetch on mount and every 1 hour
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 3600000);
    return () => clearInterval(interval);
  }, [user?._id]);

  const dismissAlert = useCallback(async (alertId) => {
    try {
      await fetch(`${API}/assistant/proactive-alerts/${alertId}/dismiss`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('mj_token')}`,
        },
      });
      setAlerts((prev) => prev.filter((a) => a.id !== alertId));
      if (nextAlert?.id === alertId) {
        setNextAlert(null);
      }
    } catch (err) {
      console.error('Failed to dismiss alert:', err);
    }
  }, [nextAlert]);

  return {
    alerts,
    nextAlert,
    loading,
    dismissAlert,
  };
};

export default useProactiveAlerts;
