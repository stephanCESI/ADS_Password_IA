document.addEventListener('DOMContentLoaded', () => {

    // --- GESTION DES ONGLETS ---
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            navButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            tabContents.forEach(content => content.classList.add('hidden'));
            const targetId = 'tab-' + btn.dataset.tab;
            document.getElementById(targetId).classList.remove('hidden');
        });
    });

    // --- ELEMENTS DU HOME ---
    const input = document.getElementById('passwordInput');
    const btn = document.getElementById('sendBtn');
    const wrapper = document.getElementById('homeInputWrapper');

    // --- ELEMENTS DU SÉLECTEUR ---
    const modelSelect = document.getElementById('modelSelect');
    const displaySpan = document.getElementById('selectedModelText'); // Le texte visible

    let lastPassword = "";

    // Fonction de mise à jour du texte (car le select est invisible)
    function updateModelDisplay() {
        if (modelSelect && displaySpan) {
            const selectedOption = modelSelect.options[modelSelect.selectedIndex];
            if (selectedOption) {
                // On affiche "Random Forest" (en enlevant le pourcentage pour le style, ou tout le texte)
                // Ici je prends tout avant la parenthèse pour faire propre
                displaySpan.textContent = selectedOption.text.split('(')[0].trim();
            }
        }
    }

    // --- 1. GESTION DE LA TOUCHE ENTRÉE ---
    input.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            btn.click();
        }
    });

    // --- 2. UI INPUT ---
    input.addEventListener('input', () => {
        if (input.value.trim().length > 0) btn.classList.add('visible');
        else btn.classList.remove('visible');
    });

    input.addEventListener('focus', () => {
        btn.style.backgroundColor = '#30243F'; btn.style.color = '#e0d9f3';
    });
    input.addEventListener('blur', () => {
        btn.style.backgroundColor = '#e0d9f3'; btn.style.color = '#30243F';
    });

    // --- FONCTION D'ANALYSE ---
    async function analyze(password) {
        const selectedModel = modelSelect ? modelSelect.value : 'rf';

        try {
            const response = await fetch("http://127.0.0.1:8000/test-password", {
                method: "POST",
                headers: { 'Content-Type': "application/json" },
                body: JSON.stringify({
                    password: password,
                    model_type: selectedModel
                })
            });
            const data = await response.json();
            console.log(`Résultat (${selectedModel}) :`, data);

            // TODO: renderCard(data) ici plus tard

        } catch (err) {
            console.error('Erreur API:', err);
        }
    }

    // --- 3. CLIC ENVOYER ---
    btn.addEventListener('click', async () => {
        const password = input.value;
        if (!password) return;

        lastPassword = password;

        if (wrapper) wrapper.classList.add('moved-up');
        input.value = "";
        btn.classList.remove('visible');
        input.blur();

        analyze(password);
    });

    // --- 4. GESTION SÉLECTEUR ---
    if (modelSelect) {
        // Init texte au chargement
        updateModelDisplay();

        modelSelect.addEventListener('change', () => {
            // A. Met à jour le texte visible
            updateModelDisplay();

            // B. Relance l'analyse si besoin
            if (lastPassword) {
                console.log("Changement de modèle, relance...");
                analyze(lastPassword);
            }
        });
    }
});