import { useState, useRef, useCallback, useEffect } from "react";
import {
  UploadCloud,
  FileSearch,
  Brain,
  CheckCircle,
  Loader2,
  AlertTriangle,
  XCircle,
  Upload,
  RefreshCw,
} from "lucide-react";
import { api } from "../services/api";

interface DocumentUploadProps {
  onUploadComplete: (doc_id: string) => void;
}

const STEPS = [
  { label: "Upload File", icon: Upload },
  { label: "Extracting content", icon: FileSearch },
  { label: "Analysing contract", icon: Brain },
  { label: "Ready!", icon: CheckCircle },
];

const PROGRESS_MAP: Record<number, number> = {
  1: 15,
  2: 40,
  3: 75,
  4: 100,
};

const ACCEPT =
  ".pdf,.doc,.docx,.xlsx,.xls,.txt,.csv,.jpg,.jpeg,.png,.tiff,.tif,.bmp,.webp,.heic,.html,.rtf,.eml";

// How many consecutive 404s before we give up (doc was deleted server-side)
const MAX_404_COUNT = 2;
// Hard timeout: 5 minutes = 75 polls × 4s
const MAX_POLLS = 75;

export default function DocumentUpload({
  onUploadComplete,
}: DocumentUploadProps) {
  const [step, setStep] = useState<0 | 1 | 2 | 3 | 4>(0);
  const [status, setStatus] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [docId, setDocId] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [, setRetryCount] = useState(0);
  const [isSlaFailed, setIsSlaFailed] = useState(false);
  const [slaProgress, setSlaProgress] = useState<{
    step: number;
    total: number;
    message: string;
  } | null>(null);
  const [analysisElapsed, setAnalysisElapsed] = useState(0);
  const analysisTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollCountRef = useRef(0);
  const notFoundCountRef = useRef(0);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
      if (analysisTimerRef.current) clearInterval(analysisTimerRef.current);
    };
  }, []);

  const startAnalysisTimer = useCallback(() => {
    if (analysisTimerRef.current) return;
    setAnalysisElapsed(0);
    analysisTimerRef.current = setInterval(() => {
      setAnalysisElapsed((prev) => prev + 1);
    }, 1000);
  }, []);

  const stopAnalysisTimer = useCallback(() => {
    if (analysisTimerRef.current) {
      clearInterval(analysisTimerRef.current);
      analysisTimerRef.current = null;
    }
  }, []);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    pollCountRef.current = 0;
    notFoundCountRef.current = 0;
    stopAnalysisTimer();
  }, [stopAnalysisTimer]);

  const handleFatalError = useCallback(
    (msg: string) => {
      stopPolling();
      setStatus("error");
      setErrorMessage(msg);
    },
    [stopPolling],
  );

  const startPolling = useCallback(
    (id: string) => {
      stopPolling();
      pollCountRef.current = 0;
      notFoundCountRef.current = 0;

      pollRef.current = setInterval(async () => {
        // Hard timeout guard
        pollCountRef.current += 1;
        if (pollCountRef.current > MAX_POLLS) {
          handleFatalError(
            "Processing timed out after 5 minutes. Please try uploading again.",
          );
          return;
        }

        try {
          const res = await api.documents.getStatus(id);
          const ps = res.processing_status;

          // Reset 404 counter on any successful response
          notFoundCountRef.current = 0;

          // Track sla_progress from backend
          if (res.sla_progress) {
            setSlaProgress(res.sla_progress);
          }

          if (ps === "processing") {
            setStep(2);
          } else if (ps === "extraction_complete") {
            setStep(3);
            startAnalysisTimer();
          } else if (ps === "ready") {
            setStep(4);
            setSlaProgress({
              step: 100,
              total: 100,
              message: "Analysis complete!",
            });
            stopPolling();
            setStatus("ready");
            setTimeout(() => onUploadComplete(id), 800);
          } else if (ps === "sla_failed") {
            stopPolling();
            setIsSlaFailed(true);
            setErrorMessage(res.error_message || "Contract analysis failed.");
            setRetryCount(res.sla_retry_count || 0);
          } else if (ps === "error") {
            // ← KEY FIX: extraction failed, doc still exists with error status
            handleFatalError(
              res.error_message ||
                "Could not extract text from this file. Please upload a clearer PDF or DOCX.",
            );
          }
          // "pending" — still queued, keep polling silently
        } catch (err: unknown) {
          const status = (err as { response?: { status?: number } })?.response
            ?.status;

          if (status === 404) {
            // Doc not found — could be deleted or never created
            notFoundCountRef.current += 1;
            if (notFoundCountRef.current >= MAX_404_COUNT) {
              handleFatalError(
                "This document no longer exists on the server. Please upload again.",
              );
            }
            // else: give it one more poll in case of race condition
          }
          // Other errors (network, 500) — keep polling silently, don't give up yet
        }
      }, 4000);
    },
    [onUploadComplete, stopPolling, handleFatalError, startAnalysisTimer],
  );

  const handleFileSelect = async (file: File) => {
    setStep(1);
    setErrorMessage(null);
    setIsSlaFailed(false);
    setStatus(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      const result = await api.documents.upload(formData);
      setDocId(result.doc_id);
      setStep(2);
      startPolling(result.doc_id);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Upload failed. Please check the file and try again.";
      setErrorMessage(msg);
      setStatus("error");
      setStep(0);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileSelect(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  };

  const handleRetry = async () => {
    if (!docId) return;
    setIsSlaFailed(false);
    setErrorMessage(null);
    try {
      await api.documents.retrySLA(docId);
      setStep(3);
      startPolling(docId);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Retry failed. Please try uploading again.";
      setErrorMessage(msg);
      setIsSlaFailed(true);
    }
  };

  const resetAll = () => {
    stopPolling();
    setStep(0);
    setDocId(null);
    setIsSlaFailed(false);
    setErrorMessage(null);
    setStatus(null);
    setRetryCount(0);
    setSlaProgress(null);
    setAnalysisElapsed(0);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // Compute progress: use sla_progress when in AI analysis step, else use step map
  const computedProgress = (() => {
    if (step === 3 && slaProgress) {
      // During AI analysis, map sla_progress into the 50-95% range (step 3 covers 40-100%)
      const slaPercent =
        slaProgress.total > 0
          ? (slaProgress.step / slaProgress.total) * 100
          : 0;
      // Map 0-100% of sla to 50-95% of total bar
      return Math.round(50 + (slaPercent / 100) * 45);
    }
    return PROGRESS_MAP[step] || 0;
  })();
  const progress = computedProgress;
  const isReady = step === 4;

  const formatElapsed = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
  };

  // ─── DROPZONE (step 0) ────────────────────────────────────────────────────
  if (step === 0 && !isSlaFailed && status !== "error") {
    return (
      <div className="flex flex-col gap-6">
        <div
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={`
            border-2 border-dashed rounded-xl p-10 text-center cursor-pointer
            transition-all duration-200
            ${
              isDragging
                ? "border-blue-400 bg-blue-500/10"
                : "border-gray-600 bg-gray-800/50 hover:border-blue-500 hover:bg-blue-500/5"
            }
          `}
        >
          <UploadCloud size={48} className="mx-auto mb-3 text-blue-400" />
          <p className="text-gray-300 text-sm">
            Drop your contract here or click to browse
          </p>
          <p className="text-gray-500 text-xs mt-2">
            Supports PDF, Word, Excel, images and more. Max 50MB.
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPT}
            onChange={handleInputChange}
            className="hidden"
          />
        </div>

        {errorMessage && (
          <div className="flex items-start gap-3 bg-red-900/20 border border-red-500/50 rounded-xl p-5">
            <XCircle size={20} className="text-red-400 shrink-0 mt-0.5" />
            <div>
              <p className="text-red-300 font-semibold">Upload Failed</p>
              <p className="text-red-400 text-sm mt-1">{errorMessage}</p>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ─── SLA FAILED UI ────────────────────────────────────────────────────────
  if (isSlaFailed) {
    return (
      <div className="flex flex-col gap-4">
        <div className="bg-amber-900/20 border border-amber-500/50 rounded-xl p-5">
          <div className="flex items-start gap-3">
            <AlertTriangle
              size={24}
              className="text-amber-400 shrink-0 mt-0.5"
            />
            <div>
              <p className="text-amber-300 font-semibold">
                Contract Analysis Incomplete
              </p>
              <p className="text-amber-400/80 text-sm mt-1">{errorMessage}</p>
            </div>
          </div>
          <div className="flex gap-3 mt-4">
            <button
              onClick={handleRetry}
              className="flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-black font-semibold
                         rounded-lg px-5 py-2.5 text-sm transition-colors"
            >
              <RefreshCw size={14} />
              Retry Analysis
            </button>
            <button
              onClick={resetAll}
              className="bg-white/5 hover:bg-white/10 text-gray-300 border border-gray-600
                         font-semibold rounded-lg px-5 py-2.5 text-sm transition-colors"
            >
              Upload Different File
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ─── ERROR UI ─────────────────────────────────────────────────────────────
  if (status === "error") {
    return (
      <div className="flex flex-col gap-4">
        <div className="bg-red-900/20 border border-red-500/50 rounded-xl p-5">
          <div className="flex items-start gap-3">
            <XCircle size={24} className="text-red-400 shrink-0 mt-0.5" />
            <div>
              <p className="text-red-300 font-semibold">Processing Failed</p>
              <p className="text-red-400/80 text-sm mt-1">{errorMessage}</p>
            </div>
          </div>
        </div>

        {/* Tips for the user */}
        <div className="bg-blue-900/20 border border-blue-500/30 rounded-xl p-4">
          <p className="text-blue-300 text-sm font-semibold mb-2">
            💡 Tips for a successful upload:
          </p>
          <ul className="text-blue-400/80 text-xs space-y-1 list-disc list-inside">
            <li>
              Use a native PDF (exported from Word/Google Docs) — best results
            </li>
            <li>For scanned images, ensure good lighting and no rotation</li>
            <li>DOCX and TXT files always work reliably</li>
            <li>Avoid photos taken at an angle or in low light</li>
          </ul>
        </div>

        <button
          onClick={resetAll}
          className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700
                     text-white font-semibold rounded-lg px-5 py-2.5 text-sm transition-colors"
        >
          <Upload size={14} />
          Upload a Different File
        </button>
      </div>
    );
  }

  // ─── STEPPER UI (steps 1–4) ───────────────────────────────────────────────
  return (
    <div className="flex flex-col gap-4">
      <div className="bg-gray-800/50 rounded-xl p-5">
        <div className="flex flex-col gap-3">
          {STEPS.map((s, idx) => {
            const stepNum = idx + 1;
            const isDone = step > stepNum;
            const isActive = step === stepNum;

            return (
              <div key={idx} className="flex items-center gap-3 py-1">
                {isDone ? (
                  <div className="w-7 h-7 rounded-full bg-green-500/20 flex items-center justify-center">
                    <CheckCircle size={16} className="text-green-400" />
                  </div>
                ) : isActive ? (
                  <div className="w-7 h-7 rounded-full bg-blue-500/20 flex items-center justify-center">
                    <span className="text-blue-400 text-xs font-bold">
                      {stepNum}
                    </span>
                  </div>
                ) : (
                  <div className="w-7 h-7 rounded-full border-2 border-gray-600 flex items-center justify-center">
                    <span className="text-gray-600 text-xs font-bold">
                      {stepNum}
                    </span>
                  </div>
                )}

                <span
                  className={`text-sm font-medium ${
                    isDone
                      ? "text-gray-400"
                      : isActive
                        ? "text-blue-400"
                        : "text-gray-600"
                  }`}
                >
                  {s.label}
                </span>

                {isActive && step < 4 && (
                  <Loader2
                    size={16}
                    className="text-blue-400 animate-spin ml-auto"
                  />
                )}
              </div>
            );
          })}
        </div>

        {/* ── AI Analysis detailed progress (step 3) ── */}
        {step === 3 && (
          <div className="mt-4 bg-gray-900/60 border border-gray-700/50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="relative flex items-center justify-center w-5 h-5">
                  <div className="absolute inset-0 rounded-full border-2 border-blue-500/30 border-t-blue-400 animate-spin" />
                  <Brain size={10} className="text-blue-400" />
                </div>
                <span className="text-xs font-semibold text-blue-300 uppercase tracking-wider">
                  AI Analysis
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500 font-mono">
                  {formatElapsed(analysisElapsed)}
                </span>
                <span className="text-sm font-bold text-blue-400 font-mono">
                  {progress}%
                </span>
              </div>
            </div>

            {/* Progress bar with glow */}
            <div className="h-2 w-full bg-gray-700/60 rounded-full overflow-hidden border border-gray-600/40">
              <div
                className={`h-full rounded-full transition-all duration-700 ease-out relative ${
                  slaProgress && slaProgress.step === slaProgress.total && slaProgress.total > 0
                    ? "bg-green-500"
                    : "bg-gradient-to-r from-blue-600 via-blue-500 to-indigo-400"
                }`}
                style={{ width: `${Math.max(5, progress)}%` }}
              >
                {/* Animated shimmer effect on active bar */}
                {progress < 95 && (
                  <div
                    className="absolute inset-0 overflow-hidden rounded-full"
                    style={{
                      background:
                        "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.15) 50%, transparent 100%)",
                      backgroundSize: "200% 100%",
                      animation: "shimmer 1.5s infinite linear",
                    }}
                  />
                )}
              </div>
            </div>

            {/* Progress message from backend */}
            <div className="mt-2 flex items-center justify-between">
              <p className="text-xs text-gray-400 truncate">
                {slaProgress?.message || "Initializing analysis..."}
              </p>
              {slaProgress && slaProgress.total > 1 && (
                <span className="text-[10px] text-gray-500 font-mono ml-2 whitespace-nowrap">
                  chunk {slaProgress.step}/{slaProgress.total}
                </span>
              )}
            </div>
          </div>
        )}

        {/* ── Main progress bar ── */}
        <div className={step === 3 ? "mt-3" : "mt-4"}>
          <div className="bg-gray-700 rounded-full h-1.5 w-full">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                isReady ? "bg-green-500" : "bg-blue-500"
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      {/* Shimmer keyframe style */}
      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(200%); }
        }
      `}</style>
    </div>
  );
}
