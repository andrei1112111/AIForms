document.addEventListener('DOMContentLoaded', function() {
    const md = window.markdownit({
        html: false,
        linkify: true,
        typographer: true,
        highlight: function (str, lang) {
            if (lang && hljs.getLanguage(lang)) {
                try {
                    return `<pre><code class="hljs ${lang}">` +
                           hljs.highlight(str, { language: lang }).value +
                           "</code></pre>";
                } catch (__) {}
            }
            return '<pre><code class="hljs">' + md.utils.escapeHtml(str) + '</code></pre>';
        }
    });

    // Элементы DOM
    const chooseAccountBtn = document.getElementById('chooseAccountBtn');
    const accountModal = document.getElementById('accountModal');
    const confirmAccountBtn = document.getElementById('confirmAccountBtn');
    const cancelAccountBtn = document.getElementById('cancelAccountBtn');
    const accountError = document.getElementById('accountError');
    const companyInput = document.getElementById('companyInput');
    const usernameInput = document.getElementById('usernameInput');
    
    const accountSummary = document.getElementById('accountSummary');
    const summaryCompany = document.getElementById('summaryCompany');
    const summaryUsername = document.getElementById('summaryUsername');
    const logoutBtn = document.getElementById('logoutBtn');
    
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    const chatArea = document.getElementById('chatArea');
    const heroSection = document.getElementById('heroSection');
    
    let chatSearchContainer = null;
    let currentEventSource = null;
    let currentQuery = '';

    // обновить шапку с данными аккаунта
    function setAccountSummary(company, username) {
        summaryCompany.textContent = company;
        summaryUsername.textContent = username;
        accountSummary.hidden = false;
        chooseAccountBtn.hidden = true;
    }
    
    // закинуть сообщения в чат
    function appendMessage(text, kind, stage = null, isProgress = false) {
        const div = document.createElement('div');
        div.className = `message ${kind === 'query' ? 'user-message' : 'assistant-message'} ${isProgress ? 'progress-message' : ''}`;
        
        if (isProgress) {
            div.innerHTML = `
                <div class="message-content">${text}</div>
                ${stage ? `<div class="processing-stage">${stage}</div>` : ''}
            `;
        } else {
            div.innerHTML = md.render(text);
            if (stage) {
                const stageDiv = document.createElement('div');
                stageDiv.className = 'processing-stage';
                stageDiv.textContent = stage;
                div.appendChild(stageDiv);
            }
        }

        const meta = document.createElement('div');
        meta.className = 'message-meta';
        meta.textContent = new Date().toLocaleString();
        div.appendChild(meta);
        
        chatArea.appendChild(div);
        window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});
        
        return div;
    }
    
    // обновление прогресс обработки сообщения
    function updateProgressMessage(stage, message, messageDiv) {
        if (!messageDiv) return;
        
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="progress-indicator">
                    <div class="progress-spinner"></div>
                    <span>${message}</span>
                </div>
            </div>
            <div class="processing-stage">${stage}</div>
            <div class="message-meta">${new Date().toLocaleString()}</div>
        `;
        
        window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});
    }
    
    // завершение прогресс обработки сообщения с результатом
    function finishProgressMessage(messageDiv, finalMessage, stage, data = null) {
        if (!messageDiv) return;
        
        if (data && data.large_data) {
            // большие данные - показываем кнопки выбора
            messageDiv.innerHTML = `
                <div class="message-content">
                    ${md.render(finalMessage)}
                    ${createLargeDataChoice(data.data_id, data.data_size, data.data_preview).outerHTML}
                </div>
                <div class="processing-stage">${stage}</div>
                <div class="message-meta">${new Date().toLocaleString()}</div>
            `;
        } else if (data && data.reply) {
            // ббычный ответ
            messageDiv.innerHTML = `
                <div class="message-content">${md.render(data.reply)}</div>
                <div class="processing-stage">${stage}</div>
                <div class="message-meta">${new Date().toLocaleString()}</div>
            `;
        } else {
            // простое сообщение
            messageDiv.innerHTML = `
                <div class="message-content">${md.render(finalMessage)}</div>
                <div class="processing-stage">${stage}</div>
                <div class="message-meta">${new Date().toLocaleString()}</div>
            `;
        }
        
        messageDiv.classList.remove('progress-message');
        window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});
    }
    
    // создание интерфейса выбора для больших данных
    function createLargeDataChoice(dataId, dataSize, dataPreview) {
        const container = document.createElement('div');
        container.className = 'large-data-choice';
        container.setAttribute('data-id', dataId);
        
        container.innerHTML = `
            <div class="choice-header">
                <h4>📊 Обнаружены данные большого объема</h4>
                <p>Размер данных: <strong>${dataSize.toLocaleString()} символов</strong> (превышает лимит в 4,000 символов)</p>
            </div>
            
            <div class="choice-options">
                <div class="option-card">
                    <div class="option-icon">💾</div>
                    <h5>Скачать данные</h5>
                    <p>Скачайте полные данные в формате JSON для анализа вручную</p>
                    <button class="choice-btn download-choice" onclick="downloadDataChoice('${dataId}')">
                        <i class="fas fa-download"></i> Скачать JSON
                    </button>
                </div>
                
                <div class="option-card">
                    <div class="option-icon">🚀</div>
                    <h5>Продолжить генерацию</h5>
                    <p>Возможно займет много времени</p>
                    <button class="choice-btn continue-choice" onclick="continueWithLimitedChoice('${dataId}')">
                        <i class="fas fa-play"></i> Продолжить
                    </button>
                </div>
            </div>
            
            <div class="data-preview">
                <details>
                    <summary>🔍 Показать превью данных (${Math.min(1000, dataPreview.length).toLocaleString()} символов)</summary>
                    <div class="preview-content">
                        <pre>${escapeHtml(dataPreview)}</pre>
                    </div>
                </details>
            </div>
        `;
        
        return container;
    }
    
    // экранирование HTML для превью
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    // глобальные функции для выбора качать json или додеп модели
    window.downloadDataChoice = async function(dataId) {
        const choiceContainer = document.querySelector(`.large-data-choice[data-id="${dataId}"]`);
        if (!choiceContainer) return;
        
        const downloadBtn = choiceContainer.querySelector('.download-choice');
        downloadBtn.disabled = true;
        downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Скачивание...';
        
        try {
            // качаем файл
            window.open(`/download-data?data_id=${encodeURIComponent(dataId)}`, '_blank');
            
            // показываем сообщение об успехе
            choiceContainer.innerHTML = `
                <div class="choice-complete">
                    <div class="success-icon">✅</div>
                    <p><strong>Данные успешно скачаны!</strong></p>
                    <p>Файл сохранен в формате JSON. Вы можете задать новый вопрос.</p>
                </div>
            `;
        } catch (error) {
            downloadBtn.disabled = false;
            downloadBtn.innerHTML = '<i class="fas fa-download"></i> Скачать JSON';
            alert('Ошибка при скачивании: ' + error.message);
        }
    };
    
    window.continueWithLimitedChoice = async function(dataId) {
        const choiceContainer = document.querySelector(`.large-data-choice[data-id="${dataId}"]`);
        if (!choiceContainer) return;
        
        const continueBtn = choiceContainer.querySelector('.continue-choice');
        continueBtn.disabled = true;
        continueBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Генерация...';
        
        try {
            const response = await fetch('/generate-with-limited-data', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                credentials: 'same-origin',
                body: JSON.stringify({data_id: dataId})
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Ошибка генерации');
            }
            
            // заменяем выбор на сгенерированный ответ
            const messageDiv = choiceContainer.closest('.message');
            messageDiv.innerHTML = `
                <div class="message-content">${md.render(data.reply)}</div>
                <div class="processing-stage">${data.stage}</div>
                <div class="message-meta">${new Date().toLocaleString()}</div>
            `;
            
        } catch (error) {
            continueBtn.disabled = false;
            continueBtn.innerHTML = '<i class="fas fa-play"></i> Продолжить';
            alert('Ошибка при генерации: ' + error.message);
        }
    };
    
    // фиксированная поисковая строка для чата
    function createChatSearch() {
        if (chatSearchContainer) return;
        
        chatSearchContainer = document.createElement('div');
        chatSearchContainer.className = 'chat-search-container';
        chatSearchContainer.innerHTML = `
            <input type="text" id="chatSearchInput" class="search-box" placeholder="Задайте следующий вопрос...">
            <button id="chatSearchBtn" class="search-btn">
                <i class="fas fa-paper-plane"></i>
            </button>
        `;
        
        document.body.appendChild(chatSearchContainer);
        
        const chatSearchInput = document.getElementById('chatSearchInput');
        const chatSearchBtn = document.getElementById('chatSearchBtn');
        
        chatSearchBtn.addEventListener('click', () => {
            const q = chatSearchInput.value.trim();
            if (!q) return;
            sendQuery(q);
            chatSearchInput.value = '';
        });
        
        chatSearchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                chatSearchBtn.click();
            }
        });
        
        setTimeout(() => chatSearchInput.focus(), 100);
    }
    
    // Запроса поиска с SSE
    function sendQuery(query) {
        if (!query) return;
        
        currentQuery = query;
        
        // закрываем предыдущее соединение если открыто
        if (currentEventSource) {
            currentEventSource.close();
        }
        
        // показать чат если это первый запрос
        if (chatArea.style.display === 'none' || window.getComputedStyle(chatArea).display === 'none') {
            heroSection.style.display = 'none';
            chatArea.style.display = 'block';
            createChatSearch();
        }
        
        // добавить сообщение пользователя
        appendMessage(query, 'query');
        
        // добавляем обрбатывающееся сообщение
        const progressMessage = appendMessage('Подготовка к обработке...', 'reply', '(0/3) → Начинаем обработку', true);
        
        // делаем кнопку поиска неактивной
        const currentSearchBtn = document.getElementById('chatSearchBtn') || searchBtn;
        const currentSearchInput = document.getElementById('chatSearchInput') || searchInput;
        
        currentSearchBtn.disabled = true;
        currentSearchInput.disabled = true;
        
        // создаем SSE соединение
        currentEventSource = new EventSource(`/search-stream?query=${encodeURIComponent(query)}`);
        
        currentEventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            if (data.final) {
                finishProgressMessage(progressMessage, data.message, data.stage, data.data);
                currentEventSource.close();
                
                currentSearchBtn.disabled = false;
                currentSearchInput.disabled = false;
                currentSearchInput.focus();
            } else {
                updateProgressMessage(data.stage, data.message, progressMessage);
            }
        };
        
        currentEventSource.onerror = function(event) {
            finishProgressMessage(progressMessage, 'Ошибка соединения с сервером', 'Ошибка');
            currentEventSource.close();
            
            currentSearchBtn.disabled = false;
            currentSearchInput.disabled = false;
            currentSearchInput.focus();
        };
    }
    
    searchBtn.addEventListener('click', () => {
        const q = searchInput.value.trim();
        if (!q) return;
        sendQuery(q);
        searchInput.value = '';
    });
    
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            searchBtn.click();
        }
    });
    
    chooseAccountBtn.addEventListener('click', () => {
        accountError.hidden = true;
        companyInput.value = '';
        usernameInput.value = '';
        accountModal.hidden = false;
        companyInput.focus();
    });
    
    cancelAccountBtn.addEventListener('click', () => accountModal.hidden = true);
    
    confirmAccountBtn.addEventListener('click', async () => {
        accountError.hidden = true;
        const company = companyInput.value.trim();
        const username = usernameInput.value.trim();
        
        if (!company || !username) {
            accountError.hidden = false;
            accountError.textContent = 'Оба поля обязательны';
            return;
        }

        // меняем кнопку на "Поиск..." и делаем неактивной
        confirmAccountBtn.disabled = true;
        confirmAccountBtn.innerHTML = '🔍 Поиск...';
        cancelAccountBtn.disabled = true;
        
        try {
            const res = await fetch('/validate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                credentials: 'same-origin',
                body: JSON.stringify({company, username, fio: username})
            });
            
            const data = await res.json();
            
            // восстанавливаем кнопку
            confirmAccountBtn.disabled = false;
            confirmAccountBtn.innerHTML = '✅ Подтвердить';
            cancelAccountBtn.disabled = false;

            if (!data.ok) {
                accountError.hidden = false;
                accountError.textContent = data.error || 'Ошибка валидации';
                return;
            }
            
            accountModal.hidden = true;
            setAccountSummary(data.company || company, data.name || data.username || username);
        } catch (err) {
            // восстанавливаем кнопку
            confirmAccountBtn.disabled = false;
            confirmAccountBtn.innerHTML = '✅ Подтвердить';
            cancelAccountBtn.disabled = false;

            accountError.hidden = false;
            accountError.textContent = 'Сетевая ошибка';
        }
    });
    
    accountModal.addEventListener('click', (e) => {
        if (e.target === accountModal) {
            accountModal.hidden = true;
        }
    });
    
    // инициализация шапки при загрузке
    (function loadFromCookies() {
        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) {
                // если значение содержит много экранированных символов - пропускаем
                // // if (cookieValue && cookieValue.includes('\\3') && cookieValue.includes('\\"')) {
                    // // return null;
                // // }
                return decodeURIComponent(parts.pop().split(';').shift());
            }
            return null;
        }
        
        const username = getCookie('name');
        const company = getCookie('company');
        
        if (username && company) {
            setAccountSummary(company, username);
        }
    })();

    // функция выхода из аккаунта
    function logout() {
        // чистим cookies
        document.cookie = "user_id=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        document.cookie = "department_id=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        document.cookie = "name=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        document.cookie = "username=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        document.cookie = "company=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        
        // чистим localStorage если используется
        localStorage.removeItem('userData');
        
        // сбрасываем интерфейс
        setAccountSummary("", "")
        accountSummary.hidden = true;
        chooseAccountBtn.hidden = false;
        
        // чистим чат если он открыт
        if (chatArea.style.display !== 'none') {
            chatArea.style.display = 'none';
            heroSection.style.display = 'flex';
            
            // удаляем поисковую строку чата если есть
            if (chatSearchContainer) {
                chatSearchContainer.remove();
                chatSearchContainer = null;
            }
            
            // чистим сообщения
            chatArea.innerHTML = '';
        }
        
        console.log('Вышли из аккаунта');
    }

    logoutBtn.addEventListener('click', logout); 
});
