import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.js'
import Navbar from '../components/Navbar.jsx'
import UploadZone from '../components/UploadZone.jsx'
import FairnessScore from '../components/FairnessScore.jsx'
import SLAGrid from '../components/SLAGrid.jsx'
import FlagsList from '../components/FlagsList.jsx'
import VINLookup from '../components/VINLookup.jsx'
import ChatBot from '../components/ChatBot.jsx'
import styles from './DashboardPage.module.css'

export default function DashboardPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const [contractId,    setContractId]    = useState(null)
  const [analysisResult,setAnalysisResult]= useState(null)   // { fairness_score, sla, flags }
  const [analyzing,     setAnalyzing]     = useState(false)

  function handleLogout() {
    logout()
    navigate('/login')
  }

  function handleAnalysisComplete(result, cId) {
    setAnalysisResult(result)
    setContractId(cId)
  }

  return (
    <div className={styles.page}>
      <Navbar user={user} onLogout={handleLogout} />

      <div className={styles.layout}>
        {/* ── LEFT COLUMN ── */}
        <div className={styles.left}>
          <UploadZone
            onAnalysisComplete={handleAnalysisComplete}
            analyzing={analyzing}
            setAnalyzing={setAnalyzing}
          />

          {analysisResult && (
            <>
              <FairnessScore score={analysisResult.fairness_score} />
              <FlagsList flags={analysisResult.flags} />
              <SLAGrid sla={analysisResult.sla} />
            </>
          )}

          <VINLookup contractId={contractId} />
        </div>

        {/* ── RIGHT COLUMN ── */}
        <div className={styles.right}>
          <ChatBot contractId={contractId} sla={analysisResult?.sla} score={analysisResult?.fairness_score} />
        </div>
      </div>
    </div>
  )
}
