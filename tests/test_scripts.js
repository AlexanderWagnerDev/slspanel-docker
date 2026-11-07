'use strict';

const test = require('node:test');
const assert = require('node:assert');
const path = require('node:path');

const scriptPath = path.join(__dirname, '..', 'static', 'js', 'scripts.js');

// The browser script registers a DOMContentLoaded listener at load time and
// resolves document/window/navigator at call time. Provide inert defaults for
// the initial load; each test replaces them with its own fixture.
global.window = { translations: {} };
global.document = {
    addEventListener() {},
    documentElement: { lang: 'en' },
    getElementById() { return null; },
    querySelectorAll() { return []; },
    createElement() { return null; },
    body: { appendChild() {}, removeChild() {} },
    execCommand() { return false; },
};
Object.defineProperty(globalThis, 'navigator', {
    configurable: true,
    writable: true,
    value: {},
});

const { copyToClipboard, loadStats } = require(scriptPath);

function setNavigator(value) {
    Object.defineProperty(globalThis, 'navigator', {
        configurable: true,
        writable: true,
        value,
    });
}

function createClipboardFixture({ clipboard, execResult = true } = {}) {
    const feedback = {
        textContent: '',
        classList: {
            add() {},
            remove() {},
        },
    };
    const button = {
        dataset: { url: 'srt://example.test:4000?streamid=play' },
        nextElementSibling: feedback,
    };
    const textArea = {
        value: '',
        style: {},
        focus() {},
        select() {},
        remove() {},
    };
    const execCalls = [];
    global.window = {
        translations: {
            copiedText: 'Copied',
            copyError: 'Copy failed',
        },
    };
    global.document = {
        documentElement: { lang: 'en' },
        addEventListener() {},
        getElementById() { return null; },
        querySelectorAll() { return []; },
        createElement(tag) {
            assert.equal(tag, 'textarea');
            return textArea;
        },
        body: {
            appendChild(element) {
                assert.equal(element, textArea);
            },
            removeChild() {},
        },
        execCommand(command) {
            execCalls.push(command);
            return execResult;
        },
    };
    setNavigator(clipboard === undefined ? {} : { clipboard });

    return { button, feedback, execCalls, textArea };
}

async function runWithoutTimers(callback) {
    const originalSetTimeout = global.setTimeout;
    global.setTimeout = () => 0;
    try {
        return await callback();
    } finally {
        global.setTimeout = originalSetTimeout;
    }
}

test('copyToClipboard falls back to execCommand when the Clipboard API is unavailable', async () => {
    const fixture = createClipboardFixture();

    await runWithoutTimers(() => copyToClipboard(fixture.button));

    assert.deepEqual(fixture.execCalls, ['copy']);
    assert.equal(fixture.feedback.textContent, 'Copied');
});

test('copyToClipboard shows an error when the fallback also fails', async () => {
    const fixture = createClipboardFixture({ execResult: false });

    await runWithoutTimers(() => copyToClipboard(fixture.button));

    assert.deepEqual(fixture.execCalls, ['copy']);
    assert.equal(fixture.feedback.textContent, 'Copy failed');
});

test('copyToClipboard uses the Clipboard API when it is available', async () => {
    let written;
    const fixture = createClipboardFixture({
        clipboard: {
            async writeText(value) {
                written = value;
            },
        },
    });

    await runWithoutTimers(() => copyToClipboard(fixture.button));

    assert.equal(written, 'srt://example.test:4000?streamid=play');
    assert.deepEqual(fixture.execCalls, []);
    assert.equal(fixture.feedback.textContent, 'Copied');
});

test('loadStats encodes player keys in the request path', () => {
    const requests = [];
    const container = { innerHTML: '' };
    global.document = {
        documentElement: { lang: 'en' },
        addEventListener() {},
        getElementById(id) {
            return id === 'stats-../logout' ? container : null;
        },
        querySelectorAll() { return []; },
        createElement() { return {}; },
        body: { appendChild() {}, removeChild() {} },
        execCommand() { return true; },
    };
    global.window = {
        translations: {
            copiedText: 'Copied',
            copyError: 'Copy failed',
            streamStatistics: 'Stream Statistics',
            bitrate: 'Bitrate',
            latency: 'Latency',
            rtt: 'RTT',
            buffer: 'Buffer',
            droppedPackets: 'Dropped packets',
            uptime: 'Uptime',
            status: 'Status',
            statsNotAvailable: 'Stats not available',
        },
    };
    Object.defineProperty(globalThis, 'fetch', {
        configurable: true,
        writable: true,
        value: async (url) => {
            requests.push(url);
            return {
                ok: true,
                async json() {
                    return {
                        publisher: {
                            bitrate: 1,
                            buffer: 0,
                            dropped_pkts: 0,
                            latency: 0,
                            rtt: 1.5,
                            uptime: 10,
                        },
                        status: 'ok',
                    };
                },
            };
        },
    });

    loadStats('../logout');

    assert.deepEqual(requests, ['/en/sls-stats/..%2Flogout/']);
});
