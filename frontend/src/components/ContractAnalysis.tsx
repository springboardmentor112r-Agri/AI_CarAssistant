import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, AlertTriangle, Shield, Hash, X } from 'lucide-react';
import { useAppState } from '@/context/AppContext';
import { useFetchWithRetry } from '@/hooks/useFetchWithRetry';
import Speedometer from '@/components/Speedometer';
import LoadingState from '@/components/LoadingState';

interface AnalysisResult {
  fairness_score: number;
  risk_level: string;
  issues: string[];
  vin: string;
  extracted_text?: string;
  specs?: any;
}

const ScannerOverlay = () => (
  <motion.div className="absolute inset-0 overflow-hidden rounded-2xl pointer-events-none z-10">
    <motion.div
      animate={{ y: ['0%', '100%', '0%'] }}
      transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
      className="absolute left-0 right-0 h-0.5"
      style={{
        background: 'linear-gradient(90deg, transparent, hsl(var(--primary)), transparent)',
        boxShadow: '0 0 20px 4px hsl(var(--primary) / 0.4)',
      }}
    />
  </motion.div>
);

const ContractAnalysis = () => {
  const { analysisResult, setAnalysisResult } = useAppState();
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const { loading, error, isWaking, execute } = useFetchWithRetry<AnalysisResult>();

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === 'dragenter' || e.type === 'dragover');
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) setFile(e.dataTransfer.files[0]);
  }, []);

  const handleAnalyze = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);

    const data = await execute('/upload/', { method: 'POST', body: formData });
    if (data) {
      setAnalysisResult(data);
    }
  };

  const handleNewScan = () => {
    setAnalysisResult(null);
    setFile(null);
  };

  const getRiskColor = (level?: string, score?: number) => {
    if (score !== undefined && score < 50) return 'text-score-red bg-score-red/10 ring-score-red/20';
    const l = (level ?? '').toLowerCase();
    if (l === 'low') return 'text-score-green bg-score-green/10 ring-score-green/20';
    if (l === 'medium') return 'text-score-yellow bg-score-yellow/10 ring-score-yellow/20';
    return 'text-score-red bg-score-red/10 ring-score-red/20';
  };

  const getRiskLabel = (level?: string, score?: number) => {
    if (score !== undefined && score < 50) return 'DANGER';
    return `${level ?? '---'} Risk`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
      className="space-y-6"
    >
      {/* Upload Zone - only show when no result and not loading */}
      {!analysisResult && !loading && (
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`glass-surface rounded-2xl p-8 border-2 border-dashed transition-colors ${
            dragActive ? 'border-primary bg-primary/5' : 'border-border'
          }`}
        >
          <div className="flex flex-col items-center text-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center">
              <Upload className="w-6 h-6 text-primary" />
            </div>
            <div>
              <p className="text-foreground font-medium mb-1">
                {file ? file.name : 'Drop your contract PDF here'}
              </p>
              <p className="text-sm text-muted-foreground">or click to browse</p>
            </div>

            <input
              type="file"
              accept=".pdf"
              onChange={e => e.target.files?.[0] && setFile(e.target.files[0])}
              className="hidden"
              id="file-upload"
            />

            <div className="flex gap-3">
              <label
                htmlFor="file-upload"
                className="cursor-pointer px-4 py-2 rounded-lg bg-secondary text-secondary-foreground text-sm font-medium hover:bg-secondary/80 transition-colors"
              >
                Browse Files
              </label>
              {file && (
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleAnalyze}
                  className="px-6 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:shadow-[0_0_20px_-5px_hsl(var(--primary)/0.5)] transition-all"
                >
                  Analyze Contract
                </motion.button>
              )}
            </div>

            {file && (
              <button onClick={() => setFile(null)} className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1">
                <X className="w-3 h-3" /> Remove file
              </button>
            )}
          </div>
        </div>
      )}

      {/* Loading with scanner overlay */}
      {loading && (
        <div className="relative">
          <ScannerOverlay />
          <LoadingState isWaking={isWaking} message="Analyzing contract..." showCarPulse={!isWaking} />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="glass-surface rounded-2xl p-6 text-center">
          <p className="text-destructive text-sm mb-3">{error}</p>
          <button onClick={handleNewScan} className="text-sm text-primary hover:underline">
            Try again
          </button>
        </div>
      )}

      {/* Results - persist from context */}
      <AnimatePresence>
        {analysisResult && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="glass-surface rounded-2xl p-6">
                <h3 className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-6">Fairness Score</h3>
                <Speedometer score={analysisResult.fairness_score} />
              </div>

              <div className="glass-surface rounded-2xl p-6 flex flex-col justify-between">
                <div>
                  <h3 className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-4">Risk Assessment</h3>
                  <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ring-1 text-sm font-semibold ${getRiskColor(analysisResult.risk_level, analysisResult.fairness_score)}`}>
                    <Shield className="w-4 h-4" />
                    {getRiskLabel(analysisResult.risk_level, analysisResult.fairness_score)}
                  </span>
                </div>
                {analysisResult.vin && (
                  <div className="mt-6">
                    <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-2">Extracted VIN</p>
                    <div
                      onClick={() => navigator.clipboard.writeText(analysisResult.vin)}
                      title="Click to copy"
                      className="flex items-center justify-between gap-3 px-5 py-4 rounded-xl bg-secondary ring-1 ring-border cursor-pointer hover:ring-primary/40 transition-all group"
                    >
                      <div className="flex items-center gap-3">
                        <Hash className="w-5 h-5 text-primary" />
                        <span className="text-lg font-mono tabular-nums font-semibold text-foreground tracking-wider">{analysisResult.vin}</span>
                      </div>
                      <span className="text-xs text-muted-foreground group-hover:text-primary transition-colors">Click to copy</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {analysisResult.issues?.length > 0 && (
              <div className="glass-surface rounded-2xl p-6">
                <h3 className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-4">
                  Issues Found ({analysisResult.issues.length})
                </h3>
                <div className="space-y-2 max-h-64 overflow-y-auto scrollbar-hide">
                  {analysisResult.issues.map((issue, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="flex items-start gap-3 p-3 rounded-xl bg-secondary/50"
                    >
                      <AlertTriangle className="w-4 h-4 text-score-yellow mt-0.5 shrink-0" />
                      <p className="text-sm text-foreground/90">{issue}</p>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            <button
              onClick={handleNewScan}
              className="text-sm text-primary hover:underline"
            >
              New Scan
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default ContractAnalysis;
