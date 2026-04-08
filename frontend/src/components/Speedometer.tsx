import { motion } from 'framer-motion';

interface SpeedometerProps {
  score: number;
}

const Speedometer = ({ score }: SpeedometerProps) => {
  const getColor = (s: number) => {
    if (s >= 90) return 'hsl(142 71% 45%)';
    if (s >= 70) return 'hsl(48 96% 53%)';
    return 'hsl(0 84% 60%)';
  };

  const getLabel = (s: number) => {
    if (s >= 90) return 'Excellent';
    if (s >= 70) return 'Fair';
    if (s >= 50) return 'Risky';
    return 'DANGER';
  };

  const color = getColor(score);

  return (
    <div className="relative w-64 h-36 flex flex-col items-center justify-end mx-auto">
      <svg viewBox="0 0 256 130" className="w-full h-auto">
        {/* Background arc */}
        <path
          d="M 18 120 A 110 110 0 0 1 238 120"
          fill="none"
          stroke="currentColor"
          strokeWidth="14"
          strokeLinecap="round"
          className="text-secondary"
        />
        {/* Score arc */}
        <motion.path
          d="M 18 120 A 110 110 0 0 1 238 120"
          fill="none"
          stroke={color}
          strokeWidth="14"
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: Math.min(score / 100, 1) }}
          transition={{ duration: 1.5, ease: [0.25, 0.1, 0.25, 1] }}
          style={{ filter: `drop-shadow(0 0 8px ${color})` }}
        />
      </svg>
      <div className="absolute bottom-0 text-center">
        <motion.span
          className="text-5xl font-bold tabular-nums text-foreground"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          {score}
        </motion.span>
        <p className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground mt-1">
          {getLabel(score)}
        </p>
      </div>
    </div>
  );
};

export default Speedometer;
