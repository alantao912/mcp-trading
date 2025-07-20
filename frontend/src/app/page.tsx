'use client';

import { useState, useRef, useEffect } from 'react';
// @ts-ignore
import { FaChartLine } from 'react-icons/fa';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Hello! How can I help you today?',
      isUser: false,
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [selectedServices, setSelectedServices] = useState<string[]>([]); // No default selection
  const [hasInteracted, setHasInteracted] = useState(false);
  const services = ['Robinhood', 'E*TRADE', 'Fidelity', 'Charles Schwab', 'Webull'];
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [showRobinhoodLogin, setShowRobinhoodLogin] = useState(false);
  const [robinhoodUsername, setRobinhoodUsername] = useState('');
  const [robinhoodPassword, setRobinhoodPassword] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [connectError, setConnectError] = useState('');

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    if (dropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    } else {
      document.removeEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [dropdownOpen]);

  // Handle Robinhood connect/disconnect on selection change
  useEffect(() => {
    if (
      hasInteracted &&
      selectedServices.includes('Robinhood') &&
      !isConnected
    ) {
      setShowRobinhoodLogin(true);
    } else {
      setShowRobinhoodLogin(false);
      // Disconnect if Robinhood is deselected and was connected
      if (!selectedServices.includes('Robinhood') && isConnected) {
        fetch('http://localhost:8000/api/robinhood/disconnect', { method: 'POST' });
        setIsConnected(false);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedServices, hasInteracted]);

  const handleSendMessage = () => {
    if (inputValue.trim() === '') return;

    const newMessage: Message = {
      id: Date.now().toString(),
      text: inputValue,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, newMessage]);
    setInputValue('');

    // Simulate a response (you can replace this with actual API calls)
    setTimeout(() => {
      const responseMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'This is a sample response. In a real application, this would come from your backend API.',
        isUser: false,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, responseMessage]);
    }, 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleRobinhoodLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsConnecting(true);
    setConnectError('');
    try {
      const res = await fetch('http://localhost:8000/api/robinhood/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: robinhoodUsername, password: robinhoodPassword })
      });
      const data = await res.json();
      if (data.error) {
        setConnectError(data.error);
        setIsConnected(false);
      } else {
        setIsConnected(true);
        setShowRobinhoodLogin(false);
        setRobinhoodUsername('');
        setRobinhoodPassword('');
      }
    } catch (err) {
      setConnectError('Connection failed');
      setIsConnected(false);
    }
    setIsConnecting(false);
  };

  return (
    <div className="relative min-h-screen w-full bg-gradient-to-br from-blue-950 via-slate-900 to-green-900">
      {/* Fixed Header */}
      <header className="fixed top-0 left-0 right-0 z-30 flex justify-center bg-gradient-to-r from-blue-950 via-slate-900 to-green-900 border-b border-blue-900 shadow-lg">
        <div className="flex items-center space-x-3 w-full max-w-2xl px-6 py-4">
          <FaChartLine className="text-emerald-400 text-2xl" />
          <h1 className="text-3xl font-extrabold text-emerald-300 tracking-wide leading-tight">Finly</h1>
          <span className="ml-auto text-lg font-semibold text-emerald-100">Your personal key to smarter investing</span>
        </div>
      </header>
      {/* Fixed Footer (Input) */}
      <footer className="fixed bottom-0 left-0 right-0 z-30 flex justify-center bg-gradient-to-r from-blue-950 via-slate-900 to-green-900 border-t border-blue-900 shadow-xl">
        <div className="w-full max-w-2xl px-4 py-4">
          {/* Show selected services above input */}
          <div className="mb-3 flex items-center text-lg font-bold text-emerald-200">
            <span className="mr-2 text-emerald-300">Selected portfolios:</span>
            <span className="truncate">{selectedServices.join(', ') || <span className='text-blue-300'>None</span>}</span>
          </div>
          {/* Robinhood Login Modal */}
          {showRobinhoodLogin && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60">
              <form onSubmit={handleRobinhoodLogin} className="bg-slate-900 border border-emerald-400 rounded-xl p-8 shadow-xl flex flex-col min-w-[320px] max-w-xs">
                <h2 className="text-xl font-bold text-emerald-200 mb-4">Connect to Robinhood</h2>
                <input
                  type="text"
                  placeholder="Username"
                  value={robinhoodUsername}
                  onChange={e => setRobinhoodUsername(e.target.value)}
                  className="mb-3 px-3 py-2 rounded-lg border border-emerald-400 bg-slate-800 text-emerald-100 focus:outline-none focus:ring-2 focus:ring-emerald-400"
                  required
                />
                <input
                  type="password"
                  placeholder="Password"
                  value={robinhoodPassword}
                  onChange={e => setRobinhoodPassword(e.target.value)}
                  className="mb-3 px-3 py-2 rounded-lg border border-emerald-400 bg-slate-800 text-emerald-100 focus:outline-none focus:ring-2 focus:ring-emerald-400"
                  required
                />
                {connectError && <div className="text-red-400 mb-2 text-sm">{connectError}</div>}
                <div className="flex gap-2 mt-2">
                  <button type="submit" disabled={isConnecting} className="flex-1 px-4 py-2 bg-emerald-500 text-white rounded-lg font-semibold hover:bg-emerald-600 transition-colors disabled:opacity-50">
                    {isConnecting ? 'Connecting...' : 'Connect'}
                  </button>
                  <button type="button" onClick={() => { setShowRobinhoodLogin(false); setSelectedServices(s => s.filter(x => x !== 'Robinhood')); }} className="flex-1 px-4 py-2 bg-slate-700 text-emerald-100 rounded-lg font-semibold hover:bg-slate-800 transition-colors">
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}
          <div className="flex flex-row items-end gap-3 w-full">
            {/* Custom Multi-Select Dropdown */}
            <div className="relative shrink-0" ref={dropdownRef} style={{height: '44px'}}>
              <button
                type="button"
                className="px-3 py-2 border border-emerald-400 bg-slate-900 text-emerald-200 rounded-lg focus:ring-2 focus:ring-emerald-400 focus:border-transparent hover:bg-emerald-950 min-w-[120px] text-left transition-colors"
                onClick={() => setDropdownOpen((open) => !open)}
              >
                Select portfolios
                <span className="ml-2">▼</span>
              </button>
              {dropdownOpen && (
                <div className="absolute z-10 mb-2 bottom-full w-48 bg-slate-900 border border-emerald-400 rounded-lg shadow-lg p-2">
                  {services.map((service) => (
                    <label key={service} className="flex items-center space-x-2 py-1 cursor-pointer text-emerald-100 hover:text-emerald-300">
                      <input
                        type="checkbox"
                        checked={selectedServices.includes(service)}
                        onChange={() => {
                          setHasInteracted(true);
                          setSelectedServices((prev) =>
                            prev.includes(service)
                              ? prev.filter((s) => s !== service)
                              : [...prev, service]
                          );
                        }}
                        className="accent-emerald-400"
                      />
                      <span className="text-sm">{service}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>
            <div className="flex-1 mx-2 flex items-center" style={{minHeight: '44px'}}>
              <label htmlFor="chat-input" className="sr-only">Type your message</label>
              <textarea
                id="chat-input"
                value={inputValue || ''}
                onChange={e => setInputValue(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Type your message..."
                className="w-full px-4 py-2 border border-emerald-400 bg-slate-900 text-emerald-100 rounded-lg focus:ring-2 focus:ring-emerald-400 focus:border-transparent resize-none placeholder:text-emerald-300 min-h-[44px] max-h-[120px] align-middle"
                rows={1}
                style={{ minHeight: '44px', maxHeight: '120px', height: '44px' }}
              />
            </div>
            <button
              onClick={handleSendMessage}
              disabled={inputValue.trim() === ''}
              className="h-[44px] px-6 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 focus:ring-2 focus:ring-emerald-400 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-semibold shadow-md shrink-0 flex items-center justify-center"
              type="button"
            >
              Send
            </button>
          </div>
        </div>
      </footer>
      {/* Main Content Area: fills between header and footer, two columns, both scrollable */}
      <main className="absolute top-[5.5rem] bottom-[6.5rem] left-0 right-0 flex max-w-7xl mx-auto w-full">
        {/* Chat Column */}
        <section className="flex flex-col w-full max-w-2xl px-4 h-full min-h-0">
          <div className="h-full min-h-0 px-4 py-6 space-y-4 bg-gradient-to-br from-blue-950/80 via-slate-900/80 to-green-900/80 rounded-xl shadow-inner border border-blue-900 overflow-y-auto">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-xl shadow-md border ${
                    message.isUser
                      ? 'bg-emerald-600 text-white border-emerald-400 rounded-br-none'
                      : 'bg-slate-800 text-emerald-100 border-blue-900 rounded-bl-none'
                  }`}
                >
                  <p className="text-sm font-medium">{message.text}</p>
                  <p
                    className={`text-xs mt-1 ${
                      message.isUser
                        ? 'text-emerald-100'
                        : 'text-blue-200'
                    }`}
                  >
                    {message.timestamp.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>
        {/* Real-Time Analysis/Results Column */}
        <aside className="hidden md:flex flex-col flex-1 h-full min-h-0 bg-gradient-to-br from-slate-900 via-blue-950 to-green-900 border-l border-blue-900 overflow-y-auto rounded-xl">
          <div className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)]">
            <FaChartLine className="text-emerald-400 text-5xl mb-4" />
            <h2 className="text-2xl font-bold text-emerald-200 mb-2">Real-Time Analysis</h2>
            <p className="text-emerald-100 text-center">Results and live trading analysis will appear here.</p>
          </div>
        </aside>
      </main>
    </div>
  );
}
