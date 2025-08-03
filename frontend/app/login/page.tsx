'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { ArrowLeft, HelpCircle } from 'lucide-react'
import LoginForm from '@/components/LoginForm'

export default function LoginPage() {
  const [mounted, setMounted] = useState(false)
  const [activeTab, setActiveTab] = useState<'login' | 'register'>('login')

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="container-custom">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center space-x-2">
              <ArrowLeft className="w-5 h-5 text-gray-600" />
              <span className="text-gray-600 hover:text-blue-600 transition-colors">Retour à l'accueil</span>
            </Link>
            
            <Link href="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">C</span>
              </div>
              <span className="text-xl font-bold text-gray-900">Coko</span>
            </Link>
            
            <div className="w-24"> {/* Spacer for centering */}</div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="py-12">
        <div className="max-w-md mx-auto px-4">
          
          {/* Form Container */}
          <LoginForm activeTab={activeTab} onTabChange={setActiveTab} />

          {/* Additional Info */}
          <div className="mt-8 text-center">
            <div className="flex items-center justify-center space-x-4 text-sm text-gray-600">
              <Link href="/help" className="hover:text-blue-600 transition-colors flex items-center">
                <HelpCircle className="w-4 h-4 mr-1" />
                Aide
              </Link>
              <span>•</span>
              <Link href="/contact" className="hover:text-blue-600 transition-colors">
                Contact
              </Link>
              <span>•</span>
              <Link href="/about" className="hover:text-blue-600 transition-colors">
                À propos
              </Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}