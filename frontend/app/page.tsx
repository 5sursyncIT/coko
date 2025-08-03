'use client'

import Header from '@/components/Header'
import { Play, Star, Users, BookOpen, Download, Globe, Heart, ArrowRight } from 'lucide-react'

const featuredBooks = [
  {
    id: 1,
    title: 'Les Bouts de Bois de Dieu',
    author: 'Ousmane Sembène',
    category: 'Littérature Africaine',
    rating: 4.8,
    image: '/api/placeholder/300/400',
    type: 'Ebook'
  },
  {
    id: 2,
    title: 'Une si longue lettre',
    author: 'Mariama Bâ',
    category: 'Roman',
    rating: 4.9,
    image: '/api/placeholder/300/400',
    type: 'Livre Audio'
  },
  {
    id: 3,
    title: 'Le Ventre de l\'Atlantique',
    author: 'Fatou Diome',
    category: 'Fiction',
    rating: 4.7,
    image: '/api/placeholder/300/400',
    type: 'Ebook'
  },
  {
    id: 4,
    title: 'Gouverneurs de la Rosée',
    author: 'Jacques Roumain',
    category: 'Classique',
    rating: 4.6,
    image: '/api/placeholder/300/400',
    type: 'PDF'
  }
]

const plans = [
  {
    name: 'Gratuit',
    price: '0',
    currency: 'FCFA',
    period: '',
    features: ['Accès limité', 'Avec publicités', '50 pages/jour'],
    popular: false
  },
  {
    name: 'Premium',
    price: '2,500',
    currency: 'FCFA',
    period: '/mois',
    features: ['Accès illimité', 'Sans publicité', 'Téléchargement offline', 'Support prioritaire'],
    popular: true
  },
  {
    name: 'Famille',
    price: '4,000',
    currency: 'FCFA',
    period: '/mois',
    features: ['5 comptes', 'Accès illimité', 'Contrôle parental', 'Statistiques familiales'],
    popular: false
  }
]

const advantages = [
  {
    icon: BookOpen,
    title: 'Catalogue riche',
    description: 'Plus de 15,000 livres, ebooks et livres audio'
  },
  {
    icon: Globe,
    title: 'Contenu africain',
    description: 'Littérature et auteurs africains mis en avant'
  },
  {
    icon: Download,
    title: 'Mode offline',
    description: 'Téléchargez et lisez sans connexion internet'
  },
  {
    icon: Users,
    title: 'Communauté',
    description: 'Partagez vos avis et découvertes'
  }
]

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-50 to-indigo-100 py-20">
        <div className="container-custom">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              Faites le plein d'
              <span className="text-blue-600">ebooks</span> et de{' '}
              <span className="text-green-600">livres audio</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Des milliers d'ebooks, de livres audio, de journaux et de documents 
              à découvrir sur tous vos écrans !
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="btn btn-primary text-lg px-8 py-3">
                Découvrir les offres
              </button>
              <button className="btn btn-outline text-lg px-8 py-3">
                Essai gratuit
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Trends Section */}
      <section className="py-16 bg-white">
        <div className="container-custom">
          <div className="flex items-center justify-between mb-12">
            <h2 className="text-3xl font-bold text-gray-900">Tendances</h2>
            <button className="btn btn-outline">
              Voir tout
              <ArrowRight className="w-4 h-4 ml-2" />
            </button>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {featuredBooks.map((book) => (
              <div key={book.id} className="card group cursor-pointer hover:shadow-lg transition-all">
                <div className="relative aspect-[3/4] bg-gray-100">
                  <img 
                    src={book.image} 
                    alt={book.title}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute top-3 left-3">
                    <span className="bg-blue-600 text-white px-2 py-1 rounded text-xs font-medium">
                      {book.type}
                    </span>
                  </div>
                  <div className="absolute top-3 right-3">
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
                <div className="p-4">
                  <div className="text-sm text-blue-600 font-medium mb-1">{book.category}</div>
                  <h3 className="font-semibold text-gray-900 mb-1 line-clamp-2">{book.title}</h3>
                  <p className="text-gray-600 text-sm mb-2">{book.author}</p>
                  <div className="flex items-center">
                    <Star className="w-4 h-4 text-yellow-400 fill-current" />
                    <span className="text-sm font-medium ml-1">{book.rating}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Subscription Plans */}
      <section className="py-16 bg-gray-50">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Nos offres</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Choisissez l'offre qui vous convient et accédez à des milliers de contenus
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {plans.map((plan, index) => (
              <div key={index} className={`card relative ${plan.popular ? 'ring-2 ring-blue-600' : ''}`}>
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <span className="bg-blue-600 text-white px-4 py-1 rounded-full text-sm font-medium">
                      Populaire
                    </span>
                  </div>
                )}
                <div className="p-6 text-center">
                  <h3 className="text-xl font-semibold text-gray-900 mb-4">{plan.name}</h3>
                  <div className="mb-6">
                    <span className="text-4xl font-bold text-gray-900">{plan.price}</span>
                    <span className="text-gray-600 ml-1">{plan.currency}</span>
                    <span className="text-gray-600">{plan.period}</span>
                  </div>
                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-center text-gray-600">
                        <div className="w-2 h-2 bg-blue-600 rounded-full mr-3"></div>
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <button className={`btn w-full ${plan.popular ? 'btn-primary' : 'btn-outline'}`}>
                    {plan.name === 'Gratuit' ? 'Commencer gratuitement' : 'Choisir cette offre'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Advantages */}
      <section className="py-16 bg-white">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Pourquoi choisir Coko ?</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {advantages.map((advantage, index) => {
              const Icon = advantage.icon
              return (
                <div key={index} className="text-center">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Icon className="w-8 h-8 text-blue-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{advantage.title}</h3>
                  <p className="text-gray-600">{advantage.description}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-blue-600">
        <div className="container-custom text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Prêt à découvrir votre prochaine lecture ?
          </h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Rejoignez des milliers de lecteurs qui ont déjà trouvé leurs livres préférés sur Coko
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="btn bg-white text-blue-600 hover:bg-gray-50 px-8 py-3">
              Commencer maintenant
            </button>
            <button className="btn border-white text-white hover:bg-blue-700 px-8 py-3">
              Explorer le catalogue
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="container-custom">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">C</span>
                </div>
                <span className="text-xl font-bold">Coko</span>
              </div>
              <p className="text-gray-400">
                La plateforme de lecture numérique conçue pour l'Afrique
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Produit</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">Catalogue</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Abonnements</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Applications</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Support</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">Centre d'aide</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
                <li><a href="#" className="hover:text-white transition-colors">FAQ</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Société</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">À propos</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Carrières</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Presse</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2025 Coko. Tous droits réservés.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}