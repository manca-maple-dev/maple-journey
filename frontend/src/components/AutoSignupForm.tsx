import React, { useState } from 'react';

export default function AutoSignupForm() {
  const [formData, setFormData] = useState({
    email: '',
    phone: '',
    full_name: '',
    address: '',
    immigration_status: 'PR',
    income: '',
    children: 0,
    form_type: 'profile',
  });

  const [status, setStatus] = useState('idle'); // idle, loading, success, error
  const [message, setMessage] = useState('');
  const [recordId, setRecordId] = useState('');

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseInt(value) : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus('loading');
    setMessage('');

    try {
      const response = await fetch('/api/automation/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        setStatus('success');
        setMessage('✅ Your information has been received and is being processed!');
        setRecordId(data.record_id);
        setFormData({
          email: '',
          phone: '',
          full_name: '',
          address: '',
          immigration_status: 'PR',
          income: '',
          children: 0,
          form_type: 'profile',
        });
      } else {
        setStatus('error');
        setMessage(`❌ Error: ${data.detail || 'Failed to submit form'}`);
      }
    } catch (error) {
      setStatus('error');
      setMessage(`❌ Connection error: ${error.message}`);
    }
  };

  return (
    <div
      className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg"
    >
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          MapleJourney Information Form
        </h1>
        <p className="text-gray-600">
          Share your details to get connected with resources and support
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Form Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            What type of information are you sharing?
          </label>
          <select
            name="form_type"
            value={formData.form_type}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="profile">Profile</option>
            <option value="housing">Housing</option>
            <option value="jobs">Jobs</option>
            <option value="education">Education</option>
          </select>
        </div>

        {/* Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Full Name *
          </label>
          <input
            type="text"
            name="full_name"
            value={formData.full_name}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="John Doe"
          />
        </div>

        {/* Email */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Email *
          </label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="john@example.com"
          />
        </div>

        {/* Phone */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Phone *
          </label>
          <input
            type="tel"
            name="phone"
            value={formData.phone}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="647-555-0100"
          />
        </div>

        {/* Address */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Address *
          </label>
          <input
            type="text"
            name="address"
            value={formData.address}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="123 Main Street, Toronto, ON"
          />
        </div>

        {/* Immigration Status */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Immigration Status *
          </label>
          <select
            name="immigration_status"
            value={formData.immigration_status}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="PR">Permanent Resident</option>
            <option value="CITIZEN">Citizen</option>
            <option value="WP">Work Permit</option>
            <option value="SP">Study Permit</option>
            <option value="OTHER">Other</option>
          </select>
        </div>

        {/* Income */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Annual Income (CAD) *
          </label>
          <input
            type="number"
            name="income"
            value={formData.income}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="50000"
          />
        </div>

        {/* Children */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Number of Children (0-20) *
          </label>
          <input
            type="number"
            name="children"
            value={formData.children}
            onChange={handleChange}
            min="0"
            max="20"
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={status === 'loading'}
          className={`w-full py-3 px-4 rounded-lg font-semibold text-white transition-all ${
            status === 'loading'
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {status === 'loading' ? '⏳ Submitting...' : '📤 Submit Information'}
        </button>
      </form>

      {/* Status Messages */}
      {status === 'success' && (
        <div
          className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg"
        >
          <p className="text-green-800 font-semibold">{message}</p>
          {recordId && (
            <p className="text-green-700 text-sm mt-2">
              Record ID: <code className="bg-green-100 px-2 py-1 rounded">{recordId}</code>
            </p>
          )}
        </div>
      )}

      {status === 'error' && (
        <div
          className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg"
        >
          <p className="text-red-800 font-semibold">{message}</p>
        </div>
      )}

      {/* Info Box */}
      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="font-semibold text-blue-900 mb-2">🔐 Your Data is Safe</h3>
        <ul className="text-blue-800 text-sm space-y-1">
          <li>✅ Encrypted at rest and in transit</li>
          <li>✅ Stored securely in MongoDB</li>
          <li>✅ Never shared without permission</li>
          <li>✅ GDPR compliant</li>
        </ul>
      </div>
    </div>
  );
}
