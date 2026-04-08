import { motion } from 'framer-motion';

const GridBackground = () => (
  <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
    <div
      className="absolute inset-0 opacity-[0.12]"
      style={{
        backgroundImage: `linear-gradient(to right, hsl(217 91% 60%) 1px, transparent 1px), linear-gradient(to bottom, hsl(217 91% 60%) 1px, transparent 1px)`,
        backgroundSize: '40px 40px',
        maskImage: 'radial-gradient(ellipse at center, black, transparent 80%)',
        WebkitMaskImage: 'radial-gradient(ellipse at center, black, transparent 80%)',
      }}
    />
    <motion.div
      animate={{ y: [0, -40] }}
      transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
      className="absolute inset-0 opacity-[0.04]"
      style={{
        backgroundImage: `linear-gradient(to right, hsl(217 91% 60%) 1px, transparent 1px), linear-gradient(to bottom, hsl(217 91% 60%) 1px, transparent 1px)`,
        backgroundSize: '40px 40px',
      }}
    />
    <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/50 to-background" />
  </div>
);

export default GridBackground;
