// FILE: src/components/ui/BookCard.tsx
import { motion } from 'framer-motion'
import { Heart, BookOpen } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { Book } from '@/types'
import StarRating from './StarRating'
import { truncate } from '@/utils'

interface BookCardProps {
  book: Book
  onFavourite?: (id: string) => void
  isFavourited?: boolean
}

const COVER_GRADIENTS = [
  'from-purple-600 to-blue-600',
  'from-blue-600 to-cyan-500',
  'from-violet-600 to-purple-600',
  'from-indigo-600 to-blue-500',
  'from-fuchsia-600 to-purple-600',
  'from-sky-500 to-indigo-600',
]

function getGradient(title: string) {
  const idx = title.charCodeAt(0) % COVER_GRADIENTS.length
  return COVER_GRADIENTS[idx]
}

export default function BookCard({ book, onFavourite, isFavourited }: BookCardProps) {
  const navigate = useNavigate()

  return (
    <motion.div
      whileHover={{ y: -6, scale: 1.02 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      className="group cursor-pointer relative flex flex-col rounded-2xl border border-[#1e2d4a] bg-[#0f1629] overflow-hidden hover:border-purple-500/40 hover:shadow-xl hover:shadow-purple-500/10 transition-all duration-300"
      onClick={() => navigate(`/books/${book.id}`)}
    >
      {/* Cover */}
      <div className="relative h-52 overflow-hidden">
        {book.cover_url ? (
          <img
            src={book.cover_url}
            alt={book.title}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
          />
        ) : (
          <div
            className={`w-full h-full bg-gradient-to-br ${getGradient(book.title)} flex items-center justify-center`}
          >
            <span className="text-5xl font-bold text-white/30 select-none">
              {book.title[0].toUpperCase()}
            </span>
          </div>
        )}

        {/* Overlay badges */}
        <div className="absolute top-2 left-2 flex gap-1 flex-wrap">
          {book.is_featured && (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-purple-600 text-white">
              Featured
            </span>
          )}
          {book.is_trending && (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-orange-500 text-white">
              Trending
            </span>
          )}
          {book.is_new_arrival && (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-green-600 text-white">
              New
            </span>
          )}
        </div>

        {/* Favourite button */}
        {onFavourite && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onFavourite(book.id)
            }}
            className="absolute top-2 right-2 p-1.5 rounded-full bg-black/40 backdrop-blur-sm border border-white/10 hover:border-red-400/50 transition-all duration-200 opacity-0 group-hover:opacity-100"
          >
            <Heart
              size={14}
              className={isFavourited ? 'text-red-400 fill-red-400' : 'text-white'}
            />
          </button>
        )}

        {/* Gradient overlay at bottom */}
        <div className="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-[#0f1629] to-transparent" />
      </div>

      {/* Content */}
      <div className="flex flex-col flex-1 p-4 gap-2">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold text-slate-100 text-sm leading-snug line-clamp-2">
            {truncate(book.title, 60)}
          </h3>
        </div>

        {book.author && (
          <p className="text-xs text-slate-400">{book.author.name}</p>
        )}

        <div className="flex items-center gap-1.5 mt-0.5">
          <StarRating rating={book.average_rating} size="sm" />
          <span className="text-xs text-slate-400">
            {book.average_rating.toFixed(1)} ({book.total_ratings})
          </span>
        </div>

        <div className="flex items-center gap-1.5 flex-wrap mt-1">
          {book.category && (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-purple-500/15 text-purple-400 border border-purple-500/20">
              {book.category.name}
            </span>
          )}
          <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-blue-500/15 text-blue-400 border border-blue-500/20">
            {book.language}
          </span>
        </div>

        <button
          onClick={(e) => {
            e.stopPropagation()
            navigate(`/books/${book.id}`)
          }}
          className="mt-auto pt-3 w-full flex items-center justify-center gap-2 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-blue-500 text-white text-xs font-semibold opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:opacity-90"
        >
          <BookOpen size={13} />
          Read Now
        </button>
      </div>
    </motion.div>
  )
}

