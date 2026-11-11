/** @odoo-module **/

import { Component, useState, onMounted, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

/**
 * TermMappingHandler - term mapping handler component.
 *
 * This component dynamically replaces terms in the front end,
 * swapping industrial terms for agricultural ones.
 */
export class TermMappingHandler extends Component {
    /**
     * Component setup.
     */
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.state = useState({
            termMappings: [],
            loaded: false
        });
        // Perbaikan simulasi batch 2 / B2: guard anti-loop (lihat
        // loadTermMappings + replaceTextInDOM + watchDOMChanges).
        // _processedText: WeakMap<Text, string> — nilai teks yang sudah
        // diproses untuk node itu; node dilewati bila nilainya tidak berubah.
        this._processedText = new WeakMap();
        // Regex gabungan sekali-pass + lookup, dibangun di loadTermMappings.
        this._mappingRegex = null;
        this._mappingBySource = {};
        this._observer = null;

        onWillStart(async () => {
            await this.loadTermMappings();
        });
        
        onMounted(() => {
            if (this.state.loaded) {
                this.applyTermMappingsToPage();
                this.watchDOMChanges();
            }
        });
    }

    /**
     * Load term mappings.
     *
     * Perbaikan simulasi batch 2 / B2: mapping yang target-nya mengandung
     * kembali source-nya (case-insensitive) DIBUANG di sini — kalau tidak,
     * teks hasil replace masih mengandung source sehingga pass berikutnya
     * memanjangkannya lagi tanpa henti ("Grape Grape Grape...").
     * Yang dibuang dari data batch 2: Processing -> Food Processing,
     * Baking -> Baking Process, Fermentation -> Fermentation Process,
     * Crushing -> Grape Crushing, Task -> Farm Task, plus mapping
     * identitas (Seed -> Seed, Fertilizer -> Fertilizer, dst. — no-op).
     * Mapping MO -> AI tetap nonaktif di data, tidak disentuh.
     * Sisa rantai antar-mapping (mis. Manufacturing Order ->
     * Agricultural Intervention, lalu Intervention -> Farm Operation)
     * dibatasi oleh regex sekali-pass di replaceTextInDOM: tiap pass
     * konvergen dalam <= 2 pass, tidak pernah memanjang tanpa batas.
     */
    async loadTermMappings() {
        try {
            // Fetch term mappings from the backend
            const termMappings = await this.orm.searchRead(
                'term.mapping',
                [['is_active', '=', true]],
                ['source_term', 'target_term']
            );

            const usable = [];
            const skipped = [];
            for (const mapping of termMappings || []) {
                if (!mapping.source_term || !mapping.target_term) {
                    continue;
                }
                if (mapping.target_term.toLowerCase().includes(mapping.source_term.toLowerCase())) {
                    skipped.push(`${mapping.source_term} -> ${mapping.target_term}`);
                } else {
                    usable.push(mapping);
                }
            }
            if (skipped.length > 0) {
                console.warn(
                    'TermMappingHandler: skipped self-containing mappings ' +
                    '(target contains source, would re-apply forever):',
                    skipped
                );
            }

            this.state.termMappings = usable;
            this.state.loaded = true;

            // Satu regex gabungan, source terpanjang dulu: String.replace
            // dengan regex ini hanya SATU pass atas teks asli — teks hasil
            // replace tidak pernah di-scan ulang di dalam pass yang sama,
            // jadi mapping berantai tidak berlipat dalam satu pass.
            const sorted = [...usable].sort((a, b) =>
                (b.source_term || "").length - (a.source_term || "").length
            );
            this._mappingBySource = {};
            for (const mapping of sorted) {
                this._mappingBySource[mapping.source_term.toLowerCase()] = mapping.target_term;
            }
            this._mappingRegex = sorted.length > 0
                ? new RegExp(sorted.map(m => this.escapeRegExp(m.source_term)).join("|"), "gi")
                : null;

            if (this.state.termMappings.length > 0) {
                this.applyTermMappingsToPage();
                this.watchDOMChanges();
            }
        } catch (error) {
            console.error('Error loading term mappings:', error);
        }
    }

    /**
     * Apply term mappings to the page.
     */
    applyTermMappingsToPage() {
        if (!this.state.termMappings || this.state.termMappings.length === 0) {
            return;
        }

        // Replace text nodes on the page
        this.replaceTextInDOM(document.body);
    }

    /**
     * Replace text inside a DOM element.
     *
     * Perbaikan simulasi batch 2 / B2: SATU pass regex gabungan per text
     * node (teks hasil replace tidak di-scan ulang) + node yang nilainya
     * sudah diproses dilewati (WeakMap nilai-terakhir). Gabungan keduanya
     * menghentikan pemanjangan berulang; fitur term-mapping tetap jalan.
     * @param {HTMLElement} element - DOM element
     */
    replaceTextInDOM(element) {
        if (!this.state.termMappings || this.state.termMappings.length === 0) {
            return;
        }
        if (!this._mappingRegex) {
            return;
        }

        const walker = document.createTreeWalker(
            element,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );

        const textNodes = [];
        let node;
        while (node = walker.nextNode()) {
            if (node.parentElement &&
                !['SCRIPT', 'STYLE', 'TEXTAREA', 'INPUT'].includes(node.parentElement.tagName) &&
                node.nodeValue.trim() !== '') {
                textNodes.push(node);
            }
        }

        textNodes.forEach(textNode => {
            // Jangan proses ulang node yang nilainya tidak berubah sejak
            // pass terakhir (melindungi dari re-render / observer re-fire).
            if (this._processedText.get(textNode) === textNode.nodeValue) {
                return;
            }
            const newText = textNode.nodeValue.replace(
                this._mappingRegex,
                (match) => this._mappingBySource[match.toLowerCase()]
            );
            if (newText !== textNode.nodeValue) {
                textNode.nodeValue = newText;
            }
            this._processedText.set(textNode, textNode.nodeValue);
        });
    }

    /**
     * Escape regex special characters.
     * @param {string} string - string to escape
     * @returns {string} escaped string
     */
    escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\\]/g, '\\$&');
    }

    /**
     * Watch DOM changes.
     *
     * Perbaikan simulasi batch 2 / B2: observer DIPUTUS selama replace
     * (disconnect -> proses sinkron -> observe lagi) supaya mutasi yang
     * dipicu pemrosesan sendiri tidak memicu ulang handler; setTimeout(0)
     * dihapus agar pemrosesan terjadi di dalam jendela disconnect itu.
     */
    watchDOMChanges() {
        if (!this.state.termMappings || this.state.termMappings.length === 0) {
            return;
        }
        if (this._observer) {
            return;
        }

        const observer = new MutationObserver(mutations => {
            // Putuskan observer selama replace agar mutasi sendiri tidak
            // memicu ulang; sambung lagi sesudahnya (finally).
            observer.disconnect();
            try {
                mutations.forEach(mutation => {
                    if (mutation.type === 'childList') {
                        mutation.addedNodes.forEach(node => {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                this.replaceTextInDOM(node);
                            } else if (node.nodeType === Node.TEXT_NODE) {
                                const parentElement = node.parentElement;
                                if (parentElement &&
                                    !['SCRIPT', 'STYLE', 'TEXTAREA', 'INPUT'].includes(parentElement.tagName)) {
                                    this.replaceTextInDOM(parentElement);
                                }
                            }
                        });
                    }
                });
            } finally {
                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });
            }
        });

        this._observer = observer;
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    static template = 'TermMappingHandler';
}

registry.category("main_components").add("TermMappingHandler", { Component: TermMappingHandler });
