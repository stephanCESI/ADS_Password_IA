document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('passwordInput');
    const btn = document.getElementById('sendBtn');

    input.addEventListener('input', () => {
        if (input.value.trim().length > 0) {
            btn.classList.add('visible');
        } else {
            btn.classList.remove('visible');
        }
    });

    input.addEventListener('focus', () => {
        if (input.value.trim().length > 0) {
            btn.style.backgroundColor = '#30243F';
            btn.style.color = '#e0d9f3';
        }
    });

    input.addEventListener('blur', () => {
        if (input.value.trim().length > 0) {
            btn.style.backgroundColor = '#e0d9f3';
            btn.style.color = '#30243F';
        }
    });

    btn.addEventListener('click', async () => {
        const password = input.value;
        if (!password) return;

        try {
            const response = await fetch("http://127.0.0.1:8000/test-password", {
                method: "POST",
                headers: { 'Content-Type': "application/json" },
                body: JSON.stringify({ password })
            });
            const data = await response.json();
            console.log(data);
        } catch (err) {
            console.error('Erreur API:', err);
        }
    });
});
