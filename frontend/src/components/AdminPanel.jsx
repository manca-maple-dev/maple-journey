import React, { useState, useEffect } from 'react';

export default function AdminPanel() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRecords, setSelectedRecords] = useState(new Set());
  const [exportFormat, setExportFormat] = useState('json');

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const resp = await fetch('/api/telegram/latest/public?limit=100');
      if (resp.ok) {
        const list = await resp.json();
        setData(Array.isArray(list) ? list : []);
      }
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const filteredData = data.filter(item => {
    if (filter !== 'all' && item.form_type !== filter) return false;
    if (searchTerm && !item.email?.includes(searchTerm) && !item.name?.includes(searchTerm)) return false;
    return true;
  });

  const handleSelectAll = () => {
    if (selectedRecords.size === filteredData.length) {
      setSelectedRecords(new Set());
    } else {
      setSelectedRecords(new Set(filteredData.map((_, i) => i)));
    }
  };

  const handleSelectRecord = (index) => {
    const newSelected = new Set(selectedRecords);
    if (newSelected.has(index)) {
      newSelected.delete(index);
    } else {
      newSelected.add(index);
    }
    setSelectedRecords(newSelected);
  };

  const handleExport = () => {
    const toExport = Array.from(selectedRecords).map(i => filteredData[i]);
    const content = exportFormat === 'json' 
      ? JSON.stringify(toExport, null, 2)
      : toCSV(toExport);
    
    const blob = new Blob([content], { type: exportFormat === 'json' ? 'application/json' : 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `export_${new Date().toISOString().slice(0, 10)}.${exportFormat === 'json' ? 'json' : 'csv'}`;
    a.click();
  };

  const toCSV = (records) => {
    const headers = ['Name', 'Email', 'Phone', 'Address', 'Status', 'Form Type', 'Collected At'];
    const rows = records.map(r => [
      r.name || '',
      r.email || '',
      r.phone || '',
      r.address || '',
      r.status || '',
      r.form_type || '',
      r.collected_at || ''
    ]);
    return [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Admin Data Manager</h1>
          <p className="text-gray-600">View, filter, and export collected data</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">Error: {error}</p>
          </div>
        )}

        {/* Controls */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
              <input
                type="text"
                placeholder="Email or name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
              />
            </div>

            {/* Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Form Type</label>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
              >
                <option value="all">All Types</option>
                <option value="profile">Profile</option>
                <option value="housing">Housing</option>
                <option value="jobs">Jobs</option>
                <option value="education">Education</option>
              </select>
            </div>

            {/* Export Format */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Export As</label>
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
              >
                <option value="json">JSON</option>
                <option value="csv">CSV</option>
              </select>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={handleSelectAll}
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 font-medium"
            >
              {selectedRecords.size === filteredData.length ? 'Deselect All' : 'Select All'}
            </button>
            <button
              onClick={handleExport}
              disabled={selectedRecords.size === 0}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium disabled:opacity-50"
            >
              Export {selectedRecords.size > 0 ? `(${selectedRecords.size})` : ''}
            </button>
            <div className="ml-auto text-sm text-gray-600 flex items-center">
              Showing {filteredData.length} of {data.length} records
            </div>
          </div>
        </div>

        {/* Data Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {filteredData.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedRecords.size === filteredData.length && filteredData.length > 0}
                        onChange={handleSelectAll}
                        className="rounded"
                      />
                    </th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Name</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Email</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Phone</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Address</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Form Type</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Status</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredData.map((item, idx) => (
                    <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={selectedRecords.has(idx)}
                          onChange={() => handleSelectRecord(idx)}
                          className="rounded"
                        />
                      </td>
                      <td className="py-3 px-4 text-gray-900">{item.name || '-'}</td>
                      <td className="py-3 px-4 text-gray-700">{item.email || '-'}</td>
                      <td className="py-3 px-4 text-gray-700">{item.phone || '-'}</td>
                      <td className="py-3 px-4 text-gray-700 truncate">{item.address || '-'}</td>
                      <td className="py-3 px-4">
                        <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs font-semibold capitalize">
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
                      <td className="py-3 px-4 text-gray-600 text-xs">
                        {item.collected_at 
                          ? new Date(item.collected_at).toLocaleDateString() 
                          : '-'
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center text-gray-500">
              <p className="text-lg">No records match your filters</p>
              <p className="text-sm mt-2">Try adjusting your search or filters</p>
            </div>
          )}
        </div>

        {/* Info Box */}
        <div className="mt-8 p-4 bg-purple-50 border border-purple-200 rounded-lg">
          <h3 className="font-semibold text-purple-900 mb-2">💡 Admin Features</h3>
          <ul className="text-purple-800 text-sm space-y-1">
            <li>✅ View all collected data in real-time</li>
            <li>✅ Filter by form type or search by name/email</li>
            <li>✅ Select multiple records and bulk export</li>
            <li>✅ Export as JSON or CSV for analysis</li>
            <li>✅ Auto-refreshing every 30 seconds</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
