document.addEventListener('DOMContentLoaded', () => {

    // --- VARIABLES GLOBALES ---
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    const input = document.getElementById('passwordInput');
    const btn = document.getElementById('sendBtn');
    const wrapper = document.getElementById('homeInputWrapper');
    const resultSolo = document.getElementById('resultSolo');

    const targetInput = document.getElementById('target-pwd-input');
    const targetBtn = document.getElementById('target-btn');
    const targetResult = document.getElementById('target-result');

    const pFirst = document.getElementById('target-firstname');
    const pLast = document.getElementById('target-lastname');
    const pDate = document.getElementById('target-birthdate');
    const pWord = document.getElementById('target-word');
    const pZipBirth = document.getElementById('target-zip-birth');
    const pZipHome = document.getElementById('target-zip-home');

    const modelSelect = document.getElementById('modelSelect');
    const displaySpan = document.getElementById('selectedModelText');

    const burgerBtn = document.getElementById('burgerBtn');
    const sideMenu = document.getElementById('sideMenu');
    const closeMenuBtn = document.getElementById('closeMenuBtn');
    const menuItems = document.querySelectorAll('.menu-list li');
    const docOverlay = document.getElementById('docOverlay');
    const closeDocBtn = document.getElementById('closeDocBtn');
    const docContents = document.querySelectorAll('.doc-content');

    let lastPassword = "";

    // --- NAVIGATION ---
    navButtons.forEach(btnTab => {
        btnTab.addEventListener('click', () => {
            navButtons.forEach(b => b.classList.remove('active'));
            btnTab.classList.add('active');
            tabContents.forEach(content => content.classList.add('hidden'));
            const targetId = 'tab-' + btnTab.dataset.tab;
            if(document.getElementById(targetId)) document.getElementById(targetId).classList.remove('hidden');
        });
    });

    // --- SELECTEUR MODÈLE ---
    function updateModelDisplay() {
        if (modelSelect && displaySpan) {
            const selectedOption = modelSelect.options[modelSelect.selectedIndex];
            if (selectedOption) displaySpan.textContent = selectedOption.text.split('(')[0].trim();
        }
    }
    if (modelSelect) {
        updateModelDisplay();
        modelSelect.addEventListener('change', () => {
            updateModelDisplay();
            if (lastPassword && !document.getElementById('tab-home').classList.contains('hidden')) {
                runHomeAnalysis(lastPassword);
            }
        });
    }

    // --- API ---
    async function fetchAnalysis(password, model) {
        try {
            const response = await fetch("http://127.0.0.1:8000/test-password", {
                method: "POST",
                headers: { 'Content-Type': "application/json" },
                body: JSON.stringify({ password: password, model_type: model })
            });
            return await response.json();
        } catch (err) {
            console.error('Erreur API:', err);
            return null;
        }
    }

    async function runHomeAnalysis(password) {
        const selectedModel = modelSelect ? modelSelect.value : 'rf';
        if (resultSolo) {
            resultSolo.classList.remove('hidden');
            resultSolo.innerHTML = '<div class="text-center text-muted"><i class="fa-solid fa-spinner fa-spin"></i> Analyse en cours...</div>';
        }
        const data = await fetchAnalysis(password, selectedModel);
        if (resultSolo && data) renderCard(resultSolo, data);
    }

    // --- HOME (SOLO) ---
    if (input && btn) {
        input.addEventListener('input', () => {
            input.value.trim().length > 0 ? btn.classList.add('visible') : btn.classList.remove('visible');
        });
        input.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); btn.click(); } });
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
            runHomeAnalysis(pwd);
        });
    }

    // --- TARGETED ATTACK ---
    if (targetInput && targetBtn) {
        targetInput.addEventListener('input', () => {
            targetInput.value.trim().length > 0 ? targetBtn.classList.add('visible') : targetBtn.classList.remove('visible');
        });
        targetInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); targetBtn.click(); } });
        targetInput.addEventListener('focus', () => { targetBtn.style.backgroundColor = '#30243F'; targetBtn.style.color = '#e0d9f3'; });
        targetInput.addEventListener('blur', () => { targetBtn.style.backgroundColor = '#e0d9f3'; targetBtn.style.color = '#30243F'; });

        targetBtn.addEventListener('click', async () => {
            const pwd = targetInput.value;
            if (!pwd) return;

            // ANIMATION SPLIT VIEW
            const layoutContainer = document.getElementById('targetedContainer');
            if (layoutContainer) layoutContainer.classList.add('layout-active');

            targetInput.value = "";
            targetBtn.classList.remove('visible');
            targetInput.blur();

            targetResult.classList.remove('hidden');
            targetResult.innerHTML = '<div class="text-center text-danger-custom"><i class="fa-solid fa-radar fa-spin"></i> Simulation d\'attaque ciblée...</div>';

            const model = modelSelect ? modelSelect.value : 'rf';
            let data = await fetchAnalysis(pwd, model);

            if (!data) { targetResult.innerHTML = "Erreur API"; return; }

            // Vérification Profil
            let compromised = [];
            const checkList = [
                { val: pFirst.value, name: "Prénom" }, { val: pLast.value, name: "Nom" },
                { val: pWord.value, name: "Mot-clé" }, { val: pZipBirth.value, name: "CP Naissance" },
                { val: pZipHome.value, name: "CP Domicile" }
            ];
            checkList.forEach(item => {
                if (item.val && item.val.length > 2) {
                    if (pwd.toLowerCase().includes(item.val.toLowerCase())) compromised.push(item.name + " (" + item.val + ")");
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

    // --- RENDER CARD ---
    function renderCard(container, data, isMini = false, isHacked = false) {
        let statusText = "VULNÉRABLE", statusColor = "#ff4d4d";
        if (isHacked) { statusText = "COMPROMIS ☠️"; statusColor = "#ff0000"; }
        else if (data.score >= 80) { statusText = "EXCELLENT 🛡️"; statusColor = "#00e676"; }
        else if (data.score >= 60) { statusText = "ROBUSTE ✅"; statusColor = "#00e676"; }
        else if (data.score >= 40) { statusText = "MOYEN ⚠️"; statusColor = "#ffc107"; }

        let feedbackHTML = "";
        if (data.feedback && data.feedback.length > 0) {
            feedbackHTML = data.feedback.map(f => {
                let icon = "fa-xmark", color = "#ff4d4d";
                if (f.toLowerCase().includes("excellent")) { icon = "fa-check"; color = "#00e676"; }
                if (f.includes("DANGER")) { icon = "fa-skull-crossbones"; color = "#ff0000"; }
                return `<div class="d-flex align-items-start mb-1"><i class="fa-solid ${icon} me-2 mt-1" style="color:${color}"></i> <span>${f}</span></div>`;
            }).join('');
        } else {
            feedbackHTML = `<div style="color:#00e676"><i class="fa-solid fa-check me-2"></i> Aucun défaut détecté</div>`;
        }

        const titleClass = isHacked ? "hacked-alert" : "";

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
                    <small class="text-white d-block" style="font-size:0.7rem;text-transform:uppercase;">Temps estimé (Bruteforce)</small>
                    <span class="fw-bold text-white fs-5">${data.details.crack_time_display}</span>
                </div>
                <div class="col-6">
                    <small class="text-white d-block" style="font-size:0.7rem;text-transform:uppercase;">Complexité (Entropie)</small>
                    <span class="fw-bold text-white fs-5">${data.details.entropy_bits} bits</span>
                </div>
            </div>
            <hr style="border-color:rgba(255,255,255,0.1)">
            <div class="mt-3 text-start ps-2 pe-2">
                <h6 class="text-white mb-3" style="font-size:0.8rem">DIAGNOSTIC :</h6>
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

    // --- MENU BURGER ---
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