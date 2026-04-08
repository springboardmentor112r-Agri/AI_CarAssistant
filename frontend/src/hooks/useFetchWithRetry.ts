import { useState } from 'react';
import { supabase } from '@/integrations/supabase/client';

const API_BASE = 'https://ai-carassistant-1.onrender.com';

interface FetchState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  isWaking: boolean;
}

export function useFetchWithRetry<T>() {
  const [state, setState] = useState<FetchState<T>>({
    data: null, loading: false, error: null, isWaking: false,
  });

  const execute = async (path: string, options?: RequestInit) => {
    setState({ data: null, loading: true, error: null, isWaking: false });

    const wakingTimeout = setTimeout(() => {
      setState(prev => ({ ...prev, isWaking: true }));
    }, 3000);

    try {
      // Attach the Supabase JWT so the external API can verify the caller
      const { data: { session } } = await supabase.auth.getSession();
      const authHeaders: Record<string, string> = {};
      if (session?.access_token) {
        authHeaders['Authorization'] = `Bearer ${session.access_token}`;
      }

      const res = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers: {
          ...authHeaders,
          ...(options?.headers as Record<string, string>),
        },
        signal: AbortSignal.timeout(60000),
      });

      clearTimeout(wakingTimeout);

      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setState({ data, loading: false, error: null, isWaking: false });
      return data as T;
    } catch (err: any) {
      clearTimeout(wakingTimeout);
      setState({ data: null, loading: false, error: err.message || 'Request failed', isWaking: false });
      return null;
    }
  };

  return { ...state, execute };
}
