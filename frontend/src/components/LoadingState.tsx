import { motion } from 'framer-motion';
import { Loader2, ServerCrash, Car } from 'lucide-react';

interface LoadingStateProps {
  isWaking: boolean;
  message?: string;
  showCarPulse?: boolean;
}

const LoadingState = ({ isWaking, message, showCarPulse }: LoadingStateProps) => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    className="flex flex-col items-center justify-center py-16 gap-4"
  >
    {isWaking ? (
      <>
        <ServerCrash className="w-8 h-8 text-primary animate-pulse-glow" />
        <p className="text-sm text-muted-foreground text-center">
          Waking up server... please wait 30 seconds
        </p>
        <div className="w-48 h-1 rounded-full bg-secondary overflow-hidden">
          <motion.div
            className="h-full bg-primary rounded-full"
            initial={{ width: '0%' }}
            animate={{ width: '100%' }}
            transition={{ duration: 30, ease: 'linear' }}
          />
        </div>
      </>
    ) : showCarPulse ? (
      <>
        <motion.div
          animate={{ scale: [1, 1.15, 1], opacity: [0.7, 1, 0.7] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
        >
          <Car className="w-10 h-10 text-primary" />
        </motion.div>
        <p className="text-sm text-muted-foreground">{message || 'Analyzing...'}</p>
      </>
    ) : (
      <>
        <Loader2 className="w-6 h-6 text-primary animate-spin" />
        <p className="text-sm text-muted-foreground">{message || 'Processing...'}</p>
      </>
    )}
  </motion.div>
);

export default LoadingState;
