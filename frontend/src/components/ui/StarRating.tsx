// FILE: src/components/ui/StarRating.tsx
import { Star } from 'lucide-react'
import { cn } from '@/utils'

interface StarRatingProps {
  rating: number
  size?: 'sm' | 'md' | 'lg'
}

const sizeMap = { sm: 12, md: 16, lg: 20 }

export default function StarRating({ rating, size = 'sm' }: StarRatingProps) {
  const px = sizeMap[size]
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((star) => {
        const filled = rating >= star
        const half = !filled && rating >= star - 0.5
        return (
          <span key={star} className="relative" style={{ width: px, height: px }}>
            <Star
              size={px}
              className={cn(
                'absolute inset-0',
                filled ? 'text-amber-400 fill-amber-400' : 'text-slate-600'
              )}
            />
            {half && (
              <span
                className="absolute inset-0 overflow-hidden"
                style={{ width: '50%' }}
              >
                <Star size={px} className="text-amber-400 fill-amber-400" />
              </span>
            )}
          </span>
        )
      })}
    </div>
  )
}

