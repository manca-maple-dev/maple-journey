import React, { useState, useEffect, useRef } from 'react';

export default function AskMaple() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'maple',
      text: "👋 Hi! I'm Maple, your AI guide for settling in Canada. Ask me anything about immigration, payments to the government, housing, jobs, education, or benefits!",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    // Add user message
    const userMessage = {
      id: messages.length + 1,
      sender: 'user',
      text: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          conversation_id: 'maple_chat_session',
          context: 'canadian_immigration',
        }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();

      const mapleMessage = {
        id: messages.length + 2,
        sender: 'maple',
        text: data.response || 'Sorry, I could not process that. Please try again.',
        sources: data.sources || [],
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, mapleMessage]);
    } catch (err) {
      setError(err.message);
      const errorMessage = {
        id: messages.length + 2,
        sender: 'maple',
        text: '❌ I encountered an error. Please try again later.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const suggestedQuestions = [
    'How do I confirm a payment to the Government of Canada?',
    'What are the steps to move to Canada as a newcomer?',
    'How can I find a job in Canada?',
    'What benefits am I eligible for as a newcomer?',
    'How does the Canadian education system work?',
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center gap-3">
          <div className="text-4xl">🍁</div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Ask Maple</h1>
            <p className="text-sm text-gray-600">Your AI guide to settling in Canada</p>
          </div>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto max-w-4xl w-full mx-auto px-4 py-6 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No messages yet</p>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-2xl px-4 py-3 rounded-lg ${
                    msg.sender === 'user'
                      ? 'bg-blue-600 text-white rounded-br-none'
                      : 'bg-gray-200 text-gray-900 rounded-bl-none'
                  }`}
                >
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.text}</p>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-300 text-xs">
                      <p className="font-semibold mb-2">📚 Sources:</p>
                      <ul className="space-y-1">
                        {msg.sources.map((source, idx) => (
                          <li key={idx} className="text-gray-700">
                            • {source}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <p className="text-xs mt-2 opacity-70">
                    {msg.timestamp.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-200 text-gray-900 px-4 py-3 rounded-lg rounded-bl-none">
                  <div className="flex gap-2">
                    <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce delay-100"></div>
                    <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce delay-200"></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Suggested Questions */}
      {messages.length === 1 && (
        <div className="max-w-4xl w-full mx-auto px-4 py-4 bg-white rounded-lg shadow-sm mb-4">
          <p className="text-sm font-semibold text-gray-700 mb-3">💡 Try asking me:</p>
          <div className="grid grid-cols-1 gap-2">
            {suggestedQuestions.map((question, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setInput(question);
                }}
                className="text-left px-3 py-2 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 text-sm transition"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 shadow-lg">
        <div className="max-w-4xl mx-auto px-4 py-4">
          {error && (
            <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {error}
            </div>
          )}
          <div className="flex gap-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything about Canada, immigration, payments, housing, jobs..."
              rows="3"
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 font-medium transition flex items-center justify-center"
            >
              {loading ? '...' : '📤'}
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            💡 Tip: Press Enter to send (Shift+Enter for new line)
          </p>
        </div>
      </div>

      {/* Footer Info */}
      <div className="bg-gray-50 border-t border-gray-200 text-center py-3 text-xs text-gray-600">
        <p>
          ℹ️ Cited information only — not legal advice. Consult a regulated representative (RCIC or
          lawyer).
        </p>
      </div>
    </div>
  );
}
