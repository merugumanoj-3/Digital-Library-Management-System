// FILE: src/components/ui/Button.tsx
import { forwardRef } from 'react'
import { motion } from 'framer-motion'
import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { cn } from '@/utils'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'
type Size = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
  fullWidth?: boolean
  children: ReactNode
}

const variantClasses: Record<Variant, string> = {
  primary:
    'bg-gradient-to-r from-purple-600 to-blue-500 text-white hover:opacity-90 shadow-lg shadow-purple-500/20',
  secondary:
    'border border-purple-500/50 text-purple-400 hover:bg-purple-500/10 bg-transparent',
  ghost: 'text-slate-300 hover:text-white hover:bg-white/5 bg-transparent',
  danger: 'bg-red-500/10 border border-red-500/50 text-red-400 hover:bg-red-500/20',
}

const sizeClasses: Record<Size, string> = {
  sm: 'px-3 py-1.5 text-sm rounded-lg gap-1.5',
  md: 'px-5 py-2.5 text-sm rounded-xl gap-2',
  lg: 'px-7 py-3.5 text-base rounded-xl gap-2.5',
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', loading = false, fullWidth = false, children, className, disabled, ...rest }, ref) => {
    return (
      <motion.button
        ref={ref}
        whileHover={{ scale: disabled || loading ? 1 : 1.02, y: disabled || loading ? 0 : -1 }}
        whileTap={{ scale: disabled || loading ? 1 : 0.97 }}
        className={cn(
          'inline-flex items-center justify-center font-semibold transition-all duration-200 cursor-pointer focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:ring-offset-2 focus:ring-offset-transparent disabled:opacity-50 disabled:cursor-not-allowed select-none',
          variantClasses[variant],
          sizeClasses[size],
          fullWidth && 'w-full',
          className
        )}
        disabled={disabled || loading}
        {...(rest as React.ComponentProps<typeof motion.button>)}
      >
        {loading && (
          <svg
            className="animate-spin h-4 w-4 shrink-0"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
        )}
        {children}
      </motion.button>
    )
  }
)

Button.displayName = 'Button'
export default Button

