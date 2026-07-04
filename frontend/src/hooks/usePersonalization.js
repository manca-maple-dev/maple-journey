import { useState, useCallback } from 'react';

/**
 * React hook for personalization engine
 * Ranks alerts, resources, and policies by user-specific relevance score
 */
export const usePersonalization = () => {
  const [personalizationScore, setPersonalizationScore] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Rank alerts
  const rankAlerts = useCallback(async (alerts) => {
    try {
      setLoading(true);
      const response = await fetch('/api/assistant/rank-alerts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alerts }),
      });

      if (!response.ok) throw new Error('Failed to rank alerts');

      return await response.json();
    } catch (err) {
      setError(err.message);
      return { ranked_alerts: alerts }; // Return unranked on error
    } finally {
      setLoading(false);
    }
  }, []);

  // Rank resources
  const rankResources = useCallback(async (resources, resourceType) => {
    try {
      setLoading(true);
      const response = await fetch('/api/assistant/rank-resources', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resources,
          resource_type: resourceType,
        }),
      });

      if (!response.ok) throw new Error('Failed to rank resources');

      return await response.json();
    } catch (err) {
      setError(err.message);
      return { ranked_resources: resources };
    } finally {
      setLoading(false);
    }
  }, []);

  // Rank policies
  const rankPolicies = useCallback(async (policies) => {
    try {
      setLoading(true);
      const response = await fetch('/api/assistant/rank-policies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ policies }),
      });

      if (!response.ok) throw new Error('Failed to rank policies');

      return await response.json();
    } catch (err) {
      setError(err.message);
      return { ranked_policies: policies };
    } finally {
      setLoading(false);
    }
  }, []);

  // Get user's personalization score
  const getPersonalizationScore = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/assistant/personalization-score');

      if (!response.ok) throw new Error('Failed to get personalization score');

      const data = await response.json();
      setPersonalizationScore(data);
      return data;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    personalizationScore,
    loading,
    error,
    rankAlerts,
    rankResources,
    rankPolicies,
    getPersonalizationScore,
  };
};

export default usePersonalization;
