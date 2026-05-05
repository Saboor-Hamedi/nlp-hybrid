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
-- PART 5: COMPREHENSIVE TEXT CLEANUP FUNCTION
-- ============================================

CREATE OR REPLACE FUNCTION clean_garbage_from_text(input_text TEXT)
RETURNS TEXT AS $$
DECLARE
    result TEXT := input_text;
BEGIN
    IF input_text IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- ============================================
    -- SAFE OPERATIONS (Replace with spaces, not empty strings)
    -- ============================================
    
    -- Structure & Symbol Artifacts (REPLACE WITH SPACE, NOT EMPTY)
    result := REGEXP_REPLACE(result, '^[\#\*\-\•]+\s*', '', 'g');
    result := REGEXP_REPLACE(result, '\(cid:\d+\)', ' ', 'g');
    result := REGEXP_REPLACE(result, '\[\]', ' ', 'g');
    result := REGEXP_REPLACE(result, '\[\d+\]', ' ', 'g');
    result := REGEXP_REPLACE(result, '[⊗¡\*∗†‡§¶‖]', ' ', 'g'); -- Math/special symbols & Author marks
    
    -- Messy Symbols (Replace with space)
    result := REGEXP_REPLACE(result, '[%±τ_—]', ' ', 'g');
    result := REGEXP_REPLACE(result, '\s+-\s+', ' ', 'g');
    
    -- PDF Specific Artifacts
    -- Fix hyphenated line breaks (comput- ation -> computation) - SAFE
    result := REGEXP_REPLACE(result, '([a-zA-Z]+)-\s+([a-zA-Z]+)', '\1\2', 'g');
    -- Remove emails and URLs (replace with space)
    result := REGEXP_REPLACE(result, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', ' ', 'g');
    result := REGEXP_REPLACE(result, 'https?:\/\/[^\s]+', ' ', 'g');
    result := REGEXP_REPLACE(result, '\y(page\s*\d+\s*(of\s*\d+)?)\y', ' ', 'gi');
    result := REGEXP_REPLACE(result, '\y(fig\.|figure|table)\s+\d+[a-zA-Z]?\y', ' ', 'gi');
    
    -- Ligatures (Safe replacement)
    result := REGEXP_REPLACE(result, 'ﬁ', 'fi', 'g');
    result := REGEXP_REPLACE(result, 'ﬂ', 'fl', 'g');
    result := REGEXP_REPLACE(result, 'ﬀ', 'ff', 'g');
    result := REGEXP_REPLACE(result, 'ﬃ', 'ffi', 'g');
    result := REGEXP_REPLACE(result, 'ﬄ', 'ffl', 'g');
    result := REGEXP_REPLACE(result, '[\u200B\u200C\u200D\uFEFF]', '', 'g');
    result := REGEXP_REPLACE(result, '[=+\/<>≤≥∈∑∫≈∞≠−⃗αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ]', ' ', 'g');
    result := REGEXP_REPLACE(result, '[“”‘’`]', ' ', 'g');
    
    -- Academic Citations (Replace with space)
    result := REGEXP_REPLACE(result, 'i\.\s*i\.\s*d\.', ' ', 'gi');
    result := REGEXP_REPLACE(result, 'i\.\s*e\.\s*,?', ' ', 'gi');
    result := REGEXP_REPLACE(result, 'qper⊗l?|dkl', ' ', 'gi');
    result := REGEXP_REPLACE(result, 'standard errors in parentheses|p¡\.?\*{1,3}', ' ', 'gi');
    result := REGEXP_REPLACE(result, '\(\w+\s+et\s+al\.,\s+\d{4}\)|\(\w+\s+and\s+\w+,\s+\d{4}\)', ' ', 'gi');
    result := REGEXP_REPLACE(result, '\s+et\s+al\.', ' ', 'gi');
    result := REGEXP_REPLACE(result, 'arxiv:[^,\.\s]+|biometrika[^,\.\s]+|doi:[^,\.\s]+', ' ', 'gi');
    result := REGEXP_REPLACE(result, '\(\d+\):–,\d+|\(\d+\):–,|\(\d+\):,', ' ', 'gi');
    result := REGEXP_REPLACE(result, 'doi:\s*\.\./\.\.|isbn\s+\.', ' ', 'gi');
    
    -- ============================================
    -- NUMBER CLEANUP (REPLACE WITH SPACE)
    -- ============================================
    
    -- Remove standalone numbers (replace with space)
    result := REGEXP_REPLACE(result, '\s+\d+(?:\.\d+)?\s+', ' ', 'g');
    result := REGEXP_REPLACE(result, '^\d+(?:\.\d+)?\s+', '', 'g');
    result := REGEXP_REPLACE(result, '\s+\d+(?:\.\d+)?$', '', 'g');
    
    -- Remove numbers attached to words (1department -> department)
    -- BUT preserve the word by removing only the numbers
    result := REGEXP_REPLACE(result, '\m\d+', '', 'g');
    result := REGEXP_REPLACE(result, '\d+\M', '', 'g');
    
    -- ============================================
    -- SINGLE LETTER & MATH VARIABLE CLEANUP
    -- ============================================
    
    -- Remove single letters (Keep ONLY 'a' as a valid word, delete 'i' because in academic papers 'i' is an index)
    result := REGEXP_REPLACE(result, '\s+[bcdefghijklmnopqrstuvwxyz]\s+', ' ', 'gi');
    result := REGEXP_REPLACE(result, '^[bcdefghijklmnopqrstuvwxyz]\s+', '', 'gi');
    result := REGEXP_REPLACE(result, '\s+[bcdefghijklmnopqrstuvwxyz]$', '', 'gi');
    
    -- Remove isolated 2-letter math variables left over from subscripts (wt, ct, bt, xt, yt, zt, mt, nt, st, xk, mk, etc.)
    result := REGEXP_REPLACE(result, '\y(wt|ct|bt|xt|yt|zt|mt|nt|st|pt|xk|yk|zk|mk|nk|ij|ji)\y', ' ', 'gi');
    
    -- Remove single letters with periods (c., A.)
    result := REGEXP_REPLACE(result, '\y[a-zA-Z]\.\s*', ' ', 'gi');
    
    -- Remove letter with parentheses y(n)
    result := REGEXP_REPLACE(result, '[a-zA-Z]\([^)]*\)', ' ', 'g');
    
    -- ============================================
    -- REPEATED WORDS (Keep one instance)
    -- ============================================
    
    -- Remove repeated words 3+ times (word word word -> word)
    result := REGEXP_REPLACE(result, '\y(\w+)\y(\s+\1\y){2,}', '\1', 'gi');
    -- Remove repeated words 2+ times (word word -> word)
    result := REGEXP_REPLACE(result, '\y(\w+)\y\s+\1\y', '\1', 'gi');
    
    -- ============================================
    -- PUNCTUATION & FORMATTING (Replace with space)
    -- ============================================
    
    -- Remove control characters (replace with space)
    result := REGEXP_REPLACE(result, '[\x00-\x1F\x7F]', ' ', 'g');
    
    -- Remove diacritics
    result := REGEXP_REPLACE(result, '[́ˆ`´¨]', '', 'g');
    
    -- Fix hyphenated words (learn-ing -> learning) - SAFE (only when hyphenated)
    result := REGEXP_REPLACE(result, '(\w+)-(\w+)', '\1\2', 'g');
    
    -- Remove multiple punctuation (replace with space)
    result := REGEXP_REPLACE(result, '\.{2,}|,{2,}', ' ', 'g');
    
    -- Remove leading punctuation
    result := REGEXP_REPLACE(result, '^\s*[\.\:\;\,\-\_]+', '', 'g');
    
    -- Fix space before punctuation (hello . world -> hello. world)
    result := REGEXP_REPLACE(result, '\s+([.,;:!?])', '\1', 'g');
    
    -- ============================================
    -- SPECIAL PATTERNS
    -- ============================================
    
    -- Remove abbreviation patterns (-ht1b (iaq))
    result := REGEXP_REPLACE(result, '\s*[-]?[a-z0-9]+\s*\([a-z]+\)', ' ', 'gi');
    
    -- Remove standalone parentheses with letters
    result := REGEXP_REPLACE(result, '\(\s*[a-z]+\s*\)', ' ', 'gi');
    
    -- Fix spaced DOIs
    result := REGEXP_REPLACE(result, 'h\s+t\s+t\s+p\s*s?\s*:\s*/\s*/\s*d\s*o\s*i\s*\.\s*o\s*r\s*g', 'https://doi.org', 'gi');
    
    -- ============================================
    -- FINAL AGGRESSIVE PUNCTUATION REMOVAL
    -- Removes: . – , " / ? ( ) # { } [ ] :
    -- ============================================
    result := REGEXP_REPLACE(result, '[\.\–\,\"\/\\\?\(\)\#\{\}\[\]\:]', ' ', 'g');
    
    -- ============================================
    -- FINAL: COLLAPSE MULTIPLE SPACES TO SINGLE SPACE
    -- This is SAFE - keeps word boundaries intact
    -- ============================================
    
    -- Collapse multiple spaces to single space (PRESERVES word separation)
    result := TRIM(REGEXP_REPLACE(result, '\s+', ' ', 'g'));
    
    -- Remove spaces before punctuation (safety)
    result := REGEXP_REPLACE(result, '\s+([.,;:!?])', '\1', 'g');
    
    -- Final trim
    result := TRIM(result);
    
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
SET content = REGEXP_REPLACE(content, 'ragstyle',
'rag style', 'g')
WHERE content ~ 'ragstyle';
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





