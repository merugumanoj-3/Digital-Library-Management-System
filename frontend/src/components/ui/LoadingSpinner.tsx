// FILE: src/components/ui/LoadingSpinner.tsx
import { cn } from '@/utils'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  text?: string
  className?: string
}

const sizeMap = { sm: 'h-5 w-5', md: 'h-9 w-9', lg: 'h-14 w-14' }

export default function LoadingSpinner({ size = 'md', text, className }: LoadingSpinnerProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-3', className)}>
      <div
        className={cn(
          'rounded-full border-[3px] border-transparent animate-spin',
          sizeMap[size]
        )}
        style={{
          borderTopColor: '#7c3aed',
          borderRightColor: '#3b82f6',
          background: 'transparent',
        }}
      />
      {text && <p className="text-sm text-slate-400 animate-pulse">{text}</p>}
    </div>
  )
}

