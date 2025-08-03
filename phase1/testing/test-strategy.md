# Stratégie de Tests - Projet Coko

## 🎯 Objectifs de Test

### Couverture Cible
- **Backend** : 85% de couverture de code
- **Frontend** : 80% de couverture de code
- **APIs** : 100% des endpoints testés
- **E2E** : Tous les parcours utilisateur critiques

### Critères de Qualité
- **Performance** : APIs < 200ms, Frontend < 3s TTI
- **Sécurité** : 0 vulnérabilité critique
- **Accessibilité** : WCAG 2.1 AA
- **Compatibilité** : Chrome, Firefox, Safari, Mobile

---

## 🏗️ Pyramide de Tests

```
        E2E Tests (10%)
       ┌─────────────────┐
      │  User Journeys   │
     │   Integration     │
    └───────────────────┘
   
    Integration Tests (20%)
   ┌─────────────────────┐
  │   API Integration    │
 │   Service Communication│
└─────────────────────────┘

     Unit Tests (70%)
┌───────────────────────────┐
│    Components, Functions   │
│    Models, Services        │
│    Business Logic          │
└───────────────────────────┘
```

---

## 🧪 Tests Backend

### Tests Unitaires Django

#### Configuration
```python
# backend/pytest.ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = coko.settings_test
addopts = 
    --cov=.
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=85
    --reuse-db
    --nomigrations
testpaths = tests/
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

#### Tests des Modèles
```python
# tests/test_models.py
from django.test import TestCase
from django.core.exceptions import ValidationError
from shared_models.models import BookReference

class BookReferenceModelTest(TestCase):
    def setUp(self):
        self.book_data = {
            'book_uuid': uuid.uuid4(),
            'title': 'Test Book',
            'slug': 'test-book',
            'isbn': '978-0123456789'
        }
    
    def test_book_creation(self):
        """Test création d'une référence de livre"""
        book = BookReference.objects.create(**self.book_data)
        self.assertEqual(book.title, 'Test Book')
        self.assertTrue(book.is_active)
        self.assertIsNotNone(book.created_at)
    
    def test_slug_uniqueness(self):
        """Test unicité du slug"""
        BookReference.objects.create(**self.book_data)
        
        with self.assertRaises(ValidationError):
            duplicate_book = BookReference(**self.book_data)
            duplicate_book.full_clean()
    
    def test_string_representation(self):
        """Test représentation string"""
        book = BookReference.objects.create(**self.book_data)
        self.assertEqual(str(book), 'BookRef: Test Book')
```

#### Tests des Services
```python
# tests/test_billing_services.py
from django.test import TestCase
from unittest.mock import patch, Mock
from shared_models.billing_services import BillingService, RoyaltyService

class BillingServiceTest(TestCase):
    def setUp(self):
        self.billing_service = BillingService()
        self.user = self.create_test_user()
    
    def test_create_invoice(self):
        """Test création de facture"""
        invoice_data = {
            'user': self.user,
            'amount': 1000,
            'currency': 'XOF',
            'description': 'Abonnement mensuel'
        }
        
        invoice = self.billing_service.create_invoice(**invoice_data)
        
        self.assertEqual(invoice.amount, 1000)
        self.assertEqual(invoice.currency, 'XOF')
        self.assertEqual(invoice.status, 'pending')
    
    @patch('shared_models.billing_services.AfricanPaymentProvider')
    def test_mobile_payment_integration(self, mock_provider):
        """Test intégration paiement mobile"""
        mock_provider.return_value.initiate_payment.return_value = {
            'transaction_id': 'TXN123',
            'status': 'pending'
        }
        
        result = self.billing_service.process_mobile_payment(
            phone='221771234567',
            amount=1000,
            provider='orange'
        )
        
        self.assertEqual(result['transaction_id'], 'TXN123')
        mock_provider.return_value.initiate_payment.assert_called_once()

class RoyaltyServiceTest(TestCase):
    def test_calculate_author_royalties(self):
        """Test calcul des royalties d'auteur"""
        royalty_service = RoyaltyService()
        
        # Données de test
        sales_data = [
            {'book_id': 'book1', 'amount': 5000, 'author_rate': 0.15},
            {'book_id': 'book2', 'amount': 3000, 'author_rate': 0.20}
        ]
        
        royalties = royalty_service.calculate_author_royalties(
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31)
        )
        
        self.assertIsInstance(royalties, list)
        self.assertTrue(len(royalties) > 0)
```

#### Tests des APIs
```python
# tests/test_apis.py
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class AuthAPITest(APITestCase):
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def test_user_registration(self):
        """Test inscription utilisateur"""
        response = self.client.post('/api/v1/auth/register/', self.user_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access_token', response.data)
        self.assertTrue(User.objects.filter(email='test@example.com').exists())
    
    def test_user_login(self):
        """Test connexion utilisateur"""
        # Créer un utilisateur
        user = User.objects.create_user(**self.user_data)
        
        login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post('/api/v1/auth/login/', login_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
    
    def test_protected_endpoint(self):
        """Test endpoint protégé"""
        user = User.objects.create_user(**self.user_data)
        refresh = RefreshToken.for_user(user)
        
        # Sans token
        response = self.client.get('/api/v1/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Avec token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        response = self.client.get('/api/v1/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class CatalogAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.authenticate()
    
    def authenticate(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_get_books_list(self):
        """Test récupération liste des livres"""
        response = self.client.get('/api/v1/catalog/books/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
    
    def test_book_search(self):
        """Test recherche de livres"""
        response = self.client.get('/api/v1/catalog/books/?search=python')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Vérifier que les résultats contiennent le terme recherché
    
    def test_book_filters(self):
        """Test filtres de livres"""
        response = self.client.get('/api/v1/catalog/books/?category=programming&language=fr')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Vérifier que les filtres sont appliqués
```

### Tests d'Intégration

```python
# tests/test_integration.py
from django.test import TransactionTestCase
from django.db import transaction
from shared_models.models import BookReference, UserReference
from shared_models.services import SyncService

class ServiceIntegrationTest(TransactionTestCase):
    def test_cross_service_sync(self):
        """Test synchronisation entre services"""
        # Créer un livre dans catalog_service
        book_data = {
            'book_uuid': uuid.uuid4(),
            'title': 'Integration Test Book',
            'slug': 'integration-test-book'
        }
        
        book_ref = BookReference.objects.create(**book_data)
        
        # Déclencher la synchronisation
        sync_service = SyncService()
        result = sync_service.sync_book_to_reading_service(book_ref.book_uuid)
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['sync_id'])
    
    def test_billing_workflow(self):
        """Test workflow complet de facturation"""
        # Créer utilisateur
        user_ref = UserReference.objects.create(
            user_uuid=uuid.uuid4(),
            username='testuser',
            display_name='Test User'
        )
        
        # Créer facture
        billing_service = BillingService()
        invoice = billing_service.create_invoice(
            user=user_ref,
            amount=1000,
            currency='XOF'
        )
        
        # Simuler paiement
        payment_result = billing_service.process_payment(
            invoice_id=invoice.id,
            payment_method='mobile',
            provider='orange'
        )
        
        # Vérifier le résultat
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'paid')
        self.assertIsNotNone(payment_result['transaction_id'])
```

---

## 🎨 Tests Frontend

### Configuration Jest

```javascript
// jest.config.js
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './'
})

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapping: {
    '^@/components/(.*)$': '<rootDir>/components/$1',
    '^@/lib/(.*)$': '<rootDir>/lib/$1',
    '^@/app/(.*)$': '<rootDir>/app/$1'
  },
  testEnvironment: 'jest-environment-jsdom',
  collectCoverageFrom: [
    'components/**/*.{js,jsx,ts,tsx}',
    'lib/**/*.{js,jsx,ts,tsx}',
    'app/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
}

module.exports = createJestConfig(customJestConfig)
```

### Tests de Composants

```typescript
// __tests__/components/BookCard.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import { BookCard } from '@/components/catalog/BookCard'
import { authSlice } from '@/lib/store/authSlice'

const mockStore = configureStore({
  reducer: {
    auth: authSlice.reducer
  },
  preloadedState: {
    auth: {
      user: { id: '1', name: 'Test User' },
      isAuthenticated: true,
      loading: false
    }
  }
})

const renderWithProvider = (component: React.ReactElement) => {
  return render(
    <Provider store={mockStore}>
      {component}
    </Provider>
  )
}

describe('BookCard Component', () => {
  const mockBook = {
    id: '1',
    title: 'Test Book',
    author: 'Test Author',
    coverUrl: '/test-cover.jpg',
    description: 'Test description',
    price: 1000,
    currency: 'XOF'
  }

  const mockProps = {
    book: mockBook,
    onRead: jest.fn(),
    onAddToLibrary: jest.fn(),
    onPurchase: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders book information correctly', () => {
    renderWithProvider(<BookCard {...mockProps} />)
    
    expect(screen.getByText('Test Book')).toBeInTheDocument()
    expect(screen.getByText('Test Author')).toBeInTheDocument()
    expect(screen.getByText('1000 XOF')).toBeInTheDocument()
  })

  it('calls onRead when read button is clicked', async () => {
    renderWithProvider(<BookCard {...mockProps} />)
    
    const readButton = screen.getByRole('button', { name: /lire/i })
    fireEvent.click(readButton)
    
    await waitFor(() => {
      expect(mockProps.onRead).toHaveBeenCalledWith('1')
    })
  })

  it('shows loading state during purchase', async () => {
    const mockPurchase = jest.fn().mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    )
    
    renderWithProvider(
      <BookCard {...mockProps} onPurchase={mockPurchase} />
    )
    
    const purchaseButton = screen.getByRole('button', { name: /acheter/i })
    fireEvent.click(purchaseButton)
    
    expect(screen.getByText(/chargement/i)).toBeInTheDocument()
    
    await waitFor(() => {
      expect(screen.queryByText(/chargement/i)).not.toBeInTheDocument()
    })
  })

  it('handles error states gracefully', async () => {
    const mockPurchase = jest.fn().mockRejectedValue(new Error('Payment failed'))
    
    renderWithProvider(
      <BookCard {...mockProps} onPurchase={mockPurchase} />
    )
    
    const purchaseButton = screen.getByRole('button', { name: /acheter/i })
    fireEvent.click(purchaseButton)
    
    await waitFor(() => {
      expect(screen.getByText(/erreur/i)).toBeInTheDocument()
    })
  })
})
```

### Tests de Hooks

```typescript
// __tests__/hooks/useAuth.test.tsx
import { renderHook, act } from '@testing-library/react'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import { useAuth } from '@/lib/hooks/useAuth'
import { authSlice } from '@/lib/store/authSlice'

const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      auth: authSlice.reducer
    },
    preloadedState: {
      auth: {
        user: null,
        isAuthenticated: false,
        loading: false,
        ...initialState
      }
    }
  })
}

const wrapper = ({ children, store }: any) => (
  <Provider store={store}>{children}</Provider>
)

describe('useAuth Hook', () => {
  it('returns initial auth state', () => {
    const store = createMockStore()
    const { result } = renderHook(() => useAuth(), {
      wrapper: ({ children }) => wrapper({ children, store })
    })
    
    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.user).toBe(null)
    expect(result.current.loading).toBe(false)
  })

  it('handles login correctly', async () => {
    const store = createMockStore()
    const { result } = renderHook(() => useAuth(), {
      wrapper: ({ children }) => wrapper({ children, store })
    })
    
    await act(async () => {
      await result.current.login('test@example.com', 'password')
    })
    
    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.user).toBeTruthy()
  })

  it('handles logout correctly', async () => {
    const store = createMockStore({
      user: { id: '1', email: 'test@example.com' },
      isAuthenticated: true
    })
    
    const { result } = renderHook(() => useAuth(), {
      wrapper: ({ children }) => wrapper({ children, store })
    })
    
    await act(async () => {
      result.current.logout()
    })
    
    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.user).toBe(null)
  })
})
```

---

## 🔄 Tests E2E avec Cypress

### Configuration Cypress

```typescript
// cypress.config.ts
import { defineConfig } from 'cypress'

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    supportFile: 'cypress/support/e2e.ts',
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    viewportWidth: 1280,
    viewportHeight: 720,
    video: true,
    screenshotOnRunFailure: true,
    defaultCommandTimeout: 10000,
    requestTimeout: 10000,
    responseTimeout: 10000
  },
  component: {
    devServer: {
      framework: 'next',
      bundler: 'webpack'
    }
  }
})
```

### Tests de Parcours Utilisateur

```typescript
// cypress/e2e/user-journey.cy.ts
describe('Complete User Journey', () => {
  beforeEach(() => {
    // Reset database state
    cy.task('db:seed')
  })

  it('should complete full user registration and book reading flow', () => {
    // 1. Visit homepage
    cy.visit('/')
    cy.get('[data-testid=hero-section]').should('be.visible')
    
    // 2. Navigate to registration
    cy.get('[data-testid=register-button]').click()
    cy.url().should('include', '/register')
    
    // 3. Fill registration form
    cy.get('[data-testid=email-input]').type('newuser@example.com')
    cy.get('[data-testid=password-input]').type('SecurePass123!')
    cy.get('[data-testid=confirm-password-input]').type('SecurePass123!')
    cy.get('[data-testid=first-name-input]').type('John')
    cy.get('[data-testid=last-name-input]').type('Doe')
    cy.get('[data-testid=country-select]').select('Sénégal')
    
    // 4. Submit registration
    cy.get('[data-testid=register-submit]').click()
    
    // 5. Verify redirect to catalog
    cy.url().should('include', '/catalog')
    cy.get('[data-testid=welcome-message]').should('contain', 'Bienvenue John')
    
    // 6. Search for a book
    cy.get('[data-testid=search-input]').type('Python')
    cy.get('[data-testid=search-button]').click()
    
    // 7. Select a book
    cy.get('[data-testid=book-card]').first().click()
    cy.url().should('include', '/books/')
    
    // 8. Start reading
    cy.get('[data-testid=read-button]').click()
    cy.url().should('include', '/reading/')
    
    // 9. Verify reading interface
    cy.get('[data-testid=reader-content]').should('be.visible')
    cy.get('[data-testid=reading-progress]').should('be.visible')
    
    // 10. Navigate through pages
    cy.get('[data-testid=next-page-button]').click()
    cy.get('[data-testid=page-indicator]').should('contain', '2')
    
    // 11. Add bookmark
    cy.get('[data-testid=bookmark-button]').click()
    cy.get('[data-testid=bookmark-success]').should('be.visible')
    
    // 12. Access profile
    cy.get('[data-testid=user-menu]').click()
    cy.get('[data-testid=profile-link]').click()
    
    // 13. Verify reading history
    cy.url().should('include', '/profile')
    cy.get('[data-testid=reading-history]').should('contain', 'Python')
  })

  it('should handle mobile payment flow', () => {
    // Login first
    cy.login('user@example.com', 'password')
    
    // Navigate to subscription
    cy.visit('/billing')
    
    // Select premium plan
    cy.get('[data-testid=premium-plan]').click()
    cy.get('[data-testid=subscribe-button]').click()
    
    // Choose mobile payment
    cy.get('[data-testid=payment-method-mobile]').click()
    
    // Select Orange Money
    cy.get('[data-testid=provider-orange]').click()
    
    // Enter phone number
    cy.get('[data-testid=phone-input]').type('221771234567')
    
    // Confirm payment
    cy.get('[data-testid=confirm-payment]').click()
    
    // Verify payment processing
    cy.get('[data-testid=payment-processing]').should('be.visible')
    
    // Mock payment success (in real test, would wait for webhook)
    cy.intercept('GET', '/api/v1/billing/payment-status/*', {
      statusCode: 200,
      body: { status: 'completed' }
    })
    
    // Verify success
    cy.get('[data-testid=payment-success]', { timeout: 15000 })
      .should('be.visible')
    
    // Verify subscription activation
    cy.get('[data-testid=subscription-status]')
      .should('contain', 'Premium')
  })
})
```

### Tests de Performance

```typescript
// cypress/e2e/performance.cy.ts
describe('Performance Tests', () => {
  it('should load pages within performance budgets', () => {
    // Test homepage performance
    cy.visit('/', {
      onBeforeLoad: (win) => {
        win.performance.mark('start')
      },
      onLoad: (win) => {
        win.performance.mark('end')
        win.performance.measure('pageLoad', 'start', 'end')
        
        const measure = win.performance.getEntriesByName('pageLoad')[0]
        expect(measure.duration).to.be.lessThan(3000) // 3s budget
      }
    })
    
    // Test catalog page performance
    cy.visit('/catalog')
    
    // Measure time to interactive
    cy.get('[data-testid=book-grid]').should('be.visible')
    cy.window().then((win) => {
      const navigation = win.performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
      const tti = navigation.loadEventEnd - navigation.navigationStart
      expect(tti).to.be.lessThan(5000) // 5s TTI budget
    })
  })

  it('should handle large datasets efficiently', () => {
    // Load page with many books
    cy.intercept('GET', '/api/v1/catalog/books*', {
      fixture: 'large-book-dataset.json'
    })
    
    cy.visit('/catalog')
    
    // Verify virtual scrolling works
    cy.get('[data-testid=book-card]').should('have.length.lessThan', 50)
    
    // Scroll and verify more items load
    cy.scrollTo('bottom')
    cy.get('[data-testid=book-card]').should('have.length.greaterThan', 50)
  })
})
```

---

## 🔒 Tests de Sécurité

### Tests d'Authentification

```python
# tests/test_security.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
import jwt
from datetime import datetime, timedelta

User = get_user_model()

class SecurityTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='SecurePass123!'
        )
    
    def test_jwt_token_expiration(self):
        """Test expiration des tokens JWT"""
        # Login pour obtenir un token
        response = self.client.post('/api/v1/auth/login/', {
            'email': 'test@example.com',
            'password': 'SecurePass123!'
        })
        
        token = response.data['access_token']
        
        # Décoder le token pour vérifier l'expiration
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp_time = datetime.fromtimestamp(decoded['exp'])
        
        # Vérifier que le token expire dans moins de 1 heure
        self.assertLess(
            exp_time - datetime.now(),
            timedelta(hours=1)
        )
    
    def test_password_strength_validation(self):
        """Test validation de la force du mot de passe"""
        weak_passwords = [
            '123456',
            'password',
            'azerty',
            'test123'
        ]
        
        for weak_password in weak_passwords:
            response = self.client.post('/api/v1/auth/register/', {
                'email': 'weak@example.com',
                'username': 'weakuser',
                'password': weak_password,
                'first_name': 'Test',
                'last_name': 'User'
            })
            
            self.assertEqual(response.status_code, 400)
            self.assertIn('password', response.data)
    
    def test_rate_limiting(self):
        """Test limitation du taux de requêtes"""
        # Tenter plusieurs connexions échouées
        for i in range(10):
            response = self.client.post('/api/v1/auth/login/', {
                'email': 'test@example.com',
                'password': 'wrongpassword'
            })
        
        # La 11ème tentative devrait être bloquée
        response = self.client.post('/api/v1/auth/login/', {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, 429)  # Too Many Requests
    
    def test_sql_injection_protection(self):
        """Test protection contre l'injection SQL"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --"
        ]
        
        for malicious_input in malicious_inputs:
            response = self.client.post('/api/v1/auth/login/', {
                'email': malicious_input,
                'password': 'password'
            })
            
            # Vérifier que l'injection n'a pas fonctionné
            self.assertNotEqual(response.status_code, 200)
    
    def test_xss_protection(self):
        """Test protection contre XSS"""
        xss_payloads = [
            '<script>alert("XSS")</script>',
            'javascript:alert("XSS")',
            '<img src=x onerror=alert("XSS")>'
        ]
        
        for payload in xss_payloads:
            response = self.client.post('/api/v1/catalog/books/', {
                'title': payload,
                'description': payload
            })
            
            # Vérifier que le payload est échappé
            if response.status_code == 201:
                self.assertNotIn('<script>', str(response.data))
                self.assertNotIn('javascript:', str(response.data))
```

---

## 📊 Rapports et Métriques

### Configuration Coverage

```python
# .coveragerc
[run]
source = .
omit = 
    */venv/*
    */migrations/*
    */tests/*
    manage.py
    */settings/*
    */node_modules/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:

[html]
directory = htmlcov
```

### Scripts de Test

```bash
#!/bin/bash
# scripts/run-tests.sh

echo "🧪 Running Backend Tests..."
cd backend
python -m pytest --cov=. --cov-report=html --cov-report=term

echo "🎨 Running Frontend Tests..."
cd ../frontend
npm run test:coverage

echo "🔄 Running E2E Tests..."
npm run cypress:run

echo "🔒 Running Security Tests..."
python -m pytest tests/test_security.py -v

echo "⚡ Running Performance Tests..."
npm run test:performance

echo "📊 Generating Reports..."
python scripts/generate_test_report.py
```

### Intégration CI/CD

```yaml
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        cd backend
        python -m pytest --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Run tests
      run: |
        cd frontend
        npm run test:coverage
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./frontend/coverage/lcov.info

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Start services
      run: |
        docker-compose -f docker-compose.test.yml up -d
    
    - name: Wait for services
      run: |
        sleep 30
    
    - name: Run E2E tests
      run: |
        cd frontend
        npm run cypress:run
    
    - name: Upload test artifacts
      uses: actions/upload-artifact@v3
      if: failure()
      with:
        name: cypress-screenshots
        path: frontend/cypress/screenshots
```

---

## 🎯 Critères de Validation

### Seuils de Qualité

| Métrique | Seuil Minimum | Seuil Cible |
|----------|---------------|-------------|
| Couverture Backend | 80% | 85% |
| Couverture Frontend | 75% | 80% |
| Tests E2E | 90% parcours | 100% parcours |
| Performance API | < 300ms | < 200ms |
| Performance Frontend | < 5s TTI | < 3s TTI |
| Accessibilité | WCAG AA | WCAG AAA |
| Sécurité | 0 critique | 0 haute |

### Checklist de Validation

- [ ] Tous les tests unitaires passent
- [ ] Couverture de code atteinte
- [ ] Tests d'intégration validés
- [ ] Parcours E2E fonctionnels
- [ ] Performance dans les budgets
- [ ] Sécurité auditée
- [ ] Accessibilité validée
- [ ] Tests mobiles réussis
- [ ] Documentation à jour
- [ ] Rapports générés

---

*Cette stratégie de tests assure la qualité et la fiabilité de la plateforme Coko à tous les niveaux, du code aux parcours utilisateur complets.*