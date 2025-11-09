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
});
function copyToClipboard(element) {
    const text = element.getAttribute('data-url');
    navigator.clipboard.writeText(text).then(() => {
        const feedback = element.nextElementSibling;
        if(feedback) {
            feedback.textContent = "{% trans 'Kopiert' %}";
            feedback.classList.add('visible');
            setTimeout(() => {
                feedback.textContent = '';
                feedback.classList.remove('visible');
            }, 2000);
        }
    });
}
