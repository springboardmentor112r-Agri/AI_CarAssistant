import { useEffect, useState } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import {
  ArrowLeft,
  Trophy,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Minus,
  FileText,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { api } from "../services/api";
import Navbar from "../components/Navbar";

// ─── TYPES ───────────────────────────────────────────────
interface ContractData {
  doc_id: string;
  filename: string;
  fairness_score: number | null;
  red_flags: string[];
  contract_type: string | null;
  vin: string | null;
  vehicle_make: string | null;
  vehicle_model: string | null;
  vehicle_year: string | null;
  lease_term: string | null;
  loan_term: string | null;
  mileage_allowance: string | null;
  apr: string | null;
  monthly_payment: string | null;
  down_payment: string | null;
  loan_amount: string | null;
  residual_value: string | null;
  acquisition_fee: string | null;
  early_termination_fee: string | null;
  mileage_overage_charge: string | null;
  disposition_fee: string | null;
}

interface CompareResult {
  contract1: ContractData;
  contract2: ContractData;
  winners: Record<string, string | null>;
  overall_winner: string | null;
}

// ─── HELPERS ─────────────────────────────────────────────
const scoreColor = (score: number | null) => {
  if (score === null) return "text-gray-400";
  if (score >= 80) return "text-green-400";
  if (score >= 50) return "text-yellow-400";
  return "text-red-400";
};

const scoreRingColor = (score: number | null) => {
  if (score === null) return "#6b7280";
  if (score >= 80) return "#22c55e";
  if (score >= 50) return "#eab308";
  return "#ef4444";
};

const scoreBg = (score: number | null) => {
  if (score === null) return "bg-gray-800";
  if (score >= 80) return "bg-green-900/30 border-green-700/50";
  if (score >= 50) return "bg-yellow-900/30 border-yellow-700/50";
  return "bg-red-900/30 border-red-700/50";
};

function ScoreRing({ score }: { score: number | null }) {
  const r = 36;
  const circ = 2 * Math.PI * r;
  const pct = score !== null ? score / 100 : 0;
  const dash = pct * circ;
  const color = scoreRingColor(score);

  return (
    <div className="relative w-24 h-24 flex items-center justify-center">
      <svg className="absolute w-24 h-24 -rotate-90">
        <circle
          cx="48"
          cy="48"
          r={r}
          fill="none"
          stroke="#1f2937"
          strokeWidth="8"
        />
        <circle
          cx="48"
          cy="48"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
          style={{ transition: "stroke-dasharray 1s ease" }}
        />
      </svg>
      <div className="relative text-center">
        <div className={`text-2xl font-bold ${scoreColor(score)}`}>
          {score !== null ? Math.round(score) : "N/A"}
        </div>
        <div className="text-xs text-gray-500">/100</div>
      </div>
    </div>
  );
}

function WinnerBadge({ isWinner }: { isWinner: boolean | null }) {
  if (isWinner === null) return <Minus className="w-4 h-4 text-gray-500" />;
  if (isWinner) return <TrendingDown className="w-4 h-4 text-green-400" />;
  return <TrendingUp className="w-4 h-4 text-red-400 opacity-40" />;
}

// ─── MAIN COMPONENT ──────────────────────────────────────
export default function ComparisonPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const doc1 = searchParams.get("doc1") || "";
  const doc2 = searchParams.get("doc2") || "";

  const [result, setResult] = useState<CompareResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!doc1 || !doc2) {
      setError("Two contracts required for comparison.");
      setIsLoading(false);
      return;
    }

    const fetchComparison = async () => {
      try {
        const data = await api.compare.twoContracts(doc1, doc2);
        setResult(data);
      } catch (err: any) {
        setError(err?.response?.data?.detail || "Failed to load comparison.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchComparison();
  }, [doc1, doc2]);

  if (isLoading)
    return (
      <div className="min-h-screen bg-gray-950 flex flex-col">
        <Navbar />
        <div className="flex-1 flex flex-col items-center justify-center gap-4">
          <div className="w-10 h-10 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
          <p className="text-gray-400 text-sm">Comparing contracts...</p>
        </div>
      </div>
    );

  if (error || !result)
    return (
      <div className="min-h-screen bg-gray-950 flex flex-col">
        <Navbar />
        <div className="flex-1 flex flex-col items-center justify-center gap-4 px-4">
          <XCircle className="w-12 h-12 text-red-500" />
          <p className="text-white font-semibold text-lg">Comparison Failed</p>
          <p className="text-gray-400 text-sm text-center">{error}</p>
          <button
            onClick={() => navigate("/dashboard")}
            className="mt-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );

  const { contract1, contract2, winners, overall_winner } = result;

  const getWinnerFor = (field: string, idx: 1 | 2) => {
    const w = winners[field];
    if (!w || w === "tie") return null;
    return w === `contract${idx}`;
  };

  const overallDoc =
    overall_winner === "contract1"
      ? contract1
      : overall_winner === "contract2"
        ? contract2
        : null;

  const financialRows = [
    { label: "APR", field: "apr" },
    { label: "Monthly Payment", field: "monthly_payment" },
    { label: "Down Payment", field: "down_payment" },
    { label: "Loan Amount", field: "loan_amount" },
    { label: "Residual Value", field: "residual_value" },
    { label: "Acquisition Fee", field: "acquisition_fee" },
    { label: "Early Termination Fee", field: "early_termination_fee" },
    { label: "Mileage Overage", field: "mileage_overage_charge" },
    { label: "Disposition Fee", field: "disposition_fee" },
  ];

  const infoRows: {
    label: string;
    field?: string;
    value1?: string | null;
    value2?: string | null;
  }[] = [
    { label: "Contract Type", field: "contract_type" },
    {
      label: "Vehicle",
      value1:
        [
          contract1.vehicle_year,
          contract1.vehicle_make,
          contract1.vehicle_model,
        ]
          .filter(Boolean)
          .join(" ") || null,
      value2:
        [
          contract2.vehicle_year,
          contract2.vehicle_make,
          contract2.vehicle_model,
        ]
          .filter(Boolean)
          .join(" ") || null,
    },
    { label: "VIN", field: "vin" },
    { label: "Lease Term", field: "lease_term" },
    { label: "Loan Term", field: "loan_term" },
    { label: "Mileage Allowance", field: "mileage_allowance" },
  ];

  const val = (doc: ContractData, field: string) => (doc as any)[field] ?? null;

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />

      <div className="max-w-6xl mx-auto px-4 py-8">
        <button
          onClick={() => navigate("/dashboard")}
          className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors mb-6 text-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </button>

        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white">Contract Comparison</h1>
          <p className="text-gray-400 text-sm mt-1">
            Side by side analysis of your contracts
          </p>
        </div>

        {/* Overall Winner Banner */}
        {overall_winner && (
          <div
            className={`rounded-2xl border p-5 mb-8 flex items-center gap-4 ${
              overall_winner === "tie"
                ? "bg-gray-800/50 border-gray-700"
                : "bg-blue-900/30 border-blue-700/50"
            }`}
          >
            <div className="p-3 bg-yellow-500/10 rounded-xl">
              <Trophy className="w-6 h-6 text-yellow-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400 font-medium">
                Overall Winner
              </p>
              {overall_winner === "tie" ? (
                <p className="text-white font-bold text-lg">
                  It&apos;s a tie — both contracts are equal
                </p>
              ) : (
                <p className="text-white font-bold text-lg">
                  {overallDoc?.filename}
                  <span className="ml-2 text-sm font-normal text-gray-400">
                    ({Math.round(overallDoc?.fairness_score ?? 0)}/100 fairness
                    score)
                  </span>
                </p>
              )}
            </div>
          </div>
        )}

        {/* Header Row — contract names + scores */}
        <div className="grid grid-cols-[200px_1fr_1fr] gap-4 mb-2">
          <div />
          {[contract1, contract2].map((doc, i) => (
            <div
              key={i}
              className="bg-gray-900 border border-gray-800 rounded-2xl p-5 text-center"
            >
              <div className="flex items-center justify-center gap-2 mb-4">
                <FileText className="w-4 h-4 text-blue-400 flex-shrink-0" />
                <p
                  className="text-sm font-semibold text-white truncate max-w-[180px]"
                  title={doc.filename}
                >
                  {doc.filename}
                </p>
              </div>

              <div className="flex justify-center mb-3">
                <ScoreRing score={doc.fairness_score} />
              </div>

              <div
                className={`inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1 rounded-full border ${scoreBg(doc.fairness_score)}`}
              >
                <span className={scoreColor(doc.fairness_score)}>
                  {doc.fairness_score !== null
                    ? doc.fairness_score >= 80
                      ? "✓ Fair Contract"
                      : doc.fairness_score >= 50
                        ? "⚠ Some Concerns"
                        : "⚠ Serious Issues"
                    : "Not Scored"}
                </span>
              </div>

              {overall_winner === `contract${i + 1}` && (
                <div className="mt-3 flex items-center justify-center gap-1.5 text-xs text-yellow-400 font-medium">
                  <Trophy className="w-3.5 h-3.5" />
                  Better Deal
                </div>
              )}

              <div className="mt-4 flex gap-2 justify-center">
                <Link
                  to={`/documents/${doc.doc_id}/review`}
                  className="text-xs px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 transition-colors"
                >
                  View Contract
                </Link>
                <Link
                  to={`/chat/${doc.doc_id}`}
                  className="text-xs px-3 py-1.5 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 transition-colors"
                >
                  Negotiate
                </Link>
              </div>
            </div>
          ))}
        </div>

        {/* Red Flags Section */}
        <div className="grid grid-cols-[200px_1fr_1fr] gap-4 mb-4">
          <div className="flex items-center">
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Red Flags
            </span>
          </div>
          {[contract1, contract2].map((doc, i) => (
            <div
              key={i}
              className={`rounded-xl border p-4 ${
                doc.red_flags.length === 0
                  ? "bg-green-900/20 border-green-800/40"
                  : "bg-red-900/20 border-red-800/40"
              }`}
            >
              {doc.red_flags.length === 0 ? (
                <div className="flex items-center gap-2 text-green-400 text-sm">
                  <CheckCircle className="w-4 h-4 flex-shrink-0" />
                  No red flags found
                </div>
              ) : (
                <div className="space-y-1.5">
                  <div className="flex items-center gap-1.5 text-red-400 text-xs font-semibold mb-2">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    {doc.red_flags.length} issue
                    {doc.red_flags.length > 1 ? "s" : ""} found
                  </div>
                  {doc.red_flags.map((flag, j) => (
                    <div
                      key={j}
                      className="flex items-start gap-1.5 text-xs text-red-300"
                    >
                      <span className="text-red-500 mt-0.5 flex-shrink-0">
                        •
                      </span>
                      {flag}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Financial Terms Table */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden mb-4">
          <div className="px-5 py-3 border-b border-gray-800 bg-gray-800/50">
            <h2 className="text-sm font-semibold text-white">
              Financial Terms
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              ↓ Green arrow = better (lower cost)
            </p>
          </div>

          {financialRows.map((row, idx) => {
            const v1 = val(contract1, row.field);
            const v2 = val(contract2, row.field);
            const w1 = getWinnerFor(row.field, 1);
            const w2 = getWinnerFor(row.field, 2);
            const isTie = winners[row.field] === "tie";

            return (
              <div
                key={idx}
                className={`grid grid-cols-[200px_1fr_1fr] ${
                  idx % 2 === 0 ? "bg-transparent" : "bg-gray-800/20"
                }`}
              >
                <div className="px-5 py-3 flex items-center">
                  <span className="text-xs font-medium text-gray-400">
                    {row.label}
                  </span>
                </div>
                <div
                  className={`px-5 py-3 flex items-center justify-between border-l border-gray-800 ${w1 ? "bg-green-900/10" : ""}`}
                >
                  <span
                    className={`text-sm font-medium ${v1 ? "text-white" : "text-gray-600"}`}
                  >
                    {v1 || "—"}
                  </span>
                  {v1 && v2 && (
                    <div className="ml-2">
                      {isTie ? (
                        <Minus className="w-4 h-4 text-gray-500" />
                      ) : (
                        <WinnerBadge isWinner={w1} />
                      )}
                    </div>
                  )}
                </div>
                <div
                  className={`px-5 py-3 flex items-center justify-between border-l border-gray-800 ${w2 ? "bg-green-900/10" : ""}`}
                >
                  <span
                    className={`text-sm font-medium ${v2 ? "text-white" : "text-gray-600"}`}
                  >
                    {v2 || "—"}
                  </span>
                  {v1 && v2 && (
                    <div className="ml-2">
                      {isTie ? (
                        <Minus className="w-4 h-4 text-gray-500" />
                      ) : (
                        <WinnerBadge isWinner={w2} />
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Contract Info Table */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden mb-8">
          <div className="px-5 py-3 border-b border-gray-800 bg-gray-800/50">
            <h2 className="text-sm font-semibold text-white">
              Contract Details
            </h2>
          </div>

          {infoRows.map((row, idx) => {
            const v1 =
              row.value1 !== undefined
                ? row.value1
                : val(contract1, row.field!);
            const v2 =
              row.value2 !== undefined
                ? row.value2
                : val(contract2, row.field!);

            return (
              <div
                key={idx}
                className={`grid grid-cols-[200px_1fr_1fr] ${
                  idx % 2 === 0 ? "bg-transparent" : "bg-gray-800/20"
                }`}
              >
                <div className="px-5 py-3 flex items-center">
                  <span className="text-xs font-medium text-gray-400">
                    {row.label}
                  </span>
                </div>
                <div className="px-5 py-3 border-l border-gray-800">
                  <span
                    className={`text-sm ${v1 ? "text-white" : "text-gray-600"}`}
                  >
                    {v1 || "—"}
                  </span>
                </div>
                <div className="px-5 py-3 border-l border-gray-800">
                  <span
                    className={`text-sm ${v2 ? "text-white" : "text-gray-600"}`}
                  >
                    {v2 || "—"}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
