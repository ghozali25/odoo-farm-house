# Porting odoo-farm (jeffery9) 19.0 → Odoo 18

- **Sumber:** `jeffery9/odoo-farm`, branch 19.0, commit `aaa0ab6` (19 Agu 2026).
  Clone kajian (JANGAN diubah): `~/workspace/odoo-farm-eval/odoo-farm`.
  Folder kerja porting: `~/workspace/odoo-farm-port-18/` (salinan repo, tanpa `.git`).
- **Perintah king:** 9 Nov 2026 21:30 WIB ("kamu porting agar bisa di odoo18").
  Menggantikan jalur desain-dari-nol; dokumen desain
  `~/workspace/agri-design-18/DESAIN-MODUL-PERTANIAN-ODOO18.md` tetap sebagai referensi.
- **Tambahan king 9 Nov 21:33 WIB:** port harus bisa disesuaikan Indonesia/universal
  (de-China-ize, lihat §6).
- **Lisensi: AGPL-3 TETAP.** Porting kode AGPL-3 — jangan ganti lisensi ke LGPL-3
  atau lainnya. Jangan ubah logika bisnis inti; yang diubah hanya yang diperlukan
  agar jalan di Odoo 18 + adaptasi Indonesia/universal (§6).
- **Test bed:** Odoo 18 di `~/workspace/odoo18-test/`, DB `test18`, PG port 5433,
  HTTP `http://127.0.0.1:8071`. Login admin/admin. Uji browser wajib `?debug=1`.

## 1. Alat migrasi — keterbatasan yang ditemukan

Aturan tetap king: porting WAJIB diawali `odoo-module-migrator` + `oca-port`.
Hasil pengecekan 9 Nov 2026:

- `odoo-module-migrator` 0.5.0 terpasang di sandbox (`~/.local/bin/odoo-module-migrate`),
  TAPI **tidak mendukung 19.0 sebagai versi awal**: `-i` hanya menerima 8.0–17.0,
  `-t` hanya 9.0–18.0. Tidak ada rule 19.0→18.0.
- `oca-port` 0.22 terpasang (`~/.local/bin/oca-port`), TAPI bekerja antar branch git
  (butuh repo git + branch target 18.0) — upstream tidak punya branch 18.0 dan
  folder porting adalah salinan tanpa `.git`.
- **Keputusan:** sapuan mekanis dilakukan manual setara migrator (grep pola 19-only,
  verifikasi API terhadap source Odoo 18 di `~/workspace/odoo18-test/odoo`,
  bump versi manifest 19.0→18.0), lalu perbaikan manual. Ini didokumentasikan
  di sini supaya jelas: alatnya dicoba dulu, bukan dilewati diam-diam.

## 2. Batch 1 — rantai inti (14 modul)

Urutan install (topologis, sesudah pemangkasan depends §3):

1. `farm_core`
2. `farm_agri_science`
3. `farm_operation`
4. `farm_quality`
5. `farm_crop`
6. `farm_breeding`
7. `farm_mrp`
8. `farm_planning`
9. `farm_field_crops`
10. `farm_processing`
11. `farm_agricultural_processing`
12. `farm_seed_industry`
13. `farm_biological_valuation`
14. `farm_valuation`

## 3. Depends di luar batch 1 — dipangkas (bukan ditambah)

Manifest asli batch 1 merujuk modul di luar batch 1. Sesuai arahan (ISL
disederhanakan, IoT/keuangan/China di luar batch 1), depends ini DIHAPUS dari
manifest + kode yang memakainya disederhanakan/dihapus (bukan dengan menambah
modul ke batch 1):

| Modul batch 1 | Depends yang dipangkas | Acuan kode yang terdampak |
|---|---|---|
| `farm_operation` | `farm_ux`, `agri_iot`, `agri_intervention` | `models/__init__.py`, `views/menu.xml`, `views/agri_science_dashboard_views.xml`, `views/farm_production_task_views.xml`, `models/farm_agricultural_campaign_base.py`, `models/project_task.py` (ref `farm_iot`), `tests/test_epic_044.py` |
| `farm_mrp` | `farm_isl` | `models/mrp_bom.py`, `models/mrp_bom_line_isl.py`, `models/mrp_production.py`, `models/stock_lot.py` |
| `farm_processing` | `farm_isl` | file-file `*_isl.py`, `missing_models.py` (termasuk SC license, lihat §6) |
| `farm_seed_industry` | `farm_isl` | `models/seed_isl.py`, `views/seed_isl_views.xml` |
| `farm_planning` | `farm_hr` | hanya manifest (tidak ada acuan kode di luar manifest yang terdeteksi) |
| `farm_agricultural_processing` | `farm_iot`, `farm_waste_mgmt` | `views/menu.xml`, `models/licensing/production_sc_extension.py` (SC license, lihat §6) |
| `farm_valuation` | `farm_financial`, `farm_financial_valuation` | hanya manifest (tidak ada acuan kode di luar manifest yang terdeteksi) |

## 4. Kendala yang sudah diketahui dari kajian — status

- **(a) PostGIS/geospasial di `farm_core`:** file terkait `agri_mixins.py`
  (`agri.geospatial.mixin`), `gis_utils.py`, `land_location.py`,
  `farm_location_3d.py`, `agri_neighborhood.py`, `agri_biological_asset.py`,
  `industry_physio_stage.py`, `product_template_extension.py`,
  `stock_matter_tracking.py`. Hasil cek awal: `gis_utils.py` hanya import
  stdlib (`math`, `json`, `logging`) — TIDAK ada import `shapely`/`pyproj` di
  batch 1. Penanganan per model dicatat di §7 (per modul).
- **(b) Lapisan ISL:** `farm_isl` (21 file .py) TIDAK masuk batch 1. Model paralel
  `agri.isl.*` + redirector tidak di-port. File `*_isl.py` di modul batch 1
  dihapus/disederhanakan; mixin `agri.odoo19.*` di `farm_core` dinilai per modul.
- **(c) Dependensi Python berat:** `shapely/pyproj/paho-mqtt/numpy/scipy` —
  hasil grep: **0 import** di modul batch 1 (non-test). Bila ditemukan saat
  perbaikan, catat di §7.
- **(d) UI Mandarin:** lihat §6.

## 5. Perubahan 19→18 (mekanis)

- Versi manifest: `1.0` → `18.0.1.0.0` (ekor numerik dipertahankan, mis.
  `1.2.1` → `18.0.1.2.1`); `19.0.1.0.0` → `18.0.1.0.0`
  (`farm_biological_valuation`).
- View sudah `<list>` (0× `<tree>` di repo), `attrs=`/`states=` 0×,
  `@api.multi` 0×, `decimal_precision` 0× — tidak ada pekerjaan di sana.
- JS batch 1: hanya 4 file — 3 tour test + 1 komponen nyata
  (`farm_quality/static/src/components/record_book_execution/`). OWL 3 (19)
  vs OWL 2 (18) dicek per komponen.
- Pola lain yang dicek manual per modul: API/field Odoo 19 yang tidak ada di 18
  (verifikasi grep terhadap source Odoo 18), `ir.actions`, bundle aset web,
  widget view.
- **Perbaikan koordinator saat ronde install test18 (9 Nov, malam):**
  - `models.Constraint(...)` (API deklaratif baru Odoo 19) → `_sql_constraints`
    gaya Odoo 18 (nama + definisi SQL + pesan sama persis). 4 titik:
    `farm_core/models/agri_lot_kinship.py`, `farm_core/models/stock_matter_link.py`,
    `farm_processing/models/mrp_bom_packaging.py` (2×). Sesudah perbaikan: 0
    `models.Constraint` tersisa di batch 1.
  - `stock.package` (nama model baru Odoo 19) → `stock.quant.package` (nama di
    Odoo 18; terverifikasi `stock/models/stock_quant.py:1584`). 5 titik, 2 file:
    `farm_core/models/stock_matter_tracking.py` (`_inherits`, Many2one
    `package_id`, `env[]` di `action_execute_fission`) +
    `farm_processing/models/package_management.py` (Many2one
    `stock_package_id`, `env[]` di `_action_done`).
  - **Multi-inherit tanpa `_name` (Odoo 18 `MetaModel.__new__`: `_name`
    default = `inherit[0]` hanya bila `_inherit` berisi 1 item; bila list
    >1 item, `_name` default = NAMA CLASS)** — kelas upstream
    `_inherit = ['product.template', ...]` tanpa `_name` menjadi model BARU
    bernama `ProductTemplate` yang menyalin semua field `product.template`
    sehingga `taxes_id` Many2many bentrok tabel relasi yang sama
    (`TypeError: Many2many fields ProductTemplate.taxes_id and
    product.template.taxes_id use the same table and columns`; model
    `StockLocation` yang sama menyalin `stock.location`). Perbaikan: tambah
    `_name` eksplisit = model yang diperluas:
    `farm_core/models/product_template_extension.py` →
    `_name = 'product.template'`;
    `farm_core/models/land_location.py` (class `StockLocation`) →
    `_name = 'stock.location'`. Hasil scan AST batch 1: hanya 2 kelas ini
    yang kena pola tersebut.
  - `res.groups` field `user_ids` (baru di Odoo 19, tidak ada di 18) di
    `farm_core/security/farm_security.xml` (grup Farm Manager diberi user
    root + admin) → dihapus; diganti 2 record update `res.users`
    (`base.user_root`, `base.user_admin`) dengan
    `<field name="groups_id" eval="[(4, ref('group_farm_manager'))]"/>` —
    efek sama, pola standar Odoo 18.

## 6. Adaptasi Indonesia / universal (perintah king 9 Nov 21:33 WIB)

1. **De-China-ize UI dan locale:** string Mandarin di `.py`/`.xml`/`.csv`/demo
   data → Bahasa Inggris (bahasa sumber Odoo). Tambah `i18n/id_ID.po` per modul
   batch 1 (terjemahan Bahasa Indonesia untuk string yang terlihat pengguna).
   `i18n/zh_CN.po` asli dibiarkan (tidak berbahaya). Jangan mengasumsikan locale
   `zh_CN` di mana pun dalam kode (hasil cek: 0 acuan `zh_CN` di kode batch 1
   di luar i18n/tests).
   Sebaran Mandarin (file non-test, terverifikasi Python): farm_core 14,
   farm_processing 10, farm_operation 8, farm_agricultural_processing 5,
   farm_agri_science 3, farm_planning 3, farm_seed_industry 2, farm_mrp 2,
   farm_quality 2, farm_biological_valuation 2, farm_breeding 1, farm_crop 1,
   farm_field_crops 0, farm_valuation 0.
2. **Fitur khusus regulasi China dikeluarkan/digeneralisasi:**
   - Lisensi SC (izin produksi pangan China): `farm.sc.license`,
     `farm.sc.category`, field `sc_license_required`/`sc_license_number`
     (`farm_processing/models/missing_models.py`, `mrp_bom.py`,
     `product_isl.py`), `farm_agricultural_processing/models/licensing/production_sc_extension.py`
     (cek SC saat produksi). Pilihan per item: hapus total, atau ubah jadi model
     sertifikasi/lisensi produksi generik yang bisa dikonfigurasi — dicatat di §7.
   - Modul industri pharma/chemical ISL (`farm.pharma.*`, `farm.chemical.*`
     di `farm_processing/models/industry_isl.py` dkk.) — khusus China/ISL,
     dikeluarkan bersama ISL.
   - Government reporting platform China ada di `farm_greenhouse` (bukan batch 1)
     — tidak disentuh di batch 1.
3. **Hal lokal harus konfigurabel, bukan hardcode:** daftar regulasi/sertifikasi,
   satuan, label — pakai pola standar Odoo (`res.country`, selection yang bisa
   di-extend, model konfigurasi) supaya adaptasi Indonesia/negara lain tinggal
   konfigurasi/terjemahan.
4. **Konteks Indonesia yang SUDAH ada dipertahankan:** PVP (Perlindungan
   Varietas Tanaman) di seed batch — JANGAN dihapus.
5. Lisensi tetap AGPL-3; logika bisnis inti tidak diubah.

## 7. Perubahan per modul (detail)

> Detail lengkap per modul di `PORTING.d/<modul>.md`. Ringkasan di bawah ini
> digabung koordinator sesudah perbaikan + verifikasi statis (py_compile,
> XML well-formed, scan CJK ulang = 0 di file non-test ke-14 modul).

- **farm_core** — `1.0` → `18.0.1.0.0`. Menu "Telemetry Center" (agri_iot)
  dihapus; `web_icon` farm_mobile/farm_livestock di-repoint; docstring
  `agri_view_mixin.py` digeneralisasi; `geofencing.py` guard `iiot.telemetry`.
  PostGIS nyata hanya `farm_location_3d.py` (`CREATE EXTENSION postgis` +
  `ST_3DIntersects`) → ditulis ulang Python murni (ray-casting + uji potong
  segmen 2D + rentang Z, fail-closed), field `geom_3d_polygon` tetap Char WKT;
  model lain sudah tanpa PostGIS (Char/Text/Float lat-lng + GeoJSON). Mixin
  `agri.odoo19.*` dipertahankan (tidak ada API 19-only di dalamnya; nama teknis
  sengaja tidak diganti karena dirujuk modul batch 2+); bug `datetime.timedelta`,
  guard `records[0]`, signature `search()` diperbaiki. Bug tambahan: import
  `ValidationError` hilang di clearing engine; dekorator `@api.model` yang salah
  di `land_location.calculate_area`. De-CJK 15 file; `i18n/id_ID.po` baru (97
  entri). Sisa: `quality.point` mock berpotensi konflik dengan `farm_quality`;
  `EmbeddingMixin` merujuk `llm.service` (gagal hanya bila dipanggil).
- **farm_agri_science** — `1.1.0` → `18.0.1.1.0`; depends tetap
  `['farm_core','mrp']`. De-CJK 3 file; `id_ID.po` baru (201 entri).
- **farm_operation** — `1.2.1` → `18.0.1.2.1`; depends dipangkas
  `farm_ux`, `agri_iot`, `agri_intervention`. Engine L0 `agri.intervention.base`
  hanya ada di modul `agri_intervention` (luar batch 1) tapi dipakai seluruh
  modul → **di-vendor verbatim 244 baris** ke
  `models/agri_intervention_base.py` (repo & lisensi sama, AGPL-3; header
  rekonsiliasi batch 2 — file ini WAJIB dihapus saat `agri_intervention`
  di-port). `_onchange_bom_id` memanggil `super()` yang tidak ada di Odoo 18 →
  dijaga `hasattr`. Widget `farm_ux` dihapus dari form MRP + `gauge
  max_field:'50'` → `max_value:50`; `iot_device_ids` (Many2many `iiot.device`)
  dihapus; `farm_isl_redirection.py` (stub no-op) dihapus; acuan
  `iiot.telemetry`/`farm.geofence`/`agri.carbon.ledger` dijaga degradasi.
  De-CJK 14 file (termasuk demo `2026春季产季` dihapus); `id_ID.po` baru (241
  entri). Sisa: `agri.intervention.base` mendefinisikan field
  `state`/`intervention_type`/`name` yang juga dimiliki `mrp.production`
  (tabrakan desain upstream — awasi saat install); cron
  `cron_generate_feeding_proposals` mencari state `'inprogress'` (bukan
  `'01_in_progress'` Odoo 18, bug upstream dibiarkan).
- **farm_planning** — `1.0` → `18.0.1.0.0`; depends dipangkas `farm_hr`.
  `intervention_template_views.xml` ternyata merujuk model milik sendiri
  (`agri.intervention.template`), tidak diubah. `planning_templates.py` duplikat
  mati (tidak di-import) dipertahankan sebagai referensi + header peringatan.
  De-CJK 3 file; `id_ID.po` baru (40 entri).
- **farm_quality** — `1.0` → `18.0.1.0.0`; depends **+`purchase`** (field
  `purchase_order_line_id` butuh `purchase.order.line`). Grup
  `farm_quality.group_farm_quality_manager` tidak ada → dibuat
  (`security/farm_quality_groups.xml`). `import math` hilang ditambah;
  `widget="priority"` dihapus dari 4 skor sensori Integer (Odoo 18 hanya
  izinkan di Selection); `views/quality_sample_views.xml` dimasukkan ke
  manifest; dekorasi `expiry_date < today` → `< current_date`. `JS
  record_book_execution` kompatibel OWL 2 apa adanya (tanpa perubahan; string
  UI hardcode Inggris, tidak masuk `.po`). `action_trigger_recall` dijaga
  (model `farm.supply.recall` bukan batch 1). De-CJK 12 baris `.py` + 10 baris
  `index.html`; `id_ID.po` baru (248 entri).
- **farm_crop** — `1.0` → `18.0.1.0.0`. Stub `farm.crop.cycle` 8 baris
  dibiarkan (hanya `_description` di-English-kan). `action_plan_campaign`
  dijaga (field campaign tidak ada di `farm.agricultural.campaign`);
  `mode="tree"` → `mode="list"`. De-CJK 1 baris `.py` + 10 baris `index.html`;
  `id_ID.po` baru (45 entri).
- **farm_breeding** — `1.0` → `18.0.1.0.0`. Dedup definisi ganda
  `trait_score_avg` di `stock.lot` (Selection vs Float) → hanya di
  `farm_trait.py`; `dna_marker` ditambah ke `stock.lot`; `widget="priority"` /
  `widget="handle"` dihapus dari field skor; satuan `mu` → ha (label + komentar
  konversi 1 mu = 1/15 ha). PVP: tidak ada di modul ini. De-CJK 3 docstring +
  10 baris `index.html`; `id_ID.po` baru (51 entri).
- **farm_field_crops** — `1.0` → `18.0.1.0.0`. Field `product.template` yang
  dirujuk tapi tidak ada di repo mana pun → dibuat (`models/product_template.py`
  baru: `is_agricultural_product`, `default_seeding_rate`,
  `default_planting_density`). `_get_isl_model` defensif + koreksi nama model
  (`farm.crop.production`→`farm.crop.task`, `farm.crop.bom`→`farm.crop.recipe`);
  `self.production_id` → `self.intervention_id` (VRA). Label `target_yield_mu`
  "per Mu" → "per Area Unit" (nama field dipertahankan). De-CJK 0 `.py` + 10
  baris `index.html`; `id_ID.po` baru (72 entri).
- **farm_mrp** — `1.1` → `18.0.1.1.0`; depends dipangkas `farm_isl`.
  `mrp_bom.py` + `mrp_production.py` ditulis ulang (hanya `industry_type` +
  guard backpressure `action_confirm` dipertahankan); dihapus:
  `mrp_bom_line_isl.py`, `mrp_bom_line_isl_models.py`, `stock_lot.py`,
  `mrp_isl_navigation_views.xml`, `test_isl_core.py`, `test_isl_views.py`.
  Shim `lot_producing_id` dihapus — Odoo 18 core sudah punya field itu dan
  tidak punya `lot_producing_ids`. De-CJK 2 file; `id_ID.po` baru (20 entri).
- **farm_processing** — `1.1.1` → `18.0.1.1.1`; depends dipangkas `farm_isl`.
  Dihapus total `industry_isl.py` (model `farm.pharma.*`/`farm.chemical.*`),
  `picking_isl.py` (stub kosong), `mrp_operation_isl.py`,
  `product_isl_views.xml`, `picking_isl_views.xml`. Model bisnis nyata
  dipertahankan dengan nama file baru: `processing_models.py`,
  `product_template.py`, `lot_harvest.py`, `processing_bom_line.py`,
  `industry_workcenter.py`. `stock_lot.py` diperbaiki (super() ke hook yang
  dihapus dihilangkan; tambah import `ValidationError` yang hilang upstream).
  De-CJK 10 file; `id_ID.po` baru (80 entri).
- **farm_agricultural_processing** — `1.1` → `18.0.1.1.0`; depends dipangkas
  `farm_iot`, `farm_waste_mgmt` (menu Storage Monitoring + Processing Waste
  dihapus). `Many2one('agri.isl.mrp.production')` → `mrp.production` (2 file);
  `harvest_altitude` dihapus dari `tea_isl.py` (`altitude_meters` hanya ada di
  `farm_medicinal_plants`, luar batch 1); label `(ISL Layer)` dibuang.
  **Penyimpangan dari rencana hapus `processing_isl.py`:** file dipertahankan
  sebagai `processing_models.py` karena modul ini sangat bergantung pada
  `agri.isl.processing.bom`/`agri.isl.processing.production` (12+ inherit/
  Many2one) — `_inherit = ['agri.isl.mrp.production']` → `_inherits =
  {'mrp.production': 'mrp_production_id'}` + field penghubung eksplisit; nama
  teknis `agri.isl.processing.*` dipertahankan agar tidak ada rename berantai.
  De-CJK 5 file; `id_ID.po` baru (93 entri).
- **farm_seed_industry** — `1.0` → `18.0.1.0.0`; depends dipangkas `farm_isl`.
  `seed_isl.py` → `seed_models.py` (model benih inti dipertahankan; semua mixin
  diverifikasi ada di batch 1), view → `seed_views.xml`. **PVP dipertahankan
  utuh** (`pvp_certificate_id`, `is_pvp_compliant`, ribbon). De-CJK 2 file;
  `id_ID.po` baru (32 entri).
- **farm_biological_valuation** — `19.0.1.0.0` → `18.0.1.0.0`; depends tetap.
  `_compute_market_price` memakai `price.price` (tidak ada; `farm.market.price`
  pakai `unit_price`) → diperbaiki + `try/except KeyError` (model belum ada
  saat modul ini install sebelum `farm_valuation`); akses `asset.lot_id` /
  `asset.growth_stage` → `getattr(..., False)`; tanggal string →
  `fields.Date.to_date()`; ref model cron yang salah diperbaiki + hook no-op.
  De-CJK penuh `fair_value_engine.py` + `index.html`; `id_ID.po` baru (102
  entri).
- **farm_valuation** — `1.0` → `18.0.1.0.0`; depends dipangkas `farm_financial`,
  `farm_financial_valuation` (0 acuan kode — hanya 2 baris manifest). Deskripsi
  "CAS standards" → "IAS 41 Agriculture". De-CJK `index.html` + komentar
  "Chinese standards" → hint CoA generik; `id_ID.po` baru (72 entri). Sisa:
  domain `_cron_run_monthly_revaluation()` merujuk field `growth_stage` yang
  tidak ada di `agri.biological.asset` (tidak memblokir install — method belum
  di-wire ke cron); harga pasar = 0 bila aset tanpa `lot_id`;
  `farm.market.price` belum punya form view/action/menu.

### SC license → lisensi produksi generik (bukan hapus)

Model baru `farm.production.license.category` (dengan `country_id`
`res.country`) + `farm.production.license`; field `sc_category_id` /
`sc_category_ids` / `sc_license_required` / `sc_license_number` →
`license_category_id` / `license_category_ids` / `license_required` /
`license_number`; cek di `action_confirm` tetap jalan, pesan error
`SC COMPLIANCE ERROR` → `PRODUCTION LICENSE ERROR`. PIRT/halal/BPOM bisa
ditambahkan sebagai DATA, bukan hardcode. 0 referensi `farm.sc.*` tersisa di
kode non-test (hanya 2 baris komentar/docstring di file lisensi baru yang
menyebut nama lama sebagai riwayat).

### Total de-China-ize batch 1

- 0 karakter CJK tersisa di file non-test ke-14 modul (terverifikasi scan
  Python oleh koordinator).
- `i18n/id_ID.po` baru di ke-14 modul, total **1.394 entri** (97 + 201 + 241 +
  40 + 248 + 45 + 51 + 72 + 20 + 80 + 93 + 32 + 102 + 72).
- `i18n/zh_CN.po` asli dibiarkan di semua modul; tidak ada locale di-hardcode.

## 8. Hasil install test18

**9 Nov 2026 ±22:15 WIB — 14/14 modul batch 1 `installed` di DB `test18`**
(terverifikasi via `ir.module.module`, bukan hanya exit code). Urutan install:
farm_core → farm_agri_science → farm_operation → farm_quality → farm_crop →
farm_breeding → farm_mrp → farm_planning → farm_field_crops →
farm_processing → farm_agricultural_processing → farm_seed_industry →
farm_biological_valuation → farm_valuation.

| Modul | Versi ter-install | Ronde lolos |
|---|---|---|
| farm_core | 18.0.1.0.0 | 5 |
| farm_agri_science | 18.0.1.1.0 | 5 |
| farm_operation | 18.0.1.2.1 | 5 |
| farm_quality | 18.0.1.0.0 | 6 (retry) |
| farm_crop | 18.0.1.0.0 | 5 |
| farm_breeding | 18.0.1.0.0 | 5 |
| farm_mrp | 18.0.1.1.0 | 5 |
| farm_planning | 18.0.1.0.0 | 5 |
| farm_field_crops | 18.0.1.0.0 | 5 |
| farm_processing | 18.0.1.1.1 | 6 (retry) |
| farm_agricultural_processing | 18.0.1.1.0 | 7 (retry 2) |
| farm_seed_industry | 18.0.1.0.0 | 7 (retry 2) |
| farm_biological_valuation | 18.0.1.0.0 | 5 |
| farm_valuation | 18.0.1.0.0 | 5 |

Perbaikan koordinator selama ronde install (detail di §5 + catatan per modul
di `PORTING.d/` — ditambahkan ke §7 ringkasan di bawah):

1. Ronde 1–2: `models.Constraint` → `_sql_constraints`; `stock.package` →
   `stock.quant.package`.
2. Ronde 3: multi-inherit tanpa `_name` menjadi model baru bernama class
   (`ProductTemplate`/`StockLocation`) → tambah `_name` eksplisit.
3. Ronde 4: `res.groups` field `user_ids` (baru Odoo 19) → record update
   `res.users` (`base.user_root`, `base.user_admin`) dengan `groups_id`.
4. Ronde 5: `farm_quality` gagal karena `models/__init__.py` menonaktifkan
   `from . import sample` (komentar pekerja salah: `sample.py` BUKAN proxy
   Enterprise — `farm.quality.sample` hanya alias atas `agri.quality.sample`
   milik sendiri) padahal `security/ir.model.access.csv` +
   `views/quality_sample_views.xml` merujuk `model_farm_quality_sample`.
   Perbaikan: import `sample` diaktifkan lagi; `quality.py` (proxy
   Enterprise `quality.point`/`quality.check`, HACCP) TETAP nonaktif.
   Satu akar ini yang menjatuhkan farm_quality + farm_processing +
   farm_agricultural_processing + farm_seed_industry sekaligus.
5. Ronde 6: `ValueError: Wrong @depends ... 'total_biomass' not found in
   model farm.lot.ham` — `@api.depends` mixin di
   `farm_core/models/agri_mixins.py` merujuk field dari mixin SAUDARA
   (`total_biomass` dari `AgriBiologicalInventoryMixin`, `current_stage_id`
   dari `AgriGrowthCycleMixin`, `geo_point` dari `GeoSpatialMixin`).
   Odoo 18 menggabung depends SEMUA override di MRO (`resolve_mro`) dan
   menolak field yang tidak ada di host model (Odoo 19 mentolerir).
   Perbaikan: `AgriBiologicalValuationMixin._compute_fair_value` depends →
   `('market_peg_price',)` saja; `AgriTraceabilityMixin._compute_trace_hash`
   depends → `('create_date',)` saja. Kedua method sudah membaca field
   opsional itu secara defensif (`getattr`/`hasattr`), dan di batch 1 tidak
   ada model yang menggabungkan ketiga mixin itu sekaligus, jadi tidak ada
   perilaku yang hilang. Catatan: bila batch 2 ada model yang menggabungkan
   valuation + inventory + growth, recompute otomatis atas perubahan biomass/
   stage tidak akan terpicu — perlu depends eksplisit di model itu.

Sisa peringatan (non-fatal, muncul tiap load registry): `DeprecationWarning`
"not overriding the create method in batch" di beberapa model (pola
`@api.model_create_multi` vs `create` upstream — Odoo 18 hanya warning),
plus warning deprecation upstream sendiri (`farm.quality.sample`,
`farm.biological.asset`, `farm.stock.lot.health`, dsb. — alias lama yang
sengaja dipertahankan). Tidak ada ERROR di log install ronde terakhir.

6. **Ronde 7 — celah `ir.model.access` upstream (9 Nov malam):** smoke test
   browser menemukan 3 action melempar dialog **Access Error** ("No group
   currently allows this operation") untuk `agri.biological.growth.curve`,
   `agri.industry.variety`, `agri.industry.physio.stage` — model-model itu
   tidak punya SATU PUN aturan akses. Audit presisi (167 model konkret
   batch 1 vs `ir.model.access` di DB): **119 model tanpa aturan** —
   farm_processing 45, farm_agricultural_processing 25, farm_core 21,
   farm_agri_science 8, farm_operation 7, farm_planning 6,
   farm_seed_industry 3, farm_biological_valuation 2, farm_valuation 2;
   farm_quality/farm_crop/farm_breeding/farm_mrp/farm_field_crops sudah
   lengkap (0). Penyebab: CSV di 5 modul hanya berisi header, dan di 3 modul
   (`farm_agri_science`, `farm_operation`, `farm_agricultural_processing`)
   CSV bahkan masih di-comment di manifest. Perbaikan: **+113 baris**
   `access_<model>,<model>,model_<model>,base.group_user,1,1,1,1` ke CSV
   masing-masing modul (6 baris sudah ada di CSV farm_agricultural_processing
   tapi belum termuat — hanya diaktifkan lewat uncomment manifest);
   uncomment CSV di 3 manifest; versi 9 modul yang disentuh naik 1 patch
   (mis. farm_core 18.0.1.0.0 → 18.0.1.0.1). Verifikasi sesudah `-u`:
   **0 model tanpa aturan**; semua 14 modul tetap `installed`. Grup yang
   dipakai mengikuti konvensi upstream sendiri (`base.group_user` seperti
   di farm_core) — penyempitan per grup farm (specialist/manager) diserahkan
   ke tahap hardening, bukan porting.

Smoke test browser: _lihat §10_.

## 9. Batch berikutnya (belum dikerjakan)

`farm_iot`, `agri_iot`, `farm_ai*`, `farm_robotics`, `farm_weather`,
`farm_livestock`, `farm_aquaculture`, `farm_apiculture`, `farm_mushroom`,
`farm_orchard_horticulture`, `farm_floriculture`, `farm_medicinal_plants`,
`farm_viticulture`, `farm_winery`, `farm_esg*`, `farm_financial*`,
`farm_hr`, `farm_waste_mgmt`,
modul khusus China lainnya.
(Batch 2 — `agri_intervention`, `farm_isl`, `farm_ux` — selesai 10 Nov 2026, lihat §12.)

## 10. Smoke test browser test18 (9 Nov 2026 ±22:30 WIB)

- Cara: Playwright headless Chromium (skrip
  `smoke-test.py`), login `admin/admin` `?debug=1`, buka action farm via
  URL path Odoo 18 `/odoo/action-<id>?debug=1`. **Catatan pola:** deep link
  hash lama `#menu_id=<id>&action=<id>` TIDAK diproses bila path sudah
  `/odoo/action-99` (terbukti di probe: hash berubah tapi tampilan tetap
  Dashboard action-99); navigasi wajib lewat path action.
- Hasil akhir (sesudah perbaikan ACL §8 butir 6): **7/7 action membuka list
  view, 0 pageerror, 0 console error** — Growth Curves (885), Quality
  Checks (977), Varieties (886), Growth Stages (887), Rotation History
  (965), Samples (982), Quality Record Books (980). Form New Quality Checks
  terbuka lengkap (Control Point, Lot/Batch, Linked Sample, Production Task,
  tombol Pass/Fail/Verify CCP, statusbar To do/Passed/Failed, tab Field
  Quick Test + LIMS & Traceability). Screenshot bukti di `smoke/`
  (`01-home-debug.png` … `09-quality-form-new.png`).
- Sebelum perbaikan ACL, 3 action (885/886/887) melempar dialog Access
  Error — lihat §8 butir 6.
- Pengamatan (bukan blocker): menu induk Crop Operations (618), Sci-Lab &
  VRA (620), Mobile Tasks (617), Livestock & Fish (619) TIDAK punya submenu
  di batch 1 (anak-anaknya didefinisikan modul luar batch 1 / dipangkas) —
  menu tampil tapi kosong. Alur fungsional penuh (buat + simpan record,
  MRP, dsb.) BELUM diuji — smoke test hanya membuktikan render list/form
  dan 0 error JS.

## 11. Simulasi fungsional batch 1 (10 Nov 2026) — perbaikan blocker

Laporan lengkap: `SIMULASI.md` + screenshot `simulasi/`. Dua bug upstream
ditemukan saat simulasi dan DIPERBAIKI (diizinkan aturan simulasi: perbaiki
blocker + dokumentasikan di sini). Keduanya bug logika upstream, bukan
artefak porting 19→18.

### 11a. `farm.crop.rotation.history` create SELALU gagal — tanggal string

- **Gejala:** buat rotation history apa pun (UI/shell) → `AttributeError:
  'str' object has no attribute 'year'`.
- **Akar:** override `create()` di
  `farm_crop/models/crop_rotation_history.py` mengambil
  `vals.get('planting_date', fields.Date.today())` — nilai dari vals
  adalah STRING `'YYYY-MM-DD'` — lalu diteruskan mentah ke
  `check_continuous_cropping_risk()` yang memanggil
  `planting_date.replace(year=planting_date.year - 3)`.
- **Fix:** `planting_date = fields.Date.to_date(vals.get('planting_date'))
  or fields.Date.today()` di `create()`, plus hardening yang sama di
  `check_continuous_cropping_risk()` (terima string juga). Compute
  `_compute_continuous_cropping_warning` sendiri sudah benar (membaca
  `record.planting_date` yang sudah berupa objek date).
- **Verifikasi:** rotation `SIMULASI Rotasi Tomat A1` (id 2) terbuat,
  state `planted`, warning False, risk 0.0; sesudah panen jadi `harvested`.

### 11b. `stage_progress` GDD SELALU crash saat fase di-assign — `target_gdd` tidak ada

- **Gejala:** set `current_stage_id` pada `agri.biological.asset` →
  `AttributeError: 'agri.industry.physio.stage' object has no attribute
  'target_gdd'` (compute `_compute_stage_progress`).
- **Akar:** mixin `agri.gdd.mixin` (`farm_core/models/agri_mixins.py`)
  membaca `current_stage_id.target_gdd`, tapi model
  `agri.industry.physio.stage` TIDAK punya field itu — target GDD fase
  bernama `accumulated_temp_threshold` ("Target Accumulated Temp (°C)").
- **Fix:** `_compute_stage_progress` memakai
  `rec.current_stage_id.accumulated_temp_threshold` sebagai target.
- **Verifikasi:** asset `SIMULASI Tanaman Tomat A1` (id 3): 10 hari suhu
  32/22 → GDD 170.0; set fase Germinasi (threshold 80) → progress 100.0;
  +10 hari → 357.0, fase TETAP Germinasi (`_check_stage_migration`
  memang no-op — pindah fase MANUAL); Vegetatif → 100.0, Berbunga →
  71.4, Berbuah/Panen → 44.6 (matematika persis).
- **Catatan desain (bukan bug):** progres dihitung terhadap threshold
  fase SAAT INI (`accumulated/threshold` fase berjalan, cap 100), bukan
  kumulatif antar fase; migrasi fase otomatis memang belum
  diimplementasikan upstream.

### 11c. Temuan simulasi lain (TIDAK diperbaiki — dicatat apa adanya)

### 11d. Form MO crash — `_compute_efficiencies` no-op (ditemukan saat bukti browser)

- **Gejala:** buka form `mrp.production` → dialog "Oops!" + log
  `ValueError: Compute method failed to assign
  mrp.production(17,).rue_actual`.
- **Akar:** `farm_processing/models/mrp_production.py` meng-override
  `_compute_efficiencies` (dari `farm.agri.science.mixin`) dengan badan
  `pass` — field compute `rue_actual`/`wue_actual` tidak pernah
  di-assign.
- **Fix:** override meng-assign `0.0` seperti mixin aslinya.
  Terverifikasi: form WH/MO/00017 terbuka lengkap (Done, 8,00/8,00,
  komponen 10,00 consumed).

### 11e. Perbaikan lingkungan test bed (bukan kode modul)

- **Kolom hilang `farm_location`:** `valuation_in_account_id` /
  `valuation_out_account_id` (field standar `stock.location` dari
  `stock_account`, diwarisi `farm.location` tapi kolomnya tidak pernah
  terbuat) → semua form yang membaca `farm.location` (rotation,
  intervensi) crash `ProgrammingError: column farm_location.
  valuation_in_account_id does not exist`. Fix: upgrade ke-14 modul
  batch 1 (`odoo-bin -u ... --stop-after-init`) — kolom terbuat.
- **View yatim `hr_maintenance`:** 4 view inherit
  (`maintenance.equipment.view.*.inherit.hr`, id 2402–2405) milik modul
  `hr_maintenance` yang sudah `uninstalled` masih ada di DB dan menyebut
  `employee_id` → form intervensi (auto-generated, tanpa view farm)
  crash client-side `OwlError:
  "maintenance.equipment"."employee_id" field is undefined`. Fix: hapus
  4 view yatim via shell + restart server (cache view di registry
  server lama masih menyimpan arch lama — restart WAJIB sesudah hapus
  view). Catatan: `agri.intervention` TIDAK PUNYA satu pun view di DB
  (form 100% auto-generated) — wajar bila batch 2 menambahkan view
  form/list khusus.

### 11f. Temuan simulasi lain (TIDAK diperbaiki — dicatat apa adanya)

- **NPK intervensi = 0, MO = benar.** `agri.intervention.pure_n/p/k_qty`
  dihitung `_compute_agri_costs` (mixin) yang TIDAK PERNAH meng-assign
  ketiganya → selalu 0.0 di form intervensi. MO induk
  (`AgriInterventionMrp._compute_pure_nutrients`) menghitung benar dari
  `move_raw_ids`: 50 kg NPK 16-16-16 → 8.0/8.0/8.0 kg. Perlu disatukan
  di batch 2 (saat `agri_intervention` di-port, engine verbatim diganti).
- **`farm.seasonal.bom.action_activate` stub.** Mengembalikan `True`
  tanpa menulis state — seasonal BoM tetap `draft` sesudah Activate.
  Sama untuk `action_deactivate`. Fungsinya murni pembungkus data BoM.
- **`farm.nursery.batch` tanpa state machine + tombol pindah tanam stub.**
  Tidak ada field `state`; `action_create_transplant_task` return True
  tanpa membuat `farm.breeding.order`/asset apa pun (terverifikasi
  hitungan 0→0). Pindah tanam → crop batch dilakukan manual di simulasi.
- **Valuasi market_price = 0.** `action_run_fair_valuation` membuat
  record di `agri.biological.asset.fair.valuation` (BUKAN di
  `agri.biological.asset.valuation` — ada DUA definisi method yang sama
  di dua modul, yang `farm_valuation` menang di MRO). Nilai pasar 0
  karena lookup harga butuh `lot_id` di asset, dan `agri.biological.asset`
  TIDAK punya `lot_id`. Valuasi cost_model bekerja: NBV = fair =
  Rp 2.500.000 (5.000.000 × koefisien 0,5). Nama valuasi fair
  berduplikasi (`VAL-...-1` dua kali) karena generator nama memakai
  `len(records)+1` per pemanggilan create tunggal.
- **`agri.intervention` TIDAK terikat lahan.** Tidak ada field
  `land_id`/`farm_location_id` di modelnya (hanya `intervention_type`,
  grade A/B/C, approval, `harvest_lot_ids`); keterikatan lahan hanya
  lewat lokasi MO. Template `agri.intervention.template` tidak mengenal
  tipe `irrigation` (hanya tillage/sowing/fertilizing/protection/
  harvesting) — intervensi irigasi tetap bisa dibuat langsung.
- **MO selesai TANPA `_set_quantities()` = jebakan shell, bukan bug
  modul.** `button_mark_done` pada MO yang `qty_producing`-nya ditulis
  via ORM (tanpa `_set_quantities()` seperti yang dilakukan onchange UI)
  menghasilkan MO `done` tapi move tetap `assigned` dan stok tidak
  bergerak — karena `stock.move.picked` tetap False dan
  `_post_inventory` melewati move yang belum picked secara diam-diam.
  Alur UI-equivalent (`_set_quantities()` dulu, lalu
  `button_mark_done`) TERBUKTI bekerja: MO 17/18 selesai, saus +16 kg,
  tomat −20 kg. Pelajaran metodologi: simulasi MO via shell WAJIB
  memanggil `_set_quantities()` sesudah `action_assign()`.

## 12. Batch 2 — agri_intervention + farm_isl + farm_ux (10 Nov 2026)

Perintah: aturan flow king (10 Nov 08:01) — simulasi batch 1 bersih (9/9)
→ batch berikutnya. Rekomendasi #1 laporan port.

### 12a. Hasil install test18 — 17/17 modul farm `installed`

| Modul | Versi ter-install |
|---|---|
| agri_intervention | 18.0.1.0.1 |
| farm_isl | 18.0.1.0.0 |
| farm_ux | 18.0.1.1.1 |
| farm_operation (upgrade) | 18.0.1.2.4 |

Urutan: agri_intervention → upgrade farm_operation (vendor dihapus, §12b)
→ farm_isl → farm_ux → upgrade agri_intervention + farm_operation
(widget dipulihkan, §12d). Semua terverifikasi via `ir.module.module`,
0 traceback di log install terakhir tiap modul.

### 12b. Rekonsiliasi engine vendor (WAJIB, dari §7 farm_operation)

- `farm_operation/models/agri_intervention_base.py` (244 baris verbatim)
  DIHAPUS 10 Nov; import dihapus dari `models/__init__.py`;
  `'agri_intervention'` ditambah ke depends `farm_operation`;
  versi 18.0.1.2.2 → 18.0.1.2.3.
- Diff terverifikasi koordinator: file vendor identik dengan engine asli
  `agri_intervention/models/agri_intervention_base.py` kecuali header
  komentar 10 baris. Upgrade farm_operation lolos, 0 traceback.

### 12c. Perbaikan koordinator saat install

1. **farm_ux install ronde 1 gagal** — `ValueError: External ID not found
   in the system: farm_ux.menu_ux_root`. Akar: pekerja mendedup
   `'views/menu.xml'` di manifest (upstream mencantumkannya DUA kali —
   pertama dan terakhir); file `*_views.xml` lain merujuk parent
   `menu_ux_root` yang baru didefinisikan di `menu.xml`. Fix: kembalikan
   `'views/menu.xml'` sebagai entri pertama `data` (duplikat dipertahankan
   seperti upstream) + komentar NOTE. Install ronde 2 lolos.
2. **Mapping MO→AI dinonaktifkan SEBELUM install** — record
   `term_mapping_mrp_production_short` (source `"MO"` → `"AI"`,
   `is_active` True) + engine regex tanpa word boundary, case-insensitive
   → merusak kata apa pun yang mengandung "MO" (`"Model"`→`"AIdel"`,
   `"Month"`→`"AI nth"`). Engine tidak diubah (logika upstream); record
   di-set `is_active` False + komentar NOTE. Mapping
   `"Manufacturing Order"` → `"Agricultural Intervention"` dibiarkan
   (frasa utuh, itu fungsi modul).
3. **ACL audit batch 2: 0 model konkret tanpa aturan.** 32 model tanpa
   aturan di `ir_model_access` — SEMUANYA `AbstractModel`
   (mixin/plugin/trait/base: `agri.intervention.base`,
   `agri.intervention.plugin*`, `agri.dna.plugin*`,
   `agri.valuation.plugin*`, `agri.isl.*.mixin`, `agri.isl.trait.*`,
   `agri.isl.model.redirector`, `agri.view.mixin`) — diverifikasi via AST.
   Tidak ada penambahan CSV di luar yang sudah dibuat pekerja
   (farm_isl +13 baris, farm_ux +3 baris).

### 12d. Widget farm_ux dipulihkan (sesudah farm_ux ter-install)

4 tag `<widget>` dikembalikan persis seperti upstream:
- `agri_gating_audit` di form `agri.intervention.test`
  (`agri_intervention/views/intervention_base_views.xml`).
- `agri_gating_audit`, `agri_spatial_gauge`, `agri_nutrient_gauge` di
  form `mrp.production`
  (`farm_operation/views/agri_intervention_views.xml`).
Versi naik: agri_intervention 18.0.1.0.0 → 18.0.1.0.1, farm_operation
18.0.1.2.3 → 18.0.1.2.4. Gauge `carbon_intensity` `max_value:50` TIDAK
di-revert (sudah benar). Catatan: gauge nutrisi menunjukkan 0 sampai bug
`_compute_agri_costs` (temuan simulasi batch 1) diperbaiki — lihat §13.

### 12e. Perubahan per modul batch 2 (ringkas; detail di PORTING.d/)

- **agri_intervention** — `1.0.0` → `18.0.1.0.0`. 2 guard baru di
  `models/intervention_plugins.py` (`agri.weather.forecast`,
  `agri.iot.telemetry` — keduanya ternyata TIDAK terjaga, dikoreksi dari
  premis awal); widget `agri_gating_audit` dihapus sementara dari form
  (lalu dipulihkan §12d); `i18n/id_ID.po` baru (72 entri); 0 CJK.
  Sisa: menu `Interventions` kosong (action tanpa menuitem anak);
  tidak ada `static/description/icon.png` (upstream juga tidak punya);
  bug upstream dibiarkan (plugin harvest memanggil
  `next_by_code('stock.lot')` padahal kode 18 adalah
  `stock.lot.serial` → nama lot grading jatuh ke fallback `'New'`).
- **farm_isl** — `19.0.1.0.0` → `18.0.1.0.0`. Author dibersihkan dari
  CJK; ACL CSV di-uncomment + 13 baris; guard di
  `agri_isl_bridge.py` (proxy `farm.lot.*` yang tidak ada di batch 1+2);
  2 file contoh root diberi header `DOCUMENTATION ONLY — DO NOT IMPORT`
  (tidak di-import); `views/qc_isl_views.xml` SENGAJA tidak dimuat
  (3 record kosong → install gagal validasi); de-CJK 44 → 0;
  `i18n/id_ID.po` baru (174 entri). Sisa: redirector bisa mengembalikan
  model lain (`agri.isl.processing.*`, `agri.intervention`,
  `farm.nursery.batch`); domain `industry_type` ISL vs batch 1 tidak
  cocok mentah; reintegrasi batch 1: tidak ada yang wajib
  (`industry_isl.py` pharma/kimia China JANGAN disambung).
- **farm_ux** — `1.1.1` → `18.0.1.1.1`. 4 perbaikan JS nyata:
  `useService` dari `@web/core/utils` → `@web/core/utils/hooks`;
  `useService("rpc")` → `import { rpc } from "@web/core/network/rpc"`;
  `this.env.session.uid` → `session.uid`; override mati
  `Home._set_lang` dihapus. Bonus: field `icon_class` → `icon`;
  `loadAllCustomizations`/`loadContextData` dipecah try/catch per
  sumber; panggilan help dialihkan dari model tak-ada
  `accessibility.integration` ke `contextual.help`; `owl="1"` dihapus
  dari template traceability. De-CJK 1.823 → 0 (termasuk 32 record
  `term_mapping` berlabel `zh_CN` padahal istilahnya Inggris → `en_US`,
  4 duplikat dihapus; default `zh_CN`/`Asia/Shanghai` → `en_US`/`UTC`;
  perintah suara `"zh"` → `"id"`). ACL +3 baris; `i18n/id_ID.po` baru
  (197 entri). Sisa: `menu.xml` me-rename 7 menu root core secara
  global (nama tidak kembali otomatis bila modul di-uninstall);
  `auto_install: True` (install eksplisit saja); `t-on-hold` bukan
  event standar 18 (tombol MARK AS DONE tidak terpanggil — widget belum
  dipakai view mana pun); panel Farm Hub tampil kosong
  (`get_contextual_help` mengembalikan list id, template mengharapkan
  objek).

### 12f. De-China-ize batch 2 (total)

- 0 karakter CJK di file non-test ketiga modul (terverifikasi scan
  Python oleh koordinator: agri_intervention 0, farm_isl 0, farm_ux 0).
- `i18n/id_ID.po` baru: 72 + 174 + 197 = **443 entri**.
- Total porting (batch 1 + 2): 1.394 + 443 = **1.837 entri**.

### 12g. Perbaikan B9 — tombol eksekusi wizard migrasi ISL (10 Nov 2026)

Temuan simulasi ulang batch 2 (SIMULASI.md, Blocker B9): dialog
`ISL Data Migration` (action 1013, model `agri.isl.migration.utility`)
terbuka dan field `Base Model`/`Industry Type`/`Confirm Migration`
bisa diisi, tapi footer form `view_isl_migration_utility_form`
(`farm_isl/views/menu.xml`) kosong — tidak ada tombol yang memanggil
`action_migrate_data`. Klik Ok (default save+close) hanya menutup
dialog: 0 notifikasi, jumlah `agri.isl.mrp.production` tetap 1,
migrasi tidak berjalan. Method-nya sendiri sudah lengkap
(`models/agri_isl_migration.py:42` — `UserError` bila `confirmation`
mati, migrasi via `agri.isl.model.redirector.create_isl_record`,
return `ir.actions.client` `display_notification` "Migration
Complete"); tidak ada perubahan Python.

Fix (view saja): tombol footer di form wizard tersebut —
`<button string="Migrate Data" name="action_migrate_data"
type="object" class="btn-primary"/>`. Label "Migrate Data": tidak ada
string tombol "Migrate" di modul (yang ada hanya nama action
"ISL Data Migration" dan pesan "Migration completed...").
Tombol object di wizard target=new: method jalan, lalu dialog
menutup dan notifikasi client action tampil — perilaku yang
diharapkan. Versi naik: farm_isl 18.0.1.0.1 → **18.0.1.0.2**.
Verifikasi fungsional (klik tombol → jumlah record ISL bertambah +
notifikasi "Migration Complete") dilakukan agen simulasi sesudah
upgrade oleh koordinator — belum diuji di sini.

### 12h. Perbaikan B6 + B7 — blocker simulasi ulang batch 2 (10 Nov 2026)

Temuan simulasi ulang batch 2 (SIMULASI.md, Blocker B6 + B7).
Keduanya di `farm_operation` saja; tidak ada modul lain yang diubah.

1. **B6 — `widget="ace"` mode `'json'` tidak valid di Odoo 18.**
   `farm_operation/views/agri_intervention_views.xml:65`, field
   `quality_fingerprint` (Text berisi JSON dari `json.dumps`).
   `CodeEditor.MODES` 18 hanya `javascript/xml/qweb/scss/python` —
   `'json'` tidak ada: di `?debug=1` validasi prop Owl melempar
   `OwlError: Invalid props for component 'CodeEditor': 'mode' is not
   valid` sehingga tab Spatial & Evidence Oops total; di non-debug Ace
   404 `mode-json.js`. Fix (view saja): mode `'json'` →
   `'javascript'` — JSON adalah subset sintaks JS object literal,
   jadi highlighting-nya cocok. Satu-satunya `ace`+`json` di modul
   ter-install batch 1+2 adalah field ini (grep sesudah perbaikan:
   0 hasil di `farm_operation/`).
2. **B7 — buat intervensi baru via UI crash `ValueError: Wrong value
   for agri.intervention.intervention_type: 'process'`.** Akar:
   ada TIGA definisi `intervention_type` — `agri.intervention.base`
   (modul `agri_intervention`, seleksi 9 nilai + `default='process'`),
   `agri.intervention.mixin` (`farm_operation`, seleksi 9 nilai TANPA
   `'process'`, tanpa default), dan `mrp.production`
   (`farm_operation`, seleksi 10 nilai + `default='process'`).
   Redefinisi field Odoo mempertahankan atribut yang tidak
   di-override, sehingga default `'process'` dari base lolos ke field
   mixin sementara seleksinya membuang nilai itu — `default_get()`
   mengembalikan `{'intervention_type': 'process'}` dan
   `onchange`/`_update_cache` menolaknya sebelum `create()` berjalan
   (perbaikan propagasi B4 saat `create()` tidak menutup jalur ini).
   Fix (Python, minimal): tambah `('process', 'General Process')` +
   `default='process'` eksplisit pada seleksi mixin
   (`farm_operation/models/agri_intervention_mixin.py`) — seleksi
   mixin kini identik dengan seleksi MO (10 nilai, label sama), jadi
   default selalu valid. Dampak yang dijaga: propagasi B4 tidak
   berubah (fertilizing → MO `fertilizing`, tillage → MO `tillage`;
   `'process'` terpropagasi sebagai no-op karena itu juga default MO)
   dan MO 19 yang sudah ber-`intervention_type='process'` tetap
   valid. Komentar B4 di
   `farm_operation/models/farm_agricultural_intervention.py`
   dikoreksi (sebelumnya menulis mixin "tidak punya 'process'").
   Verifikasi: `py_compile` semua file Python yang diubah; XML
   tervalidasi well-formed; `default_get` `agri.intervention` via
   odoo-bin shell (read-only) mengembalikan `'process'` yang kini
   lolos validasi seleksi. Verifikasi browser (New form intervensi
   terbuka di `?debug=1` tanpa Oops + tab Spatial tanpa CodeEditor
   error) dilakukan agen simulasi sesudah upgrade oleh koordinator —
   belum diuji di sini, karena perubahan view/registry baru aktif
   sesudah upgrade modul.
Versi naik: farm_operation 18.0.1.2.5 → **18.0.1.2.6**.

### 12i. Perbaikan B8 — gauge spatial NaN% (10 Nov 2026)

Temuan simulasi ulang batch 2 (SIMULASI.md, B8): tab Spatial &
Evidence form MO 23 (tillage) me-render gauge `SPATIAL COMPLIANCE
AUDIT`, tapi cincin menunjukkan **NaN%** merah + label **OOB
Points**, padahal nilai server benar (shell: MO 23
`spatial_compliance_rate = 100.0`, `out_of_bounds_count = 0`;
MO 20 sama). Akar: `record.data` di web client HANYA berisi field
yang ada di arch view — kedua field itu TIDAK ada di form MO
(`farm_operation/views/agri_intervention_views.xml`: di page
Spatial & Evidence hanya ada `<widget name="agri_spatial_gauge"/>`
tanpa field tersebut), jadi `data.spatial_compliance_rate` =
`undefined` → `Math.round(undefined)` = NaN (template
`farm_ux/static/src/xml/agri_spatial_gauge.xml:22`), dan
`out_of_bounds_count === 0` = false → cabang OOB. Getter JS
(`|| 0`) hanya menutupi `strokeDasharray`/`gaugeColor`, bukan
teks template — itulah sebabnya cincin merah 0% + teks NaN%.

Fix (JS saja, di `farm_ux`, tanpa ubah logika hitung server dan
tanpa ubah view MO): `fieldDependencies` pada registry item
`agriSpatialGauge` di
`farm_ux/static/src/js/agri_spatial_gauge.esm.js` —
`[{name: "spatial_compliance_rate", type: "float"},
{name: "out_of_bounds_count", type: "integer"}]`. Ini mekanisme
resmi Odoo 18: `relational_model/utils.js`
(`extractFieldsFromArchInfo`) membaca
`widgetInfo.widget.fieldDependencies` dan menambahkan field
tersebut ke `activeFields`/read; skema validasinya ada di
`web/.../views/widgets/widget.js` (`fieldDependencies` opsional,
bentuk `{name: String, type: String}`); preseden core:
`week_days` (boolean). Penempatan WAJIB di objek registry item,
bukan di class Component. Alternatif "tambah kedua field ke arch
view MO" ditolak: view MO milik `farm_operation`, bukan `farm_ux`,
dan `fieldDependencies` memang disediakan untuk kasus ini.

Pemeriksaan dua widget lain (sesuai perintah tugas):
- `agri_nutrient_gauge` — TIDAK cacat, TIDAK diubah: `pure_n/p/k_qty`
  ADA di arch view MO (`agri_intervention_views.xml:75-77`), itulah
  sebabnya gauge N/P/K 8.0 tampil benar di simulasi. Menambah
  `fieldDependencies` di sana tidak perlu (field sudah di-load via
  arch; `addFieldDependencies` hanya me-patch field yang sudah ada).
- `agri_gating_audit` — cacat LATEN kelas yang sama, DIPERBAIKI:
  `weather_gating_status`/`compliance_gating_status`/`iot_status`
  tidak ada di arch view mana pun yang memakai widget ini (form
  `mrp.production` maupun form `agri.intervention.test`), jadi
  getter selalu jatuh ke fallback `config['none']` (WEATHER N/A,
  COMPLIANCE Pending, IOT No Sensors). Hari ini tampilannya
  kebetulan benar karena itu juga nilai default server
  (`'none'`/`'none'`; `iot_status` MO = `'normal'` versi mixin yang
  juga tidak ada di config widget) — tapi begitu plugin
  cuaca/kepatuhan menulis nilai nyata (`'safe'`/`'blocked'`/...),
  widget tetap menampilkan N/A. Fix: `fieldDependencies` ketiga
  field selection tersebut di `agri_gating_audit.esm.js`. Tampilan
  saat ini TIDAK berubah; yang berubah hanya nilai server nyata
  kini terbaca. Catatan: `iot_status` di `mrp.production` adalah
  versi mixin (`normal/monitoring/warning/critical`), bukan versi
  base (`connected/offline/critical/none`) — `'critical'` tetap
  tampil Alert, sisanya fallback No Sensors.

Versi naik: farm_ux 18.0.1.1.2 → **18.0.1.1.3**. Verifikasi visual
(gauge MO 23 = 100.0% hijau + "Within Boundaries"; gating tetap
N/A/Pending/No Sensors) dilakukan agen simulasi sesudah upgrade
oleh koordinator — belum diuji di sini.

### 12j. Perbaikan B7b + B7c + B9b — ronde perbaikan batch 2 (10 Nov 2026)

Perintah king 10:39 WIB. Dua pekerja paralel (modul terpisah, tanpa
tabrakan); catatan lengkap di `PORTING.d/b7b.md` + `PORTING.d/b9b.md`.

- **B7b — form view khusus `agri.intervention`** (`farm_operation`
  18.0.1.2.6 → **18.0.1.2.7**): record baru
  `view_agri_intervention_form` (`agri.intervention.form`), primary,
  priority 16, satu-satunya form view model itu → form default,
  termasuk via URL langsung. **TIDAK memuat `production_id` sama
  sekali** (bahkan bukan readonly) — client tidak memvalidasi field
  yang tak ada di view; `create()` `_inherits` tetap membuat MO
  otomatis. Berisi semua field skenario B2F (`intervention_type`,
  `biological_asset_id`, `product_id`, `product_qty`, `bom_id`,
  `product_uom_id`, `picking_type_id`, lokasi) + field mixin/base
  (approval, jadwal, eksekusi, grading, biaya, nutrien, gating,
  audit spasial, Components readonly, chatter) + tombol header
  workflow (Submit/Approve/Reject/Start/Stop, visibilitas
  dicerminkan dari inherit form MO) + statusbar `state`. Alternatif
  "jadikan `production_id` tidak-required" DITOLAK: tidak diperlukan
  dan melawan kontrak `_inherits` (`_inherits_check` core justru
  memaksa field `_inherits` menjadi `required=True` + `ondelete
  cascade`).
- **B7c — `name` editable di form baru**
  (`<field name="name" readonly="0" force_save="1"/>`) + fallback
  di `create()`: bila `name` dibiarkan `New`/kosong, diganti nama MO
  yang baru dibuat (`WH/MO/xxxxx`); nama yang diketik tidak pernah
  disentuh. **Koreksi diagnosis:** `name` adalah field MILIK
  `agri.intervention` sendiri (`agri.intervention.base`,
  `agri_intervention/models/agri_intervention_base.py:17`:
  `required=True, readonly=True, default='New'`) — BUKAN warisan
  `mrp.production` seperti ditulis SIMULASI.md B7c. Core
  (`_add_inherited_fields`) hanya menambahkan field parent yang
  "not redefined locally", jadi saat `_inherits` create membagi
  vals, `name` tinggal di vals anak dan MO tidak pernah
  menerimanya; MO selalu dapat sequence. Sequence MO juga tidak
  menimpa nama ketik (`mrp.production.create` hanya memberi
  sequence bila nama kosong/`'New'`). Propagasi B4 tidak diubah.
- **B9b — dialog wizard menutup sendiri** (`farm_isl` 18.0.1.0.2 →
  **18.0.1.0.3**): `action_migrate_data()` kini mengembalikan
  `display_notification` dengan `params.next = {'type':
  'ir.actions.act_window_close'}`. Pola diverifikasi dari source
  test bed (`web/.../client_actions.js:9-23` menambahkan notifikasi
  lalu `return params.next`; `action_service.js:1262-1268`
  mengeksekusi nilai kembalian via `doAction`) dan dipakai core
  Odoo 18 sendiri di wizard dialog (`account_merge_wizard.py:121`,
  `account_move_send_batch_wizard.py:115`). Notifikasi hijau tetap
  ada; Confirm mati → UserError tetap (dialog tetap terbuka).
- **B9 hitungan — hanya record ISL baru:** pre-check
  `redirector.get_isl_record(base_model_name, base_record.id)`
  sebelum `create_isl_record`; hitung hanya bila sebelumnya belum
  ada DAN create mengembalikan record. `create_isl_record()` tidak
  diubah (anti-duplikat utuh). Verifikasi read-only: rerun
  `mrp.production` dengan logika baru → would claim **0** (kode
  lama mengklaim 25); `get_isl_record` vs pencarian link-field
  langsung ke-25 MO → 0 mismatch. Batasan jujur: `get` menyaring
  by industry milik base record, `create` menyimpan industry milik
  wizard — bila industry wizard berbeda antar run dan sudah ada
  record ISL dengan stored industry lain, hitungan bisa over-claim
  untuk record itu (tanpa duplikat); kasus normal (industry sama)
  sepakat penuh.
- Verifikasi koordinator: `py_compile` OK, XML well-formed, 0
  `<field name="production_id"` di view baru, manifest
  farm_operation 18.0.1.2.7 + farm_isl 18.0.1.0.3, klaim `name`
  milik anak terverifikasi dari source (`agri_intervention_base.py:17`).
- **Koreksi koordinator saat upgrade (10 Nov 2026):** upgrade
  `farm_operation` GAGAL pertama kali — `ParseError: Field
  "product_uom" does not exist in model "agri.intervention"` pada
  sub-view Components (`move_raw_ids`/`move_finished_ids`). Akar:
  worker memakai tag **`<tree>`** (deprecated); di Odoo 18
  `_validate_tag_field` (`ir_ui_view.py`) hanya merekursi sub-view
  bila child.tag in `('form','list','graph','kanban','calendar')`
  — `<tree>` dilewati sehingga field di dalamnya divalidasi
  terhadap model form, bukan comodel `stock.move` (padahal
  `product_uom` ADA di `stock.move`). Fix: kedua `<tree>` →
  **`<list>`** (aturan AGENTS.md: view list pakai tag `<list>`).
  Inventaris field worker ("semua field ada") benar isinya tapi
  salah tag — pelajaran: cek tag sub-view, bukan hanya nama field.
  `farm_isl` sudah ter-upgrade duluan (0.3) sebelum kegagalan ini;
  `farm_operation` di-upgrade ulang sesudah fix → 2.7 = 2.7,
  `installed`, 0 traceback; view `agri.intervention.form` (id 2771)
  ada; server hidup 8071 → 200.

## 13. Simulasi fungsional batch 2 (10 Nov 2026)

- Ronde B6–B9 (10 Nov ±10:20–10:40 WIB): **TIDAK BERSIH** —
  B7 GAGAL (blocker baru B7b: `production_id` required memblokir
  Save), B9 lolos dengan catatan (B9b dialog tidak menutup +
  hitungan notifikasi). Detail: `SIMULASI.md` § "Simulasi ulang
  batch 2 — ronde perbaikan B6–B9".
- **Ronde perbaikan B7b (10 Nov ±11:00–11:30 WIB): BERSIH —
  batch 2 SELESAI.** B7b + B7c + B9b + regresi penuh lolos lewat
  UI `?debug=1`, 0 pageerror + 0 console error di semua run
  (fase A/A2/B/C2/D), log server 0 Traceback / 0 HTTP 404.
  IV13 `SIMULASI B2G Intervensi Pupuk NPK Tomat A1` dibuat
  murni lewat UI (nama persis, MO WH/MO/00026
  `intervention_type='fertilizing'`); IV14 tanpa menyentuh
  `name` → bernama `WH/MO/00027` (MO27 `tillage`); workflow
  tombol UI Submit → Approve → Start → Stop sampai `done`,
  NPK 0.0 → 8.0/8.0/8.0; MO26 done (tomat +5.000 kg →
  20.480 kg, NPK 50 → 0 kg); migrasi ISL run 1 klaim tepat 2,
  run 2 klaim 0, dialog menutup sendiri di kedua run, negatif
  UserError dialog tetap terbuka; MO27 spatial 100% Within
  Boundaries. Detail + data: `SIMULASI.md` § "Simulasi ulang
  batch 2 — ronde perbaikan B7b". Batch 3 BOLEH dimulai atas
  perintah king.
- Catatan alat uji (bukan bug produk): label selection
  `tillage` adalah **Soil Preparation**, bukan `Tillage` —
  pilih selection via label yang benar; skrip uji fase C
  sempat berhenti di klik × wizard karena dialog UserError
  menutupi × di bawahnya (halaman wizard dibuktikan ulang
  bersih di fase C2).

## 14. Batch 3 — farm_livestock + farm_aquaculture (10 Nov 2026)

Dua pekerja paralel (modul terpisah, tanpa tabrakan); catatan
lengkap di `PORTING.d/farm_livestock.md`,
`PORTING.d/farm_livestock_matter.md`,
`PORTING.d/farm_aquaculture.md`,
`PORTING.d/farm_aquaculture_matter.md`,
`PORTING.d/farm_livestock_valuation.md`.
Verifikasi + install oleh koordinator.

### 14a. Hasil install test18 — 21/21 modul farm `installed`

`farm_livestock` **18.0.1.2.0**, `farm_livestock_matter`
**18.0.1.0.0**, `farm_aquaculture` **18.0.1.0.0**,
`farm_aquaculture_matter` **18.0.1.0.0** — semua `installed`,
`installed_version = latest_version`. Server hidup lagi
(PID 16088, 8071 → 200, log server 0 Traceback).

### 14b. Scope batch 3 — yang ikut dan yang tidak

| Modul | Keputusan |
|---|---|
| `farm_livestock` | Ikut. Depends asli semua sudah ter-install (farm_operation, farm_core, farm_mrp, project, mrp, stock) — tidak ada pemangkasan. |
| `farm_livestock_matter` | Ikut (`auto_install: True`). |
| `farm_aquaculture` | Ikut. Depends `farm_iot` **DIPANGKAS** (batch IoT/cuaca, belum ada) — lihat §14c. |
| `farm_aquaculture_matter` | Ikut (`auto_install: True`). |
| `farm_livestock_valuation` | **DITANGGUHKAN ke batch financial.** `LivestockBiomassValuator._inherit = 'farm.financial.asset.valuation'` — model itu hanya ada di `farm_financial_valuation` (belum di-port); tanpa itu install gagal di registry. File TIDAK disentuh (diff vs clone = 0). Lisensi LGPL-3 dipertahankan untuk nanti. Dua model lain di file itu (`farm.livestock` stub, `livestock.weight.record`) hanya bermakna sebagai input jembatan valuasi, jadi tidak di-port terpisah. |

### 14c. Pemangkasan `farm_iot` dari farm_aquaculture

Manifest: `'farm_iot'` dihapus dari depends (+ NOTE). Koreksi
terhadap handover: `models/ras_welfare.py` ternyata TIDAK
merujuk `farm_iot` sama sekali (grep = 0) — satu-satunya
sentuhan IoT adalah dua hook transport-agnostic yang menerima
dict polos (`handle_aquaculture_telemetry`,
`handle_lss_telemetry`) + payload JSON ke
`agent_instruction_json`; tidak ada import/`env[]` ke
`farm_iot`/`iiot.*`, jadi **tidak ada baris kode IoT yang
dipangkas**, hanya ditambah komentar NOTE bahwa `farm_iot`
(batch berikut) bisa memanggil hook tersebut. Satu-satunya
acuan `iiot.device`/`industrial_iot` ada di file test (epic
019/034) — tidak diubah.

### 14d. Perubahan per modul batch 3 (ringkas; detail di PORTING.d/)

- **farm_livestock** — `1.2` → `18.0.1.2.0`. Pola 19-only:
  `_get_isl_model` tanpa base hook (`models/mrp.py`, hook
  dasarnya hilang saat `farm_mrp` ditulis ulang batch 1 →
  guard `try/except AttributeError → False` pola
  `farm_field_crops`); `mrp.bom` tidak punya
  `intervention_type` (domain `active_feeding_bom_id` dan
  test mengasumsikannya ada — hanya ada di
  `mrp.production`) → field ditambahkan ke `MrpBom`
  (seleksi 10 nilai + default `'process'`, persis
  `mrp.production`, pelajaran B7); `widget="ace"` mode
  `'json'` → `'javascript'` (jebakan B6 batch 2).
  Bug upstream lain (ada juga di 19.0): demo data menulis
  `born_at`/`gender` ke `stock.lot` → ditulis ulang
  (`birth_date`, `is_animal`); `action_record_death`
  tidak ada (wizard + test memanggilnya) → alias ke
  `action_record_mortality`; `action_merge_from` menulis
  `active: False` (stock.lot tidak punya field `active`
  di 18) → dihapus; cron harian mencari
  `biological_stage` (computed non-stored) → search
  `active_feeding_bom_id` + `.filtered()` Python; kanban
  `default_group_by="biological_stage"` + measure
  `animal_count` (non-stored) membuat `read_group`
  melempar → keduanya dihapus dari view.
  `ir.model.access`: CSV tadinya dikomentari di manifest
  dan hanya 1 aturan → audit AST 10 model konkret, +9
  baris `base.group_user,1,1,1,1`, CSV diaktifkan, 0 model
  tanpa aturan. De-CJK 29 baris → 0; `i18n/id_ID.po`
  baru 219 entri.
- **farm_livestock_matter** — `19.0.1.0.0` →
  `18.0.1.0.0`. 0 model konkret (hanya extend
  `stock.matter.tracking`) → tidak butuh CSV.
  `id_ID.po` baru 2 entri.
- **farm_aquaculture** — `1.0` → `18.0.1.0.0`. Pola
  19-only: `widget="ace"` mode `'json'` →
  `'javascript'` (B6); `super()._get_isl_model()` /
  `super()._get_isl_summary_parts()` tanpa base →
  defensive `try/except AttributeError` + koreksi nama
  model kembalian yang tidak ada
  (`agri.isl.aquaculture.production` → `.task`,
  `.bom` → `.recipe`) dan field
  (`isl.current_count` → `isl.animal_count`);
  `message_post()` tanpa `mail.thread` di
  `ras_welfare.py` → `'mail.thread'` ditambah ke
  `_inherit` di `ras_isl.py`; compute method hilang
  (`agri.isl.aquaculture.task.current_density`
  `compute='_compute_aquaculture_kpi'` padahal method
  hanya ada di model lot) → field jadi Float polos
  `default=0.0`; `self.recipe_id` tidak ada di
  `handle_aquaculture_telemetry` → recipe dicari lewat
  `self.bom_id` (parent `_inherits`). Lapisan ISL
  dipertahankan utuh (semua mixin ada di batch 1+2).
  ACL: CSV upstream hanya header → +8 baris
  `base.group_user,1,1,1,1` (8 model konkret).
  De-CJK: `index.html` 97 + `banner.svg` 9 → 0;
  `i18n/id_ID.po` baru 132 entri. Matter: nama
  manifest de-CJK + tambah `'license': 'AGPL-3'`
  (upstream tidak punya kunci lisensi).
- **farm_aquaculture_matter** — `19.0.1.0.0` →
  `18.0.1.0.0`. `id_ID.po` baru 2 entri.

### 14e. Perbaikan koordinator saat install (10 Nov 2026)

1. **farm_livestock tidak terlihat di `ir.module.module`**
   pada percobaan install pertama (symlink dibuat sesudah
   update apps-list terakhir) → `update_list()` dulu, baru
   `button_immediate_install`. farm_aquaculture ter-install
   bersih di percobaan pertama; matter keduanya ikut
   `auto_install`.
2. **Wizard `livestock.death.report` tidak pernah
   ter-register** — install farm_livestock gagal
   `ParseError: No matching record found for external id
   'model_livestock_death_report'` di CSV akses. Akar:
   `farm_livestock/__init__.py` upstream (19.0 juga) hanya
   `from . import models`; paket `wizard/` (model
   TransientModel `livestock.death.report`) tidak pernah
   di-import, jadi model tidak ada di registry padahal
   aturan akses CSV merujuknya. Fix: tambah
   `from . import wizard` ke `__init__.py` (tidak ada view
   yang membuka wizard ini — tetap dormant, tapi
   ter-register dan aturan aksesnya valid).
3. **Demo data farm_livestock masih gagal load**
   (ParseError, non-fatal — install tetap lanjut):
   `ref="farm_core.product_variety_cow"` tidak ada di
   test18 (pekerja mengklaim "ada" — keliru; produk itu
   didefinisikan di `farm_core/data/farm_demo_data.xml`
   tapi demo farm_core tidak ter-load di DB ini: 0 record
   produk farm_core). Fix: demo dibuat self-contained —
   produk sapi didefinisikan lokal di demo file
   (`product.template` "Demo Dairy Cow", tracking lot);
   varian dicari lewat atribut `search` (membuat
   `product.product` eksplisit melanggar unique
   constraint kombinasi varian karena template otomatis
   membuat satu varian). Diverifikasi lewat
   `convert_file(kind='demo')`: 2 lot COW-2026-001/002
   terbentuk benar (`is_animal=True`, birth_date benar),
   lalu dibersihkan lagi supaya test18 tetap bersih
   untuk simulasi.

### 14f. De-China-ize batch 3 (total)

0 karakter CJK di file non-test keempat modul (livestock
29 → 0, aquaculture 106 → 0 di index.html/banner.svg;
`.py`/`.xml` sudah 0). `zh_CN.po` dibiarkan. `i18n/id_ID.po`
baru: livestock 219, livestock_matter 2, aquaculture 132,
aquaculture_matter 2 entri. Tidak ada fitur khusus
regulasi China di keempat modul.

### 14g. Batasan yang diketahui (untuk simulasi batch 3)

- Test upstream sebagian merujuk model yang tidak ada
  (`agri.isl.aquaculture.bom`/`.production`,
  `iiot.device`, `agri.ras.biofilter`, `gender` di test
  matter) — test akan error bila dijalankan, install
  tidak terpengaruh. `test_ras_welfare.py` self-skip.
  Test livestock yang diperkirakan masih gagal
  (inkonsistensi upstream): `test_livestock_isl::test_02`
  (recipe `daily_feed_intake=12.5` vs constraint max
  10.0), `test_livestock_logic::test_02`
  (`product_qty==50` — `animal_count` tidak persisten
  lewat bridge), `test_feeding::test_01` (baca
  `move_raw_ids` tanpa `action_confirm`),
  `test_group_movements::test_02` (assert stage
  `'harvested'` pasca-merge).
- `animal_count`/`average_weight`/`biological_stage`
  computed non-stored — tidak bisa ditulis/dicari/
  groupby; cron memanggil `button_mark_done()` tanpa
  `_set_quantities()` (jebakan MO batch 1 — perlu
  dibuktikan saat simulasi batch 3); field
  `mrp.bom.intervention_type` belum tampil di view mana
  pun; 4 action tanpa menu (Lifecycle Events,
  Environment Monitoring, Livestock Recipes ISL,
  Livestock Growth Tasks — hanya via URL action); dua
  menu root "Livestock" + dua menu root "Aquaculture"
  (duplikat upstream, dibiarkan).
- **Aturan flow KUMULATIF (king 10 Nov 11:18 WIB,
  menggantikan aturan 08:01):** simulasi tiap batch
  mengulang SEMUA batch yang sudah selesai — batch 3
  berarti simulasi batch 1 + batch 2 + batch 3; ada
  error di bagian mana pun → perbaiki → simulasi ulang
  kumulatif sampai semua bersih. Catatan jujur: simulasi
  batch 2 kemarin hanya batch 2 + regresi parsial
  (gating/NPK/stok), bukan rantai penuh batch 1 — mulai
  batch 3 simulasinya kumulatif penuh.

## §15 — Ronde perbaikan B10–B14 + simulasi ulang kumulatif batch 3 (10 Nov 2026)

Aturan flow FINAL king 10 Nov 12:20 WIB (menggantikan "berhenti dan lapor"): JANGAN BERHENTI kalau ada error — balik perbaiki → audit lagi dengan simulasi → ulangi sampai SEMUA 100% pass; baru 100% pass, batch selesai.

### B10 — Save `stock.lot` via UI (farm_livestock, 18.0.1.2.1)
- `farm_livestock/models/farm_lot.py`: ketiga inverse (`_inverse_animal_count`, `_inverse_average_weight`, `_inverse_biological_stage`) defensif — no-op bila tidak ada Matter Tracking record atau nilai = default UI (0/0.0/kosong) atau sama dengan hasil compute; tetap `UserError` Legacy Write Block bila benar-benar menyimpang. Helper baru `_get_matter_tracking_record()` dipakai compute + inverse agar nilai pembanding identik.
- `farm_livestock/views/livestock_views.xml` (form inherit `stock.lot.livestock.form.inherit`): `animal_count`, `average_weight`, `biological_stage` jadi `readonly="1"` (client tidak mengirim field readonly saat Save); `is_animal` + `active_feeding_bom_id` masuk grup "Livestock Information" (sebelumnya tidak ada di view mana pun). `livestock_lot_views.xml` tidak diubah (kanban display-only).
- Verifikasi shell: create lot hewan + lot biasa via ORM dengan vals UI (termasuk `animal_count=0`) berhasil; write 7/123.4/'growing' pada lot tanpa tracking = no-op. Catatan: cabang raise belum terbukti live (test18 punya 0 record `stock.matter.tracking`).
- Detail: `PORTING.d/b10-b11.md`.

### B11 — cron pakan harian (farm_livestock, 18.0.1.2.1)
- `farm_lot.py:275`: `lot.active_feeding_bom_id.name` → `.display_name` (`mrp.bom` tidak punya `name`). Tidak ada pemakaian `.name` lain pada `mrp.bom` di file itu.
- Watch item: jebakan `_set_quantities` di dalam cron (PORTING.d §6.6) belum sempat tercapai karena B11 selalu rollback duluan — bisa muncul sesudah B11 diperbaiki; simulasi harus memperhatikan.
- Detail: `PORTING.d/b10-b11.md`.

### B12 — `depend_on_ids` operasi akuakultur (farm_aquaculture, 18.0.1.0.1)
- `farm_aquaculture/models/aquaculture_operation.py`: `depend_on_ids`/`dependent_ids` comodel jadi `'farm.aquaculture.operation'` + `recursive=True`, cerminan persis definisi core (`project_task.py:262-271`); relation table khusus dipertahankan; `dependent_ids` jadi inverse HIDUP di tabel relasi yang sama dengan kolom ditukar (definisi lama memakai tabel terpisah `farm_aqua_op_dependent_rel` yang tidak pernah terisi — dibiarkan yatim, harmless). Siklus tetap ditolak (`ValidationError`) — guard core utuh.
- Verifikasi di DB salinan `test18_b12b14` (pg_dump/restore, sudah di-drop; test18 tidak disentuh): create dengan `depend_on_ids=[(6,0,[])]` OK; `B.depend_on_ids=[A]` → `A.dependent_ids=[B]`.
- Detail: `PORTING.d/b12-b14.md`.

### B13 — hook telemetri tanpa `mail.thread` (farm_aquaculture + farm_livestock)
- `farm_aquaculture/models/aquaculture_isl.py` + `farm_livestock/models/livestock_isl.py`: tambah `'mail.thread'` ke `_inherit` `agri.isl.aquaculture.task` dan `agri.isl.livestock.task`. `report_incident` di mixin bersama tidak diubah; tidak ada view/chatter ditambah.
- Verifikasi shell (koordinator, independen): `hasattr(task, 'message_subscribe')` True; `handle_aquaculture_telemetry({'dissolved_oxygen': 2.0, 'temperature': 29.0})` pada task 1 → True tanpa crash, `agent_instruction_json` aerasi tertulis, aktivitas insiden 1 → 2 (id 488).
- Laten (dicatat, tidak diperbaiki): 4 model lain pemakai `report_incident` tanpa `mail.thread` (`farm.fermentation.order`, `farm.mushroom.production`, `farm.winery.production`, `farm.haccp.check`) — rawan crash sama; pola perbaikan yang sama di ronde berikut.
- Detail: `PORTING.d/b13.md`.

### B14 — form operasi tanpa tab (farm_aquaculture, 18.0.1.0.1)
- `farm_aquaculture/views/aquaculture_operation_views.xml`: view 2772 diberi `<field name="mode">primary</field>` (`inherit_id` + xpath tidak berubah — primary view dengan `inherit_id` pola standar Odoo); action 1024 diberi `view_id` eksplisit ke 2772 (belt-and-braces).
- Verifikasi di DB salinan: `get_view(view_type='form')` default mengandung `<notebook`, "Aquaculture Information", `pond_id`, `water_temperature`, `harvest_plan_date`, identik dengan `get_view(view_id=2772)`. Koreksi: Odoo 18 sudah tidak punya `BaseModel.fields_view_get` — yang setara `BaseModel.get_view(...)` (`addons/base/models/ir_ui_view.py:2801`).
- Detail: `PORTING.d/b12-b14.md`.

### Hasil simulasi ulang kumulatif ronde B3F (10 Nov 2026 siang WIB) — TIDAK BERSIH

Bagian 1 (rantai batch 1, data B3F): **LOLOS 9/9** (Fase A, screenshot 186–198, 0/0 error; tomat 5.480 kg, saus 16 kg, NPK 0 kg sesudah MO55 selesai). Bagian 2 (batch 2): **LOLOS** (IV26 murni UI → MO55 `done`; migrasi ISL run 1 +13 → 48, run 2 0, Confirm OFF → UserError; redirector MO55→48; spatial MO27 100%). Bagian 3: **B11 LOLOS** (cron selesai, MO58 bertahan, pakan 90→80 kg, sapi 12→13; jebakan `_set_quantities` §6.6 TIDAK muncul — watch item tertutup), **B13 LOLOS** (telemetri DO 2.0 → True, insiden 489, payload aerasi tertulis), **B14 LOLOS** (tab tampil, form 854 px) — tapi **B10 MASIH GAGAL** dan **B12 MASIH GAGAL**:

- **B10-residu** (`farm_processing/models/stock_lot.py:92`, di luar modul yang diperbaiki): inverse `_inverse_matter_life_stage` (`life_stage`) selalu raise `UserError: Legacy Write Block: Lifecycle stages are now managed dynamically by Matter Tracking (LPN/Vessel). Please update status on the active Matter Tracking container.` — client mengirim `life_stage` + `current_weight` saat Save lot via UI (lot hewan MAUPUN lot biasa). Fix farm_livestock 18.0.1.2.1 sendiri TERBUKTI bekerja (repro shell: vals UI pasca-fix OK). Perbaikan: pola defensif yang sama (no-op tanpa Matter Tracking / nilai default) atau `readonly="1"` di view, juga untuk `_inverse_current_weight` (baris 78) dan `_inverse_spatial_properties` (baris 85, GPS).
- **B12-residu** (`farm_aquaculture` + core `project_task.py:574-576`): `depend_on_ids` sudah benar (repro: `depend_on_ids=[(6,0,[])]` OK), tapi `parent_id` meledak: `ValueError: Field must be a many2one or many2many relation on itself: 'parent_id'` (constraint `_check_parent_id` → `_has_cycle`; client mengirim `parent_id=False` saat create; satu-satunya Traceback di log server ronde ini). Perbaikan: redefine `parent_id` comodel `'farm.aquaculture.operation'` + `recursive=True`, atau keluarkan dari form/view, atau override `_check_parent_id`.
- **Efek samping B14:** action 1024 kini langsung membuka form New — daftar operasi tidak terbuka dari menu (kemungkinan `view_id` eksplisit 2772); perlu verifikasi apakah menghapus `view_id` mengembalikan list sambil mempertahankan tab.
- **Efek samping B11 (desain cron, transparan):** cron tanpa filter lot memproses lot B3 lama 53 → MO57 `done`, pakan sapi B3 90→80 kg, sapi B3 10→11 ekor, `total_feed_consumed` lot 53 = 1.0.
- Sisa alur batch 3 selesai: MO pakan/panen sapi (MO56/59) + lele (MO61/62) via UI → `done`; event timbang 320 kg, breeding (gestation 0), env `comfort_index` 77.64; WQ log 2 → write-back operasi 9 (28.50/7.40/6.80, `good`, screenshot 256). Fase F regresi (screenshot 257–266): 0 pageerror + 0 console error, tanpa Oops.
- Detail lengkap + reproduksi minimal: `SIMULASI.md` § "Simulasi kumulatif batch 3 — ronde perbaikan B10–B14".

## §16 — Ronde perbaikan residu B10/B12 (10 Nov 2026)

Simulasi ulang B3F (ronde B10–B14) TIDAK BERSIH — 2 residu di luar modul yang diperbaiki ronde lalu. Aturan flow FINAL king 10 Nov 12:20: jangan berhenti — perbaiki → simulasi ulang sampai 100% pass.

### B10-residu — inverse `farm_processing` selalu raise (farm_processing, 18.0.1.1.3)
- `farm_processing/models/stock_lot.py`: helper baru `_get_matter_tracking_record()` (lookup via quant package, dipakai compute + inverse — pola sama dengan `farm_livestock`); `_compute_matter_physical_properties` direfaktor memakainya (perilaku compute tidak berubah: default tanpa tracking 0.0/0.0/0.0/`'juvenile'`). Ketiga inverse (`_inverse_current_weight`, `_inverse_spatial_properties`, `_inverse_matter_life_stage`) jadi defensif — no-op tanpa tracking / nilai default UI (0.0 bobot/GPS, stage kosong) / sama dengan hasil compute (toleransi float 1e-6; GPS bandingkan lat DAN lng); tetap `UserError` bila benar-benar menyimpang. Guard bersama: konteks `bypass_legacy_write_block` / registry belum ready → no-op.
- Deviasi sadar: TIDAK ada early-return `config['test_enable']` — `farm_processing/tests/test_stock_lot_bridge.py` menegaskan `UserError` pada tulis menyimpang dalam mode test; guard itu akan mematikan cabang raise tepat di test yang mengujinya.
- `farm_processing/views/stock_lot_views.xml`: `life_stage` (2×: statusbar + radio), `current_weight` (2×: gauge + biasa), `last_gps_lat`, `last_gps_lng` jadi `readonly="1"` (computed bridge non-stored — nilai user tidak pernah persisten). Tombol "Sync Plot from GPS" tidak diubah (masih raise bila diklik — aksi eksplisit, di luar scope).
- Verifikasi shell: repro asli `/tmp/b3f_repro_b10.py` REPRO-1 s.d. 5 SEMUA OK; F3 (lot DENGAN tracking buatan 120.5/`mature`/41.25/-73.98): read-back compute tepat, write sama/default → no-op, write menyimpang → `UserError` untuk ketiganya — **cabang raise TERBUKTI live**. Semua data TEST di-rollback (0 sisa).
- Detail: `PORTING.d/b10-residu.md`.

### B12-residu — `parent_id` + efek samping B14 (farm_aquaculture, 18.0.1.0.2)
- `farm_aquaculture/models/aquaculture_operation.py`: `parent_id` di-redefine comodel `'farm.aquaculture.operation'` (cerminan persis core `project_task.py:229-230`, string/index/domain/tracking — TANPA `recursive=True`, karena definisi core tidak punya flag itu; `recursive=True` hanya untuk computed field dengan dependensi-diri). FK DB di-repoint otomatis saat upgrade oleh `Registry.check_foreign_keys` (`REFERENCES farm_aquaculture_operation(id)`). `child_ids` ikut di-redefine sebagai inverse hidup (comodel sendiri, inverse `parent_id`) supaya tab Sub-tasks tidak menampilkan baris `project.task` asing.
- Dua temuan lanjutan dari kelas akar yang sama (tabrakan id antar tabel): (1) `_compute_subtask_count` core hardcode `self.env['project.task']._read_group` — operasi privat id 13 gagal "This task has sub-tasks, so it can't be private" karena `project.task` 13 punya anak; override cerminan core dengan `_read_group` ke model sendiri. (2) `_get_subtask_ids_per_task_id` core pakai SQL mentah `FROM project_task` — `unlink()` operasi id 19 gagal `MissingError`; override dengan nama tabel diganti; `_get_subtasks_recursively` juga dicerminkan (kasus kosong core mengembalikan recordset `project.task` kosong → `concat()` TypeError).
- Efek samping B14: `view_id` action 1024 dikosongkan eksplisit `<field name="view_id" eval="False" />` (`view_mode` tetap `list,form`, view 2772 tetap `mode=primary`). Pelajaran: sekadar menghapus baris `view_id` dari XML TIDAK membersihkan DB (nilai lama 2772 bertahan — terbukti di salinan sesudah upgrade pertama; baru `eval="False"` yang mengosongkannya).
- Verifikasi di DB salinan `test18_b12res` (sudah di-drop; test18 tidak disentuh): repro asli `/tmp/b3f_repro_b12.py` REPRO-1 s.d. 4 OK (create + unlink bersih); 28/29 PASS skrip verifikasi (1 FAIL artefak skrip); create B parent=A OK, `A.child_ids == [B]`, `subtask_count A == 1`, siklus ditolak, self-parent ditolak, 5 operasi privat `subtask_count == 0`, unlink parent ikut hapus anak tanpa menyentuh anak `project.task`, `get_view` form default mengandung notebook, action 1024 `view_id` NULL + `view_mode list,form`.
- Batasan dicatat: `_compute_depend_on_count` / `_compute_dependent_tasks_count` core masih hardcode `project.task` — angka count bisa salah karena tabrakan id, tapi display-only (bukan constraint). Detail: `PORTING.d/b12-residu.md`.

### Upgrade ronde ini
- farm_processing 18.0.1.1.2 → **18.0.1.1.3**; farm_aquaculture 18.0.1.0.1 → **18.0.1.0.2**. (Hasil upgrade + simulasi ulang kumulatif diisi sesudah simulasi.)

### Koreksi pasca-upgrade — guard `registry.ready` mematikan inverse di mode test (farm_processing 18.0.1.1.3, file sama, tanpa bump versi)
- Sesudah upgrade, suite `farm_processing` dijalankan di DB salinan `test18_b10test` (salinan sudah di-drop) sebagai konfirmasi akhir worker B10-residu: **sebelum koreksi 2 failed + 8 error; sesudah koreksi 1 failed + 8 error**.
- **Regresi yang ditemukan**: `test_stock_lot_bridge.TestStockLotBridge.test_decoupled_compatibility_bridge_and_write_locks` FAIL — `AssertionError: UserError not raised` pada `write({'current_weight': 250.0})` (test file baris 62). Repro shell di salinan yang sama MENAIKKAN UserError dengan benar — jadi akar bukan logika perbandingan, melainkan guard.
- **Akar (terbukti via log debug sementara)**: guard `not self.env.registry.ready` di ketiga inverse — selama run `--test-enable`, registry test melaporkan `ready=False`, sehingga inverse jadi no-op total di mode test. Guard itu dicopot dari ketiga inverse (`_inverse_current_weight`, `_inverse_spatial_properties`, `_inverse_matter_life_stage`); satu-satunya early-return kini flag konteks `bypass_legacy_write_block`. Alasan didokumentasikan di docstring `_inverse_current_weight` (tanpa guard `test_enable` MAUPUN `registry.ready`, karena keduanya menonaktifkan cabang raise yang ditegaskan test). Perilaku pra-B10-residu (inverse tanpa guard) sudah terbukti aman saat install batch 1–3 — pencopotan ini kembali ke baseline itu, bukan risiko baru.
- **Hasil sesudah koreksi**: bridge test LOLOS (0 kegagalan); server test18 di-restart agar memuat kode terkoreksi (8071 → 200, 0 traceback, versi tetap 18.0.1.1.3 — perubahan .py murni di dalam versi yang sama, tanpa bump).
- **Sisa 1 failed + 8 error = PRE-EXISTING, di luar area perubahan** (tidak satu pun traceback-nya menyentuh `stock_lot.py` / `aquaculture_operation.py` / `farm_lot.py`): FAIL `TestProcessingLogic.test_mass_balance_validation` (ekspektasi UserError tak terpenuhi); ERROR `test_advanced_processing` (null `mrp_workorder.product_uom_id`), `test_epic_135` (null `stock_move.name`), `test_farm_processing` setUpClass, `test_mass_balance`, `test_processing`, `test_processing_isl` (null `agri_isl_processing_production.total_loss_qty`), `test_processing_logic.test_traceability_linkage`, `test_converged_package` setUpClass (`KeyError: 'stock.package'` — test masih memakai nama model lama, padahal kode sudah pindah ke `stock.quant.package`). Perluasan scope memperbaikinya = ronde terpisah, bukan ronde residu ini.
- **Catatan run suite**: run pertama gagal load registry karena `partner_identification/tests/test_res_partner.py` mengimpor `odoo_test_helper` yang tidak ter-install (sisa evaluasi AgriOS) — diatasi dengan uninstall `partner_identification` HANYA di DB salinan; test18 tidak disentuh. Run test butuh port HTTP bebas (`--no-http --http-port=8079`) karena 8071 dipakai server live test bed.

## 17. Batch 4 — farm_iot + agri_iot + farm_weather (10 Nov 2026)

Tiga pekerja paralel (modul terpisah, tanpa tabrakan); catatan
lengkap di `PORTING.d/farm_iot.md` (330 baris),
`PORTING.d/agri_iot.md` (207 baris),
`PORTING.d/farm_weather.md` (242 baris).
Verifikasi + install oleh koordinator.

### 17a. Hasil install test18 — 24/24 modul farm `installed`

`agri_iot` **18.0.1.0.0**, `farm_weather` **18.0.1.0.0**,
`farm_iot` **18.0.1.2.0** — semua `installed`,
`installed_version = latest_version`. Total modul farm/agri
ter-install di test18: 28 (24 odoo-farm + 4 AgriOS lama dari
evaluasi 8 Nov). Server hidup lagi (PID 6604, 8071 → 200,
log server 0 Traceback).

### 17b. Scope batch 4 — yang ikut dan yang tidak

| Modul | Keputusan |
|---|---|
| `agri_iot` | Ikut. Depends hanya core (`base/web/mail/http_routing`) — tanpa pemangkasan. |
| `farm_iot` | Ikut. Depends (`farm_core/project/agri_iot/maintenance/stock/mrp`) semua ter-install — tanpa pemangkasan. |
| `farm_weather` | Ikut. Depends `farm_iot` **DIPANGKAS** (0 acuan ke `farm_iot`/`iiot.*` di kode di luar manifest — preseden persis §14c); kini hanya `farm_core`. Reversibel, didokumentasikan di manifest. |
| `farm_livestock_valuation` | Tetap ditangguhkan ke batch financial (§14b). |

### 17c. Perubahan per modul batch 4 (ringkas; detail di PORTING.d/)

- **farm_iot** — `2.1.0` → `18.0.1.2.0`. `agri_telemetry`
  diaktifkan lagi (satu-satunya definisi `agri.telemetry` di
  repo; tanpanya `farm.telemetry` gagal register — bug
  upstream yang juga ada di 19.0); `from . import wizard`
  ditambah (paket wizard tidak pernah di-import upstream —
  pola §14e.2); `models.Constraint` → `_sql_constraints`;
  `mrp.py` ditulis ulang (hook `_hook_post_start`/
  `_hook_pre_done` tidak ada di core mrp 18 → guard
  `try/except AttributeError`; `connection_state` →
  `connection_status`; write `iot_status` diselaraskan ke
  seleksi mixin farm_operation); wizard `farm.device.command`
  diperbaiki (`create()` memakai field tak ada `params`/
  `execution_time_ms` → `payload`/`execution_latency`);
  field baru `maintenance.equipment.is_drone` (dirujuk domain
  `drone_id` tapi tidak didefinisikan di repo mana pun);
  guard `'farm.csa.subscription' in self.env` (soft ref ke
  `farm_csa`, bukan depends); dedup definisi ganda identik
  (`farm.location` + `iiot.device` digital-twin fields, 2×
  → 1×). ACL: +5 baris, audit AST 17/17 model konkret
  ter-cover. De-CJK penuh. `i18n/id_ID.po` baru 208 entri
  (203 diterjemahkan).
- **agri_iot** — `19.0.1.0.0` → `18.0.1.0.0`. `Constraint` ×4
  → `_sql_constraints`; `send_command(action, **params)` →
  `send_command(action=None, **params)` (tombol UI `type=
  "object"` memanggil tanpa argumen — signature lama pasti
  `TypeError`); `import requests` + `UserError` ditambah di
  `iiot_gateway.py` (dipakai `action_ping`/`action_sync_
  subscriptions` tapi tak pernah di-import → `NameError`);
  `import jsonpath_ng` top-level → defensif (`try/except
  ImportError`); `env['farm.command.log']` di controller
  dijaga `try/except KeyError` (model milik `farm_iot`);
  view baru `iiot_telemetry_views.xml` (model `iiot.telemetry`
  + ACL ada upstream tapi tanpa view/action/menu); ace mode
  `'json'` → `'javascript'` (B6); `statusbar_visible`
  diperbaiki; grup kosong "Telemetry Rules" diisi +
  sub-view `<list>`; page firmware diisi `update_ids`.
  ACL: tidak diubah — sudah lengkap (7/7 model, 14 aturan).
  `i18n/id_ID.po` baru 205 entri. **paho-mqtt: kode Odoo
  TIDAK mengimpor paho sama sekali** (grep 0 di models/ +
  controllers/) — paho hanya di `mqtt_bridge/` standalone.
- **farm_weather** — `1.0` → `18.0.1.0.0`. Bug upstream:
  cron memanggil `model._cron_fetch_forecast()` yang TIDAK
  ADA → `model.action_fetch_weather_all_locations()`;
  `_trigger_disaster_alert()` memanggil
  `env['farm.disaster.incident']` tanpa guard (model hanya
  ada di `farm_disaster_risk`, bukan batch 4) → guard
  `if 'farm.disaster.incident' in self.env`; typo `Metrix`
  → `Metrics`; `℃` → `°C`. ACL: tadinya hanya header → +2
  baris, audit AST 0 model tanpa aturan. `i18n/id_ID.po`
  baru 50 entri. API: OpenWeatherMap 5-day/3-hour
  (`requests`, key di `ir.config.parameter`
  `farm_weather.api_key`, tidak ada key di kode); lokasi dari
  `farm.location` parcel ber-GPS; tanpa key fetch = log
  warning + return, 0 exception.

### 17d. Perbaikan koordinator saat install (10 Nov 2026)

1. **Symlink belum dibuat** — ketiga modul belum ada di
   `custom_addons/` test bed (pola batch 1–3: symlink dari
   `~/workspace/odoo-farm-port-18/`); `update_list()` saja
   tidak cukup. Fix: symlink `agri_iot`/`farm_iot`/
   `farm_weather`, baru `update_list()` + install.
2. **`agri_iot` gagal `ParseError` di
   `security/iiot_security.xml:11`** — `res.groups` di Odoo
   18 TIDAK punya field `sequence` (baru ada di 19).
   Terverifikasi dari source (`res_users.py`, `Groups`:
   `sequence` tidak ada di `_fields`). Fix: hapus
   `<field name="sequence">` di kedua grup, tambah
   `category_id` → `ir_module_category_iiot`.
3. **`farm_iot` gagal `No matching record found for external
   id 'model_farm_telemetry'`** — `models/farm_telemetry.py`
   ada tapi TIDAK pernah di-import di `models/__init__.py`
   (bug upstream yang sama kelasnya dengan `agri_telemetry`
   yang sudah diperbaiki pekerja). Fix: tambah
   `from . import farm_telemetry` (sesudah `agri_telemetry`,
   karena `farm_telemetry` inherit `agri.telemetry`).
4. **`jsonpath-ng` di-install di venv test bed**
   (`pip install jsonpath-ng`) — dibutuhkan evaluasi aturan
   telemetri `agri_iot` (sudah dibuat defensif oleh pekerja,
   tapi tanpa library ini rule mati). Bukan syarat install.

### 17e. Infrastruktur MQTT untuk simulasi (disiapkan koordinator)

- **Arsitektur (terverifikasi):** Odoo TIDAK mengimpor paho.
  `agri_iot/mqtt_bridge/` adalah service FastAPI standalone
  (fastapi 0.104.1, uvicorn, paho-mqtt 1.6.1, httpx,
  pydantic 1.10.13, python-dotenv, aiosqlite) yang bicara
  MQTT ke broker di satu sisi dan HTTP webhook ke Odoo di
  sisi lain (`/iiot/config`, `/iiot/webhook/{device_id}`,
  `/iiot/command/{device_id}`, `/iiot/gateway/register`,
  `/iiot/gateway/config`). Topik telemetri:
  `telemetry/{device}/data`.
- **Venv bridge:** `~/workspace/odoo-farm-port-18/bridge-venv/`
  (Python 3.12) — requirements bridge + `amqtt` (broker MQTT
  murni-Python; mosquitto tidak ada di sandbox:
  `apt-cache policy` kosong). Verifikasi:
  `import paho.mqtt.client, fastapi, amqtt` OK.
- **`.env` bridge WAJIB diisi sebelum uji end-to-end:**
  default vendor masih contoh (`mqtt.factory.com:8883` TLS,
  `localhost:8000/8069`) — override ke broker lokal
  (`127.0.0.1:1883`, tanpa TLS) dan Odoo test bed
  (`http://127.0.0.1:8071`).
- **Laten B13 (dicatat, BUKAN dikerjakan di batch 4):** 4
  model lain pemakai `report_incident` tanpa `mail.thread`
  (`farm.fermentation.order`, `farm.mushroom.production`,
  `farm.winery.production`, `farm.haccp.check`) — rawan crash
  sama; itu scope batch 6.

### 17f. Batasan yang diketahui (untuk simulasi batch 4)

- `iiot.telemetry` tidak pernah ditulis kode mana pun —
  webhook hanya update device shadow + jalankan rules; menu
  Telemetry Data akan kosong sampai ada kode penulisnya (gap
  upstream, dibiarkan).
- Test yang akan gagal bila suite dijalankan (bukan blocker
  install): `agri_iot/test_epic_006.py` (merujuk
  `agri.telemetry`/`farm.automation.rule` — `agri.telemetry`
  kini ada berkat §17c, `farm.automation.rule` ada di
  `farm_iot`; perlu dibuktikan saat simulasi), `farm_iot`
  test `stock.package` ×3 (`test_high_throughput_
  concurrency`, `test_iot_sync_pipeline`,
  `test_iot_wal_buffering`) + `env['agri.digital.twin']`
  (`test_integration_flows.py:46`), `farm_weather/
  test_epic_069.py` (merujuk `agri.weather.sensor`/
  `iiot.device`/PLC yang tidak ada).
- `farm_weather`: parsing JSON OWM nyata belum terbukti
  (butuh mock/key live); akun OWM baru kadang hanya dapat
  paket 3.0, bukan 2.5 — bila key baru 401, endpoint perlu
  ditinjau. Ikon FA4 di `_map_icon_to_fa` mungkin tidak
  render di Odoo 18.
- `farm_iot`: aksi `method`/webhook korelasi adalah stub;
  bulk insert melewati `create()`; cron WAL membuat
  perangkat fallback otomatis; `farm.telemetry` tanpa view
  sendiri; wizard `farm.device.command` tanpa view/action
  dan 2 action tanpa menu (Storage Monitoring, IoT Device
  Mappings) dibiarkan dormant.

### 17g. Status perbaikan B15–B23 + blocker baru B24 — simulasi ulang B4R1 (10 Nov 2026)

Simulasi ulang kumulatif B4R1 (detail + bukti: `SIMULASI.md` §
"Batch 4 — Ronde perbaikan B15–B23, simulasi ulang kumulatif
(B4R1)"). **B15–B23 SEMUA LOLOS (9/9)** di test18
(`agri_iot` 18.0.1.0.1, `farm_iot` 18.0.1.2.1, `farm_weather`
18.0.1.0.1, semua `installed`): B15 device via UI tanpa
`device_id` (id 9, auto `simulasi-b4r1-sn-001`); B16 kelima
endpoint `type='json'` → `result.status=success` (tanpa
`jsonrequest`); B17 subscribe `telemetry/+/data`; B18 bridge
membaca `result` + E2E MQTT → shadow/last_telemetry/rule di
Odoo, 0 fallback persistence; B19 bridge start bersih,
`/health` 200; B20 telemetri T=40 tersimpan saat gateway mati
(log `AUTOMATION (B20)` + chatter FAILED task 12); B21 telemetri
T=50 tersimpan + activity korelasi 504/505; B22 `warning_type`
benar saat create 5/5 (storm/frost/heat/wind/normal); B23
disaster alert activity 503 dengan `res_model_id` benar.
Kumulatif ikut LOLOS: batch 1 9/9, batch 2 (intervensi UI IV72 +
MO159 + ISL 79→95), batch 3 (lot sapi 220, MO160–168, B13
activity 506), render F7 17/17, 0 pageerror + 0 console error
di semua skrip browser B4R1.

**Blocker BARU B24 (bukan regresi B15–B23):** command Odoo →
bridge SELALU HTTP 500 — `agri_iot/mqtt_bridge/main.py:89`
(`odoo_webhook_callback`, cabang `event == "command"`) meng-`await`
`self.mqtt_service.send_device_command(...)` padahal method itu
mengembalikan bool (sync) → `TypeError: object bool can't be used
in 'await' expression`. Repro: bridge hidup,
`POST /api/v1/webhook {"event":"command","payload":
{"device_id":"simulasi_b4_sn_001","action":"power_on",
"params":{"state":"on"}}}` → 500 `Internal Server Error`;
via Odoo `POST /iiot/command/simulasi_b4_sn_001` → `result=
{"error":"... Gateway rejected command: Internal Server Error",
"status":"error"}`. Perbaikan: hapus `await` di baris 89 (atau
jadikan `send_device_command` async). Sampai B24 diperbaiki,
batch 4 **TIDAK BERSIH** — gerbang batch 5 tetap tertutup.

**Simulasi ulang B4R2 (10 Nov 2026, sesudah perbaikan B24 —
detail: `SIMULASI.md` § "Batch 4 — Simulasi ulang jalur command
(B4R2)"): B24 LOLOS 100%.** Hapus `await` di 5 baris
`main.py` (89/170/227/349/364) terverifikasi: 0×
`await self.mqtt_service`; `POST /iiot/command/
simulasi_b4_sn_001` → `result.status=success`, subscriber MQTT
menerima `{"action":"power_on","params":{"state":"on"}}`,
`farm.command.log` 1→2; webhook langsung 200 success,
`POST {}` 200 ignored, `/command/send` 200, OTA
`firmware_update` 200 + payload diterima subscriber; config
publish end-to-end via MQTT (token salah → error di
`iiot/config/SIMULASI-B4-SN-001`, token benar → config lengkap
di `iiot/config/simulasi_b4_sn_001`); B20 dengan bridge hidup:
telemetri T=40 tersimpan (id 11), command TERKIRIM (log id 4,
chatter sukses 26630 di task 12 — kebalikan B4R1); F7 17/17,
0 pageerror + 0 console error; stok batch 1–3 utuh; gateway
tetap 1. **Tetapi batch 4 MASIH TIDAK BERSIH — blocker BARU
B25:** tombol Power On/Power Off/Reset di form device
(`iiot_device_views.xml:52-54`) SELALU dialog "Oops!" —
`TypeError: IiotDevice.send_command() missing 1 required
positional argument: 'action'` (repro 2×, screenshot 515/516).
Akar: `farm_iot/models/iiot_device.py:23` meng-override
`def send_command(self, action, **params)` tanpa default,
menimpa base `agri_iot/models/iiot_device.py:154`
(`action=None`, dibuat agar tombol UI tanpa argumen jalan).
Jalur controller + rule tidak kena (argumen eksplisit).
Perbaikan: beri default `action=None` di override `farm_iot`.
Sampai B25 diperbaiki, gerbang batch 5 tetap tertutup.

**Simulasi ulang B4R3 (10 Nov 2026, sesudah perbaikan B25 —
detail: `SIMULASI.md` § "Batch 4 — Simulasi ulang tombol
device (B4R3)"): B25 hanya SEPARUH LOLOS.** `farm_iot`
18.0.1.2.2 terinstall: tombol **Power On + Power Off LOLOS**
(subscriber MQTT menerima `{"action": "power", "params":
{"state": "on"/"off"}}`, `farm.command.log` id 7, 8
`command='power'`, dispatched — action final tercatat,
bukan None). Tetapi tombol **Reset + Send Reset Command
MASIH dialog "Oops!"** — blocker BARU **B26** (`TypeError`
baru, 4× repro): `send_command() got multiple values for
argument 'action'` (`farm_iot/models/iiot_device.py:47`,
panggilan `super()`). Akar: perbaikan B25 mengambil
`params` dari `env.context.get('params')`; bila context
tombol tanpa `params` (Reset hanya `{'action': 'reset'}`),
yang terambil adalah `params` web client Odoo 18
(`{debug, resId, action: 1041, actionStack}`) yang
mengandung kunci `action` → bentrok dengan argumen
posisional `'reset'`. Pola yang sama ada di base
`agri_iot/models/iiot_device.py:154-163`. Perbaikan:
jangan ambil `params` mentah dari context — saring
kunci-kunci client (`action`/`debug`/`resId`) sebelum
`super()`. B24 (curl, envelope JSON-RPC), B20 (bridge
hidup, telemetri 12 + log 10 + chatter 26637), F7 17/17,
stok batch 1–3, dan kebersihan infra semuanya LOLOS —
tidak ada regresi. Batch 4 **MASIH TIDAK BERSIH** — gerbang
batch 5 tetap tertutup sampai B26 diperbaiki.

**Simulasi ulang B4R4 (10 Nov 2026, sesudah perbaikan B26 —
detail: `SIMULASI.md` § "Batch 4 — Simulasi ulang tombol
Reset (B4R4)" + `PORTING.d/b26.md`): B26 LOLOS, batch 4
BERSIH 100%.** `agri_iot` 18.0.1.0.2 + `farm_iot`
18.0.1.2.3 terinstall: tombol **Reset + Send Reset Command
TIDAK LAGI dialog "Oops!"** — subscriber MQTT menerima
`{"action": "reset", "params": {}}` untuk keduanya,
`farm.command.log` id 16, 17 `command='reset'`,
dispatched (bukan None, bukan 1041); **0× `TypeError`**
di log server. Tidak ada regresi: Power On/Off (log id
14, 15 `power`), B24 curl (success, log id 18), B20
(telemetri 13 + log id 19 + chatter 26647), F7 17/17,
stok batch 1–3 utuh, infra bersih — **0 pageerror + 0
console error**. Gerbang batch 5 **TERBUKA**.

## 18. Batch 5 — farm_hr + farm_waste_mgmt + farm_financial* + farm_esg* (10 Nov 2026)

Empat pekerja paralel (modul terpisah, tanpa tabrakan); catatan
lengkap di `PORTING.d/farm_hr.md`, `PORTING.d/farm_waste_mgmt.md`,
`PORTING.d/batch5_financial.md`, `PORTING.d/farm_esg_batch5.md`,
`PORTING.d/farm_esg_batch5_problematic.md`. Verifikasi + install
oleh koordinator. Alat migrasi: `odoo-module-migrator` 0.5.0 dan
`oca-port` keduanya menolak source 19.0 (migrator `-i` maks 17.0;
oca-port butuh repo git + branch 18.0 upstream) — sapuan mekanis
manual seperti batch 1–4.

### 18a. Hasil install test18 — 45/45 modul farm `installed`

21 modul batch 5 `installed`, `installed_version =
latest_version` (19× `18.0.1.0.0`, 2× `18.0.1.0.1` — lihat
§18d). Total modul farm/agri ter-install di test18: 45 (24
batch 1–4 + 21 batch 5; 4 AgriOS lama dari evaluasi 8 Nov
ter-install terpisah, bukan hitungan ini). Server di-restart
(PID 16982, 8071 → 200, log `/tmp/odoo18-server-b5.log`
0 Traceback).

### 18b. Scope batch 5 — yang ikut dan yang tidak

| Modul | Keputusan |
|---|---|
| `farm_hr`, `farm_waste_mgmt` | Ikut. Depends bersih (hr/hr_attendance/maintenance standar; farm_core/farm_livestock/farm_quality). |
| `farm_financial`, `farm_financial_basic`, `farm_financial_clearing`, `farm_financial_government`, `farm_financial_insurance` | Ikut. Depends bersih. Government modul cangkang kosong upstream (tanpa model/view/menu). |
| `farm_financial_credit` | Ikut. Depends `farm_multi_farm_financial` DIPANGKAS (0 acuan kode); `sale` DITAMBAH (field `sale_order_id`). |
| `farm_financial_valuation` | Ikut. Depends `farm_ecology` DIPANGKAS (0 acuan model; `gep_score` di-guard via `getattr`, nilai nyata terbaca bila farm_ecology kelak dipasang). |
| `farm_livestock_valuation` | Ikut — keluar dari penangguhan §14b (valuation kini ada). |
| `farm_esg`, `farm_esg_carbon`, `farm_esg_matter`, `farm_esg_fair_trade`, `farm_esg_report`, `farm_esg_risk`, `farm_esg_social` | Ikut. Depends bersih (carbon butuh environmental — ter-install batch ini). |
| `farm_esg_environmental`, `farm_esg_circular`, `farm_esg_compliance`, `farm_esg_sustainability` | Ikut — SEMUA TRIM + PORT, 0 ditangguhkan (dugaan compliance ditangguhkan tidak terbukti sesudah audit pemakaian depends). Lihat §18c. |
| `farm_multi_farm_financial`, `farm_ecology`, `farm_equipment`, `farm_supply_analytics`, `farm_supply_logistics`, `farm_subsidy` | TIDAK di-port (batch 6 / luar scope). Hanya depends-nya yang dipangkas + guard. |

### 18c. Perubahan per modul batch 5 (ringkas; detail di PORTING.d/)

- **farm_hr** — `1.0` → `18.0.1.0.0`. `project.task` 18 tanpa
  `analytic_account_id` → pakai `task.project_id.account_id`;
  `account.analytic.line` 18 tanpa `product_id`/`employee_id`;
  `hr.employee` 18 tanpa `address_id`/`address_home_id` →
  `work_contact_id.property_account_payable_id` /
  `user_id.partner_id or work_contact_id`; field `color`
  ditambah ke `farm.agri.skill` (many2many_tags
  `color_field`); `maintenance` DITAMBAH ke depends
  (`maintenance.equipment` di `service_team.py`); sequence
  baru `farm.labor.payment` (LAB/…) + `farm.time.bank`
  (TB/…); ACL +8 baris; de-CJK 209 → 0; `i18n/id_ID.po` 98
  entri.
- **farm_waste_mgmt** — `1.0` → `18.0.1.0.0`. Modul paling
  China-spesifik di batch 5: MOARA → Ledger generik
  (`action_generate_moara_ledger` → `action_generate_ledger`,
  report `MOARA Manure Ledger` → `Manure Ledger`, QWeb
  di-English-kan); bug render `doc.with_context(lang=
  doc.lang)` padahal model tanpa field `lang` → baris
  dihapus; tanggal `'%Y年%m月%d日'` → `'%Y-%m-%d'`;
  `binding_model_id` report dari alias deprecated
  `farm.manure.ledger` → `model_agri_manure_ledger`; field
  `input_type` (hanya didefinisikan upstream di
  `farm_supply_procurement`, belum di-port) didefinisikan
  lokal di `product.template` — **wajib direkonsiliasi saat
  `farm_supply_procurement` di-port (batch 6)**; sequence
  baru `agri.manure.batch` (MNR/…) + `agri.manure.ledger`
  (MNL/…); ACL +5 baris; de-CJK 202 → 0; `i18n/id_ID.po`
  85 entri.
- **farm_financial** — `19.0.1.0.0` → `18.0.1.0.0`.
  `models.Constraint` → `_sql_constraints`; CSV +2 baris;
  `i18n/id_ID.po` 57 entri.
- **farm_financial_basic** — `19.0.1.0.0` → `18.0.1.0.0`.
  Label `Per Mu (Chinese Acre)` → `Per Mu`; guard
  `purchase.order`/`sale.order` + `hasattr(po,
  'agri_task_id')` di `AccountMove.create`; guard
  `mrp.bom.analytic_account_id` di `action_allocate_costs`;
  guard `lot_ids` di `project.task` + `lot_id` di
  `account.analytic.line`; action
  `project_task_action_view_analytic` yang dirujuk tapi
  tidak ada didefinisikan; CSV +5 baris; `i18n/id_ID.po`
  136 entri.
- **farm_financial_clearing** — `19.0.1.0.0` →
  `18.0.1.0.0` (LGPL-3 dipertahankan). Hanya bump versi +
  `i18n/id_ID.po` 5 entri; tanpa perubahan kode.
- **farm_financial_credit** — `19.0.1.0.0` →
  `18.0.1.0.0`. Depends `farm_multi_farm_financial`
  dipangkas; `sale` ditambah; `security/ir_rule.xml`
  (ada di disk, tidak termuat upstream) diaktifkan; bug
  upstream: `_compute_credit_rating`
  (`state='validated'` → `'valid'`, `order='rating_date
  desc'` → `'evaluation_date desc'`), `order='score_date
  desc'` ×3 → `evaluation_date desc`, guard `lot_id` di
  `agri.biological.asset`, field `is_broker` ditambah ke
  `res.partner`, guard `quality.control.standard`, UoM
  `jin` dihapus; CSV +12 baris; `i18n/id_ID.po` 328 entri.
- **farm_financial_government** — `19.0.1.0.0` →
  `18.0.1.0.0`. Modul cangkang kosong (upstream 19.0 juga
  tanpa model); `from . import *` diganti komentar;
  `i18n/id_ID.po` 2 entri; CSV tetap header saja.
- **farm_financial_insurance** — `19.0.1.0.0` →
  `18.0.1.0.0`. Manifest + author de-CJK; CSV +3 baris;
  `i18n/id_ID.po` 102 entri; tanpa perubahan kode.
- **farm_financial_valuation** — `19.0.1.0.0` →
  `18.0.1.0.0`. Depends `farm_ecology` dipangkas (lihat
  §18b); `models.Constraint` → `_sql_constraints`;
  `create()` fix tanggal string → `fields.Date.to_date`
  (kelas bug §11a); label "(Anji Model)" digeneralisasi;
  CSV +2 baris; `i18n/id_ID.po` 95 entri.
- **farm_livestock_valuation** — `19.0.1.0.0` →
  `18.0.1.0.0` (LGPL-3 dipertahankan). Keluar dari
  penangguhan §14b; `_get_specialized_algorithms` tidak ada
  di platform tapi subclass sudah guard `hasattr`; file
  baru `security/ir.model.access.csv` (+2 baris); `.py`
  0 baris berubah; `i18n/id_ID.po` 11 entri.
- **farm_esg** — `1.0` → `18.0.1.0.0`. `models.Constraint`
  ×2 → `_sql_constraints`; CSV +6 baris; `i18n/id_ID.po`
  204 entri.
- **farm_esg_carbon** — `1.0` → `18.0.1.0.0`. Depends
  didedup; `farm_esg_environmental` DIPERTAHANKAN (pemilik
  `agri.carbon.ledger` yang di-extend); bug upstream
  `action_tokenize_offset` membaca `ledger.co2e_amount`
  yang tidak ada → `abs(total_co2e)`; CSV +1 baris
  (`farm.exchange.asset`); `i18n/id_ID.po` 24 entri.
- **farm_esg_matter** — `19.0.1.0.0` → `18.0.1.0.0`.
  Tambah `'license': 'AGPL-3'` (upstream tanpa kunci);
  0 model konkret → tanpa CSV (preseden
  farm_livestock_matter); `i18n/id_ID.po` 2 entri.
- **farm_esg_fair_trade** — `19.0.1.0.0` →
  `18.0.1.0.0`. Author + docstring de-CJK; CSV +4 baris;
  `i18n/id_ID.po` 102 entri.
- **farm_esg_report** — `19.0.1.0.0` → `18.0.1.0.0`.
  Author + docstring de-CJK; CSV +3 baris; `i18n/id_ID.po`
  168 entri.
- **farm_esg_risk** — `19.0.1.0.0` → `18.0.1.0.0`.
  `widget="ace"` mode `'json'` → `'javascript'` ×4
  (jebakan B6); `report_language` default `zh_CN` →
  `en_US` + opsi `id_ID`; label `(CNY)` + `¥` → simbol
  mata uang company; bug upstream
  `action_validate_data` menulis `validation_status=
  'requires_review'` yang tidak ada di seleksi (nilai
  ditambah) dan `action_reset_kpi_target` menulis
  `baseline_year` yang tidak ada (field ditambah); CSV
  +11 baris; `i18n/id_ID.po` 499 entri.
- **farm_esg_social** — `19.0.1.0.0` → `18.0.1.0.0`.
  Author + docstring de-CJK; CSV +1 baris; `i18n/id_ID.po`
  24 entri.
- **farm_esg_environmental** — `19.0.1.0.0` →
  `18.0.1.0.1` (lihat §18d). Depends `farm_ecology` +
  `farm_equipment` dipangkas (0 acuan `farm_ecology`; 1
  file `farm_equipment` dihapus + import-nya); guard
  `KeyError` phantom
  `farm.sustainability.carbon.footprint.calculation`;
  fragmen menuitem rusak di `views/menu.xml` dibersihkan;
  ACL +12 baris; `i18n/id_ID.po` 143 entri.
- **farm_esg_circular** — `19.0.1.0.0` → `18.0.1.0.0`.
  Depends `farm_equipment` dipangkas (0 acuan ke
  `farm.equipment.*`; equipment hanya core
  `maintenance.equipment` via farm_operation); `'hr'`
  ditambah (`hr.department` Many2one); guard
  `env['agri.sustainability.algorithms']` + `getattr`
  field impact produk; ACL +16 baris; `i18n/id_ID.po`
  146 entri.
- **farm_esg_compliance** — `19.0.1.0.0` →
  `18.0.1.0.1` (lihat §18d). Depends
  `farm_supply_analytics` / `farm_supply_logistics` /
  `farm_subsidy` / `farm_financial` / `farm_esg_risk` /
  `account` dipangkas (0 acuan Python; satu-satunya
  sentuhan 1 action + 1 menu subsidy, dihapus);
  `models.Constraint` → `_sql_constraints`; guard
  `farm.vra.prescription` / `farm.biological.twin`;
  `kg/mu` → `kg/ha`; ACL +20 baris; `i18n/id_ID.po`
  277 entri.
- **farm_esg_sustainability** — `19.0.1.0.0` →
  `18.0.1.0.0`. Depends `farm_financial` +
  `farm_esg_carbon` dipangkas (0 acuan); 2 pasang view +
  2 action + 2 menu Ecological Records dihapus
  (`farm_ecology`); guard phantom carbon-footprint ×3;
  ACL +10 baris; `i18n/id_ID.po` 96 entri.

Total `i18n/id_ID.po` batch 5: ±3.800 entri (HR/waste 183,
financial 736, ESG inti 1.023, ESG bermasalah 662,
ditambah entri manifest). Total porting batch 1–5: ±6.400
entri.

### 18d. Perbaikan koordinator saat install (10 Nov 2026)

1. **M2M table collision — `farm_esg_environmental`
   gagal install** (`TypeError: Many2many fields
   esg.environmental.report.assessment_ids and
   esg.performance.report.assessment_ids use the same table
   and columns`). Akar: `esg.environmental.report`
   (`_name` baru + `_inherit = ['esg.performance.report']`,
   prototype inheritance) menyalin field `assessment_ids` /
   `target_ids` verbatim beserta relation table eksplisitnya
   (`esg_performance_report_esg_assessment_rel` /
   `esg_performance_report_esg_target_rel`) → registry 18
   menolak duplikat tabel+kolom. Fix: redefine kedua field
   di child dengan relation table BERBEDA
   (`esg_environmental_report_esg_assessment_rel` /
   `esg_environmental_report_esg_target_rel`, comodel +
   kolom + label sama). Satu-satunya prototype-inherit
   bermasalah di batch 5 (audit: tidak ada `_inherit`
   lain ke `esg.target`/`esg.assessment`). Versi →
   `18.0.1.0.1`.
2. **File model tidak di-import — CSV gagal diproses.**
   `esg_environmental_tracker.py` (model
   `esg.environmental.tracker`) ada di disk tapi tidak ada
   di `models/__init__.py` (bug upstream) → CSV merujuk
   `model_esg_environmental_tracker` yang tidak ada.
   Fix: tambah `from . import esg_environmental_tracker`.
   (Pola yang sama dengan `wizard/` + `farm_telemetry`
   batch 3/4 — selalu audit `__init__.py` vs file di disk
   bila CSV gagal diproses.)
3. **Load-order sirkular `farm_esg_compliance` —
   `ParseError: menu.xml:58`.** Upstream memuat
   `views/menu.xml` dua kali (ke-3 DAN terakhir); copy
   pertama gagal karena 11 menuitem merujuk action yang
   baru didefinisikan di views files sesudahnya. Memindah
   seluruh file ke akhir justru memecahkan
   `esg_compliance_views.xml:113` (menuitem di sana
   menggantung di `menu_esg_operations` yang didefinisikan
   menu.xml). Fix: SPLIT — `menu.xml` hanya kategori +
   record overrides (load awal); 11 menuitem ber-action
   pindah ke file baru `views/menu_actions.xml` (load
   terakhir). Versi → `18.0.1.0.1`. Pelajaran: bila dua
   file XML saling merujuk (menu ↔ action), pisah file
   menurut arah dependensi, jangan hanya reorder.

### 18e. Batasan yang diketahui (untuk simulasi batch 5)

- `farm_financial_government` tanpa model/view/menu
  (cangkang kosong upstream).
- `farm_financial_valuation`: `test_gep_valuation.py`
  akan gagal bila suite dijalankan (butuh `farm_ecology`);
  nilai GEP nyata terbaca otomatis bila farm_ecology
  kelak dipasang.
- `farm_waste_mgmt`: `input_type` di `product.template`
  didefinisikan lokal — wajib direkonsiliasi saat
  `farm_supply_procurement` di-port (batch 6).
- `farm_hr`: `action_approve` no-op diam-diam bila project
  task tanpa analytic account.
- `farm_esg_circular`: biogas `action_push_to_carbon_ledger`
  menulis `'total_co2e'` langsung ke field computed
  (redundan — compute menimpa saat create; dibungkus
  try/except).
- Model phantom yang di-guard (bukan blocker): 
  `farm.sustainability.carbon.footprint.calculation`,
  `farm.vra.prescription`, `farm.biological.twin` — guard
  tidak merugikan bila pemiliknya muncul di batch 6.
- `farm_esg_compliance`: menu Subsidies dihapus bersama
  trim (kembali saat `farm_subsidy` di-port, batch 6).

## Ronde perbaikan B27–B29 (B5R1) (10 Nov 2026)

Perbaikan blocker simulasi kumulatif batch 5 (SIMULASI.md §B28/B29).
Tiap perbaikan diverifikasi di DB salinan test18 (bukan test18),
lalu DB salinan di-drop. test18 TIDAK di-upgrade di ronde ini
(upgrade + simulasi ulang kumulatif = koordinator).

### B27 — auto-worklog hook (a–e) — DIPERBAIKI ✅

- File:
  `agri_intervention/models/agri_intervention_base.py`
  (pemetaan bersama + savepoint `_run_plugins`),
  `agri_intervention/models/intervention_plugins.py`
  (plugin labor defensif),
  `farm_operation/models/agri_intervention_mixin.py`
  (`_create_auto_worklog_from_hook` defensif).
- Akar (persis SIMULASI.md §B27): `_create_auto_worklog_from_hook`
  (mixin) dan duplikatnya di plugin labor memasukkan
  `intervention_type` mentah ke `farm.worklog.work_type` yang
  seleksinya hanya {tillage, sowing, harvesting, packaging,
  feeding}; dan memasukkan `employee_id`/`task_id` yang bisa null
  (keduanya NOT NULL di `farm.worklog`).
- Fix (minimal, logika bisnis lain tidak diubah):
  1. Pemetaan tunggal `WORKLOG_WORK_TYPE_BY_INTERVENTION_TYPE` di
     `agri_intervention_base.py` + method
     `AgriInterventionBase._get_worklog_work_type()`: hanya
     tillage→tillage, sowing→sowing, harvesting→harvesting,
     feeding→feeding. Tipe tanpa padanan (fertilizing, irrigation,
     protection, aerial_spraying, medical, process) TIDAK membuat
     worklog — dicatat di log info, bukan crash (B27c/B27d).
     Dipakai bersama oleh mixin dan plugin labor supaya tidak drift.
  2. Kedua pembuat worklog kini DEFENSIF: lewati pembuatan bila
     `work_type` tak ada padanan, bila `employee_id` null (user
     tanpa employee, mis. shell user 1 — B27b), atau bila
     `agri_task_id` null (intervensi tanpa task — B27a/B27e).
     Bukan IntegrityError lagi.
  3. `_run_plugins` membungkus tiap plugin call dalam
     `self.env.cr.savepoint()`: IntegrityError satu plugin tidak
     lagi meng-abort transaksi pemanggil (akar B27e — ValueError
     terjadi saat validasi Python sebelum SQL sehingga transaksi
     selamat, tapi IntegrityError terjadi saat SQL execute sehingga
     transaksi abort walau exception ditangkap Python). UserError
     tetap diteruskan (gating disengaja); tulisan parsial plugin
     yang gagal ikut di-rollback oleh savepoint.
  4. `_create_auto_worklog_from_hook` (mixin, jalur langsung
     `_hook_post_done` — B27c) juga dibungkus savepoint +
     try/except + log warning: hook worklog yang gagal dengan cara
     apa pun tidak pernah menggagalkan penyelesaian MO.
- Versi: `agri_intervention` `18.0.1.0.1` → `18.0.1.0.2`;
  `farm_operation` `18.0.1.2.7` → `18.0.1.2.8`.
- Verifikasi (DB salinan `test18_b27fix` via pg_dump dari test18;
  upgrade `-u farm_operation,agri_intervention` exit 0, 0
  Traceback; skrip `shell-b5r1/b27_verify.py` +
  `shell-b5r1/b27_verify_a.py`):
  - (a) MO 201 (WH/MO/00203, saus, `intervention_type='process'`,
    confirmed) → `button_mark_done` sebagai user 2: **done**,
    move finished + raw `done`, worklog 9→9 (delta 0 — 'process'
    tak ada padanan, tanpa worklog palsu), transaksi hidup.
    **PASS.** (Satu FAIL semu di run pertama adalah bug skrip
    verifikasi sendiri — `stock.move` Odoo 18 tidak punya
    `quantity_done` — terjadi SETELAH commit, saat MO sudah done;
    diulang bersih di salinan baru → PASS.)
  - (b) MO feeding baru (WH/MO/00206, lot 252, tanpa
    `agri_task_id`, user 2) → **done**, worklog 9→9, transaksi
    hidup. **PASS.**
  - (c) MO sowing baru (WH/MO/00207, task 23 ADA) sebagai uid 1
    (SUPERUSER, tanpa employee) → **done**, worklog 9→9,
    transaksi hidup. **PASS.**
  - (d) `_cron_daily_feed_depletion` sebagai user 2 (skenario B11):
    kembali normal tanpa exception; feeding MO done 23→30
    (**+7**, WH/MO/00209–00215, satu per lot), stok pakan
    terkonsumsi (produk 283: 90→80 kg, 295: 60→50 kg),
    `total_feed_consumed` ketujuh lot naik +1,0. **B11 LOLOS.**
    Worklog 11→11 (delta 0 — SUDAH DIHARAPKAN: intervensi yang
    dibuat cron tidak punya `agri_task_id`, dan fix #1
    memerintahkan skip bila task null; lihat "Terbuka").
  - (e) MO 203 (WH/MO/00205, fertilizing, confirmed) →
    `button_mark_done` user 2: **done**, worklog 9→9.
    **PASS** (workflow + stok benar, worklog boleh absen untuk
    tipe tanpa padanan).
  - (f) Kontrol positif: MO feeding baru + task 23 + user 2 (ada
    employee) → **done**, worklog 9→11 (**+2**).
  - (d2) Mekanisme savepoint: INSERT `farm_worklog` task NULL di
    dalam savepoint melempar `NotNullViolation` seperti
    diharapkan, transaksi tetap hidup (SELECT sesudahnya OK).
    **PASS.**
  - test18 TIDAK tersentuh (tetap `farm_operation` 2.7 /
    `agri_intervention` 0.1, MO 201/203 tetap confirmed, worklog
    9). DB salinan `test18_b27fix` di-drop sesudah verifikasi.
- Terbuka / catatan untuk koordinator:
  - (d) nuansa worklog cron: "feeding MO/stok/worklog TERBENTUK"
    hanya terpenuhi 2 dari 3 — worklog cron TIDAK terbentuk
    karena intervensi cron tidak punya `agri_task_id` (dan user
    cron tidak punya task untuk dilampirkan). Itu konsekuensi
    langsung fix #1 yang diminta (skip bila task null), bukan
    kegagalan fix. Bila worklog pakan harian memang diinginkan,
    cron itu sendiri harus menautkan task (perubahan di
    `farm_livestock/models/farm_lot.py`, di luar scope B27) —
    atau diterima bahwa pakan harian tercatat lewat MO + stok
    saja. Keputusan ini milik koordinator/king.
  - (f) duplikat worklog PRA-ADA (bukan diperkenalkan fix ini):
    MO lengkap (tipe valid + task + employee) membuat **2**
    worklog identik — satu dari plugin labor (jalur
    `_run_plugins('post_done')`), satu dari
    `_create_auto_worklog_from_hook` langsung di mixin. Fix ini
    sengaja tidak mengubahnya (di luar scope "minimal, jangan
    ubah logika bisnis lain"); bila koordinator mau, salah satu
    jalur bisa dihapus di ronde terpisah.
  - B27a–B27e semua tertutup oleh perbaikan ini; tidak ada
    sub-blocker B27 yang tersisa di kode. Simulasi ulang
    kumulatif (koordinator) yang memutuskan B27 lolos final di
    test18.

### B28 — `action_convert_to_fertilizer` memakai farm.location id sebagai stock.location id — DIPERBAIKI ✅

- File: `farm_waste_mgmt/models/agri_manure_batch.py`
  (method baru `_get_stock_location_for_farm_location`, dipakai di
  `action_convert_to_fertilizer` untuk `location_src_id` DAN
  `location_dest_id` — keduanya sebelumnya memakai
  `self.location_source_id.id` mentah).
- Akar (terverifikasi di test18): `farm.location` adalah model/tabel
  terpisah (`_name = 'farm.location'` + `_inherit = 'stock.location'`
  di `farm_core/models/land_location.py` — prototype inheritance,
  urutan id sendiri, TANPA field penghubung ke `stock.location` dan
  tanpa `_inherits`). Jadi id farm.location BUKAN id stock.location:
  farm.location 48 = "SIMULASI B5R1 Lahan A1", stock.location 48
  TIDAK ADA. Tidak ada `stock.location` yang bernama sama dengan
  farm.location mana pun di test18, jadi pemetaan nama tidak
  menemukan apa-apa di sini.
- Pemetaan yang dipakai: (1) cari `stock.location` dengan `name`
  sama + `company_id` sama dengan farm.location, bila ada; (2) bila
  tidak ada → lokasi stok warehouse default perusahaan
  (`stock.warehouse.lot_stock_id`, yaitu WH/Stock); (3) bila itu pun
  tidak ada → `stock.stock_location_stock`; bila semuanya gagal,
  kunci `location_src_id`/`location_dest_id` tidak dikirim sama
  sekali sehingga default `mrp.production` yang berlaku. Logika
  bisnis lain tidak diubah (produk, qty, QC-pass gate, confirm).
- Versi: `farm_waste_mgmt` `18.0.1.0.1` → `18.0.1.0.2` (manifest
  di disk sudah `.0.1` saat ronde ini dimulai, sementara yang
  ter-install di test18 masih `.0.0`).
- Verifikasi (DB salinan `test18_b28fix`, upgrade `-u
  farm_waste_mgmt` exit 0, 0 Traceback; satu baris ERROR di log
  upgrade adalah peringatan umum "Importing test framework" yang
  sudah ada sebelumnya, bukan dari perubahan ini): batch 1
  (MNR/2026/00002, farm.location 48) → MO 204 WH/MO/00206,
  `confirmed`, `location_src_id` = `location_dest_id` = 8
  (WH/Stock), produk 293 qty 500 — TANPA FK error. Kontrol batch 2
  (MNR/2026/00003, farm.location 8) → MO 205 WH/MO/00207,
  `confirmed`, src/dest 8 (WH/Stock) — sebelumnya lolos hanya
  karena kebetulan id 8 = stock.location 8; kini deterministik
  lewat fallback, bukan kebetulan. Kedua MO terverifikasi
  tersimpan di DB salinan. test18 tidak tersentuh (tetap
  `18.0.1.0.0`, tanpa MO 204/205). DB salinan + dump dihapus
  sesudah verifikasi.
- Terbuka: pemetaan nama (langkah 1) belum pernah menemukan
  pasangan di test18 — bila kelak ada `stock.location` yang
  namanya sama persis dengan parcel farm, MO akan memakai lokasi
  itu, bukan WH/Stock; itu perilaku yang diinginkan, tapi belum
  teruji dengan data nyata.

### B29 — laporan QWeb manure ledger crash `KeyError: 'doc'` di setiap render — DIPERBAIKI ✅

- File: `farm_waste_mgmt/report/manure_ledger_report_templates.xml`
  + `farm_waste_mgmt/report/manure_ledger_reports.xml`
  (template dokumen sendiri TIDAK diubah isinya kecuali baris tanggal,
  lihat butir 2).
- Akar (persis SIMULASI.md §B29): `report_name` menunjuk LANGSUNG ke
  template dokumen `farm_waste_mgmt.report_manure_ledger_document`
  yang memakai `doc.*` di top-level, tanpa template pembungkus yang
  melakukan `<t t-foreach="docs" t-as="doc">`. Engine report hanya
  menyediakan `docs` → setiap render melempar `KeyError: 'doc'`
  (template 2831 baris 10, `t_call_0`). Jalur PDF menutupi bug ini
  (400 wkhtmltopdf tidak ada di test bed); jalur HTML mengeksposnya.
- Fix (pola standar Odoo, minimal):
  1. Template pembungkus baru `report_manure_ledger` di
     `manure_ledger_report_templates.xml`:
     `<t t-call="web.html_container">` +
     `<t t-foreach="docs" t-as="doc">` +
     `<t t-call="farm_waste_mgmt.report_manure_ledger_document" />`.
     Template dokumen tetap memakai `doc.*` di dalam foreach.
  2. `report_name` + `report_file` di `manure_ledger_reports.xml`
     diarahkan ke pembungkus (`farm_waste_mgmt.report_manure_ledger`).
  3. Bug laten KEDUA yang baru terlihat sesudah wrapper bekerja
     (template dokumen sebelumnya tidak pernah berhasil render,
     jadi baris ini tidak pernah dieksekusi): baris tanggal tanda
     tangan `datetime.now().strftime('%Y-%m-%d')` melempar
     `AttributeError: 'wrap_module' object has no attribute 'now'` —
     di konteks QWeb Odoo 18, `datetime` adalah modul (bukan class),
     `now` hanya ada di `datetime.datetime`. Diperbaiki ke
     `datetime.datetime.now().strftime('%Y-%m-%d')` — pola yang
     dipakai core sendiri (`web/views/report_templates.xml:842`,
     `account_test/report/report_account_test_templates.xml:7`).
     Satu-satunya pemakaian `datetime.now()` di modul ini.
- Versi: `farm_waste_mgmt` TETAP `18.0.1.0.2` (manifest sudah `.0.2`
  saat fix ini di-upgrade — bump `.0.0` → `.0.1` oleh pekerja B29,
  lalu `.0.1` → `.0.2` oleh pekerja B28 yang bekerja paralel di
  modul yang sama; koordinator menyelaraskan. Tidak di-bump lagi
  di sini supaya tidak balapan versi).
- Verifikasi (DB salinan `test18_b29fix`, dibuat via pg_dump dari
  test18; upgrade `-u farm_waste_mgmt` exit 0, 0 Traceback; satu
  baris ERROR di log upgrade adalah peringatan umum "Importing test
  framework" yang sudah ada sebelumnya):
  - HTTP (server salinan port 8079, sesi admin): `GET
    /report/html/farm_waste_mgmt.report_manure_ledger/1` → **200**,
    4.758 byte; isi memuat `MNL/2026/00001`, judul "Livestock and
    Poultry Manure Utilization Monthly Ledger", "Manure Batch
    Details", tanggal `2026-11-10`; 0 penanda KeyError/Traceback.
    Nama lama `...report_manure_ledger_document/1` → 500
    `ValueError: ... type ir.ui.view, expected ir.actions.report`
    (sudah bukan report — diharapkan, bukan regresi).
  - Shell (`env['ir.actions.report']._render_qweb_html(...)` —
    catatan: `render_qweb_html` tanpa underscore TIDAK ADA di
    Odoo 18; API yang benar `_render_qweb_html`): action 1055
    "Manure Ledger", `report_name` =
    `farm_waste_mgmt.report_manure_ledger`, render ledger 1
    → len 4.758, ctype `html`, `HAS_LEDGER_NO/TITLE/BATCH_TABLE/
    DATE` semua True; `_get_report_from_name` mengembalikan
    action 1055. (Dua kegagalan shell di tengah jalan adalah
    kesalahan harness sendiri — lupa `-c odoo.conf`, lalu
    `'str' in bytes` — bukan bug modul.)
  - test18 TIDAK di-upgrade (tetap `18.0.1.0.0`); server utama
    8071 tetap 200. DB salinan `test18_b29fix` di-drop sesudah
    verifikasi; server salinan 8079 dimatikan.
  - Catatan: satu `FileNotFoundError` filestore di log server
    salinan adalah artefak salinan pg_dump tanpa filestore
    (attachment yang dirujuk DB tidak ada di filestore salinan),
    non-fatal, bukan dari render report.
- Terbuka: jalur PDF (`/report/pdf/...`) tetap 400 di test bed
  karena wkhtmltopdf memang tidak terpasang — bukan bug modul,
  tidak diuji di sini. Tombol Print di form ("Manure Ledger",
  action 1055) belum diklik di browser — render-nya sudah
  terbukti lewat HTTP + shell; klik browser menjadi bagian
  simulasi ulang koordinator.

## Ronde perbaikan B30–B31 (B5R2) (10 Nov 2026)

### B30 — "registry kehilangan model fair trade" — BUKAN bug, kesalahan nama model di probe ✅ (B5R2, tidak ada perubahan kode)

- Klaim SIMULASI.md §B30: `POST /web/dataset/call_kw` model
  `farm.esg.fair_trade.certificate` / `.premium.allocation` → 404
  `KeyError` di registry, "terkonfirmasi 4 boot", plus "flip
  non-deterministik" dan dialog "Oops!" di direct-URL (shot 1016).
- Akar (terbukti, bukan hipotesis): probe memakai nama model
  **underscore** `farm.esg.fair_trade.*`; nama terdaftar adalah
  **dotted** `farm.esg.fair.trade.*` (semua titik). Bukti: source
  `farm_esg_fair_trade/models/__init__.py:13,83`; `ir_model` test18
  id 2974/2975 + action 1074–1077 `res_model` (dotted semua); grep
  seluruh tree: NOL referensi underscore di kode/data modul; log
  server PID 1835: semua request UI dotted → 200 (baris 15:09:52
  yang dikutip sebagai "flip" sebenarnya dotted — salah transkripsi).
  Kesalahan yang sama sudah dikoreksi sekali di B5R1 (SIMULASI.md
  K-1) dan terulang di skrip B5R2.
- Verifikasi (skrip `/tmp/b30_verify.py`, `/tmp/b30_verify2.py`,
  boot PID 1835 yang sama): dotted `search_count` cert 200/2,
  premium 200/3, `read`/`fields_get`/`search_read`/`name_search`/
  `web_search_read` semua 200; underscore → JSON-RPC error code 404
  `KeyError` di `dataset.py:22` (HTTP 200, bukan HTTP 404 — koreksi
  redaksional); flip test dotted 10× → 200 semua; direct-URL dotted
  premium 3 → form terbuka errdlg 0, underscore → errdlg 1 "Oops!"
  (reproduksi shot 1016).
- Perbaikan: HANYA skrip probe B5R2 (bukan kode modul):
  `shell-b5r2/b5r2_5c.py:191,200`, `shell-b5r2/b5r2_5c2.py:157,166`,
  `shell-b5r2/b5r2_5c_ft.py:6,20` + docstring, dan
  `browser-proof-b5r2-5ft3-retry.py:17` — underscore → dotted
  (py_compile OK). Modul `farm_esg_fair_trade` TIDAK diubah, versi
  TETAP, test18 TIDAK di-upgrade.
- Keputusan: B30 DICABUT sebagai blocker. Simulasi ulang (koordinator)
  dengan skrip yang sudah diperbaiki; Bagian 5 fair trade LOLOS penuh
  (UI + RPC/API + direct-URL dengan nama model yang benar).

### B31 — cron "Check Biological Asset Maturity" memanggil method yang tidak ada — DIPERBAIKI ✅ (B5R2, cron DINONAKTIFKAN)

- Gejala (SIMULASI.md §B31): cron id 40 "Check Biological Asset Maturity"
  (`farm_core/data/ir_cron_data.xml:8`, model `stock.lot`, interval 1 hari,
  aktif) menjalankan `model._cron_check_maturity_and_transfer_asset()` →
  `AttributeError: 'stock.lot' object has no attribute
  '_cron_check_maturity_and_transfer_asset'` di log server, 1×/hari; tidak
  memblokir alur simulasi manapun.
- Investigasi — niat method TIDAK bisa dipulihkan dengan yakin, jadi TIDAK
  diimplementasikan (pilihan jujur sesuai arahan tugas):
  1. Method tidak ada di codebase manapun: grep `*.py` di repo port DAN di
     repo upstream kajian `~/workspace/odoo-farm-eval/odoo-farm/` (commit
     aaa0ab6) kosong; hanya XML cron itu sendiri yang merujuknya. Jadi ini
     cacat upstream, bukan kehilangan saat porting — tidak ada implementasi
     referensi yang bisa dipulihkan.
  2. Separuh "transfer" dari nama cron tidak punya pendukung sama sekali:
     tidak ada logika transfer/reklasifikasi/promosi aset matang di mana
     pun (grep `transfer.*asset|matur.*transfer|reclassif` di farm_core,
     farm_livestock, farm_livestock_valuation, farm_biological_valuation,
     farm_financial_valuation, farm_aquaculture, farm_processing kosong),
     tidak ada tujuan transfer (lokasi/akun/kategori), tidak ada action,
     test, atau dokumen. Membuatnya berarti mengarang semantik bisnis.
  3. Separuh "maturity" memang ada fieldnya, tapi tidak menopang cron ini:
     `farm.biological.asset.maturity_date` / `is_mature` adalah computed
     stored (dari `birth_date` + `product.maturity_age_days`,
     `farm_core/models/common_fields.py:48`) yang terhitung saat tulis dan
     TIDAK punya konsumen — tidak ada kode yang membaca `is_mature` untuk
     memicu apa pun (hanya tampil di view). `stock.lot` sendiri TIDAK
     punya field maturity; model saat ini `agri.biological.asset` punya
     `maturity_date`/`is_mature` polos tapi TIDAK punya link ke lot
     (hanya tracking carrier), jadi cron di `stock.lot` tidak bisa
     menjangkaunya. Satu-satunya link lot→asset ada di model DEPRECATED
     `farm.biological.asset` (`lot_id`).
  4. Implementasi tebakan (mis. membalik `growth_stage` ke `mature`) akan
     berefek samping finansial yang dikarang: koefisien valuasi
     `farm_biological_valuation` naik 0.6 → 1.0. Karena itu TIDAK dibuat
     stub method — cron yang tetap aktif + stub kosong hanya akan
     menyembunyikan masalah.
- Perbaikan (minimal, jujur): cron DINONAKTIFKAN — `active` `True` →
  `False` di `farm_core/data/ir_cron_data.xml`, plus komentar XML yang
  mendokumentasikan keempat butir bukti di atas dan syarat pengaktifan
  kembali (perilaku "transfer" harus dispesifikasi dulu + method
  diimplementasikan). String `code` yang menggantung dibiarkan apa adanya
  (tidak dieksekusi selama cron nonaktif); field `name`/`code`/`state`/
  `model_id` di XML tetap seperti semula karena itu field delegasi
  `ir.actions.server` (`ir.cron.ir_actions_server_id`, `delegate=True`)
  — di Odoo 18 kolom nama di tabel `ir_cron` sendiri adalah `cron_name`
  (stored computed dari nama server action), terverifikasi di test18:
  `cron_name = {"en_US": "Check Biological Asset Maturity"}`.
- Versi: `farm_core` `18.0.1.0.1` → `18.0.1.0.2`.
- Verifikasi (DB salinan `test18_b31fix`, pg_dump dari test18; test18 TIDAK
  di-upgrade — tetap `18.0.1.0.1`, cron 40 tetap aktif di sana):
  - Upgrade `-u farm_core` di salinan: exit 0, 0 Traceback.
  - Shell salinan: cron 40 `cron_name='Check Biological Asset Maturity'`,
    `active=False`; `search([('active','=',True),('id','=',40)])` kosong;
    query persis scheduler Odoo 18 (`ir.cron._get_all_ready_jobs`:
    `WHERE active = true AND nextcall <= now() ...`) TIDAK memuat id 40;
    `farm_core` `installed`, `latest_version=18.0.1.0.2`; method tetap
    tidak ada di `stock.lot` (diharapkan — cron tidak bisa lagi
    memanggilnya); tidak ada cron aktif lain yang memanggil method itu.
  - Server salinan port 8079 jalan 100 detik (HTTP 200): 0 kemunculan
    `_cron_check_maturity`, 0 `AttributeError`, 0 Traceback di log.
  - DB salinan di-drop sesudah verifikasi; server utama 8071 tetap 200.
- Terbuka: bila king kelak mendefinisikan arti "transfer asset" saat
  matang (mis. pindah lokasi/kategori/akun + siapa yang dipindah),
  method `_cron_check_maturity_and_transfer_asset` dapat diimplementasikan
  di `stock.lot` (atau di model pemilik aset) dan cron diaktifkan lagi —
  sampai saat itu cron tetap nonaktif dan bukan blocker.

## 19. Batch 6 — vertikal hortikultura + rekonsiliasi tertunda (11 Nov 2026)

Batch TERAKHIR rencana awal. Audit manifest LANGKAH 0 (11 Nov 2026):
64 modul belum ter-install ditemukan di disk (bukan 60 — hitungan tugas
melewatkan 4: `farm_fermentation_matter`, `farm_multi_farm_equipment`,
`farm_supply_chain_smart`, `farm_supply_logistics` sudah termasuk dalam
pola `farm_*` yang diaudit). 49 modul farm/agri ter-install di test18
(43 modul `farm_*` + `agri_intervention` + `agri_iot` + 4 modul AgriOS
lama `agrios_*` = 49 baris `ir_module_module state='installed'`
per psql 11 Nov 2026.)

### 19a. SET batch 6 — 20 modul

| Kelompok | Modul | Alasan masuk |
|---|---|---|
| INTI hortikultura | `farm_orchard_horticulture` | buah (apel/durian/mangga generik) |
| INTI | `farm_floriculture` | bunga + vase-life |
| INTI | `farm_mushroom` | jamur (B13 laten: `farm.mushroom.production`) |
| INTI | `farm_apiculture` | lebah/madu |
| INTI | `farm_viticulture` | anggur |
| INTI | `farm_winery` | wine (B13 laten: `farm.winery.production`) |
| INTI | `farm_medicinal_plants` | tanaman obat (GMP) |
| INTI | `farm_greenhouse` | greenhouse + IoT |
| INTI | `farm_protected_cultivation` | budidaya terlindung |
| INTI | `farm_fermentation` | fermentasi (B13 laten: `farm.fermentation.order`) |
| INTI | `farm_fermentation_matter` | depends `farm_fermentation` |
| REKONSILIASI | `farm_supply` | depends `farm_supply_procurement` |
| REKONSILIASI | `farm_supply_procurement` | `input_type` `product.template` (§18c/§18e — rekonsiliasi definisi lokal `farm_waste_mgmt`) |
| REKONSILIASI | `farm_ecology` | GEP valuation `farm_financial_valuation` §18e (`gep_score` kini nyata di `farm.location`-turunan; guard di valuation tidak dirugikan) |
| REKONSILIASI | `farm_equipment` | depends yang dipangkas `farm_esg_environmental` + `farm_esg_circular` §18c |
| REKONSILIASI | `farm_subsidy` | menu Subsidies `farm_esg_compliance` yang dihapus §18d/§18e (dikembalikan §19d); depends `farm_mobile` dipangkas (0 acuan kode) |
| REKONSILIASI | `farm_multi_farm` | prasyarat `farm_multi_farm_financial` |
| REKONSILIASI | `farm_multi_farm_financial` | depends NYATA hanya `farm_multi_farm` + `account` (BUKAN `farm_financial_credit` seperti dugaan §18b) — bisa dipasang utuh |
| REKONSILIASI | `farm_certification` | sertifikasi organik/GAP/GI — vertikal hortikultura (bukan depends keras modul inti, tapi satu rumpun) |
| REKONSILIASI | `farm_crop_matter` | jembatan matter `farm.crop.cycle` (pola `*_matter` batch 3/5) |

Urutan install (topologis): `farm_supply` → `farm_supply_procurement`,
`farm_multi_farm` → `farm_multi_farm_financial`, sisanya sesudah
depends-nya (`farm_core`/`farm_operation`/`farm_isl`/`farm_processing`/
`farm_agricultural_processing`/`farm_iot`/`farm_esg` sudah ter-install).

### 19b. TETAP DIKECUALIKAN — China-specific (11 modul, sama seperti batch 1–5)

`farm_cert_ch`, `farm_entity_reg`, `farm_green_monitor`,
`farm_input_reg`, `farm_land_mgmt`, `farm_machinery_ch`,
`farm_sale_ch`, `farm_subsidy_ch`, `farm_live_streaming`,
`farm_finance_gov` (juga DEPRECATED upstream — pakai
`farm_financial_government`), `farm_exchange` (format DAPLOS/
TELEPAC/Agri-EDI Prancis — bukan China, tapi regulasi-luar;
tetap dikecualikan dari batch 6 karena bukan vertikal inti dan
tidak dirujuk modul SET; bila king butuh EDI, masuk batch 7+).

### 19c. DITANGGUHKAN KE BATCH 7+ (29 modul)

| Modul | Alasan |
|---|---|
| `farm_ai`, `farm_ai_agent`, `farm_ai_decision`, `farm_ai_llm_integration`, `farm_ai_robotics`, `farm_ai_vision` (6) | butuh LLM/API eksternal + `farm_robotics`; bukan vertikal tanam |
| `farm_robotics` | butuh perangkat/robot + `farm_knowledge` (juga tangguhan); otomasi lapangan |
| `farm_multi_farm_equipment`, `farm_multi_farm_procurement`, `farm_multi_farm_quality` | multi-entity lanjutan; bukan prasyarat `farm_multi_farm_financial` |
| `farm_supply_analytics`, `farm_supply_logistics`, `farm_supply_quality` | analitik/logistik/quality lanjutan supply chain; `farm_supply_quality` butuh `farm_ai_decision` |
| `farm_pos`, `farm_mobile` | kanal penjualan/mobile; `farm_mobile` berat (`hr_timesheet`) |
| `farm_dashboard` | dashboard gabungan; bukan prasyarat alur vertikal |
| `farm_marketing` | butuh `website` + `loyalty`; pemasaran/konsumen |
| `farm_logistics` | STUB tanpa manifest (lihat §19d) |
| `farm_gov` | butuh `farm_input_reg` + `farm_multi_farm` + `farm_ecology`; antarmuka regulator |
| `farm_crisis`, `farm_disaster_risk` | butuh `farm_safety` (juga tangguhan) + `farm_crisis`; manajemen bencana |
| `farm_data_security` | keamanan data/audit lanjutan |
| `farm_knowledge` | basis pengetahuan hama/penyakit; bukan prasyarat alur tanam |
| `farm_training` | pelatihan petani (`hr`) |
| `farm_agritourism` | pariwisata (booking/activity/membership) |
| `farm_csa` | butuh `farm_multi_farm` + langganan mingguan; model bisnis CSA |
| `farm_safety` | biosafety/epidemi; prasyarat `farm_crisis` |
| `farm_symbiosis` | rice-fish/rice-shrimp; vertikal tapi di luar INTI batch 6 per tugas (depends sudah ter-install semua — kandidat pertama batch 7) |
| `farm_label` | butuh `farm_marketing` + `barcodes`; pelabelan |
| `farm_insurance` | asuransi hasil panen; modul mandiri, kandidat batch 7 |
| `farm_finance_advanced`, `farm_finance_loan`, `farm_supply_chain_smart` | STUB tanpa manifest (lihat §19d) |

### 19d. Temuan audit manifest (LANGKAH 0)

1. **4 stub tanpa `__manifest__.py` — tidak bisa di-install apa adanya:**
   `farm_finance_advanced`, `farm_finance_loan`, `farm_logistics`,
   `farm_supply_chain_smart` (hanya `__init__.py` + `i18n/` + `tests/`).
   Bukan modul sungguhan di upstream commit ini; ditangguhkan sampai
   upstream melengkapinya. BUKAN kegagalan porting.
2. **`farm_subsidy` depends `farm_mobile` hanya di manifest** (0 acuan
   kode ke model farm_mobile) → dipangkas seperti pola §3/§14c/§17b.
3. **`farm_multi_farm_financial` TIDAK depends `farm_financial_credit`**
   (dugaan §18b salah — manifest nyata: `farm_multi_farm`,
   `account`, `base`, `mail`) → dipasang utuh beserta prasyaratnya
   `farm_multi_farm`.
4. **`input_type` — rekonsiliasi (§18c):** `farm_supply_procurement/
   models/farm_input.py` mendefinisikan `input_type` di
   `product.template` dengan nilai seleksi IDENTIK dengan definisi
   lokal `farm_waste_mgmt` (seed/fertilizer/pesticide/feed/medicine/
   other). Urutan aman: (1) install `farm_supply_procurement` dulu
   (dua definisi identik berdampingan — Odoo menoleransi redefinisi
   field yang sama tipenya), (2) HAPUS definisi lokal dari
   `farm_waste_mgmt/models/product_template.py` + upgrade
   `farm_waste_mgmt` (kolom dipakai ulang, tidak di-drop). `n_content`/
   `p_content`/`k_content` di `farm_input.py` juga duplikat `farm_core`
   (`common_fields.py`) — tipe sama (Float), dibiarkan.
5. **B13 laten — 3 dari 4 model ADA di batch 6:** `farm.fermentation.order`
   (`fermentation_isl.py:39`), `farm.mushroom.production`
   (`mushroom_operation.py:54`), `farm.winery.production`
   (`winery_isl.py:50`) — ketiganya `_inherit` mencakup
   `agri.incident.alert.mixin` (`report_incident` → `mail.activity.create`)
   tanpa `mail.thread`. Perbaikan pola B13: tambah `'mail.thread'` ke
   `_inherit` masing-masing. Model ke-4, `farm.haccp.check`, TIDAK ADA
   sebagai model di repo mana pun (hanya disebut di test/string
   `farm_agricultural_processing`/`farm_isl`/`farm_processing`) —
   tetap laten sebagai nama, bukan blocker.
6. **`farm_subsidy` — model `agri.evidence` tidak ada di repo:**
   `subsidy.py` memakai `env['agri.evidence']` di 6 tempat + class
   `_inherit = 'agri.evidence'` (registry akan gagal) + template QWeb
   memakai `doc.evidence_records` (One2many yang di-comment-out).
   Perbaikan: definisikan model konkret `agri.evidence` di `farm_subsidy`
   (`_inherit = ['mail.thread', 'agri.evidence.mixin']` dari farm_core)
   dengan field yang dipakai kode/template (`name`, `res_model`,
   `res_id`, `taken_at`, `gps_lat`, `gps_lng`, `is_on_site`, `note`,
   `worker_id`, `is_hash_verified`, `verify_evidence_integrity()`) +
   `subsidy_application_id` + kembalikan One2many `evidence_records`.
   Catatan: bila `farm_gov` kelak di-port dan mendefinisikan
   `agri.evidence` sendiri, definisi itu harus diubah jadi extend.
   Juga: `views/subsidy_report_views.xml` TIDAK termuat di manifest
   (bug upstream) → ditambahkan; widget `ace` mode `'json'` → 
   `'javascript'` (jebakan B6); sequence `farm.subsidy.application`
   tidak ada → file `data/ir_sequence.xml` baru.
7. **`farm_certification` — wizard `farm.certification.renewal.wizard`
   tidak ada:** `action_renew_certificate` (`gap_certification.py:75`)
   `create()` + act_window ke model yang tidak didefinisikan di mana pun.
   Perbaikan: TransientModel minimal + form view + `action_confirm_renewal`
   (perpanjang `expiry_date` + status `valid`).
8. **`farm_multi_farm` — `farm.biological.twin` tanpa guard:**
   `regional_oversight.py:39` `env['farm.biological.twin']` di
   `_compute_yield_forecast` (compute → crash saat field dibaca; model
   tidak ada di repo — phantom §18e). Perbaikan: guard
   `if 'farm.biological.twin' in self.env` else 0. Demo data
   (`data/demo_data.xml`, model `farm.entity.link` dkk.) TIDAK termuat
   di manifest → bukan blocker. Ref `joint.procurement*` semua
   ter-comment-out.
9. **File model tidak di-import (pola §18d.2):**
   `farm_floriculture/models/sale_order_bridge.py`,
   `farm_greenhouse/models/ecommerce_integration.py`,
   `farm_certification/models/gap_certification.py` +
   `farm_certification/models/certification_dashboard.py` — ditambah ke
   `models/__init__.py` masing-masing. `farm_ecology` BUKAN masalah
   (import multi-baris berkurung terlewat audit regex pertama).
   `farm_multi_farm/models/extension_models_original.py` = salinan basi
   `extension_models.py` — sengaja TIDAK di-import.
10. **`models.Constraint` (19-only, pola §5) di 3 file:**
    `farm_supply/models/agri_supply_chain_mixin.py`,
    `farm_certification/models/gap_certification.py`,
    `farm_multi_farm/models/cooperative_member.py` → `_sql_constraints`.
11. **CSV akses kosong:** 17 dari 20 modul SET punya
    `security/ir.model.access.csv` berisi header saja; `farm_crop_matter`
    + `farm_fermentation_matter` tanpa CSV (0 model konkret — preseden
    `farm_esg_matter` §18c, tanpa CSV); `farm_supply` 3 model mixin
    abstrak → tanpa aturan. Aturan ditambahkan per audit AST model
    konkret (pola batch 4/5).
12. **CJK non-test:** terbanyak komentar/docstring (`farm_multi_farm`
    ~400 karakter, `farm_multi_farm_financial` ~200,
    `farm_certification` ~100, `farm_subsidy` ~65,
    `farm_supply_procurement` ~80, `farm_equipment` ~37,
    `farm_protected_cultivation` ~33) + label user-visible:
    fase jamur (`chamber_plc.py`), tipe operasi protected cultivation,
    tipe vessel fermentasi, `Grand Vin (正牌酒)`/`Secondary Label (副牌酒)`
    (`barrel_tracking.py`), judul grup view orchard/viticulture.
    Semua diterjemahkan ke Inggris (label) / Inggris (komentar);
    `i18n/zh_CN.po` + `.pot` dibiarkan (pola batch 1–5).
13. **Menu Subsidies `farm_esg_compliance` (§18e) DIKEMBALIKAN:**
    upstream `esg_compliance_views.xml:4-8` (`action_farm_subsidy`) +
    `:117` (`menu_farm_subsidy`, parent `menu_esg_operations`) +
    depends `farm_subsidy` dipulihkan verbatim;
    `farm_esg_compliance` 18.0.1.0.1 → **18.0.1.0.2**.
14. **`farm_ecology` — `gep_score`:** didefinisikan di
    `ecology.py:72` sebagai field compute+store pada `_inherit =
    'farm.location'` (`FarmLocation`, 0.6*biodiversity_index +
    0.4*eco_zone_coverage; `message_post` bila > 80) +
    `farm_financial_valuation` sudah guard (§18c) → nilai GEP nyata
    terbaca otomatis sesudah install.
15. **Cross-ref audit (regex `env[]`/Many2one/`res_model` atas SET +
    modul ter-install, tanpa test):** semua referensi model
    `farm.*`/`agri.*`/`esg.*` terpenuhi KECUALI 3 temuan di atas
    (butir 6–8). `farm_mushroom` memakai mixin
    `agri.odoo19.performance.security.mixin` — ADA di `farm_core`
    (bukan blocker). `farm_greenhouse` mengimpor `requests` (dipakai
    `farm_weather` juga — tersedia di venv test bed).
16. **Alat migrasi:** `odoo-module-migrator` + `oca-port` tetap tidak
    bisa dipakai untuk 19.0→18.0 (alasan §1, tidak berubah) — sapuan
    mekanis manual seperti batch 1–5.

### 19e. Perubahan per modul batch 6 (ringkas; detail di PORTING.d/b6.md)

Semua 20 modul SET ter-install 18.0.1.0.0 di test18 (kecuali yang disebut).
Simulasi kumulatif batch 6 **BERSIH ✅ 100%** (11 Nov 2026, SIMULASI.md
bagian batch 6, shot 1554–1733). Perbaikan sesudah install:

- **B32 (ace `'json'` → `'javascript'`, laten batch 1):** `CodeEditor.MODES`
  Odoo 18 = `javascript/xml/qweb/scss/python` — `'json'` crash form.
  Diperbaiki di 6 modul ter-install: `farm_core` → 18.0.1.0.3,
  `farm_agri_science` → 18.0.1.1.2, `farm_greenhouse` → 18.0.1.0.1,
  `farm_mushroom` → 18.0.1.0.1, `farm_processing` → 18.0.1.1.4,
  `farm_ux` → 18.0.1.1.4 (14 pemakaian). Modul belum ter-install yang
  masih `'json'` (`farm_ai_*`, `farm_gov`, `farm_live_streaming`,
  `farm_robotics`) dibiarkan untuk batch 7+.
- **B33 (statusbar pada Boolean):** `farm_certification` → 18.0.1.0.1 —
  `overall_compliant` (Boolean) dilepas dari `widget="statusbar"` di form
  `farm.gap.compliance.check` (crash `StatusBarField.getAllItems`),
  dipindah jadi checkbox di sheet.
- **§19d terverifikasi:** (4) `input_type` direkonsiliasi
  (`farm_waste_mgmt` 18.0.1.0.3, definisi lokal dihapus); (5) B13 laten —
  `mail.thread` di `farm.fermentation.order`, `farm.mushroom.production`,
  `farm.winery.production`, terverifikasi fungsional (`report_incident`
  → `mail.activity` 3/3); (6) `agri.evidence` konkret di `farm_subsidy`
  + One2many `evidence_records` + sequence SUB + view laporan termuat;
  (7) wizard `farm.certification.renewal.wizard` minimal (Renew →
  expiry +2 tahun, terverifikasi 2027-01-14 → 2029-11-10); (8)
  `farm.biological.twin` di-guard di `farm_multi_farm`
  (`farm_multi_farm` 18.0.1.2.0); (13) menu Subsidies
  `farm_esg_compliance` dikembalikan (18.0.1.0.2).
- Per modul SET (versi akhir di test18): `farm_orchard_horticulture`,
  `farm_floriculture`, `farm_mushroom` (→ .0.1, B32),
  `farm_apiculture`, `farm_viticulture`, `farm_winery`,
  `farm_medicinal_plants`, `farm_greenhouse` (→ .0.1, B32),
  `farm_protected_cultivation`, `farm_fermentation`,
  `farm_fermentation_matter`, `farm_supply`, `farm_supply_procurement`,
  `farm_ecology` (GEP nyata: `gep_score` 26.0 di lahan 51),
  `farm_equipment`, `farm_subsidy`, `farm_multi_farm` (.2.0),
  `farm_multi_farm_financial`, `farm_certification` (→ .0.1, B33),
  `farm_crop_matter` — semua 18.0.1.0.0 kecuali yang disebut.
  `farm_supply`/`farm_crop_matter`/`farm_fermentation_matter` tanpa model
  konkret (mixin/penghubung saja, preseden `farm_esg_matter`).
- **O-B6R1-1 (harness, bukan kode):** `agri.cost.calculation` adalah
  TransientModel — record id 6 terhapus `ir.autovacuum`; harness yang
  memakai ID transient hardcoded rapuh. Dibuat ulang segar (id 7) +
  terverifikasi browser (total 500.000,00 + `calculate()` OK).

### 19f. Sisa sesudah batch 6 — batch 7+ (dari §19c)

29 modul ditangguhkan: AI/robotics (`farm_ai`, `farm_ai_agent`,
`farm_ai_decision`, `farm_ai_llm_integration`, `farm_ai_robotics`,
`farm_ai_vision`, `farm_robotics`), multi-farm lanjutan
(`farm_multi_farm_equipment`, `farm_multi_farm_procurement`,
`farm_multi_farm_quality`), supply lanjutan (`farm_supply_analytics`,
`farm_supply_logistics`, `farm_supply_quality`), `farm_pos`,
`farm_mobile`, `farm_dashboard`, `farm_marketing`, `farm_gov`,
`farm_crisis`, `farm_disaster_risk`, `farm_data_security`,
`farm_knowledge`, `farm_training`, `farm_agritourism`, `farm_csa`,
`farm_safety`, `farm_symbiosis` (kandidat pertama batch 7 — depends
sudah ter-install semua), `farm_label`, `farm_insurance`. 4 stub tanpa
manifest (`farm_finance_advanced`, `farm_finance_loan`, `farm_logistics`,
`farm_supply_chain_smart`) menunggu upstream. 11 modul China-specific
tetap dikecualikan (§19b).

## 20. Batch 7 — AI/robotics + multi-farm/supply lanjutan + POS/mobile/dashboard + gov/krisis + pengetahuan/pelatihan/agriturisme/CSA/safety/symbiosis/label/insurance (11 Nov 2026)

Perintah king "Lanjut batch 7" (11 Nov 2026 ~06:44 WIB). Aturan flow FINAL
(10 Nov 12:20): jangan berhenti kalau ada error — perbaiki → simulasi ulang
kumulatif sampai 100% pass. Scope HANYA batch 7 (29 modul); batch 8 diputuskan
parent sesudah laporan. Semua 29 modul ter-install di test18; simulasi
kumulatif batch 1–7 **BERSIH ✅ 100%** (SIMULASI.md bagian batch 7,
shot 1733–1853).

### 20a. LANGKAH 0 — audit (skrip `/tmp/b7_audit0.py`, output `/tmp/b7_audit0.txt`)

Semua 29 dir di folder port adalah salinan upstream murni (diff 0 vs eval).

1. **Depends hilang:** hanya `farm_gov` → `farm_input_reg`
   (China-specific, 0 referensi kode — di-trim dari manifest).
   `farm_data_security` → `base_setup` ada di core addons. `farm_ai_agent`
   → `farm_financial_insurance` sudah ter-install.
2. **`models.Constraint` (19-only):** `farm_ai/models/ai_base.py`,
   `farm_supply_logistics/models/cold_storage.py` → `_sql_constraints`.
3. **Ace `mode 'json'` (pola B32):** 12 file XML di `farm_ai_agent`,
   `farm_ai_decision`, `farm_ai_vision`, `farm_robotics`, `farm_gov` →
   `'javascript'`.
4. **`<tree>` di view:** 0. **Statusbar Boolean (pola B33):** 0 — semua
   statusbar memakai Selection / `stage_id` Many2one.
5. **CJK non-test:** ~2.500 karakter total; terbanyak `farm_mobile` 533,
   `farm_ai_agent` 467, `farm_marketing` 334,
   `farm_multi_farm_procurement` 187, `farm_safety` 170.
6. **Import eksternal:** `farm_ai_agent` memakai `numpy` (ada di venv
   odoo18, 2.5.4); `openai` TIDAK ter-install — layanan LLM memakai
   `requests` ke API provider, butuh API key eksternal (lihat §20e).
7. **Tanpa model konkret:** `farm_dashboard` (view saja), `farm_pos`
   (hanya `_inherit`), `farm_ai_robotics`, `farm_label` (0 model konkret).

### 20b. Sapuan mekanis (`/tmp/b7_sweep1.py`, `/tmp/b7_acl.py`, `/tmp/b7_cjk_map.py`, `/tmp/b7_po.py`)

- **Versi:** `19.0.x` → `18.0.x`; `1.0` → `18.0.1.0.0`, `1.1` →
  `18.0.1.1.0`, `1.2` → `18.0.1.2.0`, `1.0.0` → `18.0.1.0.0`
  (`farm_data_security` 1.2 → 18.0.1.2.0, `farm_knowledge` 1.1 →
  18.0.1.1.0, `farm_agritourism` 1.1 → 18.0.1.1.0,
  `farm_ai_decision` 19.0.1.2.1 → 18.0.1.2.1).
- **Depends:** `farm_gov` lepas `farm_input_reg` (butir 20a.1).
- **Ace:** `'json'` → `'javascript'` (12 file, butir 20a.3).
- **`models.Constraint` → `_sql_constraints`:** `farm_ai/ai_base.py`
  (1 + 3 constraint), `cold_storage.py` (2).
- **Import `__init__` yang hilang ditambah:** `farm_multi_farm_equipment`
  (stock_picking_extension), `farm_training` (agri_skill, farm_training,
  hr_employee), `farm_agritourism` (sale_order); controller:
  `farm_ai_vision` (top-level `from . import controllers`),
  `farm_mobile` + `farm_marketing` (`from . import main` + import
  top-level).
- **ACL (+91 baris `base.group_user,1,1,1,1`):** modul yang CSV-nya
  hanya header — farm_ai +2, farm_ai_agent +1 (farm.water.valve),
  farm_ai_decision +14, farm_ai_llm_integration +2, farm_ai_vision +6,
  farm_robotics +3, farm_supply_analytics +8, farm_supply_logistics +8,
  farm_supply_quality +1, farm_mobile +6, farm_marketing +4,
  farm_crisis +2, farm_disaster_risk +2, farm_data_security +2,
  farm_knowledge +4, farm_training +9, farm_agritourism +4, farm_csa +3,
  farm_safety +3, farm_symbiosis +4, farm_insurance +3. Sudah lengkap:
  farm_multi_farm_equipment, farm_multi_farm_procurement,
  farm_multi_farm_quality, farm_gov. Tanpa CSV (0 model konkret):
  farm_ai_robotics, farm_pos, farm_dashboard, farm_label.
- **De-CJK:** 0 karakter CJK tersisa di file non-test (verifikasi scan).
  Regex menghapus parenthetical CJK + pola `CJK / English`, lalu kamus
  terjemahan (`/tmp/b7_cjk_map.py`, 250 string) longest-first.
  **Jebakan (ditemukan & diperbaiki):** regex
  `\s*\([^()\n]*CJK[^()\n]*\)` ikut menghapus tuple selection seperti
  `('pending', 'Pending / 待审批')` dan mengosongkan f-string — kerusakan
  terbatas di `farm_ai_agent` (selection tool_request dipulihkan
  Pending/Approved/Rejected/Executed; f-string sandbox_mixin dipulihkan
  Inggris; `gxp_contamination.py` 3 bagian `""` dipulihkan Inggris) dan
  `farm_csa` (4 bagian `""` dipulihkan Inggris). Verifikasi akhir:
  py_compile 0 buruk, XML well-formed 0 buruk, CJK 0. Sertifikat China
  `farm_label` digeneralisasi ke Inggris "Edible Agricultural Product
  Compliance Certificate" + teks komitmen terjemahan (pola §6).
- **i18n/id_ID.po (`/tmp/b7_po.py`):** dibuat per modul (ekstrak string
  `_()`/field/selection/view; kamus EN→ID untuk istilah umum; string
  yang belum diterjemahkan tetap msgstr Inggris — semi-otomatis, jujur
  dicatat di header file). Jumlah entri mis. farm_ai_agent 483 (28
  diterjemahkan), farm_ai_decision 514 (44), farm_ai 147 (15),
  farm_marketing 240 (18); total 29 modul ≈ 4.000 entri. farm_pos
  hanya 1 entri.

### 20c. Perbaikan instalasi (blocker B34–B37)

- **B34 — konflik `agri.evidence` (farm_mobile vs farm_subsidy batch 6):**
  batch 6 membuat `agri.evidence` konkret di `farm_subsidy` (res_id
  Integer, worker_id res.users, is_on_site Boolean biasa, evidence_hash
  via mixin, tanpa photo). Upstream `farm_mobile` mendefinisikan
  `agri.evidence` konkret sendiri (res_id Many2oneReference, worker_id
  hr.employee, photo wajib, is_on_site/evidence_hash computed,
  mail.activity.mixin). `farm_mobile/models/agri_evidence.py` ditulis
  ulang jadi ekstensi murni (`_inherit = 'agri.evidence'`, tanpa `_name`):
  tambah `photo` Binary TIDAK wajib, override compute `evidence_hash`
  (Char, store=True, precompute) dan `is_on_site` (Boolean, store=True,
  precompute; geofence hanya untuk farm.location/mrp.production),
  override `verify_evidence_integrity()` dengan tamper-alert message_post.
  `mail.activity.mixin` TIDAK ditambah. `res_id` tetap Integer,
  `worker_id` tetap res.users (keputusan: definisi batch 6 dipertahankan).
- **Geofence salah nama:** model asli `agri.geospatial.geofence`
  (`farm_core/models/geofencing.py`, punya `is_point_inside(lon, lat)` +
  `coordinates`); `farm.geofence` tidak ada. Diperbaiki `env['farm.geofence']`
  → `env['agri.geospatial.geofence']` di `farm_mobile` (agri_evidence.py,
  farm_checkin.py) dan `farm_safety/models/prevention_template.py`.
- **B35 — bentrok tabel relasi M2M alias-model (Odoo 18 menolak dua
  Many2many berbagi tabel+kolom):** `farm.training.certification`
  (`_name` + `_inherit='agri.training.certification'`) mewarisi relasi
  eksplisit `required_skills_ids` → install gagal `TypeError: Many2many
  fields... use the same table and columns`. Diperbaiki dengan override
  field di alias memakai tabel relasi sendiri
  (`farm_training_certification_agri_training_skill_rel`). Pola sama
  diperbaiki preemptif di `farm_knowledge/models/pest_disease.py`
  (alias `farm.pest.disease`): override `conventional_products`,
  `organic_products`, `affected_crops` dengan tabel relasi sendiri
  (`farm_pest_disease_conventional_rel`,
  `farm_pest_disease_organic_rel`, `farm_pest_disease_crop_rel`).
  Aman: `farm_mobile` farm.evidence (mixin M2M tanpa relasi eksplisit),
  `farm_supply_analytics` node mixin (tanpa M2M), `farm_marketing`
  passport plugins (tanpa M2M), `farm_gov` regulator plugin (tanpa M2M),
  `farm_agritourism` (M2M project.task sudah di-override upstream
  dengan tabel relasi berbeda).
- **B36 — bentrok `hr.employee.skill_ids` (farm_training):** core
  `hr_skills` (ter-install di test18) mendefinisikan
  `hr.employee.skill_ids` sebagai Many2many COMPUTED ke `hr.skill`;
  farm_training mendefinisikan ulang nama sama ke `farm.training.skill`
  sambil mempertahankan compute core → `ValueError: Wrong value for
  hr.employee.skill_ids: hr.skill()` saat registry load. Field farm
  di-rename jadi `farm_skill_ids` (tabel relasi sama
  `hr_employee_farm_training_skill_rel`) di
  `farm_training/models/hr_employee.py` (field + 2 pemakaian di
  `check_qualification_for_task`) dan `views/hr_employee_views.xml`.
- **B37 — import di-comment-out:** `farm_knowledge/models/__init__.py`
  upstream berisi `#from . import pest_disease`, sehingga
  `farm.pest.disease` tidak pernah terdaftar tapi ACL CSV merujuknya →
  `No matching record found for external id 'model_farm_pest_disease'`.
  Import di-uncomment. Re-audit (parsing import yang benar, bukan
  substring) mengonfirmasi ini SATU-SATUNYA file model yang tidak
  di-import di batch 7.
- **Gelombang install:** W1 farm_symbiosis 18.0.1.0.0 (exit 0). W2
  farm_knowledge/farm_safety/farm_insurance/farm_training: 3 ronde gagal
  (B35 → exit 255; B36 → exit 255; B37 → exit 255) lalu W2d exit 0.
  W3 (14 modul) exit 0, 0 Traceback. W4 farm_mobile + farm_pos exit 0
  (ikut ter-install point_of_sale 18.0.1.0.2, website, fleet). W5 rantai
  AI (8 modul) exit 0, 0 Traceback. Baris log berulang non-fatal di tiap
  install: `ERROR test18 odoo.tests.common: Importing test framework...`
  — install tetap sukses, bukan kegagalan.
- **Nama model salah di farm_ai_vision:** `llm.service` → benar
  `agri.ai.llm.service` (5 file: ai_image_analysis_prediction,
  ai_image_based_planning, ai_pest_disease_detection,
  ai_vision_risk_assessment, ai_visual_sorting). Controller
  `farm_ai_vision/controllers/ai_vision_api.py`: `ai.pest.disease.detection`
  → `agri.ai.pest.disease.detection`, `ai.visual.sorting` →
  `agri.ai.visual.sorting`, `ai.image.analysis.prediction` →
  `agri.ai.image.analysis.prediction`, `ai.vision.risk.assessment` →
  `agri.ai.vision.risk.assessment`, `ai.image.based.planning` →
  `agri.ai.image.based.planning`.
- **`is_toxic_to_fish` tidak didefinisikan di mana pun:**
  `farm_symbiosis/models/symbiosis_isl.py` membaca
  `product_id.is_toxic_to_fish` di `_compute_toxin_risk`. Ditambah
  `farm_symbiosis/models/product_template.py` (Boolean di product.template,
  default False) + import di `models/__init__.py`.

### 20d. Perbaikan sesudah install / selama simulasi (blocker B38–B51)

- **B38 — field `api_base_url` hilang (farm_ai_llm_integration):**
  `llm_service.py` membaca `config_id.api_base_url` di SEMUA pemanggilan
  provider, tapi TIDAK ADA model yang mendefinisikan field itu (parent
  `agri.ai.configuration` hanya punya `base_url`, tampil di form tapi
  tidak pernah dibaca service) → semua pemanggilan LLM akan crash
  AttributeError sebelum request terkirim. Ditambah
  `api_base_url = fields.Char('API Base URL',
  default='https://9router-go.hiddenlab.me/v1', ...)` di
  `agri.ai.llm.configuration` (`farm_ai_llm_integration/models/llm_config.py`)
  + `@api.onchange('provider')` (pindah dari OpenAI mengosongkan default
  gateway ke default publik provider itu; kembali ke OpenAI memulihkan
  default bila kosong) + field form diganti `base_url` →
  `api_base_url`. TIDAK ADA API key di kode mana pun.
  farm_ai_llm_integration → 18.0.1.0.1.
- **B39 — bug kurung kurawal ganda (farm_ai_llm_integration, blocker):**
  `llm_service.py` ditulis dengan `{{...}}` ganda di seluruh file (27
  pasang) — mis. `'messages': [{{'role': 'user', 'content': prompt}}]`
  adalah set literal berisi dict → `TypeError: unhashable type: 'dict'`
  pada SETIAP pemanggilan OpenAI (dan path embeddings/anthropic/google/
  hf/ollama/custom yang sama). Diganti semua `{{`→`{` dan `}}`→`}` di
  file itu saja (tidak ada escape f-string `{{` di sana; scan
  mengonfirmasi `{{` tidak muncul di file .py batch 7 lain). AST parse +
  py_compile OK. Versi 18.0.1.0.1 (upgrade sama dengan B38).
- **Bukan bug — `agri.ai.base.mixin.service` (revert):** edit awal di
  `farm_ai/models/ai_base.py` mengganti delegasi ke
  `agri.ai.base.mixin.service` dengan implementasi langsung, dengan klaim
  model itu tidak ada. Model itu ADA
  (`farm_ai/models/ai_services/ai_mixin_service.py`, di-import di
  `models/__init__.py`); edit itu juga menduplikasi satu baris `def`
  (IndentationError). File dipulihkan dari salinan eval dengan hanya
  konversi `models.Constraint` → `_sql_constraints` diterapkan ulang;
  delegasi utuh dan benar (`call_llm_service` menemukan service lewat
  refleksi dan menemukan `agri.ai.llm.service`).
- **EmbeddingMixin model salah (farm_core):**
  `farm_core/models/agri_mixins.py:444` memakai `env['llm.service']`
  (tidak ada) → `env['agri.ai.llm.service']` + guard
  (`if 'agri.ai.llm.service' not in self.env: return False`). Tidak ada
  model konkret yang mewarisi `agri.embedding.mixin` di batch 7, jadi fix
  ini benar tapi belum dieksekusi model konkret — catat jujur.
  farm_core 18.0.1.0.3 → 18.0.1.0.4.
- **B40 — KeyError `sale_order_id` (farm_agritourism, blocker pada
  rebuild `-u` penuh):** `sale.order.agri_task_ids =
  One2many('project.task', 'sale_order_id')` + `action_confirm` membuat
  task dengan `'sale_order_id'`, tapi core Odoo 18 `project.task` TIDAK
  punya field itu → `KeyError: 'sale_order_id'` di `setup_models`
  (terbukti di upgrade farm_core.0.4, exit 255 — walau start server biasa
  sempat load). Ditambah `sale_order_id = fields.Many2one('sale.order',
  ondelete='set null', index=True)` pada `project.task` di
  `farm_agritourism/models/sale_order.py`. farm_agritourism 18.0.1.1.0 →
  18.0.1.1.1; upgrade gabungan dengan farm_core exit 0, 0 Traceback.
- **B41 — `farm.location.child_internal_location_ids` (farm_core,
  blocker):** `farm.location` (`_name`, `_inherit='stock.location'`,
  prototype inheritance, tabel terpisah) mewarisi computed M2M
  `child_internal_location_ids` ke `stock.location`; compute warisan
  `self.search(...)` mengembalikan record farm.location → `ValueError:
  Wrong value for farm.location.child_internal_location_ids:
  farm.location(2,)` pada SETIAP pembacaan (terbukti lewat form
  auto-generated `farm.symbiotic.plot` — farm_symbiosis TANPA dir views,
  jadi form auto-generated dan mencantumkan field lokasi yang
  didelegasikan). Diperbaiki di `farm_core/models/land_location.py`
  (class FarmLocation): override field sebagai
  `Many2many('farm.location', compute='_compute_child_internal_location_ids',
  recursive=True)` + compute pencocokan yang mencari farm.location.
  farm_core → 18.0.1.0.5; upgrade exit 0; probe sesudah restart segar
  yang BENAR: errdlg 0, 0 pageerror, 0 Traceback.
- **B42 — CSV ACL di-comment-out (farm_ai, farm_csa):** kedua manifest
  me-comment-out `security/ir.model.access.csv`, sehingga TIDAK ADA
  aturan akses yang termuat → admin (uid 2) kena `Access Denied by ACLs
  for operation: read` pada `farm.csa.plan` / `farm.csa.subscription`
  (dan akan kena juga pada `agri.ai.*`). Audit semua 27 CSV batch 7 vs
  manifest menunjukkan HANYA 2 ini yang tidak terdaftar. Diperbaiki:
  uncomment keduanya + farm_ai dan farm_csa → 18.0.1.0.1; upgrade exit 0;
  5 baris ACL kini ada untuk CSA + model AI; form CSA terbukti ulang
  bersih. **Pelajaran:** audit ACL batch 7 awal (§20b) hanya memeriksa
  ISI csv, bukan apakah csv terdaftar di manifest — cek keduanya.
- **Cold-storage temperature log (farm_supply_logistics):**
  `_compute_is_alert` membaca `zone_id.humidity_min` / `humidity_max`
  yang TIDAK ADA di `cold.storage.zone` (hanya `humidity_level`) →
  AttributeError pada SETIAP pembuatan temperature-log dengan zone.
  Diperbaiki: guard `getattr(..., 'humidity_min', False)`; kelembapan
  hanya dicek bila zone benar-benar membawa range.
  farm_supply_logistics → 18.0.1.0.1; upgrade exit 0.
- **Kode aktivitas agritourism NewId (farm_agritourism):**
  `_compute_activity_code` memakai `f"...-{record.id:04d}"` → `TypeError:
  unsupported format string passed to NewId` pada setiap create.
  Diperbaiki: `rec_id = record.id if isinstance(record.id, int) else 0`.
  farm_agritourism → 18.0.1.1.2.
- **Related field feedback konsumen (farm_marketing):** `product_id =
  Many2one('product.template', related='lot_id.product_id')` —
  `lot_id.product_id` adalah varian product.product → recompute
  stored-related saat commit melempar `Wrong value for
  farm.consumer.feedback.product_id: product.product(327,)` dan me-rollback
  seluruh seksi patch. Diperbaiki: related jadi
  `'lot_id.product_id.product_tmpl_id'`. Dua field pola sama lainnya
  sudah benar (recall `farm_supply_analytics` product_id product.product
  ← `triggering_qc_id.lot_id.product_id`; klaim `farm_insurance`
  product_id product.template ← `policy_id.product_id` di mana policy
  product adalah product.template). farm_marketing → 18.0.1.0.1.
- **Gauge robot (farm_robotics):** form view `<field name="battery_level"
  widget="gauge" options="{'max_field': 100}" />` — GaugeField Odoo 18
  mensyaratkan `max_field` berupa NAMA FIELD string; integer 100 melempar
  `OwlError: Invalid props for component 'GaugeField': 'maxValueField' is
  not a string` + error dialog. Diperbaiki: options dihapus (default max
  gauge 100 = skala % baterai). farm_robotics → 18.0.1.0.1.
- **Domain cockpit (farm_dashboard):** action 1230 domain
  `[('is_agri_activity', '=', True)]` pada `project.task`, tapi
  `is_agri_activity` hanya didefinisikan di `project.project`
  (`farm_core/models/activity_operation.py:9`) → `ValueError: Invalid field
  project.task.is_agri_activity in leaf ...` pada setiap pembacaan cockpit
  (2 Traceback server). Diperbaiki: domain →
  `[('project_id.is_agri_activity', '=', True)]`. farm_dashboard →
  18.0.1.0.1. Action winemaking 1231 (`mrp.production`, domain
  `[('process_mode', '=', 'fermentation')]`) sudah bersih.
- **Kuirks operasi agritourism tanpa project (BUKAN diperbaiki di kode —
  aturan data):** `farm.agritourism.operation` mewarisi `project.task`;
  membuat tanpa `project_id` gagal `UserError: This task cannot be private
  because there are some timesheets linked to it` (hr_timesheet
  `_check_project_root`): sequence id operasi itu bertabrakan numerik
  dengan id project.task lama yang punya analytic line. Membuat DENGAN
  `project_id` berhasil (terbukti: OP2 id=3, project=5). Data simulasi
  selalu menyertakan `project_id`. Catat sebagai kuirks upstream.
- **Model abstrak (tanpa tabel, tanpa record — benar dilewati saat
  pembuatan data):** `gov.reporting.service`, `agri.a2a.protocol`,
  `agri.embedding.provider`. Konsumen konkret yang dipakai:
  `agri.a2a.message`, `gov.platform.config`.

### 20e. LLM — routing 9router-go / Ali Connection (instruksi king 11 Nov 07:07 WIB)

- LLM untuk modul AI batch 7 (`farm_ai_llm_integration` dan modul AI lain
  yang memanggil LLM) memakai **9router-go (Ali Connection) —
  https://9router-go.hiddenlab.me/v1, OpenAI-compatible** — BUKAN API
  eksternal berbayar (bukan OpenAI langsung) dan BUKAN mock bila gateway
  bisa dipakai.
- **JANGAN minta, mencatat, atau menyimpan API key apa pun** di
  kode/dokumen/file. Uji end-to-end live butuh key yang disediakan king di
  luar test bed; bila key tidak tersedia di test bed, uji alur sampai titik
  pemanggilan API (config endpoint + bentuk request) dan catat jujur bahwa
  verifikasi live menunggu key king. Jangan klaim integrasi live bila belum
  diuji dengan key sungguhan.
- Cara modul memanggil LLM: `requests.post` langsung (tanpa library
  `openai`) ke `{api_base_url}/chat/completions` (dan `/embeddings`)
  dengan header Bearer — lihat B38 (field `api_base_url` yang tadinya
  hilang) dan B39 (kurung ganda).
- Verifikasi (SIMULASI.md bagian batch 7): config DB id=2
  (provider=openai, api_base_url=https://9router-go.hiddenlab.me/v1,
  api_key_set=False, default_model=gpt-4o-mini, is_active=True,
  is_default=True); gateway terjangkau dari test bed (`curl .../v1/models`
  → 401 JSON gaya OpenAI `invalid_api_key`); uji mock (requests.post
  di-monkeypatch) menangkap URL + payload OpenAI-compatible dan
  `call_llm` success=True; uji live tanpa key: `call_llm` success=False,
  error `401 Client Error: Unauthorized for url: .../v1/chat/completions`
  — membuktikan request benar-benar sampai ke gateway. **Inferensi live
  TIDAK diklaim; menunggu key king.**
- Delegasi mixin: `agri.ai.base.mixin.call_llm_service` (via
  `agri.ai.base.mixin.service`) merutekan ke `agri.ai.llm.service` aktif
  dan mengembalikan dict error 401 yang sama (terbukti pada recordset
  `agri.ai.agent` kosong). `stock.lot` tidak punya `call_llm_service` /
  `action_sync_embedding` — sesuai harapan, ia tidak mewarisi mixin itu.

### 20f. Regresi kumulatif batch 1–6 sesudah batch 7 (B48–B51)

Regresi pertama (22 langkah, shot 1815–1836) menemukan 2 kegagalan nyata
di batch 1–5 — keduanya laten (bukan disebabkan perubahan batch 7, tapi
baru terungkap karena regresi ini membuka form-form itu):

- **B48 — widget check-in farm_mobile merusak form mrp.production
  (farm_mobile, blocker regresi):** view warisan farm_mobile menyisipkan
  `<widget name="farm_mobile_checkin" />` di form mrp.production. Template
  OWL-nya memakai `t-if="!navigator.onLine"` — template OWL tidak bisa
  melihat global `navigator` → `TypeError: Cannot read properties of
  undefined (reading 'onLine')` → OwlError + error dialog pada SETIAP
  pembukaan form produksi. Plus `OfflineStorage.cacheTasks([this.props.record.data])`
  — `record.data` berisi objek OWL yang tidak bisa di-clone IndexedDB →
  `DataCloneError: Failed to execute 'put' on 'IDBObjectStore'`. Plus
  prefetch SOP memanggil model `farm.knowledge.article` yang tidak ada
  (benar: `agricultural.knowledge`) → RPC reject tak tertangani.
  Diperbaiki: status online dilacak di state komponen (`is_online`,
  listener online/offline; template memakai `state.is_online`);
  cacheTasks hanya menerima snapshot plain-JSON `{id, name, state}` +
  try/catch di `offline_storage.js` (cache offline tidak boleh merusak
  form); prefetch SOP ke `agricultural.knowledge` + `.catch(()=>{})`.
  farm_mobile → 18.0.1.0.1.
- **B49 — chatter pada model delegasi tanpa mail.thread (farm_core,
  blocker regresi):** form `farm.activity` dan `farm.task` punya
  `<chatter>`, tapi modelnya tidak pernah mewarisi mail.thread (delegasi
  via `_inherits` ke project.project/project.task TIDAK membawa method
  Python) → `/mail/thread/data` melempar `AttributeError:
  'farm.activity' object has no attribute '_get_thread_with_access'` +
  error dialog. Diperbaiki: tambah `'mail.thread'` ke `_inherit`
  keduanya (preseden core: hr.employee `_inherits` res.users +
  `_inherit` mail.thread). farm_core → 18.0.1.0.6.
- **B50 — `_inherit` ganda menghapus mail.thread
  (farm_esg_compliance, blocker regresi):**
  `AgriTripleBottomLineMetrics` meng-assign `_inherit` DUA kali di class
  yang sama (`['mail.thread', 'mail.activity.mixin']` lalu
  `['agri.sustainability.mixin']`) — Python hanya menyimpan yang kedua,
  mail.thread hilang diam-diam, chatter form crash sama seperti B49.
  Diperbaiki: gabung jadi satu list
  `['mail.thread', 'mail.activity.mixin', 'agri.sustainability.mixin']`.
  farm_esg_compliance 18.0.1.0.2 → 18.0.1.0.3. Probe shell atas 29 model
  yang view-nya punya `<chatter>` menemukan tepat 3 tanpa mail.thread:
  farm.activity, farm.task, agri.triple.bottom.line.metrics — ketiganya
  diperbaiki; 26 lainnya OK.
- **B51 — `_inherit` ganda di FarmSupplyChainNode (farm_supply_analytics,
  BUKAN bug — revert):** percobaan menggabungkan
  `['agri.supply.chain.node.mixin', 'supply.chain.node.mixin']` melempar
  `TypeError: Cannot create a consistent method resolution order (MRO)`
  saat upgrade (exit 255) — `supply.chain.node.mixin` sendiri
  `_inherit`s `agri.supply.chain.node.mixin`, jadi ia harus mendahului
  parent-nya di MRO. Daftar tunggal upstream
  `['supply.chain.node.mixin']` SUDAH menarik mixin agri secara transitif;
  dikembalikan seperti semula + komentar penjelas. **Pelajaran:** sebelum
  menggabungkan `_inherit` ganda, periksa apakah satu parent mewarisi
  parent lainnya — penggabungan naif memecahkan MRO. farm_supply_analytics
  tetap 18.0.1.0.1 (upgrade ulang exit 0).
- **Re-run regresi (8 langkah, shot 1837–1844):** farm.activity form 1,
  farm.task form 1, TBLM form 1, mrp.production form 169, list
  farm.supply.chain.node, list farm.checkin, intervention form 12, lot
  form 280 — semua errdlg=0, TOTAL pageerrors 0, TOTAL console errors 2
  (pasangan tunnel, lihat §20g), 0 Traceback server. Upgrade 4 modul
  (farm_core, farm_esg_compliance, farm_supply_analytics, farm_mobile)
  exit 0, 0 Traceback, "Modules loaded".

### 20g. Artefak console + jebakan operasional batch 7

- **Artefak tunnel — TERIDENTIFIKASI:** pasangan `Failed to load resource:
  net::ERR_TUNNEL_CONNECTION_FAILED` di tiap run berasal dari
  `https://fonts.googleapis.com/css?family=Inter:300,300i,400,400i,700,700i&display=swap`
  (dan `Inter Tight`) — halaman login/web client memuat font Google
  Inter, gagal lewat proxy sandbox (tidak ada internet ke Google Fonts
  dari browser sandbox). Bukan error modul. Probe `requestfailed`
  membuktikannya (`browser-b7-probe-prod.py`).
- **Artefak service worker:** `Service worker registration failed`
  (chromium_headless_shell tidak bisa mendaftarkan service worker Odoo) —
  difilter dari hitungan console error di semua run, seperti batch 6.
- **Jebakan server basi (terbukti 2×, AGENTS.md):** skrip install/upgrade
  hanya membunuh PID odoo PERTAMA; child worker selamat dan terus memegang
  port 8071, sehingga "restart" diam-diam gagal (instance baru tidak bisa
  bind dan mati) dan browser menguji kode BASI. Terbukti pada PID 8247
  (bertahan melewati upgrade farm_core.0.5; fix symplot tampak gagal sampai
  8247 dibunuh via PID eksplisit). Sesudah SETIAP restart: verifikasi port
  8071 bebas (`ss -tln | grep 8071`) dan konfirmasi PID BARU yang melayani
  sebelum klaim browser apa pun.
- **Jebakan `pkill` self-kill:** `pkill -f "odoo/odoo-bin -c odoo.conf"`
  langsung di exec shell mencocokkan cmdline shell itu sendiri dan
  SIGTERM shell-nya. Bunuh hanya via PID eksplisit, atau pola terfragmentasi
  `P='odoo-bi'; P="${P}n"; pgrep -f "$P"`.
- **VM replacement (11 Nov ~01:50 WIB):** VM diganti di tengah bukti POS —
  uptime 0 mnt, /tmp terhapus total (semua skrip/log `/tmp/b7_*` hilang),
  user `pgtest` + `/opt/pgserver` hilang, PG + Odoo mati. Dipulihkan per
  AGENTS.md (useradd pgtest uid 1001 + rebuild /opt/pgserver dari venv
  odoo14-test + copy `.so*` dari `pgserver.libs/` + `chmod -R a+rX
  /opt/pgserver` + start PG dari `~/workspace/pgrun` + start Odoo);
  data test18 UTUH (92 modul farm installed). Workspace selamat
  (`~/workspace/odoo-farm-port-18/` + `simulasi/` utuh) — skrip browser
  yang tinggal di workspace bisa langsung dipakai ulang; skrip `/tmp`
  harus dibuat ulang bila dibutuhkan lagi.
- **POS `/pos/ui` tidak pernah mencapai `networkidle`** (long-polling POS)
  → pakai `domcontentloaded` + sleep manual di probe POS.
- **Perangkap ID transient:** `agri.cost.calculation` adalah TransientModel
  (record bisa hilang oleh autovacuum, pola O-B6R1-1); `farm.task` /
  `agri.triple.bottom.line.metrics` tidak punya record sampai dibuat
  (`/tmp/b7_regdata.py` — hilang bersama /tmp; dibuat ulang dari pola
  yang didokumentasikan di SIMULASI.md bila perlu).

### 20h. Versi akhir batch 7 di test18 (dari DB `ir_module_module`)

farm_agritourism 18.0.1.1.2, farm_ai 18.0.1.0.1, farm_ai_agent 18.0.1.0.0,
farm_ai_decision 18.0.1.2.1, farm_ai_llm_integration 18.0.1.0.1,
farm_ai_robotics 18.0.1.0.0, farm_ai_vision 18.0.1.0.0, farm_crisis
18.0.1.0.0, farm_csa 18.0.1.0.1, farm_dashboard 18.0.1.0.1,
farm_data_security 18.0.1.2.0, farm_disaster_risk 18.0.1.0.0, farm_gov
18.0.1.0.0, farm_insurance 18.0.1.0.0, farm_knowledge 18.0.1.1.0,
farm_label 18.0.1.0.0, farm_marketing 18.0.1.0.1, farm_mobile 18.0.1.0.1,
farm_multi_farm_equipment 18.0.1.0.0, farm_multi_farm_procurement
18.0.1.0.0, farm_multi_farm_quality 18.0.1.0.0, farm_pos 18.0.1.0.0,
farm_robotics 18.0.1.0.1, farm_safety 18.0.1.0.0, farm_supply_analytics
18.0.1.0.1, farm_supply_logistics 18.0.1.0.1, farm_supply_quality
18.0.1.0.0, farm_symbiosis 18.0.1.0.0, farm_training 18.0.1.0.0.
Juga berubah untuk batch 7: farm_core 18.0.1.0.6, farm_esg_compliance
18.0.1.0.3.

### 20i. Sisa sesudah batch 7

- 4 stub tanpa manifest (`farm_finance_advanced`, `farm_finance_loan`,
  `farm_logistics`, `farm_supply_chain_smart`) menunggu upstream.
- 11 modul China-specific tetap dikecualikan (§19b).
- Inferensi LLM live: TERBUKTI via UI di Simulasi FINAL (§21) — jangan
  klaim menunggu key lagi. Key king sudah tersimpan di config test18 id 2.
- POS: dashboard + layar jual + modal Opening Control + pembuatan sesi
  terbukti 0-error; validasi sesi ke status `opened` via klik browser
  TERCAPAI di Simulasi FINAL (§21, sesi 3 opened). Satu sesi uji
  tertinggal `opening_control` (Bakery Shop/00000 id 4) — data uji, aman
  dibiarkan/ditutup manual.
- Batch 8 diputuskan parent sesudah laporan batch 7.


## 21. Simulasi FINAL — perbaikan B52–B54 (11 Nov 2026)

Simulasi kumulatif PENUH terakhir atas perintah king ("coba simulasi kan
semuanya"): rantai batch 1–7 dari nol data baru, 98 modul installed,
247 screenshot (shot 1854–2100), 0 pageerror + 0 console error
non-artefak + 0 errdlg sesudah perbaikan. Detail: SIMULASI.md bagian
"Simulasi FINAL". Tiga blocker baru ditemukan + diperbaiki + terverifikasi
di ronde ini:

### B52 — plugin gov_audit crash di setiap post_done (`farm_gov` 18.0.1.0.1, `farm_marketing` 18.0.1.0.2)

`farm_gov/models/gov_audit.py:106` membaca
`intervention.company_id.gs1_gln` — field `gs1_gln` hidup di
`res.partner` (`farm_core/models/res_partner.py:12`), BUKAN
`res.company`. Akibat: `AttributeError` di setiap penyelesaian
intervensi (plugin error ditelan framework, workflow tetap done, tapi
snapshot audit tidak pernah terbuat). Laten di fungsi yang sama:
`"operator_id": getattr` (builtin mentah — `json.dumps` akan TypeError)
dan `responsible_id.name` tanpa guard. Pola sama di
`farm_marketing/models/traceability_passport.py:152`
(`lot.company_id.gs1_gln`). Fix: `getattr(company.partner_id,
'gs1_gln', None) or '0000000000000'`; `operator_id` →
`responsible_id.id`/None; guard `location_id`/`responsible_id`.
Verifikasi: intervensi 110 → done, snapshot +1 (id 3); 0 Plugin Error
di log sesudah restart.

### B53 — plugin compliance singleton di pre_confirm tanpa task (`agri_intervention` 18.0.1.0.3)

`agri_intervention/models/intervention_plugins.py:233`
`_trigger_withdrawal_sync` memanggil method di
`intervention.agri_task_id` kosong → `Expected singleton:
project.task()` di setiap pre_confirm MO/intervensi tanpa task
(terlihat saat `_post_inventory` MO saus). Fix: guard `if not
getattr(intervention, 'agri_task_id', False): return`. Verifikasi: MO
saus 321 tanpa task → `action_confirm()` bersih.

### B54 — form `agri.ai.market.prediction` crash GaugeField (`farm_ai_decision` 18.0.1.2.2)

`farm_ai_decision/views/ai_market_prediction_views.xml:29`:
`options="{'max_field': 100}"` (integer) → OwlError "maxValueField is
not a string", form tidak bisa dibuka sama sekali. Kelas yang sama
dengan B46 (farm_robotics, batch 7); 5 view lain memakai string
(`'100'`/`'30'`) dan lolos. Fix mengikuti B46 persis: hapus option
(confidence_score persen, default max 100 sudah tepat). Verifikasi:
probe ulang form id 3 (shot 2089) → errdlg=0.

### Batasan lama yang TERTUTUP di Simulasi FINAL

- Inferensi LLM live via UI: form config id 2 tidak punya tombol "Test
  Connection" (metode `test_connection()` ada tapi tidak diekspos di
  view) — tombol UI yang ada adalah "Test API Call" di form service id
  2; diklik via browser → call_count 2→4, error 0; agent FINAL id 2
  "Execute Agent" → status Recommended + jawaban Gemini sungguhan di
  `output_data.llm_response`. `api_key` ter-mask (`password="True"`).
- Validasi sesi POS ke `opened` via klik browser: TERCAPAI ronde ini —
  klik `.modal .btn-primary:has-text('Open Register')` di modal Opening
  Control → sesi 3 `opening_control` → `opened` (POS/00001). Sesi
  Bakery id 4 masih `opening_control` (sisa B7).
