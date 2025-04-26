document.addEventListener('DOMContentLoaded', () => {

    const apiKeyInput = document.getElementById('apiKeyInput');
    const processBtn = document.getElementById('processBtn');
    const resultOutput = document.getElementById('resultOutput');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultContainer = document.querySelector('.result-container');
    const fileInput = document.getElementById('fileInput');
    const fileInfoContainer = document.getElementById('fileInfoContainer');
    const fileLink = document.getElementById('fileLink');
    const fileNameSpan = document.getElementById('fileName');
    const deleteFileBtn = document.getElementById('deleteFileBtn');
    const toggleApiKeyButton = document.getElementById('toggleApiKey');

    let currentFile = null;
    let currentFileUrl = null;

    const backendProcessUrl = 'http://localhost:5000/process-code';

    function showLoading() {
        loadingIndicator.classList.add('visible');
        resultContainer.classList.add('loading');
        resultOutput.textContent = '';
        resultOutput.style.color = '#5a5c69';
    }

    function hideLoading() {
        loadingIndicator.classList.remove('visible');
        resultContainer.classList.remove('loading');
    }

    function clearFileInfo() {
        if (currentFileUrl) {
            URL.revokeObjectURL(currentFileUrl);
        }
        currentFile = null;
        currentFileUrl = null;
        fileInput.value = null;
        fileLink.href = '#';
        fileLink.removeAttribute('download');
        fileNameSpan.textContent = '';
        fileInfoContainer.style.display = 'none';
    }

    function displayResult(data) {
        resultOutput.innerHTML = '<h3>Console Output:</h3>';
        resultOutput.innerHTML += `<pre>${data.output}</pre>`;

        if (data.error && data.error.trim()) {
            resultOutput.innerHTML += '<h3>Errors:</h3>';
            resultOutput.innerHTML += `<pre style="color: red;">${data.error}</pre>`;
        }
    }

    processBtn.addEventListener('click', async () => {
        const apiKey = apiKeyInput.value.trim();
        const selectedFile = currentFile;

        if (!selectedFile) {
            resultOutput.textContent = 'Помилка: Будь ласка, завантажте файл з кодом.';
            resultOutput.style.color = 'red';
            return;
        }

        if (!apiKey) {
            resultOutput.textContent = 'Помилка: Будь ласка, введіть API ключ.';
            resultOutput.style.color = 'red';
            return;
        }

        showLoading();
        const formData = new FormData();
        formData.append('apiKey', apiKey);
        formData.append('codeFile', selectedFile, selectedFile.name);

        try {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', backendProcessUrl, true);

            xhr.onload = function () {
                hideLoading();
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const data = JSON.parse(xhr.responseText);
                        resultOutput.style.color = 'green';
                        displayResult(data);
                    } catch (jsonError) {
                        resultOutput.textContent = 'Помилка: Не вдалося розібрати відповідь сервера як JSON.';
                        resultOutput.style.color = 'red';
                    }
                } else {
                    let errorMessage = `Помилка ${xhr.status}: ${xhr.statusText}`;
                    if (xhr.status === 401) { errorMessage = 'Помилка 401: Неправильний або відсутній API ключ. Доступ заборонено.'; }
                    else if (xhr.status === 403) { errorMessage = 'Помилка 403: API ключ не має дозволу на цю операцію.'; }
                    else if (xhr.status === 400) { errorMessage = `Помилка 400: Неправильний запит.`; }
                    else if (xhr.status === 500) { errorMessage = `Помилка 500: Внутрішня помилка сервера.`; }

                    resultOutput.textContent = errorMessage;
                    resultOutput.style.color = 'red';
                }
            };

            xhr.onerror = function () {
                hideLoading();
                resultOutput.textContent = `Помилка мережі або виконання запиту.`;
                resultOutput.style.color = 'red';
            };

            xhr.send(formData);

        } catch (error) {
            hideLoading();
            resultOutput.textContent = `Помилка мережі або виконання запиту: ${error.message}`;
            resultOutput.style.color = 'red';
        }
    });

    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (file) {
            clearFileInfo();
            currentFile = file;
            currentFileUrl = URL.createObjectURL(file);
            fileLink.href = currentFileUrl;
            fileLink.download = file.name;
            fileNameSpan.textContent = file.name;
            fileInfoContainer.style.display = 'flex';
        } else {
            clearFileInfo();
        }
    });

    deleteFileBtn.addEventListener('click', () => {
        clearFileInfo();
    });

    toggleApiKeyButton.addEventListener('click', () => {
        const isPassword = apiKeyInput.getAttribute('type') === 'password';
        apiKeyInput.setAttribute('type', isPassword ? 'text' : 'password');

        const icon = toggleApiKeyButton.querySelector('i');
        icon.classList.toggle('fa-eye', !isPassword);
        icon.classList.toggle('fa-eye-slash', isPassword);
    });
});
