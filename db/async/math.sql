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
