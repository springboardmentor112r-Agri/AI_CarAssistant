import { clsx } from 'clsx'

export default function Spinner({ className }: { className?: string }) {
  return (
    <div className={clsx('inline-block w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin', className)} />
  )
}