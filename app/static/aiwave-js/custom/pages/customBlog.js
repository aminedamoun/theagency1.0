document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('search-form');
    const searchInput = searchForm.querySelector('input[name="search"]');
    
    // Debounce function to limit API calls
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Handle search input changes
    searchInput.addEventListener('input', debounce(function() {
        if (this.value.length >= 2 || this.value.length === 0) {
            searchForm.submit();
        }
    }, 500));
    
    // Handle category clicks
    document.querySelectorAll('.category-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const category = this.getAttribute('href').split('=')[1];
            window.location.href = category ? `?category=${category}` : '{% url "aiwave-blog" %}';
        });
    });
    
    // Handle tag clicks
    document.querySelectorAll('.tag-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const tag = this.textContent.trim();
            window.location.href = `?search=${tag}`;
        });
    });

    document.querySelectorAll('.delete-blog-form').forEach(function(form) {
        const deleteBtn = form.querySelector('.btn-delete-blog');
        const confirmBox = form.querySelector('.delete-confirmation');
        const confirmBtn = form.querySelector('.btn-confirm-delete');
        let confirmationOpen = false;
        deleteBtn.addEventListener('click', function(e) {
            e.preventDefault();
            deleteBtn.style.display = 'none';
            confirmBox.style.display = 'inline-flex';
            confirmationOpen = true;
        });
        confirmBtn.addEventListener('click', function(e) {
            e.preventDefault();
            form.submit();
        });
        document.addEventListener('mousedown', function(event) {
            if (confirmationOpen && !form.contains(event.target)) {
                confirmBox.style.display = 'none';
                deleteBtn.style.display = '';
                confirmationOpen = false;
            }
        });
    });
});