/**
 * Telegram Data Collection Monitoring Dashboard
 * Real-time display of data collection metrics and alerts
 */

import React, { useState, useEffect, useCallback } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface Metric {
  timestamp: string;
  collections_today: Record<string, number>;
  active_sessions: number;
  avg_completion_time: number;
  form_distribution: Record<string, number>;
  field_completion: Record<string, number>;
  hourly_trend: Record<string, number>;
  error_rate: Record<string, number>;
  user_retention: Record<string, number>;
}

interface Alert {
  _id: string;
  type: string;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  timestamp: string;
  acknowledged: boolean;
}

interface DashboardData {
  timestamp: string;
  metrics: Metric;
  active_alerts: Alert[];
  status: string;
}

export const TelegramDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trendData, setTrendData] = useState<any[]>([]);
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds

  // Fetch dashboard data
  const fetchDashboard = useCallback(async () => {
    try {
      const response = await fetch('/api/telegram/dashboard', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch dashboard');
      
      const data = await response.json();
      setDashboardData(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch trend data
  const fetchTrends = useCallback(async () => {
    try {
      const response = await fetch('/api/telegram/metrics', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setTrendData(Object.entries(data.hourly_breakdown || {}).map(([hour, count]) => ({
          hour,
          count
        })));
      }
    } catch (err) {
      console.error('Failed to fetch trends:', err);
    }
  }, []);

  // Refresh data periodically
  useEffect(() => {
    fetchDashboard();
    fetchTrends();

    const interval = setInterval(() => {
      fetchDashboard();
      fetchTrends();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval, fetchDashboard, fetchTrends]);

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/telegram/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        fetchDashboard();
      }
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="text-4xl mb-4">📊</div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center text-red-600">
          <div className="text-4xl mb-4">❌</div>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  const metrics = dashboardData?.metrics;
  const alerts = dashboardData?.active_alerts || [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            📊 Telegram Data Collection Dashboard
          </h1>
          <p className="text-gray-600">Real-time monitoring of user data collection</p>
        </div>

        {/* Alerts Section */}
        {alerts.length > 0 && (
          <div className="grid grid-cols-1 gap-4 mb-8">
            {alerts.map(alert => (
              <div
                key={alert._id}
                className={`p-4 rounded-lg border-l-4 ${
                  alert.severity === 'critical'
                    ? 'bg-red-50 border-red-500'
                    : alert.severity === 'warning'
                    ? 'bg-yellow-50 border-yellow-500'
                    : 'bg-blue-50 border-blue-500'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{alert.type}</h3>
                    <p className="text-gray-700 mt-1">{alert.message}</p>
                    <p className="text-sm text-gray-500 mt-2">
                      {new Date(alert.timestamp).toLocaleString()}
                    </p>
                  </div>
                  {!alert.acknowledged && (
                    <button
                      onClick={() => handleAcknowledgeAlert(alert._id)}
                      className="ml-4 px-3 py-1 bg-gray-800 text-white rounded hover:bg-gray-900 text-sm"
                    >
                      ✓ Acknowledge
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Collections Today"
            value={Object.values(metrics?.collections_today || {}).reduce((a, b) => a + b, 0)}
            icon="📝"
            color="bg-blue-500"
          />
          <MetricCard
            title="Active Sessions"
            value={metrics?.active_sessions || 0}
            icon="👥"
            color="bg-green-500"
          />
          <MetricCard
            title="Avg Completion Time"
            value={`${Math.round(metrics?.avg_completion_time || 0)}s`}
            icon="⏱️"
            color="bg-purple-500"
          />
          <MetricCard
            title="Forms by Type"
            value={Object.keys(metrics?.form_distribution || {}).length}
            icon="📊"
            color="bg-orange-500"
          />
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Hourly Trend */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Hourly Trend</h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="count" stroke="#3B82F6" name="Collections" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Form Distribution */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Form Distribution</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={Object.entries(metrics?.form_distribution || {}).map(([name, count]) => ({
                  name,
                  count
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#8B5CF6" name="Count" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Detailed Metrics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Field Completion */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Field Completion Rate</h2>
            <div className="space-y-3">
              {Object.entries(metrics?.field_completion || {}).map(([field, completion]) => (
                <div key={field}>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700 capitalize">{field}</span>
                    <span className="text-sm font-medium text-gray-900">{completion}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: `${completion}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* User Retention */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">User Retention</h2>
            <div className="space-y-4">
              <RetentionMetric
                label="Today's Users"
                value={metrics?.user_retention?.today_unique || 0}
              />
              <RetentionMetric
                label="Yesterday's Users"
                value={metrics?.user_retention?.yesterday_unique || 0}
              />
              <RetentionMetric
                label="7-Day Unique"
                value={metrics?.user_retention?.week_unique || 0}
              />
              <RetentionMetric
                label="Returning Users"
                value={metrics?.user_retention?.repeat_users || 0}
                highlight
              />
            </div>
          </div>
        </div>

        {/* Refresh Control */}
        <div className="mt-8 flex items-center justify-between bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">
            Last updated: {new Date(dashboardData?.timestamp || Date.now()).toLocaleTimeString()}
          </div>
          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(parseInt(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            <option value={10000}>Refresh: 10s</option>
            <option value={30000}>Refresh: 30s</option>
            <option value={60000}>Refresh: 1m</option>
            <option value={300000}>Refresh: 5m</option>
          </select>
        </div>
      </div>
    </div>
  );
};

// Helper Components

interface MetricCardProps {
  title: string;
  value: number | string;
  icon: string;
  color: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon, color }) => (
  <div className="bg-white rounded-lg shadow p-6">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-gray-600 text-sm">{title}</p>
        <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
      </div>
      <div className={`text-4xl ${color} p-3 rounded-lg text-white`}>
        {icon}
      </div>
    </div>
  </div>
);

interface RetentionMetricProps {
  label: string;
  value: number;
  highlight?: boolean;
}

const RetentionMetric: React.FC<RetentionMetricProps> = ({ label, value, highlight }) => (
  <div className={`flex items-center justify-between p-3 rounded-lg ${highlight ? 'bg-green-50' : 'bg-gray-50'}`}>
    <span className="text-sm font-medium text-gray-700">{label}</span>
    <span className={`text-lg font-bold ${highlight ? 'text-green-600' : 'text-gray-900'}`}>
      {value}
    </span>
  </div>
);

export default TelegramDashboard;
