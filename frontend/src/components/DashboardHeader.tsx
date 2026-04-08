import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Shield, LogOut, Activity } from 'lucide-react';
import { useAppState } from '@/context/AppContext';

const DashboardHeader = () => {
  const { profile, logout } = useAppState();
  const [greeting, setGreeting] = useState('Welcome');

  useEffect(() => {
    const key = 'dealguard_has_visited';
    if (localStorage.getItem(key)) {
      setGreeting('Welcome back');
    } else {
      setGreeting('Welcome');
      localStorage.setItem(key, 'true');
    }
  }, []);

  const displayName = profile?.full_name || 'User';

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-primary" />
            <span className="font-bold text-foreground">DealGuard</span>
          </div>
          <div className="hidden sm:flex items-center gap-2 text-sm text-muted-foreground">
            <span>{greeting},</span>
            <span className="font-medium text-foreground">{displayName}</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-score-green/10 ring-1 ring-score-green/20">
            <Activity className="w-3.5 h-3.5 text-score-green" />
            <span className="text-xs font-medium text-score-green">Status: Active</span>
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={logout}
            className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </motion.button>
        </div>
      </div>
    </header>
  );
};

export default DashboardHeader;
