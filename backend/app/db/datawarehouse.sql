-- ============================================
-- TABLES DE DIMENSION (référentiels)
-- ============================================

-- Dimension Temps
CREATE TABLE dim_date (
    date_id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    week INTEGER,
    day_of_week INTEGER,
    day_name VARCHAR(10),
    month_name VARCHAR(10),
    is_weekend BOOLEAN
);

-- Dimension Région
CREATE TABLE dim_region (
    region_id SERIAL PRIMARY KEY,
    region_name VARCHAR(100) NOT NULL,
    province VARCHAR(100),
    postal_code VARCHAR(10),
    country VARCHAR(50) DEFAULT 'Belgium',
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension Entreprise
CREATE TABLE dim_company (
    company_id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    company_size VARCHAR(50), -- 'SME', 'Large', 'Startup'
    nace_code VARCHAR(10),
    sector VARCHAR(100),
    industry VARCHAR(100),
    website VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension Profession
CREATE TABLE dim_profession (
    profession_id SERIAL PRIMARY KEY,
    profession_name VARCHAR(255) NOT NULL,
    cp200_code VARCHAR(20),
    category VARCHAR(100), -- 'IT', 'Finance', 'Marketing', etc.
    seniority_level VARCHAR(50), -- 'Junior', 'Medior', 'Senior', 'Expert'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension Compétences
CREATE TABLE dim_skill (
    skill_id SERIAL PRIMARY KEY,
    skill_name VARCHAR(100) NOT NULL UNIQUE,
    skill_category VARCHAR(100), -- 'Technical', 'Soft', 'Language', 'Tool'
    skill_type VARCHAR(50), -- 'Programming', 'Framework', 'Certification'
    popularity_score INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension Source (plateforme de scraping)
CREATE TABLE dim_source (
    source_id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL UNIQUE, -- 'Indeed', 'Stepstone', 'Actiris'
    source_url VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLE DE FAITS (données transactionnelles)
-- ============================================

CREATE TABLE fact_job_offer (
    job_id SERIAL PRIMARY KEY,
    
    -- Foreign Keys vers dimensions
    date_id INTEGER REFERENCES dim_date(date_id),
    region_id INTEGER REFERENCES dim_region(region_id),
    company_id INTEGER REFERENCES dim_company(company_id),
    profession_id INTEGER REFERENCES dim_profession(profession_id),
    source_id INTEGER REFERENCES dim_source(source_id),
    
    -- Attributs de l'offre
    job_title VARCHAR(255) NOT NULL,
    job_description TEXT,
    contract_type VARCHAR(50), -- 'CDI', 'CDD', 'Freelance', 'Interim'
    work_regime VARCHAR(50), -- 'Full-time', 'Part-time'
    remote_option VARCHAR(50), -- 'On-site', 'Hybrid', 'Remote'
    
    -- Informations financières
    salary_min DECIMAL(10, 2),
    salary_max DECIMAL(10, 2),
    salary_currency VARCHAR(10) DEFAULT 'EUR',
    salary_period VARCHAR(20), -- 'yearly', 'monthly', 'hourly'
    
    -- Métadonnées
    date_posted DATE NOT NULL,
    date_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    application_deadline DATE,
    url_original TEXT,
    external_job_id VARCHAR(255),
    
    -- Flags
    is_active BOOLEAN DEFAULT TRUE,
    is_duplicate BOOLEAN DEFAULT FALSE,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_external_job UNIQUE (source_id, external_job_id)
);

-- ============================================
-- TABLES DE LIAISON (many-to-many)
-- ============================================

-- Compétences requises par offre
CREATE TABLE fact_job_skill (
    job_skill_id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES fact_job_offer(job_id) ON DELETE CASCADE,
    skill_id INTEGER REFERENCES dim_skill(skill_id),
    is_required BOOLEAN DEFAULT FALSE, -- TRUE si obligatoire
    proficiency_level VARCHAR(50), -- 'Basic', 'Intermediate', 'Advanced', 'Expert'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_job_skill UNIQUE (job_id, skill_id)
);

-- ============================================
-- TABLES ANALYTIQUES (pré-agrégées)
-- ============================================

-- Vue matérialisée pour performances
CREATE MATERIALIZED VIEW mv_job_trends AS
SELECT 
    d.year,
    d.month,
    d.month_name,
    r.region_name,
    p.category as profession_category,
    c.sector,
    COUNT(j.job_id) as job_count,
    AVG(j.salary_min) as avg_salary_min,
    AVG(j.salary_max) as avg_salary_max
FROM fact_job_offer j
JOIN dim_date d ON j.date_id = d.date_id
JOIN dim_region r ON j.region_id = r.region_id
JOIN dim_profession p ON j.profession_id = p.profession_id
JOIN dim_company c ON j.company_id = c.company_id
WHERE j.is_active = TRUE
GROUP BY d.year, d.month, d.month_name, r.region_name, p.category, c.sector;

-- Index pour optimisation
CREATE INDEX idx_job_date ON fact_job_offer(date_id);
CREATE INDEX idx_job_region ON fact_job_offer(region_id);
CREATE INDEX idx_job_company ON fact_job_offer(company_id);
CREATE INDEX idx_job_profession ON fact_job_offer(profession_id);
CREATE INDEX idx_job_posted ON fact_job_offer(date_posted);
CREATE INDEX idx_job_active ON fact_job_offer(is_active);
CREATE INDEX idx_job_skill_job ON fact_job_skill(job_id);
CREATE INDEX idx_job_skill_skill ON fact_job_skill(skill_id);