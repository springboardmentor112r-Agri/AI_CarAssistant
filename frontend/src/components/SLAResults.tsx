"use client";

import { AlertTriangle, CheckCircle2, Info } from "lucide-react";

interface SLAData {
  apr?: number;
  lease_term_months?: number;
  monthly_payment?: number;
  down_payment?: number;
  residual_value?: number;
  mileage_allowance?: number;
  overage_charge_per_mile?: number;
  buyout_price?: number;
  fairness_score?: number;
  red_flags?: string[];
}

interface VehicleData {
  make?: string;
  model?: string;
  year?: number;
  vin?: string;
}

interface ContractResult {
  id: string;
  status: string;
  sla?: SLAData;
  vehicle?: VehicleData;
}

export function SLAResults({ result }: { result: ContractResult }) {
  const sla = result.sla;
  const score = sla?.fairness_score ?? 0;
  const scoreColor =
    score >= 70 ? "text-green-400" : score >= 45 ? "text-yellow-400" : "text-red-400";
  const scoreBg =
    score >= 70 ? "from-green-500/20 to-emerald-500/10" : score >= 45 ? "from-yellow-500/20 to-amber-500/10" : "from-red-500/20 to-rose-500/10";
  const scoreBorder =
    score >= 70 ? "border-green-500/30" : score >= 45 ? "border-yellow-500/30" : "border-red-500/30";
  const scoreLabel =
    score >= 70 ? "Fair Deal ✓" : score >= 45 ? "Review Carefully" : "Poor Deal ⚠";

  const fields = [
    { label: "APR / Interest Rate", value: sla?.apr != null ? `${sla.apr}%` : null },
    { label: "Lease Term", value: sla?.lease_term_months != null ? `${sla.lease_term_months} months` : null },
    { label: "Monthly Payment", value: sla?.monthly_payment != null ? `$${sla.monthly_payment.toLocaleString()}` : null },
    { label: "Down Payment", value: sla?.down_payment != null ? `$${sla.down_payment.toLocaleString()}` : null },
    { label: "Residual Value", value: sla?.residual_value != null ? `$${sla.residual_value.toLocaleString()}` : null },
    { label: "Mileage Allowance", value: sla?.mileage_allowance != null ? `${sla.mileage_allowance.toLocaleString()} mi/yr` : null },
    { label: "Overage Charge", value: sla?.overage_charge_per_mile != null ? `$${sla.overage_charge_per_mile}/mile` : null },
    { label: "Buyout Price", value: sla?.buyout_price != null ? `$${sla.buyout_price.toLocaleString()}` : null },
  ];

  return (
    <div className="space-y-5">
      {/* Vehicle Info Header */}
      {result.vehicle && (
        <div className="bg-white/5 border border-white/10 rounded-2xl p-5 flex items-center gap-4">
          <div className="bg-indigo-500/20 p-3 rounded-xl">
            <CheckCircle2 className="w-6 h-6 text-indigo-400" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">
              {result.vehicle.year} {result.vehicle.make} {result.vehicle.model}
            </h3>
            <p className="text-sm text-slate-400">Extracted from contract Document</p>
          </div>
        </div>
      )}

      {/* Fairness Score */}
      <div className={`relative overflow-hidden rounded-2xl p-6 border ${scoreBorder} bg-gradient-to-br ${scoreBg}`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-400 mb-1">Contract Fairness Score</p>
            <p className={`text-5xl font-extrabold ${scoreColor}`}>{score}<span className="text-2xl text-slate-500">/100</span></p>
            <p className={`text-sm font-semibold mt-1 ${scoreColor}`}>{scoreLabel}</p>
          </div>
          {/* Circular visual */}
          <svg className="w-24 h-24 -rotate-90" viewBox="0 0 36 36">
            <circle cx="18" cy="18" r="15.9" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="3" />
            <circle
              cx="18" cy="18" r="15.9" fill="none"
              stroke={score >= 70 ? "#4ade80" : score >= 45 ? "#facc15" : "#f87171"}
              strokeWidth="3"
              strokeDasharray={`${score} ${100 - score}`}
              strokeLinecap="round"
              className="transition-all duration-1000"
            />
          </svg>
        </div>
      </div>

      {/* SLA Fields Grid */}
      <div className="grid grid-cols-2 gap-3">
        {fields.map(({ label, value }) => (
          <div key={label} className="bg-white/5 border border-white/10 rounded-xl p-4">
            <p className="text-xs text-slate-500 mb-1">{label}</p>
            <p className={`text-base font-bold ${value ? "text-white" : "text-slate-600"}`}>
              {value ?? "Not Found"}
            </p>
          </div>
        ))}
      </div>

      {/* Red Flags */}
      {sla?.red_flags && sla.red_flags.length > 0 ? (
        <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <h3 className="font-bold text-red-400">Red Flags Detected ({sla.red_flags.length})</h3>
          </div>
          <ul className="space-y-2">
            {sla.red_flags.map((flag, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-red-300">
                <span className="mt-1 w-1.5 h-1.5 rounded-full bg-red-400 shrink-0" />
                {flag}
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <div className="bg-green-500/10 border border-green-500/20 rounded-2xl p-4 flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-green-400 shrink-0" />
          <p className="text-sm text-green-300 font-medium">No red flags detected in this contract.</p>
        </div>
      )}

      {/* Info note */}
      <div className="flex items-start gap-2 text-xs text-slate-500 bg-white/3 rounded-xl p-3 border border-white/5">
        <Info className="w-3.5 h-3.5 mt-0.5 shrink-0" />
        <p>SLA data extracted via AI analysis. Always verify with a licensed automotive finance professional.</p>
      </div>
    </div>
  );
}
