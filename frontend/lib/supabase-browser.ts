import { createClient, type SupabaseClient } from "@supabase/supabase-js";

let singleton: SupabaseClient | null = null;

function getSupabaseEnv(): { url: string; anonKey: string } | null {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !anonKey) {
    return null;
  }

  return { url, anonKey };
}

export function isSupabaseConfigured(): boolean {
  return getSupabaseEnv() !== null;
}

export function getSupabaseBrowserClient(): SupabaseClient | null {
  if (singleton) {
    return singleton;
  }

  const env = getSupabaseEnv();
  if (!env) {
    return null;
  }

  singleton = createClient(env.url, env.anonKey, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  });

  return singleton;
}
