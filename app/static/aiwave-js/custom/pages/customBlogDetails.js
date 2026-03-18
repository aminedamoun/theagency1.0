document.addEventListener('DOMContentLoaded', function() {
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