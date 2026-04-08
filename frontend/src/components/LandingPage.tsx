import { motion } from 'framer-motion';
import { ArrowRight, Shield } from 'lucide-react';

interface LandingPageProps {
  onGetStarted: () => void;
}

const LandingPage = ({ onGetStarted }: LandingPageProps) => {
  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden bg-background">
      {/* Animated radial gradient */}
      <motion.div
        animate={{ scale: [1, 1.15, 1], opacity: [0.25, 0.45, 0.25] }}
        transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[900px] rounded-full pointer-events-none"
        style={{ background: 'radial-gradient(circle, hsl(var(--primary) / 0.18) 0%, transparent 70%)' }}
      />

      {/* Subtle grid */}
      <div
        className="absolute inset-0 opacity-[0.04] pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(to right, hsl(var(--primary)) 1px, transparent 1px), linear-gradient(to bottom, hsl(var(--primary)) 1px, transparent 1px)`,
          backgroundSize: '60px 60px',
          maskImage: 'radial-gradient(ellipse at center, black 30%, transparent 80%)',
          WebkitMaskImage: 'radial-gradient(ellipse at center, black 30%, transparent 80%)',
        }}
      />

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.25, 0.1, 0.25, 1] }}
        className="relative z-10 text-center px-6 max-w-3xl mx-auto"
      >
        <div className="flex items-center justify-center gap-3 mb-8">
          <Shield className="w-10 h-10 text-primary" />
        </div>

        <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-foreground mb-4">
          DealGuard
        </h1>

        <p className="text-base md:text-lg text-muted-foreground max-w-lg mx-auto mb-14 font-light">
          Instant Legal Intelligence for Vehicle Purchases.
        </p>

        <motion.button
          onClick={onGetStarted}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          className="group relative inline-flex items-center gap-3 px-12 py-4 rounded-xl bg-primary text-primary-foreground font-semibold text-base transition-all hover:shadow-[0_0_40px_-8px_hsl(var(--primary)/0.6)]"
        >
          <span className="absolute inset-0 rounded-xl ring-1 ring-primary/50 group-hover:ring-primary transition-all" />
          <span className="relative flex items-center gap-3">
            Launch Dashboard
            <ArrowRight className="w-5 h-5" />
          </span>
        </motion.button>
      </motion.div>
    </div>
  );
};

export default LandingPage;
