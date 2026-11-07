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

function createClipboardFixture({ clipboard, textAreaError = false } = {}) {
    const inserted = [];
    const textAreas = [];
    let currentField = null;
    const feedback = {
        textContent: '',
        classList: {
            add() {},
            remove() {},
            contains(name) {
                return name === 'copy-feedback';
            },
        },
        get nextElementSibling() {
            return currentField;
        },
        after(element) {
            currentField = element;
            inserted.push({ position: 'after', element });
        },
    };
    const button = {
        dataset: { url: 'srt://example.test:4000?streamid=play' },
        nextElementSibling: feedback,
        after(element) {
            inserted.push({ position: 'after', element });
        },
    };
    function createTextArea() {
        const textArea = {
            value: '',
            className: '',
            attributes: {},
            focused: false,
            selected: false,
            removed: false,
            classList: {
                contains(name) {
                    return textArea.className.split(/\s+/).includes(name);
                },
            },
            setAttribute(name, value) {
                this.attributes[name] = value;
            },
            focus() {
                this.focused = true;
            },
            select() {
                this.selected = true;
            },
            remove() {
                this.removed = true;
                if (currentField === this) currentField = null;
            },
        };
        textAreas.push(textArea);
        return textArea;
    }
    global.window = {
        translations: {
            copiedText: 'Copied',
            copyManual: 'Copy manually (Ctrl+C)',
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
            if (textAreaError) throw new Error('textarea unavailable');
            return createTextArea();
        },
    };
    setNavigator(clipboard === undefined ? {} : { clipboard });

    return { button, feedback, inserted, textAreas };
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

test('copyToClipboard shows a manual copy field when the Clipboard API is unavailable', async () => {
    const fixture = createClipboardFixture();

    await runWithoutTimers(() => copyToClipboard(fixture.button));

    const field = fixture.textAreas[0];
    assert.equal(fixture.inserted.length, 1);
    assert.equal(fixture.inserted[0].position, 'after');
    assert.equal(fixture.inserted[0].element, field);
    assert.equal(field.value, 'srt://example.test:4000?streamid=play');
    assert.equal(field.attributes.readonly, '');
    assert.equal(field.className, 'manual-copy-field');
    assert.equal(field.focused, true);
    assert.equal(field.selected, true);
    assert.equal(fixture.feedback.textContent, 'Copy manually (Ctrl+C)');
});

test('copyToClipboard replaces an existing manual copy field', async () => {
    const fixture = createClipboardFixture();

    await runWithoutTimers(() => copyToClipboard(fixture.button));
    await runWithoutTimers(() => copyToClipboard(fixture.button));

    assert.equal(fixture.textAreas.length, 2);
    assert.equal(fixture.textAreas[0].removed, true);
    assert.equal(fixture.textAreas[1].removed, false);
    assert.equal(fixture.feedback.nextElementSibling, fixture.textAreas[1]);
});

test('copyToClipboard shows an error when the manual field cannot be created', async () => {
    const fixture = createClipboardFixture({ textAreaError: true });

    await runWithoutTimers(() => copyToClipboard(fixture.button));

    assert.equal(fixture.inserted.length, 0);
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
    assert.equal(fixture.inserted.length, 0);
    assert.equal(fixture.textAreas.length, 0);
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
