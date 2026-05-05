-- ============================================
-- COMPLETE DATABASE SETUP & CLEANUP SCRIPT
-- ============================================

-- ============================================
-- PART 1: TABLE CREATION AND SETUP
-- ============================================

CREATE TABLE IF NOT EXISTS document (
    id SERIAL PRIMARY KEY,
    content TEXT,
    language VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS document_embedding;
CREATE TABLE document_embedding (
    id SERIAL PRIMARY KEY,
    doc_id INTEGER REFERENCES document(id),
    embedding VECTOR(384) -- For MiniLM-L12-v2
);

ALTER TABLE document RENAME COLUMN languages TO language;

CREATE TABLE IF NOT EXISTS search_logs (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    search_type VARCHAR(20) NOT NULL,
    top_k INT DEFAULT 0,
    results_count INT DEFAULT 0,
    latency_ms DOUBLE PRECISION DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- PART 2: FULL-TEXT SEARCH SETUP
-- ============================================

ALTER TABLE document ADD COLUMN IF NOT EXISTS content_tsvector TSVECTOR;
UPDATE document SET content_tsvector = to_tsvector('simple', content);
CREATE INDEX IF NOT EXISTS idx_document_content_tsvector ON document USING GIN (content_tsvector);

CREATE OR REPLACE FUNCTION update_tsvector_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.content_tsvector := to_tsvector('simple', NEW.content);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_tsvector ON document;
CREATE TRIGGER trigger_update_tsvector
    BEFORE INSERT OR UPDATE OF content ON document
    FOR EACH ROW
    EXECUTE FUNCTION update_tsvector_column();

-- ============================================
-- PART 3: VECTOR INDEX FOR SIMILARITY SEARCH
-- ============================================

CREATE INDEX IF NOT EXISTS idx_document_embedding_hnsw ON document_embedding USING hnsw (embedding vector_cosine_ops);

-- ============================================
-- PART 4: DATA PRUNING (DELETIONS)
-- ============================================

-- 1. Delete extremely short or empty documents
DELETE FROM document WHERE content IS NULL OR LENGTH(TRIM(content)) < 15;

-- 2. Delete statistical metric tables / classification reports
DELETE FROM document WHERE 
    content ~* 'f1-score|precision.*recall.*f1-score|classification report|macro\s+avg';

-- 3. Delete records with mathematical matrix artifacts
DELETE FROM document WHERE content ~ '×[\s\d\.]+';

-- 4. Delete heavy number sequences (5+ numbers in a row)
DELETE FROM document WHERE content ~ '(\d+\.\d+\s+){5,}';

-- ============================================
-- PART 5: MODULAR FORENSIC CLEANING PIPELINE
-- ============================================

-- MODULE A: ACADEMIC FILTER
CREATE OR REPLACE FUNCTION forensic_clean_academic(input_text TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN REGEXP_REPLACE(input_text, 
        'i\.\s*i\.\s*d\.|i\.\s*e\.\s*,?|qper⊗l?|dkl|standard errors in parentheses|p¡\.?\*{1,3}|\(\w+\s+et\s+al\.,\s+\d{4}\)|\(\w+\s+and\s+\w+,\s+\d{4}\)|\s+et\s+al\.|arxiv:[^,\.\s]+|biometrika[^,\.\s]+|doi:[^,\.\s]+|\(\d+\):–,\d+|\(\d+\):–,|\(\d+\):,|doi:\s*\.\./\.\.|isbn\s+\.|h\s+t\s+t\s+p\s*s?\s*:\s*/\s*/\s*d\s*o\s*i\s*\.\s*o\s*r\s*g', 
        ' ', 'gi');
END;
$$ LANGUAGE plpgsql;

-- MODULE B: PDF & OCR ARTIFACT REPAIR
CREATE OR REPLACE FUNCTION forensic_clean_artifacts(input_text TEXT)
RETURNS TEXT AS $$
DECLARE result TEXT := input_text;
BEGIN
    result := REGEXP_REPLACE(result, '\(cid:\d+\)|\[\]|\[\d+\]|[⊗¡\*∗†‡§¶‖]|[%±τ_—]|\s+-\s+|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|https?:\/\/[^\s]+|\y(page\s*\d+\s*(of\s*\d+)?)\y|\y(fig\.|figure|table)\s+\d+[a-zA-Z]?\y', ' ', 'gi');
    result := REGEXP_REPLACE(result, '([a-zA-Z]+)-\s+([a-zA-Z]+)', '\1\2', 'g'); -- Fix hyphenated line breaks
    result := REGEXP_REPLACE(result, 'ﬁ', 'fi', 'g');
    result := REGEXP_REPLACE(result, 'ﬂ', 'fl', 'g');
    result := REGEXP_REPLACE(result, 'ﬀ', 'ff', 'g');
    result := REGEXP_REPLACE(result, 'ﬃ', 'ffi', 'g');
    result := REGEXP_REPLACE(result, 'ﬄ', 'ffl', 'g');
    result := REGEXP_REPLACE(result, '[\u200B\u200C\u200D\uFEFF]', '', 'g');
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- MODULE C: MATH & SYMBOL PURGE
CREATE OR REPLACE FUNCTION forensic_clean_math(input_text TEXT)
RETURNS TEXT AS $$
DECLARE result TEXT := input_text;
BEGIN
    result := REGEXP_REPLACE(result, '[=+\/<>≤≥∈∑∫≈∞≠−⃗αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ]', ' ', 'g');
    result := REGEXP_REPLACE(result, '\s+[bcdefghijklmnopqrstuvwxyz]\s+', ' ', 'gi'); -- Single letters (indices)
    result := REGEXP_REPLACE(result, '\y(wt|ct|bt|xt|yt|zt|mt|nt|st|pt|xk|yk|zk|mk|nk|ij|ji)\y', ' ', 'gi'); -- Math vars
    result := REGEXP_REPLACE(result, '[a-zA-Z]\([^)]*\)', ' ', 'g'); -- Functional notation f(x)
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- MODULE D: NUMERICAL FILTER
CREATE OR REPLACE FUNCTION forensic_clean_numerical(input_text TEXT)
RETURNS TEXT AS $$
DECLARE result TEXT := input_text;
BEGIN
    result := REGEXP_REPLACE(result, '\s+\d+(?:\.\d+)?\s+', ' ', 'g'); -- Standalone numbers
    result := REGEXP_REPLACE(result, '\m\d+|\d+\M', '', 'g'); -- Numbers attached to words
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- MASTER ORCHESTRATOR: THE NEURAL CLEANER
CREATE OR REPLACE FUNCTION clean_garbage_modular(
    input_text TEXT,
    do_academic BOOLEAN DEFAULT TRUE,
    do_artifacts BOOLEAN DEFAULT TRUE,
    do_math BOOLEAN DEFAULT TRUE,
    do_num BOOLEAN DEFAULT TRUE
)
RETURNS TEXT AS $$
DECLARE
    result TEXT := input_text;
BEGIN
    IF input_text IS NULL THEN RETURN NULL; END IF;
    
    -- Sequential Processing based on Toggles
    IF do_artifacts THEN result := forensic_clean_artifacts(result); END IF;
    IF do_academic  THEN result := forensic_clean_academic(result); END IF;
    IF do_math      THEN result := forensic_clean_math(result); END IF;
    IF do_num       THEN result := forensic_clean_numerical(result); END IF;
    
    -- Final Normalization (Always runs)
    result := REGEXP_REPLACE(result, '\y(\w+)\y(\s+\1\y){2,}', '\1', 'gi'); -- Repeated words
    result := REGEXP_REPLACE(result, '[\x00-\x1F\x7F]', ' ', 'g'); -- Control chars
    result := REGEXP_REPLACE(result, '[\.\–\,\"\/\\\?\(\)\#\{\}\[\]\:]', ' ', 'g'); -- Punctuation
    result := TRIM(REGEXP_REPLACE(result, '\s+', ' ', 'g')); -- Collapse whitespace
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;
-- ============================================
-- PART 6: APPLY CLEANUP
-- ============================================

-- Execute the super-function on all content
UPDATE document 
SET content = clean_garbage_from_text(content)
WHERE content IS NOT NULL;

-- Secondary sweep for documents that became empty after cleanup
DELETE FROM document WHERE LENGTH(TRIM(content)) < 15 OR content IS NULL;

SELECT * FROM document where content ILIKE '%infinitewidth%';
-- ============================================
-- PART 7: PREVIEW AND VERIFICATION
-- ============================================

-- 1. Preview how the cleanup will change your documents (Run this BEFORE Part 6)
SELECT 
    id,
    LEFT(content, 100) as original_text,
    LEFT(clean_garbage_from_text(content), 100) as preview_cleaned_text
FROM document 
WHERE content IS NOT NULL
LIMIT 20;

-- 2. Count how many records still need cleaning
SELECT COUNT(*) as records_need_cleaning
FROM document 
WHERE content IS DISTINCT FROM clean_garbage_from_text(content);

-- 3. Verify final cleaned output (Run this AFTER Part 6)
SELECT 
    id,
    LEFT(content, 150) as fully_cleaned_content
FROM document 
ORDER BY id ASC
LIMIT 20;

-- ============================================
-- PART 8: MAINTENANCE
-- ============================================

VACUUM ANALYZE document;
VACUUM ANALYZE document_embedding;

-- Replace 
UPDATE document 
SET content = REGEXP_REPLACE(content, 'featurelearning',
'feature learning', 'g')
WHERE content ~ 'featurelearning';
SELECT * FROM document order by RANDOM() LIMIT 100;
-- swuggy invocab and outofvoca


UPDATE document 
SET content = REPLACE(REPLACE(REPLACE(content, 
    'infinitewidth', 'infinite width'),
    'infinitewidths', 'infinite widths'),
    'infinite-width', 'infinite width');


-- Preview NULL rows first
SELECT * FROM document WHERE content IS NULL;

-- Count NULL rows
SELECT COUNT(*) as null_rows FROM document WHERE content IS NULL;

-- Remove NULL rows
DELETE FROM document WHERE content IS NULL;


SELECT * FROM document order by RANDOM() LIMIT 100;





