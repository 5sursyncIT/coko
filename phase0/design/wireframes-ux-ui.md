# Coko Platform - Wireframes UX/UI & Design System

## Table des Matières
1. [Principes de Design](#principes-de-design)
2. [Architecture de l'Information](#architecture-de-linformation)
3. [Wireframes Détaillés](#wireframes-détaillés)
4. [Design System](#design-system)
5. [Optimisations Africaines](#optimisations-africaines)

---

## Principes de Design

### 1. Mobile First
- **Priorité absolue** : Conception pour smartphones (écrans 360px-414px)
- Interface tactile optimisée avec zones de touche ≥ 44px
- Navigation par gestes intuitifs
- Chargement progressif du contenu

### 2. Accessibilité
- Contraste minimum WCAG AA (4.5:1)
- Support des lecteurs d'écran
- Navigation au clavier
- Tailles de police ajustables
- Support des langues RTL (arabe)

### 3. Performance
- Temps de chargement < 3 secondes sur 3G
- Images optimisées et lazy loading
- Mise en cache intelligente
- Mode hors ligne pour la lecture

### 4. Localisation
- Support multilingue (Français, Anglais, Wolof, Arabe)
- Adaptation culturelle des couleurs et symboles
- Formats de date/heure locaux
- Devises locales (XOF, EUR, USD)

### 5. Simplicité
- Interface épurée et intuitive
- Hiérarchie visuelle claire
- Actions principales mises en évidence
- Feedback utilisateur immédiat

---

## Architecture de l'Information

### Navigation Principale
```
Coko App
├── Accueil
│   ├── Livres recommandés
│   ├── Nouveautés
│   ├── Tendances
│   └── Continuer la lecture
├── Catalogue
│   ├── Recherche
│   ├── Catégories
│   ├── Auteurs
│   └── Filtres
├── Ma Bibliothèque
│   ├── En cours
│   ├── Terminés
│   ├── Favoris
│   └── Téléchargés
├── Communauté
│   ├── Forums
│   ├── Clubs de lecture
│   ├── Discussions
│   └── Événements
└── Profil
    ├── Statistiques
    ├── Badges
    ├── Paramètres
    └── Abonnement
```

---

## Wireframes Détaillés

### 1. Écrans d'Authentification

#### 1.1 Écran de Connexion
```
┌─────────────────────────────────────┐
│  [Logo Coko]                       │
│                                     │
│  Bienvenue sur Coko                 │
│  Votre bibliothèque numérique       │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 📧 Email                        │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 🔒 Mot de passe                 │ │
│  └─────────────────────────────────┘ │
│                                     │
│  [ Mot de passe oublié? ]           │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │        SE CONNECTER             │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ────────── ou ──────────           │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 📱 Orange Money                 │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 💳 Wave                         │ │
│  └─────────────────────────────────┘ │
│                                     │
│  Pas de compte? [S'inscrire]        │
└─────────────────────────────────────┘
```

#### 1.2 Écran d'Inscription
```
┌─────────────────────────────────────┐
│  [← Retour]    Inscription          │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 👤 Prénom                       │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 👤 Nom                          │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 📧 Email                        │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 📱 Téléphone                    │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 🌍 Pays ▼                       │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 🗣️ Langue ▼                     │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 🔒 Mot de passe                 │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ☑️ J'accepte les conditions        │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │        S'INSCRIRE               │ │
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 2. Écran d'Accueil

```
┌─────────────────────────────────────┐
│  [🔍] Coko [🔔] [👤]               │
│                                     │
│  Bonjour Aminata! 👋                │
│  Prête pour une nouvelle lecture?   │
│                                     │
│  ┌─ Continuer la lecture ─────────┐ │
│  │ [📖] "Sous l'orage"             │ │
│  │      Seydou Badian             │ │
│  │      ████████░░ 80%            │ │
│  │      [CONTINUER]               │ │
│  └─────────────────────────────────┘ │
│                                     │
│  📚 Recommandés pour vous           │
│  ┌───┐ ┌───┐ ┌───┐ ┌───┐          │
│  │[📖]│ │[📖]│ │[📖]│ │[📖]│ [→]     │
│  │Livre│ │Livre│ │Livre│ │Livre│          │
│  └───┘ └───┘ └───┘ └───┘          │
│                                     │
│  🔥 Tendances                       │
│  ┌───┐ ┌───┐ ┌───┐ ┌───┐          │
│  │[📖]│ │[📖]│ │[📖]│ │[📖]│ [→]     │
│  │Livre│ │Livre│ │Livre│ │Livre│          │
│  └───┘ └───┘ └───┘ └───┘          │
│                                     │
│  🆕 Nouveautés                      │
│  ┌───┐ ┌───┐ ┌───┐ ┌───┐          │
│  │[📖]│ │[📖]│ │[📖]│ │[📖]│ [→]     │
│  │Livre│ │Livre│ │Livre│ │Livre│          │
│  └───┘ └───┘ └───┘ └───┘          │
│                                     │
│  🏆 Votre progression               │
│  Niveau 5 • 1,250 points           │
│  ████████░░ 80% vers niveau 6      │
│                                     │
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │
│ │ 🏠  │ │ 📚  │ │ 📖  │ │ 👥  │ │ 👤│
│ │Accueil│Catalogue│Biblio│Communauté│Profil│
│ └─────┘ └─────┘ └─────┘ └─────┘   │
└─────────────────────────────────────┘
```

### 3. Catalogue et Recherche

#### 3.1 Écran Catalogue
```
┌─────────────────────────────────────┐
│  [←] Catalogue [🔍] [⚙️]            │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 🔍 Rechercher un livre...       │ │
│  └─────────────────────────────────┘ │
│                                     │
│  📂 Catégories                      │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │
│  │📚   │ │🔬   │ │🏛️   │ │💡   │   │
│  │Litt.│ │Sci. │ │Hist.│ │Phil.│   │
│  └─────┘ └─────┘ └─────┘ └─────┘   │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │
│  │🎓   │ │👤   │ │💻   │ │🌍   │   │
│  │Éduc.│ │Dev. │ │Tech.│ │Afr. │   │
│  └─────┘ └─────┘ └─────┘ └─────┘   │
│                                     │
│  🔥 Livres populaires               │
│  ┌─────────────────────────────────┐ │
│  │ [📖] "Une si longue lettre"     │ │
│  │      Mariama Bâ                │ │
│  │      ⭐⭐⭐⭐⭐ (4.8) • Gratuit   │ │
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │ [📖] "L'Aventure ambiguë"       │ │
│  │      Cheikh Hamidou Kane       │ │
│  │      ⭐⭐⭐⭐⭐ (4.7) • 1,500 XOF │ │
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │ [📖] "Sous l'orage"             │ │
│  │      Seydou Badian             │ │
│  │      ⭐⭐⭐⭐☆ (4.2) • Premium   │ │
│  └─────────────────────────────────┘ │
│                                     │
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │
│ │ 🏠  │ │ 📚  │ │ 📖  │ │ 👥  │ │ 👤│
│ │Accueil│Catalogue│Biblio│Communauté│Profil│
│ └─────┘ └─────┘ └─────┘ └─────┘   │
└─────────────────────────────────────┘
```

#### 3.2 Détail d'un Livre
```
┌─────────────────────────────────────┐
│  [←] [❤️] [📤] [⋮]                  │
│                                     │
│  ┌─────┐                           │
│  │     │  "Une si longue lettre"    │
│  │ 📖  │  Mariama Bâ                │
│  │     │                           │
│  └─────┘  ⭐⭐⭐⭐⭐ 4.8 (1,234)      │
│           📚 Littérature • 🇸🇳 Sénégal│
│           📄 128 pages • 🗣️ Français │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │         LIRE GRATUITEMENT       │ │
│  └─────────────────────────────────┘ │
│  [ ⬇️ Télécharger ] [ ➕ Ma liste ]  │
│                                     │
│  📝 Résumé                          │
│  Roman épistolaire qui raconte      │
│  l'histoire de Ramatoulaye qui      │
│  écrit à son amie Aissatou...       │
│  [Lire plus]                        │
│                                     │
│  👤 À propos de l'auteur            │
│  Mariama Bâ (1929-1981) était une  │
│  écrivaine sénégalaise...           │
│  [Voir plus]                        │
│                                     │
│  ⭐ Avis des lecteurs (1,234)       │
│  ┌─────────────────────────────────┐ │
│  │ Fatou K. ⭐⭐⭐⭐⭐               │ │
│  │ "Un chef-d'œuvre de la          │ │
│  │ littérature africaine..."       │ │
│  │ Il y a 2 jours                  │ │
│  └─────────────────────────────────┘ │
│  [Voir tous les avis]               │
│                                     │
│  📚 Livres similaires              │
│  ┌───┐ ┌───┐ ┌───┐ ┌───┐          │
│  │[📖]│ │[📖]│ │[📖]│ │[📖]│          │
│  └───┘ └───┘ └───┘ └───┘          │
└─────────────────────────────────────┘
```

### 4. Interface de Lecture

```
┌─────────────────────────────────────┐
│  [←] [🔖] [💡] [Aa] [⋮]             │
│                                     │
│                                     │
│    Chapitre 1                       │
│    La lettre                        │
│                                     │
│    Aissatou, mon amie,              │
│                                     │
│    Je reçois ton mot. Tu oses       │
│    penser à moi ! Ton cœur          │
│    devine le mien. Tu as            │
│    toujours su deviner.             │
│                                     │
│    Hier, tu as divorcé. Moi,        │
│    je suis veuve depuis             │
│    trois mois.                      │
│                                     │
│    Je ne te condamne pas.           │
│    Je ne te plains pas non          │
│    plus. Je t'analyse.              │
│                                     │
│                                     │
│  ────────────────────────────────   │
│  Page 12 sur 128 • 9%              │
│  ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│                                     │
│  [⏮️] [⏭️] [🔖] [✏️] [💬]            │
└─────────────────────────────────────┘
```

### 5. Ma Bibliothèque

```
┌─────────────────────────────────────┐
│  Ma Bibliothèque [🔍] [⚙️]          │
│                                     │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │
│  │En   │ │Ter- │ │Fav- │ │Télé-│   │
│  │cours│ │minés│ │oris │ │chargés│   │
│  │ (5) │ │(12) │ │(8)  │ │(3)  │   │
│  └─────┘ └─────┘ └─────┘ └─────┘   │
│                                     │
│  📖 En cours de lecture             │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ [📖] "Sous l'orage"             │ │
│  │      Seydou Badian             │ │
│  │      ████████░░ 80%            │ │
│  │      Dernière lecture: hier    │ │
│  │      [CONTINUER]               │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ [📖] "L'Aventure ambiguë"       │ │
│  │      Cheikh Hamidou Kane       │ │
│  │      ███░░░░░░░ 30%            │ │
│  │      Dernière lecture: 3 jours │ │
│  │      [CONTINUER]               │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ [📖] "Une si longue lettre"     │ │
│  │      Mariama Bâ                │ │
│  │      █░░░░░░░░░ 10%            │ │
│  │      Dernière lecture: 1 semaine│ │
│  │      [CONTINUER]               │ │
│  └─────────────────────────────────┘ │
│                                     │
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │
│ │ 🏠  │ │ 📚  │ │ 📖  │ │ 👥  │ │ 👤│
│ │Accueil│Catalogue│Biblio│Communauté│Profil│
│ └─────┘ └─────┘ └─────┘ └─────┘   │
└─────────────────────────────────────┘
```

### 6. Communauté

```
┌─────────────────────────────────────┐
│  Communauté [🔍] [➕]               │
│                                     │
│  ┌─────┐ ┌─────┐ ┌─────┐           │
│  │💬   │ │📚   │ │🎉   │           │
│  │Forums│Clubs │Événements│           │
│  └─────┘ └─────┘ └─────┘           │
│                                     │
│  🔥 Discussions populaires          │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 💬 "Vos livres africains        │ │
│  │    préférés?"                   │ │
│  │    📚 Littérature Africaine     │ │
│  │    👤 Aminata D. • 23 réponses  │ │
│  │    🕐 Il y a 2 heures           │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 💬 "Conseils pour lire plus"    │ │
│  │    🎯 Développement Personnel   │ │
│  │    👤 Moussa K. • 15 réponses   │ │
│  │    🕐 Il y a 4 heures           │ │
│  └─────────────────────────────────┘ │
│                                     │
│  📚 Clubs actifs                    │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 📖 "Club Littérature Féminine"  │ │
│  │    👥 45 membres                │ │
│  │    📚 Livre actuel: "Riwan"     │ │
│  │    🗓️ Discussion: Demain 19h    │ │
│  │    [REJOINDRE]                 │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 📖 "Jeunes Auteurs Africains"   │ │
│  │    👥 32 membres                │ │
│  │    📚 Livre actuel: "Bleu Blanc Rouge"│
│  │    🗓️ Discussion: Vendredi 20h  │ │
│  │    [REJOINDRE]                 │ │
│  └─────────────────────────────────┘ │
│                                     │
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │
│ │ 🏠  │ │ 📚  │ │ 📖  │ │ 👥  │ │ 👤│
│ │Accueil│Catalogue│Biblio│Communauté│Profil│
│ └─────┘ └─────┘ └─────┘ └─────┘   │
└─────────────────────────────────────┘
```

### 7. Profil et Gamification

```
┌─────────────────────────────────────┐
│  [←] Profil [⚙️]                    │
│                                     │
│  ┌─────┐                           │
│  │ 👤  │  Aminata Diallo             │
│  │     │  @aminata_d                │
│  └─────┘  📍 Dakar, Sénégal         │
│           📅 Membre depuis mars 2024│
│                                     │
│  🏆 Niveau 5 • 1,250 points         │
│  ████████░░ 80% vers niveau 6       │
│                                     │
│  📊 Statistiques                    │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │
│  │ 23  │ │ 15  │ │ 8   │ │ 45  │   │
│  │Livres│Terminés│Badges│Jours │   │
│  │lus  │       │     │série │   │
│  └─────┘ └─────┘ └─────┘ └─────┘   │
│                                     │
│  🏅 Badges récents                  │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │
│  │ 🥇  │ │ 📚  │ │ 🔥  │ │ ✍️  │   │
│  │Premier│Lecteur│Série │Annot-│   │
│  │Livre │Assidu │de 30 │ateur │   │
│  └─────┘ └─────┘ └─────┘ └─────┘   │
│  [Voir tous les badges]             │
│                                     │
│  📈 Classement                      │
│  🥈 2ème cette semaine              │
│  🥉 3ème ce mois                    │
│  🏆 Top 10 général                  │
│                                     │
│  💳 Abonnement Premium              │
│  ✅ Actif jusqu'au 15 mars 2025     │
│  [Gérer l'abonnement]              │
│                                     │
│  ⚙️ Actions                         │
│  [Modifier le profil]              │
│  [Paramètres]                      │
│  [Aide et support]                 │
│  [Se déconnecter]                  │
│                                     │
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │
│ │ 🏠  │ │ 📚  │ │ 📖  │ │ 👥  │ │ 👤│
│ │Accueil│Catalogue│Biblio│Communauté│Profil│
│ └─────┘ └─────┘ └─────┘ └─────┘   │
└─────────────────────────────────────┘
```

---

## Design System

### 1. Palette de Couleurs

#### Couleurs Principales
```css
/* Couleurs inspirées de l'Afrique */
--primary-orange: #FF6B35;      /* Orange vif (soleil africain) */
--primary-green: #2E8B57;       /* Vert forêt (nature africaine) */
--primary-gold: #FFD700;        /* Or (richesse culturelle) */
--primary-terracotta: #CD853F;  /* Terre cuite (artisanat) */

/* Couleurs secondaires */
--secondary-blue: #4A90E2;      /* Bleu ciel */
--secondary-purple: #8E44AD;    /* Violet royal */
--secondary-teal: #16A085;      /* Turquoise */

/* Couleurs neutres */
--neutral-dark: #2C3E50;        /* Gris foncé */
--neutral-medium: #7F8C8D;      /* Gris moyen */
--neutral-light: #ECF0F1;       /* Gris clair */
--neutral-white: #FFFFFF;       /* Blanc pur */

/* Couleurs système */
--success: #27AE60;             /* Vert succès */
--warning: #F39C12;             /* Orange avertissement */
--error: #E74C3C;               /* Rouge erreur */
--info: #3498DB;                /* Bleu information */
```

#### Mode Sombre
```css
/* Adaptation pour le mode sombre */
--dark-bg-primary: #1A1A1A;     /* Fond principal */
--dark-bg-secondary: #2D2D2D;   /* Fond secondaire */
--dark-text-primary: #FFFFFF;   /* Texte principal */
--dark-text-secondary: #B0B0B0; /* Texte secondaire */
```

### 2. Typographie

#### Polices
```css
/* Police principale - Support multilingue */
--font-primary: 'Inter', 'Noto Sans', 'Roboto', sans-serif;

/* Police pour l'arabe */
--font-arabic: 'Noto Sans Arabic', 'Arial', sans-serif;

/* Police pour les titres */
--font-heading: 'Poppins', 'Inter', sans-serif;

/* Police monospace pour le code */
--font-mono: 'JetBrains Mono', 'Consolas', monospace;
```

#### Échelle Typographique
```css
/* Tailles de police (Mobile First) */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
--text-4xl: 2.25rem;   /* 36px */

/* Hauteurs de ligne */
--leading-tight: 1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.75;

/* Poids de police */
--font-light: 300;
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### 3. Espacement

```css
/* Système d'espacement (8px base) */
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
--space-20: 5rem;     /* 80px */
```

### 4. Composants UI

#### Boutons
```css
/* Bouton principal */
.btn-primary {
  background: var(--primary-orange);
  color: var(--neutral-white);
  padding: var(--space-3) var(--space-6);
  border-radius: 8px;
  font-weight: var(--font-medium);
  min-height: 44px; /* Accessibilité tactile */
  transition: all 0.2s ease;
}

.btn-primary:hover {
  background: #E55A2B; /* Orange plus foncé */
  transform: translateY(-1px);
}

/* Bouton secondaire */
.btn-secondary {
  background: transparent;
  color: var(--primary-orange);
  border: 2px solid var(--primary-orange);
  padding: var(--space-3) var(--space-6);
  border-radius: 8px;
}

/* Bouton fantôme */
.btn-ghost {
  background: transparent;
  color: var(--neutral-dark);
  padding: var(--space-2) var(--space-4);
}
```

#### Cartes
```css
.card {
  background: var(--neutral-white);
  border-radius: 12px;
  padding: var(--space-4);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.card-book {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-3);
}
```

#### Champs de Saisie
```css
.input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border: 2px solid var(--neutral-light);
  border-radius: 8px;
  font-size: var(--text-base);
  transition: border-color 0.2s ease;
}

.input:focus {
  outline: none;
  border-color: var(--primary-orange);
  box-shadow: 0 0 0 3px rgba(255, 107, 53, 0.1);
}

.input-error {
  border-color: var(--error);
}
```

### 5. Iconographie

#### Système d'Icônes
- **Bibliothèque** : Feather Icons + Phosphor Icons
- **Taille standard** : 24px (mobile), 20px (desktop)
- **Style** : Outline pour la navigation, Filled pour les actions
- **Couleurs** : Héritent de la couleur du texte parent

#### Icônes Spécifiques
```
📚 Catalogue
📖 Lecture
👥 Communauté
👤 Profil
🔍 Recherche
❤️ Favoris
⬇️ Téléchargement
🔔 Notifications
⚙️ Paramètres
🏆 Badges/Récompenses
📊 Statistiques
💬 Discussions
🌍 Langues/Pays
💳 Paiement
```

### 6. Animations

#### Transitions
```css
/* Transitions standard */
.transition-fast { transition: all 0.15s ease; }
.transition-normal { transition: all 0.2s ease; }
.transition-slow { transition: all 0.3s ease; }

/* Animations de chargement */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes slideIn {
  from { transform: translateX(-100%); }
  to { transform: translateX(0); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
```

### 7. Responsive Design

#### Breakpoints
```css
/* Mobile First Approach */
--mobile: 320px;      /* Petit mobile */
--mobile-lg: 414px;   /* Grand mobile */
--tablet: 768px;      /* Tablette */
--desktop: 1024px;    /* Desktop */
--desktop-lg: 1440px; /* Grand desktop */

/* Media queries */
@media (min-width: 768px) {
  /* Styles tablette */
}

@media (min-width: 1024px) {
  /* Styles desktop */
}
```

#### Grille
```css
.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--space-4);
}

.grid {
  display: grid;
  gap: var(--space-4);
}

.grid-2 { grid-template-columns: repeat(2, 1fr); }
.grid-3 { grid-template-columns: repeat(3, 1fr); }
.grid-4 { grid-template-columns: repeat(4, 1fr); }

@media (max-width: 767px) {
  .grid-2, .grid-3, .grid-4 {
    grid-template-columns: 1fr;
  }
}
```

### 8. Accessibilité

#### Contrastes
- **Texte normal** : Ratio 4.5:1 minimum
- **Texte large** : Ratio 3:1 minimum
- **Éléments interactifs** : Ratio 3:1 minimum

#### Focus
```css
.focus-visible {
  outline: 2px solid var(--primary-orange);
  outline-offset: 2px;
}

/* Suppression de l'outline par défaut */
*:focus {
  outline: none;
}

/* Focus visible uniquement au clavier */
*:focus-visible {
  outline: 2px solid var(--primary-orange);
  outline-offset: 2px;
}
```

#### Tailles Tactiles
- **Minimum** : 44px × 44px
- **Recommandé** : 48px × 48px
- **Espacement** : 8px minimum entre éléments

---

## Optimisations Africaines

### 1. Connectivité
- **Images optimisées** : WebP avec fallback JPEG
- **Lazy loading** : Chargement progressif
- **Mode hors ligne** : Lecture sans connexion
- **Compression** : Réduction de 60% de la bande passante

### 2. Appareils
- **RAM limitée** : Optimisation mémoire
- **Processeurs lents** : Animations légères
- **Écrans variés** : Support 240px à 1440px
- **Tactile** : Zones de touche généreuses

### 3. Localisation
- **Langues** : Français, Anglais, Wolof, Arabe
- **Devises** : XOF, EUR, USD
- **Formats** : Dates, heures, nombres locaux
- **Paiements** : Orange Money, Wave, cartes

### 4. Culturel
- **Couleurs** : Inspirées de l'artisanat africain
- **Contenu** : Focus sur la littérature africaine
- **Communauté** : Clubs de lecture locaux
- **Événements** : Calendrier culturel africain

### 5. Performance
- **Temps de chargement** : < 3s sur 3G
- **Taille de l'app** : < 50MB
- **Consommation data** : Optimisée pour forfaits limités
- **Batterie** : Mode économie d'énergie

---

## Validation et Tests

### 1. Tests d'Accessibilité
- [ ] Contraste WCAG AA
- [ ] Navigation clavier
- [ ] Lecteurs d'écran
- [ ] Tailles tactiles

### 2. Tests de Performance
- [ ] Lighthouse Score > 90
- [ ] Temps de chargement < 3s
- [ ] First Contentful Paint < 1.5s
- [ ] Largest Contentful Paint < 2.5s

### 3. Tests Multilingues
- [ ] Interface en français
- [ ] Interface en anglais
- [ ] Interface en wolof
- [ ] Interface en arabe (RTL)

### 4. Tests Appareils
- [ ] iPhone SE (375px)
- [ ] Samsung Galaxy (360px)
- [ ] iPad (768px)
- [ ] Desktop (1024px+)

### 5. Tests Connectivité
- [ ] 3G lent (50 Kbps)
- [ ] 3G rapide (1.6 Mbps)
- [ ] 4G (10 Mbps)
- [ ] Mode hors ligne

---

*Ce document constitue la base du design system Coko et sera mis à jour tout au long du développement.*