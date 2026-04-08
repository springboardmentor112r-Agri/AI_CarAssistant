"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  UploadCloud, MessageSquare, CarFront, TrendingUp,
  LogOut, LayoutDashboard, ChevronRight, User, Car
} from "lucide-react";
import { getUser, logout } from "@/lib/auth";
import { ContractUpload } from "@/components/ContractUpload";
import { PriceEstimation } from "@/components/PriceEstimation";

type Section = "upload" | "price";

const navItems: { key: Section; icon: React.ElementType; label: string; description: string }[] = [
  { key: "upload",  icon: UploadCloud,    label: "Contract Review",      description: "Upload & analyze your lease/loan contract" },
  { key: "price",   icon: TrendingUp,     label: "Price Estimator",      description: "Get fair market value for any vehicle" },
];

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ name: string; email: string } | null>(null);
  const [active, setActive] = useState<Section>("upload");

  useEffect(() => {
    const u = getUser();
    if (!u) { router.push("/login"); return; }
    setUser(u);
  }, [router]);

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  if (!user) return null;

  const initials = user.name.split(" ").map(n => n[0]).join("").slice(0, 2).toUpperCase();

  return (
    <div className="min-h-screen bg-dark-gradient flex pt-16">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 border-r border-white/10 glass flex flex-col fixed top-16 bottom-0 left-0 z-40">
        {/* User Profile */}
        <div className="p-5 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-indigo-500/30">
              {initials}
            </div>
            <div className="min-w-0">
              <p className="text-white font-semibold text-sm truncate">{user.name}</p>
              <p className="text-slate-500 text-xs truncate">{user.email}</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          <p className="text-xs font-semibold text-slate-600 uppercase tracking-wider px-3 mb-2 mt-2">Features</p>
          {navItems.map(({ key, icon: Icon, label, description }) => {
            const isActive = active === key;
            return (
              <button
                key={key}
                onClick={() => setActive(key)}
                className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl text-left transition-all duration-200 group ${isActive ? "bg-indigo-600/20 border border-indigo-500/30 text-white" : "text-slate-400 hover:text-white hover:bg-white/5"}`}
              >
                <div className={`p-1.5 rounded-lg transition-all duration-200 ${isActive ? "bg-indigo-500/30" : "bg-white/5 group-hover:bg-white/10"}`}>
                  <Icon className={`w-4 h-4 ${isActive ? "text-indigo-400" : ""}`} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium truncate">{label}</p>
                  <p className="text-xs text-slate-500 truncate leading-tight">{description}</p>
                </div>
                {isActive && <ChevronRight className="w-3.5 h-3.5 text-indigo-400 shrink-0" />}
              </button>
            );
          })}

          {/* About the Project */}
          <div className="mt-4">
            <p className="text-xs font-semibold text-slate-600 uppercase tracking-wider px-3 mb-2">Project Info</p>
            <div className="bg-white/3 border border-white/8 rounded-xl p-4 space-y-2 mx-1">
              <p className="text-xs text-slate-400 font-semibold">Car Lease/Loan AI Assistant</p>
              <ul className="space-y-1">
                {["SLA Extraction", "VIN Lookup", "Negotiation AI", "Price Estimation", "Fairness Scoring"].map(f => (
                  <li key={f} className="text-xs text-slate-500 flex items-center gap-1.5">
                    <span className="w-1 h-1 rounded-full bg-indigo-500" />
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </nav>

        {/* Logout */}
        <div className="p-3 border-t border-white/10">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-3 py-2.5 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-xl text-sm transition-all duration-200"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64 p-8 overflow-y-auto">
        {/* Top Welcome Banner */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-slate-400 text-sm mb-2">
            <LayoutDashboard className="w-4 h-4" />
            <span>Dashboard</span>
            <ChevronRight className="w-3 h-3" />
            <span className="text-white">{navItems.find(n => n.key === active)?.label}</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white">
            Welcome back,{" "}
            <span className="gradient-text-blue">{user.name.split(" ")[0]}</span> 👋
          </h1>
          <p className="text-slate-400 mt-1">
            {active === "upload"
              ? "Upload your car contract and let AI extract, score, and coach you."
              : active === "price"
              ? "Get a fair market price estimate for any vehicle make and model."
              : "Standalone negotiation chat for your contracts."}
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          {[
            { label: "Contracts Analyzed", value: "0", icon: UploadCloud, color: "text-indigo-400", bg: "bg-indigo-500/10" },
            { label: "Red Flags Found", value: "0", icon: Car, color: "text-red-400", bg: "bg-red-500/10" },
            { label: "Avg. Fairness Score", value: "—", icon: TrendingUp, color: "text-green-400", bg: "bg-green-500/10" },
          ].map(({ label, value, icon: Icon, color, bg }) => (
            <div key={label} className="glass border border-white/10 rounded-2xl p-5">
              <div className={`w-9 h-9 rounded-xl ${bg} flex items-center justify-center mb-3`}>
                <Icon className={`w-4 h-4 ${color}`} />
              </div>
              <p className={`text-2xl font-extrabold ${color}`}>{value}</p>
              <p className="text-xs text-slate-500 mt-1">{label}</p>
            </div>
          ))}
        </div>

        {/* Feature Panel */}
        <div className="glass border border-white/10 rounded-3xl p-7">
          {active === "upload"  && <ContractUpload />}
          {active === "price"   && <PriceEstimation />}
        </div>
      </main>
    </div>
  );
}
