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
