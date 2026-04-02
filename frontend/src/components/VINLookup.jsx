import { useState } from 'react'
import { vinAPI } from '../services/api.js'
import styles from './VINLookup.module.css'

export default function VINLookup() {
  const [vin,     setVin]     = useState('')
  const [result,  setResult]  = useState(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')

  async function handleLookup() {
    const v = vin.trim().toUpperCase()
    if (v.length !== 17) { setError('VIN must be exactly 17 characters'); return }
    setError(''); setLoading(true); setResult(null)
    try {
      const data = await vinAPI.lookup(v)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.panel}>
      <div className={styles.title}>🔍 VIN Vehicle Lookup</div>

      <div className={styles.row}>
        <input
          className={styles.vinInput}
          placeholder="Enter 17-character VIN code"
          maxLength={17}
          value={vin}
          onChange={e => setVin(e.target.value.toUpperCase())}
          onKeyDown={e => e.key === 'Enter' && handleLookup()}
        />
        <button className={styles.btn} onClick={handleLookup} disabled={loading}>
          {loading ? '…' : 'Look Up'}
        </button>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {result && (
        <div className={styles.result}>
          <div className={styles.carTitle}>
            {result.year} {result.make} {result.model} {result.trim}
          </div>
          <div className={styles.specs}>
            {[
              ['Make',      result.make],
              ['Model',     result.model],
              ['Year',      result.year],
              ['Engine',    result.engine],
              ['Body Type', result.body_class],
              ['Drive',     result.drive_type],
              ['Fuel',      result.fuel_type],
              ['Country',   result.country],
            ].map(([k, v]) => v && (
              <div key={k} className={styles.spec}>
                <div className={styles.specKey}>{k}</div>
                <div className={styles.specVal}>{v}</div>
              </div>
            ))}
          </div>

          {result.recall_count > 0 ? (
            <div className={styles.badgeWarn}>
              ⚠ {result.recall_count} Active Recall{result.recall_count > 1 ? 's' : ''} Found
            </div>
          ) : (
            <div className={styles.badgeSafe}>✓ No Active Recalls</div>
          )}

          {result.recalls?.length > 0 && (
            <div className={styles.recallList}>
              {result.recalls.map((r, i) => (
                <div key={i} className={styles.recallItem}>
                  <strong>{r.component}</strong>: {r.summary}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
