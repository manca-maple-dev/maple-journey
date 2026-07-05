import React, { useState, useEffect } from 'react';

export default function DataCollectionDashboard() {
  const [stats, setStats] = useState({
    total_records: 0,
    completed: 0,
    today: 0,
    by_form_type: {},
    auto_signups_today: 0,
    payments_today: 0,
  });

  const [recentData, setRecentData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch automation stats
        const statsResp = await fetch('/api/automation/status/auto');
        if (statsResp.ok) {
          const statsData = await statsResp.json();
          setStats(statsData);
        }

        // Fetch recent data
        const recentResp = await fetch('/api/telegram/latest/public?limit=10');
        if (recentResp.ok) {
          const recentList = await recentResp.json();
          setRecentData(Array.isArray(recentList) ? recentList : []);
        }

        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Data Collection Dashboard</h1>
          <p className="text-gray-600">Real-time overview of all collected data</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">Error: {error}</p>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Records */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm font-medium">Total Records</p>
                <p className="text-3xl font-bold text-gray-900">{stats.total_records || 0}</p>
              </div>
              <div className="text-4xl">📊</div>
            </div>
          </div>

          {/* Completed */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm font-medium">Completed</p>
                <p className="text-3xl font-bold text-green-600">{stats.completed || 0}</p>
              </div>
              <div className="text-4xl">✅</div>
            </div>
          </div>

          {/* Today */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm font-medium">Today</p>
                <p className="text-3xl font-bold text-blue-600">{stats.today || 0}</p>
              </div>
              <div className="text-4xl">📅</div>
            </div>
          </div>

          {/* Payments */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm font-medium">Payments Today</p>
                <p className="text-3xl font-bold text-purple-600">{stats.payments_today || 0}</p>
              </div>
              <div className="text-4xl">💳</div>
            </div>
          </div>
        </div>

        {/* Form Types Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* By Form Type */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">By Form Type</h2>
            <div className="space-y-3">
              {Object.entries(stats.by_form_type || {}).length > 0 ? (
                Object.entries(stats.by_form_type).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="font-medium text-gray-700 capitalize">{type}</span>
                    <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-semibold">
                      {count}
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-center py-4">No data yet</p>
              )}
            </div>
          </div>

          {/* Collection Methods */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Collection Methods</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <span className="text-2xl mr-3">🤖</span>
                  <span className="font-medium text-gray-700">Auto Signups</span>
                </div>
                <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-semibold">
                  {stats.auto_signups_today || 0}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <span className="text-2xl mr-3">💬</span>
                  <span className="font-medium text-gray-700">Telegram Bot</span>
                </div>
                <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-semibold">
                  {(stats.completed || 0) - (stats.auto_signups_today || 0)}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <span className="text-2xl mr-3">🎫</span>
                  <span className="font-medium text-gray-700">Payments</span>
                </div>
                <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-semibold">
                  {stats.payments_today || 0}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Submissions */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Submissions</h2>
          {recentData.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Name</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Email</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Form Type</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Status</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Submitted</th>
                  </tr>
                </thead>
                <tbody>
                  {recentData.map((item, idx) => (
                    <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 text-gray-900">{item.name || 'N/A'}</td>
                      <td className="py-3 px-4 text-gray-700">{item.email || 'N/A'}</td>
                      <td className="py-3 px-4">
                        <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs font-semibold capitalize">
                          {item.form_type || 'N/A'}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          item.status === 'completed' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {item.status || 'pending'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-gray-600">
                        {item.collected_at 
                          ? new Date(item.collected_at).toLocaleDateString() 
                          : 'N/A'
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No submissions yet</p>
          )}
        </div>

        {/* Info Box */}
        <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="font-semibold text-blue-900 mb-2">📊 Dashboard Features</h3>
          <ul className="text-blue-800 text-sm space-y-1">
            <li>✅ Real-time data updates (refreshes every 30 seconds)</li>
            <li>✅ Track all three collection methods (Web form, Telegram, API)</li>
            <li>✅ View recent submissions with details</li>
            <li>✅ Monitor form type distribution</li>
            <li>✅ Track payment processing</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
