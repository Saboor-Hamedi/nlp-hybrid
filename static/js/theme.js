/**
 * Neural Forensic Suite - Theme Manager
 * Handles Light/Dark mode persistence and DOM manipulation.
 */
(function() {
    const THEME_KEY = 'theme';
    
    // Set theme and sync toggles
    window.setTheme = function(theme) {
        if (theme === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
        localStorage.setItem(THEME_KEY, theme);
        
        // Sync any toggles on the page
        document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            if (cb.id && cb.id.includes('theme-toggle')) {
                cb.checked = (theme === 'dark');
            }
        });
    };

    window.toggleTheme = function() {
        const current = localStorage.getItem(THEME_KEY) || 'light';
        const next = current === 'light' ? 'dark' : 'light';
        setTheme(next);
    };

    // Initial sync
    const saved = localStorage.getItem(THEME_KEY) || 'light';
    setTheme(saved);
    
    document.addEventListener('DOMContentLoaded', () => {
        setTheme(localStorage.getItem(THEME_KEY) || 'light');
    });
})();
