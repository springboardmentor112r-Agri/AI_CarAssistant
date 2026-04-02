import { useState, useRef } from 'react'
import { contractAPI, extractionAPI } from '../services/api.js'
import styles from './UploadZone.module.css'

const STEPS = [
  'Reading document…',
  'Extracting text with OCR…',
  'Sending to AI for analysis…',
  'Computing fairness score…',
  'Generating flags…',
  'Done!',
]

export default function UploadZone({ onAnalysisComplete, analyzing, setAnalyzing }) {
  const [progress,  setProgress]  = useState(0)
  const [stepText,  setStepText]  = useState('')
  const [dragOver,  setDragOver]  = useState(false)
  const [fileName,  setFileName]  = useState('')
  const inputRef = useRef()

  async function processFile(file) {
    if (!file) return
    setFileName(file.name)
    setAnalyzing(true)
    setProgress(0)

    try {
      // Step 1-2: upload + OCR
      setStepText(STEPS[0]); setProgress(15)
      const uploaded = await contractAPI.upload(file)
      setStepText(STEPS[1]); setProgress(35)

      // Step 3-4: LLM analysis
      setStepText(STEPS[2]); setProgress(55)
      await new Promise(r => setTimeout(r, 400))
      setStepText(STEPS[3]); setProgress(70)
      const result = await extractionAPI.analyze(uploaded.contract_id)

      setStepText(STEPS[4]); setProgress(88)
      await new Promise(r => setTimeout(r, 300))
      setStepText(STEPS[5]); setProgress(100)

      await new Promise(r => setTimeout(r, 500))
      onAnalysisComplete(result, uploaded.contract_id)
    } catch (err) {
      setStepText('Error: ' + err.message)
    } finally {
      setAnalyzing(false)
    }
  }

  function handleDrop(e) {
    e.preventDefault(); setDragOver(false)
    processFile(e.dataTransfer.files[0])
  }

  return (
    <div className={styles.panel}>
      <div className={styles.title}>📄 Upload Contract <span className={styles.pill}>PDF / Image</span></div>

      <div
        className={`${styles.zone} ${dragOver ? styles.dragOver : ''}`}
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg"
          style={{ display: 'none' }}
          onChange={e => processFile(e.target.files[0])}
        />
        <div className={styles.zoneIcon}>📁</div>
        <div className={styles.zoneTitle}>Drop your lease or loan contract here</div>
        <div className={styles.zoneSub}>Supports PDF, PNG, JPG formats</div>
        <div className={styles.zoneBtn}>Browse Files</div>
      </div>

      {analyzing && (
        <div className={styles.progress}>
          <div className={styles.progressTop}>
            <div className={styles.spinner} />
            <span>{stepText}</span>
          </div>
          <div className={styles.bar}><div className={styles.fill} style={{ width: `${progress}%` }} /></div>
        </div>
      )}

      {fileName && !analyzing && (
        <div className={styles.done}>✅ Analyzed: <strong>{fileName}</strong></div>
      )}
    </div>
  )
}
