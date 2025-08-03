# Plan de Développement Frontend - Coko

## 🎯 Objectif

Développer une interface utilisateur moderne et performante pour la plateforme Coko, optimisée pour l'Afrique avec support mobile-first.

---

## 🏗️ Architecture Frontend

### Stack Technologique

```yaml
Framework: Next.js 14 (App Router)
Language: TypeScript
Styling: Tailwind CSS + Framer Motion
State Management: Redux Toolkit + RTK Query
Testing: Jest + React Testing Library + Cypress
Build: Next.js (SSR/SSG)
Deployment: Vercel / AWS
```

### Structure du Projet

```
frontend/
├── app/                    # App Router (Next.js 14)
│   ├── (auth)/            # Groupe d'authentification
│   │   ├── login/
│   │   └── register/
│   ├── catalog/           # Catalogue de livres
│   ├── reading/           # Interface de lecture
│   ├── profile/           # Profil utilisateur
│   └── billing/           # Facturation
├── components/            # Composants réutilisables
│   ├── ui/               # Composants UI de base
│   ├── auth/             # Composants d'authentification
│   ├── catalog/          # Composants catalogue
│   ├── reading/          # Composants lecture
│   └── common/           # Composants communs
├── lib/                  # Utilitaires et configuration
│   ├── api/              # Client API
│   ├── auth/             # Gestion authentification
│   ├── store/            # Configuration Redux
│   └── utils/            # Fonctions utilitaires
├── public/               # Assets statiques
└── styles/               # Styles globaux
```

---

## 📱 Design System

### Thème Africain

```typescript
// tailwind.config.js
const theme = {
  colors: {
    primary: {
      50: '#fff7ed',   // Orange clair
      500: '#f97316',  // Orange principal
      900: '#9a3412',  // Orange foncé
    },
    secondary: {
      50: '#f0fdf4',   // Vert clair
      500: '#22c55e',  // Vert principal
      900: '#14532d',  // Vert foncé
    },
    earth: {
      50: '#fefce8',   // Terre clair
      500: '#eab308',  // Terre principal
      900: '#713f12',  // Terre foncé
    }
  },
  fontFamily: {
    sans: ['Inter', 'system-ui'],
    serif: ['Merriweather', 'serif'],
    african: ['Noto Sans', 'system-ui'],
  }
}
```

### Composants UI de Base

```typescript
// components/ui/Button.tsx
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'outline'
  size: 'sm' | 'md' | 'lg'
  loading?: boolean
  children: React.ReactNode
}

// components/ui/Card.tsx
interface CardProps {
  elevation: 'low' | 'medium' | 'high'
  padding: 'sm' | 'md' | 'lg'
  children: React.ReactNode
}

// components/ui/Input.tsx
interface InputProps {
  label: string
  error?: string
  required?: boolean
  type: 'text' | 'email' | 'password' | 'tel'
}
```

---

## 🔐 Authentification Frontend

### Configuration Auth

```typescript
// lib/auth/authSlice.ts
interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  loading: boolean
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    loginStart: (state) => {
      state.loading = true
    },
    loginSuccess: (state, action) => {
      state.user = action.payload.user
      state.token = action.payload.token
      state.isAuthenticated = true
      state.loading = false
    },
    logout: (state) => {
      state.user = null
      state.token = null
      state.isAuthenticated = false
    }
  }
})
```

### Pages d'Authentification

```typescript
// app/(auth)/login/page.tsx
export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const dispatch = useAppDispatch()
  
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    try {
      const response = await authAPI.login({ email, password })
      dispatch(loginSuccess(response.data))
      router.push('/catalog')
    } catch (error) {
      // Gestion d'erreur
    }
  }
  
  return (
    <AuthLayout>
      <LoginForm onSubmit={handleSubmit} />
    </AuthLayout>
  )
}
```

### Protection des Routes

```typescript
// components/auth/ProtectedRoute.tsx
export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAppSelector(state => state.auth)
  
  if (loading) return <LoadingSpinner />
  if (!isAuthenticated) redirect('/login')
  
  return <>{children}</>
}
```

---

## 📚 Interface Catalogue

### Liste des Livres

```typescript
// app/catalog/page.tsx
export default function CatalogPage() {
  const [filters, setFilters] = useState({
    category: '',
    author: '',
    language: '',
    search: ''
  })
  
  const { data: books, isLoading } = useGetBooksQuery(filters)
  
  return (
    <MainLayout>
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <aside className="lg:col-span-1">
          <CatalogFilters 
            filters={filters} 
            onFiltersChange={setFilters} 
          />
        </aside>
        <main className="lg:col-span-3">
          <BookGrid books={books} loading={isLoading} />
        </main>
      </div>
    </MainLayout>
  )
}
```

### Composant Livre

```typescript
// components/catalog/BookCard.tsx
interface BookCardProps {
  book: Book
  onRead: (bookId: string) => void
  onAddToLibrary: (bookId: string) => void
}

export function BookCard({ book, onRead, onAddToLibrary }: BookCardProps) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="bg-white rounded-lg shadow-md overflow-hidden"
    >
      <div className="aspect-[3/4] relative">
        <Image
          src={book.coverUrl}
          alt={book.title}
          fill
          className="object-cover"
        />
      </div>
      <div className="p-4">
        <h3 className="font-semibold text-gray-900">{book.title}</h3>
        <p className="text-gray-600">{book.author}</p>
        <div className="mt-4 flex gap-2">
          <Button onClick={() => onRead(book.id)} variant="primary">
            Lire
          </Button>
          <Button onClick={() => onAddToLibrary(book.id)} variant="outline">
            Ajouter
          </Button>
        </div>
      </div>
    </motion.div>
  )
}
```

---

## 📖 Interface de Lecture

### Lecteur de Livres

```typescript
// app/reading/[bookId]/page.tsx
export default function ReadingPage({ params }: { params: { bookId: string } }) {
  const { data: book } = useGetBookQuery(params.bookId)
  const [currentPage, setCurrentPage] = useState(1)
  const [fontSize, setFontSize] = useState(16)
  const [theme, setTheme] = useState<'light' | 'dark' | 'sepia'>('light')
  
  return (
    <ReadingLayout>
      <ReaderHeader 
        book={book}
        onSettingsOpen={() => setShowSettings(true)}
      />
      <ReaderContent
        content={book?.content}
        currentPage={currentPage}
        fontSize={fontSize}
        theme={theme}
        onPageChange={setCurrentPage}
      />
      <ReaderControls
        currentPage={currentPage}
        totalPages={book?.totalPages}
        onPrevPage={() => setCurrentPage(p => Math.max(1, p - 1))}
        onNextPage={() => setCurrentPage(p => Math.min(book?.totalPages || 1, p + 1))}
      />
    </ReadingLayout>
  )
}
```

### Composants de Lecture

```typescript
// components/reading/ReaderContent.tsx
interface ReaderContentProps {
  content: string
  fontSize: number
  theme: 'light' | 'dark' | 'sepia'
  onTextSelect: (text: string) => void
}

export function ReaderContent({ content, fontSize, theme, onTextSelect }: ReaderContentProps) {
  const themeClasses = {
    light: 'bg-white text-gray-900',
    dark: 'bg-gray-900 text-gray-100',
    sepia: 'bg-amber-50 text-amber-900'
  }
  
  return (
    <div 
      className={`p-6 ${themeClasses[theme]}`}
      style={{ fontSize: `${fontSize}px` }}
    >
      <div 
        className="prose max-w-none"
        dangerouslySetInnerHTML={{ __html: content }}
        onMouseUp={handleTextSelection}
      />
    </div>
  )
}
```

---

## 💳 Interface de Facturation

### Page d'Abonnement

```typescript
// app/billing/page.tsx
export default function BillingPage() {
  const { data: plans } = useGetSubscriptionPlansQuery()
  const { data: userBilling } = useGetUserBillingQuery()
  
  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Abonnements</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {plans?.map(plan => (
            <SubscriptionCard 
              key={plan.id}
              plan={plan}
              current={userBilling?.planId === plan.id}
            />
          ))}
        </div>
        
        <BillingHistory transactions={userBilling?.transactions} />
      </div>
    </MainLayout>
  )
}
```

### Paiement Mobile

```typescript
// components/billing/MobilePayment.tsx
interface MobilePaymentProps {
  amount: number
  currency: string
  onSuccess: (transactionId: string) => void
}

export function MobilePayment({ amount, currency, onSuccess }: MobilePaymentProps) {
  const [provider, setProvider] = useState<'orange' | 'mtn' | 'moov'>('orange')
  const [phoneNumber, setPhoneNumber] = useState('')
  
  const handlePayment = async () => {
    try {
      const response = await paymentAPI.initiateMobilePayment({
        provider,
        phoneNumber,
        amount,
        currency
      })
      
      // Polling pour vérifier le statut
      const transactionId = await pollPaymentStatus(response.transactionId)
      onSuccess(transactionId)
    } catch (error) {
      // Gestion d'erreur
    }
  }
  
  return (
    <div className="space-y-4">
      <ProviderSelector value={provider} onChange={setProvider} />
      <PhoneInput value={phoneNumber} onChange={setPhoneNumber} />
      <Button onClick={handlePayment} className="w-full">
        Payer {amount} {currency}
      </Button>
    </div>
  )
}
```

---

## 🌍 Internationalisation

### Configuration i18n

```typescript
// lib/i18n/config.ts
export const locales = ['fr', 'en', 'wo', 'ar'] as const
export type Locale = typeof locales[number]

export const defaultLocale: Locale = 'fr'

// Dictionnaires de traduction
export const translations = {
  fr: {
    common: {
      login: 'Connexion',
      register: 'Inscription',
      read: 'Lire',
      library: 'Bibliothèque'
    },
    catalog: {
      searchPlaceholder: 'Rechercher un livre...',
      filterByCategory: 'Filtrer par catégorie'
    }
  },
  en: {
    common: {
      login: 'Login',
      register: 'Register',
      read: 'Read',
      library: 'Library'
    }
  },
  wo: {
    common: {
      login: 'Dugg',
      register: 'Bind',
      read: 'Jàng',
      library: 'Biiblioteek'
    }
  }
}
```

### Hook de Traduction

```typescript
// lib/i18n/useTranslation.ts
export function useTranslation(locale: Locale = 'fr') {
  const t = useCallback((key: string) => {
    const keys = key.split('.')
    let value = translations[locale]
    
    for (const k of keys) {
      value = value?.[k]
    }
    
    return value || key
  }, [locale])
  
  return { t }
}
```

---

## 📱 Optimisation Mobile

### Responsive Design

```typescript
// components/common/ResponsiveLayout.tsx
export function ResponsiveLayout({ children }: { children: React.ReactNode }) {
  const [isMobile, setIsMobile] = useState(false)
  
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])
  
  return (
    <div className={`min-h-screen ${isMobile ? 'mobile-layout' : 'desktop-layout'}`}>
      {children}
    </div>
  )
}
```

### PWA Configuration

```typescript
// next.config.js
const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === 'development'
})

module.exports = withPWA({
  // Configuration Next.js
})
```

---

## 🧪 Stratégie de Tests

### Tests Unitaires

```typescript
// __tests__/components/BookCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { BookCard } from '@/components/catalog/BookCard'

describe('BookCard', () => {
  const mockBook = {
    id: '1',
    title: 'Test Book',
    author: 'Test Author',
    coverUrl: '/test-cover.jpg'
  }
  
  it('renders book information correctly', () => {
    render(<BookCard book={mockBook} onRead={jest.fn()} onAddToLibrary={jest.fn()} />)
    
    expect(screen.getByText('Test Book')).toBeInTheDocument()
    expect(screen.getByText('Test Author')).toBeInTheDocument()
  })
  
  it('calls onRead when read button is clicked', () => {
    const onRead = jest.fn()
    render(<BookCard book={mockBook} onRead={onRead} onAddToLibrary={jest.fn()} />)
    
    fireEvent.click(screen.getByText('Lire'))
    expect(onRead).toHaveBeenCalledWith('1')
  })
})
```

### Tests E2E

```typescript
// cypress/e2e/user-journey.cy.ts
describe('User Journey', () => {
  it('should allow user to login and read a book', () => {
    cy.visit('/login')
    
    // Login
    cy.get('[data-testid=email-input]').type('user@example.com')
    cy.get('[data-testid=password-input]').type('password')
    cy.get('[data-testid=login-button]').click()
    
    // Navigate to catalog
    cy.url().should('include', '/catalog')
    
    // Select a book
    cy.get('[data-testid=book-card]').first().click()
    cy.get('[data-testid=read-button]').click()
    
    // Verify reading interface
    cy.url().should('include', '/reading')
    cy.get('[data-testid=reader-content]').should('be.visible')
  })
})
```

---

## 🚀 Plan de Déploiement

### Configuration Vercel

```json
// vercel.json
{
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/next"
    }
  ],
  "env": {
    "NEXT_PUBLIC_API_URL": "https://api.coko.africa"
  },
  "regions": ["cdg1", "cpt1"],
  "functions": {
    "app/api/**/*.ts": {
      "maxDuration": 30
    }
  }
}
```

### Variables d'Environnement

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_ENV=development
NEXT_PUBLIC_SENTRY_DSN=your-sentry-dsn
NEXT_PUBLIC_ANALYTICS_ID=your-analytics-id
```

---

## 📊 Métriques et Performance

### Objectifs Performance
- **First Contentful Paint** : < 1.5s
- **Largest Contentful Paint** : < 2.5s
- **Cumulative Layout Shift** : < 0.1
- **Time to Interactive** : < 3s
- **Lighthouse Score** : > 90

### Optimisations
- **Images** : Next.js Image avec lazy loading
- **Fonts** : Préchargement des polices
- **Code Splitting** : Chargement dynamique des composants
- **Service Worker** : Cache des ressources statiques
- **CDN** : Distribution géographique

---

*Ce plan de développement frontend assure une expérience utilisateur optimale pour la plateforme Coko, adaptée aux besoins spécifiques du marché africain.*