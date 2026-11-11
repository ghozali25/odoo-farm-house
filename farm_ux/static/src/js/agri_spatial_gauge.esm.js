/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class AgriSpatialGauge extends Component {
    // Perbaikan simulasi batch 2 / B3: template XML "AgriSpatialGauge" ada
    // (static/src/xml/agri_spatial_gauge.xml) tapi class ini tidak pernah
    // mendeklarasikannya -> OwlError "Missing template: ''" saat mount.
    static template = "AgriSpatialGauge";

    get strokeDasharray() {
        const rate = this.props.record.data.spatial_compliance_rate || 0;
        return `${rate}, 100`;
    }

    get gaugeColor() {
        const rate = this.props.record.data.spatial_compliance_rate || 0;
        if (rate >= 95) return "#27ae60"; // Green
        if (rate >= 80) return "#f39c12"; // Orange
        return "#e74c3c"; // Red
    }
}

export const agriSpatialGauge = {
    // NOTE (Odoo 18, perbaikan simulasi batch 2 / B1): NO extractProps here.
    // Widget.widgetProps (web/.../views/widgets/widget.js) already passes
    // `record` by default; `additionalProps` is an Odoo 19-only registry key
    // and fails 18 debug-mode schema validation ("unknown key").
    component: AgriSpatialGauge,
    // B8 (simulasi ulang batch 2, 10 Nov 2026): gauge tampil NaN% merah +
    // "OOB Points" padahal server benar (MO 23: spatial_compliance_rate =
    // 100.0, out_of_bounds_count = 0). Akar: record.data HANYA berisi field
    // yang ada di arch view — kedua field ini TIDAK ada di form MO
    // (farm_operation/views/agri_intervention_views.xml) sehingga
    // `data.spatial_compliance_rate` = undefined -> Math.round(undefined)
    // = NaN, dan `out_of_bounds_count === 0` = false -> cabang OOB.
    // fieldDependencies di registry item (bukan di Component) adalah cara
    // Odoo 18 memuat field tambahan untuk widget: relational_model/utils.js
    // `extractFieldsFromArchInfo` membaca `widgetInfo.widget.fieldDependencies`
    // dan menambahkannya ke activeFields/read (lih. week_days core).
    // Alternatif "tambah field ke arch view" ditolak: field itu milik
    // farm_operation, view MO bukan milik farm_ux, dan fieldDependencies
    // adalah mekanisme yang memang disediakan untuk kasus ini.
    fieldDependencies: [
        { name: "spatial_compliance_rate", type: "float" },
        { name: "out_of_bounds_count", type: "integer" },
    ],
};

registry.category("view_widgets").add("agri_spatial_gauge", agriSpatialGauge);
