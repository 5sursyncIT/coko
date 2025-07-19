-- =====================================================
-- COKO PLATFORM - DATABASE SCHEMAS
-- Architecture: Microservices avec bases PostgreSQL séparées
-- Version: 1.0.0
-- =====================================================

-- =====================================================
-- AUTH SERVICE DATABASE
-- =====================================================

-- Database: coko_auth
CREATE DATABASE coko_auth;
\c coko_auth;

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    country VARCHAR(3) NOT NULL, -- ISO 3166-1 alpha-3
    language VARCHAR(2) NOT NULL DEFAULT 'fr', -- ISO 639-1
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    subscription_status VARCHAR(20) DEFAULT 'free',
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT chk_language CHECK (language IN ('fr', 'en', 'wo', 'ar')),
    CONSTRAINT chk_subscription CHECK (subscription_status IN ('free', 'premium', 'student'))
);

-- User sessions table
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token VARCHAR(255) NOT NULL,
    device_info JSONB,
    ip_address INET,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Password reset tokens
CREATE TABLE password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for Auth Service
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_country ON users(country);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX idx_password_reset_tokens_token ON password_reset_tokens(token);

-- =====================================================
-- CATALOG SERVICE DATABASE
-- =====================================================

-- Database: coko_catalog
CREATE DATABASE coko_catalog;
\c coko_catalog;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For full-text search

-- Publishers table
CREATE TABLE publishers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    website VARCHAR(255),
    logo_url VARCHAR(500),
    country VARCHAR(3),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Authors table
CREATE TABLE authors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    biography TEXT,
    photo_url VARCHAR(500),
    nationality VARCHAR(3),
    birth_date DATE,
    death_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Categories table (hierarchical)
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    icon VARCHAR(100),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Books table
CREATE TABLE books (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    subtitle VARCHAR(500),
    description TEXT,
    isbn VARCHAR(20),
    language VARCHAR(2) NOT NULL DEFAULT 'fr',
    publication_date DATE,
    page_count INTEGER,
    file_size BIGINT, -- in bytes
    format VARCHAR(10) NOT NULL, -- pdf, epub, mobi
    cover_url VARCHAR(500),
    file_url VARCHAR(500),
    price DECIMAL(10,2) DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'XOF',
    is_free BOOLEAN DEFAULT false,
    is_featured BOOLEAN DEFAULT false,
    is_published BOOLEAN DEFAULT false,
    rating DECIMAL(3,2) DEFAULT 0.00,
    rating_count INTEGER DEFAULT 0,
    download_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    publisher_id UUID REFERENCES publishers(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT chk_format CHECK (format IN ('pdf', 'epub', 'mobi')),
    CONSTRAINT chk_currency CHECK (currency IN ('XOF', 'EUR', 'USD')),
    CONSTRAINT chk_rating CHECK (rating >= 0 AND rating <= 5)
);

-- Book-Author relationship (many-to-many)
CREATE TABLE book_authors (
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'author', -- author, co-author, editor, translator
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    PRIMARY KEY (book_id, author_id)
);

-- Book-Category relationship (many-to-many)
CREATE TABLE book_categories (
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    PRIMARY KEY (book_id, category_id)
);

-- Book reviews
CREATE TABLE book_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    user_id UUID NOT NULL, -- Reference to auth service
    rating INTEGER NOT NULL,
    review_text TEXT,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT chk_rating CHECK (rating >= 1 AND rating <= 5),
    UNIQUE(book_id, user_id)
);

-- Indexes for Catalog Service
CREATE INDEX idx_books_title ON books USING gin(title gin_trgm_ops);
CREATE INDEX idx_books_language ON books(language);
CREATE INDEX idx_books_is_published ON books(is_published);
CREATE INDEX idx_books_is_featured ON books(is_featured);
CREATE INDEX idx_books_is_free ON books(is_free);
CREATE INDEX idx_books_publisher_id ON books(publisher_id);
CREATE INDEX idx_books_created_at ON books(created_at DESC);
CREATE INDEX idx_book_authors_author_id ON book_authors(author_id);
CREATE INDEX idx_book_categories_category_id ON book_categories(category_id);
CREATE INDEX idx_book_reviews_book_id ON book_reviews(book_id);
CREATE INDEX idx_book_reviews_user_id ON book_reviews(user_id);
CREATE INDEX idx_authors_name ON authors USING gin(name gin_trgm_ops);
CREATE INDEX idx_categories_parent_id ON categories(parent_id);

-- =====================================================
-- READING SERVICE DATABASE
-- =====================================================

-- Database: coko_reading
CREATE DATABASE coko_reading;
\c coko_reading;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Reading progress table
CREATE TABLE reading_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL, -- Reference to auth service
    book_id UUID NOT NULL, -- Reference to catalog service
    current_page INTEGER DEFAULT 1,
    total_pages INTEGER NOT NULL,
    progress_percentage DECIMAL(5,2) DEFAULT 0.00,
    reading_time_minutes INTEGER DEFAULT 0,
    last_read_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_completed BOOLEAN DEFAULT false,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT chk_progress CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    UNIQUE(user_id, book_id)
);

-- User annotations and highlights
CREATE TABLE annotations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL, -- Reference to auth service
    book_id UUID NOT NULL, -- Reference to catalog service
    page_number INTEGER NOT NULL,
    text_selection TEXT,
    note TEXT,
    highlight_color VARCHAR(7) DEFAULT '#FFFF00', -- Hex color
    annotation_type VARCHAR(20) DEFAULT 'highlight', -- highlight, note, bookmark
    position_data JSONB, -- For precise positioning
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT chk_annotation_type CHECK (annotation_type IN ('highlight', 'note', 'bookmark'))
);

-- Reading sessions for analytics
CREATE TABLE reading_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    book_id UUID NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    pages_read INTEGER DEFAULT 0,
    device_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for Reading Service
CREATE INDEX idx_reading_progress_user_id ON reading_progress(user_id);
CREATE INDEX idx_reading_progress_book_id ON reading_progress(book_id);
CREATE INDEX idx_reading_progress_last_read_at ON reading_progress(last_read_at DESC);
CREATE INDEX idx_annotations_user_id ON annotations(user_id);
CREATE INDEX idx_annotations_book_id ON annotations(book_id);
CREATE INDEX idx_annotations_page_number ON annotations(page_number);
CREATE INDEX idx_reading_sessions_user_id ON reading_sessions(user_id);
CREATE INDEX idx_reading_sessions_book_id ON reading_sessions(book_id);
CREATE INDEX idx_reading_sessions_start_time ON reading_sessions(start_time DESC);

-- =====================================================
-- PAYMENT SERVICE DATABASE
-- =====================================================

-- Database: coko_payment
CREATE DATABASE coko_payment;
\c coko_payment;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Subscription plans
CREATE TABLE subscription_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'XOF',
    duration_days INTEGER NOT NULL,
    features JSONB, -- Array of features
    max_downloads INTEGER DEFAULT -1, -- -1 for unlimited
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT chk_currency CHECK (currency IN ('XOF', 'EUR', 'USD'))
);

-- User subscriptions
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL, -- Reference to auth service
    plan_id UUID NOT NULL REFERENCES subscription_plans(id),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    auto_renew BOOLEAN DEFAULT true,
    payment_method VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT chk_status CHECK (status IN ('pending', 'active', 'expired', 'cancelled', 'suspended'))
);

-- Payment transactions
CREATE TABLE payment_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscription_id UUID REFERENCES subscriptions(id),
    user_id UUID NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_provider VARCHAR(50), -- orange_money, wave, stripe, etc.
    provider_transaction_id VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    payment_data JSONB, -- Provider-specific data
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT chk_payment_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'refunded')),
    CONSTRAINT chk_payment_method CHECK (payment_method IN ('orange_money', 'wave', 'visa', 'mastercard', 'paypal'))
);

-- Book purchases (for individual book sales)
CREATE TABLE book_purchases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    book_id UUID NOT NULL, -- Reference to catalog service
    transaction_id UUID REFERENCES payment_transactions(id),
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    purchase_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, book_id)
);

-- Indexes for Payment Service
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_end_date ON subscriptions(end_date);
CREATE INDEX idx_payment_transactions_user_id ON payment_transactions(user_id);
CREATE INDEX idx_payment_transactions_status ON payment_transactions(status);
CREATE INDEX idx_payment_transactions_created_at ON payment_transactions(created_at DESC);
CREATE INDEX idx_book_purchases_user_id ON book_purchases(user_id);
CREATE INDEX idx_book_purchases_book_id ON book_purchases(book_id);

-- =====================================================
-- GAMIFICATION SERVICE DATABASE
-- =====================================================

-- Database: coko_gamification
CREATE DATABASE coko_gamification;
\c coko_gamification;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Badges definition
CREATE TABLE badges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon_url VARCHAR(500),
    criteria JSONB, -- Conditions to earn the badge
    points_value INTEGER DEFAULT 0,
    rarity VARCHAR(20) DEFAULT 'common',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT chk_rarity CHECK (rarity IN ('common', 'rare', 'epic', 'legendary'))
);

-- User statistics
CREATE TABLE user_stats (
    user_id UUID PRIMARY KEY, -- Reference to auth service
    total_points INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    books_read INTEGER DEFAULT 0,
    books_completed INTEGER DEFAULT 0,
    reading_streak_days INTEGER DEFAULT 0,
    max_reading_streak INTEGER DEFAULT 0,
    total_reading_time_minutes INTEGER DEFAULT 0,
    annotations_count INTEGER DEFAULT 0,
    reviews_count INTEGER DEFAULT 0,
    last_activity_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User badges (earned badges)
CREATE TABLE user_badges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL, -- Reference to auth service
    badge_id UUID NOT NULL REFERENCES badges(id),
    earned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, badge_id)
);

-- Achievement history
CREATE TABLE achievement_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    achievement_type VARCHAR(50) NOT NULL, -- book_completed, streak_milestone, etc.
    achievement_data JSONB,
    points_earned INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Leaderboards
CREATE TABLE leaderboards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    leaderboard_type VARCHAR(50) NOT NULL, -- weekly, monthly, all_time
    criteria VARCHAR(50) NOT NULL, -- points, books_read, reading_time
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Leaderboard entries
CREATE TABLE leaderboard_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    leaderboard_id UUID NOT NULL REFERENCES leaderboards(id),
    user_id UUID NOT NULL,
    rank INTEGER NOT NULL,
    score INTEGER NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(leaderboard_id, user_id)
);

-- Indexes for Gamification Service
CREATE INDEX idx_user_badges_user_id ON user_badges(user_id);
CREATE INDEX idx_user_badges_badge_id ON user_badges(badge_id);
CREATE INDEX idx_achievement_history_user_id ON achievement_history(user_id);
CREATE INDEX idx_achievement_history_created_at ON achievement_history(created_at DESC);
CREATE INDEX idx_leaderboard_entries_leaderboard_id ON leaderboard_entries(leaderboard_id);
CREATE INDEX idx_leaderboard_entries_rank ON leaderboard_entries(rank);
CREATE INDEX idx_user_stats_total_points ON user_stats(total_points DESC);
CREATE INDEX idx_user_stats_level ON user_stats(level DESC);

-- =====================================================
-- COMMUNITY SERVICE DATABASE
-- =====================================================

-- Database: coko_community
CREATE DATABASE coko_community;
\c coko_community;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Discussion forums
CREATE TABLE forums (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Forum topics
CREATE TABLE topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    forum_id UUID NOT NULL REFERENCES forums(id) ON DELETE CASCADE,
    user_id UUID NOT NULL, -- Reference to auth service
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    is_pinned BOOLEAN DEFAULT false,
    is_locked BOOLEAN DEFAULT false,
    view_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    last_reply_at TIMESTAMP WITH TIME ZONE,
    last_reply_user_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Topic replies
CREATE TABLE topic_replies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    content TEXT NOT NULL,
    parent_reply_id UUID REFERENCES topic_replies(id), -- For nested replies
    is_solution BOOLEAN DEFAULT false,
    like_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Book clubs
CREATE TABLE book_clubs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    creator_user_id UUID NOT NULL,
    current_book_id UUID, -- Reference to catalog service
    member_count INTEGER DEFAULT 1,
    max_members INTEGER DEFAULT 50,
    is_public BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Book club members
CREATE TABLE book_club_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    club_id UUID NOT NULL REFERENCES book_clubs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    role VARCHAR(20) DEFAULT 'member', -- admin, moderator, member
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(club_id, user_id),
    CONSTRAINT chk_role CHECK (role IN ('admin', 'moderator', 'member'))
);

-- Book club discussions
CREATE TABLE club_discussions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    club_id UUID NOT NULL REFERENCES book_clubs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    book_id UUID, -- Reference to catalog service
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    discussion_type VARCHAR(20) DEFAULT 'general', -- general, chapter, review
    chapter_number INTEGER,
    reply_count INTEGER DEFAULT 0,
    last_reply_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Discussion replies
CREATE TABLE discussion_replies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    discussion_id UUID NOT NULL REFERENCES club_discussions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    content TEXT NOT NULL,
    like_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for Community Service
CREATE INDEX idx_topics_forum_id ON topics(forum_id);
CREATE INDEX idx_topics_user_id ON topics(user_id);
CREATE INDEX idx_topics_created_at ON topics(created_at DESC);
CREATE INDEX idx_topic_replies_topic_id ON topic_replies(topic_id);
CREATE INDEX idx_topic_replies_user_id ON topic_replies(user_id);
CREATE INDEX idx_book_club_members_club_id ON book_club_members(club_id);
CREATE INDEX idx_book_club_members_user_id ON book_club_members(user_id);
CREATE INDEX idx_club_discussions_club_id ON club_discussions(club_id);
CREATE INDEX idx_club_discussions_user_id ON club_discussions(user_id);
CREATE INDEX idx_discussion_replies_discussion_id ON discussion_replies(discussion_id);

-- =====================================================
-- INITIAL DATA INSERTION
-- =====================================================

-- Insert default subscription plans
\c coko_payment;
INSERT INTO subscription_plans (name, description, price, currency, duration_days, features) VALUES
('Gratuit', 'Accès limité à la bibliothèque', 0.00, 'XOF', 365, '["5 livres par mois", "Lecture en ligne"]'),
('Premium Mensuel', 'Accès complet à la bibliothèque', 2500.00, 'XOF', 30, '["Livres illimités", "Téléchargement offline", "Annotations", "Support prioritaire"]'),
('Premium Annuel', 'Accès complet avec réduction', 25000.00, 'XOF', 365, '["Livres illimités", "Téléchargement offline", "Annotations", "Support prioritaire", "Accès anticipé"]'),
('Étudiant', 'Tarif préférentiel pour étudiants', 1500.00, 'XOF', 30, '["Livres illimités", "Téléchargement offline", "Annotations", "Ressources académiques"]');

-- Insert default categories
\c coko_catalog;
INSERT INTO categories (name, description, icon) VALUES
('Littérature', 'Romans, nouvelles, poésie', 'book'),
('Sciences', 'Mathématiques, physique, chimie, biologie', 'flask'),
('Histoire', 'Histoire du monde, biographies', 'clock'),
('Philosophie', 'Pensée philosophique et spiritualité', 'lightbulb'),
('Éducation', 'Manuels scolaires et universitaires', 'graduation-cap'),
('Développement Personnel', 'Croissance personnelle et professionnelle', 'user'),
('Technologie', 'Informatique, programmation, innovation', 'laptop'),
('Culture Africaine', 'Traditions, langues et cultures africaines', 'globe-africa'),
('Économie', 'Finance, business, entrepreneuriat', 'chart-line'),
('Santé', 'Médecine, bien-être, nutrition', 'heart');

-- Insert default badges
\c coko_gamification;
INSERT INTO badges (name, description, icon_url, criteria, points_value, rarity) VALUES
('Premier Livre', 'Félicitations pour votre première lecture !', '/badges/first-book.svg', '{"books_read": 1}', 10, 'common'),
('Lecteur Assidu', 'Vous avez lu 10 livres', '/badges/avid-reader.svg', '{"books_read": 10}', 50, 'rare'),
('Marathonien', 'Vous avez lu 50 livres', '/badges/marathon.svg', '{"books_read": 50}', 200, 'epic'),
('Bibliothécaire', 'Vous avez lu 100 livres', '/badges/librarian.svg', '{"books_read": 100}', 500, 'legendary'),
('Série de 7', 'Lecture pendant 7 jours consécutifs', '/badges/streak-7.svg', '{"reading_streak": 7}', 25, 'common'),
('Série de 30', 'Lecture pendant 30 jours consécutifs', '/badges/streak-30.svg', '{"reading_streak": 30}', 100, 'rare'),
('Annotateur', 'Vous avez créé 50 annotations', '/badges/annotator.svg', '{"annotations_count": 50}', 75, 'rare'),
('Critique', 'Vous avez écrit 10 critiques', '/badges/critic.svg', '{"reviews_count": 10}', 60, 'rare');

-- Insert default forums
\c coko_community;
INSERT INTO forums (name, description, category) VALUES
('Discussions Générales', 'Parlez de tout et de rien', 'general'),
('Recommandations de Livres', 'Partagez vos découvertes littéraires', 'books'),
('Aide et Support', 'Questions techniques et assistance', 'support'),
('Littérature Africaine', 'Focus sur les auteurs et œuvres africains', 'african-literature'),
('Clubs de Lecture', 'Organisez et rejoignez des clubs', 'book-clubs');

-- =====================================================
-- VIEWS AND FUNCTIONS
-- =====================================================

-- View for user reading statistics
\c coko_reading;
CREATE VIEW user_reading_stats AS
SELECT 
    user_id,
    COUNT(*) as books_started,
    COUNT(CASE WHEN is_completed = true THEN 1 END) as books_completed,
    AVG(progress_percentage) as avg_progress,
    SUM(reading_time_minutes) as total_reading_time,
    MAX(last_read_at) as last_activity
FROM reading_progress
GROUP BY user_id;

-- Function to update reading progress
CREATE OR REPLACE FUNCTION update_reading_progress(
    p_user_id UUID,
    p_book_id UUID,
    p_current_page INTEGER,
    p_total_pages INTEGER,
    p_reading_time INTEGER DEFAULT 0
) RETURNS VOID AS $$
DECLARE
    v_progress DECIMAL(5,2);
BEGIN
    v_progress := (p_current_page::DECIMAL / p_total_pages::DECIMAL) * 100;
    
    INSERT INTO reading_progress (
        user_id, book_id, current_page, total_pages, 
        progress_percentage, reading_time_minutes
    ) VALUES (
        p_user_id, p_book_id, p_current_page, p_total_pages,
        v_progress, p_reading_time
    )
    ON CONFLICT (user_id, book_id) DO UPDATE SET
        current_page = p_current_page,
        total_pages = p_total_pages,
        progress_percentage = v_progress,
        reading_time_minutes = reading_progress.reading_time_minutes + p_reading_time,
        last_read_at = NOW(),
        is_completed = (v_progress >= 100),
        completed_at = CASE WHEN v_progress >= 100 THEN NOW() ELSE reading_progress.completed_at END,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Trigger to update book rating when review is added/updated
\c coko_catalog;
CREATE OR REPLACE FUNCTION update_book_rating() RETURNS TRIGGER AS $$
BEGIN
    UPDATE books SET 
        rating = (
            SELECT AVG(rating)::DECIMAL(3,2) 
            FROM book_reviews 
            WHERE book_id = COALESCE(NEW.book_id, OLD.book_id)
        ),
        rating_count = (
            SELECT COUNT(*) 
            FROM book_reviews 
            WHERE book_id = COALESCE(NEW.book_id, OLD.book_id)
        ),
        updated_at = NOW()
    WHERE id = COALESCE(NEW.book_id, OLD.book_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_book_rating
    AFTER INSERT OR UPDATE OR DELETE ON book_reviews
    FOR EACH ROW EXECUTE FUNCTION update_book_rating();

-- Trigger to update topic reply count
\c coko_community;
CREATE OR REPLACE FUNCTION update_topic_reply_count() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE topics SET 
            reply_count = reply_count + 1,
            last_reply_at = NEW.created_at,
            last_reply_user_id = NEW.user_id,
            updated_at = NOW()
        WHERE id = NEW.topic_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE topics SET 
            reply_count = reply_count - 1,
            updated_at = NOW()
        WHERE id = OLD.topic_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_topic_reply_count
    AFTER INSERT OR DELETE ON topic_replies
    FOR EACH ROW EXECUTE FUNCTION update_topic_reply_count();

-- =====================================================
-- PERFORMANCE OPTIMIZATIONS
-- =====================================================

-- Partitioning for large tables (example for reading_sessions)
\c coko_reading;
CREATE TABLE reading_sessions_y2024m01 PARTITION OF reading_sessions
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Additional indexes for performance
\c coko_catalog;
CREATE INDEX CONCURRENTLY idx_books_fulltext ON books USING gin(to_tsvector('french', title || ' ' || COALESCE(description, '')));

-- =====================================================
-- SECURITY POLICIES (Row Level Security)
-- =====================================================

-- Enable RLS on sensitive tables
\c coko_reading;
ALTER TABLE reading_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE annotations ENABLE ROW LEVEL SECURITY;

-- Example policy (to be implemented with proper authentication)
-- CREATE POLICY user_reading_progress ON reading_progress
--     FOR ALL TO authenticated_users
--     USING (user_id = current_user_id());

-- =====================================================
-- BACKUP AND MAINTENANCE
-- =====================================================

-- Create backup user
-- CREATE ROLE coko_backup WITH LOGIN PASSWORD 'secure_backup_password';
-- GRANT CONNECT ON DATABASE coko_auth, coko_catalog, coko_reading, coko_payment, coko_gamification, coko_community TO coko_backup;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO coko_backup;

-- =====================================================
-- END OF SCHEMA DEFINITION
-- =====================================================