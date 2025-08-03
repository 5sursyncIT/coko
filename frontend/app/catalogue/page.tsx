'use client'

import { useState, useEffect } from 'react'
import Header from '@/components/Header'
import { 
  Search, 
  Filter, 
  Grid3X3, 
  List, 
  ChevronDown, 
  Star, 
  Heart, 
  Play, 
  Download,
  BookOpen,
  Headphones,
  FileText,
  Newspaper,
  X
} from 'lucide-react'

const contentTypes = [
  { id: 'all', name: 'Tout', icon: BookOpen },
  { id: 'ebooks', name: 'Ebooks', icon: BookOpen },
  { id: 'audiobooks', name: 'Livres audio', icon: Headphones },
  { id: 'pdf', name: 'PDF', icon: FileText },
  { id: 'press', name: 'Presse', icon: Newspaper },
]

const categories = [
  {
    id: 'litterature',
    name: 'Littérature',
    subcategories: ['Roman', 'Poésie', 'Théâtre', 'Nouvelles']
  },
  {
    id: 'african',
    name: 'Littérature Africaine',
    subcategories: ['Romans africains', 'Contes traditionnels', 'Poésie africaine', 'Histoire d\'Afrique']
  },
  {
    id: 'education',
    name: 'Éducation',
    subcategories: ['Sciences', 'Mathématiques', 'Histoire', 'Langues']
  },
  {
    id: 'youth',
    name: 'Jeunesse',
    subcategories: ['Albums', 'Contes', 'Apprentissage', 'Aventure']
  },
  {
    id: 'business',
    name: 'Développement Personnel',
    subcategories: ['Leadership', 'Entrepreneuriat', 'Productivité', 'Bien-être']
  },
  {
    id: 'science',
    name: 'Sciences',
    subcategories: ['Médecine', 'Technologie', 'Environnement', 'Recherche']
  }
]

const sortOptions = [
  { id: 'relevance', name: 'Pertinence' },
  { id: 'date', name: 'Plus récent' },
  { id: 'rating', name: 'Mieux notés' },
  { id: 'popular', name: 'Plus populaires' },
  { id: 'title', name: 'Titre A-Z' }
]

// Mock data for books
const books = Array.from({ length: 24 }, (_, i) => ({
  id: i + 1,
  title: [
    'Les Bouts de Bois de Dieu',
    'Une si longue lettre',
    'Le Ventre de l\'Atlantique',
    'Gouverneurs de la Rosée',
    'L\'Enfant Noir',
    'Batouala',
    'La Grève des Bàttu',
    'Le Docker Noir',
    'Xala',
    'Les Gardiens du Temple',
    'Allah n\'est pas obligé',
    'Monnè, outrages et défis',
    'Le Cercle des Tropiques',
    'Une Vie de Boy',
    'Ville Cruelle',
    'L\'Aventure Ambiguë',
    'Cahier d\'un Retour au Pays Natal',
    'Peau Noire, Masques Blancs',
    'Les Damnés de la Terre',
    'Discours sur le Colonialisme',
    'So Long a Letter',
    'The African Child',
    'Things Fall Apart',
    'Purple Hibiscus'
  ][i] || `Livre ${i + 1}`,
  author: [
    'Ousmane Sembène',
    'Mariama Bâ',
    'Fatou Diome',
    'Jacques Roumain',
    'Camara Laye',
    'René Maran',
    'Aminata Sow Fall',
    'Ousmane Sembène',
    'Ousmane Sembène',
    'Mongo Beti',
    'Ahmadou Kourouma',
    'Ahmadou Kourouma',
    'Alioum Fantouré',
    'Ferdinand Oyono',
    'Eza Boto',
    'Cheikh Hamidou Kane',
    'Aimé Césaire',
    'Frantz Fanon',
    'Frantz Fanon',
    'Aimé Césaire',
    'Mariama Bâ',
    'Camara Laye',
    'Chinua Achebe',
    'Chimamanda Ngozi Adichie'
  ][i] || `Auteur ${i + 1}`,
  category: categories[i % categories.length].name,
  type: contentTypes[(i % 4) + 1].id,
  rating: 4.0 + Math.random() * 1,
  price: Math.floor(Math.random() * 3000) + 1000,
  image: `/api/placeholder/300/400`,
  featured: i % 5 === 0,
  language: i % 3 === 0 ? 'English' : 'Français'
}))

export default function CataloguePage() {
  const [mounted, setMounted] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedContentType, setSelectedContentType] = useState('all')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [selectedSubcategory, setSelectedSubcategory] = useState('')
  const [sortBy, setSortBy] = useState('relevance')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [showFilters, setShowFilters] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage] = useState(12)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  // Filter books based on selected filters
  const filteredBooks = books.filter(book => {
    const matchesSearch = book.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         book.author.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesType = selectedContentType === 'all' || book.type === selectedContentType
    const matchesCategory = !selectedCategory || book.category === selectedCategory
    
    return matchesSearch && matchesType && matchesCategory
  })

  // Pagination
  const totalPages = Math.ceil(filteredBooks.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const currentBooks = filteredBooks.slice(startIndex, startIndex + itemsPerPage)

  const clearFilters = () => {
    setSelectedContentType('all')
    setSelectedCategory('')
    setSelectedSubcategory('')
    setSearchQuery('')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="container-custom py-6">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Catalogue</h1>
          <p className="text-gray-600">Découvrez plus de 15,000 livres, ebooks et contenus audio</p>
        </div>

        {/* Search and Filters Bar */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          {/* Search Bar */}
          <div className="flex flex-col lg:flex-row gap-4 mb-6">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Rechercher un livre, un auteur..."
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="btn btn-outline flex items-center space-x-2 lg:hidden"
            >
              <Filter className="w-4 h-4" />
              <span>Filtres</span>
            </button>
          </div>

          {/* Filters Row */}
          <div className={`grid grid-cols-1 lg:grid-cols-4 gap-4 ${showFilters ? 'block' : 'hidden lg:grid'}`}>
            {/* Content Type Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Type de contenu</label>
              <select
                value={selectedContentType}
                onChange={(e) => setSelectedContentType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              >
                {contentTypes.map((type) => (
                  <option key={type.id} value={type.id}>
                    {type.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Category Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Catégorie</label>
              <select
                value={selectedCategory}
                onChange={(e) => {
                  setSelectedCategory(e.target.value)
                  setSelectedSubcategory('')
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              >
                <option value="">Toutes les catégories</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.name}>
                    {category.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Sort By */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Trier par</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              >
                {sortOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Actions */}
            <div className="flex items-end space-x-2">
              <button
                onClick={clearFilters}
                className="btn btn-outline flex-1"
              >
                Effacer
              </button>
            </div>
          </div>
        </div>

        {/* Results Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <p className="text-gray-600">
              <span className="font-medium">{filteredBooks.length}</span> résultats
            </p>
            {(selectedContentType !== 'all' || selectedCategory || searchQuery) && (
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-500">Filtres actifs:</span>
                {selectedContentType !== 'all' && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {contentTypes.find(t => t.id === selectedContentType)?.name}
                    <button
                      onClick={() => setSelectedContentType('all')}
                      className="ml-1 text-blue-600 hover:text-blue-800"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                )}
                {selectedCategory && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    {selectedCategory}
                    <button
                      onClick={() => setSelectedCategory('')}
                      className="ml-1 text-green-600 hover:text-green-800"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                )}
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-blue-100 text-blue-600' : 'text-gray-400 hover:text-gray-600'}`}
            >
              <Grid3X3 className="w-5 h-5" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-blue-100 text-blue-600' : 'text-gray-400 hover:text-gray-600'}`}
            >
              <List className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Books Grid/List */}
        {viewMode === 'grid' ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-6 mb-8">
            {currentBooks.map((book) => (
              <div key={book.id} className="card group cursor-pointer hover:shadow-lg transition-all">
                <div className="relative aspect-[3/4] bg-gray-100">
                  <img 
                    src={book.image} 
                    alt={book.title}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute top-2 left-2">
                    <span className="bg-blue-600 text-white px-2 py-1 rounded text-xs font-medium">
                      {contentTypes.find(t => t.id === book.type)?.name}
                    </span>
                  </div>
                  {book.featured && (
                    <div className="absolute top-2 right-2">
                      <span className="bg-orange-500 text-white px-2 py-1 rounded text-xs font-medium">
                        Populaire
                      </span>
                    </div>
                  )}
                  <div className="absolute top-2 right-2 mt-8">
                    <button className="w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-md hover:bg-gray-50 transition-colors">
                      <Heart className="w-4 h-4 text-gray-600" />
                    </button>
                  </div>
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
                    <button className="bg-white text-blue-600 rounded-full w-12 h-12 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                      <Play className="w-5 h-5 ml-0.5" />
                    </button>
                  </div>
                </div>
                <div className="p-3">
                  <div className="text-xs text-blue-600 font-medium mb-1">{book.category}</div>
                  <h3 className="font-medium text-gray-900 mb-1 line-clamp-2 text-sm">{book.title}</h3>
                  <p className="text-gray-600 text-xs mb-2">{book.author}</p>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Star className="w-3 h-3 text-yellow-400 fill-current" />
                      <span className="text-xs font-medium ml-1">{book.rating.toFixed(1)}</span>
                    </div>
                    <span className="text-xs font-medium text-gray-900">{book.price} FCFA</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-4 mb-8">
            {currentBooks.map((book) => (
              <div key={book.id} className="card p-4 hover:shadow-lg transition-all cursor-pointer">
                <div className="flex items-center space-x-4">
                  <div className="relative w-16 h-20 bg-gray-100 rounded overflow-hidden flex-shrink-0">
                    <img 
                      src={book.image} 
                      alt={book.title}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="bg-blue-600 text-white px-2 py-0.5 rounded text-xs font-medium">
                            {contentTypes.find(t => t.id === book.type)?.name}
                          </span>
                          <span className="text-xs text-blue-600 font-medium">{book.category}</span>
                        </div>
                        <h3 className="font-medium text-gray-900 mb-1">{book.title}</h3>
                        <p className="text-gray-600 text-sm mb-2">{book.author}</p>
                        <div className="flex items-center space-x-4">
                          <div className="flex items-center">
                            <Star className="w-4 h-4 text-yellow-400 fill-current" />
                            <span className="text-sm font-medium ml-1">{book.rating.toFixed(1)}</span>
                          </div>
                          <span className="text-sm text-gray-500">{book.language}</span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 ml-4">
                        <span className="font-medium text-gray-900">{book.price} FCFA</span>
                        <button className="btn btn-primary text-sm">
                          Voir
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center space-x-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="btn btn-outline disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Précédent
            </button>
            
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum
              if (totalPages <= 5) {
                pageNum = i + 1
              } else if (currentPage <= 3) {
                pageNum = i + 1
              } else if (currentPage >= totalPages - 2) {
                pageNum = totalPages - 4 + i
              } else {
                pageNum = currentPage - 2 + i
              }
              
              return (
                <button
                  key={pageNum}
                  onClick={() => setCurrentPage(pageNum)}
                  className={`w-10 h-10 rounded-lg font-medium transition-colors ${
                    currentPage === pageNum
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  {pageNum}
                </button>
              )
            })}
            
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="btn btn-outline disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Suivant
            </button>
          </div>
        )}
      </div>
    </div>
  )
}