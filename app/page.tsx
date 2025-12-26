"use client";

import { useEffect, useMemo, useState } from "react";
import { ExternalLink, Search, Copy, Check } from "lucide-react";

type Deal = {
  id: string;
  tool_name: string;
  category: string;
  deal_type: string;
  deal_value: string;
  promo_code?: string | null;
  link: string;
  source_url: string;
  confidence_score: number;
  status: string;
};

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDeals = async () => {
      setLoading(true);
      try {
        const res = await fetch("/api/deals");
        const json = await res.json();
        setDeals(json.deals || []);
      } catch {
        setDeals([]);
      } finally {
        setLoading(false);
      }
    };

    loadDeals();
  }, []);

  const filteredDeals = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return deals;

    return deals.filter(
      (deal) =>
        deal.tool_name.toLowerCase().includes(q) ||
        deal.category.toLowerCase().includes(q)
    );
  }, [query, deals]);

  const handleCopy = async (dealId: string, code: string) => {
    try {
      await navigator.clipboard.writeText(code);
      setCopiedId(dealId);
      setTimeout(() => setCopiedId(null), 1200);
    } catch {
      alert("Copy failed. Please copy manually.");
    }
  };

  const badge = (score: number) => {
    if (score >= 85) return "Verified";
    if (score >= 60) return "Likely";
    return "Unverified";
  };

  return (
    <main className="min-h-screen bg-premium-gradient">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <header className="mb-8">
          <h1 className="text-3xl font-semibold tracking-tight">
            AI Deals Hunter
          </h1>
          <p className="mt-2 text-sm text-white/70">
            Auto-scraped AI free trials, free tiers, credits, and promo codes.
          </p>
        </header>

        <div className="mb-8">
          <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 shadow-lg backdrop-blur">
            <Search className="h-5 w-5 text-white/60" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by tool name or category..."
              className="w-full bg-transparent text-sm outline-none placeholder:text-white/40"
            />
          </div>
        </div>

        {loading ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-10 text-center text-white/60">
            Loading scraped deals...
          </div>
        ) : filteredDeals.length === 0 ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-10 text-center text-white/60">
            No deals found yet. Run GitHub Actions scraper.
          </div>
        ) : (
          <section className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {filteredDeals.map((deal) => (
              <div
                key={deal.id}
                className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-xl backdrop-blur transition hover:border-white/20 hover:bg-white/10"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold">{deal.tool_name}</h2>
                    <p className="text-xs text-white/60">{deal.category}</p>
                  </div>

                  <a
                    href={deal.link}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white/80 transition hover:border-white/20 hover:bg-black/60"
                  >
                    Visit <ExternalLink className="h-4 w-4" />
                  </a>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  <span className="rounded-full border border-white/10 bg-black/30 px-3 py-1 text-[11px] text-white/70">
                    {deal.deal_type}
                  </span>
                  <span className="rounded-full border border-white/10 bg-black/30 px-3 py-1 text-[11px] text-white/70">
                    {deal.deal_value}
                  </span>
                  <span className="rounded-full border border-white/10 bg-black/50 px-3 py-1 text-[11px] text-white/80">
                    {badge(deal.confidence_score)} • {deal.confidence_score}%
                  </span>
                </div>

                {deal.promo_code ? (
                  <div className="mt-4 flex items-center justify-between gap-3 rounded-xl border border-white/10 bg-black/40 px-4 py-3">
                    <div className="flex flex-col">
                      <span className="text-[10px] uppercase tracking-wider text-white/50">
                        Promo Code
                      </span>
                      <span className="font-mono text-sm font-semibold tracking-wide">
                        {deal.promo_code}
                      </span>
                    </div>

                    <button
                      onClick={() =>
                        handleCopy(deal.id, deal.promo_code as string)
                      }
                      className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-white/80 transition hover:border-white/20 hover:bg-white/10"
                    >
                      {copiedId === deal.id ? (
                        <>
                          <Check className="h-4 w-4" /> Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="h-4 w-4" /> Copy
                        </>
                      )}
                    </button>
                  </div>
                ) : (
                  <div className="mt-4 rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-xs text-white/60">
                    No promo code detected ✅
                  </div>
                )}

                <a
                  href={deal.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-4 block text-xs text-white/40 hover:text-white/70"
                >
                  Source ↗
                </a>
              </div>
            ))}
          </section>
        )}

        <footer className="mt-12 text-center text-xs text-white/40">
          Daily auto-scrape via GitHub Actions + Supabase • No paid APIs
        </footer>
      </div>
    </main>
  );
}