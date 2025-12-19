function generateKey(prefix, bytes) {
    const arr = new Uint8Array(bytes);
    window.crypto.getRandomValues(arr);
    return prefix + Array.from(arr).map(b => b.toString(16).padStart(2, '0')).join('');
}
document.addEventListener('DOMContentLoaded', function(){
    const publisherInput = document.getElementById('publisher');
    const playerInput = document.getElementById('player');
    if (publisherInput && !publisherInput.value) {
        publisherInput.value = generateKey('live_', 16);
    }
    if (playerInput && !playerInput.value) {
        playerInput.value = generateKey('play_', 16);
    }
    initializeStats();
});
async function copyToClipboard(element) {
    const text = element.getAttribute('data-url');
    try {
        await navigator.clipboard.writeText(text);
        showCopyFeedback(element);
    } catch (err) {
        copyToClipboardFallback(text, element);
    }
}
function copyToClipboardFallback(text, element) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.cssText = 'position:fixed;top:0;left:0;width:2em;height:2em;padding:0;border:none;outline:none;box-shadow:none;background:transparent;opacity:0;';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showCopyFeedback(element);
        } else {
            showCopyError(element);
        }
    } catch (err) {
        showCopyError(element);
    } finally {
        document.body.removeChild(textArea);
    }
}
function showCopyFeedback(element) {
    const feedback = element.nextElementSibling;
    if(feedback) {
        feedback.textContent = window.translations.copiedText;
        feedback.classList.add('visible');
        setTimeout(() => {
            feedback.textContent = '';
            feedback.classList.remove('visible');
        }, 2000);
    }
}
function showCopyError(element) {
    const feedback = element.nextElementSibling;
    if(feedback) {
        feedback.textContent = window.translations.copyError;
        feedback.classList.add('visible', 'text-danger');
        setTimeout(() => {
            feedback.textContent = '';
            feedback.classList.remove('visible', 'text-danger');
        }, 2000);
    }
}
function initializeStats() {
    const statsContainers = document.querySelectorAll('[id^="stats-"]');
    if (statsContainers.length === 0) {
        return;
    }
    statsContainers.forEach(container => {
        const playerKey = container.dataset.playerKey;
        if (playerKey) {
            loadStats(playerKey);
        }
    });
    setInterval(() => {
        statsContainers.forEach(container => {
            const playerKey = container.dataset.playerKey;
            if (playerKey) {
                loadStats(playerKey);
            }
        });
    }, 1000);
}
function loadStats(playerKey) {
    const statsContainer = document.getElementById(`stats-${playerKey}`);
    if (!statsContainer) {
        return;
    }
    const langCode = document.documentElement.lang || 'en';
    const url = `/${langCode}/sls-stats/${playerKey}/`;
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                statsContainer.innerHTML = `<p class="text-danger">${data.error}</p>`;
                return;
            }
            const publisher = data.publisher || {};
            const bitrate = publisher.bitrate || 0;
            const buffer = publisher.buffer || 0;
            const droppedPkts = publisher.dropped_pkts || 0;
            const latency = publisher.latency || 0;
            const rtt = publisher.rtt ? publisher.rtt.toFixed(2) : '0.00';
            const uptime = formatUptime(publisher.uptime || 0);
            const status = data.status || 'unknown';
            const statusClass = status === 'ok' ? 'text-success' : 'text-warning';
            const translations = window.translations || {};
            statsContainer.innerHTML = `
                <div class="mt-2 p-2 bg-dark bg-opacity-50 rounded">
                    <h6 class="mb-2">${translations.streamStatistics}</h6>
                    <div class="row g-2">
                        <div class="col-md-4 col-6">
                            <p>${translations.bitrate}:</p>
                            <strong>${bitrate} kbps</strong>
                        </div>
                        <div class="col-md-4 col-6">
                            <p>${translations.latency}:</p>
                            <strong>${latency} ms</strong>
                        </div>
                        <div class="col-md-4 col-6">
                            <p>${translations.rtt}:</p>
                            <strong>${rtt} ms</strong>
                        </div>
                        <div class="col-md-4 col-6">
                            <p>${translations.buffer}:</p>
                            <strong>${buffer} ms</strong>
                        </div>
                        <div class="col-md-4 col-6">
                            <p>${translations.droppedPackets}:</p>
                            <strong class="${droppedPkts > 0 ? 'text-warning' : ''}">${droppedPkts}</strong>
                        </div>
                        <div class="col-md-4 col-6">
                            <p>${translations.uptime}:</p>
                            <strong>${uptime}</strong>
                        </div>
                        <div class="col-12 mt-2">
                            <p>${translations.status}:</p>
                            <span class="${statusClass} fw-bold"> ${status.toUpperCase()}</span>
                        </div>
                    </div>
                </div>
            `;
        })
        .catch(error => {
            statsContainer.innerHTML = `<p><em>${window.translations.statsNotAvailable}</em></p>`;
        });
}
function formatUptime(seconds) {
    if (!seconds) return '00:00:00';
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    const time = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    return days > 0 ? `${days}d ${time}` : time;
}