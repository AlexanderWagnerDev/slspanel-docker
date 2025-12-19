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
        console.warn('Clipboard API failed, using fallback:', err);
        copyToClipboardFallback(text, element);
    }
}
function copyToClipboardFallback(text, element) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.top = '0';
    textArea.style.left = '0';
    textArea.style.width = '2em';
    textArea.style.height = '2em';
    textArea.style.padding = '0';
    textArea.style.border = 'none';
    textArea.style.outline = 'none';
    textArea.style.boxShadow = 'none';
    textArea.style.background = 'transparent';
    textArea.style.opacity = '0';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showCopyFeedback(element);
        } else {
            console.error('Fallback: Copy command was unsuccessful');
            showCopyError(element);
        }
    } catch (err) {
        console.error('Fallback: Unable to copy', err);
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
        console.error('Stats container not found for:', playerKey);
        return;
    }
    const langCode = document.documentElement.lang
    const url = `/${langCode}/sls-stats/${playerKey}/`;
    console.log('Fetching stats from:', url);
    
    fetch(url)
        .then(response => {
            console.log('Response status:', response.status);
            console.log('Response ok:', response.ok);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Stats data received:', data);
            
            if (data.error) {
                statsContainer.innerHTML = `<p class="text-danger">${data.error}</p>`;
                return;
            }
            
            const publisher = data.publisher || {};
            
            console.log('Publisher data:', publisher);
            
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
                    <h6 class="mb-2">${translations.streamStatistics || 'Stream Statistics'}</h6>
                    <div class="row g-2">
                        <div class="col-md-4 col-6">
                            <small class="text-muted">${translations.bitrate || 'Bitrate'}:</small><br>
                            <strong>${bitrate} kbps</strong>
                        </div>
                        <div class="col-md-4 col-6">
                            <small class="text-muted">${translations.latency || 'Latency'}:</small><br>
                            <strong>${latency} ms</strong>
                        </div>
                        <div class="col-md-4 col-6">
                            <small class="text-muted">${translations.rtt || 'RTT'}:</small><br>
                            <strong>${rtt} ms</strong>
                        </div>
                        <div class="col-md-4 col-6">
                            <small class="text-muted">${translations.buffer || 'Buffer'}:</small><br>
                            <strong>${buffer} ms</strong>
                        </div>
                        <div class="col-md-4 col-6">
                            <small class="text-muted">${translations.droppedPackets || 'Dropped Packets'}:</small><br>
                            <strong class="${droppedPkts > 0 ? 'text-warning' : ''}">${droppedPkts}</strong>
                        </div>
                        <div class="col-md-4 col-6">
                            <small class="text-muted">${translations.uptime || 'Uptime'}:</small><br>
                            <strong>${uptime}</strong>
                        </div>
                        <div class="col-12 mt-1">
                            <small class="text-muted">${translations.status || 'Status'}:</small>
                            <span class="${statusClass} fw-bold"> ${status.toUpperCase()}</span>
                        </div>
                    </div>
                </div>
            `;
        })
        .catch(error => {
            console.error('Error fetching stats:', error);
            statsContainer.innerHTML = `
                <p class="text-danger">
                    <small>Error: ${error.message}</small>
                </p>
            `;
        });
}
function formatUptime(seconds) {
    if (!seconds) return '00:00:00';
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    if (days > 0) {
        return `${days}d ${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    } else {
        return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }
}


