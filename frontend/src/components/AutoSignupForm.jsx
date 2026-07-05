import React from 'react';

export default function AutoSignupForm() {
  return (
    <div className="max-w-md mx-auto bg-white rounded-lg shadow p-6">
      <h2 className="text-2xl font-bold mb-4">Sign Up</h2>
      <form>
        <input 
          type="email" 
          placeholder="Email" 
          className="w-full px-4 py-2 border rounded mb-4"
        />
        <input 
          type="password" 
          placeholder="Password" 
          className="w-full px-4 py-2 border rounded mb-4"
        />
        <button className="w-full bg-blue-600 text-white py-2 rounded">
          Sign Up
        </button>
      </form>
    </div>
  );
}
