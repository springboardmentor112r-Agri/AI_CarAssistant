import { motion } from 'framer-motion';
import { Car, Tag, Calendar, Truck, Fuel, Cog, CircleDot, Gauge, FileText } from 'lucide-react';
import { useAppState } from '@/context/AppContext';

const specConfig = [
  { key: 'make', label: 'Make', icon: Car },
  { key: 'model', label: 'Model', icon: Tag },
  { key: 'year', label: 'Year', icon: Calendar },
  { key: 'body', label: 'Body Type', icon: Truck },
  { key: 'fuel', label: 'Fuel Type', icon: Fuel },
  { key: 'drive', label: 'Drive Type', icon: Cog },
  { key: 'cylinders', label: 'Cylinders', icon: CircleDot },
  { key: 'hp', label: 'Horsepower', icon: Gauge },
];

const VehicleSpecs = () => {
  const { analysisResult } = useAppState();

  if (!analysisResult || !analysisResult.specs) {
    return (
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
        className="glass-surface rounded-2xl p-12 text-center"
      >
        <div className="w-16 h-16 rounded-2xl bg-secondary flex items-center justify-center mx-auto mb-4">
          <FileText className="w-7 h-7 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold text-foreground mb-2">No Vehicle Data</h3>
        <p className="text-sm text-muted-foreground max-w-sm mx-auto">
          Upload a contract to view technical specs.
        </p>
      </motion.div>
    );
  }

  const specs = analysisResult.specs;

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
    >
      <div className="glass-surface rounded-2xl p-6">
        <h3 className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-6">Vehicle Specifications</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {specConfig.map(({ key, label, icon: Icon }, i) => (
            <motion.div
              key={key}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
              className="glass-surface rounded-2xl p-5 ring-1 ring-border hover:ring-primary/30 transition-all duration-500 flex flex-col items-center text-center gap-3"
              style={{ boxShadow: '0 0 15px -5px hsl(var(--primary) / 0.08)' }}
            >
              <div className="w-11 h-11 rounded-xl bg-primary/10 flex items-center justify-center">
                <Icon className="w-5 h-5 text-primary" />
              </div>
              <p className="text-xs uppercase tracking-[0.15em] text-muted-foreground">{label}</p>
              <p className="text-lg font-semibold text-foreground">
                {specs[key] != null && specs[key] !== '' ? String(specs[key]) : 'Not Listed'}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  );
};

export default VehicleSpecs;
