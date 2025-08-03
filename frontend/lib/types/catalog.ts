// Book and catalog related types

export interface Book {
  id: string
  title: string
  subtitle?: string
  description: string
  isbn?: string
  language: string
  publishedDate: string
  pageCount: number
  format: 'pdf' | 'epub' | 'audiobook'
  fileSize: number
  coverImage: string
  thumbnailImage?: string
  price: number
  currency: string
  isFree: boolean
  isAvailable: boolean
  downloadUrl?: string
  streamingUrl?: string
  previewUrl?: string
  
  // Relationships
  authors: Author[]
  categories: Category[]
  publisher: Publisher
  
  // Metadata
  rating: number
  reviewCount: number
  downloadCount: number
  tags: string[]
  
  // Timestamps
  createdAt: string
  updatedAt: string
  
  // User-specific data (populated when user is authenticated)
  isPurchased?: boolean
  isInLibrary?: boolean
  isFavorite?: boolean
  readingProgress?: number
  lastReadAt?: string
}

export interface Author {
  id: string
  name: string
  biography?: string
  profileImage?: string
  nationality?: string
  birthDate?: string
  deathDate?: string
  website?: string
  socialLinks?: {
    twitter?: string
    facebook?: string
    instagram?: string
    linkedin?: string
  }
  bookCount: number
  createdAt: string
  updatedAt: string
}

export interface Category {
  id: string
  name: string
  description?: string
  slug: string
  parentId?: string
  children?: Category[]
  bookCount: number
  isActive: boolean
  sortOrder: number
  createdAt: string
  updatedAt: string
}

export interface Publisher {
  id: string
  name: string
  description?: string
  logo?: string
  website?: string
  email?: string
  address?: string
  country: string
  foundedYear?: number
  bookCount: number
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface SearchFilters {
  query?: string
  categories?: string[]
  authors?: string[]
  publishers?: string[]
  languages?: string[]
  formats?: ('pdf' | 'epub' | 'audiobook')[]
  priceRange?: {
    min: number
    max: number
  }
  isFree?: boolean
  rating?: number
  publishedAfter?: string
  publishedBefore?: string
  tags?: string[]
  sortBy?: 'relevance' | 'title' | 'author' | 'publishedDate' | 'rating' | 'price' | 'downloadCount'
  sortOrder?: 'asc' | 'desc'
}

export interface PaginationMeta {
  currentPage: number
  totalPages: number
  totalItems: number
  itemsPerPage: number
  hasNextPage: boolean
  hasPreviousPage: boolean
}

export interface SearchResult {
  books: Book[]
  pagination: PaginationMeta
  filters: SearchFilters
  totalResults: number
  searchTime: number
  suggestions?: string[]
}

export interface FeaturedContent {
  id: string
  type: 'book' | 'author' | 'category' | 'collection'
  title: string
  description?: string
  image: string
  targetId: string
  targetType: 'book' | 'author' | 'category' | 'collection'
  priority: number
  isActive: boolean
  startDate?: string
  endDate?: string
  createdAt: string
  updatedAt: string
}

export interface Collection {
  id: string
  name: string
  description?: string
  coverImage?: string
  isPublic: boolean
  bookIds: string[]
  books?: Book[]
  createdBy: string
  createdAt: string
  updatedAt: string
}

export interface Review {
  id: string
  bookId: string
  userId: string
  userName: string
  userAvatar?: string
  rating: number
  title?: string
  content: string
  isVerifiedPurchase: boolean
  helpfulCount: number
  isHelpful?: boolean
  createdAt: string
  updatedAt: string
}

export interface BookStats {
  totalBooks: number
  totalAuthors: number
  totalCategories: number
  totalPublishers: number
  totalDownloads: number
  averageRating: number
  mostPopularBooks: Book[]
  mostPopularAuthors: Author[]
  mostPopularCategories: Category[]
  recentlyAdded: Book[]
}

// API Response types
export interface BooksResponse {
  data: Book[]
  pagination: PaginationMeta
  success: boolean
  message?: string
}

export interface BookResponse {
  data: Book
  success: boolean
  message?: string
}

export interface AuthorsResponse {
  data: Author[]
  pagination: PaginationMeta
  success: boolean
  message?: string
}

export interface AuthorResponse {
  data: Author
  success: boolean
  message?: string
}

export interface CategoriesResponse {
  data: Category[]
  pagination?: PaginationMeta
  success: boolean
  message?: string
}

export interface CategoryResponse {
  data: Category
  success: boolean
  message?: string
}

export interface PublishersResponse {
  data: Publisher[]
  pagination: PaginationMeta
  success: boolean
  message?: string
}

export interface PublisherResponse {
  data: Publisher
  success: boolean
  message?: string
}

export interface SearchResponse {
  data: SearchResult
  success: boolean
  message?: string
}

export interface FeaturedContentResponse {
  data: FeaturedContent[]
  success: boolean
  message?: string
}

export interface BookStatsResponse {
  data: BookStats
  success: boolean
  message?: string
}

export interface ReviewsResponse {
  data: Review[]
  pagination: PaginationMeta
  success: boolean
  message?: string
}

// Error types
export interface CatalogError {
  code: string
  message: string
  details?: Record<string, any>
}

// Utility types
export type BookFormat = 'pdf' | 'epub' | 'audiobook'
export type SortOption = 'relevance' | 'title' | 'author' | 'publishedDate' | 'rating' | 'price' | 'downloadCount'
export type SortOrder = 'asc' | 'desc'
export type ContentType = 'book' | 'author' | 'category' | 'collection'

// Form types for creating/updating
export interface CreateBookRequest {
  title: string
  subtitle?: string
  description: string
  isbn?: string
  language: string
  publishedDate: string
  pageCount: number
  format: BookFormat
  price: number
  currency: string
  isFree: boolean
  authorIds: string[]
  categoryIds: string[]
  publisherId: string
  tags: string[]
  coverImage: File | string
  bookFile: File
}

export interface UpdateBookRequest extends Partial<CreateBookRequest> {
  id: string
}

export interface CreateAuthorRequest {
  name: string
  biography?: string
  profileImage?: File | string
  nationality?: string
  birthDate?: string
  deathDate?: string
  website?: string
  socialLinks?: Author['socialLinks']
}

export interface UpdateAuthorRequest extends Partial<CreateAuthorRequest> {
  id: string
}

export interface CreateCategoryRequest {
  name: string
  description?: string
  slug: string
  parentId?: string
  sortOrder: number
}

export interface UpdateCategoryRequest extends Partial<CreateCategoryRequest> {
  id: string
}

export interface CreatePublisherRequest {
  name: string
  description?: string
  logo?: File | string
  website?: string
  email?: string
  address?: string
  country: string
  foundedYear?: number
}

export interface UpdatePublisherRequest extends Partial<CreatePublisherRequest> {
  id: string
}