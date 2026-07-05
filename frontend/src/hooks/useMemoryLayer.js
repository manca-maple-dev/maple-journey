import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { API } from '../lib/api';

/**
 * React hook for memory layer management
 * Users can view, verify, edit, and delete facts Maple remembers about them
 */
export const useMemoryLayer = () => {
  const { user } = useAuth();
  const [memories, setMemories] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch all memories on mount
  useEffect(() => {
    if (!user) return;

    const fetchMemories = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API}/assistant/memory`);

        if (!response.ok) throw new Error('Failed to fetch memories');

        const data = await response.json();
        setMemories(data.memories || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchMemories();
  }, [user]);

  // Get memory summary
  const getMemorySummary = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API}/assistant/memory-summary`);

      if (!response.ok) throw new Error('Failed to get summary');

      const data = await response.json();
      setSummary(data);
      return data;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Add new fact to memory
  const addMemory = useCallback(async (fact, category = 'personal', confidence = 'high') => {
    try {
      setLoading(true);
      const response = await fetch(`${API}/assistant/memory`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fact, category, confidence }),
      });

      if (!response.ok) throw new Error('Failed to add memory');

      const data = await response.json();
      setMemories([...memories, data.memory]);
      return data.memory;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [memories]);

  // Update an existing memory
  const updateMemory = useCallback(async (memoryId, updates) => {
    try {
      setLoading(true);
      const response = await fetch(`${API}/assistant/memory/${memoryId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });

      if (!response.ok) throw new Error('Failed to update memory');

      // Update local state
      setMemories(
        memories.map((m) =>
          m._id === memoryId ? { ...m, ...updates } : m
        )
      );

      return true;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [memories]);

  // Delete a memory
  const deleteMemory = useCallback(async (memoryId) => {
    try {
      setLoading(true);
      const response = await fetch(`${API}/assistant/memory/${memoryId}`, {
        method: 'DELETE',
      });

      if (!response.ok) throw new Error('Failed to delete memory');

      // Remove from local state
      setMemories(memories.filter((m) => m._id !== memoryId));
      return true;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [memories]);

  // Verify or dispute a memory fact
  const verifyMemory = useCallback(async (memoryId, verified) => {
    try {
      const response = await fetch(`${API}/assistant/memory/${memoryId}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ verified }),
      });

      if (!response.ok) throw new Error('Failed to verify memory');

      // Update local state
      setMemories(
        memories.map((m) =>
          m._id === memoryId
            ? { ...m, user_verified: verified, verified_at: new Date().toISOString() }
            : m
        )
      );

      return true;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [memories]);

  // Get memories by category
  const getMemoriesByCategory = useCallback((category) => {
    return memories.filter((m) => m.category === category);
  }, [memories]);

  return {
    memories,
    summary,
    loading,
    error,
    getMemorySummary,
    addMemory,
    updateMemory,
    deleteMemory,
    verifyMemory,
    getMemoriesByCategory,
  };
};

export default useMemoryLayer;
