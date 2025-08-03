'use client'

import { useState } from 'react'
import { ChevronDown, Upload, User, Search, Menu, X } from 'lucide-react'

const languages = [
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'ar', name: 'العربية', flag: '🇸🇦' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
]

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [currentLang, setCurrentLang] = useState(languages[0])
  const [isLangOpen, setIsLangOpen] = useState(false)

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="container-custom">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo */}
          <div className="flex items-center space-x-8">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">C</span>
              </div>
              <span className="text-xl font-bold text-gray-900">Coko</span>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-6">
              <a href="/catalogue" className="text-gray-600 hover:text-blue-600 transition-colors">Catalogue</a>
              <a href="/abonnements" className="text-gray-600 hover:text-blue-600 transition-colors">Abonnements</a>
              <a href="#" className="text-gray-600 hover:text-blue-600 transition-colors">À propos</a>
            </nav>
          </div>

          {/* Right side */}
          <div className="flex items-center space-x-4">
            
            {/* Language selector */}
            <div className="relative">
              <button 
                onClick={() => setIsLangOpen(!isLangOpen)}
                className="flex items-center space-x-1 text-gray-600 hover:text-blue-600 transition-colors"
              >
                <span className="text-lg">{currentLang.flag}</span>
                <span className="hidden sm:block">{currentLang.code.toUpperCase()}</span>
                <ChevronDown className="w-4 h-4" />
              </button>
              
              {isLangOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1">
                  {languages.map((lang) => (
                    <button
                      key={lang.code}
                      onClick={() => {
                        setCurrentLang(lang)
                        setIsLangOpen(false)
                      }}
                      className="w-full flex items-center space-x-3 px-4 py-2 text-left hover:bg-gray-50 transition-colors"
                    >
                      <span className="text-lg">{lang.flag}</span>
                      <span>{lang.name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Publish button */}
            <button className="hidden sm:flex items-center space-x-2 text-gray-600 hover:text-blue-600 transition-colors">
              <Upload className="w-4 h-4" />
              <span>Publier</span>
            </button>

            {/* Search button - mobile */}
            <button className="md:hidden p-2 text-gray-600 hover:text-blue-600 transition-colors">
              <Search className="w-5 h-5" />
            </button>

            {/* Login button */}
            <a href="/login" className="btn btn-primary">
              <User className="w-4 h-4 mr-2" />
              Connexion
            </a>

            {/* Mobile menu button */}
            <button 
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="md:hidden p-2 text-gray-600 hover:text-blue-600 transition-colors"
            >
              {isMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {isMenuOpen && (
          <div className="md:hidden border-t border-gray-200 py-4">
            <nav className="flex flex-col space-y-3">
              <a href="/catalogue" className="text-gray-600 hover:text-blue-600 transition-colors py-2">Catalogue</a>
              <a href="/abonnements" className="text-gray-600 hover:text-blue-600 transition-colors py-2">Abonnements</a>
              <a href="#" className="text-gray-600 hover:text-blue-600 transition-colors py-2">À propos</a>
              <button className="flex items-center space-x-2 text-gray-600 hover:text-blue-600 transition-colors py-2">
                <Upload className="w-4 h-4" />
                <span>Publier un document</span>
              </button>
            </nav>
          </div>
        )}
      </div>
    </header>
  )
}