import { useEffect, useState, useRef } from "react";
import {
  CheckCircle,
  Loader2,
  XCircle,
  FileText,
  Brain,
  Flag,
  Calculator,
  Sparkles,
} from "lucide-react";
import { api } from "../services/api";

interface ProgressEvent {
  step: number;
  message: string;
  status: "running" | "complete" | "error";
  done: boolean;
  data?: Record<string, unknown>;
}

interface Props {
  doc_id: string;
  onComplete: (score: number, flagCount: number) => void;
  onError: () => void;
}

const STEP_ICONS: Record<
  number,
  React.ComponentType<{ className?: string }>
> = {
  1: FileText,
  2: Brain,
  3: Brain,
  4: Flag,
  5: Calculator,
  6: Sparkles,
};

const STEP_LABELS: Record<number, string> = {
  1: "Loading Contract",
  2: "AI Processing",
  3: "Extracting Terms",
  4: "Red Flag Check",
  5: "Scoring",
  6: "Complete",
};

export default function AnalysisProgress({
  doc_id,
  onComplete,
  onError,
}: Props) {
  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [isError, setIsError] = useState(false);
  const [finalScore, setFinalScore] = useState<number | null>(null);
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  useEffect(() => {
    let cancelled = false;

    const runStream = async () => {
      try {
        const response = await api.documents.analyseStream(doc_id);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        if (!response.body) {
          throw new Error("No response body");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          if (cancelled) break;

          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const raw = line.slice(6).trim();
            if (!raw) continue;

            try {
              const event: ProgressEvent = JSON.parse(raw);

              if (cancelled) break;

              setCurrentStep(event.step);
              setEvents((prev) => [...prev, event]);

              if (event.done) {
                if (event.status === "complete") {
                  const score = (event.data?.score as number) ?? 0;
                  const flagCount = (event.data?.flag_count as number) ?? 0;
                  setFinalScore(score);
                  setIsComplete(true);
                  setTimeout(() => {
                    onComplete(score, flagCount);
                  }, 800);
                } else if (event.status === "error") {
                  setIsError(true);
                  setTimeout(onError, 2000);
                }
              }
            } catch {
              // Skip malformed events
            }
          }
        }
      } catch (err) {
        if (!cancelled) {
          console.error("Analysis stream error:", err);
          setIsError(true);
          setTimeout(onError, 2000);
        }
      }
    };

    runStream();
    return () => {
      cancelled = true;
    };
  }, [doc_id]);

  const totalSteps = 6;
  const progressPct = Math.round((currentStep / totalSteps) * 100);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      {/* Progress bar */}
      <div>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "0.5rem",
          }}
        >
          <span
            style={{
              fontSize: "0.875rem",
              fontWeight: 500,
              color: "#cbd5e1",
            }}
          >
            {isComplete
              ? "Analysis Complete"
              : isError
                ? "Analysis Failed"
                : "Analysing Contract..."}
          </span>
          <span style={{ fontSize: "0.875rem", color: "#64748b" }}>
            {progressPct}%
          </span>
        </div>
        <div
          style={{
            height: "8px",
            width: "100%",
            background: "#1e293b",
            borderRadius: "99px",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: "100%",
              borderRadius: "99px",
              transition: "width 0.5s ease",
              width: `${progressPct}%`,
              background: isError
                ? "#ef4444"
                : isComplete
                  ? "#22c55e"
                  : "linear-gradient(90deg, #6366f1, #8b5cf6)",
            }}
          />
        </div>
      </div>

      {/* Step indicators */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
        }}
      >
        {Array.from({ length: totalSteps }, (_, i) => {
          const step = i + 1;
          const Icon = STEP_ICONS[step];
          const isDone = currentStep > step;
          const isActive = currentStep === step;
          return (
            <div
              key={step}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "0.25rem",
              }}
            >
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: "50%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  transition: "all 0.3s",
                  background: isDone
                    ? "#22c55e"
                    : isActive
                      ? "#6366f1"
                      : "#1e293b",
                  color: isDone || isActive ? "#fff" : "#475569",
                  animation: isActive ? "pulse 2s infinite" : undefined,
                }}
              >
                {isDone ? (
                  <CheckCircle size={16} />
                ) : isActive ? (
                  <Loader2
                    size={16}
                    style={{ animation: "spin 1s linear infinite" }}
                  />
                ) : (
                  <Icon className="" />
                )}
              </div>
              <span
                style={{
                  fontSize: "0.65rem",
                  color: "#64748b",
                  textAlign: "center",
                  width: 56,
                  lineHeight: 1.2,
                }}
              >
                {STEP_LABELS[step]}
              </span>
            </div>
          );
        })}
      </div>

      {/* Live event log */}
      <div
        style={{
          background: "#030712",
          border: "1px solid #1f2937",
          borderRadius: "0.75rem",
          padding: "1rem",
          height: 192,
          overflowY: "auto",
          fontFamily: "monospace",
          fontSize: "0.75rem",
        }}
      >
        {events.length === 0 && (
          <div style={{ color: "#4b5563" }}>
            Connecting to analysis engine...
          </div>
        )}
        {events.map((event, idx) => (
          <div
            key={idx}
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "0.5rem",
              lineHeight: 1.6,
              color:
                event.status === "error"
                  ? "#f87171"
                  : event.done && event.status === "complete"
                    ? "#4ade80"
                    : event.message.includes("⚠")
                      ? "#facc15"
                      : event.message.includes("✓")
                        ? "#4ade80"
                        : "#d1d5db",
            }}
          >
            <span
              style={{
                color: "#4b5563",
                flexShrink: 0,
                marginTop: 1,
              }}
            >
              {new Date().toLocaleTimeString("en-US", {
                hour12: false,
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              })}
            </span>
            <span>{event.message}</span>
          </div>
        ))}
        <div ref={logEndRef} />
      </div>

      {/* Final score display */}
      {isComplete && finalScore !== null && (
        <div
          style={{
            borderRadius: "0.75rem",
            padding: "1rem",
            textAlign: "center",
            background:
              finalScore >= 80
                ? "rgba(34,197,94,0.12)"
                : finalScore >= 50
                  ? "rgba(234,179,8,0.12)"
                  : "rgba(239,68,68,0.12)",
            border: `1px solid ${
              finalScore >= 80
                ? "rgba(34,197,94,0.4)"
                : finalScore >= 50
                  ? "rgba(234,179,8,0.4)"
                  : "rgba(239,68,68,0.4)"
            }`,
          }}
        >
          <div
            style={{
              fontSize: "1.75rem",
              fontWeight: 700,
              color:
                finalScore >= 80
                  ? "#4ade80"
                  : finalScore >= 50
                    ? "#facc15"
                    : "#f87171",
            }}
          >
            {finalScore}/100
          </div>
          <div style={{ fontSize: "0.875rem", color: "#94a3b8", marginTop: 4 }}>
            {finalScore >= 80
              ? "✓ Fair Contract"
              : finalScore >= 50
                ? "⚠ Some Concerns Found"
                : "⚠ Serious Issues Found"}
          </div>
        </div>
      )}

      {/* Error display */}
      {isError && (
        <div
          style={{
            background: "rgba(239,68,68,0.12)",
            border: "1px solid rgba(239,68,68,0.4)",
            borderRadius: "0.75rem",
            padding: "1rem",
            textAlign: "center",
          }}
        >
          <XCircle
            size={32}
            color="#f87171"
            style={{ margin: "0 auto 0.5rem" }}
          />
          <p
            style={{
              color: "#f87171",
              fontSize: "0.875rem",
              fontWeight: 500,
              margin: 0,
            }}
          >
            Analysis failed
          </p>
          <p
            style={{
              color: "#94a3b8",
              fontSize: "0.75rem",
              marginTop: 4,
            }}
          >
            Please try uploading again
          </p>
        </div>
      )}

      {/* Keyframes */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
