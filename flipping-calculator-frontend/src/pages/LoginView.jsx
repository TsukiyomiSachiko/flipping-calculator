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
    <div className="min-h-screen bg-luxury-dark text-gray-200 font-outfit relative overflow-hidden flex items-center justify-center p-4">
      {/* Floating Background Glows */}
      <div className="absolute top-[-100px] left-[-100px] w-[450px] h-[450px] rounded-full bg-luxury-purple/10 blur-[120px] pointer-events-none animate-float-slow" />
      <div className="absolute bottom-[-100px] right-[-100px] w-[450px] h-[450px] rounded-full bg-luxury-gold/5 blur-[120px] pointer-events-none animate-float-delayed" />

      <div className="card max-w-md w-full overflow-hidden relative z-10 p-0 border border-luxury-border/60">
        {/* Header */}
        <div className="bg-luxury-darker/60 p-8 border-b border-luxury-border/60 text-center">
          <h1 className="text-3xl font-black font-cinzel text-transparent bg-clip-text bg-gold-gradient tracking-widest drop-shadow-md">
            RuneScape Flipping
          </h1>
          <p className="text-luxury-purpleLight/70 mt-2 text-xs font-bold uppercase tracking-wider font-outfit">
            {isRegistering ? 'Create a new account' : 'Sign in to your account'}
          </p>
        </div>

        {/* Content */}
        <div className="p-8">
          {error && (
            <div className="bg-red-950/40 border border-osrs-red/30 text-red-200 p-3.5 rounded-xl mb-6 text-sm text-center backdrop-blur-md">
              ⚠️ {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-bold text-luxury-purpleLight/60 uppercase tracking-wider mb-2">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input w-full"
                placeholder="Enter username"
                disabled={isLoading}
              />
            </div>
            
            <div>
              <label className="block text-xs font-bold text-luxury-purpleLight/60 uppercase tracking-wider mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input w-full"
                placeholder="Enter password"
                disabled={isLoading}
              />
            </div>

            <button
              type="submit"
              disabled={isLoading || !username || !password}
              className="btn btn-primary w-full py-3.5 mt-6"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5 text-luxury-darker" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Processing...
                </span>
              ) : (
                isRegistering ? 'Create Account' : 'Sign In'
              )}
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
              className="text-sm text-luxury-purpleLight/80 hover:text-luxury-gold transition-colors font-medium underline underline-offset-4 decoration-luxury-purpleLight/30 hover:decoration-luxury-gold"
            >
              {isRegistering ? 'Already have an account? Sign in' : "Don't have an account? Create one"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
