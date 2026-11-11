/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class AgriGatingAudit extends Component {
    static template = "farm_ux.AgriGatingAudit";
    
    get weatherInfo() {
        const status = this.props.record.data.weather_gating_status;
        const config = {
            'safe': { icon: 'fa-sun-o', class: 'text-success', text: 'Safe' },
            'warning': { icon: 'fa-cloud', class: 'text-warning', text: 'Caution' },
            'blocked': { icon: 'fa-umbrella', class: 'text-danger', text: 'Blocked' },
            'none': { icon: 'fa-minus', class: 'text-muted', text: 'N/A' }
        };
        return config[status] || config['none'];
    }

    get complianceInfo() {
        const status = this.props.record.data.compliance_gating_status;
        const config = {
            'compliant': { icon: 'fa-shield', class: 'text-success', text: 'Compliant' },
            'warning': { icon: 'fa-exclamation-triangle', class: 'text-warning', text: 'Warning' },
            'blocked': { icon: 'fa-ban', class: 'text-danger', text: 'Violation' },
            'none': { icon: 'fa-circle-o-notch', class: 'text-muted', text: 'Pending' }
        };
        return config[status] || config['none'];
    }

    get iotInfo() {
        const status = this.props.record.data.iot_status;
        const config = {
            'connected': { icon: 'fa-wifi', class: 'text-success', text: 'Connected' },
            'offline': { icon: 'fa-times-circle', class: 'text-warning', text: 'Offline' },
            'critical': { icon: 'fa-bolt', class: 'text-danger', text: 'Alert' },
            'none': { icon: 'fa-power-off', class: 'text-muted', text: 'No Sensors' }
        };
        return config[status] || config['none'];
    }
}

export const agriGatingAudit = {
    // NOTE (Odoo 18, perbaikan simulasi batch 2 / B1): NO extractProps here.
    // Widget.widgetProps (web/.../views/widgets/widget.js) already passes
    // `record` by default; `additionalProps` is an Odoo 19-only registry key
    // and fails 18 debug-mode schema validation ("unknown key").
    component: AgriGatingAudit,
    // Cacat laten kelas yang sama dengan B8 (spatial gauge, 10 Nov 2026):
    // ketiga field ini TIDAK ada di arch view mana pun yang memakai widget
    // ini (form mrp.production maupun form agri.intervention.test), jadi
    // record.data ketiganya = undefined dan getter selalu jatuh ke fallback
    // config['none'] (WEATHER N/A, COMPLIANCE Pending, IOT No Sensors).
    // Hari ini tampilannya kebetulan benar karena itu juga nilai default
    // server ('none'/'none'; iot_status MO = 'normal' yang juga tidak ada
    // di config widget) — tapi begitu plugin cuaca/kepatuhan menulis nilai
    // nyata ('safe'/'blocked'/...), widget tetap menampilkan N/A. Karena
    // itu ketiga field dimuat via fieldDependencies (mekanisme Odoo 18,
    // lih. week_days core + relational_model/utils.js). Tampilan saat ini
    // TIDAK berubah; yang berubah hanya: nilai server nyata kini terbaca.
    // Catatan: iot_status di mrp.production adalah versi mixin
    // (normal/monitoring/warning/critical), bukan versi base
    // (connected/offline/critical/none) yang dipakai config widget —
    // 'critical' tetap tampil Alert, sisanya fallback No Sensors.
    fieldDependencies: [
        { name: "weather_gating_status", type: "selection" },
        { name: "compliance_gating_status", type: "selection" },
        { name: "iot_status", type: "selection" },
    ],
};

registry.category("view_widgets").add("agri_gating_audit", agriGatingAudit);
