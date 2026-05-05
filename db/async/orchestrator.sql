-- MASTER ORCHESTRATOR: THE NEURAL CLEANER
-- Manages the execution flow based on toggle settings.

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
