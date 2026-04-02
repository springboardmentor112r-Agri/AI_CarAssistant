import styles from './FairnessScore.module.css'

function getColor(score) {
  if (score >= 75) return '#00e5a0'
  if (score >= 50) return '#ffb347'
  return '#ff4f6a'
}

function getLabel(score) {
  if (score >= 75) return 'Fair Contract'
  if (score >= 50) return 'Negotiable Terms Detected'
  return 'Unfair — Strong Action Needed'
}

export default function FairnessScore({ score }) {
  if (score == null) return null
  const color = getColor(score)
  const circumference = 2 * Math.PI * 48
  const offset = circumference - (score / 100) * circumference

  return (
    <div className={styles.panel}>
      <div className={styles.title}>⚡ Contract Fairness Score</div>
      <div className={styles.wrap}>
        <div className={styles.circle}>
          <svg width="110" height="110" viewBox="0 0 110 110">
            <circle cx="55" cy="55" r="48" fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="10" />
            <circle
              cx="55" cy="55" r="48"
              fill="none"
              stroke={color}
              strokeWidth="10"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              strokeLinecap="round"
              transform="rotate(-90 55 55)"
            />
          </svg>
          <div className={styles.scoreText}>
            <span className={styles.num} style={{ color }}>{score}</span>
            <span className={styles.sub}>/ 100</span>
          </div>
        </div>
        <div className={styles.details}>
          <h3 style={{ color }}>{getLabel(score)}</h3>
          <p>Review the flags below and use the AI assistant to get negotiation strategies for unfair terms.</p>
        </div>
      </div>
    </div>
  )
}
