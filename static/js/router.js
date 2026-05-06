/**
 * High-Performance Forensic Router
 * Zero-Reload SPA Navigation Engine
 */

document.addEventListener('DOMContentLoaded', () => {
    const mainContent = document.querySelector('main .max-w-5xl');
    
    // Universal Link Interceptor
    document.addEventListener('click', async (e) => {
        const link = e.target.closest('a');
        if (!link) return;

        // Origin Validation: Only intercept internal links
        const url = link.getAttribute('href');
        if (!url || url.startsWith('http') || url.startsWith('//') || link.getAttribute('target') === '_blank') return;

        e.preventDefault();
        await navigateTo(url);
    });

    // Handle back/forward
    window.addEventListener('popstate', () => {
        navigateTo(window.location.pathname, false);
    });

    /**
     * Surgical Page Navigation
     * @param {string} url - Target Forensic Pathway
     * @param {boolean} push - Whether to update history
     */
    async function navigateTo(url, push = true) {
        if (!mainContent) return;

        // Entry Transition & Telemetry
        mainContent.style.opacity = '0.3';
        mainContent.style.filter = 'blur(2px)';
        mainContent.style.transition = 'all 0.4s ease';

        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('Pathway access denied');
            
            const text = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(text, 'text/html');
            const newContent = doc.querySelector('main .max-w-5xl');

            if (newContent) {
                // Update Page Title
                document.title = doc.title || 'Neural Forensic Suite';

                // Surgical Swap
                mainContent.innerHTML = newContent.innerHTML;
                
                // Re-execute scripts to wake up graphs/interactives
                const scripts = newContent.querySelectorAll('script');
                scripts.forEach(oldScript => {
                    const newScript = document.createElement('script');
                    Array.from(oldScript.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
                    newScript.appendChild(document.createTextNode(oldScript.innerHTML));
                    document.body.appendChild(newScript);
                    // Cleanup to prevent DOM bloating
                    newScript.remove(); 
                });

                // Update URL
                if (push) history.pushState({ url }, '', url);

                // Update Active State in Sidebar
                updateSidebarActive(url);
            } else {
                console.warn('Surgical anchor not found, falling back to hard navigation');
                window.location.href = url;
            }
        } catch (error) {
            console.error('SPA Navigation Failed:', error);
            window.location.href = url; // Hard fallback for stability
        } finally {
            // Exit Transition
            setTimeout(() => {
                mainContent.style.opacity = '1';
                mainContent.style.filter = 'none';
            }, 50);
        }
    }

    function updateSidebarActive(currentPath) {
        document.querySelectorAll('.nav-link').forEach(link => {
            const href = link.getAttribute('href');
            if (href === currentPath) {
                link.classList.add('bg-blue-50', 'dark:bg-blue-900/20', 'text-blue-600', 'font-bold');
                link.classList.remove('font-medium');
            } else {
                link.classList.remove('bg-blue-50', 'dark:bg-blue-900/20', 'text-blue-600', 'font-bold');
                link.classList.add('font-medium');
            }
        });
    }

    // Initialize active state on load
    updateSidebarActive(window.location.pathname);
});
