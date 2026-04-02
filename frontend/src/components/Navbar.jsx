import styles from './Navbar.module.css'

export default function Navbar({ user, onLogout }) {
  const initials = user?.name
    ? user.name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
    : 'AG'

  return (
    <header className={styles.nav}>
      <div className={styles.logo}>
        <div className={styles.icon}>🛡️</div>
        <span>AutoGuard</span>
      </div>
      <div className={styles.right}>
        <div className={styles.avatar}>{initials}</div>
        <span className={styles.name}>{user?.name}</span>
        <button className={styles.logout} onClick={onLogout}>Log Out</button>
      </div>
    </header>
  )
}
