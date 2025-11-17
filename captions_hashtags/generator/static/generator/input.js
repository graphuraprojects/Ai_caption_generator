// Navbar Hamburger Toggle
document.addEventListener('DOMContentLoaded', () => {
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('nav-menu');

    // Toggle dropdown
    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        navMenu.classList.toggle('active');
    });

    // Close dropdown on link click
    document.querySelectorAll('#nav-menu ul li a').forEach(link => {
        link.addEventListener('click', () => {
            hamburger.classList.remove('active');
            navMenu.classList.remove('active');
        });
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const checkboxes = document.querySelectorAll('input[name="platforms"]');
    const maxSelection = 3;

    checkboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", function () {
            const checked = document.querySelectorAll('input[name="platforms"]:checked').length;

            if (checked > maxSelection) {
                alert(`You can select a maximum of ${maxSelection} platforms.`);
                this.checked = false; // undo the extra selection
            }
        });
    });

    // Handle form submission and button state
    const form = document.querySelector('form');
    const generateBtn = document.getElementById('generate-btn');

    form.addEventListener('submit', function (e) {
        // Change button text to "Generating..."
        generateBtn.textContent = 'Generating...';
        generateBtn.disabled = true;

        // Optionally, you can add a loading spinner or animation here
        // For example: generateBtn.innerHTML = '<span class="spinner"></span> Generating...';
    });
});
