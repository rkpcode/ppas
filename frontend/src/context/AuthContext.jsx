import { createContext, useContext, useState, useEffect } from 'react';
import { login as apiLogin, getMe } from '../api/auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('pdh_token');
    if (token) {
      getMe()
        .then(setUser)
        .catch((err) => {
          console.error("Auth error on load:", err);
          // Only remove token if it was explicitly a 401/Auth error.
          // The client.js already removes it on 401, so we don't need to aggressively delete here.
          // This prevents logging out when Hugging Face space is waking up (503).
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  async function login(username, password) {
    const data = await apiLogin(username, password);
    localStorage.setItem('pdh_token', data.access_token);
    const me = await getMe();
    setUser(me);
    return me;
  }

  function logout() {
    localStorage.removeItem('pdh_token');
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
