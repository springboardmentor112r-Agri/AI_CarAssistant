import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authAPI } from '../services/api.js'
import { useAuth } from '../hooks/useAuth.js'
import styles from './LoginPage.module.css'

export default function LoginPage() {
  const [tab,    setTab]    = useState('login')
  const [error,  setError]  = useState('')
  const [loading,setLoading]= useState(false)
  const { login } = useAuth()
  const navigate   = useNavigate()

  const [loginForm, setLoginForm] = useState({ email: '', password: '' })
  const [regForm,   setRegForm]   = useState({ full_name: '', email: '', password: '', confirm: '' })

  async function handleLogin(e) {
    e.preventDefault(); setError(''); setLoading(true)
    try {
      const data = await authAPI.login({ email: loginForm.email, password: loginForm.password })
      login(data.token, { id: data.user_id, name: data.full_name, email: data.email })
      navigate('/dashboard')
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  async function handleRegister(e) {
    e.preventDefault(); setError(''); setLoading(true)
    if (regForm.password !== regForm.confirm) { setError('Passwords do not match'); setLoading(false); return }
    try {
      const data = await authAPI.register({ full_name: regForm.full_name, email: regForm.email, password: regForm.password })
      login(data.token, { id: data.user_id, name: data.full_name, email: data.email })
      navigate('/dashboard')
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  return (
    <div className={styles.page}>
      <div className={styles.bg} />
      <div className={styles.grid} />
      <div className={styles.container}>
        <div className={styles.logo}>
          <div className={styles.logoIcon}>🛡️</div>
          <h1>AutoGuard</h1>
          <p>AI-Powered Car Lease Review & Negotiation</p>
        </div>

        <div className={styles.card}>
          <div className={styles.tabs}>
            <button className={tab === 'login'    ? styles.tabActive : styles.tab} onClick={() => { setTab('login');    setError('') }}>Sign In</button>
            <button className={tab === 'register' ? styles.tabActive : styles.tab} onClick={() => { setTab('register'); setError('') }}>Register</button>
          </div>

          {error && <div className={styles.error}>{error}</div>}

          {tab === 'login' ? (
            <form onSubmit={handleLogin}>
              <div className={styles.field}>
                <label>Email Address</label>
                <input type="email" placeholder="you@example.com" required
                  value={loginForm.email} onChange={e => setLoginForm(p => ({ ...p, email: e.target.value }))} />
              </div>
              <div className={styles.field}>
                <label>Password</label>
                <input type="password" placeholder="Enter your password" required
                  value={loginForm.password} onChange={e => setLoginForm(p => ({ ...p, password: e.target.value }))} />
              </div>
              <button type="submit" className={styles.btnPrimary} disabled={loading}>
                {loading ? 'Signing in…' : 'Sign In to AutoGuard'}
              </button>
              <p className={styles.cta}>
                Don't have an account?{' '}
                <span onClick={() => setTab('register')}>Register Now →</span>
              </p>
            </form>
          ) : (
            <form onSubmit={handleRegister}>
              <div className={styles.field}>
                <label>Full Name</label>
                <input type="text" placeholder="John Smith" required
                  value={regForm.full_name} onChange={e => setRegForm(p => ({ ...p, full_name: e.target.value }))} />
              </div>
              <div className={styles.field}>
                <label>Email Address</label>
                <input type="email" placeholder="you@example.com" required
                  value={regForm.email} onChange={e => setRegForm(p => ({ ...p, email: e.target.value }))} />
              </div>
              <div className={styles.field}>
                <label>Password</label>
                <input type="password" placeholder="Create a password" required
                  value={regForm.password} onChange={e => setRegForm(p => ({ ...p, password: e.target.value }))} />
              </div>
              <div className={styles.field}>
                <label>Confirm Password</label>
                <input type="password" placeholder="Repeat your password" required
                  value={regForm.confirm} onChange={e => setRegForm(p => ({ ...p, confirm: e.target.value }))} />
              </div>
              <button type="submit" className={styles.btnPrimary} disabled={loading}>
                {loading ? 'Creating account…' : 'Create My Account'}
              </button>
              <p className={styles.cta}>
                Already have an account?{' '}
                <span onClick={() => setTab('login')}>Sign In</span>
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
