/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class AgriDnaIntegrity extends Component {
    static template = "farm_ux.AgriDnaIntegrity";
    
    get score() {
        return Math.round(this.props.record.data.dna_integrity_score || 0);
    }

    get scoreColor() {
        if (this.score >= 90) return '#27ae60'; // Green
        if (this.score >= 70) return '#f1c40f'; // Yellow
        return '#e74c3c'; // Red
    }

    get statusText() {
        if (this.score >= 90) return 'PRISTINE DNA';
        if (this.score >= 70) return 'VERIFIED';
        return 'TAINTED / AT RISK';
    }

    get dashArray() {
        const percentage = this.score;
        return `${percentage}, 100`;
    }
}

export const agriDnaIntegrity = {
    // NOTE (Odoo 18, perbaikan simulasi batch 2 / B1): NO extractProps here.
    // Widget.widgetProps (web/.../views/widgets/widget.js) already passes
    // `record` by default; `additionalProps` is an Odoo 19-only registry key
    // and fails 18 debug-mode schema validation ("unknown key").
    component: AgriDnaIntegrity,
};

registry.category("view_widgets").add("agri_dna_integrity", agriDnaIntegrity);
