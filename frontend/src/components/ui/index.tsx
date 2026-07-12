import { cn } from '@/lib/utils'
import { forwardRef } from 'react'

// ── Button ────────────────────────────────────────────────────────────────────
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'ghost' | 'danger' | 'outline'
  size?: 'sm' | 'md' | 'lg'
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center gap-2 font-semibold rounded-lg transition-all duration-150 cursor-pointer',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          {
            // primary — use the `background` shorthand (arbitrary property) so the
            // orange gradient in --btn-primary-bg renders; `bg-[..]` maps to
            // background-color, which silently drops a gradient value.
            '[background:var(--btn-primary-bg)] text-[var(--btn-primary-text)] hover:opacity-90 shadow-sm hover:-translate-y-px':
              variant === 'primary',
            // ghost
            'bg-[var(--surface-2)] border border-[var(--border)] text-[var(--ink-2)] hover:border-[var(--border-2)] hover:text-[var(--ink)]':
              variant === 'ghost',
            // outline
            'border border-[var(--border-2)] bg-transparent text-[var(--ink-2)] hover:bg-[var(--surface-2)]':
              variant === 'outline',
            // danger
            'bg-[var(--red-dim)] text-[var(--red)] border border-[var(--red-dim)] hover:bg-[var(--red-soft)]':
              variant === 'danger',
            // sizes
            'text-xs px-3 py-1.5': size === 'sm',
            'text-sm px-4 py-2': size === 'md',
            'text-sm px-5 py-2.5': size === 'lg',
          },
          className
        )}
        {...props}
      >
        {children}
      </button>
    )
  }
)
Button.displayName = 'Button'

// ── Card ─────────────────────────────────────────────────────────────────────
export function Card({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'bg-[var(--surface)] border border-[var(--border)] rounded-xl overflow-hidden',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardHeader({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'flex items-center justify-between px-5 py-3.5 border-b border-[var(--border)]',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardTitle({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('text-sm font-bold tracking-tight text-[var(--ink)]', className)} {...props}>
      {children}
    </div>
  )
}

export function CardSub({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('text-xs text-[var(--ink-3)] mt-0.5', className)} {...props}>
      {children}
    </div>
  )
}

// ── Status Pill ───────────────────────────────────────────────────────────────
type PillVariant = 'filed' | 'due' | 'overdue' | 'review' | 'ai' | 'final' | 'pending'

export function StatusPill({ variant, children }: { variant: PillVariant; children: React.ReactNode }) {
  return (
    <span className={`pill pill-${variant}`}>
      <span className="pill-dot" />
      {children}
    </span>
  )
}

// ── Input ─────────────────────────────────────────────────────────────────────
export const Input = forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        'w-full px-3 py-2 rounded-lg text-sm',
        'bg-[var(--canvas)] border border-[var(--border)]',
        'text-[var(--ink)] placeholder:text-[var(--ink-4)]',
        'focus:outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent-dim)]',
        'transition-all duration-150',
        className
      )}
      {...props}
    />
  )
)
Input.displayName = 'Input'

// ── Select ────────────────────────────────────────────────────────────────────
export const Select = forwardRef<HTMLSelectElement, React.SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        'w-full px-3 py-2 rounded-lg text-sm',
        'bg-[var(--canvas)] border border-[var(--border)]',
        'text-[var(--ink)]',
        'focus:outline-none focus:border-[var(--accent)]',
        className
      )}
      {...props}
    >
      {children}
    </select>
  )
)
Select.displayName = 'Select'

// ── Skeleton ──────────────────────────────────────────────────────────────────
export function Skeleton({ className }: { className?: string }) {
  return <div className={cn('skeleton', className)} />
}

// ── Score Bar ─────────────────────────────────────────────────────────────────
export function ScoreBar({ score }: { score: number }) {
  const color = score >= 80 ? 'var(--forest-3)' : score >= 60 ? 'var(--amber-2)' : 'var(--red)'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1 bg-[var(--border)] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${score}%`, background: color }}
        />
      </div>
      <span className="num text-xs font-semibold min-w-[24px] text-right" style={{ color }}>
        {score}
      </span>
    </div>
  )
}

// ── Badge ─────────────────────────────────────────────────────────────────────
export function Badge({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold',
        'bg-[var(--forest-dim)] text-[var(--forest-2)]',
        className
      )}
    >
      {children}
    </span>
  )
}

// ── Divider ───────────────────────────────────────────────────────────────────
export function Divider({ className }: { className?: string }) {
  return <div className={cn('border-t border-[var(--border)]', className)} />
}

// ── Empty State ───────────────────────────────────────────────────────────────
export function EmptyState({
  icon,
  title,
  body,
  action,
}: {
  icon?: React.ReactNode
  title: string
  body?: string
  action?: React.ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center px-6">
      {icon && <div className="text-3xl mb-3 opacity-40">{icon}</div>}
      <div className="font-semibold text-[var(--ink)] mb-1">{title}</div>
      {body && <div className="text-sm text-[var(--ink-3)] mb-4 max-w-xs">{body}</div>}
      {action}
    </div>
  )
}
