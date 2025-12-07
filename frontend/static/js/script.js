document.addEventListener('DOMContentLoaded', () => {

    // ============================================================
    // 1. VARIABLES & ÉLÉMENTS DU DOM
    // ============================================================
    // Navigation
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    // Home / Solo
    const input = document.getElementById('passwordInput');
    const btn = document.getElementById('sendBtn');
    const wrapper = document.getElementById('homeInputWrapper');
    const resultSolo = document.getElementById('resultSolo'); // La carte de résultat

    // Sélecteur de Modèle
    const modelSelect = document.getElementById('modelSelect');
    const displaySpan = document.getElementById('selectedModelText');

    // Menu & Doc
    const burgerBtn = document.getElementById('burgerBtn');
    const sideMenu = document.getElementById('sideMenu');
    const closeMenuBtn = document.getElementById('closeMenuBtn');
    const menuItems = document.querySelectorAll('.menu-list li');
    const docOverlay = document.getElementById('docOverlay');
    const closeDocBtn = document.getElementById('closeDocBtn');
    const docContents = document.querySelectorAll('.doc-content');

    let lastPassword = "";

    // ============================================================
    // 2. GESTION DE LA NAVIGATION (ONGLETS)
    // ============================================================
    navButtons.forEach(btnTab => {
        btnTab.addEventListener('click', () => {
            navButtons.forEach(b => b.classList.remove('active'));
            btnTab.classList.add('active');
            tabContents.forEach(content => content.classList.add('hidden'));
            const targetId = 'tab-' + btnTab.dataset.tab;
            if(document.getElementById(targetId)) {
                document.getElementById(targetId).classList.remove('hidden');
            }
        });
    });

    // ============================================================
    // 3. GESTION DU SÉLECTEUR DE MODÈLE (OVERLAY)
    // ============================================================
    function updateModelDisplay() {
        if (modelSelect && displaySpan) {
            const selectedOption = modelSelect.options[modelSelect.selectedIndex];
            if (selectedOption) {
                // Affiche "Random Forest" sans le pourcentage pour le style
                displaySpan.textContent = selectedOption.text.split('(')[0].trim();
            }
        }
    }

    if (modelSelect) {
        updateModelDisplay(); // Init au chargement
        modelSelect.addEventListener('change', () => {
            updateModelDisplay();
            // Relance l'analyse si on change de modèle avec un mdp déjà saisi
            if (lastPassword) {
                console.log("Changement de modèle, relance...");
                analyze(lastPassword);
            }
        });
    }

    // ============================================================
    // 4. LOGIQUE D'ANALYSE (HOME)
    // ============================================================

    // Gestion visuelle de l'input
    input.addEventListener('input', () => {
        if (input.value.trim().length > 0) btn.classList.add('visible');
        else btn.classList.remove('visible');
    });
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { e.preventDefault(); btn.click(); }
    });
    input.addEventListener('focus', () => { btn.style.backgroundColor = '#30243F'; btn.style.color = '#e0d9f3'; });
    input.addEventListener('blur', () => { btn.style.backgroundColor = '#e0d9f3'; btn.style.color = '#30243F'; });

    // Fonction principale d'appel API
    async function analyze(password) {
        const selectedModel = modelSelect ? modelSelect.value : 'rf';

        // Affichage du chargement
        if (resultSolo) {
            resultSolo.classList.remove('hidden');
            resultSolo.innerHTML = '<div class="text-center text-muted"><i class="fa-solid fa-spinner fa-spin"></i> Analyse en cours...</div>';
        }

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

            // APPEL DE L'AFFICHAGE
            if (resultSolo) renderCard(resultSolo, data);

        } catch (err) {
            console.error('Erreur API:', err);
            if (resultSolo) resultSolo.innerHTML = '<div class="text-danger text-center">Erreur de connexion. Vérifiez le serveur.</div>';
        }
    }

    // Clic sur le bouton Envoyer
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

    // ============================================================
    // 5. FONCTION D'AFFICHAGE (RENDERER)
    // ============================================================
    function renderCard(container, data) {
        // 1. Style selon le score
        let statusText = "VULNÉRABLE";
        let statusColor = "#ff4d4d";

        if (data.score >= 80) {
            statusText = "EXCELLENT 🛡️"; statusColor = "#00e676";
        } else if (data.score >= 60) {
            statusText = "ROBUSTE ✅"; statusColor = "#00e676";
        } else if (data.score >= 40) {
            statusText = "MOYEN ⚠️"; statusColor = "#ffc107";
        } else {
            statusText = "FAIBLE ❌"; statusColor = "#ff4d4d";
        }

        // 2. Feedbacks avec gestion intelligente des icônes
        let feedbackHTML = "";
        if (data.feedback && data.feedback.length > 0) {
            feedbackHTML = data.feedback.map(f => {
                // Si le message est positif (ex: "Mot de passe excellent !"), on met une coche verte
                let iconClass = "fa-xmark";
                let iconColor = "#ff4d4d"; // Rouge par défaut

                if (f.toLowerCase().includes("excellent") || f.toLowerCase().includes("bravo")) {
                    iconClass = "fa-check";
                    iconColor = "#00e676"; // Vert
                }

                return `<div class="d-flex align-items-start mb-1">
                    <i class="fa-solid ${iconClass} me-2 mt-1" style="color:${iconColor}"></i> 
                    <span>${f}</span>
                 </div>`;
            }).join('');
        } else {
            feedbackHTML = `<div style="color:#00e676"><i class="fa-solid fa-check me-2"></i> Aucun défaut détecté</div>`;
        }

        // 3. Construction HTML (Avec barre fixe et texte overlay)
        container.innerHTML = `
            <div class="text-center mb-3">
                <h1 style="color: ${statusColor}; font-weight:bold; margin: 10px 0;">${data.score}/100</h1>
                <p style="letter-spacing: 3px; font-weight:bold; opacity:0.8">${statusText}</p>
            </div>
            
            <div class="analyzed-password text-center mb-3">${data.password}</div>

            <!-- La Barre "Magique" -->
            <div class="score-track">
                <!-- Le texte est sorti de la barre pour être toujours visible et centré -->
                <div class="score-text-overlay">${data.score} / 100</div>
                
                <!-- La barre qui se remplit -->
                <div class="score-fill" style="width: 0%;"></div>
            </div>
            
            <div class="row text-center mt-4 mb-4">
                <div class="col-6 border-end border-secondary">
                    <small class="text-white d-block" style="font-size:0.7rem; text-transform:uppercase; letter-spacing: 1px;">Temps estimé (Bruteforce)</small>
                    <span class="fw-bold text-white fs-5">${data.details.crack_time_display}</span>
                </div>
                <div class="col-6">
                    <small class="text-white d-block" style="font-size:0.7rem; text-transform:uppercase; letter-spacing: 1px;">Complexité (Entropie)</small>
                    <span class="fw-bold text-white fs-5">${data.details.entropy_bits} bits</span>
                </div>
            </div>
            
            <hr style="border-color:rgba(255,255,255,0.1)">
            
            <div class="mt-3 text-start ps-2 pe-2">
                <h6 class="text-muted mb-3" style="font-size:0.8rem">DIAGNOSTIC IA :</h6>
                <div style="color: #e0d9f3;">${feedbackHTML}</div>
            </div>
        `;

        // 4. Animation Barre (Fix Dégradé)
        setTimeout(() => {
            const track = container.querySelector('.score-track');
            const bar = container.querySelector('.score-fill');

            if (track && bar) {
                // Fixe le background size à la taille totale du track
                const trackWidth = track.offsetWidth;
                bar.style.backgroundSize = `${trackWidth}px 100%`;
                // Lance l'animation
                bar.style.width = `${data.score}%`;
            }
        }, 50);
    }

    // ============================================================
    // 6. GESTION MENU BURGER & DOC
    // ============================================================
    // Ouvrir le menu
    if (burgerBtn) {
        burgerBtn.addEventListener('click', () => { sideMenu.classList.add('open'); });
    }
    // Fermer le menu
    if (closeMenuBtn) {
        closeMenuBtn.addEventListener('click', () => { sideMenu.classList.remove('open'); });
    }
    // Clic dehors
    document.addEventListener('click', (e) => {
        if (sideMenu && sideMenu.classList.contains('open') &&
            !sideMenu.contains(e.target) && !burgerBtn.contains(e.target)) {
            sideMenu.classList.remove('open');
        }
    });

    // Clic sur un article
    menuItems.forEach(item => {
        item.addEventListener('click', () => {
            const docId = item.dataset.doc;
            docContents.forEach(content => content.classList.add('hidden'));
            const targetContent = document.getElementById('content-' + docId);
            if (targetContent) targetContent.classList.remove('hidden');
            if (docOverlay) docOverlay.classList.remove('hidden');
            if (sideMenu) sideMenu.classList.remove('open');
        });
    });

    // Fermer la doc
    if (closeDocBtn) {
        closeDocBtn.addEventListener('click', () => { docOverlay.classList.add('hidden'); });
    }
});