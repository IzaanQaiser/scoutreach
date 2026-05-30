"use client";

import { type Session } from "@supabase/supabase-js";
import { useRouter } from "next/navigation";
import {
  createContext,
  type ReactNode,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { getSupabaseBrowserClient } from "../lib/supabase-browser";

type AuthContextValue = {
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  signInWithPassword: (email: string, password: string) => Promise<void>;
  signUpWithPassword: (email: string, password: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);
  const supabase = useMemo(() => getSupabaseBrowserClient(), []);
  const devToken = process.env.NEXT_PUBLIC_DEV_AUTH_TOKEN?.trim() ?? null;

  useEffect(() => {
    let mounted = true;

    if (!supabase) {
      setToken(devToken);
      setIsLoading(false);
      return () => {
        mounted = false;
      };
    }

    supabase.auth.getSession().then(({ data, error }) => {
      if (error) {
        console.error("Failed to load session", error);
      }
      if (mounted) {
        const nextSession = data.session ?? null;
        setSession(nextSession);
        setToken(nextSession?.access_token ?? devToken);
        setIsLoading(false);
      }
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession ?? null);
      setToken(nextSession?.access_token ?? devToken);
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, [devToken, supabase]);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      isLoading,
      isAuthenticated: Boolean(token),
      async signInWithPassword(email: string, password: string) {
        if (!supabase) {
          throw new Error(
            "Supabase auth is not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.",
          );
        }
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) {
          throw error;
        }
      },
      async signUpWithPassword(email: string, password: string) {
        if (!supabase) {
          throw new Error(
            "Supabase auth is not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.",
          );
        }
        const { error } = await supabase.auth.signUp({ email, password });
        if (error) {
          throw error;
        }
      },
      async signInWithGoogle() {
        if (!supabase) {
          throw new Error(
            "Supabase auth is not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.",
          );
        }
        const origin = window.location.origin;
        const { error } = await supabase.auth.signInWithOAuth({
          provider: "google",
          options: {
            redirectTo: `${origin}/auth/callback`,
          },
        });
        if (error) {
          throw error;
        }
      },
      async signOut() {
        if (supabase) {
          const { error } = await supabase.auth.signOut();
          if (error) {
            throw error;
          }
        }
        setToken(null);
        router.push("/");
      },
    }),
    [devToken, isLoading, router, supabase, token],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
