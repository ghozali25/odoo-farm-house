/** @odoo-module **/

import { Component, useState, onMounted, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { session } from "@web/session";

/**
 * FarmUXIntegration - farm user-experience integration component.
 */
export class FarmUXIntegration extends Component {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            workspaceCustomization: {},
            visualIndicators: [],
            accessibilityFeatures: {},
            contextualHelp: [],
            weatherData: null,
            activeTab: 'knowledge',
            showHelpPanel: false,
            currentModel: '',
            currentViewType: '',
            loaded: false
        });

        onWillStart(async () => {
            await this.loadAllCustomizations();
        });

        onMounted(() => {
            this.applyAllCustomizations();
            this.watchDOMChanges();
            this.listenToViewChanges();
        });
    }

    async loadAllCustomizations() {
        // NOTE (porting 19.0 -> 18.0): each source is loaded in its own
        // try/catch so one missing model cannot block the others.
        let customization = session.workspace_customization || {};
        try {
            customization = session.workspace_customization || await this.orm.call(
                'workspace.customization', 'get_user_customization', [[]], { user_id: session.uid }
            );
        } catch (error) {
            console.error('Error loading workspace customization:', error);
        }

        let visualIndicators = [];
        try {
            visualIndicators = await this.orm.searchRead(
                'visual.status.indicator', [['is_active', '=', true]],
                ['id', 'status_type', 'status_value', 'color_code', 'icon', 'badge_style']
            );
        } catch (error) {
            console.error('Error loading visual status indicators:', error);
        }

        // Perbaikan simulasi batch 2 / B5: model 'accessibility.integration'
        // TIDAK ADA di mana pun (hanya disebut di sini + satu test) dan
        // method 'get_accessibility_features' tidak ada di model mana pun —
        // pemanggilan itu 404 di tiap halaman. Model yang benar-benar ada
        // adalah 'accessibility.settings' (models/accessibility_settings.py,
        // tanpa method) — dibaca via searchRead seperti visual indicators
        // di atas. 'accessibility.settings' tidak punya field
        // 'larger_text_size'; nilai itu diturunkan dari font_scaling > 1.
        let accessibilityFeatures = session.accessibility_features || {};
        try {
            if (!session.accessibility_features) {
                const rows = await this.orm.searchRead(
                    'accessibility.settings',
                    [['user_id', '=', session.uid], ['is_active', '=', true]],
                    ['high_contrast_mode', 'screen_reader_enabled', 'reduced_motion', 'font_scaling']
                );
                const row = (rows || [])[0] || {};
                accessibilityFeatures = {
                    high_contrast_mode: row.high_contrast_mode,
                    screen_reader_enabled: row.screen_reader_enabled,
                    reduced_motion: row.reduced_motion,
                    larger_text_size: (row.font_scaling || 1) > 1,
                };
            }
        } catch (error) {
            console.error('Error loading accessibility features:', error);
        }

        Object.assign(this.state, {
            workspaceCustomization: customization || {},
            visualIndicators: visualIndicators || [],
            accessibilityFeatures: accessibilityFeatures || {},
            loaded: true
        });
    }

    applyAllCustomizations() {
        if (!this.state.loaded) return;
        this.applyTheme(this.state.workspaceCustomization.theme);
        this.applyFontSize(this.state.workspaceCustomization.font_size);
        this.applyAccessibilityFeatures(this.state.accessibilityFeatures);
        this.applyVisualStatusIndicatorsToElements();
    }

    applyTheme(theme) {
        if (!theme) return;
        document.body.classList.remove('workspace-theme-dark', 'workspace-theme-eye-care', 'workspace-theme-high-contrast');
        if (theme !== 'light') document.body.classList.add(`workspace-theme-${theme}`);
    }

    applyFontSize(fontSize) {
        if (!fontSize) return;
        document.body.classList.remove('font-size-small', 'font-size-normal', 'font-size-large', 'font-size-extra-large');
        document.body.classList.add(`font-size-${fontSize}`);
    }

    applyAccessibilityFeatures(features) {
        if (!features) return;
        if (features.high_contrast_mode) document.body.classList.add('accessibility-high-contrast');
        if (features.larger_text_size) document.body.classList.add('accessibility-larger-text');
        if (features.reduced_motion) document.body.classList.add('reduce-motion');
        if (features.screen_reader_enabled) this.enableScreenReaderCompatibility();
    }

    /**
     * Listen for view changes to fetch contextual help and weather.
     */
    listenToViewChanges() {
        const self = this;
        // In Odoo, controller changes can be observed;
        // here this is simplified to a periodic check or a toggleHelpPanel trigger.
    }

    /**
     * Load contextual data (help, weather, etc.).
     */
    async loadContextData(model, viewType, resId) {
        if (!model) return;
        // 1. Load contextual help (guarded: 'contextual.help' exists in
        // this module; NOTE its get_contextual_help returns record ids over
        // RPC, so the help panel only receives ids until a search_read-based
        // variant is added upstream).
        try {
            const helpData = await this.orm.call(
                'contextual.help',
                'get_contextual_help',
                [],
                { model_name: model, view_type: viewType }
            );
            this.state.contextualHelp = helpData;
        } catch (error) {
            console.error('Error loading contextual help:', error);
        }

        // 2. Load weather (for intervention or parcel models). Guarded:
        // 'farm.weather.forecast' lives in farm_weather, not in batch 2.
        try {
            if (resId && (model === 'mrp.production' || model === 'project.task' || model === 'stock.location')) {
                const weatherData = await this.orm.call(
                    'farm.weather.forecast',
                    'get_context_weather',
                    [],
                    { res_model: model, res_id: resId }
                );
                this.state.weatherData = weatherData;
            } else {
                this.state.weatherData = null;
            }
        } catch (error) {
            console.error('Error loading weather context:', error);
            this.state.weatherData = null;
        }

        this.state.currentModel = model;
        this.state.currentViewType = viewType;
    }

    toggleHelpPanel() {
        this.state.showHelpPanel = !this.state.showHelpPanel;
        if (this.state.showHelpPanel) {
            // Get the model info from the current controller
            const controller = this.action.currentController;
            if (controller && controller.props.resModel) {
                this.loadContextData(
                    controller.props.resModel, 
                    controller.props.type || 'form',
                    controller.props.resId
                );
            }
        }
    }

    /**
     * Voice control integration [US-16-07]
     */
    startVoiceControl() {
        if (!('webkitSpeechRecognition' in window)) {
            console.warn('Speech recognition not supported');
            return;
        }

        const recognition = new window.webkitSpeechRecognition();
        recognition.lang = navigator.language || 'en-US';
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onresult = (event) => {
            const command = event.results[0][0].transcript;
            this.processVoiceCommand(command);
        };

        recognition.start();
    }

    processVoiceCommand(command) {
        console.log('Voice Command received:', command);
        const lower = command.toLowerCase();
        if (lower.includes('start') || lower.includes('begin')) {
            const btn = document.querySelector('.o_agri_action_buttons .btn-success');
            if (btn) btn.click();
        } else if (lower.includes('stop') || lower.includes('end')) {
            const btn = document.querySelector('.o_agri_action_buttons .btn-warning');
            if (btn) btn.click();
        } else if (lower.includes('finish') || lower.includes('done') || lower.includes('save')) {
            const btn = document.querySelector('.o_form_button_save, .o_agri_action_buttons .btn-primary');
            if (btn) btn.click();
        }
    }



    enableScreenReaderCompatibility() {
        const elements = document.querySelectorAll('button, a, input, select, textarea');
        elements.forEach(el => {
            if (!el.getAttribute('aria-label') && !el.title) {
                const text = el.textContent.trim() || el.value || el.placeholder || '';
                if (text) el.setAttribute('aria-label', text);
            }
        });
    }

    applyVisualStatusIndicatorsToElements() {
        if (!this.state.visualIndicators || this.state.visualIndicators.length === 0) return;
        this.state.visualIndicators.forEach(indicator => {
            const selector = `[data-status-type="${indicator.status_type}"][data-status-value="${indicator.status_value}"]`;
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                if (el.querySelector(`.visual-status-indicator[data-id="${indicator.id}"]`)) return;
                const indicatorEl = document.createElement('span');
                indicatorEl.className = `visual-status-indicator badge rounded-pill bg-${indicator.badge_style || 'secondary'} ms-1`;
                indicatorEl.dataset.id = indicator.id;
                if (indicator.color_code) indicatorEl.style.backgroundColor = indicator.color_code;
                if (indicator.icon) {
                    const iconEl = document.createElement('i');
                    iconEl.className = indicator.icon;
                    indicatorEl.appendChild(iconEl);
                }
                el.appendChild(indicatorEl);
            });
        });
    }

    watchDOMChanges() {
        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    setTimeout(() => {
                        this.applyVisualStatusIndicatorsToElements();
                    }, 100);
                }
            });
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    static template = 'FarmUXIntegration';
}

registry.category("main_components").add("FarmUXIntegration", { Component: FarmUXIntegration });
