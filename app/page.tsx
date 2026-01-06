"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ExternalLink,
  Search,
  Copy,
  Check,
  Sparkles,
  ShieldCheck,
  Clock
} from "lucide-react";

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
  const [showFilters, setShowFilters] = useState(false);
  const [status, setStatus] = useState<{
    status: string;
    last_updated: string | null;
    deals_count: number;
  }>({ status: "idle", last_updated: null, deals_count: 0 });

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

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const res = await fetch("/api/status");
        const json = await res.json();
        setStatus(json);
      } catch {
        setStatus({ status: "offline", last_updated: null, deals_count: 0 });
      }
    };

    loadStatus();
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

  const trackedCount = status.deals_count || deals.length;

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#0b0b13]">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-32 left-1/2 h-96 w-96 -translate-x-1/2 rounded-full bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.35),transparent_65%)] blur-3xl" />
        <div className="absolute bottom-0 right-0 h-80 w-80 rounded-full bg-[radial-gradient(circle_at_center,rgba(16,185,129,0.35),transparent_70%)] blur-3xl" />
        <div className="absolute left-10 top-24 h-44 w-44 rounded-full border border-white/10 bg-white/5 blur-2xl" />
      </div>

      <div className="relative mx-auto max-w-6xl px-4 py-12 sm:py-16">
        <header className="flex flex-col gap-6">
          <div className="inline-flex w-fit items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs uppercase tracking-[0.3em] text-white/70">
            <Sparkles className="h-4 w-4 text-emerald-300" />
            AI Sub Scalp
          </div>
          <div className="flex flex-col gap-4">
            <h1 className="font-display text-4xl font-semibold leading-tight sm:text-5xl">
              The promo scalper for real AI freebies.
            </h1>
            <p className="max-w-2xl text-base text-white/70">
              Daily sweep across search, communities, and directories to surface
              only full-free, open-source, or 100% off offers. Strict rules. No
              student gates. No partial discounts.
            </p>
          </div>
          <div className="flex flex-wrap gap-3 text-xs text-white/60">
            <span className="rounded-full border border-white/10 bg-black/40 px-3 py-2">
              Free trials and full credits only
            </span>
            <span className="rounded-full border border-white/10 bg-black/40 px-3 py-2">
              Rejects 10% / 50% / 70% promos
            </span>
            <span className="rounded-full border border-white/10 bg-black/40 px-3 py-2">
              Open-source detection
            </span>
            <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/40 px-3 py-2">
              <Clock className="h-4 w-4 text-emerald-300" />
              {status.last_updated
                ? `Last scan ${new Date(status.last_updated).toLocaleString()}`
                : "Scan status pending"}
            </span>
          </div>
        </header>

        <section className="mt-10 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="glass rounded-3xl p-6 sm:p-8">
            <div className="flex items-center gap-3 text-sm text-white/70">
              <ShieldCheck className="h-5 w-5 text-emerald-300" />
              Verified pipeline with strict filters and content checks
            </div>
            <div className="mt-6 grid gap-4 sm:grid-cols-3">
              <div className="rounded-2xl border border-white/10 bg-black/40 p-4">
                <p className="text-xs text-white/60">Sources</p>
                <p className="mt-2 text-2xl font-semibold">8+</p>
                <p className="text-xs text-white/50">Search, Reddit, HN, GH</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-black/40 p-4">
                <p className="text-xs text-white/60">Filter Rules</p>
                <p className="mt-2 text-2xl font-semibold">Strict</p>
                <p className="text-xs text-white/50">No partial discounts</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-black/40 p-4">
                <p className="text-xs text-white/60">Deals Tracked</p>
                <p className="mt-2 text-2xl font-semibold">{trackedCount}</p>
                <p className="text-xs text-white/50">Auto-refreshed daily</p>
              </div>
            </div>
          </div>

          <div className="glass rounded-3xl p-6 sm:p-8">
            <h2 className="font-display text-2xl font-semibold">
              Filter and scan
            </h2>
            <p className="mt-2 text-sm text-white/60">
              Search by tool name or category. Copy promo codes with one click.
            </p>
            <div className="mt-6">
              <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 shadow-lg backdrop-blur">
                <Search className="h-5 w-5 text-white/60" />
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search by tool name or category..."
                  className="w-full bg-transparent text-sm outline-none placeholder:text-white/40"
                />
              </div>
              <button
                type="button"
                onClick={() => setShowFilters((prev) => !prev)}
                className="mt-4 inline-flex items-center justify-center rounded-full border border-white/10 bg-black/30 px-4 py-2 text-[11px] uppercase tracking-[0.2em] text-white/60 sm:hidden"
              >
                {showFilters ? "Hide Filters" : "Show Filters"}
              </button>
              <div
                className={`mt-4 flex flex-wrap gap-2 text-[11px] text-white/60 ${
                  showFilters ? "flex" : "hidden"
                } sm:flex`}
              >
                {["Free Trial", "100% Off", "Free Credits", "Open-Source"].map(
                  (tag) => (
                    <span
                      key={tag}
                      className="rounded-full border border-white/10 bg-black/30 px-3 py-1"
                    >
                      {tag}
                    </span>
                  )
                )}
              </div>
            </div>
          </div>
        </section>

        <section className="mt-12">
          {loading ? (
            <div className="glass rounded-2xl p-10 text-center text-white/60">
              Loading verified promos...
            </div>
          ) : filteredDeals.length === 0 ? (
            <div className="glass rounded-2xl p-10 text-center text-white/60">
              No deals found yet. Run a scan to populate the feed.
            </div>
          ) : (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {filteredDeals.map((deal) => (
                <div
                  key={deal.id}
                  className="glass rounded-2xl p-5 transition hover:-translate-y-1 hover:border-white/20"
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
                    <span className="rounded-full border border-white/10 bg-emerald-500/10 px-3 py-1 text-[11px] text-emerald-200">
                      {badge(deal.confidence_score)} · {deal.confidence_score}%
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
                            <Check className="h-4 w-4" /> Copied
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
                      No promo code detected.
                    </div>
                  )}

                  <a
                    href={deal.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-4 block text-xs text-white/40 hover:text-white/70"
                  >
                    Source
                  </a>
                </div>
              ))}
            </div>
          )}
        </section>

        <footer className="mt-14 text-center text-xs text-white/40">
          Daily auto-scrape via CLI + scheduled runs. Respectful rate limits.
        </footer>
      </div>
    </main>
  );
}
