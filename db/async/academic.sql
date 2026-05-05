-- MODULE A: ACADEMIC FILTER
CREATE OR REPLACE FUNCTION forensic_clean_academic(input_text TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN REGEXP_REPLACE(input_text, 
        'i\.\s*i\.\s*d\.|i\.\s*e\.\s*,?|qper⊗l?|dkl|standard errors in parentheses|p¡\.?\*{1,3}|\(\w+\s+et\s+al\.,\s+\d{4}\)|\(\w+\s+and\s+\w+,\s+\d{4}\)|\s+et\s+al\.|arxiv:[^,\.\s]+|biometrika[^,\.\s]+|doi:[^,\.\s]+|\(\d+\):–,\d+|\(\d+\):–,|\(\d+\):,|doi:\s*\.\./\.\.|isbn\s+\.|h\s+t\s+t\s+p\s*s?\s*:\s*/\s*/\s*d\s*o\s*i\s*\.\s*o\s*r\s*g', 
        ' ', 'gi');
END;
$$ LANGUAGE plpgsql;
