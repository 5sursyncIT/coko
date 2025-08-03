'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'

type Language = 'fr' | 'en' // French, English

interface I18nContextType {
  language: Language
  setLanguage: (lang: Language) => void
  t: (key: string, params?: Record<string, string>) => string
  isRTL: boolean
}

const I18nContext = createContext<I18nContextType | undefined>(undefined)

// Simple translations object
const translations: Record<Language, Record<string, string>> = {
  fr: {
    'common.loading': 'Chargement...',
    'common.error': 'Erreur',
    'common.success': 'Succès',
    'common.cancel': 'Annuler',
    'common.save': 'Enregistrer',
    'common.delete': 'Supprimer',
    'common.edit': 'Modifier',
    'common.view': 'Voir',
    'common.search': 'Rechercher',
    'auth.login': 'Se connecter',
    'auth.logout': 'Se déconnecter',
    'auth.register': 'S\'inscrire',
    'nav.home': 'Accueil',
    'nav.catalog': 'Catalogue',
    'nav.library': 'Ma bibliothèque',
    'nav.profile': 'Profil',
  },
  en: {
    'common.loading': 'Loading...',
    'common.error': 'Error',
    'common.success': 'Success',
    'common.cancel': 'Cancel',
    'common.save': 'Save',
    'common.delete': 'Delete',
    'common.edit': 'Edit',
    'common.view': 'View',
    'common.search': 'Search',
    'auth.login': 'Login',
    'auth.logout': 'Logout',
    'auth.register': 'Register',
    'nav.home': 'Home',
    'nav.catalog': 'Catalog',
    'nav.library': 'My Library',
    'nav.profile': 'Profile',
  },
}

interface I18nProviderProps {
  children: ReactNode
}

export function I18nProvider({ children }: I18nProviderProps) {
  const [language, setLanguage] = useState<Language>('fr')

  useEffect(() => {
    // Load saved language from localStorage
    const savedLang = localStorage.getItem('coko_language') as Language
    if (savedLang && ['fr', 'en'].includes(savedLang)) {
      setLanguage(savedLang)
    } else {
      // Detect browser language
      const browserLang = navigator.language.split('-')[0]
      if (browserLang === 'en') {
        setLanguage('en')
      } else {
        setLanguage('fr') // Default to French for Senegal
      }
    }
  }, [])

  const handleSetLanguage = (lang: Language) => {
    setLanguage(lang)
    localStorage.setItem('coko_language', lang)
    // Update document language
    document.documentElement.lang = lang
  }

  const t = (key: string, params?: Record<string, string>): string => {
    let translation = translations[language][key] || key
    
    // Replace parameters in translation
    if (params) {
      Object.entries(params).forEach(([param, value]) => {
        translation = translation.replace(`{{${param}}}`, value)
      })
    }
    
    return translation
  }

  const isRTL = false // None of our supported languages are RTL

  const value: I18nContextType = {
    language,
    setLanguage: handleSetLanguage,
    t,
    isRTL,
  }

  return (
    <I18nContext.Provider value={value}>
      {children}
    </I18nContext.Provider>
  )
}

export function useI18n() {
  const context = useContext(I18nContext)
  if (context === undefined) {
    throw new Error('useI18n must be used within an I18nProvider')
  }
  return context
}

export default I18nContext