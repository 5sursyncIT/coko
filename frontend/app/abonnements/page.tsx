'use client'

import { useState, useEffect } from 'react'
import Header from '@/components/Header'
import { 
  Check, 
  X, 
  Star, 
  Download, 
  BookOpen, 
  Headphones, 
  Users, 
  Shield, 
  Smartphone,
  Globe,
  Zap,
  Crown,
  ChevronDown,
  ChevronUp,
  Quote
} from 'lucide-react'

const plans = [
  {
    id: 'free',
    name: 'Gratuit',
    price: 0,
    currency: 'FCFA',
    period: '',
    description: 'Découvrez notre plateforme',
    color: 'gray',
    popular: false,
    features: [
      { name: 'Accès limité au catalogue', included: true, limit: '50 livres' },
      { name: 'Lecture avec publicités', included: true },
      { name: 'Support communautaire', included: true },
      { name: 'Application mobile', included: true },
      { name: 'Téléchargement offline', included: false },
      { name: 'Livres audio', included: false },
      { name: 'Support prioritaire', included: false },
      { name: 'Contenu exclusif', included: false }
    ]
  },
  {
    id: 'premium',
    name: 'Premium',
    price: 2500,
    currency: 'FCFA',
    period: '/mois',
    description: 'Le plus populaire',
    color: 'blue',
    popular: true,
    features: [
      { name: 'Accès illimité au catalogue', included: true, limit: '15,000+ livres' },
      { name: 'Lecture sans publicité', included: true },
      { name: 'Téléchargement offline', included: true, limit: '100 livres' },
      { name: 'Livres audio complets', included: true },
      { name: 'Support prioritaire', included: true },
      { name: 'Application mobile', included: true },
      { name: 'Synchronisation multi-appareils', included: true },
      { name: 'Contenu exclusif', included: false }
    ]
  },
  {
    id: 'family',
    name: 'Famille',
    price: 4000,
    currency: 'FCFA',
    period: '/mois',
    description: 'Parfait pour toute la famille',
    color: 'green',
    popular: false,
    features: [
      { name: 'Tout du plan Premium', included: true },
      { name: 'Jusqu\'à 5 comptes', included: true, limit: '5 utilisateurs' },
      { name: 'Contrôle parental', included: true },
      { name: 'Profils personnalisés', included: true },
      { name: 'Statistiques familiales', included: true },
      { name: 'Support dédié', included: true },
      { name: 'Téléchargement offline', included: true, limit: '500 livres' },
      { name: 'Contenu jeunesse premium', included: true }
    ]
  },
  {
    id: 'pro',
    name: 'Professionnel',
    price: 7500,
    currency: 'FCFA',
    period: '/mois',
    description: 'Pour les professionnels et institutions',
    color: 'purple',
    popular: false,
    features: [
      { name: 'Tout des plans précédents', included: true },
      { name: 'Accès anticipé aux nouveautés', included: true },
      { name: 'Recommandations IA avancées', included: true },
      { name: 'Support dédié 24/7', included: true },
      { name: 'Statistiques avancées', included: true },
      { name: 'API d\'intégration', included: true },
      { name: 'Formation et webinaires', included: true },
      { name: 'Licence commerciale', included: true }
    ]
  }
]

const paymentMethods = [
  {
    name: 'Orange Money',
    logo: '🧡',
    description: 'Paiement mobile sécurisé',
    countries: ['Sénégal', 'Mali', 'Burkina Faso', 'Niger', 'Guinée', 'Côte d\'Ivoire']
  },
  {
    name: 'MTN Mobile Money',
    logo: '💛',
    description: 'Solution de paiement mobile',
    countries: ['Ghana', 'Ouganda', 'Rwanda', 'Zambie', 'Cameroun']
  },
  {
    name: 'Wave',
    logo: '💙',
    description: 'Transfert d\'argent instantané',
    countries: ['Sénégal', 'Côte d\'Ivoire', 'Mali', 'Burkina Faso']
  },
  {
    name: 'Carte bancaire',
    logo: '💳',
    description: 'Visa, Mastercard acceptées',
    countries: ['Tous pays']
  }
]

const testimonials = [
  {
    name: 'Aminata Diallo',
    role: 'Enseignante',
    country: 'Sénégal',
    rating: 5,
    comment: 'Coko a révolutionné ma façon d\'enseigner. L\'accès à autant de livres africains est incroyable !',
    avatar: '👩🏾‍🏫'
  },
  {
    name: 'Kofi Asante',
    role: 'Étudiant',
    country: 'Ghana',
    rating: 5,
    comment: 'Le plan famille nous permet d\'accéder tous ensemble à une bibliothèque immense. Parfait !',
    avatar: '👨🏿‍🎓'
  },
  {
    name: 'Mariam Traoré',
    role: 'Bibliothécaire',
    country: 'Mali',
    rating: 5,
    comment: 'Les livres audio sont parfaits pour mes déplacements. La qualité est exceptionnelle.',
    avatar: '👩🏾‍💼'
  }
]

const faqs = [
  {
    question: 'Puis-je changer de plan à tout moment ?',
    answer: 'Oui, vous pouvez passer à un plan supérieur ou inférieur à tout moment. Les changements prennent effet immédiatement.'
  },
  {
    question: 'Les paiements mobiles sont-ils sécurisés ?',
    answer: 'Absolument. Nous utilisons les systèmes de paiement mobile les plus sécurisés d\'Afrique avec cryptage de bout en bout.'
  },
  {
    question: 'Puis-je télécharger des livres pour une lecture hors ligne ?',
    answer: 'Oui, avec les plans Premium et plus, vous pouvez télécharger des livres pour les lire sans connexion internet.'
  },
  {
    question: 'Y a-t-il des frais cachés ?',
    answer: 'Non, aucun frais caché. Le prix affiché est tout ce que vous payez, taxes incluses.'
  },
  {
    question: 'Comment fonctionne l\'essai gratuit ?',
    answer: 'Votre essai gratuit de 14 jours commence dès votre inscription. Aucune carte bancaire requise.'
  },
  {
    question: 'Puis-je annuler mon abonnement ?',
    answer: 'Oui, vous pouvez annuler votre abonnement à tout moment depuis votre compte. Aucun engagement.'
  }
]

export default function AbonnementsPage() {
  const [mounted, setMounted] = useState(false)
  const [selectedPlan, setSelectedPlan] = useState('premium')
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly')
  const [openFaq, setOpenFaq] = useState<number | null>(null)

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

  const getColorClasses = (color: string, type: 'bg' | 'text' | 'border' | 'ring') => {
    const colorMap: Record<string, Record<string, string>> = {
      gray: {
        bg: 'bg-gray-600',
        text: 'text-gray-600',
        border: 'border-gray-200',
        ring: 'ring-gray-500'
      },
      blue: {
        bg: 'bg-blue-600',
        text: 'text-blue-600',
        border: 'border-blue-200',
        ring: 'ring-blue-500'
      },
      green: {
        bg: 'bg-green-600',
        text: 'text-green-600',
        border: 'border-green-200',
        ring: 'ring-green-500'
      },
      purple: {
        bg: 'bg-purple-600',
        text: 'text-purple-600',
        border: 'border-purple-200',
        ring: 'ring-purple-500'
      }
    }
    return colorMap[color]?.[type] || colorMap.gray[type]
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-600 to-purple-700 py-20">
        <div className="container-custom text-center text-white">
          <h1 className="text-4xl md:text-6xl font-bold mb-6">
            Choisissez votre abonnement
          </h1>
          <p className="text-xl md:text-2xl text-blue-100 mb-8 max-w-3xl mx-auto">
            Accédez à des milliers de livres, ebooks et livres audio. 
            Trouvez le plan qui vous convient.
          </p>
          <div className="flex items-center justify-center space-x-4">
            <span className={`text-lg ${billingCycle === 'monthly' ? 'text-white' : 'text-blue-200'}`}>
              Mensuel
            </span>
            <button
              onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'yearly' : 'monthly')}
              className="relative inline-flex h-6 w-11 items-center rounded-full bg-blue-500 transition-colors focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2"
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  billingCycle === 'yearly' ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
            <span className={`text-lg ${billingCycle === 'yearly' ? 'text-white' : 'text-blue-200'}`}>
              Annuel
              <span className="ml-2 text-sm bg-orange-400 text-orange-900 px-2 py-1 rounded-full">
                -20%
              </span>
            </span>
          </div>
        </div>
      </section>

      {/* Plans Section */}
      <section className="py-20">
        <div className="container-custom">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {plans.map((plan, index) => {
              const yearlyPrice = billingCycle === 'yearly' ? Math.floor(plan.price * 12 * 0.8) : plan.price
              const displayPrice = billingCycle === 'yearly' ? yearlyPrice : plan.price
              
              return (
                <div
                  key={plan.id}
                  className={`card relative ${
                    plan.popular 
                      ? 'ring-2 ring-blue-600 shadow-xl transform scale-105' 
                      : 'hover:shadow-lg'
                  } transition-all cursor-pointer ${
                    selectedPlan === plan.id ? `ring-2 ${getColorClasses(plan.color, 'ring')}` : ''
                  }`}
                  onClick={() => setSelectedPlan(plan.id)}
                >
                  {plan.popular && (
                    <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                      <span className="bg-blue-600 text-white px-4 py-2 rounded-full text-sm font-medium flex items-center space-x-1">
                        <Crown className="w-4 h-4" />
                        <span>Populaire</span>
                      </span>
                    </div>
                  )}
                  
                  <div className="p-6">
                    <div className="text-center mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                      <p className="text-gray-600 text-sm mb-4">{plan.description}</p>
                      <div className="mb-4">
                        <span className="text-4xl font-bold text-gray-900">
                          {displayPrice.toLocaleString()}
                        </span>
                        <span className="text-gray-600 ml-1">{plan.currency}</span>
                        {plan.period && (
                          <span className="text-gray-600">
                            {billingCycle === 'yearly' ? '/an' : plan.period}
                          </span>
                        )}
                      </div>
                      {billingCycle === 'yearly' && plan.price > 0 && (
                        <p className="text-sm text-green-600 font-medium">
                          Économisez {(plan.price * 12 * 0.2).toLocaleString()} FCFA/an
                        </p>
                      )}
                    </div>

                    <ul className="space-y-3 mb-6">
                      {plan.features.map((feature, idx) => (
                        <li key={idx} className="flex items-start space-x-3">
                          {feature.included ? (
                            <Check className={`w-5 h-5 ${getColorClasses(plan.color, 'text')} flex-shrink-0 mt-0.5`} />
                          ) : (
                            <X className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
                          )}
                          <div className="flex-1">
                            <span className={`text-sm ${feature.included ? 'text-gray-900' : 'text-gray-400'}`}>
                              {feature.name}
                            </span>
                            {feature.limit && (
                              <span className="text-xs text-gray-500 block">
                                {feature.limit}
                              </span>
                            )}
                          </div>
                        </li>
                      ))}
                    </ul>

                    <button
                      className={`w-full py-3 rounded-lg font-medium transition-colors ${
                        plan.popular
                          ? 'bg-blue-600 text-white hover:bg-blue-700'
                          : `${getColorClasses(plan.color, 'bg')} text-white hover:opacity-90`
                      }`}
                    >
                      {plan.price === 0 ? 'Commencer gratuitement' : 'Choisir ce plan'}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Payment Methods */}
      <section className="py-16 bg-white">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Paiements adaptés à l'Afrique
            </h2>
            <p className="text-lg text-gray-600">
              Payez facilement avec vos méthodes préférées
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {paymentMethods.map((method, index) => (
              <div key={index} className="card p-6 text-center hover:shadow-lg transition-all">
                <div className="text-4xl mb-4">{method.logo}</div>
                <h3 className="font-semibold text-gray-900 mb-2">{method.name}</h3>
                <p className="text-gray-600 text-sm mb-4">{method.description}</p>
                <div className="text-xs text-gray-500">
                  {method.countries.slice(0, 3).join(', ')}
                  {method.countries.length > 3 && '...'}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Comparison */}
      <section className="py-16 bg-gray-50">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Pourquoi choisir Coko ?
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Globe className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Contenu africain authentique
              </h3>
              <p className="text-gray-600">
                Plus de 5,000 livres d'auteurs africains et sur l'Afrique
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Smartphone className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Optimisé pour l'mobile
              </h3>
              <p className="text-gray-600">
                Conçu pour les réseaux 2G/3G avec mode offline
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Shield className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Paiements sécurisés
              </h3>
              <p className="text-gray-600">
                Intégration avec tous les systèmes de paiement mobile africains
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-16 bg-white">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Ce que disent nos utilisateurs
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <div key={index} className="card p-6">
                <div className="flex items-center mb-4">
                  <div className="text-3xl mr-3">{testimonial.avatar}</div>
                  <div>
                    <h4 className="font-semibold text-gray-900">{testimonial.name}</h4>
                    <p className="text-gray-600 text-sm">{testimonial.role} • {testimonial.country}</p>
                  </div>
                </div>
                <div className="flex items-center mb-3">
                  {Array.from({ length: testimonial.rating }, (_, i) => (
                    <Star key={i} className="w-4 h-4 text-yellow-400 fill-current" />
                  ))}
                </div>
                <blockquote className="text-gray-700 italic">
                  <Quote className="w-4 h-4 text-gray-400 mb-2" />
                  "{testimonial.comment}"
                </blockquote>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-16 bg-gray-50">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Questions fréquentes
            </h2>
          </div>

          <div className="max-w-3xl mx-auto">
            {faqs.map((faq, index) => (
              <div key={index} className="card mb-4">
                <button
                  onClick={() => setOpenFaq(openFaq === index ? null : index)}
                  className="w-full p-6 text-left flex items-center justify-between hover:bg-gray-50 transition-colors"
                >
                  <span className="font-medium text-gray-900">{faq.question}</span>
                  {openFaq === index ? (
                    <ChevronUp className="w-5 h-5 text-gray-500" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-500" />
                  )}
                </button>
                {openFaq === index && (
                  <div className="px-6 pb-6">
                    <p className="text-gray-600">{faq.answer}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-blue-600">
        <div className="container-custom text-center text-white">
          <h2 className="text-3xl font-bold mb-4">
            Prêt à commencer votre aventure de lecture ?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Essayez gratuitement pendant 14 jours, sans engagement
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="btn bg-white text-blue-600 hover:bg-gray-50 px-8 py-3">
              Essai gratuit 14 jours
            </button>
            <button className="btn border-white text-white hover:bg-blue-700 px-8 py-3">
              Voir tous les plans
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}