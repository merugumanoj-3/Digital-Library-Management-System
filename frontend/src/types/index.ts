// TypeScript types for LIBRIX AI

export type UserRole = 'student' | 'admin' | 'librarian';

export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  role: UserRole;
  avatar_url?: string;
  bio?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface Author {
  id: string;
  name: string;
  bio?: string;
  photo_url?: string;
  nationality?: string;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string;
  icon?: string;
  color?: string;
  book_count?: number;
}

export interface Book {
  id: string;
  title: string;
  description?: string;
  isbn?: string;
  publication_year?: number;
  language: string;
  pages?: number;
  cover_url?: string;
  average_rating: number;
  total_ratings: number;
  total_reads: number;
  is_featured: boolean;
  is_trending: boolean;
  is_new_arrival: boolean;
  tags: string[];
  author?: Author;
  category?: Category;
  created_at: string;
}

export interface BookListResponse {
  books: Book[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ReadingHistory {
  id: string;
  book: Book;
  current_page: number;
  total_pages?: number;
  progress_percent: number;
  is_completed: boolean;
  last_read_at: string;
}

export interface Bookmark {
  id: string;
  book_id: string;
  page_number: number;
  label?: string;
  created_at: string;
}

export interface Highlight {
  id: string;
  book_id: string;
  page_number: number;
  selected_text: string;
  color: string;
  note?: string;
  created_at: string;
}

export interface Review {
  id: string;
  rating: number;
  comment?: string;
  user: User;
  created_at: string;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  is_read: boolean;
  link?: string;
  created_at: string;
}

export interface DashboardStats {
  total_books: number;
  currently_reading: number;
  completed_books: number;
  total_reading_time_hours: number;
  reading_streak_days: number;
  favourite_count: number;
}

export interface AdminStats {
  total_books: number;
  total_users: number;
  total_reading_sessions: number;
  books_added_this_month: number;
  new_users_this_month: number;
  most_read_books: { title: string; reads: number }[];
  popular_categories: { name: string; count: number }[];
  monthly_activity: Record<string, unknown>[];
}

export interface AIChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: { page: number; excerpt: string }[];
  timestamp: Date;
}

export interface MCQQuestion {
  question: string;
  options: string[];
  correct_answer: number;
  explanation: string;
  page_reference?: number;
}

export interface ApiError {
  detail: string;
}
