document.addEventListener('DOMContentLoaded', function() {
    // Add click event listeners to category links
    document.querySelectorAll('.category-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const categoryId = this.getAttribute('data-category');
            const targetElement = document.getElementById('category-' + categoryId.toLowerCase().replace(/\s+/g, '-'));
            
            if (targetElement) {
                // Remove active class from all links
                document.querySelectorAll('.category-link').forEach(l => l.classList.remove('active'));
                // Add active class to clicked link
                this.classList.add('active');
                
                // Scroll to the category section with offset
                const headerOffset = 100;
                const elementPosition = targetElement.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
});