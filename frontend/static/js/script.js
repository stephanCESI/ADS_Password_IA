/* version enregistrée + masque sélecteur duel IA */
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
    const resultSolo = document.getElementById('resultSolo');

    // Targeted Attack
    const targetInput = document.getElementById('target-pwd-input');
    const targetBtn = document.getElementById('target-btn');
    const targetResult = document.getElementById('target-result');

    // Champs Profil (Victime)
    const pFirst = document.getElementById('target-firstname');
    const pLast = document.getElementById('target-lastname');
    const pDate = document.getElementById('target-birthdate');
    const pWord = document.getElementById('target-word');
    const pZipBirth = document.getElementById('target-zip-birth');
    const pZipHome = document.getElementById('target-zip-home');

    // Duel Mots
    const dpInput1 = document.getElementById('dp-input1');
    const dpInput2 = document.getElementById('dp-input2');
    const dpBtn = document.getElementById('dp-btn');
    const dpResult1 = document.getElementById('dp-result1');
    const dpResult2 = document.getElementById('dp-result2');
    const cardP1 = document.getElementById('card-p1');
    const cardP2 = document.getElementById('card-p2');

    // Duel IA
    const diaInput = document.getElementById('dia-input');
    const diaBtn = document.getElementById('dia-btn');
    const diaModel1 = document.getElementById('dia-model1');
    const diaModel2 = document.getElementById('dia-model2');
    const diaResult1 = document.getElementById('dia-result1');
    const diaResult2 = document.getElementById('dia-result2');
    const cardIa1 = document.getElementById('card-ia1');
    const cardIa2 = document.getElementById('card-ia2');

    // Générateur
    const btnGen = document.getElementById('btn-generate');
    const btnAnalyzeGen = document.getElementById('btn-analyze-gen');
    const displayGen = document.getElementById('gen-password-display');
    const resultGen = document.getElementById('gen-result');
    const btnCopy = document.getElementById('copy-btn');
    let generatedPasswordCache = "";

    // Sélecteur de Modèle Global
    const modelSelect = document.getElementById('modelSelect');
    const displaySpan = document.getElementById('selectedModelText');
    const modelSelectorWrapper = document.querySelector('.model-selector-wrapper'); // Le conteneur à cacher

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
            // Retirer 'active' partout
            navButtons.forEach(b => b.classList.remove('active'));
            // Ajouter 'active' au bouton cliqué
            btnTab.classList.add('active');

            // Cacher tous les contenus
            tabContents.forEach(content => content.classList.add('hidden'));

            // Afficher le contenu correspondant
            const targetId = 'tab-' + btnTab.dataset.tab;
            if(document.getElementById(targetId)) {
                document.getElementById(targetId).classList.remove('hidden');
            }

            // --- GESTION VISIBILITÉ SÉLECTEUR GLOBAL ---
            // On le cache si on est sur le Duel de Modèles, sinon on l'affiche
            if (modelSelectorWrapper) {
                if (targetId === 'tab-duel-model') {
                    modelSelectorWrapper.style.display = 'none'; // Ou classList.add('hidden') si tu préfères
                } else {
                    modelSelectorWrapper.style.display = 'flex'; // Ou remove('hidden')
                }
            }
        });
    });

    // ============================================================
    // 3. GESTION DU SÉLECTEUR DE MODÈLE
    // ============================================================
    function updateModelDisplay() {
        if (modelSelect && displaySpan) {
            const selectedOption = modelSelect.options[modelSelect.selectedIndex];
            if (selectedOption) {
                displaySpan.textContent = selectedOption.text.split('(')[0].trim();
            }
        }
    }

    if (modelSelect) {
        updateModelDisplay();
        modelSelect.addEventListener('change', () => {
            updateModelDisplay();
            // Si on est sur l'onglet Home et qu'on a déjà un mdp
            if (lastPassword && !document.getElementById('tab-home').classList.contains('hidden')) {
                runHomeAnalysis(lastPassword);
            }
            // Si on est sur l'onglet Générateur
            if (generatedPasswordCache && !document.getElementById('tab-generator').classList.contains('hidden') && !resultGen.classList.contains('hidden')) {
                runGenAnalysis();
            }
        });
    }

    // ============================================================
    // 4. API & FONCTIONS D'ANALYSE
    // ============================================================

    // Appel Serveur pur
    async function fetchAnalysis(password, model) {
        try {
            const response = await fetch("http://127.0.0.1:8000/test-password", {
                method: "POST",
                headers: { 'Content-Type': "application/json" },
                body: JSON.stringify({ password: password, model_type: model })
            });
            // Récupération et LOG du JSON
            const data = await response.json();
            console.log("🔍 Résultat API (JSON) :", data);
            return data;
        } catch (err) {
            console.error('Erreur API:', err);
            return null;
        }
    }

    // --- ANALYSE HOME ---
    async function runHomeAnalysis(password) {
        const selectedModel = modelSelect ? modelSelect.value : 'rf';
        if (resultSolo) {
            resultSolo.classList.remove('hidden');
            resultSolo.innerHTML = '<div class="text-center text-muted"><i class="fa-solid fa-spinner fa-spin"></i> Analyse en cours...</div>';
        }
        const data = await fetchAnalysis(password, selectedModel);
        if (resultSolo && data) renderCard(resultSolo, data);
    }

    // --- ANALYSE GÉNÉRATEUR ---
    async function runGenAnalysis() {
        const model = modelSelect ? modelSelect.value : 'rf';
        if (resultGen) {
            resultGen.classList.remove('hidden');
            resultGen.innerHTML = '<div class="text-center text-muted">Vérification par le Juge...</div>';
        }
        const data = await fetchAnalysis(generatedPasswordCache, model);
        if (resultGen && data) renderCard(resultGen, data);
    }

    // ============================================================
    // 5. LOGIQUES DES ONGLETS
    // ============================================================

    // --- HOME (SOLO) ---
    if (input && btn) {
        input.addEventListener('input', () => {
            if (input.value.trim().length > 0) btn.classList.add('visible');
            else btn.classList.remove('visible');
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                btn.click();
            }
        });

        input.addEventListener('focus', () => { btn.style.backgroundColor = '#30243F'; btn.style.color = '#e0d9f3'; });
        input.addEventListener('blur', () => { btn.style.backgroundColor = '#e0d9f3'; btn.style.color = '#30243F'; });

        btn.addEventListener('click', async () => {
            const pwd = input.value;
            if (!pwd) return;
            lastPassword = pwd;

            if (wrapper) wrapper.classList.add('moved-up');
            input.value = "";
            btn.classList.remove('visible');
            input.blur();

            // Appel de la fonction centrale
            runHomeAnalysis(pwd);
        });
    }

    // --- DUEL MOTS ---
    if (dpBtn) {
        dpBtn.addEventListener('click', async () => {
            const p1 = dpInput1.value;
            const p2 = dpInput2.value;
            const model = modelSelect ? modelSelect.value : 'rf'; // Modèle global

            if(!p1 || !p2) return;

            // Reset UI
            cardP1.classList.remove('winner', 'loser');
            cardP2.classList.remove('winner', 'loser');
            dpResult1.classList.remove('hidden'); dpResult1.innerHTML = 'Calcul...';
            dpResult2.classList.remove('hidden'); dpResult2.innerHTML = 'Calcul...';

            const [d1, d2] = await Promise.all([
                fetchAnalysis(p1, model),
                fetchAnalysis(p2, model)
            ]);

            renderCard(dpResult1, d1, true); // true = mini
            renderCard(dpResult2, d2, true);

            if (d1.score > d2.score) { cardP1.classList.add('winner'); cardP2.classList.add('loser'); }
            else if (d2.score > d1.score) { cardP2.classList.add('winner'); cardP1.classList.add('loser'); }
        });
    }

    // --- DUEL IA ---
    if (diaBtn) {
        diaInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); diaBtn.click(); } });

        diaBtn.addEventListener('click', async () => {
            const pwd = diaInput.value;
            const m1 = diaModel1.value;
            const m2 = diaModel2.value;

            if(!pwd) return;

            cardIa1.classList.remove('winner', 'loser');
            cardIa2.classList.remove('winner', 'loser');
            diaResult1.classList.remove('hidden'); diaResult1.innerHTML = 'Calcul...';
            diaResult2.classList.remove('hidden'); diaResult2.innerHTML = 'Calcul...';

            const [d1, d2] = await Promise.all([
                fetchAnalysis(pwd, m1),
                fetchAnalysis(pwd, m2)
            ]);

            renderCard(diaResult1, d1, true);
            renderCard(diaResult2, d2, true);

            if (d1.score > d2.score) { cardIa1.classList.add('winner'); cardIa2.classList.add('loser'); }
            else if (d2.score > d1.score) { cardIa2.classList.add('winner'); cardIa1.classList.add('loser'); }
        });
    }

    // --- TARGETED ATTACK ---
    if (targetInput && targetBtn) {
        targetInput.addEventListener('input', () => {
            targetInput.value.trim().length > 0 ? targetBtn.classList.add('visible') : targetBtn.classList.remove('visible');
        });
        targetInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); targetBtn.click(); } });

        targetBtn.addEventListener('click', async () => {
            const pwd = targetInput.value;
            if (!pwd) return;

            const layoutContainer = document.getElementById('targetedContainer');
            if (layoutContainer) layoutContainer.classList.add('layout-active');

            targetInput.value = ""; targetBtn.classList.remove('visible'); targetInput.blur();

            targetResult.classList.remove('hidden');
            targetResult.innerHTML = '<div class="text-center text-danger-custom"><i class="fa-solid fa-radar fa-spin"></i> Simulation d\'attaque ciblée...</div>';

            const model = modelSelect ? modelSelect.value : 'rf';
            let data = await fetchAnalysis(pwd, model);

            if (!data) { targetResult.innerHTML = "Erreur API"; return; }

            let compromised = [];
            const checkList = [
                { val: pFirst.value.trim(), name: "Prénom" },
                { val: pLast.value.trim(), name: "Nom" },
                { val: pWord.value.trim(), name: "Mot-clé" },
                { val: pZipBirth.value.trim(), name: "CP Naissance" },
                { val: pZipHome.value.trim(), name: "CP Domicile" }
            ];

            checkList.forEach(item => {
                if (item.val && item.val.length >= 2) {
                    const valLower = item.val.toLowerCase();
                    const pwdLower = pwd.toLowerCase();
                    if (pwdLower.includes(valLower)) compromised.push(item.name + " (" + item.val + ")");

                    if (item.name.startsWith("CP")) {
                        const dept = item.val.substring(0, 2);
                        if (pwd.includes(dept) && !pwdLower.includes(valLower)) {
                            const deptName = item.name.replace("CP ", "");
                            compromised.push(`Département ${deptName} (${dept})`);
                        }
                    }
                }
            });

            if (pDate.value) {
                const dateObj = new Date(pDate.value);
                const year = dateObj.getFullYear().toString();
                const shortYear = year.slice(-2);
                const day = String(dateObj.getDate()).padStart(2, '0');
                const month = String(dateObj.getMonth() + 1).padStart(2, '0');
                if (pwd.includes(year)) compromised.push(`Année (${year})`);
                else if (pwd.includes(shortYear)) compromised.push(`Année courte (${shortYear})`);
                if (pwd.includes(day + month)) compromised.push(`Anniversaire (${day}${month})`);
            }

            if (compromised.length > 0) {
                data.score = 0; data.is_strong = false;
                const alertMsg = `<b>🚨 DANGER CRITIQUE :</b> Ingénierie Sociale détectée !<br>Éléments trouvés : ${compromised.join(", ")}.`;
                data.feedback.unshift(alertMsg);
            }
            renderCard(targetResult, data, false, compromised.length > 0);
        });
    }

    // --- GÉNÉRATEUR ---
    if (btnGen) {
        btnGen.addEventListener('click', async () => {
            displayGen.style.color = "#aaa"; displayGen.innerText = "Génération...";
            resultGen.classList.add('hidden'); btnAnalyzeGen.classList.add('hidden');
            try {
                const response = await fetch("http://127.0.0.1:8000/generate-password");
                const data = await response.json();
                generatedPasswordCache = data.generated_password;
                displayGen.innerText = generatedPasswordCache; displayGen.style.color = "#fff";
                btnAnalyzeGen.classList.remove('hidden');
            } catch (e) { displayGen.innerText = "Erreur Serveur"; }
        });
        btnAnalyzeGen.addEventListener('click', runGenAnalysis);
        btnCopy.addEventListener('click', () => {
            if(generatedPasswordCache) {
                navigator.clipboard.writeText(generatedPasswordCache);
                const original = btnCopy.innerHTML;
                btnCopy.innerHTML = '<i class="fa-solid fa-check" style="color:#00e676"></i>';
                setTimeout(() => btnCopy.innerHTML = original, 1500);
            }
        });
    }

    // ============================================================
    // 6. FONCTION D'AFFICHAGE (RENDERER)
    // ============================================================
    function renderCard(container, data, isMini = false, isHacked = false) {
        let statusText = "VULNÉRABLE", statusColor = "#ff4d4d";
        if (isHacked) { statusText = "COMPROMIS ☠️"; statusColor = "#ff0000"; }
        else if (data.score >= 80) { statusText = "EXCELLENT 🛡️"; statusColor = "#00e676"; }
        else if (data.score >= 60) { statusText = "ROBUSTE ✅"; statusColor = "#00e676"; }
        else if (data.score >= 40) { statusText = "MOYEN ⚠️"; statusColor = "#ffc107"; }

        let feedbackHTML = "";
        if (data.feedback && data.feedback.length > 0) {
            feedbackHTML = data.feedback.map(f => {
                let iconClass = "fa-xmark", iconColor = "#ff4d4d";
                if (f.toLowerCase().includes("excellent") || f.toLowerCase().includes("bravo")) { iconClass = "fa-check"; iconColor = "#00e676"; }
                if (f.includes("DANGER")) { iconClass = "fa-skull-crossbones"; iconColor = "#ff0000"; }
                return `<div class="d-flex align-items-start mb-1"><i class="fa-solid ${iconClass} me-2 mt-1" style="color:${iconColor}"></i> <span>${f}</span></div>`;
            }).join('');
        } else {
            feedbackHTML = `<div style="color:#00e676"><i class="fa-solid fa-check me-2"></i> Aucun défaut détecté</div>`;
        }

        const titleClass = isHacked ? "hacked-alert" : "";

        // MODE MINI
        if (isMini) {
            container.innerHTML = `
                <div class="text-center">
                    <h2 style="color:${statusColor}; margin:0; font-size: 2.5rem;">${data.score}</h2>
                    <small style="opacity:0.7; letter-spacing:1px">${statusText}</small>
                    <div style="background:rgba(255,255,255,0.1); height:6px; border-radius:5px; margin:10px 0;">
                        <div style="width:${data.score}%; background:${statusColor}; height:100%"></div>
                    </div>
                    <div style="font-size:0.8rem; text-align:left; color:#ccc">${feedbackHTML}</div>
                </div>`;
        } else {
            // MODE COMPLET
            container.innerHTML = `
                <div class="text-center mb-3">
                    <h1 class="${titleClass}" style="color: ${statusColor}; font-weight:bold; margin: 10px 0;">${data.score}/100</h1>
                    <p style="letter-spacing: 3px; font-weight:bold; opacity:0.8; color:${statusColor}">${statusText}</p>
                </div>
                <div class="analyzed-password text-center mb-3">${data.password}</div>
                <div class="score-track">
                    <div class="score-text-overlay">${data.score} / 100</div>
                    <div class="score-fill" style="width: 0%;"></div>
                </div>
                <div class="row text-center mt-4 mb-4">
                    <div class="col-6 border-end border-secondary">
                        <small class="text-muted d-block" style="font-size:0.7rem;text-transform:uppercase; letter-spacing: 1px;">Temps estimé (Bruteforce)</small>
                        <span class="fw-bold text-white fs-5">${data.details.crack_time_display}</span>
                    </div>
                    <div class="col-6">
                        <small class="text-muted d-block" style="font-size:0.7rem;text-transform:uppercase; letter-spacing: 1px;">Complexité (Entropie)</small>
                        <span class="fw-bold text-white fs-5">${data.details.entropy_bits} bits</span>
                    </div>
                </div>
                <hr style="border-color:rgba(255,255,255,0.1)">
                <div class="mt-3 text-start ps-2 pe-2">
                    <h6 class="text-muted mb-3" style="font-size:0.8rem">DIAGNOSTIC :</h6>
                    <div style="color: #e0d9f3;">${feedbackHTML}</div>
                </div>
            `;
            setTimeout(() => {
                const track = container.querySelector('.score-track');
                const bar = container.querySelector('.score-fill');
                if (track && bar) {
                    const trackWidth = track.offsetWidth;
                    bar.style.backgroundSize = `${trackWidth}px 100%`;
                    bar.style.width = `${data.score}%`;
                }
            }, 50);
        }
    }

    // ============================================================
    // 7. GESTION MENU BURGER & DOC
    // ============================================================
    if (burgerBtn) burgerBtn.addEventListener('click', () => { sideMenu.classList.add('open'); });
    if (closeMenuBtn) closeMenuBtn.addEventListener('click', () => { sideMenu.classList.remove('open'); });
    document.addEventListener('click', (e) => {
        if (sideMenu && sideMenu.classList.contains('open') && !sideMenu.contains(e.target) && !burgerBtn.contains(e.target)) sideMenu.classList.remove('open');
    });
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
    if (closeDocBtn) closeDocBtn.addEventListener('click', () => { docOverlay.classList.add('hidden'); });
});