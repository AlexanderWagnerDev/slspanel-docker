'use strict';

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'static', 'js', 'scripts.js'), 'utf8');

function createClipboardContext({ clipboard, execResult = true } = {}) {
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
    };
    const execCalls = [];
    const document = {
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
            removeChild(element) {
                assert.equal(element, textArea);
            },
        },
        execCommand(command) {
            execCalls.push(command);
            return execResult;
        },
    };
    const window = {
        translations: {
            copiedText: 'Copied',
            copyError: 'Copy failed',
        },
    };
    const navigatorObject = clipboard === undefined ? {} : { clipboard };
    const context = vm.createContext({
        window,
        document,
        navigator: navigatorObject,
        setTimeout() {},
        console,
        Uint8Array,
        Array,
        String,
        Math,
    });

    vm.runInContext(source, context);

    return {
        context,
        button,
        feedback,
        execCalls,
    };
}

test('copyToClipboard falls back to execCommand when the Clipboard API is unavailable', async () => {
    const fixture = createClipboardContext();

    await fixture.context.copyToClipboard(fixture.button);

    assert.deepEqual(fixture.execCalls, ['copy']);
    assert.equal(fixture.feedback.textContent, 'Copied');
});

test('copyToClipboard shows an error when the fallback also fails', async () => {
    const fixture = createClipboardContext({ execResult: false });

    await fixture.context.copyToClipboard(fixture.button);

    assert.deepEqual(fixture.execCalls, ['copy']);
    assert.equal(fixture.feedback.textContent, 'Copy failed');
});

test('copyToClipboard uses the Clipboard API when it is available', async () => {
    let written;
    const fixture = createClipboardContext({
        clipboard: {
            async writeText(value) {
                written = value;
            },
        },
    });

    await fixture.context.copyToClipboard(fixture.button);

    assert.equal(written, 'srt://example.test:4000?streamid=play');
    assert.deepEqual(fixture.execCalls, []);
    assert.equal(fixture.feedback.textContent, 'Copied');
});

test('loadStats encodes player keys in the request path', () => {
    const requests = [];
    const container = { innerHTML: '' };
    const document = {
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
    const fetch = async (url) => {
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
    };
    const context = vm.createContext({
        window: {
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
        },
        document,
        navigator: {},
        setTimeout() {},
        fetch,
        console,
        Uint8Array,
        Array,
        String,
        Math,
        encodeURIComponent,
    });

    vm.runInContext(source, context);
    context.loadStats('../logout');

    assert.deepEqual(requests, ['/en/sls-stats/..%2Flogout/']);
});
