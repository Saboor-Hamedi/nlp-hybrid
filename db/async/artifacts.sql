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
