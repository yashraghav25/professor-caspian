"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import {
  Activity,
  Briefcase,
  Play,
  Square,
  RefreshCcw,
  TrendingUp,
  TrendingDown,
  Clock,
  Newspaper,
  Sparkles,
  Check,
  Loader2,
  Settings2,
} from "lucide-react";

interface Holding {
  id: number;
  symbol: string;
  quantity: number;
  average_price: number;
  current_price: number;
  position_value: number;
  weight: number;
  unrealized_pnl: number;
  change_percent: number;
}

interface Portfolio {
  id: number;
  name: string;
  total_value: number;
  invested_value: number;
  cash_value: number;
  total_pnl: number;
  total_pnl_percent: number;
  holdings: Holding[];
}

interface Alert {
  id: number;
  alert_id: string;
  severity_level: string;
  severity_score: number;
  title: string;
  reason: string;
  ai_summary?: string | null;
  status: string;
  created_at: string;
}

interface NewsItem {
  id: number;
  event_id: string;
  headline: string;
  summary: string | null;
  source: string;
  ai_analysis: {
    entities?: string[];
    sectors?: string[];
    sentiment?: string;
    impact?: string;
    confidence?: number;
    reason?: string;
  } | null;
  created_at: string;
}

interface SimStatus {
  running: boolean;
  scenario: string | null;
  progress: number;
  latest_event: string | null;
  latest_ai_summary?: string | null;
  agent_busy?: boolean;
}

const API_BASE = "http://localhost:8000/api";

const POPULAR_TICKERS = [
  { symbol: "NVDA", name: "NVIDIA" },
  { symbol: "AAPL", name: "Apple" },
  { symbol: "MSFT", name: "Microsoft" },
  { symbol: "GOOGL", name: "Alphabet" },
  { symbol: "AMZN", name: "Amazon" },
  { symbol: "META", name: "Meta" },
  { symbol: "TSLA", name: "Tesla" },
  { symbol: "AMD", name: "AMD" },
  { symbol: "AVGO", name: "Broadcom" },
  { symbol: "NFLX", name: "Netflix" },
  { symbol: "CRM", name: "Salesforce" },
  { symbol: "ORCL", name: "Oracle" },
];

const TIMEFRAMES = [
  { id: "1_month", label: "1 Month Ago" },
  { id: "6_months", label: "6 Months Ago" },
  { id: "1_year", label: "1 Year Ago" },
] as const;

const MAX_SELECTIONS = 5;

export default function Dashboard() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [simStatus, setSimStatus] = useState<SimStatus>({
    running: false,
    scenario: null,
    progress: 0,
    latest_event: null,
  });
  const [loading, setLoading] = useState(true);
  const [needsSetup, setNeedsSetup] = useState(false);

  // Onboarding state
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>([]);
  const [timeframe, setTimeframe] = useState<string>("6_months");
  const [setupLoading, setSetupLoading] = useState(false);
  const [setupError, setSetupError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const [portRes, alertsRes, newsRes, simRes] = await Promise.all([
        axios.get(`${API_BASE}/portfolio`).catch((err) => {
          if (err?.response?.status === 404) return { data: null };
          return { data: null };
        }),
        axios.get(`${API_BASE}/alerts`).catch(() => ({ data: [] })),
        axios.get(`${API_BASE}/events/news`).catch(() => ({ data: [] })),
        axios
          .get(`${API_BASE}/simulation/status`)
          .catch(() => ({
            data: {
              running: false,
              scenario: null,
              progress: 0,
              latest_event: null,
              latest_ai_summary: null,
              agent_busy: false,
            },
          })),
      ]);

      const port = portRes.data as Portfolio | null;
      if (!port || !port.holdings || port.holdings.length === 0) {
        setPortfolio(null);
        setNeedsSetup(true);
      } else {
        setPortfolio(port);
        setNeedsSetup(false);
      }

      setAlerts(Array.isArray(alertsRes.data) ? alertsRes.data : []);
      setNews(Array.isArray(newsRes.data) ? newsRes.data : []);
      setSimStatus(simRes.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  const toggleSymbol = (symbol: string) => {
    setSelectedSymbols((prev) => {
      if (prev.includes(symbol)) return prev.filter((s) => s !== symbol);
      if (prev.length >= MAX_SELECTIONS) return prev;
      return [...prev, symbol];
    });
  };

  const submitSetup = async () => {
    if (selectedSymbols.length !== MAX_SELECTIONS) {
      setSetupError(`Please select exactly ${MAX_SELECTIONS} stocks.`);
      return;
    }
    setSetupLoading(true);
    setSetupError(null);
    try {
      await axios.post(`${API_BASE}/setup/portfolio`, {
        symbols: selectedSymbols,
        timeframe,
      });
      await fetchData();
    } catch (err: any) {
      setSetupError(err?.response?.data?.detail || err.message || "Setup failed");
    } finally {
      setSetupLoading(false);
    }
  };

  const startDemoCrash = async () => {
    try {
      await axios.post(`${API_BASE}/simulation/demo-crash`);
      fetchData();
    } catch (err: any) {
      console.warn("Demo crash failed:", err?.response?.data?.detail || err.message);
    }
  };

  const stopSim = async () => {
    await axios.post(`${API_BASE}/simulation/stop`);
    fetchData();
  };

  const resetPortfolio = async () => {
    try {
      await axios.delete(`${API_BASE}/setup/portfolio`);
      setPortfolio(null);
      setSelectedSymbols([]);
      setNeedsSetup(true);
    } catch (err: any) {
      console.warn("Reset failed:", err?.response?.data?.detail || err.message);
    }
  };

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(val);
  const formatPercent = (val: number) => `${val > 0 ? "+" : ""}${val.toFixed(2)}%`;

  // Prefer alert with real agent narrative; fall back to sim status / news
  const alertWithAI =
    alerts.find((a) => a.ai_summary) ||
    alerts.find(
      (a) => a.severity_level === "CRITICAL" || a.severity_level === "HIGH"
    ) ||
    alerts[0];

  const aiNarrative =
    simStatus.latest_ai_summary ||
    alertWithAI?.ai_summary ||
    null;

  const isAnalyzing =
    !!simStatus.agent_busy ||
    (simStatus.running && !aiNarrative);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center gap-3 text-gray-400">
        <Loader2 className="w-5 h-5 animate-spin text-primary" />
        Loading SentinelAI...
      </div>
    );
  }

  return (
    <main className="min-h-screen p-6 max-w-7xl mx-auto space-y-6 relative">
      {/* Onboarding Modal */}
      {needsSetup && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="glass-panel w-full max-w-2xl p-6 md:p-8 space-y-6 animate-in">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="bg-primary/20 p-2 rounded-lg">
                  <Activity className="text-primary w-6 h-6" />
                </div>
                <h1 className="text-2xl font-bold tracking-tight">Welcome to SentinelAI</h1>
              </div>
              <p className="text-sm text-gray-400">
                Select {MAX_SELECTIONS} stocks and a purchase date to start live portfolio
                monitoring with Finnhub market data.
              </p>
            </div>

            <div>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-gray-300">
                  Choose Stocks
                </h2>
                <span className="text-xs text-gray-500">
                  {selectedSymbols.length}/{MAX_SELECTIONS} selected
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {POPULAR_TICKERS.map((t) => {
                  const selected = selectedSymbols.includes(t.symbol);
                  const disabled = !selected && selectedSymbols.length >= MAX_SELECTIONS;
                  return (
                    <button
                      key={t.symbol}
                      type="button"
                      disabled={disabled}
                      onClick={() => toggleSymbol(t.symbol)}
                      className={`flex items-center gap-2 px-3 py-2.5 rounded-lg border text-left text-sm transition-colors
                        ${selected
                          ? "border-primary bg-primary/15 text-white"
                          : disabled
                            ? "border-white/5 bg-black/20 text-gray-600 cursor-not-allowed"
                            : "border-white/10 bg-black/30 text-gray-300 hover:border-primary/40 hover:bg-white/5"
                        }`}
                    >
                      <span
                        className={`w-4 h-4 rounded border flex items-center justify-center shrink-0
                          ${selected ? "bg-primary border-primary" : "border-gray-600"}`}
                      >
                        {selected && <Check className="w-3 h-3 text-white" />}
                      </span>
                      <span>
                        <span className="font-semibold block">{t.symbol}</span>
                        <span className="text-xs text-gray-500">{t.name}</span>
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <h2 className="text-sm font-semibold text-gray-300 mb-3">
                Purchase Date (Cost Basis)
              </h2>
              <div className="flex flex-wrap gap-2">
                {TIMEFRAMES.map((tf) => (
                  <button
                    key={tf.id}
                    type="button"
                    onClick={() => setTimeframe(tf.id)}
                    className={`px-4 py-2 rounded-lg text-sm border transition-colors
                      ${timeframe === tf.id
                        ? "border-primary bg-primary/20 text-primary"
                        : "border-white/10 bg-black/30 text-gray-400 hover:border-white/20"
                      }`}
                  >
                    {tf.label}
                  </button>
                ))}
              </div>
            </div>

            {setupError && (
              <p className="text-sm text-danger bg-danger/10 border border-danger/20 rounded-lg px-3 py-2">
                {setupError}
              </p>
            )}

            <button
              type="button"
              onClick={submitSetup}
              disabled={setupLoading || selectedSymbols.length !== MAX_SELECTIONS}
              className="w-full py-3 rounded-lg font-semibold text-sm flex items-center justify-center gap-2
                bg-primary text-white hover:bg-primary-hover disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {setupLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Fetching historical prices...
                </>
              ) : (
                <>Start Live Monitoring</>
              )}
            </button>
          </div>
        </div>
      )}

      <header className="flex items-center justify-between pb-4 border-b border-card-border">
        <div className="flex items-center gap-3">
          <div className="bg-primary/20 p-2 rounded-lg">
            <Activity className="text-primary w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">SentinelAI</h1>
            <p className="text-sm text-gray-400">Autonomous Portfolio Monitoring</p>
          </div>
        </div>

        <div className="flex items-center gap-4 glass-panel px-4 py-2">
          <div className="text-sm text-gray-400 mr-2 flex items-center gap-2">
            <RefreshCcw
              className={`w-4 h-4 ${simStatus.running ? "animate-spin text-primary" : ""}`}
            />
            {simStatus.running
              ? `Demo: ${simStatus.scenario} (${simStatus.progress}%)`
              : "Live Tracking"}
          </div>

          {!needsSetup && (
            <button
              onClick={resetPortfolio}
              className="px-3 py-1.5 rounded text-sm font-medium flex items-center gap-2 transition-colors
                bg-white/5 text-gray-300 hover:bg-white/10"
              title="Clear portfolio and pick new stocks"
            >
              <Settings2 className="w-4 h-4" /> Change Stocks
            </button>
          )}

          <button
            onClick={() => (simStatus.running ? stopSim() : startDemoCrash())}
            disabled={needsSetup}
            className={`px-3 py-1.5 rounded text-sm font-medium flex items-center gap-2 transition-colors disabled:opacity-40
              ${simStatus.running
                ? "bg-danger/20 text-danger hover:bg-danger/30"
                : "bg-danger/20 text-danger hover:bg-danger/30"
              }`}
          >
            {simStatus.running ? (
              <>
                <Square className="w-4 h-4" /> Stop
              </>
            ) : (
              <>
                <Play className="w-4 h-4" /> Run Demo Crash
              </>
            )}
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Portfolio & Holdings */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-panel p-6">
            <div className="flex items-center gap-2 mb-6">
              <Briefcase className="w-5 h-5 text-gray-400" />
              <h2 className="text-lg font-semibold">Portfolio Overview</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-black/20 rounded-lg border border-white/5">
                <p className="text-sm text-gray-400 mb-1">Total Value</p>
                <p className="text-2xl font-bold">
                  {formatCurrency(portfolio?.total_value || 0)}
                </p>
              </div>
              <div className="p-4 bg-black/20 rounded-lg border border-white/5">
                <p className="text-sm text-gray-400 mb-1">Invested</p>
                <p className="text-xl font-semibold">
                  {formatCurrency(portfolio?.invested_value || 0)}
                </p>
              </div>
              <div className="p-4 bg-black/20 rounded-lg border border-white/5">
                <p className="text-sm text-gray-400 mb-1">Total P/L</p>
                <p
                  className={`text-xl font-bold ${(portfolio?.total_pnl || 0) >= 0 ? "text-success" : "text-danger"}`}
                >
                  {formatCurrency(portfolio?.total_pnl || 0)}
                  <span className="text-sm ml-2">
                    {formatPercent(portfolio?.total_pnl_percent || 0)}
                  </span>
                </p>
              </div>
            </div>
          </div>

          <div className="glass-panel p-6">
            <h2 className="text-lg font-semibold mb-4">Current Holdings</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="text-sm text-gray-400 border-b border-card-border">
                    <th className="pb-3 font-medium">Asset</th>
                    <th className="pb-3 font-medium">Price</th>
                    <th className="pb-3 font-medium">Holdings</th>
                    <th className="pb-3 font-medium">Value</th>
                    <th className="pb-3 font-medium">P/L</th>
                    <th className="pb-3 font-medium text-right">Weight</th>
                  </tr>
                </thead>
                <tbody className="text-sm">
                  {!portfolio?.holdings?.length ? (
                    <tr>
                      <td colSpan={6} className="py-10 text-center text-gray-500">
                        No holdings yet — complete setup to begin.
                      </td>
                    </tr>
                  ) : (
                    portfolio.holdings
                      .filter((h) => h.symbol.toUpperCase() !== "CASH")
                      .map((h) => (
                        <tr
                          key={h.id}
                          className="border-b border-card-border/50 last:border-0 hover:bg-white/5 transition-colors"
                        >
                          <td className="py-4 font-semibold">{h.symbol}</td>
                          <td className="py-4">
                            {formatCurrency(h.current_price)}
                            {h.change_percent !== 0 && (
                              <span
                                className={`ml-2 text-xs px-1.5 py-0.5 rounded ${
                                  h.change_percent > 0
                                    ? "bg-success/10 text-success"
                                    : "bg-danger/10 text-danger"
                                }`}
                              >
                                {h.change_percent > 0 ? (
                                  <TrendingUp className="w-3 h-3 inline mr-1" />
                                ) : (
                                  <TrendingDown className="w-3 h-3 inline mr-1" />
                                )}
                                {Math.abs(h.change_percent).toFixed(2)}%
                              </span>
                            )}
                          </td>
                          <td className="py-4">{h.quantity}</td>
                          <td className="py-4 font-medium">
                            {formatCurrency(h.position_value)}
                          </td>
                          <td
                            className={`py-4 ${h.unrealized_pnl >= 0 ? "text-success" : "text-danger"}`}
                          >
                            {formatCurrency(h.unrealized_pnl)}
                          </td>
                          <td className="py-4 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <span className="w-12 text-right">
                                {h.weight.toFixed(1)}%
                              </span>
                              <div className="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-primary"
                                  style={{ width: `${Math.min(h.weight, 100)}%` }}
                                />
                              </div>
                            </div>
                          </td>
                        </tr>
                      ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right: AI Summary + News Feed */}
        <div className="space-y-6">
          {/* AI Summarization Box */}
          <div className="glass-panel p-5 border-primary/20">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className={`w-5 h-5 text-primary ${isAnalyzing ? "animate-pulse" : ""}`} />
              <h2 className="text-lg font-semibold">AI Analysis</h2>
              {isAnalyzing && (
                <span className="ml-auto text-xs text-primary flex items-center gap-1.5">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Agent analyzing…
                </span>
              )}
            </div>

            {aiNarrative ? (
              <div className="space-y-3">
                {alertWithAI && (
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs font-bold px-2 py-0.5 rounded ${
                        alertWithAI.severity_level === "CRITICAL"
                          ? "bg-danger text-white"
                          : alertWithAI.severity_level === "HIGH"
                            ? "bg-warning text-black"
                            : "bg-blue-500/20 text-blue-400"
                      }`}
                    >
                      {alertWithAI.severity_level}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(alertWithAI.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                )}
                <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap ai-narrative">
                  {aiNarrative}
                </div>
              </div>
            ) : isAnalyzing ? (
              <div className="text-center py-6 text-gray-400 text-sm space-y-2">
                <Loader2 className="w-7 h-7 mx-auto animate-spin text-primary" />
                <p>Crash detected — SentinelAI agent is drafting impact analysis and suggested actions…</p>
              </div>
            ) : (
              <div className="text-center py-6 text-gray-500 text-sm">
                <Sparkles className="w-7 h-7 mx-auto mb-2 opacity-20" />
                Waiting for significant events. Run a demo crash to trigger AI analysis.
              </div>
            )}
          </div>

          {/* News Feed */}
          <div className="glass-panel p-6 flex flex-col max-h-140">
            <div className="flex items-center gap-2 mb-4">
              <Newspaper className="w-5 h-5 text-gray-400" />
              <h2 className="text-lg font-semibold">Live News</h2>
              {news.length > 0 && (
                <span className="ml-auto bg-primary/20 text-primary text-xs font-bold px-2 py-1 rounded-full">
                  {news.length}
                </span>
              )}
            </div>

            <div className="flex-1 overflow-y-auto pr-2 space-y-3">
              {news.length === 0 ? (
                <div className="text-center py-10 text-gray-500 text-sm">
                  <Newspaper className="w-8 h-8 mx-auto mb-2 opacity-20" />
                  News headlines will appear once your portfolio is tracking.
                </div>
              ) : (
                news.map((item) => (
                  <div
                    key={item.id}
                    className="bg-black/30 border border-white/5 p-4 rounded-lg"
                  >
                    <div className="flex justify-between items-start mb-2 gap-2">
                      <span className="text-xs font-medium text-primary truncate">
                        {item.source}
                      </span>
                      <span className="text-xs text-gray-500 flex items-center gap-1 shrink-0">
                        <Clock className="w-3 h-3" />
                        {new Date(item.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                    <h3 className="font-semibold text-sm mb-1 leading-snug">
                      {item.headline}
                    </h3>
                    {item.summary && (
                      <p className="text-xs text-gray-400 line-clamp-3">{item.summary}</p>
                    )}
                    {item.ai_analysis?.sentiment && (
                      <div className="mt-2 flex gap-2">
                        <span className="text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded bg-white/5 text-gray-400">
                          {item.ai_analysis.sentiment}
                        </span>
                        {item.ai_analysis.impact && (
                          <span className="text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded bg-white/5 text-gray-400">
                            {item.ai_analysis.impact} impact
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
