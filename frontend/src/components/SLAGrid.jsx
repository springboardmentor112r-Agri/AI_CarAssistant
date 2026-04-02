import styles from './SLAGrid.module.css'

function fmt(val, prefix = '', suffix = '') {
  if (val == null) return '—'
  return `${prefix}${val}${suffix}`
}

export default function SLAGrid({ sla }) {
  if (!sla) return null

  const fields = [
    { key: 'APR',          val: fmt(sla.apr,                '',  '%'),  flag: sla.apr > 7 },
    { key: 'Monthly',      val: fmt(sla.monthly_payment,    '$', ''),   flag: false },
    { key: 'Term',         val: fmt(sla.term_months,        '',  ' mo'),flag: false },
    { key: 'Down Payment', val: fmt(sla.down_payment,       '$', ''),   flag: sla.down_payment > 3000 },
    { key: 'Mileage/yr',   val: fmt(sla.mileage_allowance,  '',  '/yr'),flag: false },
    { key: 'Overage/mi',   val: fmt(sla.mileage_overage_fee,'$', '/mi'),flag: sla.mileage_overage_fee > 0.20 },
    { key: 'Residual',     val: fmt(sla.residual_value,     '',  '%'),  flag: false, ok: sla.residual_value >= 48 && sla.residual_value <= 58 },
    { key: 'Buyout',       val: fmt(sla.buyout_price,       '$', ''),   flag: false },
    { key: 'Early Exit',   val: fmt(sla.early_termination,  '$', ''),   flag: sla.early_termination > 2000 },
    { key: 'Warranty',     val: sla.warranty_summary || '—',            flag: false },
  ]

  return (
    <div className={styles.panel}>
      <div className={styles.title}>📊 Extracted Contract Terms</div>
      <div className={styles.grid}>
        {fields.map(f => (
          <div key={f.key} className={styles.card}>
            <div className={styles.key}>{f.key}</div>
            <div className={`${styles.val} ${f.flag ? styles.flagRed : ''} ${f.ok ? styles.flagGreen : ''}`}>
              {f.val}
            </div>
          </div>
        ))}
      </div>
      <p className={styles.legend}>🔴 Above market &nbsp;·&nbsp; 🟢 Fair &nbsp;·&nbsp; Grey = neutral</p>
    </div>
  )
}
