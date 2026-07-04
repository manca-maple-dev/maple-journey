import { useState, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';

/**
 * React hook for location awareness
 * Manages user location, nearby resource searches, and emergency resource lookup
 */
export const useLocationAwareness = () => {
  const { user } = useAuth();
  const [location, setLocation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [resources, setResources] = useState([]);

  // Get user's current location
  const getLocation = useCallback(async () => {
    if (!navigator.geolocation) {
      setError('Geolocation not supported');
      return null;
    }

    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const loc = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            timestamp: new Date(),
          };
          setLocation(loc);
          resolve(loc);
        },
        (err) => {
          setError(err.message);
          resolve(null);
        }
      );
    });
  }, []);

  // Find nearby resources
  const findNearbyResources = useCallback(
    async (
      latitude = null,
      longitude = null,
      resourceType = null,
      radiusKm = 5
    ) => {
      try {
        setLoading(true);
        setError(null);

        const lat = latitude || location?.latitude;
        const lon = longitude || location?.longitude;

        if (!lat || !lon) {
          setError('Location required');
          return [];
        }

        const response = await fetch('/api/assistant/nearby-resources', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            latitude: lat,
            longitude: lon,
            resource_type: resourceType,
            radius_km: radiusKm,
          }),
        });

        if (!response.ok) throw new Error('Failed to find resources');

        const data = await response.json();
        setResources(data.resources);
        return data.resources;
      } catch (err) {
        setError(err.message);
        return [];
      } finally {
        setLoading(false);
      }
    },
    [location]
  );

  // Get emergency resources
  const getEmergencyResources = useCallback(
    async (emergencyType, latitude = null, longitude = null) => {
      try {
        setLoading(true);
        setError(null);

        const lat = latitude || location?.latitude;
        const lon = longitude || location?.longitude;

        if (!lat || !lon) {
          setError('Location required for emergency resources');
          return [];
        }

        const response = await fetch('/api/assistant/emergency-resources', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            latitude: lat,
            longitude: lon,
            emergency_type: emergencyType,
            country: 'canada',
          }),
        });

        if (!response.ok) throw new Error('Failed to get emergency resources');

        const data = await response.json();
        return data.resources;
      } catch (err) {
        setError(err.message);
        return [];
      } finally {
        setLoading(false);
      }
    },
    [location]
  );

  return {
    location,
    resources,
    loading,
    error,
    getLocation,
    findNearbyResources,
    getEmergencyResources,
  };
};

export default useLocationAwareness;
