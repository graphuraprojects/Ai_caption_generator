document.addEventListener("DOMContentLoaded", function () {
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('nav-menu');

    if (hamburger && navMenu) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('active');
            navMenu.classList.toggle('active');
        });
        document.querySelectorAll('#nav-menu ul li a').forEach(link => {
            link.addEventListener('click', () => {
                hamburger.classList.remove('active');
                navMenu.classList.remove('active');
            });
        });
    }

    function setupCopyButtons() {
        const copyButtons = document.querySelectorAll('.copy-btn');
        copyButtons.forEach(btn => {
            btn.addEventListener('click', function () {
                const suggestionBox = btn.closest('.suggestion-box');
                const textToCopy = suggestionBox.querySelector('p').innerText;
                navigator.clipboard.writeText(textToCopy).then(() => {
                    btn.textContent = 'Copied ✅';
                    setTimeout(() => { btn.textContent = '📋 Copy'; }, 1500);
                });
            });
        });
    }
    setupCopyButtons();

    // Regenerate button
    const regenerateButtons = document.querySelectorAll('.regenerate-btn');

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    regenerateButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const platform = btn.dataset.platform;
            const index = btn.dataset.index;

            btn.disabled = true;
            btn.textContent = '⏳ Regenerating';

            fetch("", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrftoken,
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: `regenerate_platform=${platform}&suggestion_index=${index}`
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const suggestionBox = btn.closest('.suggestion-box');
                    const pTag = suggestionBox.querySelector('p');
                    pTag.innerHTML = data.suggestion.caption + 
                        (data.suggestion.hashtags_list.length > 0 ?
                        ' <span class="hashtags">' +
                        data.suggestion.hashtags_list.map(tag => `<span>#${tag}</span>`).join(' ') +
                        '</span>' : '');
                }
            })
            .finally(() => {
                btn.disabled = false;
                btn.textContent = '🔁 Regenerate';
                setupCopyButtons();
            });
        });
    });
});
