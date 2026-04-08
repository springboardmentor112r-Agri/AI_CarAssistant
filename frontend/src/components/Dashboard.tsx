import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ScanLine, Car, MessageSquare } from 'lucide-react';
import DashboardHeader from '@/components/DashboardHeader';
import ContractAnalysis from '@/components/ContractAnalysis';
import VehicleSpecs from '@/components/VehicleSpecs';
import AIChatbot from '@/components/AIChatbot';

const tabs = [
  { id: 'analysis', label: 'Contract Scan', icon: ScanLine },
  { id: 'vehicle', label: 'Vehicle Details', icon: Car },
  { id: 'chat', label: 'AI Consultant', icon: MessageSquare },
] as const;

type TabId = typeof tabs[number]['id'];

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState<TabId>('analysis');

  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader />

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex gap-1 p-1 rounded-xl bg-secondary/50 ring-1 ring-border mb-8 overflow-x-auto scrollbar-hide">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`relative flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap flex-1 justify-center ${
                activeTab === tab.id
                  ? 'text-primary-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {activeTab === tab.id && (
                <motion.div
                  layoutId="active-tab"
                  className="absolute inset-0 bg-primary rounded-lg"
                  transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                />
              )}
              <span className="relative z-10 flex items-center gap-2">
                <tab.icon className="w-4 h-4" />
                <span className="hidden sm:inline">{tab.label}</span>
              </span>
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          {activeTab === 'analysis' && <ContractAnalysis key="analysis" />}
          {activeTab === 'vehicle' && <VehicleSpecs key="vehicle" />}
          {activeTab === 'chat' && <AIChatbot key="chat" />}
        </AnimatePresence>
      </main>
    </div>
  );
};

export default Dashboard;
