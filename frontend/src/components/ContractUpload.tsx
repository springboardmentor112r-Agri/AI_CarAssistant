"use client";

import { useState } from "react";
import axios from "axios";
import { UploadCloud, Loader2, FileUp, X, CheckCircle2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { NegotiationChat } from "./NegotiationChat";
import { VehicleDataLookup } from "./VehicleDataLookup";
import { SLAResults } from "./SLAResults";
import { API_ENDPOINTS } from "@/lib/api";

export function ContractUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"sla" | "chat" | "vin">("sla");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) setFile(e.target.files[0]);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files?.[0]) setFile(e.dataTransfer.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setError(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await axios.post(`${API_ENDPOINTS.UPLOAD_CONTRACT}?user_id=123`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      pollContract(res.data.id);
    } catch {
      setError("Failed to upload. Ensure the backend is running on port 8000.");
      setIsUploading(false);
    }
  };

  const pollContract = async (id: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(API_ENDPOINTS.GET_CONTRACT(id));
        if (res.data.status === "COMPLETED") {
          setResult(res.data);
          setIsUploading(false);
          clearInterval(interval);
        } else if (res.data.status === "FAILED") {
          setError("Document analysis failed. Please try again.");
          setIsUploading(false);
          clearInterval(interval);
        }
      } catch {
        clearInterval(interval);
        setIsUploading(false);
        setError("Error fetching analysis result.");
      }
    }, 2000);
  };

  const tabs = [
    { key: "sla" as const, label: "📋 SLA Analysis" },
    { key: "chat" as const, label: "💬 Negotiation AI" },
    { key: "vin" as const, label: "🚘 VIN Lookup" },
  ];

  return (
    <div className="space-y-6">
      {!result ? (
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          className={`relative flex flex-col items-center justify-center p-12 border-2 border-dashed rounded-2xl transition-all duration-300 cursor-pointer ${dragging ? "border-indigo-400 bg-indigo-500/10" : "border-white/15 hover:border-indigo-400/50 bg-white/3"}`}
        >
          <input
            type="file"
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={handleFileChange}
            disabled={isUploading}
          />

          {file ? (
            <div className="flex flex-col items-center gap-3">
              <div className="bg-indigo-500/20 p-4 rounded-2xl">
                <FileUp className="w-10 h-10 text-indigo-400" />
              </div>
              <p className="text-white font-medium text-center">{file.name}</p>
              <p className="text-slate-500 text-sm">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              <button
                onClick={(e) => { e.stopPropagation(); setFile(null); }}
                className="flex items-center gap-1 text-xs text-slate-400 hover:text-red-400 transition-colors mt-1"
              >
                <X className="w-3 h-3" /> Remove file
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3 text-center pointer-events-none">
              <div className="bg-white/5 p-4 rounded-2xl border border-white/10">
                <UploadCloud className="w-10 h-10 text-slate-400" />
              </div>
              <p className="text-white font-medium">Drop your contract here</p>
              <p className="text-slate-500 text-sm">PDF, JPG, PNG — up to 10 MB</p>
            </div>
          )}
        </div>
      ) : null}

      {!result && (
        <button
          onClick={handleUpload}
          disabled={!file || isUploading}
          className="w-full flex items-center justify-center gap-2 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold rounded-2xl shadow-lg hover:shadow-indigo-500/40 transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed hover:-translate-y-0.5"
        >
          {isUploading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              AI is analyzing your contract...
            </>
          ) : (
            <>
              <UploadCloud className="w-5 h-5" />
              Analyze Contract
            </>
          )}
        </button>
      )}

      {error && (
        <p className="text-red-400 text-sm text-center bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">{error}</p>
      )}

      {/* Results */}
      <AnimatePresence>
        {result && (
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            {/* Success bar */}
            <div className="flex items-center justify-between bg-green-500/10 border border-green-500/20 rounded-2xl px-6 py-4">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-400 shrink-0" />
                <div>
                  <p className="text-green-300 font-semibold text-lg">Analysis Complete!</p>
                  <p className="text-xs text-slate-500">Contract Reviewed successfully using Gemini AI</p>
                </div>
              </div>
              <button
                onClick={() => { setResult(null); setFile(null); }}
                className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-xs text-slate-300 transition-all font-medium"
              >
                Upload New
              </button>
            </div>

            {/* Integrated Report Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              {/* Main Report Column */}
              <div className="lg:col-span-7 space-y-6">
                <div className="bg-white/3 border border-white/10 rounded-3xl p-1 overflow-hidden">
                  <div className="p-6 bg-white/[0.02]">
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                       📋 Contract Analysis Report
                    </h3>
                    <SLAResults result={result} />
                  </div>
                </div>

                {/* Optional VIN Lookup remains as a secondary utility if needed, 
                    but basic info is already in SLA header */}
                <div className="bg-white/3 border border-white/10 rounded-3xl p-6">
                   <h4 className="text-sm font-semibold text-white mb-4">Manufacturer Verification</h4>
                   <VehicleDataLookup contractId={result.id} />
                </div>
              </div>

              {/* AI Consultation Sidebar */}
              <div className="lg:col-span-5 sticky top-6">
                <div className="bg-indigo-600/5 border border-indigo-500/20 rounded-3xl overflow-hidden backdrop-blur-sm">
                  <div className="p-5 border-b border-indigo-500/20 bg-indigo-500/10 flex items-center gap-3">
                    <div className="bg-indigo-400/20 p-2 rounded-lg">
                       <CheckCircle2 className="w-5 h-5 text-indigo-400" />
                    </div>
                    <div>
                      <h3 className="font-bold text-white">AI Consultation</h3>
                      <p className="text-xs text-slate-400">Ask questions about this contract</p>
                    </div>
                  </div>
                  <div className="h-[600px] overflow-hidden">
                    <NegotiationChat contractId={result.id} />
                  </div>
                </div>
                
                <p className="text-[10px] text-slate-500 text-center mt-4 px-4">
                  The AI consultant provides guidance based on standard automotive industry practices. 
                  Final decisions should be verified with the lender.
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
