window.addEventListener('load', function () {
    setTimeout(() => {
        // Try different selectors for nested admin vorgabe elements
        const selectors = [
            '.djn-dynamic-form-dokumente-vorgabe',
            '.djn-dynamic-form-Standards-vorgabe',
            '.inline-related[data-inline-type="stacked"]',
            '.nested-inline'
        ];
        
        let vorgabenBlocks = [];
        for (const selector of selectors) {
            vorgabenBlocks = document.querySelectorAll(selector);
            if (vorgabenBlocks.length > 0) {
                console.log("Found", vorgabenBlocks.length, "Vorgaben blocks with selector:", selector);
                break;
            }
        }

        if (vorgabenBlocks.length === 0) {
            console.log("No Vorgaben blocks found, trying fallback...");
            // Fallback: look for any inline with vorgabe in the class
            vorgabenBlocks = document.querySelectorAll('[class*="vorgabe"]');
        }

        vorgabenBlocks.forEach((block, index) => {
            // Find the existing title/header within the vorgabe block
            const existingHeader = block.querySelector('h3, .inline-label, .module h2, .djn-inline-header');
            
            if (existingHeader) {
                // Make the existing header clickable for collapse/expand
                existingHeader.style.cursor = 'pointer';
                existingHeader.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Find all content to collapse - everything except the header itself
                    const allChildren = Array.from(block.children);
                    const contentElements = allChildren.filter(child => child !== existingHeader && !child.contains(existingHeader));
                    
                    contentElements.forEach(element => {
                        const isHidden = element.style.display === 'none';
                        element.style.display = isHidden ? '' : 'none';
                    });
                    
                    // Update the header text to show collapse state
                    const originalText = existingHeader.textContent.replace(/[▼▶]\s*/, '');
                    const anyHidden = contentElements.some(el => el.style.display === 'none');
                    existingHeader.innerHTML = `${anyHidden ? '▶' : '▼'} ${originalText}`;
                });
                
                // Add initial collapse indicator
                const originalText = existingHeader.textContent;
                existingHeader.innerHTML = `▼ ${originalText}`;
            }
        });
    }, 1000); // wait longer to allow nested inlines to render
});
