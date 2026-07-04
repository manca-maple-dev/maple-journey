import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';

/**
 * React hook for government policy feed updates
 * Fetches relevant policies, tracks reads, manages subscriptions
 */
export const usePolicyFeed = () => {
  const { user } = useAuth();
  const [policies, setPolicies] = useState([]);
  const [urgentPolicies, setUrgentPolicies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch relevant policies on mount
  useEffect(() => {
    const fetchPolicies = async () => {
      if (!user) return;

      try {
        setLoading(true);
        const [relevant, urgent] = await Promise.all([
          fetch('/api/assistant/relevant-policies').then(r => r.json()),
          fetch('/api/assistant/urgent-policies').then(r => r.json()),
        ]);

        setPolicies(relevant.policies || []);
        setUrgentPolicies(urgent.urgent_policies || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch + refresh every 1 hour
    fetchPolicies();
    const interval = setInterval(fetchPolicies, 3600000);
    return () => clearInterval(interval);
  }, [user]);

  // Mark policy as read
  const markPolicyRead = useCallback(async (policyId) => {
    try {
      await fetch('/api/assistant/policy-read', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ policy_id: policyId }),
      });
    } catch (err) {
      console.error('Failed to mark policy as read:', err);
    }
  }, []);

  // Subscribe to policy updates
  const subscribeToPolicies = useCallback(async (categories, minSeverity = 'high') => {
    try {
      const response = await fetch('/api/assistant/policy-subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          categories,
          severity_minimum: minSeverity,
        }),
      });

      if (!response.ok) throw new Error('Failed to subscribe');

      return await response.json();
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  // Get all policy updates
  const getallUpdates = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/assistant/policy-updates');

      if (!response.ok) throw new Error('Failed to fetch updates');

      const data = await response.json();
      return data.updates || [];
    } catch (err) {
      setError(err.message);
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    policies,
    urgentPolicies,
    loading,
    error,
    markPolicyRead,
    subscribeToPolicies,
    getallUpdates,
  };
};

export default usePolicyFeed;
