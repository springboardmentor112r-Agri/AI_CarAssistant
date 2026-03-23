import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Zap,
  Hash,
  DollarSign,
  Clock,
  CheckCircle,
  XCircle,
  RefreshCw,
  BarChart2,
  ChevronRight,
  AlertCircle,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useAuthStore } from "../store/authStore";
import { api } from "../services/api";
import Navbar from "../components/Navbar";

interface AdminStats {
  overall: {
    total_calls: number;
    total_tokens: number;
    total_cost_usd: number;
    avg_response_ms: number;
    total_errors: number;
    success_rate: number;
  };
  daily: Array<{
    date: string;
    calls: number;
    tokens: number;
    cost: number;
  }>;
  modules: Array<{
    module: string;
    calls: number;
    tokens: number;
    avg_ms: number;
    errors: number;
  }>;
}

interface LLMLog {
  log_id: string;
  timestamp: string;
  module: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  response_time_ms: number;
  success: boolean;
  error_message: string | null;
  cost_usd: number;
  user_id: string | null;
  doc_id: string | null;
}

const AdminPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [logs, setLogs] = useState<LLMLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "logs">("overview");
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const isAdmin = user?.email === import.meta.env.VITE_ADMIN_EMAIL;

  const fetchData = useCallback(async () => {
    if (!isAdmin) return;
    setIsLoading(true);
    try {
      const [statsRes, logsRes] = await Promise.all([
        api.admin.getStats(),
        api.admin.getLogs(50),
      ]);
      setStats(statsRes);
      setLogs(logsRes);
      setLastUpdated(new Date());
    } catch (err) {
      console.error("Failed to fetch admin data", err);
    } finally {
      setIsLoading(false);
    }
  }, [isAdmin]);

  useEffect(() => {
    if (user && !isAdmin) {
      navigate("/dashboard");
      return;
    }
    fetchData();
  }, [user, isAdmin, navigate, fetchData]);

  if (!isAdmin) return null;

  const getModuleColor = (module: string) => {
    switch (module) {
      case "chat":
        return "bg-blue-500/20 text-blue-400 border-blue-500/30";
      case "sla_extraction":
        return "bg-purple-500/20 text-purple-400 border-purple-500/30";
      case "vin_pricing":
        return "bg-green-500/20 text-green-400 border-green-500/30";
      default:
        return "bg-gray-500/20 text-gray-400 border-gray-500/30";
    }
  };

  const formatRelativeTime = (isoString: string) => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);

    if (diffSec < 60) return "Just now";
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHour < 24) return `${diffHour}h ago`;
    return `${diffDay}d ago`;
  };

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white">
      <Navbar />

      {/* Header */}
      <header className="px-6 py-8 border-b border-white/5 bg-white/[0.02]">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
              LLM Monitor
            </h1>
            <p className="text-gray-400 mt-1 flex items-center gap-2">
              <BarChart2 className="w-4 h-4" />
              Admin Dashboard & Infrastructure Health
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <p className="text-xs text-gray-500 uppercase tracking-wider">
                Last updated
              </p>
              <p className="text-sm font-medium text-gray-300">
                {lastUpdated.toLocaleTimeString()}
              </p>
            </div>
            <button
              onClick={fetchData}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 transition-colors rounded-lg font-medium text-sm shadow-lg shadow-blue-500/20"
            >
              <RefreshCw
                className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`}
              />
              Refresh
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-8">
        {/* Tabs */}
        <div className="px-6 mb-8">
          <div className="flex gap-1 bg-white/5 p-1 rounded-xl w-fit">
            <button
              onClick={() => setActiveTab("overview")}
              className={`px-6 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === "overview"
                  ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                  : "text-gray-400 hover:text-gray-200 hover:bg-white/5"
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab("logs")}
              className={`px-6 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === "logs"
                  ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                  : "text-gray-400 hover:text-gray-200 hover:bg-white/5"
              }`}
            >
              Recent Logs
            </button>
          </div>
        </div>

        {activeTab === "overview" ? (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Stat Cards */}
            <div className="px-6 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <StatCard
                icon={<Zap className="text-blue-400" />}
                value={stats?.overall.total_calls || 0}
                label="Total LLM Calls"
              />
              <StatCard
                icon={<Hash className="text-purple-400" />}
                value={(stats?.overall.total_tokens || 0).toLocaleString()}
                label="Tokens Used"
              />
              <StatCard
                icon={<DollarSign className="text-green-400" />}
                value={`$${(stats?.overall.total_cost_usd || 0).toFixed(4)}`}
                label="Est. Cost (USD)"
              />
              <StatCard
                icon={<Clock className="text-yellow-400" />}
                value={`${stats?.overall.avg_response_ms || 0}ms`}
                label="Avg Response"
              />
              <StatCard
                icon={
                  <CheckCircle
                    className={
                      (stats?.overall.success_rate || 0) > 95
                        ? "text-green-400"
                        : (stats?.overall.success_rate || 0) > 80
                          ? "text-yellow-400"
                          : "text-red-400"
                    }
                  />
                }
                value={`${stats?.overall.success_rate || 0}%`}
                label="Success Rate"
              />
              <StatCard
                icon={
                  <XCircle
                    className={
                      (stats?.overall.total_errors || 0) > 0
                        ? "text-red-400"
                        : "text-gray-500"
                    }
                  />
                }
                value={stats?.overall.total_errors || 0}
                label="Total Errors"
              />
            </div>

            {/* Daily Chart */}
            <div className="px-6">
              <div className="bg-white/[0.03] border border-white/5 rounded-2xl p-6">
                <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                  <BarChart2 className="w-5 h-5 text-blue-400" />
                  LLM Calls — Last 7 Days
                </h3>
                <div className="h-64 w-full">
                  {stats && (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={stats.daily}>
                        <CartesianGrid
                          strokeDasharray="3 3"
                          stroke="#ffffff0a"
                          vertical={false}
                        />
                        <XAxis
                          dataKey="date"
                          stroke="#666"
                          fontSize={12}
                          tickFormatter={(str) => {
                            const d = new Date(str);
                            return d.toLocaleDateString("en-US", {
                              month: "short",
                              day: "numeric",
                            });
                          }}
                        />
                        <YAxis stroke="#666" fontSize={12} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "#1a1a1c",
                            border: "1px solid #ffffff14",
                            borderRadius: "8px",
                          }}
                          cursor={{ fill: "#ffffff05" }}
                        />
                        <Bar
                          dataKey="calls"
                          fill="#3b82f6"
                          radius={[4, 4, 0, 0]}
                          barSize={40}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </div>
            </div>

            {/* Module Breakdown */}
            <div className="px-6">
              <div className="bg-white/[0.03] border border-white/5 rounded-2xl p-6">
                <h3 className="text-lg font-semibold mb-6">Usage by Module</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {stats?.modules.map((m) => (
                    <div
                      key={m.module}
                      className="bg-white/[0.02] border border-white/5 rounded-xl p-5 hover:border-blue-500/20 transition-colors"
                    >
                      <div className="flex justify-between items-start mb-4">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider border ${getModuleColor(m.module)}`}
                        >
                          {m.module.replace("_", " ")}
                        </span>
                        {m.errors > 0 && (
                          <span className="text-red-400 text-xs flex items-center gap-1 font-medium">
                            <AlertCircle className="w-3 h-3" /> {m.errors}{" "}
                            errors
                          </span>
                        )}
                      </div>

                      <div className="space-y-3">
                        <div className="flex justify-between items-baseline">
                          <span className="text-gray-500 text-sm">Calls</span>
                          <span className="text-lg font-semibold text-gray-200">
                            {m.calls}
                          </span>
                        </div>
                        <div className="flex justify-between items-baseline">
                          <span className="text-gray-500 text-sm">Tokens</span>
                          <span className="text-sm font-medium text-gray-300">
                            {m.tokens.toLocaleString()}
                          </span>
                        </div>
                        <div className="flex justify-between items-baseline">
                          <span className="text-gray-500 text-sm">
                            Avg Resp
                          </span>
                          <span className="text-sm font-medium text-gray-300">
                            {m.avg_ms}ms
                          </span>
                        </div>
                      </div>

                      <div className="mt-4 pt-4 border-t border-white/5">
                        <div className="flex justify-between text-[10px] text-gray-500 uppercase tracking-widest mb-1.5">
                          <span>Volume Share</span>
                          <span>
                            {Math.round(
                              (m.calls / (stats.overall.total_calls || 1)) *
                                100,
                            )}
                            %
                          </span>
                        </div>
                        <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-600 rounded-full"
                            style={{
                              width: `${(m.calls / (stats.overall.total_calls || 1)) * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="px-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="bg-white/[0.03] border border-white/5 rounded-2xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-white/[0.05] border-b border-white/5">
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-gray-400">
                        Time
                      </th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-gray-400">
                        Module
                      </th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-gray-400">
                        Tokens
                      </th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-gray-400">
                        Resp
                      </th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-gray-400">
                        Cost
                      </th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-gray-400">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {logs.map((log) => (
                      <tr
                        key={log.log_id}
                        className={`hover:bg-white/[0.02] transition-colors ${!log.success ? "bg-red-900/10" : ""}`}
                      >
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex flex-col">
                            <span className="text-sm text-gray-200">
                              {formatRelativeTime(log.timestamp)}
                            </span>
                            <span className="text-[10px] text-gray-600">
                              {new Date(log.timestamp).toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${getModuleColor(log.module)}`}
                          >
                            {log.module.replace("_", " ")}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-1.5">
                            <span className="text-sm text-gray-300 font-medium">
                              {log.total_tokens}
                            </span>
                            <span className="text-[10px] text-gray-600">
                              ({log.prompt_tokens}+{log.completion_tokens})
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                          {log.response_time_ms}ms
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">
                          ${log.cost_usd.toFixed(5)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {log.success ? (
                            <span className="flex items-center gap-1 text-green-400 text-xs font-medium bg-green-400/10 px-2 py-0.5 rounded-full border border-green-400/20">
                              <CheckCircle className="w-3 h-3" /> Success
                            </span>
                          ) : (
                            <div className="group relative w-fit">
                              <span className="flex items-center gap-1 text-red-100 text-xs font-medium bg-red-600/20 px-2 py-0.5 rounded-full border border-red-500/30">
                                <XCircle className="w-3 h-3" /> Failed
                              </span>
                              {log.error_message && (
                                <div className="absolute left-0 top-full mt-2 hidden group-hover:block z-50 w-64 p-3 bg-gray-900 border border-white/10 rounded-lg shadow-2xl text-[11px] text-red-200 break-words backdrop-blur-md">
                                  {log.error_message}
                                </div>
                              )}
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="p-4 bg-white/[0.02] border-t border-white/5 flex justify-center">
                <button className="text-sm text-blue-400 hover:text-blue-300 font-medium transition-colors flex items-center gap-1">
                  Load More <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

const StatCard: React.FC<{
  icon: React.ReactNode;
  value: string | number;
  label: string;
}> = ({ icon, value, label }) => (
  <div className="bg-white/[0.03] border border-white/5 rounded-2xl p-4 hover:border-white/10 transition-colors">
    <div className="flex items-center justify-between mb-3">
      <div className="p-2 bg-white/5 rounded-lg">{icon}</div>
    </div>
    <div className="text-xl font-bold text-gray-100 whitespace-nowrap overflow-hidden text-ellipsis">
      {value}
    </div>
    <div className="text-[10px] text-gray-500 uppercase tracking-widest font-medium mt-1">
      {label}
    </div>
  </div>
);

export default AdminPage;
