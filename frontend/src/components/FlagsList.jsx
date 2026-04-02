import styles from './FlagsList.module.css'

const severityMap = {
  red:    { cls: styles.red,    dot: styles.dotRed    },
  yellow: { cls: styles.yellow, dot: styles.dotYellow },
  green:  { cls: styles.green,  dot: styles.dotGreen  },
}

export default function FlagsList({ flags }) {
  if (!flags?.length) return null

  return (
    <div className={styles.panel}>
      <div className={styles.title}>🚩 Contract Flags</div>
      {flags.map((f, i) => {
        const s = severityMap[f.severity] || severityMap.yellow
        return (
          <div key={i} className={`${styles.flag} ${s.cls}`}>
            <div className={`${styles.dot} ${s.dot}`} />
            <span>{f.message}</span>
          </div>
        )
      })}
    </div>
  )
}
