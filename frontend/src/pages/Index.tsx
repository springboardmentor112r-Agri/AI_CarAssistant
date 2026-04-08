import { useState } from 'react';
import { useAppState } from '@/context/AppContext';
import LandingPage from '@/components/LandingPage';
import AuthPage from '@/components/AuthPage';
import Dashboard from '@/components/Dashboard';
import LoadingState from '@/components/LoadingState';

type View = 'landing' | 'auth';

const Index = () => {
  const { isLoggedIn, isLoading } = useAppState();
  const [view, setView] = useState<View>('landing');

  if (isLoading) return <LoadingState isWaking={false} message="Loading..." />;
  if (isLoggedIn) return <Dashboard />;
  if (view === 'auth') return <AuthPage onBack={() => setView('landing')} />;
  return <LandingPage onGetStarted={() => setView('auth')} />;
};

export default Index;
