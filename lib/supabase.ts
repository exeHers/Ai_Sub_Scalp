import { createClient, SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL?.trim();
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.trim();

const isValidUrl = (value?: string) => {
  if (!value) return false;
  try {
    const u = new URL(value);
    return u.protocol === "http:" || u.protocol === "https:";
  } catch {
    return false;
  }
};

export const hasSupabaseEnv =
  isValidUrl(supabaseUrl) && Boolean(supabaseAnonKey);

export const supabase: SupabaseClient | null = hasSupabaseEnv
  ? createClient(supabaseUrl as string, supabaseAnonKey as string)
  : null;