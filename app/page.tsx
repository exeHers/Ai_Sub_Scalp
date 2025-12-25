"use client";
import React, { useState, useEffect } from 'react';
import { Search, Zap, Copy, CheckCircle, ExternalLink } from 'lucide-react';

type DealType = 'Free Trial' | 'Promo Code' | 'Free Tier';

interface AIModel {
  id: string;
  name: string;
  category: string;
  dealType: DealType;
  value: string;
  url: string;
  code?: string;
}

const initialDeals: AIModel[] = [
  { id: '1', name: 'Perplexity Pro', category: 'Research', dealType: 'Promo Code', value: 'HOLIDAY25 - 25% OFF', url: 'https://perplexity.ai/pro', code: 'HOLIDAY25' },
  { id: '2', name: 'Midjourney', category: 'Image', dealType: 'Free Trial', value: '25 Free Images', url: 'https://midjourney.com', code: '' },
  { id: '3', name: 'Claude AI', category: 'Text', dealType: 'Free Tier', value: 'Unlimited Basic', url: 'https://claude.ai', code: '' },
  { id: '4', name: 'ElevenLabs', category: 'Voice', dealType: 'Promo Code', value: 'VOICE50 - 50% OFF', url: 'https://elevenlabs.io', code: 'VOICE50' },
];

export default function Home() {
  const [query, setQuery] = useState('');
  const [deals, setDeals] = useState(initialDeals);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const filteredDeals = deals.filter(deal =>
    deal.name.toLowerCase().includes(query.toLowerCase()) ||
    deal.category.toLowerCase().includes(query.toLowerCase())
  );

  const copyCode = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 text-white">
      {/* Header */}
      <header className="border-b border-white/10 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center">
              <Zap className="w-7 h-7" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                AI Deals Hunter
              </h1>
              <p className="text-sm text-gray-400">Live promo codes & free trials</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-12">
        {/* Search */}
        <div className="mb-12">
          <div className="relative max-w-2xl mx-auto">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search Midjourney, GPT, Claude..."
              className="w-full pl-12 pr-6 py-4 bg-white/5 border border-white/20 rounded-2xl backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all text-lg"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
        </div>

        {/* Deals Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDeals.map((deal) => (
            <div key={deal.id} className="group bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 hover:border-purple-500/50 hover:shadow-2xl hover:shadow-purple-500/10 transition-all hover:-translate-y-2">
              {/* Header */}
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center font-bold text-2xl">
                    {deal.name.slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="text-xl font-bold">{deal.name}</h3>
                    <span className="inline-block mt-1 px-3 py-1 bg-purple-500/20 text-purple-300 rounded-full text-sm font-medium">
                      {deal.category}
                    </span>
                  </div>
                </div>
              </div>

              {/* Deal Info */}
              <div className="mb-8">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-xs font-bold">
                    {deal.dealType}
                  </span>
                </div>
                <p className="text-2xl font-bold text-white">{deal.value}</p>
              </div>

              {/* Buttons */}
              <div className="flex gap-3">
                {deal.code ? (
                  <button
                    onClick={() => copyCode(deal.code!, deal.id)}
                    className="flex-1 bg-white/10 hover:bg-white/20 border border-white/20 py-4 px-6 rounded-2xl text-white font-semibold flex items-center justify-center gap-2 transition-all group-hover:bg-white/30"
                  >
                    {copiedId === deal.id ? (
                      <CheckCircle className="w-5 h-5 text-green-400" />
                    ) : (
                      <Copy className="w-5 h-5" />
                    )}
                    {copiedId === deal.id ? 'Copied!' : deal.code}
                  </button>
                ) : (
                  <div className="flex-1 bg-gray-700/50 text-gray-400 py-4 px-6 rounded-2xl text-center font-medium text-sm">
                    No code needed
                  </div>
                )}
                <a
                  href={deal.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-14 h-14 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-2xl flex items-center justify-center shadow-lg hover:shadow-xl transition-all"
                >
                  <ExternalLink className="w-5 h-5" />
                </a>
              </div>
            </div>
          ))}
        </div>

        {filteredDeals.length === 0 && (
          <div className="text-center py-24">
            <p className="text-xl text-gray-400">No deals found. Try searching "Claude" or "Midjourney"</p>
          </div>
        )}
      </main>
    </div>
  );
}
