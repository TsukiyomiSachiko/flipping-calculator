import { useState } from 'react';
import { useAppStore } from '../stores/appStore';
import { authApi } from '../services/api';

export default function LoginView() {
  const { setCurrentAccount, setToken, setRefreshToken } = useAppStore();
  const [isRegistering, setIsRegistering] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username || !password) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      let response;
      if (isRegistering) {
        response = await authApi.register(username, password);
      } else {
        response = await authApi.login(username, password);
      }
      
      const { access_token, refresh_token, account_id, name } = response.data;
      
      setToken(access_token);
      setRefreshToken(refresh_token);
      setCurrentAccount({ id: account_id, name });
    } catch (err) {
      console.error('Auth failed:', err);
      setError(err.response?.data?.detail || 'Authentication failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4 bg-gradient-to-br from-gray-900 to-gray-800">
      <div className="max-w-md w-full bg-gray-800 border-2 border-osrs-gold rounded-xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-gray-900 p-6 border-b border-gray-700 text-center">
          <h1 className="text-3xl font-bold text-osrs-gold tracking-wider drop-shadow-md">
            RuneScape Flipping
          </h1>
          <p className="text-gray-400 mt-2 text-sm">
            {isRegistering ? 'Create a new account' : 'Sign in to your account'}
          </p>
        </div>

        {/* Content */}
        <div className="p-6">
          {error && (
            <div className="bg-red-900/50 border border-red-500 text-red-200 p-3 rounded-lg mb-4 text-sm text-center">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:border-osrs-gold focus:outline-none"
                placeholder="Enter username"
                disabled={isLoading}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:border-osrs-gold focus:outline-none"
                placeholder="Enter password"
                disabled={isLoading}
              />
            </div>

            <button
              type="submit"
              disabled={isLoading || !username || !password}
              className="w-full bg-osrs-gold hover:bg-yellow-600 disabled:opacity-50 disabled:cursor-not-allowed text-black font-bold py-3 rounded-lg transition-colors mt-4"
            >
              {isLoading ? 'Processing...' : (isRegistering ? 'Create Account' : 'Sign In')}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => {
                setIsRegistering(!isRegistering);
                setError(null);
                setUsername('');
                setPassword('');
              }}
              className="text-sm text-gray-400 hover:text-osrs-gold underline"
            >
              {isRegistering ? 'Already have an account? Sign in' : "Don't have an account? Create one"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
