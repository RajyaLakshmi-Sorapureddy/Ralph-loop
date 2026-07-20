import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { api } from '../api/client';
import type { TokenResponse, User } from '../types';

const TOKEN_STORAGE_KEY = 'authToken';

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<User>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function hydrate() {
      if (!token) {
        setUser(null);
        setIsLoading(false);
        return;
      }
      try {
        const me = await api.get<User>('/auth/me', token);
        if (!cancelled) {
          setUser(me);
        }
      } catch {
        if (!cancelled) {
          localStorage.removeItem(TOKEN_STORAGE_KEY);
          setToken(null);
          setUser(null);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    setIsLoading(true);
    void hydrate();

    return () => {
      cancelled = true;
    };
  }, [token]);

  async function login(email: string, password: string): Promise<User> {
    const tokenResponse = await api.post<TokenResponse>('/auth/login', { email, password });
    const me = await api.get<User>('/auth/me', tokenResponse.access_token);
    localStorage.setItem(TOKEN_STORAGE_KEY, tokenResponse.access_token);
    setToken(tokenResponse.access_token);
    setUser(me);
    return me;
  }

  async function signup(name: string, email: string, password: string): Promise<void> {
    await api.post('/auth/signup', { name, email, password });
  }

  function logout() {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
