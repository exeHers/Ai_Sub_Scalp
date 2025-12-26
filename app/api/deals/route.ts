import { NextResponse } from "next/server";
import { supabase, hasSupabaseEnv } from "@/lib/supabase";
import { seedDeals } from "@/lib/seedDeals";

export async function GET() {
  // If Supabase env vars are missing, fallback gracefully
  if (!hasSupabaseEnv || !supabase) {
    return NextResponse.json({ deals: seedDeals });
  }

  try {
    const { data, error } = await supabase
      .from("deals")
      .select("*")
      .eq("status", "active")
      .order("confidence_score", { ascending: false })
      .limit(200);

    if (error) throw error;

    if (!data || data.length === 0) {
      return NextResponse.json({ deals: seedDeals });
    }

    return NextResponse.json({ deals: data });
  } catch {
    return NextResponse.json({ deals: seedDeals });
  }
}