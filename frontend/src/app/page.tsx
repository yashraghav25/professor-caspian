"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { 
  Activity, 
  AlertTriangle, 
  Briefcase, 
  Play, 
  Square, 
  RefreshCcw, 
  TrendingUp, 
  TrendingDown,
  Clock,
  ShieldAlert
} from "lucide-react";

// Types
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
  status: string;
  created_at: string;
}

interface SimStatus {
  running: boolean;
  scenario: string | null;
  progress: number;
  latest_event: string | null;
}

const API_BASE = "http://localhost:8000/api";

export default function Dashboard() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [simStatus, setSimStatus] = useState<SimStatus>({ running: false, scenario: null, progress: 0, latest_event: null });
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [portRes, alertsRes, simRes] = await Promise.all([
        axios.get(`${API_BASE}/portfolio`).catch(() => ({ data: null })),
        axios.get(`${API_BASE}/alerts`).catch(() => ({ data: [] })),
        axios.get(`${API_BASE}/simulation/status`).catch(() => ({ data: { running: false, scenario: null, progress: 0, latest_event: null } }))
      ]);
      
      if (portRes.data) setPortfolio(portRes.data);
      setAlerts(alertsRes.data);
      setSimStatus(simRes.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  const startSim = async (scenario: string) => {
    try {
      await axios.post(`${API_BASE}/simulation/start/${scenario}`);
      fetchData();
    } catch (err: any) {
      console.warn('Simulation start failed:', err?.response?.data?.detail || err.message);
    }
  };

  const stopSim = async () => {
    await axios.post(`${API_BASE}/simulation/stop`);
    fetchData();
  };

  const formatCurrency = (val: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
  const formatPercent = (val: number) => `${val > 0 ? '+' : ''}${val.toFixed(2)}%`;

  if (loading) return <div className="min-h-screen flex items-center justify-center">Loading SentinelAI...</div>;

  return (
    <main className="min-h-screen p-6 max-w-7xl mx-auto space-y-6">
      <header className="flex items-center justify-between pb-4 border-b border-[var(--color-card-border)]">
        <div className="flex items-center gap-3">
          <div className="bg-primary/20 p-2 rounded-lg">
            <Activity className="text-primary w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">SentinelAI</h1>
            <p className="text-sm text-gray-400">Autonomous Portfolio Monitoring</p>
          </div>
        </div>
        
        {/* Simulation Controls */}
        <div className="flex items-center gap-4 glass-panel px-4 py-2">
          <div className="text-sm text-gray-400 mr-2 flex items-center gap-2">
            <RefreshCcw className={`w-4 h-4 ${simStatus.running ? 'animate-spin text-primary' : ''}`} />
            {simStatus.running ? `Running: ${simStatus.scenario} (${simStatus.progress}%)` : 'Simulation Idle'}
          </div>
          
          <button 
            onClick={() => simStatus.running ? stopSim() : startSim("rapid_crash")}
            className={`px-3 py-1.5 rounded text-sm font-medium flex items-center gap-2 transition-colors
              ${simStatus.running 
                ? 'bg-danger/20 text-danger hover:bg-danger/30' 
                : 'bg-primary/20 text-primary hover:bg-primary/30'}`}
          >
            {simStatus.running ? <><Square className="w-4 h-4"/> Stop</> : <><Play className="w-4 h-4"/> Run Crash Test</>}
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Portfolio & Holdings */}
        <div className="lg:col-span-2 space-y-6">
          {/* Portfolio Summary Card */}
          <div className="glass-panel p-6">
            <div className="flex items-center gap-2 mb-6">
              <Briefcase className="w-5 h-5 text-gray-400" />
              <h2 className="text-lg font-semibold">Portfolio Overview</h2>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-black/20 rounded-lg border border-white/5">
                <p className="text-sm text-gray-400 mb-1">Total Value</p>
                <p className="text-2xl font-bold">{formatCurrency(portfolio?.total_value || 0)}</p>
              </div>
              <div className="p-4 bg-black/20 rounded-lg border border-white/5">
                <p className="text-sm text-gray-400 mb-1">Invested</p>
                <p className="text-xl font-semibold">{formatCurrency(portfolio?.invested_value || 0)}</p>
              </div>
              <div className="p-4 bg-black/20 rounded-lg border border-white/5">
                <p className="text-sm text-gray-400 mb-1">Cash</p>
                <p className="text-xl font-semibold">{formatCurrency(portfolio?.cash_value || 0)}</p>
              </div>
              <div className="p-4 bg-black/20 rounded-lg border border-white/5">
                <p className="text-sm text-gray-400 mb-1">Total P/L</p>
                <p className={`text-xl font-bold ${(portfolio?.total_pnl || 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                  {formatCurrency(portfolio?.total_pnl || 0)}
                  <span className="text-sm ml-2">{formatPercent(portfolio?.total_pnl_percent || 0)}</span>
                </p>
              </div>
            </div>
          </div>

          {/* Holdings Table */}
          <div className="glass-panel p-6">
            <h2 className="text-lg font-semibold mb-4">Current Holdings</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="text-sm text-gray-400 border-b border-[var(--color-card-border)]">
                    <th className="pb-3 font-medium">Asset</th>
                    <th className="pb-3 font-medium">Price</th>
                    <th className="pb-3 font-medium">Holdings</th>
                    <th className="pb-3 font-medium">Value</th>
                    <th className="pb-3 font-medium">P/L</th>
                    <th className="pb-3 font-medium text-right">Weight</th>
                  </tr>
                </thead>
                <tbody className="text-sm">
                  {portfolio?.holdings.map((h) => (
                    <tr key={h.id} className="border-b border-[var(--color-card-border)]/50 last:border-0 hover:bg-white/5 transition-colors">
                      <td className="py-4 font-semibold">{h.symbol}</td>
                      <td className="py-4">
                        {formatCurrency(h.current_price)}
                        {h.change_percent !== 0 && (
                          <span className={`ml-2 text-xs px-1.5 py-0.5 rounded ${h.change_percent > 0 ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`}>
                            {h.change_percent > 0 ? <TrendingUp className="w-3 h-3 inline mr-1"/> : <TrendingDown className="w-3 h-3 inline mr-1"/>}
                            {Math.abs(h.change_percent).toFixed(2)}%
                          </span>
                        )}
                      </td>
                      <td className="py-4">{h.quantity}</td>
                      <td className="py-4 font-medium">{formatCurrency(h.position_value)}</td>
                      <td className={`py-4 ${h.unrealized_pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                        {formatCurrency(h.unrealized_pnl)}
                      </td>
                      <td className="py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <span className="w-12 text-right">{h.weight.toFixed(1)}%</span>
                          <div className="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                            <div className="h-full bg-primary" style={{ width: `${h.weight}%` }} />
                          </div>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: Alerts & Agent Activity */}
        <div className="space-y-6">
          {/* Active Alerts */}
          <div className="glass-panel p-6 flex flex-col h-full max-h-[800px]">
            <div className="flex items-center gap-2 mb-4">
              <ShieldAlert className="w-5 h-5 text-gray-400" />
              <h2 className="text-lg font-semibold">Active Alerts</h2>
              {alerts.length > 0 && (
                <span className="ml-auto bg-danger/20 text-danger text-xs font-bold px-2 py-1 rounded-full">
                  {alerts.length} Active
                </span>
              )}
            </div>
            
            <div className="flex-1 overflow-y-auto pr-2 space-y-3">
              {alerts.length === 0 ? (
                <div className="text-center py-10 text-gray-500">
                  <Activity className="w-8 h-8 mx-auto mb-2 opacity-20" />
                  No active alerts
                </div>
              ) : (
                alerts.map(alert => (
                  <div key={alert.id} className="bg-black/30 border border-white/5 p-4 rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <span className={`text-xs font-bold px-2 py-1 rounded ${
                        alert.severity_level === 'CRITICAL' ? 'bg-danger text-white' :
                        alert.severity_level === 'HIGH' ? 'bg-warning text-black' :
                        'bg-blue-500/20 text-blue-400'
                      }`}>
                        {alert.severity_level} ({alert.severity_score.toFixed(0)})
                      </span>
                      <span className="text-xs text-gray-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(alert.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                    <h3 className="font-semibold text-sm mb-1">{alert.title}</h3>
                    <p className="text-xs text-gray-400 line-clamp-3">{alert.reason}</p>
                    <div className="mt-3 text-xs flex justify-between items-center">
                      <span className="text-gray-500">ID: {alert.alert_id}</span>
                      <span className={`px-2 py-0.5 rounded-full border ${
                        alert.status === 'ACKNOWLEDGED' ? 'border-success text-success' : 'border-gray-600 text-gray-400'
                      }`}>
                        {alert.status}
                      </span>
                    </div>
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
