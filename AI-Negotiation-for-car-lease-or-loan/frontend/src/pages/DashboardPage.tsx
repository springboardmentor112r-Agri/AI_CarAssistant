import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  FileText,
  Image as ImageIcon,
  File,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Loader2,
  Plus,
  BarChart2,
  MessageSquare,
  Trash2,
  X,
} from "lucide-react";
import { api } from "../services/api";
import { DocumentRead } from "../types";
import DocumentUpload from "../components/DocumentUpload";
import Navbar from "../components/Navbar";

export default function DashboardPage() {
  const [documents, setDocuments] = useState<DocumentRead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [compareMode, setCompareMode] = useState(false);
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);
  const navigate = useNavigate();

  const toggleCompareSelect = (doc_id: string) => {
    setSelectedForCompare((prev) => {
      if (prev.includes(doc_id)) {
        return prev.filter((id) => id !== doc_id);
      }
      if (prev.length >= 2) {
        return [prev[0], doc_id];
      }
      return [...prev, doc_id];
    });
  };

  const pollingRefs = useRef<Map<string, ReturnType<typeof setInterval>>>(
    new Map(),
  );

  const startPolling = (doc_id: string) => {
    if (pollingRefs.current.has(doc_id)) return;

    const intervalId = setInterval(async () => {
      try {
        const statusData = await api.documents.getStatus(doc_id);
        const {
          processing_status: status,
          error_message,
          sla_progress,
        } = statusData;

        if (status === "deleted") {
          stopPolling(doc_id);
          setDocuments((prev) => prev.filter((d) => d.doc_id !== doc_id));
          return;
        }

        setDocuments((prev) =>
          prev.map((d) =>
            d.doc_id === doc_id
              ? { ...d, processing_status: status, error_message, sla_progress }
              : d,
          ),
        );

        if (
          status === "ready" ||
          status === "error" ||
          status === "sla_failed"
        ) {
          stopPolling(doc_id);
          // Refetch to get the full document details (score, etc.)
          if (status === "ready") {
            const updatedDoc = await api.documents.getById(doc_id);
            setDocuments((prev) =>
              prev.map((d) => (d.doc_id === doc_id ? updatedDoc : d)),
            );
          }
        }
      } catch (error) {
        console.error(`Failed to poll status for ${doc_id}`, error);
        stopPolling(doc_id);
      }
    }, 4000);

    pollingRefs.current.set(doc_id, intervalId);
  };

  const stopPolling = (doc_id: string) => {
    const intervalId = pollingRefs.current.get(doc_id);
    if (intervalId) {
      clearInterval(intervalId);
      pollingRefs.current.delete(doc_id);
    }
  };

  useEffect(() => {
    let mounted = true;
    const fetchDocs = async () => {
      try {
        setIsLoading(true);
        const docs = await api.documents.list();
        if (mounted) {
          setDocuments(docs);

          // Start polling for active ones
          docs.forEach((doc: DocumentRead) => {
            if (
              !["ready", "error", "deleted"].includes(doc.processing_status)
            ) {
              startPolling(doc.doc_id);
            }
          });
        }
      } catch (err) {
        console.error("Failed to load documents", err);
      } finally {
        if (mounted) setIsLoading(false);
      }
    };
    fetchDocs();

    return () => {
      mounted = false;
      pollingRefs.current.forEach((id) => clearInterval(id));
      pollingRefs.current.clear();
    };
  }, []);

  const handleUploadComplete = async (doc_id: string) => {
    // Modal stays open during analysis (AnalysisProgress handles this)
    // Only called AFTER analysis is complete
    setShowUploadModal(false);

    try {
      const doc = await api.documents.getById(doc_id);
      setDocuments((prev) => [doc, ...prev]);
      // Document should already be ready but start polling just in case
      if (doc.processing_status !== "ready") {
        startPolling(doc_id);
      }
    } catch {
      setDocuments((prev) => [
        {
          doc_id,
          user_id: "",
          filename: "Contract",
          processing_status: "ready",
          upload_timestamp: new Date().toISOString(),
          sla_retry_count: 0,
        },
        ...prev,
      ]);
    }
  };

  const handleDelete = async (doc_id: string) => {
    if (!window.confirm("Delete this contract and all chats?")) return;
    try {
      await api.documents.delete(doc_id);
      setDocuments((prev) => prev.filter((d) => d.doc_id !== doc_id));
      stopPolling(doc_id);
    } catch (err) {
      console.error("Failed to delete document", err);
    }
  };

  const handleRetry = async (doc_id: string) => {
    try {
      // Set to processing state immediately to show progress
      setDocuments((prev) =>
        prev.map((d) =>
          d.doc_id === doc_id
            ? {
                ...d,
                processing_status: "extraction_complete",
                error_message: null,
              }
            : d,
        ),
      );

      // Start polling in parallel so that /status fetches progress updates
      startPolling(doc_id);

      // Retry is now SYNCHRONOUS — awaits the full result
      const result = await api.documents.retrySLA(doc_id);

      // Stop polling as the sync result is here
      stopPolling(doc_id);

      if (result.processing_status === "ready") {
        // Refetch full doc to get sla_json, score, etc.
        const updatedDoc = await api.documents.getById(doc_id);
        setDocuments((prev) =>
          prev.map((d) => (d.doc_id === doc_id ? updatedDoc : d)),
        );
      } else {
        // sla_failed — update state to show retry button again
        setDocuments((prev) =>
          prev.map((d) =>
            d.doc_id === doc_id
              ? {
                  ...d,
                  processing_status: result.processing_status,
                  error_message: result.message,
                  sla_retry_count: result.sla_retry_count,
                }
              : d,
          ),
        );
      }
    } catch (err: any) {
      console.error("Failed to retry SLA analysis", err);
      // Reset to sla_failed so button reappears
      setDocuments((prev) =>
        prev.map((d) =>
          d.doc_id === doc_id
            ? {
                ...d,
                processing_status: "sla_failed",
                error_message:
                  err?.response?.data?.detail || "Retry failed. Try again.",
              }
            : d,
        ),
      );
    }
  };

  const readyCount = documents.filter(
    (d) => d.processing_status === "ready",
  ).length;

  const getFileIcon = (filename: string) => {
    const ext = filename.split(".").pop()?.toLowerCase() || "";
    if (["pdf"].includes(ext))
      return <FileText className="w-6 h-6 text-red-500" />;
    if (["doc", "docx"].includes(ext))
      return <FileText className="w-6 h-6 text-blue-500" />;
    if (["png", "jpg", "jpeg"].includes(ext))
      return <ImageIcon className="w-6 h-6 text-purple-500" />;
    return <File className="w-6 h-6 text-gray-500" />;
  };

  const formatRelativeTime = (dateStr: string) => {
    const dates = new Date(dateStr);
    if (isNaN(dates.getTime())) return dateStr;

    // Quick formatter matching requirement
    const formatter = new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
    const msDiff = Date.now() - dates.getTime();
    const hours = Math.floor(msDiff / 3600000);
    let relative = `${hours} hours ago`;
    if (hours < 1) {
      const mins = Math.max(1, Math.floor(msDiff / 60000));
      relative = `${mins} mins ago`;
    } else if (hours > 24) {
      relative = `${Math.floor(hours / 24)} days ago`;
    }
    return `${formatter.format(dates)} · ${relative}`;
  };

  const renderStatusBadge = (status: string) => {
    switch (status) {
      case "processing":
      case "pending":
        return (
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded-full text-xs font-medium">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>Processing</span>
          </div>
        );
      case "extraction_complete":
        return (
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 rounded-full text-xs font-medium">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>Analysing</span>
          </div>
        );
      case "sla_failed":
        return (
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded-full text-xs font-medium">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Retry needed</span>
          </div>
        );
      case "ready":
        return (
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full text-xs font-medium">
            <CheckCircle className="w-3.5 h-3.5" />
            <span>Ready</span>
          </div>
        );
      case "error":
        return (
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-full text-xs font-medium">
            <XCircle className="w-3.5 h-3.5" />
            <span>Failed</span>
          </div>
        );
      default:
        return (
          <div className="px-2.5 py-1 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-full text-xs font-medium capitalize">
            {status}
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100">
      <Navbar />

      <main className="max-w-7xl mx-auto">
        <div className="px-6 py-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">My Contracts</h1>
            <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">
              {documents.length} contract(s) uploaded
            </p>
          </div>
          <div className="flex items-center gap-3">
            {readyCount >= 2 && !compareMode && (
              <button
                onClick={() => {
                  setCompareMode(true);
                  setSelectedForCompare([]);
                }}
                className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 font-medium rounded-xl transition-colors text-sm"
              >
                <BarChart2 className="w-4 h-4" />
                Compare
              </button>
            )}
            <button
              onClick={() => setShowUploadModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl transition-colors shadow-sm text-sm"
            >
              <Plus className="w-4 h-4" />
              Upload Contract
            </button>
          </div>
        </div>

        {compareMode && (
          <div className="px-6">
            <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700/50 rounded-xl px-4 py-3 mb-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                <p className="text-sm text-blue-700 dark:text-blue-300 font-medium">
                  {selectedForCompare.length === 0
                    ? "Select 2 contracts to compare"
                    : selectedForCompare.length === 1
                      ? "1 selected — select one more"
                      : "2 contracts selected — ready to compare"}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    setCompareMode(false);
                    setSelectedForCompare([]);
                  }}
                  className="text-xs text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white px-3 py-1.5 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    if (selectedForCompare.length === 2) {
                      navigate(
                        `/compare?doc1=${selectedForCompare[0]}&doc2=${selectedForCompare[1]}`,
                      );
                    }
                  }}
                  disabled={selectedForCompare.length < 2}
                  className="text-xs font-medium px-4 py-1.5 rounded-lg transition-colors bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white"
                >
                  Compare Now →
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="px-6 pb-12">
          {isLoading ? (
            <div
              className="flex-1 flex flex-col items-center
                            justify-center gap-4 py-20"
            >
              <div
                className="w-10 h-10 border-2
                              border-blue-500/30 border-t-blue-500
                              rounded-full animate-spin"
              />
              <p className="text-gray-400 text-sm">Loading your contracts...</p>
              <p className="text-gray-600 text-xs">
                First load may take a few seconds
              </p>
            </div>
          ) : documents.length === 0 ? (
            <div className="max-w-md mx-auto mt-16 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-3xl p-8 text-center shadow-sm">
              <div className="w-16 h-16 bg-gray-50 dark:bg-gray-800 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <FileText className="w-8 h-8 text-gray-400 dark:text-gray-500" />
              </div>
              <h2 className="text-xl font-bold mb-2">No contracts yet</h2>
              <p className="text-gray-500 dark:text-gray-400 mb-8">
                Upload your first contract to get started with AI analysis and
                negotiation coaching.
              </p>
              <button
                onClick={() => setShowUploadModal(true)}
                className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-colors"
              >
                Upload Contract
              </button>
            </div>
          ) : (
            <>
              {/* Processing / in-progress documents — compact banner */}
              {documents.filter(
                (d) => !["ready", "error"].includes(d.processing_status),
              ).length > 0 && (
                <div className="mb-6 flex flex-col gap-3">
                  {documents
                    .filter(
                      (d) => !["ready", "error"].includes(d.processing_status),
                    )
                    .map((doc) => {
                      const isAnalysing =
                        doc.processing_status === "extraction_complete";
                      const isExtracting =
                        doc.processing_status === "pending" ||
                        doc.processing_status === "processing";
                      const isFailed = doc.processing_status === "sla_failed";
                      const slaPercent =
                        doc.sla_progress && doc.sla_progress.total > 0
                          ? Math.round(
                              (doc.sla_progress.step / doc.sla_progress.total) *
                                100,
                            )
                          : 0;

                      return (
                        <div
                          key={doc.doc_id}
                          className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-3"
                        >
                          <div className="flex items-center gap-3">
                            <div className="p-1.5 bg-gray-50 dark:bg-gray-900 rounded-lg">
                              {getFileIcon(doc.filename)}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium truncate">
                                {doc.filename}
                              </p>
                              <p className="text-xs text-gray-500 dark:text-gray-400">
                                {isExtracting
                                  ? "Extracting text..."
                                  : isAnalysing
                                    ? "AI analysis in progress..."
                                    : isFailed
                                      ? doc.error_message ||
                                        "Analysis failed — retry available"
                                      : "Processing..."}
                              </p>
                            </div>
                            {isFailed ? (
                              <button
                                onClick={() => handleRetry(doc.doc_id)}
                                className="px-3 py-1 text-xs font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 hover:bg-amber-200 dark:hover:bg-amber-900/50 rounded-lg transition-colors"
                              >
                                Retry
                              </button>
                            ) : (
                              <Loader2 className="w-4 h-4 text-blue-500 animate-spin flex-shrink-0" />
                            )}
                            <button
                              onClick={() => handleDelete(doc.doc_id)}
                              className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors flex-shrink-0"
                              title="Delete"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                          {/* Progress section for extracting / analysing states */}
                          {(isExtracting || isAnalysing) && (
                            <div className="mt-2 space-y-1.5">
                              <div className="flex justify-between items-center">
                                <div className="flex items-center gap-1.5">
                                  <div className="w-3 h-3 relative flex items-center justify-center">
                                    <div className="absolute inset-0 rounded-full border border-blue-500/30 border-t-blue-400 animate-spin" />
                                  </div>
                                  <p className="text-[10px] text-blue-600 dark:text-blue-400 font-medium uppercase tracking-wider truncate">
                                    {doc.sla_progress?.message ||
                                      (isAnalysing
                                        ? "Initializing analysis..."
                                        : "Extracting text...")}
                                  </p>
                                </div>
                                <div className="flex items-center gap-1.5 ml-2 flex-shrink-0">
                                  {isAnalysing &&
                                    doc.sla_progress &&
                                    doc.sla_progress.total > 1 && (
                                      <span className="text-[10px] text-gray-500 font-mono">
                                        {doc.sla_progress.step}/
                                        {doc.sla_progress.total}
                                      </span>
                                    )}
                                  <span className="text-[10px] text-gray-500 font-mono font-bold">
                                    {isAnalysing && doc.sla_progress
                                      ? `${slaPercent}%`
                                      : isExtracting
                                        ? ""
                                        : "5%"}
                                  </span>
                                </div>
                              </div>
                              <div className="h-1.5 w-full bg-gray-100 dark:bg-gray-700/50 rounded-full overflow-hidden border border-gray-200/50 dark:border-gray-700/50">
                                <div
                                  className="h-full rounded-full transition-all duration-700 ease-out relative overflow-hidden"
                                  style={{
                                    width:
                                      isAnalysing && doc.sla_progress
                                        ? `${Math.max(5, slaPercent)}%`
                                        : isExtracting
                                          ? "30%"
                                          : "5%",
                                    background:
                                      "linear-gradient(90deg, #2563eb, #6366f1)",
                                    boxShadow: "0 0 8px rgba(37,99,235,0.4)",
                                  }}
                                >
                                  {/* Shimmer on active progress */}
                                  {(!doc.sla_progress || slaPercent < 100) && (
                                    <div
                                      style={{
                                        position: "absolute",
                                        inset: 0,
                                        background:
                                          "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.2) 50%, transparent 100%)",
                                        animation:
                                          "dashShimmer 1.5s infinite linear",
                                      }}
                                    />
                                  )}
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  <style>{`
                    @keyframes dashShimmer {
                      0% { transform: translateX(-100%); }
                      100% { transform: translateX(200%); }
                    }
                  `}</style>
                </div>
              )}

              {/* Error documents — compact banner */}
              {documents.filter((d) => d.processing_status === "error").length >
                0 && (
                <div className="mb-6 flex flex-col gap-3">
                  {documents
                    .filter((d) => d.processing_status === "error")
                    .map((doc) => (
                      <div
                        key={doc.doc_id}
                        className="bg-white dark:bg-gray-800 border border-red-200 dark:border-red-900/50 rounded-xl px-4 py-3 flex items-center gap-3"
                      >
                        <div className="p-1.5 bg-red-50 dark:bg-red-900/20 rounded-lg">
                          <XCircle className="w-5 h-5 text-red-500" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">
                            {doc.filename}
                          </p>
                          <p className="text-xs text-red-500 dark:text-red-400">
                            {doc.error_message || "Processing failed"}
                          </p>
                        </div>
                        <button
                          onClick={async () => {
                            await handleDelete(doc.doc_id);
                            setShowUploadModal(true);
                          }}
                          className="px-3 py-1 text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50 rounded-lg transition-colors flex-shrink-0"
                        >
                          Re-upload
                        </button>
                        <button
                          onClick={() => handleDelete(doc.doc_id)}
                          className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors flex-shrink-0"
                          title="Delete"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                </div>
              )}

              {/* Ready documents — full cards with review & chat */}
              {documents.filter((d) => d.processing_status === "ready").length >
              0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                  {documents
                    .filter((d) => d.processing_status === "ready")
                    .map((doc) => (
                      <div
                        key={doc.doc_id}
                        className={`bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-5 hover:shadow-lg dark:hover:shadow-gray-900/50 hover:border-blue-200 dark:hover:border-gray-600 transition-all flex flex-col group relative ${
                          compareMode
                            ? "cursor-pointer ring-2 " +
                              (selectedForCompare.includes(doc.doc_id)
                                ? "ring-blue-500"
                                : "ring-transparent hover:ring-blue-500/50")
                            : ""
                        }`}
                        onClick={
                          compareMode
                            ? () => toggleCompareSelect(doc.doc_id)
                            : undefined
                        }
                      >
                        {compareMode && (
                          <div
                            className={`absolute top-3 right-3 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all z-10 ${
                              selectedForCompare.includes(doc.doc_id)
                                ? "bg-blue-500 border-blue-500"
                                : "bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600"
                            }`}
                          >
                            {selectedForCompare.includes(doc.doc_id) && (
                              <CheckCircle className="w-4 h-4 text-white" />
                            )}
                          </div>
                        )}
                        <div className="flex justify-between items-start mb-3">
                          <div className="p-2 bg-gray-50 dark:bg-gray-900 rounded-lg">
                            {getFileIcon(doc.filename)}
                          </div>
                          {renderStatusBadge(doc.processing_status)}
                        </div>

                        <h3
                          className="font-semibold text-base truncate mb-1"
                          title={doc.filename}
                        >
                          {doc.filename}
                        </h3>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-4">
                          {formatRelativeTime(doc.upload_timestamp)}
                        </div>

                        {doc.contract_fairness_score !== null &&
                          doc.contract_fairness_score !== undefined && (
                            <div className="mb-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg p-3">
                              <div className="flex justify-between items-center mb-1.5">
                                <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                  Fairness Score
                                </span>
                                <span className="text-xs font-bold text-gray-900 dark:text-white">
                                  {Math.round(doc.contract_fairness_score)}/100
                                </span>
                              </div>
                              <div className="h-1.5 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden flex">
                                <div
                                  className={`h-full rounded-full ${doc.contract_fairness_score >= 80 ? "bg-green-500" : doc.contract_fairness_score >= 50 ? "bg-yellow-500" : "bg-red-500"}`}
                                  style={{
                                    width: `${Math.max(5, doc.contract_fairness_score)}%`,
                                  }}
                                />
                              </div>

                              {(() => {
                                const count =
                                  doc.sla_json?.red_flags?.length || 0;
                                if (count > 0) {
                                  return (
                                    <div className="mt-3 flex items-center gap-1.5 text-xs font-medium text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 px-2 py-1 rounded inline-flex">
                                      <AlertTriangle className="w-3 h-3" />⚠{" "}
                                      {count} issue{count !== 1 ? "s" : ""}
                                    </div>
                                  );
                                }
                                return null;
                              })()}
                            </div>
                          )}

                        <div className="mt-auto pt-4 border-t border-gray-100 dark:border-gray-700 flex items-center gap-2">
                          <button
                            onClick={() =>
                              navigate(`/documents/${doc.doc_id}/review`)
                            }
                            className="flex-1 py-1.5 text-sm font-medium bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 text-gray-700 dark:text-white rounded-lg transition-colors border border-gray-200 dark:border-transparent"
                          >
                            Review
                          </button>
                          <button
                            onClick={() => navigate(`/chat/${doc.doc_id}`)}
                            className="flex-1 flex items-center justify-center gap-1.5 py-1.5 text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                          >
                            <MessageSquare className="w-4 h-4" />
                            Chat
                          </button>
                          <button
                            onClick={() => handleDelete(doc.doc_id)}
                            className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors ml-auto"
                            title="Delete Contract"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                </div>
              ) : (
                /* All documents are still processing — no ready cards yet */
                documents.length > 0 && (
                  <div className="text-center py-12 text-gray-400 dark:text-gray-500 text-sm">
                    Your contracts are being processed. Cards will appear here
                    once analysis is complete.
                  </div>
                )
              )}
            </>
          )}
        </div>
      </main>

      {/* UPLOAD MODAL */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
            <div className="p-4 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center">
              <h3 className="font-bold text-lg">Upload Contract</h3>
              <button
                onClick={() => setShowUploadModal(false)}
                className="p-1.5 text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 overflow-y-auto">
              <DocumentUpload onUploadComplete={handleUploadComplete} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
