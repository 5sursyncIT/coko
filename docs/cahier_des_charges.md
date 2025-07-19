## Cahier des charges – Application Coko (Harmattan Dakar)

### 1. Contexte & objectifs

**Contexte :**
Harmattan Dakar porte le projet Coko, une plateforme web et mobile de distribution, lecture et publication de contenus numériques (ebooks, livres audio, presse, BD, documents éducatifs, podcasts). L'objectif est d'offrir une expérience riche et sécurisée, adaptée aux marchés francophones et africains.

**Analyse concurrentielle :**
Le marché francophone dispose déjà de plateformes établies comme YouScribe (2 000 FCFA/mois), mais Coko se différencie par :
- Une architecture technique moderne (microservices, PWA)
- Des fonctionnalités de gamification innovantes
- Un focus spécifique sur les créateurs africains
- Des outils de publication collaborative avancés
- Une optimisation pour les connexions africaines

**Objectifs SMART :**

* **O1 – Adoption :** Atteindre **5 000 MAUs** (utilisateurs actifs mensuels) à 6 mois post-lancement.
* **O2 – Rétention :** Maintenir un **taux de rétention à J30 ≥ 40 %** (après téléchargement de l'app).
* **O3 – Performance :** Obtenir des **scores Core Web Vitals** (LCP ≤ 2,5 s, FID ≤ 100 ms, CLS ≤ 0,1) sur 90 % des pages critiques.
* **O4 – Satisfaction :** Atteindre un **NPS ≥ 40** à la fin de la phase MVP.
* **O5 – Acquisition créateurs :** Attirer **500 auteurs/éditeurs locaux** en 12 mois.
* **O6 – Engagement communauté :** **20% des utilisateurs actifs** dans les fonctions sociales.
* **O7 – Performance mobile :** Temps de chargement **≤ 3s sur connexions 3G** africaines.

---

### 2. Périmètre fonctionnel

| ID | Fonctionnalité              | Description                                                                           | Critères d’acceptation                                                                                   |
| -- | --------------------------- | ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| F1 | Catalogue & recherche       | Navigation par thème, recherche plein texte, filtres (type, langue, date).            | Recherche retourne < 2 s ; filtres cumulables ; liste paginée.                                           |
| F2 | Lecture en streaming        | Liseuse HTML5 pour EPUB/PDF, zoom, sommaire, thèmes clair/sombre.                     | Lecture fluide ≥ 60 fps ; sommaire cliquable ; bascule mode sombre OK.                                   |
| F3 | Mode hors-ligne             | Téléchargement chiffré sur mobile, synchronisation de la progression.                 | Livre synchronisé disponible offline ; progression identique à en ligne.                                 |
| F4 | Recommandation vectorielle  | Moteur ML de recommandations basées sur historique et similarité de contenu.          | 5 suggestions pertinentes affichées ; CTR ≥ 5 % sur recommandations.                                     |
| F5 | Gamification                | Badges et points de lecture, tableau de classement.                                   | Attribution automatique de badges ; leaderboard actualisé en < 5 s.                                      |
| F6 | Export de notes             | Export des annotations et marque-pages au format PDF/Markdown.                        | Fichier généré en < 3 s ; contenu conforme aux notes créées.                                             |
| F7 | Publication & monétisation  | Téléversement de documents, métadonnées, workflow de validation, suivi des royalties. | Upload < 100 Mo accepté ; statut de validation visible ; dashboard royalties mis à jour quotidiennement. |
| F8 | Administration & modération | Dashboard admin : gestion des utilisateurs, contenus, partenaires, suivi KPI.         | Accès sécurisé ; filtres admin ; export CSV des rapports d'activité.                                     |
| F9 | Communauté créateurs        | Forums, événements virtuels, mentorat entre auteurs, groupes thématiques.             | Forum actif ; 1 événement/mois ; système de mentorat opérationnel.                                       |
| F10| Monétisation flexible       | Micropaiements, abonnements par genre, achats à l'unité, freemium.                    | 3 modèles tarifaires ; conversion freemium ≥ 15% ; paiements mobiles intégrés.                           |
| F11| Accessibilité              | Support audio pour malvoyants, sous-titres, traduction automatique.                   | Lecteur d'écran compatible ; traduction 5 langues ; interface haute lisibilité.                          |
| F12| Contenu local              | Partenariats universités, archives culturelles, contenus en langues locales.          | 10 partenariats signés ; 100 contenus locaux ; support 3 langues africaines.                             |

---

### 3. Architecture technique

#### 3.1 Back-end (Django Python microservices)

* **Services :** Auth, Catalogue, Lecture, Paiement, Recommandation, Gamification, Publication, Admin.
* **Framework :** Django REST Framework + Graphene (GraphQL)
* **Base de données :** PostgreSQL (relationnel), Elasticsearch (recherche), Redis (cache)
* **Sécurité :** CSRF, XSS, injection SQL, chiffrement des données sensibles

#### 3.2 Front-end (Next.js & React)

* **Technologies :** Next.js (SSR/SSG), React, TypeScript, Tailwind CSS, Framer Motion
* **Fonctionnalités :** Navigation SPA, SEO optimisé, PWA desktop, design responsive
* **Communication :** Axios/fetch vers API REST/GraphQL, WebSocket pour notifications temps réel

#### 3.3 Infrastructure & CI/CD

* **Stockage :** AWS S3 (SSE), CDN (CloudFront/Cloudflare)
* **CDN africain :** Points de présence en Afrique de l'Ouest pour réduire la latence
* **Compression adaptative :** Optimisation automatique selon la bande passante
* **Cache intelligent :** Prédiction des contenus populaires par région
* **Conteneurisation :** Docker + Kubernetes (EKS/GKE)
* **IaC :** Terraform, GitHub Actions
* **Monitoring :** Prometheus, Grafana, ELK Stack ou CloudWatch
* **CI/CD :** Tests automatiques (unitaires, intégration, e2e), déploiement continu

---

### 4. Roadmap MVP (Sprints)

| Sprint | Durée  | Objectifs clés                               | Livrable                           |
| ------ | ------ | -------------------------------------------- | ---------------------------------- |
| S0     | 2 sem. | Cadrage, architecture, maquettes UX/UI       | Cahier des charges, wireframes     |
| S1     | 2 sem. | Authentification, base infra, API Catalogue  | Service Auth + Catalogue v1        |
| S2     | 2 sem. | Lecture streaming + mode offline             | Liseuse web + offline mobile       |
| S3     | 2 sem. | Publication / modération / back-office admin | Module publication + dashboard     |
| S4     | 2 sem. | Recommandation ML + gamification             | Service ML + leaderboard           |
| S5     | 2 sem. | Export notes, PWA Desktop, recette MVP       | MVP fonctionnel + tests concluants |
| S6     | 2 sem. | Communauté créateurs + monétisation flexible | Forums, événements, freemium      |
| S7     | 2 sem. | Accessibilité + contenu local + optimisations| Support multilingue, CDN africain |

---

### 5. Planning prévisionnel

| Phase                  | Durée totale | Livrable principal         |
| ---------------------- | -----------: | -------------------------- |
| Conception & UX/UI     |   3 semaines | Cahier validé, maquettes   |
| Développement MVP      |  16 semaines | Version 1.0 opérationnelle |
| Tests & recette        |   4 semaines | Rapports QA et correctifs  |
| Déploiement production |   2 semaines | Plateforme live            |
| Déploiement Phase 1    |   4 semaines | Lancement Sénégal          |
| Évolutions post-MVP    |      Continu | Versions incrémentales     |

---

### 6. Budget indicatif

* **Développement initial :** 6 500 000 FCFA HT (incluant nouvelles fonctionnalités)
* **Optimisations techniques :** 1 000 000 FCFA HT (CDN africain, performance)
* **Contenu et partenariats :** 500 000 FCFA HT (acquisition contenu local)
* **Marche de manœuvre :** 1 000 000 FCFA HT pour évolutions mineures ou imprévus
* **Total plafond :** 9 000 000 FCFA HT

**Répartition par phase :**
* **MVP étendu (S0-S7) :** 7 000 000 FCFA HT
* **Déploiement et optimisations :** 2 000 000 FCFA HT

---

### 7. Support & maintenance

| Service                     | Description                                        | Mensuel FCFA |
| --------------------------- | -------------------------------------------------- | -----------: |
| Support standard (SLA 24 h) | Correction bugs, patchs sécurité, supervision 24/7 |      300 000 |
| Évolutions mineures (8 h/m) | Ajustements, développements correctifs             |      100 000 |
| **Total support mensuel**   |                                                    |  **400 000** |

* **Engagement minimum :** 6 mois ; reconduction tacite sauf préavis 1 mois

---

### 8. Méthodologie & gouvernance

* **Méthode Agile Scrum** : sprints de 2 sem., daily stand-up, sprint review, rétrospective
* **Rôles :** Product Owner (client), Scrum Master, Équipe Dev (Backend, Frontend), Designer, QA, DevOps
* **Suivi :** backlog partagé, revue de sprint, comité pilotage mensuel
* **Critères d’acceptation** : user stories avec Given/When/Then pour chaque fonctionnalité majeure

---

### 9. Annexes

* Wireframes UX/UI et schémas C4
* Glossaire des termes techniques
* Charte sécurité & conformité RGPD
* Matrice des risques et plans de mitigation

*Fin du cahier des charges*

### 10. Stratégie de contenu et partenariats

#### 10.1 Contenu local prioritaire
* **Partenariats éditoriaux :** Maisons d'édition africaines, universités, centres culturels
* **Programme d'incubation :** Support aux jeunes auteurs avec mentorat et outils de publication
* **Contenus éducatifs :** Manuels scolaires, cours universitaires, formations professionnelles
* **Langues locales :** Support progressif du wolof, bambara, lingala

#### 10.2 Plan de déploiement géographique
* **Phase 1 (0-6 mois) :** Sénégal (marché test)
* **Phase 2 (6-12 mois) :** Côte d'Ivoire, Mali, Burkina Faso
* **Phase 3 (12-18 mois) :** Maghreb et Afrique centrale

---

### 11. Modèle économique détaillé

#### 11.1 Grille tarifaire
* **Freemium :** Accès limité (5 livres/mois, publicités)
* **Premium :** 1 500 FCFA/mois (accès illimité, hors-ligne, sans pub)
* **Créateur :** 500 FCFA/mois (outils publication, analytics, 70% royalties)
* **Institutionnel :** Sur devis (écoles, bibliothèques, entreprises)

#### 11.2 Objectifs de monétisation
* **Conversion freemium → premium :** 15% à 12 mois
* **Revenus créateurs :** 30% du CA total à 18 mois
* **Partenariats institutionnels :** 20% du CA à 24 mois

---

### 12. Gestion des risques concurrentiels

#### 12.1 Veille et analyse
* **Monitoring concurrentiel :** Suivi mensuel des évolutions YouScribe et autres
* **Benchmark fonctionnel :** Comparaison trimestrielle des features
* **Analyse tarifaire :** Ajustement réactif des prix

#### 12.2 Stratégies de différenciation
* **Innovation technique :** Gamification, IA, expérience mobile optimisée
* **Écosystème local :** Réseau exclusif créateurs africains
* **Partenariats stratégiques :** Alliances avec télécoms, institutions

#### 12.3 Plans de riposte
* **Agression tarifaire :** Offres promotionnelles ciblées
* **Guerre des contenus :** Exclusivités temporaires avec auteurs vedettes
* **Innovation disruptive :** Accélération R&D sur nouvelles fonctionnalités

---

### 13. Métriques de succès étendues

#### 13.1 KPIs utilisateurs
* **Taux de conversion freemium → premium :** ≥ 15%
* **Temps moyen de lecture par session :** ≥ 25 minutes
* **Taux d'engagement communauté :** ≥ 20%
* **Score de satisfaction créateurs :** NPS ≥ 50

#### 13.2 KPIs business
* **Revenus récurrents mensuels (MRR) :** 50M FCFA à 12 mois
* **Coût d'acquisition client (CAC) :** ≤ 2 000 FCFA
* **Valeur vie client (LTV) :** ≥ 15 000 FCFA
* **Ratio LTV/CAC :** ≥ 7:1

#### 13.3 KPIs techniques
* **Disponibilité plateforme :** ≥ 99,5%
* **Temps de réponse API depuis l'Afrique :** ≤ 500ms
* **Taux d'adoption fonctions gamification :** ≥ 30%
* **Performance mobile 3G :** Chargement ≤ 3s

*Fin du cahier des charges*
