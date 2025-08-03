import { apiClient } from './client'
import {
  SearchFilters,
  Review,
  BooksResponse,
  BookResponse,
  AuthorsResponse,
  AuthorResponse,
  CategoriesResponse,
  CategoryResponse,
  PublishersResponse,
  PublisherResponse,
  SearchResponse,
  FeaturedContentResponse,
  BookStatsResponse,
  ReviewsResponse,
  CreateBookRequest,
  UpdateBookRequest,
  CreateAuthorRequest,
  UpdateAuthorRequest,
  CreateCategoryRequest,
  UpdateCategoryRequest,
  CreatePublisherRequest,
  UpdatePublisherRequest
} from '@/lib/types/catalog'

export class CatalogAPI {
  // Books
  static async getBooks(params?: {
    page?: number
    limit?: number
    category?: string
    author?: string
    publisher?: string
    language?: string
    format?: string
    sortBy?: string
    sortOrder?: 'asc' | 'desc'
  }): Promise<BooksResponse> {
    const searchParams = new URLSearchParams()
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value.toString())
        }
      })
    }
    
    const response = await apiClient.get(`/catalog/books?${searchParams.toString()}`)
    return response.data
  }
  
  static async getBookById(id: string): Promise<BookResponse> {
    const response = await apiClient.get(`/catalog/books/${id}`)
    return response.data
  }
  
  static async getFeaturedBooks(): Promise<BooksResponse> {
    const response = await apiClient.get('/catalog/books/featured')
    return response.data
  }
  
  static async getPopularBooks(limit: number = 10): Promise<BooksResponse> {
    const response = await apiClient.get(`/catalog/books/popular?limit=${limit}`)
    return response.data
  }
  
  static async getRecentBooks(limit: number = 10): Promise<BooksResponse> {
    const response = await apiClient.get(`/catalog/books/recent?limit=${limit}`)
    return response.data
  }
  
  static async getRecommendedBooks(userId?: string, limit: number = 10): Promise<BooksResponse> {
    const params = new URLSearchParams({ limit: limit.toString() })
    if (userId) {
      params.append('userId', userId)
    }
    
    const response = await apiClient.get(`/catalog/books/recommended?${params.toString()}`)
    return response.data
  }
  
  static async searchBooks(filters: SearchFilters): Promise<SearchResponse> {
    const response = await apiClient.post('/catalog/books/search', filters)
    return response.data
  }
  
  static async createBook(bookData: CreateBookRequest): Promise<BookResponse> {
    const formData = new FormData()
    
    // Add text fields
    Object.entries(bookData).forEach(([key, value]) => {
      if (value !== undefined && value !== null && !(value instanceof File)) {
        if (Array.isArray(value)) {
          value.forEach(item => formData.append(`${key}[]`, item.toString()))
        } else {
          formData.append(key, value.toString())
        }
      }
    })
    
    // Add file fields
    if (bookData.coverImage instanceof File) {
      formData.append('coverImage', bookData.coverImage)
    }
    if (bookData.bookFile instanceof File) {
      formData.append('bookFile', bookData.bookFile)
    }
    
    const response = await apiClient.post('/catalog/books', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  }
  
  static async updateBook(bookData: UpdateBookRequest): Promise<BookResponse> {
    const { id, ...updateData } = bookData
    
    if (updateData.coverImage instanceof File || updateData.bookFile instanceof File) {
      const formData = new FormData()
      
      Object.entries(updateData).forEach(([key, value]) => {
        if (value !== undefined && value !== null && !(value instanceof File)) {
          if (Array.isArray(value)) {
            value.forEach(item => formData.append(`${key}[]`, item.toString()))
          } else {
            formData.append(key, value.toString())
          }
        }
      })
      
      if (updateData.coverImage instanceof File) {
        formData.append('coverImage', updateData.coverImage)
      }
      if (updateData.bookFile instanceof File) {
        formData.append('bookFile', updateData.bookFile)
      }
      
      const response = await apiClient.put(`/catalog/books/${id}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response.data
    } else {
      const response = await apiClient.put(`/catalog/books/${id}`, updateData)
      return response.data
    }
  }
  
  static async deleteBook(id: string): Promise<{ success: boolean; message?: string }> {
    const response = await apiClient.delete(`/catalog/books/${id}`)
    return response.data
  }
  
  // Authors
  static async getAuthors(params?: {
    page?: number
    limit?: number
    search?: string
    sortBy?: string
    sortOrder?: 'asc' | 'desc'
  }): Promise<AuthorsResponse> {
    const searchParams = new URLSearchParams()
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value.toString())
        }
      })
    }
    
    const response = await apiClient.get(`/catalog/authors?${searchParams.toString()}`)
    return response.data
  }
  
  static async getAuthorById(id: string): Promise<AuthorResponse> {
    const response = await apiClient.get(`/catalog/authors/${id}`)
    return response.data
  }
  
  static async getAuthorBooks(id: string, params?: {
    page?: number
    limit?: number
  }): Promise<BooksResponse> {
    const searchParams = new URLSearchParams()
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value.toString())
        }
      })
    }
    
    const response = await apiClient.get(`/catalog/authors/${id}/books?${searchParams.toString()}`)
    return response.data
  }
  
  static async createAuthor(authorData: CreateAuthorRequest): Promise<AuthorResponse> {
    if (authorData.profileImage instanceof File) {
      const formData = new FormData()
      
      Object.entries(authorData).forEach(([key, value]) => {
        if (value !== undefined && value !== null && !(value instanceof File)) {
          if (typeof value === 'object') {
            formData.append(key, JSON.stringify(value))
          } else {
            formData.append(key, value.toString())
          }
        }
      })
      
      formData.append('profileImage', authorData.profileImage)
      
      const response = await apiClient.post('/catalog/authors', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response.data
    } else {
      const response = await apiClient.post('/catalog/authors', authorData)
      return response.data
    }
  }
  
  static async updateAuthor(authorData: UpdateAuthorRequest): Promise<AuthorResponse> {
    const { id, ...updateData } = authorData
    
    if (updateData.profileImage instanceof File) {
      const formData = new FormData()
      
      Object.entries(updateData).forEach(([key, value]) => {
        if (value !== undefined && value !== null && !(value instanceof File)) {
          if (typeof value === 'object') {
            formData.append(key, JSON.stringify(value))
          } else {
            formData.append(key, value.toString())
          }
        }
      })
      
      formData.append('profileImage', updateData.profileImage)
      
      const response = await apiClient.put(`/catalog/authors/${id}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response.data
    } else {
      const response = await apiClient.put(`/catalog/authors/${id}`, updateData)
      return response.data
    }
  }
  
  static async deleteAuthor(id: string): Promise<{ success: boolean; message?: string }> {
    const response = await apiClient.delete(`/catalog/authors/${id}`)
    return response.data
  }
  
  // Categories
  static async getCategories(params?: {
    page?: number
    limit?: number
    parentId?: string
    includeChildren?: boolean
  }): Promise<CategoriesResponse> {
    const searchParams = new URLSearchParams()
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value.toString())
        }
      })
    }
    
    const response = await apiClient.get(`/catalog/categories?${searchParams.toString()}`)
    return response.data
  }
  
  static async getCategoryById(id: string): Promise<CategoryResponse> {
    const response = await apiClient.get(`/catalog/categories/${id}`)
    return response.data
  }
  
  static async getCategoryBooks(id: string, params?: {
    page?: number
    limit?: number
    sortBy?: string
    sortOrder?: 'asc' | 'desc'
  }): Promise<BooksResponse> {
    const searchParams = new URLSearchParams()
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value.toString())
        }
      })
    }
    
    const response = await apiClient.get(`/catalog/categories/${id}/books?${searchParams.toString()}`)
    return response.data
  }
  
  static async createCategory(categoryData: CreateCategoryRequest): Promise<CategoryResponse> {
    const response = await apiClient.post('/catalog/categories', categoryData)
    return response.data
  }
  
  static async updateCategory(categoryData: UpdateCategoryRequest): Promise<CategoryResponse> {
    const { id, ...updateData } = categoryData
    const response = await apiClient.put(`/catalog/categories/${id}`, updateData)
    return response.data
  }
  
  static async deleteCategory(id: string): Promise<{ success: boolean; message?: string }> {
    const response = await apiClient.delete(`/catalog/categories/${id}`)
    return response.data
  }
  
  // Publishers
  static async getPublishers(params?: {
    page?: number
    limit?: number
    search?: string
    country?: string
  }): Promise<PublishersResponse> {
    const searchParams = new URLSearchParams()
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value.toString())
        }
      })
    }
    
    const response = await apiClient.get(`/catalog/publishers?${searchParams.toString()}`)
    return response.data
  }
  
  static async getPublisherById(id: string): Promise<PublisherResponse> {
    const response = await apiClient.get(`/catalog/publishers/${id}`)
    return response.data
  }
  
  static async getPublisherBooks(id: string, params?: {
    page?: number
    limit?: number
  }): Promise<BooksResponse> {
    const searchParams = new URLSearchParams()
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value.toString())
        }
      })
    }
    
    const response = await apiClient.get(`/catalog/publishers/${id}/books?${searchParams.toString()}`)
    return response.data
  }
  
  static async createPublisher(publisherData: CreatePublisherRequest): Promise<PublisherResponse> {
    if (publisherData.logo instanceof File) {
      const formData = new FormData()
      
      Object.entries(publisherData).forEach(([key, value]) => {
        if (value !== undefined && value !== null && !(value instanceof File)) {
          formData.append(key, value.toString())
        }
      })
      
      formData.append('logo', publisherData.logo)
      
      const response = await apiClient.post('/catalog/publishers', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response.data
    } else {
      const response = await apiClient.post('/catalog/publishers', publisherData)
      return response.data
    }
  }
  
  static async updatePublisher(publisherData: UpdatePublisherRequest): Promise<PublisherResponse> {
    const { id, ...updateData } = publisherData
    
    if (updateData.logo instanceof File) {
      const formData = new FormData()
      
      Object.entries(updateData).forEach(([key, value]) => {
        if (value !== undefined && value !== null && !(value instanceof File)) {
          formData.append(key, value.toString())
        }
      })
      
      formData.append('logo', updateData.logo)
      
      const response = await apiClient.put(`/catalog/publishers/${id}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response.data
    } else {
      const response = await apiClient.put(`/catalog/publishers/${id}`, updateData)
      return response.data
    }
  }
  
  static async deletePublisher(id: string): Promise<{ success: boolean; message?: string }> {
    const response = await apiClient.delete(`/catalog/publishers/${id}`)
    return response.data
  }
  
  // Featured content
  static async getFeaturedContent(): Promise<FeaturedContentResponse> {
    const response = await apiClient.get('/catalog/featured')
    return response.data
  }
  
  // Statistics
  static async getBookStats(): Promise<BookStatsResponse> {
    const response = await apiClient.get('/catalog/stats')
    return response.data
  }
  
  // Reviews
  static async getBookReviews(bookId: string, params?: {
    page?: number
    limit?: number
    sortBy?: 'rating' | 'date' | 'helpful'
    sortOrder?: 'asc' | 'desc'
  }): Promise<ReviewsResponse> {
    const searchParams = new URLSearchParams()
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value.toString())
        }
      })
    }
    
    const response = await apiClient.get(`/catalog/books/${bookId}/reviews?${searchParams.toString()}`)
    return response.data
  }
  
  static async createReview(bookId: string, reviewData: {
    rating: number
    title?: string
    content: string
  }): Promise<{ success: boolean; data: Review; message?: string }> {
    const response = await apiClient.post(`/catalog/books/${bookId}/reviews`, reviewData)
    return response.data
  }
  
  static async updateReview(bookId: string, reviewId: string, reviewData: {
    rating?: number
    title?: string
    content?: string
  }): Promise<{ success: boolean; data: Review; message?: string }> {
    const response = await apiClient.put(`/catalog/books/${bookId}/reviews/${reviewId}`, reviewData)
    return response.data
  }
  
  static async deleteReview(bookId: string, reviewId: string): Promise<{ success: boolean; message?: string }> {
    const response = await apiClient.delete(`/catalog/books/${bookId}/reviews/${reviewId}`)
    return response.data
  }
  
  static async markReviewHelpful(bookId: string, reviewId: string, helpful: boolean): Promise<{ success: boolean; message?: string }> {
    const response = await apiClient.post(`/catalog/books/${bookId}/reviews/${reviewId}/helpful`, { helpful })
    return response.data
  }
}

export default CatalogAPI