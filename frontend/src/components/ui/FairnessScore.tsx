import { clsx } from 'clsx'

interface Props {
  score: number
  size?: 'sm' | 'md' | 'lg'
}

const colors = {
  good: 'text-green-600',
  ok: 'text-yellow-600',
  bad: 'text-red-600',
}

export default function FairnessScore({ score, size = 'md' }: Props) {
  const color = score >= 70 ? colors.good : score >= 45 ? colors.ok : colors.bad
  const bgColor = score >= 70 ? 'bg-green-50 border-green-200' : score >= 45 ? 'bg-yellow-50 border-yellow-200' : 'bg-red-50 border-red-200'
  const label = score >= 70 ? 'Fair Deal' : score >= 45 ? 'Average' : 'Unfavorable'

  const sizes = {
    sm: 'w-16 h-16 text-xl',
    md: 'w-24 h-24 text-3xl',
    lg: 'w-32 h-32 text-4xl',
  }

  return (
    <div className={clsx('rounded-full border-4 flex flex-col items-center justify-center', bgColor, sizes[size])}>
      <span className={clsx('font-bold', color)}>{Math.round(score)}</span>
      <span className={clsx('text-xs font-medium', color)}>{label}</span>
    </div>
  )
}