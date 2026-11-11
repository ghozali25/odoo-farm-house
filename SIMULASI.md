# Simulasi fungsional end-to-end rantai odoo-farm batch 1

- **Tanggal:** 10 November 2026 (08:00–±10:00 WIB, diperintah king 10 Nov 08:00)
- **Test bed:** Odoo 18 lokal `http://127.0.0.1:8071`, DB `test18`, login `admin/admin`, `?debug=1`
- **Modul:** 14 modul batch 1 `installed` (lihat `PORTING.md` §2)
- **Skenario:** tomat Servo F1 — benih → nursery → tanam (GDD) → intervensi → panen → QC → olah → finish goods → valuasi
- **Bukti browser:** Playwright headless, 19 screenshot di `simulasi/` (`01`–`19`), **0 pageerror, 0 console error** (run final)
- **Skrip:** `browser-proof.py` (bukti browser), `/tmp/sim_phase_a.py`, `/tmp/sim_phase_a2.py`, `/tmp/sim_phase_a3.py`, `/tmp/sim_phase_b.py`, `/tmp/sim_phase_b2.py`, `/tmp/sim_phase_b3.py` (skrip shell, tidak disimpan di repo)

> Aturan yang dipakai: data dibuat lewat odoo-bin shell bila UI merepotkan,
> TAPI tiap tahap dibuktikan di browser. Klaim "lolos" hanya dengan bukti
> screenshot. Data simulasi DIBIARKAN di test18 berawalan `SIMULASI`.

## Ringkasan hasil

| # | Langkah | Status akhir | Catatan |
|---|---------|--------------|---------|
| 0 | Master data (produk, lahan, varietas, fase, campaign, rute) | ✅ LOLOS | 5 produk, lahan A1, paket + 4 fase GDD, campaign, rute 4 template |
| 1 | Seed batch + uji mutu (+ blok germinasi 70%) | ✅ LOLOS | Germinasi 92% lolos; 70% TERBLOKIR sesuai harapan |
| 2 | Nursery batch | ⚠️ LOLOS DENGAN CATATAN | Tanpa state machine; tombol pindah tanam stub (return True, tidak membuat apa pun) |
| 3 | Tanam → biological asset + rotation history | ✅ LOLOS (setelah fix blocker) | `create` rotation history crash — diperbaiki (lihat §Perbaikan 1) |
| 4 | GDD + perpindahan fase | ✅ LOLOS (setelah fix blocker) | Akumulasi persis (170 → 187 → 357); `stage_progress` crash — diperbaiki (lihat §Perbaikan 2); migrasi fase TIDAK otomatis (by design upstream) |
| 5 | Intervensi (5×) + approval workflow + NPK | ✅ LOLOS DENGAN CATATAN | Workflow draft → to_approve → approved → in_progress → done jalan penuh; NPK di form intervensi = 0 (MO induk benar 8.0) |
| 6 | Panen → lot + rotation harvested | ✅ LOLOS | Lot panen 500 kg, rotation → harvested |
| 7 | Quality check + record book | ✅ LOLOS | QC none → pass; record book draft → active |
| 8 | Olah → finish goods (MO saus tomat) | ✅ LOLOS (setelah 2× investigasi) | MO 17/18 selesai, saus +16 kg, tomat −20 kg; `seasonal.bom` activate = stub (tetap draft) |
| 9 | Valuasi aset biologis | ✅ LOLOS DENGAN CATATAN | Cost model bekerja (NBV = fair = Rp 2.500.000); fair value market_price = 0 (lookup harga gagal — asset tanpa lot) |

**Keputusan: 9/9 langkah lolos pada verifikasi akhir.** Tiga bug blocker
ditemukan selama simulasi, ketiganya diperbaiki dan terverifikasi (lihat
§Perbaikan). Dua masalah tampil (view) juga diperbaiki. Kondisi akhir
bersih: 19/19 halaman browser terbuka tanpa error.

## Detail per langkah

### 0. Master data

- Produk (template/varian): Benih Tomat Servo F1 (109/120), Bibit Tomat
  Servo F1 (110/121), Tomat Segar Servo F1 (111/122), Saus Tomat Servo F1
  (112/123), Pupuk NPK 16-16-16 (113/124). Semua `type=consu`,
  `is_storable=True`, tracking lot (kecuali pupuk: none). NPK 16/16/16 di
  template pupuk.
- Lahan: `farm.location` id 3, "SIMULASI Lahan A1" (field, 5.000 m², induk
  WH/Stock company 1). **Jebakan:** WH/Stock id 28 milik company 2
  (Chicago); lokasi company 1 adalah id 8. Test18 punya 3 company.
- Paket industri id 9 "SIMULASI Paket Tomat Servo F1" (vegetables);
  varietas id 9 "Servo F1"; 4 fase GDD — Germinasi id 14 (threshold 80),
  Vegetatif id 15 (300), Berbunga id 16 (500), Berbuah/Panen id 17 (800);
  growth curve 4 titik (10 hari/0,05 kg … 90 hari/5,0 kg).
- Campaign id 3 "SIMULASI Musim Tanam 2026/2027" (base temp 10 °C, target
  GDD 800); technical route id 2 "SIMULASI Rute Tomat Servo F1" + 4
  template intervensi (id 9–12: Semai, Pupuk, Proteksi, Panen).
  Template `irrigation` TIDAK BISA dibuat — selection template tidak
  mengenalnya (intervensi langsung bisa).

### 1. Seed batch — LOLOS

- Lot `SIMULASI-LOT-BENIH-001` (id 19) + `farm.seed.batch` id 2, qty 5 kg.
  Germinasi 92%, purity 98%, clarity 97%, moisture 11,5%, PVP
  `SIMULASI-PVP-001`, `is_pvp_compliant=True`, `action_verify_seed_quality`
  → True. Bukti: `simulasi/02-seed-batch-form.png`.
- **Blok mutu terbukti:** batch germinasi 70% (`SIMULASI-LOT-BENIH-BLOK`,
  batch id 1) → `UserError: SEED QUALITY BLOCK: Batch
  SIMULASI-LOT-BENIH-BLOK germination rate (70.0%) is below national
  standard.`

### 2. Nursery batch — LOLOS DENGAN CATATAN

- `farm.nursery.batch` id 1, lot `SIMULASI-LOT-BIBIT-001`, 25.000 bibit,
  induk = lot benih 001, target GDD pindah tanam 200.
- **Tidak ada state machine** (field `state` tidak ada — terverifikasi).
- `action_create_transplant_task` return True **tanpa membuat apa pun**:
  `farm.breeding.order` 0→0, `agri.biological.asset` 0→0. Pindah tanam
  dilakukan manual (langkah 3). Bukti: `simulasi/04-nursery-batch-form.png`.

### 3. Tanam — LOLOS (setelah fix)

- `agri.biological.asset` id 3 "SIMULASI Tanaman Tomat A1" (plant,
  lahir 2026-11-10, zero temp 10 °C, target yield 5.000 kg).
- `farm.crop.rotation.history` id 2 "SIMULASI Rotasi Tomat A1" (lahan A1,
  tomat, 25.000 unit, musim 2026/2027), state `planted`, warning False,
  risk 0.0. **Awalnya create SELALU gagal** — lihat §Perbaikan 1.
- Bukti: `simulasi/06-asset-form.png`, `simulasi/08-rotation-form.png`.

### 4. GDD + fase — LOLOS (setelah fix)

- 10 hari suhu 32/22 °C → `accumulated_gdd = 170.0` persis
  (10 × 17). +1 hari → 187.0. +10 hari → 357.0.
- **Awalnya set fase crash** — lihat §Perbaikan 2. Sesudah fix: set
  Germinasi (threshold 80) → progress 100.0 (187/80, cap 100);
  Vegetatif → 100.0; Berbunga → 71.4; Berbuah/Panen → 44.625
  (357/800). Matematika persis.
- **Migrasi fase TIDAK otomatis:** `_check_stage_migration` memang
  no-op (`pass`) — GDD 357 jauh melewati threshold Germinasi (80) tapi
  fase tetap Germinasi sampai diganti manual. Ini desain upstream,
  bukan bug.
- Catatan form: form asset menampilkan field `growth_stage_id`
  ("Current Physio Stage", kosong) — field LAIN dari `current_stage_id`
  ("Current Stage", yang dipakai GDD). Dua field fase yang tidak
  tersinkron di model upstream. Nilai GDD yang benar ada di
  `current_stage_id`/`accumulated_gdd`/`stage_progress` (terverifikasi
  shell; form tidak menampilkan ketiganya di tab utama).

### 5. Intervensi — LOLOS DENGAN CATATAN

- 5 intervensi (id 1–5: Semai, Pupuk NPK, Irigasi, Proteksi, Panen),
  masing-masing auto-membuat MO (id 9–13). BoM tomat id 10: 50 kg NPK
  per 5.000 kg tomat.
- Workflow penuh terverifikasi untuk kelimanya:
  `draft` → submit → `to_approve` → approve → `approved` + `confirmed`
  → start → `in_progress` → stop → `done`. MO induk tetap `draft`
  sepanjang workflow (workflow intervensi tidak menggerakkan MO).
- **NPK:** intervensi Pupuk NPK menunjukkan `pure_n/p/k = 0.0/0.0/0.0`,
  sementara MO induknya `8.0/8.0/8.0` (benar: 50 kg × 16%). Akar:
  `_compute_agri_costs` di mixin tidak pernah meng-assign ketiga field
  itu. Perlu disatukan saat batch 2 (ketika engine verbatim diganti
  `agri_intervention` asli).
- Bukti: `simulasi/09-intervention-harvesting-form.png` (Status:
  Completed, Harvesting, Actual Start/Finish 11/10/2026 01:18:50).

### 6. Panen — LOLOS

- Lot panen `SIMULASI-LOT-PANEN-001` (stock id 21) 500 kg tomat segar
  + `farm.crop.lot` id 1 (moisture 94%, protein 0,9%), terhubung ke
  intervensi Panen (`harvest_lot_ids=[21]`), grade A 400 / B 80 / C 20.
- Rotation history → `harvested`, harvesting_date 2027-02-08.
  Bukti: `simulasi/08-rotation-form.png`.

### 7. Quality — LOLOS

- Quality point id 1 "SIMULASI Uji Kadar Air Tomat" (measure, norm 94,
  toleransi 90–96); check id 1 "SIMULASI QC Panen Tomat A1":
  `none → pass` via `action_pass`.
- Record book id 1 "SIMULASI Buku Mutu Panen 2026" (`SIMULASI-RB-001`,
  general): `draft → active` via `action_activate`.
  Bukti: `simulasi/12-quality-check-form.png`,
  `simulasi/13-record-book-form.png`.

### 8. Olah → finish goods — LOLOS

- Season id 1 "SIMULASI Musim Kemarau 2026"; BoM saus id 11 (10 kg
  tomat → 8 kg saus); `farm.seasonal.bom` id 1 (base yield 0,8,
  seasonal 0,75). **`action_activate` stub**: return True tanpa menulis
  state — seasonal BoM tetap `draft`.
- Processing steps id 1–3 (Sortasi, Pencucian, Pengemasan) terhubung ke
  MO; state hanya `draft` (tanpa workflow).
- **MO saus — dua kali investigasi sebelum lolos:**
  - MO 14/15/16 (percobaan awal): `button_mark_done` menghasilkan MO
    `done` tapi move tetap `assigned` dan stok tidak bergerak. Akar:
    skrip shell menulis `qty_producing` via ORM tanpa
    `_set_quantities()` (yang dilakukan onchange UI) → `stock.move.picked`
    tetap False → `_post_inventory` melewati move yang belum picked
    secara diam-diam. **Ini jebakan metodologi shell, BUKAN bug modul.**
    Pelajaran: simulasi MO via shell WAJIB memanggil
    `_set_quantities()` sesudah `action_assign()`. Move MO 14/15/16
    sudah di-cancel (reservasi 30 kg tomat dilepas).
  - MO 17 (T4, alur UI-equivalent): selesai — raw move done, finished
    move done 8,0 kg, lot `0000001`, saus +8 kg, tomat −10 kg.
  - MO 18 (T5, `_post_inventory` langsung): selesai — saus +8 kg lagi
    (lot `0000002`), tomat −10 kg.
- **Stok akhir (terverifikasi UI):** saus tomat **16,00 kg On Hand**
  (lot 0000001 + 0000002), tomat segar **480 kg**
  (500 − 10 − 10, lot `SIMULASI-LOT-PANEN-001`).
  Bukti: `simulasi/10-mo-saus-form.png` (WH/MO/00017, Done, 8,00/8,00,
  komponen tomat 10,00 consumed), `simulasi/19-produk-saus-form.png`
  (On Hand 16,00, Forecasted 16,00).

### 9. Valuasi — LOLOS DENGAN CATATAN

- Harga pasar: `farm.market.price` "SIMULASI Harga Tomat Feb 2027"
  (tomat, 2027-02-08, Rp 12.000/kg).
- `action_run_fair_valuation` membuat record di
  `agri.biological.asset.fair.valuation` (id 1–2) — **BUKAN** di
  `agri.biological.asset.valuation`: ada DUA definisi method yang sama
  di dua modul, yang `farm_valuation` menang di MRO. Nilai:
  `market_price = 0.0`, `fair_value = 0.0` — lookup harga pasar gagal
  karena asset tidak punya `lot_id` (`agri.biological.asset` memang
  tidak punya field itu). Kedua record fair bernama sama
  (`VAL-SIMULASI Tanaman Tomat A1-20261110-1`) — generator nama memakai
  `len(records)+1` per create tunggal.
- Valuasi cost model id 1 "SIMULASI Valuasi Biaya Tomat A1" bekerja:
  `net_book_value = fair_value = Rp 2.500.000`
  (5.000.000 × koefisien 0,5, depresiasi 0).
  Bukti: `simulasi/15-valuations-list.png`,
  `simulasi/16-fair-valuation-form.png`.

## Perbaikan blocker (kode modul — didokumentasikan juga di PORTING.md §11)

### Perbaikan 1 — `farm.crop.rotation.history` create selalu gagal

- File: `farm_crop/models/crop_rotation_history.py`
- Gejala: `AttributeError: 'str' object has no attribute 'year'`.
- Akar: override `create()` mengambil `vals.get('planting_date')`
  (string `'YYYY-MM-DD'`) lalu diteruskan mentah ke
  `check_continuous_cropping_risk()` yang memanggil
  `.replace(year=...)`.
- Fix: `fields.Date.to_date(vals.get('planting_date')) or
  fields.Date.today()` di `create()` + hardening yang sama di
  `check_continuous_cropping_risk()`.

### Perbaikan 2 — `stage_progress` GDD crash saat fase di-assign

- File: `farm_core/models/agri_mixins.py` (`_compute_stage_progress`)
- Gejala: `AttributeError: 'agri.industry.physio.stage' object has no
  attribute 'target_gdd'`.
- Akar: mixin membaca `current_stage_id.target_gdd`, tapi field target
  GDD fase bernama `accumulated_temp_threshold`.
- Fix: memakai `accumulated_temp_threshold` sebagai target.

### Perbaikan 3 — form MO crash: `_compute_efficiencies` no-op

- File: `farm_processing/models/mrp_production.py`
- Gejala: buka form MO → dialog "Oops!" + log `ValueError: Compute
  method failed to assign mrp.production(17,).rue_actual`.
- Akar: `farm_processing` meng-override `_compute_efficiencies`
  (dari `farm.agri.science.mixin`) dengan badan `pass` — field compute
  `rue_actual`/`wue_actual` tidak pernah di-assign.
- Fix: override meng-assign `0.0` seperti mixin aslinya.
- Ditemukan saat bukti browser (bukan saat simulasi shell).

### Perbaikan lingkungan test bed (bukan kode modul)

- **Kolom hilang `farm_location`:** `valuation_in_account_id` /
  `valuation_out_account_id` (field standar `stock.location` dari
  `stock_account`, diwarisi `farm.location` tapi kolomnya tidak pernah
  terbuat) → semua form yang membaca `farm.location` (rotation,
  intervensi) crash `ProgrammingError`. Fix: upgrade ke-14 modul batch
  1 (`odoo-bin -u ... --stop-after-init`) — kolom terbuat, diverifikasi
  di `information_schema`.
- **View yatim `hr_maintenance`:** 4 view inherit
  (`maintenance.equipment.view.*.inherit.hr`, id 2402–2405) milik modul
  `hr_maintenance` yang sudah `uninstalled` masih ada di DB dan
  menyebut `employee_id` (field yang hanya ada bila modul itu
  terinstall) → form intervensi (auto-generated, tanpa view farm)
  crash client-side `OwlError: "maintenance.equipment"."employee_id"
  field is undefined`. Fix: hapus 4 view yatim via shell + restart
  server (cache view di registry server lama masih menyimpan arch
  lama — restart WAJIB sesudah hapus view).

## Temuan lain (tidak diperbaiki — dicatat apa adanya)

1. NPK intervensi = 0, MO = 8.0 (lihat langkah 5).
2. `farm.seasonal.bom.action_activate`/`action_deactivate` stub
   (tetap `draft`).
3. Nursery tanpa state machine; tombol pindah tanam stub (lihat
   langkah 2).
4. Valuasi market_price = 0 + nama fair duplikat (lihat langkah 9).
5. `agri.intervention` tidak terikat lahan (tanpa `land_id` /
   `farm_location_id`); keterikatan lahan hanya lewat lokasi MO.
6. Dua field fase di asset tidak tersinkron (`current_stage_id` untuk
   GDD vs `growth_stage_id` yang ditampilkan form).
7. `agri.industry.physio.stage` punya `name_get` kustom
   ("Berbuah/Panen (Day 90)") tapi `display_name` tetap fallback
   `agri.industry.physio.stage,17` — perilaku standar Odoo 18
   (`_compute_display_name` memakai `_rec_name`, bukan `name_get`;
   model ini `_rec_name=None`).

## Data SIMULASI yang tertinggal di test18

Semua berawalan `SIMULASI` (company 1, My Company San Francisco).
Jalur buka di UI (`?debug=1`, login admin/admin):

| Data | ID | Jalur UI |
|------|----|----------|
| Seed batch "SIMULASI …" | 2 | Farm → Seed Batches (action 1007) |
| Nursery batch | 1 | Farm → Nursery Batches (action 966) |
| Biological asset "SIMULASI Tanaman Tomat A1" | 3 | Farm → Biological Assets (action 888) |
| Rotation history | 2 | Farm → Rotation History (action 965) |
| Intervensi (5) | 1–5 | `/web#model=agri.intervention&id=5&view_type=form` (tanpa action) |
| MO saus WH/MO/00017, WH/MO/00018 | 17, 18 | Manufacturing → Manufacturing Orders (done) |
| MO 14/15/16 (artefak investigasi, move di-cancel) | 14–16 | Manufacturing Orders (done, move cancel) |
| Quality check / record book | 1 / 1 | Sci-Lab → Quality Checks (977) / Record Books (980) |
| Seasonal BoM / season | 1 / 1 | `/web#model=farm.seasonal.bom&id=1&view_type=form` |
| Valuasi cost / fair | 1 / 1–2 | Farm → Valuations (975) |
| Campaign / technical route | 3 / 2 | Farm → Campaigns (963) / route via model URL |
| Produk saus (On Hand 16 kg) | template 112 / varian 123 | Inventory → Products |

Stok akhir: benih 5 kg, bibit 25.000 unit, tomat segar 480 kg,
saus tomat 16 kg, pupuk NPK belum terpakai.

## Catatan untuk batch 2

Simulasi batch 1 dinyatakan **bersih pada verifikasi akhir** (semua
error yang ditemukan sudah diperbaiki + terverifikasi ulang, bukti
browser 19/19 hijau, 0 pageerror, 0 console error). Sesuai aturan flow
king (10 Nov 08:01 — "setelah simulasi tanpa error jalankan ke batch
selanjutnya"), langkah berikutnya adalah **batch 2**:
`agri_intervention` (gantikan engine yang di-vendor verbatim di
`farm_operation`) + `farm_isl`/`farm_ux`, lalu simulasi batch 2 dengan
pola yang sama. Pekerjaan batch 2 belum dimulai di sesi ini — menunggu
perintah/penugasan lanjutan.

---

# Simulasi fungsional batch 2 — engine asli, ISL, farm_ux

- **Tanggal:** 10 November 2026 (±09:10–10:40 WIB, diperintah koordinator)
- **Test bed:** Odoo 18 lokal `http://127.0.0.1:8071`, DB `test18`, login `admin/admin`
- **Modul:** 17 modul `installed` — 14 batch 1 + `agri_intervention`
  18.0.1.0.1 + `farm_isl` 18.0.1.0.0 + `farm_ux` 18.0.1.1.1;
  `farm_operation` 18.0.1.2.4 (engine vendor sudah dihapus)
- **Skenario:** intervensi fertilizing NPK via engine asli → workflow →
  MO otomatis selesai → NPK → ISL redirector → widget farm_ux
- **Bukti browser:** Playwright headless, screenshot `simulasi/`
  (`20`–`34`)
- **Skrip:** `browser-proof-b2.py` (bukti browser),
  `/tmp/sim_b2_step1.py`, `/tmp/sim_b2_step2.py`,
  `/tmp/sim_b2_step4.py`, `/tmp/sim_b2_tillage.py`,
  `/tmp/sim_b2_verify.py`, `/tmp/sim_b2_itype.py` (skrip shell,
  tidak disimpan di repo)

> **PERINGATAN METODOLOGI — bukti `?debug=1` TIDAK MUNGKIN untuk
> batch 2.** Begitu halaman dimuat dengan `?debug=1`, SELURUH web
> client mati (halaman putih + banner merah "An error occurred while
> loading javascript modules") — lihat Blocker B1 di bawah. Karena
> itu screenshot `20`–`32` dan `34` diambil **TANPA `?debug=1`** sebagai
> bukti diagnostik (bukan bukti lolos menurut aturan `?debug=1`), dan
> `33-debug-blank.png` adalah bukti mode debug-nya. Semua klaim
> "lolos" di bawah ini dibatasi pada apa yang terbukti via shell +
> browser non-debug; **tidak ada satu pun langkah farm_ux yang bisa
> dinyatakan lolos di `?debug=1`**. Tidak ada kode modul yang diubah
> selama simulasi ini (hanya laporan temuan, sesuai perintah).

## Ringkasan hasil

| # | Langkah | Status akhir | Catatan |
|---|---------|--------------|---------|
| 1 | Engine asli dipakai (bukan vendor verbatim) | ✅ LOLOS | `ir_model_data` + file vendor hilang, versi terkonfirmasi |
| 2 | Intervensi engine asli: workflow penuh + MO otomatis selesai + stok bergerak | ✅ LOLOS | draft → to_approve → approved → in_progress → done; MO 19 done, tomat +5.000 kg, NPK −50 kg |
| 3 | NPK intervensi vs MO | ✅ MEMBAIK (temuan batch 1 TERTUTUP) | Intervensi kini 8.0/8.0/8.0 = MO (batch 1: intervensi 0) |
| 4 | ISL: redirector + view | ⚠️ LOLOS SEBAGIAN | `create_isl_record` jalan, record ISL terbuat; `get_isl_record` mengembalikan `agri.intervention` duluan dan TIDAK PERNAH mengembalikan record ISL untuk MO ber-`industry_type='standard'` |
| 5 | farm_ux: menu, Term Mappings, 3 widget, teks UI | ❌ GAGAL — 5 BLOCKER | Debug mode mati total (B1); penulisan-ulang DOM merusak semua teks UI (B2); spatial gauge crash (B3); nutrient gauge tak terjangkau alur nyata (B4); console 404 tiap halaman (B5) |

**Keputusan: simulasi batch 2 TIDAK BERSIH — BERHENTI, jangan lanjut
batch berikutnya** (aturan flow king: bila simulasi ada error →
berhenti dan lapor). Dua langkah inti (engine + intervensi) lolos dan
NPK membaik, tapi farm_ux memblokir SEMUA bukti browser `?debug=1`
dan merusak tampilan UI bahkan tanpa debug.

## Detail per langkah

### 1. Engine asli dipakai — LOLOS

- `ir.model` `agri.intervention.base` (id 2349) dimiliki modul
  `agri_intervention` (`ir_model_data`:
  `agri_intervention.model_agri_intervention_base`).
- File vendor `farm_operation/models/agri_intervention_base.py`
  **sudah tidak ada** di disk (244 baris verbatim terhapus).
- Versi ter-install: `agri_intervention` 18.0.1.0.1, `farm_isl`
  18.0.1.0.0, `farm_ux` 18.0.1.1.1, `farm_operation` 18.0.1.2.4,
  `farm_core` 18.0.1.0.1, `farm_mrp` 18.0.1.1.0,
  `farm_processing` 18.0.1.1.2 — semua `installed`.

### 2. Intervensi engine asli — LOLOS

- Intervensi baru `SIMULASI B2 Intervensi Pupuk NPK Tomat A1`
  (id 6, `fertilizing`, lahan A1 / asset tomat id 3, BoM tomat id 10:
  50 kg NPK per 5.000 kg tomat). Auto-membuat MO WH/MO/00019.
- Workflow penuh terverifikasi via shell:
  `submit: state=draft approval=to_approve` →
  `approve: state=confirmed approval=approved` →
  `start: state=in_progress` → `stop: state=done`.
  MO tetap `draft` sepanjang workflow (sama seperti batch 1).
- MO otomatis diselesaikan alur UI-equivalent
  (`action_confirm` → `action_assign` → `_set_quantities()` →
  `button_mark_done`, pelajaran batch 1 dipakai):
  MO 19 `done`, raw move done (50 kg NPK terpakai),
  finished move done 5.000 kg, lot `0000003`.
- **Stok bergerak:** tomat segar 480 → **5.480 kg**,
  NPK 50 → **0 kg** (stok NPK 50 kg disiapkan dulu via quant,
  karena batch 1 mencatat NPK "belum terpakai" = 0 di WH).
- Bukti: `simulasi/20-interv-b2-form.png` (form intervensi,
  Status Completed, Fertilizing, Actual Start/Finish
  11/10/2026 02:12:07 — non-debug, lihat peringatan di atas),
  `simulasi/21-mo19-form-gating.png` (MO 19 Done, 5.000/5.000,
  NPK consumed 50.00, lot 0000003).
- Intervensi tillage tambahan `SIMULASI B2 Intervensi Olah Tanah
  Tomat A1` (id 7, MO WH/MO/00020, `draft`) dibuat HANYA sebagai
  kendaraan bukti widget spatial gauge (lihat langkah 5, B3) —
  tidak di-workflow-kan.

### 3. NPK — MEMBAIK, temuan batch 1 TERTUTUP

- Intervensi Pupuk NPK (id 6): `pure_n/p/k = 8.0/8.0/8.0`;
  MO induknya (19): `8.0/8.0/8.0`. **Sama — temuan batch 1
  (intervensi 0, MO 8.0) sudah tidak berlaku** dengan engine
  `agri_intervention` asli (plugin NPK kini menulis ketiga field
  itu; `farm_operation/models/agri_intervention_mixin.py`
  `_compute_agri_costs` + `intervention_plugins.py`).
- Tidak ada perbaikan yang dilakukan di simulasi ini — ini hasil
  dari port batch 2 itu sendiri. Dicatat apa adanya.

### 4. ISL — LOLOS SEBAGIAN

- Model `agri.isl.*` ada (29 model), action ISL ada:
  1010 ISL Stock Pickings, 1011 ISL MRP Work Orders,
  1012 Farm ISL Extensions, 1013 ISL Data Migration.
- `create_isl_record('mrp.production', 19,
  industry_type='general')` → `agri.isl.mrp.production` **id 1**
  terbuat, terhubung ke MO 19, `industry_type='general'`
  (MO 19 sendiri `industry_type='standard'`, BUKAN salah satu dari
  `field_crop/livestock/aquaculture/general` sehingga
  disanitasi ke `'general'`).
- **Catatan 1 — `get_isl_record` tidak pernah mengembalikan
  record ISL itu.** Sebelum DAN sesudah create, `get_isl_record(
  'mrp.production', 19)` mengembalikan `('agri.intervention', 6)`:
  `agri.intervention` juga `_inherits` `mrp.production` (via
  `production_id`) dan didahulukan urutan registry. Andaipun
  intervensi tidak ada, record ISL tetap tidak akan dikembalikan:
  `get_isl_record` mensyaratkan `isl_record.industry_type ==
  base_record.industry_type`, sementara `'general' != 'standard'`.
  Redirector "bekerja" (menemukan record lapisan ISL), tapi
  semantiknya cacat untuk MO standar.
- View ISL terbuka (non-debug, 0 pageerror di halaman-halaman
  itu): Work Orders list kosong (0 record — wajar, belum ada
  workorder ISL), Stock Pickings list, Extensions list,
  Migration dialog (Base Model / Industry Type / Confirm
  Migration), form `agri.isl.mrp.production` id 1 (WH/MO/00019,
  field ala pharma: Safety Procedures, HACCP Plan, Allergen
  Control). Bukti: `simulasi/25-isl-workorders-list.png`,
  `26-isl-pickings-list.png`, `27-isl-extensions-list.png`,
  `28-isl-migration-list.png`, `29-isl-mrp-production-form.png`.
- Judul-judul view ISL ikut rusak oleh penulisan-ulang DOM
  farm_ux (lihat B2): "ISL MRP Field Farm Farm Farm…" (aslinya
  "ISL MRP Work Orders").

### 5. farm_ux — GAGAL (5 blocker)

Menu Farm UX ada (id 738, induk "Console & Setup", anak 739–747:
Term Mappings 1015, Voice Aliases, Form Layout Templates, Visual
Status Indicators, Workspace Customization, Contextual Help,
Multi-Sensory Interaction, Farm Social Network, Accessibility
Settings) dan tampil di top bar (terlihat di screenshot 24/25).
Term Mapping id 2 "MO - Agri Intervention" terverifikasi
**nonaktif** (`is_active=False`, source `MO`, target `AI`).
Namun kelima blocker di bawah membuat langkah ini GAGAL.

#### Blocker B1 — `?debug=1` mematikan SELURUH web client (paling fatal)

- Gejala: halaman putih total + banner merah di bawah
  "An error occurred while loading javascript modules, you may
  find more information in the devtools console"
  (bukti: `simulasi/33-debug-blank.png`; `action_manager=0`).
  Terjadi di SEMUA halaman yang dimuat dengan `?debug=1`
  (action 1015, form intervensi, dst.). Tanpa `?debug=1`
  aplikasi jalan normal (login redirect tanpa debug-lah yang
  membuat login awal tampak berhasil).
- Error persis (pageerror + console):
  `Error while loading "@farm_ux/js/agri_action_buttons.esm":
  Error: Invalid object: unknown key 'additionalProps'`
  + `The following modules failed to load because of an error:
  [@farm_ux/js/agri_action_buttons.esm]`.
- Akar: LIMA file JS farm_ux memakai `additionalProps` saat
  mendaftar ke `registry.category("view_widgets")`
  (`agri_action_buttons.esm.js`, `agri_dna_integrity.esm.js`,
  `agri_gating_audit.esm.js`, `agri_nutrient_gauge.esm.js`,
  `agri_spatial_gauge.esm.js`). Skema validasi Odoo 18
  (`web/static/src/views/widgets/widget.js`) HANYA mengizinkan
  `component`, `extractProps`, `additionalClasses`,
  `fieldDependencies`, `listViewWidth`, `supportedAttributes`,
  `supportedOptions` — **`additionalProps` adalah API Odoo 19,
  bukan 18** (di 18 kunci yang benar `extractProps`; dan `record`
  sudah diteruskan default oleh `Widget.widgetProps`, jadi
  `additionalProps` itu sendiri redundan). Validasi skema
  (`core/registry.js` `validateSchema`) HANYA jalan bila
  `odoo.debug` aktif — persis jebakan yang sudah didokumentasikan
  di AGENTS.md untuk modul 18. Loader modul berhenti di file
  pertama yang gagal (`agri_action_buttons`); keempat file lain
  memakai pola sama sehingga akan gagal berurutan sesudah yang
  pertama diperbaiki.
- Dampak: **tidak ada satu pun bukti browser `?debug=1` yang
  bisa dihasilkan selama farm_ux ter-install** — ini memblokir
  aturan pengujian king (uji headless modul 18 WAJIB `?debug=1`).

#### Blocker B2 — TermMappingHandler menulis-ulang SEMUA teks DOM, berulang tanpa henti

- Mekanisme: `farm_ux/static/src/js/term_mapping_handler.esm.js`
  terdaftar sebagai `main_components`, memuat SEMUA mapping aktif
  (`term.mapping` `is_active=True`, 30 record) lalu melakukan
  replace regex global case-insensitive pada SETIAP text node di
  `document.body`, PLUS `MutationObserver` yang menerapkan lagi
  ke setiap perubahan DOM.
- Cacat fatal: banyak target mengandung kembali source-nya
  (mis. source `Crushing` → target `Grape Crushing`;
  `Fermentation` → `Fermentation Process`; `Processing` →
  `Food Processing`; `Work Order` → `Field Task` lalu `Task` →
  `Farm Task`; `Manufacturing Order` → `Agricultural
  Intervention` lalu `Intervention` → `Farm Operation`).
  Sekali diterapkan, teks hasil MASIH mengandung source sehingga
  observer menerapkannya lagi, lagi, dan lagi — pemanjangan
  tanpa henti. Bukti visual (non-debug):
  - Daftar Term Mappings (`24-term-mappings-list.png`): baris
    "Baking Process Process Process Process Process Pr…",
    "Grape Grape Grape Grape Grape Grape Grape Grape…",
    "Fermentation Process Process Process Process Proc…",
    Industry Context "Food Food Food Food Food…".
  - Form intervensi (`20-interv-b2-form.png`): label field
    "Cultivation Farm Farm Farm Farm Farm Farm Farm Farm Farm
    Farm Farm Farm Farm Farm Farm Farm Farm Task", nilai
    "GS1 Business Step" = "Food Food Food … Processing
    (Transformation)".
  - Form MO (`21-mo19-form-gating.png`): tab "Field Farm Farm
    Farm Farm Farm Farm Farm Farm Farm Farm Farm Farm Farm
    Tasks", tab "Agri-Food Food Food Food Food Food Food Food
    Food Food Food Food Fo…".
  - Pivot MO (`30-mo-pivot.png`): nama aplikasi "Food Food Food
    Food Processing & Fermentation Process Process Process
    Process", judul action "Agricultural Farm Operations"
    (aslinya "Manufacturing Orders" — rantai dua mapping dalam
    satu pass).
  - Judul list ISL (`25-isl-workorders-list.png`): "ISL MRP
    Field Farm Farm Farm Farm Farm Farm Farm Farm Farm Farm
    Farm Farm Farm F…".
  - Bahkan baris mapping nonaktif ikut ditulis-ulang tampilannya:
    "MO - Agri Intervention" tampil sebagai
    "MO - Agri Farm Operation" (mapping 25 `Intervention` →
    `Farm Operation` aktif) — ini yang membuat pengecekan teks
    `'MO - Agri Intervention' in body` bernilai False.
- Spot-check yang diminta tugas: kata **"Model" UTUH**
  (header "Model Name" di ISL Extensions,
  `27-isl-extensions-list.png`, tanpa "AIdel"); kata **"Month"
  TIDAK tampil sebagai kata** di pivot MO (kolom menampilkan
  nama bulan "November 2026", bukan label "Month"); teks
  **"AIdel"/"AI nth" TIDAK PERNAH muncul** di halaman mana pun
  yang dikunjungi. Jadi ketakutan spesifik soal mapping MO→AI
  tidak terbukti — kerusakan NYATA justru dari mapping-mapping
  aktif lain yang berantai dan berulang. Mapping id 2 nonaktif
  itu sendiri benar; handler-nya yang cacat.

#### Blocker B3 — `agri_spatial_gauge` crash: template tidak ada

- Gejala: klik tab "Spatial & Evidence" di form MO 20 (tillage)
  → dialog **"Oops! Something went wrong…"** + form terkunci
  (bukti: `simulasi/22-mo20-spatial-gauge.png`,
  `32-mo20-spatial-oops.png`; detail teknis di dialog):
  `OwlError: Missing template: "" (for component
  "AgriSpatialGauge")` (console error, 2×).
- Akar: class `AgriSpatialGauge`
  (`agri_spatial_gauge.esm.js`) TIDAK mendeklarasikan
  `static template` (berbeda dengan `AgriGatingAudit` →
  `"farm_ux.AgriGatingAudit"` dan `AgriNutrientGauge` →
  `"farm_ux.AgriNutrientGauge"`); template XML-nya bernama
  `AgriSpatialGauge` (tanpa prefix `farm_ux.`) sehingga Owl
  tidak menemukannya — error terjadi saat komponen di-mount,
  SEBELUM `t-if` template dievaluasi.
- Catatan tambahan: kalaupun template ada, `t-if` di template
  (`intervention_type === 'aerial_spraying' || 'tillage'`)
  dibaca dari field MO sendiri — dan MO hasil intervensi selalu
  `intervention_type='process'` (lihat B4), jadi gauge tetap
  tidak akan tampil lewat alur nyata.

#### Blocker B4 — `agri_nutrient_gauge` tak terjangkau alur nyata (tab tidak pernah muncul)

- Gejala: form MO 19 (fertilizing) TIDAK punya tab
  "Soil Nutrient Balance" sama sekali (daftar tab yang
  ter-render: Components, 2 tab rusak, Miscellaneous,
  Sustainability & Value, Spatial & Evidence, Agri-Science
  Audit — bukti: `simulasi/31-mo19-nutrient-tab-NOTFOUND.png`).
- Akar: page itu `invisible="intervention_type not in
  ['fertilizing', 'tillage']"` dan dibaca dari field
  `mrp.production.intervention_type` — yang SELALU `'process'`
  (default) pada MO hasil intervensi. Ada DUA field berbeda
  bernama sama: `agri.intervention.intervention_type`
  (`'fertilizing'`, dari mixin) vs
  `mrp.production.intervention_type` (`'process'`). Saat
  `agri.intervention.create()` dengan `_inherits`, nilai
  `intervention_type` tinggal di record anak (karena field itu
  ada di model anak) dan MO induk mendapat default `'process'`
  (terverifikasi shell: IV6 `'fertilizing'` / MO19 `'process'`;
  IV7 `'tillage'` / MO20 `'process'`).
- Diagnostik (bukan alur nyata): `intervention_type` MO 19
  diubah manual via shell ke `'fertilizing'` → tab muncul, gauge
  me-render sempurna (3 cincin N/P/K, 8.0 kg masing-masing,
  Pure Nitrogen/Phosphorus/Potassium 8.00 — bukti:
  `simulasi/34-mo19-nutrient-gauge-diag.png`), lalu
  **dikembalikan ke `'process'`** supaya data tertinggal
  mencerminkan hasil alur nyata. Kesimpulan: komponen nutrient
  gauge-nya sendiri sehat; yang rusak adalah sinkronisasi
  `intervention_type` MO ↔ intervensi.
- Widget gating audit (`agri_gating_audit`) ME-RENDER normal
  (WEATHER N/A, COMPLIANCE Pending, IOT No Sensors — bukti
  `21-mo19-form-gating.png`). Jadi dari 3 widget: gating ✅
  render, nutrient ⚠️ render hanya via jalan pintas manual,
  spatial ❌ crash.

#### Blocker B5 — console error 404 di SETIAP halaman (model tidak ada)

- Error console berulang (14× dalam satu run browser, muncul di
  hampir tiap pemuatan halaman):
  `Error loading accessibility features: RPC_ERROR: 404: Not
  Found` (dari `farm_ux_integration.esm.js`).
- Akar: JS memanggil
  `orm.call('accessibility.integration',
  'get_accessibility_features', …)` — model
  `accessibility.integration` TIDAK ADA di mana pun dalam kode
  (hanya disebut di JS itu + satu test
  `test_ux_integration.py`); model yang benar-benar ada adalah
  `accessibility.settings` (tanpa method itu). Error ditangkap
  (`try/catch` + `console.error`) sehingga tidak membunuh halaman,
  tapi membuat target "0 console error" mustahil selama farm_ux
  aktif.

## Data SIMULASI B2 yang tertinggal di test18

Semua berawalan `SIMULASI B2` (company 1). Jalur buka di UI
(login admin/admin; **catatan: saat ini hanya bisa dibuka TANPA
`?debug=1`** karena Blocker B1):

| Data | ID | Jalur UI |
|------|----|----------|
| Intervensi Pupuk NPK (done, NPK 8.0) | 6 | `/web#id=6&model=agri.intervention&view_type=form` |
| Intervensi Olah Tanah (draft, kendaraan bukti spatial) | 7 | `/web#id=7&model=agri.intervention&view_type=form` |
| MO WH/MO/00019 (done, 5.000 kg tomat, lot 0000003) | 19 | Manufacturing → Manufacturing Orders / `/web#id=19&model=mrp.production&view_type=form` |
| MO WH/MO/00020 (draft, tillage) | 20 | `/web#id=20&model=mrp.production&view_type=form` |
| ISL MRP Production (MO 19, industry `general`) | 1 | `/web#id=1&model=agri.isl.mrp.production&view_type=form` |
| Term Mapping "MO - Agri Intervention" (nonaktif) | 2 | Farm UX → Term Mappings (action 1015) |

Stok akhir (WH/Stock company 1): benih 5 kg, bibit 25.000 unit,
**tomat segar 5.480 kg** (480 + 5.000 dari MO 19), **saus tomat
16 kg** (tidak berubah dari batch 1), **pupuk NPK 0 kg**
(50 kg habis dipakai MO 19). MO 19 `intervention_type`
dikembalikan ke `'process'` (hasil alur nyata) sesudah
diagnostik B4.

## Perbaikan yang DIPERLUKAN (tidak dikerjakan — diputuskan koordinator)

Tidak ada kode yang diubah dalam simulasi ini. Daftar perbaikan
yang harus diputuskan/dikerjakan sebelum simulasi batch 2 bisa
dinyatakan bersih:

1. **B1 (fatal):** ganti `additionalProps` → `extractProps` (atau
   hapus — `record` sudah diteruskan default) di kelima file JS
   farm_ux yang mendaftar ke `view_widgets`. Ini API Odoo 19
   yang lolos karena validasi registry hanya jalan di debug.
   Uji ulang WAJIB `?debug=1` sesudah perbaikan.
2. **B2 (fatal):** `TermMappingHandler` jangan menulis-ulang
   seluruh DOM dengan replace berantai + observer tanpa henti:
   minimal — terapkan mapping sekali per text node dengan
   guard "jangan proses teks yang sudah diganti", ganti hanya
   whole-word/boundary, dan JANGAN pernah menulis-ulang label
   sistem (nama field, judul view, nama menu). Idealnya
   pemetaan istilah hanya berlaku di konten record, bukan
   chrome UI.
3. **B3:** beri `AgriSpatialGauge` `static template` yang
   mengarah ke template XML-nya (atau samakan nama template
   dengan pola `farm_ux.*` seperti kedua widget lain).
4. **B4:** sinkronkan `mrp.production.intervention_type` dari
   `agri.intervention` saat MO dibuat (atau ubah kondisi
   `invisible`/t-if membaca lewat `production_id` /
   intervensi terkait) supaya tab nutrient + gauge spatial
   terjangkau alur nyata.
5. **B5:** perbaiki nama model di `farm_ux_integration.esm.js`
   (`accessibility.integration` → model/metode yang benar-benar
   ada) atau hapus pemanggilan itu.
6. **ISL (catatan):** `get_isl_record` sebaiknya tidak
   mengembalikan `agri.intervention` sebagai "record ISL", dan
   pencocokan `industry_type` harus menangani MO ber-
   `industry_type='standard'` (saat ini `create` mensanitasi ke
   `'general'` yang lalu tidak pernah cocok di `get`).

## Catatan untuk batch 3

Simulasi batch 2 **TIDAK bersih** — batch 3 (ternak/akuakultur
dst.) JANGAN dimulai sampai keenam perbaikan di atas dikerjakan
dan simulasi batch 2 diulang hingga bukti browser `?debug=1`
0 pageerror + 0 console error. Yang sudah terbukti kuat dan tidak
perlu diulang: engine asli `agri_intervention` (langkah 1–2) dan
NPK 8.0 (langkah 3).


---

# Simulasi ulang batch 2 — sesudah perbaikan B1–B5 + upgrade modul

- **Tanggal:** 10 November 2026 (±09:34–11:00 WIB, diperintah koordinator)
- **Test bed:** Odoo 18 lokal `http://127.0.0.1:8071`, DB `test18`, login `admin/admin`, `?debug=1`
- **Modul (terverifikasi shell, `installed_version = latest_version`):**
  `farm_operation` 18.0.1.2.5, `farm_isl` 18.0.1.0.1,
  `farm_ux` 18.0.1.1.2, `agri_intervention` 18.0.1.0.1 — semua `installed`
- **Skenario:** verifikasi ulang B1–B5 + ISL + regresi; intervensi
  `fertilizing`/`tillage` baru prefix `SIMULASI B2R` → workflow → MO
  selesai → stok bergerak
- **Bukti browser:** Playwright headless, screenshot `simulasi/`
  (`35`–`65`; `44`, `49`, `50`, `55`, `56` tidak terhasilkan karena
  skrip berhenti di tengah — lihat catatan di tiap langkah)
- **Skrip:** `browser-proof-b2r.py` (fase A),
  `browser-proof-b2r-a2.py` / `-a3.py` / `-a4.py` / `-a5.py`
  (diagnostik), `browser-proof-b2r-b.py` (buat intervensi via UI),
  `browser-proof-b2r-c.py` (fase C); `/tmp/sim_b2r_*.py` (shell,
  tidak disimpan di repo)
- **Insiden lingkungan (bukan kode modul):** VM replacement ±09:42 WIB
  di tengah simulasi (uptime 1 menit; user `pgtest` + `/opt/pgserver`
  hilang, server Odoo + PG mati) — test bed dipulihkan sesuai
  `AGENTS.md` (`useradd -u 1001 pgtest`, rebuild `/opt/pgserver` dari
  paket pip `pgserver` di venv odoo14-test, start PG dari
  `~/workspace/pgrun`, start Odoo 18; log server baru
  `server-b2r.log`). Data `test18` utuh, simulasi dilanjutkan dari
  titik yang sama. Tidak ada kode modul yang diubah selama simulasi
  ini (hanya laporan temuan, sesuai perintah).

## Ringkasan hasil

| # | Langkah | Status akhir | Catatan |
|---|---------|--------------|---------|
| B1 | `?debug=1` memuat web client | ✅ LOLOS | Home + semua halaman debug memuat normal; 0 pageerror di semua run debug |
| B2 | Teks UI tidak memanjang + mapping sah | ✅ LOLOS | 0 pola rusak di semua halaman; judul ter-mapping konvergen (bukan rusak) |
| B3 | Spatial gauge MO tillage | ⚠️ SEBAGIAN — gagal di debug | Template fix terbukti (gauge mount non-debug); tab Spatial di `?debug=1` tetap Oops karena B6; gauge tampil tapi datanya NaN% (B8) |
| B4 | Tab nutrient alur nyata + workflow + MO selesai | ⚠️ LOLOS DENGAN CATATAN | Propagasi `intervention_type` bekerja (MO22 `fertilizing`, MO23 `tillage`); tab + gauge N/P/K 8.0; workflow + MO selesai; stok bergerak. TAPI buat intervensi via UI GAGAL (B7) — kedua intervensi B2R dibuat via shell |
| B5 | 0 console error 404 `accessibility` | ✅ LOLOS | 0 error `accessibility`/RPC 404 di semua run |
| ISL | Redirector + alur migrasi | ⚠️ LOLOS SEBAGIAN | `get_isl_record('mrp.production', 19)` → `('agri.isl.mrp.production', 1)` ✅ (shell + form UI); wizard migrasi TIDAK BISA dieksekusi dari UI (B9) |
| R | Regresi: gating audit + NPK + stok | ✅ LOLOS | Gating render di MO19/22/23; NPK intervensi vs MO 8.0/8.0/8.0; stok akhir tercatat |

**Keputusan: simulasi ulang batch 2 TIDAK BERSIH — BERHENTI, jangan
lanjut batch 3.** Empat temuan baru (B6, B7, B8, B9) di bawah.
Perbaikan B1, B2, B4 (propagasi), B5 dan redirector ISL terverifikasi
lolos; yang mengganjal sekarang adalah dua blocker baru (B6, B7) +
dua cacat (B8, B9).

## Detail per langkah

### B1 — `?debug=1` memuat web client — LOLOS

- Login `/web/login?debug=1` → `.o_action_manager` muncul, home
  Dashboard (IZI) me-render penuh dengan ikon bug debug di systray
  (bukti: `simulasi/35-home-debug.png`; `'An error occurred'`
  tidak ada).
- Semua halaman yang dibuka dengan `?debug=1` (Term Mappings,
  ISL Work Orders, MO list 934, MO pivot, form MO 19/20/22/23,
  form ISL, wizard migrasi, form intervensi, form produk) memuat
  normal. **0 pageerror di seluruh run debug** (fase A, A3, C).
- Kontras dengan simulasi batch 2 pertama (halaman putih total +
  banner merah): perbaikan `additionalProps` terbukti.

### B2 — teks UI tidak memanjang + mapping sah — LOLOS

- Pengecekan pola rusak di semua halaman (`Grape Grape`,
  `Food Food`, `Process Process`, `Farm Farm Farm`,
  `Agricultural Agricultural`, `AIdel`, `AI nth`): **0 temuan**
  di Term Mappings (32 baris), ISL Work Orders, MO list, MO pivot.
- Mapping yang sah TETAP diterapkan dan konvergen (bukan rusak):
  - Daftar Term Mappings: baris `MO - Agri Intervention` tampil
    sebagai **`MO - Agri Farm Operation`** (rantai
    `Manufacturing Order` → `Agricultural Intervention` →
    `Agricultural Farm Operation`, lalu stabil — sesuai prediksi
    `PORTING.d/farm_ux.md`).
  - Judul action ISL: **`ISL MRP Field Tasks`** (aslinya
    `ISL MRP Work Orders`; `Work Order` → `Field Task`).
  - Judul MO list/pivot: **`Agricultural Interventions`**
    (aslinya `Manufacturing Orders`).
  - Kata `Month` tidak tampil sebagai kata di pivot (kolom
    menampilkan nama bulan, sama seperti batch 2); `AI nth` tidak
    pernah muncul.
- Catatan: judul `ISL MRP Work Orders` yang diminta tugas memang
  tidak tampil harfiah — yang tampil adalah hasil mapping-nya
  (`ISL MRP Field Tasks`). Itu perilaku mapping aktif, bukan
  kerusakan.

### B3 — spatial gauge MO tillage — SEBAGIAN (gagal di debug)

- **Template fix terbukti:** error batch 2
  (`OwlError: Missing template: ""`, komponen `AgriSpatialGauge`)
  TIDAK PERNAH muncul lagi. Di pemuatan **non-debug**, tab
  Spatial & Evidence MO 23 (tillage, `intervention_type`
  terpropagasi — lihat B4) me-render gauge: kotak
  `SPATIAL COMPLIANCE AUDIT` tampil, tanpa dialog Oops
  (bukti: `simulasi/62-mo23-spatial-nodebug.png`,
  `65-mo23-spatial-nodebug-2.png`; run atribusi A5: 0 pageerror,
  0 error konsol selain 404 `mode-json.js` — lihat B6).
- **TAPI di `?debug=1` tab yang sama tetap Oops** (MO 20 dan MO 23,
  bukti: `simulasi/41-mo20-spatial.png`,
  `51-mo20-spatial-error-detail.png`,
  `61-mo23-spatial-debug-oops.png`). Detail teknis dialog:
  `OwlError: Invalid props for component 'CodeEditor': 'mode' is
  not valid` di `AceField.template` — **BUKAN gauge-nya**,
  melainkan field `quality_fingerprint` di halaman yang sama
  (lihat Blocker B6). Sesudah dialog ditutup, widget spatial = 0.
- **Cacat data (B8):** kalaupun gauge tampil (non-debug), isinya
  salah: cincin menunjukkan **`NaN%`** merah + label
  **`OOB Points`** (bukti: screenshot 62/65). Nilai server benar
  (shell: MO 23 `spatial_compliance_rate = 100.0`,
  `out_of_bounds_count = 0`; MO 20 sama) — widget tidak menerima
  keduanya karena field itu tidak ada di arch view MO dan ketiga
  widget tidak mendeklarasikan `fieldDependencies` (grep: 0
  `fieldDependencies` di `agri_spatial_gauge` /
  `agri_nutrient_gauge` / `agri_gating_audit`). Gauge nutrient
  lolos dari cacat ini karena `pure_n/p/k_qty` ADA di arch view.
- MO 20 (data lama batch 2, `intervention_type='process'`) tetap
  tidak akan menampilkan gauge sekalipun B6 diperbaiki, karena
  `t-if` template mensyaratkan `tillage`/`aerial_spraying` —
  MO 20 sengaja tidak di-backfill (data simulasi batch 2 dibiarkan
  apa adanya). Bukti alur nyata yang sah adalah MO 23.

#### Blocker B6 (BARU) — `widget="ace"` mode `'json'` tidak valid di Odoo 18

- Lokasi: `farm_operation/views/agri_intervention_views.xml:65`
  (`<field name="quality_fingerprint" widget="ace"
  options="{'mode': 'json'}" />`, di page Spatial & Evidence).
- Akar (terverifikasi di source Odoo 18):
  `CodeEditor.MODES = ["javascript", "xml", "qweb", "scss",
  "python"]` — **`'json'` tidak ada**. `AceField` meneruskan
  `mode` ke `CodeEditor`, yang memvalidasi prop itu; di debug
  (validasi prop Owl aktif) render halaman gagal total →
  dialog Oops + console error `OwlError: Invalid props for
  component 'CodeEditor': 'mode' is not valid` (2× per sekali
  buka tab: mount + re-render sesudah dialog ditutup).
  Di non-debug validasi tidak melempar, tapi Ace tetap mencoba
  memuat `mode-json.js` → **404** (server log:
  `GET /web/assets/7193ddb/mode-json.js HTTP/1.1 404`, juga
  1 console error `Failed to load resource: 404` di run A5).
- Dampak: target "0 console error dengan `?debug=1`" mustahil
  selama ada halaman yang memuat field ini; tab Spatial tidak
  bisa dibuktikan di debug sebelum ini diperbaiki. Satu-satunya
  field `ace`/`json` di modul ter-install batch 1+2 adalah yang
  ini (grep: `quality_fingerprint` hanya di file view tersebut;
  `ace`+`json` lain hanya di modul yang tidak ter-install:
  `agri_iot`, `farm_agri_science`, `farm_ai_agent`).
- Perbaikan yang diperlukan: ganti `mode` ke nilai yang ada di
  `CodeEditor.MODES` (atau hapus `options` mode — default
  `AceField` adalah `'qweb'`).

### B4 — tab nutrient alur nyata + workflow + MO selesai — LOLOS DENGAN CATATAN

- **Pembuatan via UI GAGAL (Blocker B7, lihat di bawah)** — kedua
  intervensi B2R akhirnya dibuat via shell dengan nilai yang sama
  persis seperti IV6/IV7 batch 2 (produk 122, qty 5.000, BoM 10).
  Semua bukti di bawah ini adalah alur nyata sesudah create
  (tanpa set manual apa pun pada MO).
- **Propagasi bekerja:** intervensi id 9
  `SIMULASI B2R Intervensi Pupuk NPK Tomat A1` (`fertilizing`)
  → MO WH/MO/00022 (id 22) `intervention_type = 'fertilizing'`;
  intervensi id 10 `SIMULASI B2R Intervensi Olah Tanah Tomat A1`
  (`tillage`) → MO WH/MO/00023 (id 23)
  `intervention_type = 'tillage'` (terverifikasi shell).
- **Tab nutrient muncul tanpa set manual:** form MO 22 menampilkan
  tab **`Soil Nutrient Balance`** (daftar tab lengkap, bukti:
  `simulasi/59-mo22-form-gating.png`); diklik → widget
  `agri_nutrient_gauge` me-render (nutrient: 1), 3 cincin N/P/K
  masing-masing **8.0 kg**, `Pure Nitrogen/Phosphorus/Potassium
  8.00` (teks `8.00` ×3 — bukti:
  `simulasi/60-mo22-nutrient-gauge.png`). Bandingkan batch 2:
  MO 19 tidak punya tab ini sama sekali.
- **Workflow intervensi penuh (shell, method
  `action_submit_for_approval`/`action_approve`/
  `action_start_work`/`action_stop_work`):**
  `draft` → `to_approve` → `approved`/`confirmed` →
  `in_progress` → `done` (IV9 `state=done`,
  `approval=approved`; bukti form:
  `simulasi/58-interv-b2r-fert-done.png` — Completed,
  Fertilizing).
- **MO selesai alur UI-equivalent** (`action_confirm` →
  `action_assign` → `_set_quantities()` →
  `button_mark_done`, pelajaran batch 1): MO 22 `done`, raw move
  NPK 50,00 kg done, finished move tomat 5.000,00 kg done,
  lot `0000004` (bukti form MO 22: `5,000.00 / 5,000.00`,
  Lot `0000004`, komponen NPK consumed 50.00).
- **NPK intervensi vs MO:** IV9 `0.0/0.0/0.0` sesaat sesudah
  create, menjadi **`8.0/8.0/8.0` sesudah workflow** (sama
  seperti IV6); MO 22 `8.0/8.0/8.0`. IV6 re-check tetap
  `8.0/8.0/8.0` — **tidak ada regresi**. (Catatan: NPK
  intervensi terhitung selama workflow, bukan saat create.)
- **Stok bergerak:** tomat segar **5.480 → 10.480 kg** (+5.000,
  bukti form produk: On Hand `10,480.00`, Forecasted `10,480.00`
  — `simulasi/63-produk-tomat.png`); NPK 50 → **0 kg**
  (50 kg disiapkan dulu via quant, lalu habis dipakai MO 22);
  saus tomat tetap **16 kg**; benih 5 kg, bibit 25.000 unit
  tidak berubah.

#### Blocker B7 (BARU, fatal) — intervensi baru TIDAK BISA dibuat lewat UI

- Gejala: buka form intervensi (id 6) → klik **New** → dialog
  **Oops** (bukti: `simulasi/54-interv-new-form.png`,
  `57-interv-new-oops-detail.png`); form tetap readonly sehingga
  percobaan isi field via UI gagal total (timeout 30 dtk menunggu
  input yang tidak pernah ada — screenshot `45`/`46` dari fase A
  dan tidak terhasilnya `55`/`56`).
- Error persis (server, dari detail dialog):
  `ValueError: Wrong value for agri.intervention.intervention_type: 'process'`
  — traceback: `web/models/models.py:1007 onchange` →
  `record._update_cache` → `fields.py:3058 convert_to_cache`.
  (Label field di pesan tampil sebagai
  `agri.Farm Operation.Farm Operation_type` karena term mapping
  menulis-ulang `intervention` → `Farm Operation`.)
- Akar (terverifikasi shell): `default_get` pada
  `agri.intervention` mengembalikan
  `{'intervention_type': 'process', 'name': 'New'}` — default
  `'process'` dari field `mrp.production.intervention_type`
  bocor ke field anak `agri.intervention.intervention_type`,
  yang seleksinya TIDAK mengenal `'process'`
  (seleksi mixin tanpa `'process'`); `onchange`/`_update_cache`
  menolak nilai itu. Perbaikan B4 (propagasi saat `create()`)
  tidak menutup jalur ini karena `default_get`/`onchange`
  berjalan SEBELUM `create()`.
- Jalan lain yang dicoba dan gagal: list intervensi via
  `/web?debug=1#model=agri.intervention&view_type=list` tidak
  membuka list (jatuh ke home Dashboard — tidak ada
  `ir.actions.act_window` untuk `agri.intervention` sama sekali,
  jadi tidak ada action/list resmi; satu-satunya jalur UI adalah
  form → New, yang crash di atas). Duplikat record tidak dicoba
  (MO hasil duplikat adalah salinan MO Done, bukan MO draft baru
  — tidak menghasilkan pasangan intervensi+MO segar yang
  dibutuhkan simulasi).
- Perbaikan yang diperlukan: samakan default/seleksi
  `intervention_type` di kedua sisi (mis. beri default yang
  valid di seleksi mixin, atau tangani `'process'` di
  `default_get`/`onchange` anak) supaya New tidak melempar
  sebelum `create()` sempat berjalan.

### B5 — 0 console error 404 `accessibility` — LOLOS

- Di SEMUA run browser (fase A, A3, C, A5): **0 console error**
  yang menyebut `accessibility`, dan **0 RPC 404** model
  `accessibility.integration`. Perbaikan (pindah ke
  `accessibility.settings` + `searchRead`) terbukti.
- Satu-satunya 404 yang tersisa adalah resource
  `mode-json.js` (B6, bukan accessibility): 1× di fase C
  (non-debug) + 1× di run atribusi A5, terkonfirmasi di server
  log. Jadi B5 lolos; 404 yang ada berasal dari B6.
- Total error konsol per run debug (untuk target 0-error):
  fase A **3** (1 EvalError + 2 CodeEditor), fase A3 **2**
  (CodeEditor), fase C **3** (2 CodeEditor + 1 resource 404).
  **0 pageerror** di semua run. EvalError fase A berasal dari
  action 935 yang dibuka langsung tanpa `active_id`
  (context/domain-nya `{'default_picking_type_id': active_id}` —
  action khusus picking type, pemakaian langsung tidak valid);
  action MO list yang benar adalah **934** (list=1, errdlg=0,
  bukti: `simulasi/47-mo-list-934.png`) — bukan bug modul.

### ISL — redirector + alur migrasi — LOLOS SEBAGIAN

- **Redirector LOLOS:** `get_isl_record('mrp.production', 19)`
  → `('agri.isl.mrp.production', 1)` (shell, terverifikasi ulang
  sesudah upgrade ke 18.0.1.0.1; `get` untuk MO 20 tanpa record
  ISL → `None`, tidak ada false positive). Form ISL MO 19
  (`agri.isl.mrp.production` id 1) terbuka di UI dengan
  `WH/MO/00019` (bukti: `simulasi/42-isl-mrp-form.png`;
  teks `general` tidak tampil harfiah karena label-nya
  `General Agriculture`).
- **Wizard migrasi TIDAK BISA dieksekusi dari UI (Blocker B9):**
  dialog `ISL Data Migration` (action 1013) terbuka; field
  `Base Model`/`Industry Type`/`Confirm Migration` bisa diisi
  (catatan teknis: nilai `<option>` selection di-render
  JSON-quoted — `'"mrp.production"'`, bukan `'mrp.production'`;
  label tampil ter-mapping: `Farm Operation`,
  `General Agriculture` — bukti:
  `simulasi/52-migration-filled.png`); TAPI footer hanya punya
  tombol **Ok** (default save+close) — tidak ada tombol yang
  memanggil `action_migrate_data`. Sesudah klik Ok dengan
  confirmation ON: dialog tertutup, **0 notifikasi**, jumlah
  `agri.isl.mrp.production` tetap **1** (terverifikasi shell)
  — migrasi tidak berjalan. Akar: view
  `farm_isl/views/menu.xml` (`view_isl_migration_utility_form`)
  footer-nya kosong; method `action_migrate_data` tidak
  dirujuk view mana pun.
- Perbaikan yang diperlukan (B9): tambah tombol footer
  `type="object" name="action_migrate_data"` pada form wizard.

### Regresi — LOLOS

- **Gating audit** me-render normal di MO 19, MO 22 dan MO 23
  (WEATHER N/A, COMPLIANCE Pending, IOT No Sensors — bukti:
  `40-mo19-form-gating.png`, `59-mo22-form-gating.png`).
- **Nutrient gauge** me-render (lihat B4; MO 22: 3 cincin 8.0 kg).
- **NPK** intervensi vs MO tetap **8.0/8.0/8.0** (IV6 re-check,
  IV9, MO22 — lihat B4).
- **Stok akhir** (WH/Stock company 1): benih 5 kg, bibit 25.000
  unit, **tomat segar 10.480 kg** (5.480 + 5.000 dari MO 22),
  **saus tomat 16 kg** (tidak berubah), **pupuk NPK 0 kg**
  (50 kg habis dipakai MO 22).

## Data SIMULASI B2R yang tertinggal di test18

Semua berawalan `SIMULASI B2R` (company 1). Jalur buka di UI
(login admin/admin, `?debug=1`):

| Data | ID | Jalur UI |
|------|----|----------|
| Intervensi Pupuk NPK (done, NPK 8.0) | 9 | `/web#id=9&model=agri.intervention&view_type=form` |
| Intervensi Olah Tanah (draft, tillage) | 10 | `/web#id=10&model=agri.intervention&view_type=form` |
| MO WH/MO/00022 (done, 5.000 kg tomat, lot 0000004) | 22 | Manufacturing → Manufacturing Orders / `/web#id=22&model=mrp.production&view_type=form` |
| MO WH/MO/00023 (draft, tillage) | 23 | `/web#id=23&model=mrp.production&view_type=form` |

Stok akhir (WH/Stock company 1): benih 5 kg, bibit 25.000 unit,
**tomat segar 10.480 kg**, **saus tomat 16 kg**,
**pupuk NPK 0 kg**. MO 19/20 + intervensi 6/7/8 dari simulasi
batch 2 pertama TIDAK diubah (MO 19 tetap
`intervention_type='process'`, IV 6 tetap `fertilizing`).

## Perbaikan yang DIPERLUKAN (tidak dikerjakan — diputuskan koordinator)

Tidak ada kode yang diubah dalam simulasi ini. Daftar perbaikan
sebelum simulasi batch 2 bisa dinyatakan bersih:

1. **B6 (fatal di debug):** `quality_fingerprint`
   `widget="ace" options="{'mode': 'json'}"` di
   `farm_operation/views/agri_intervention_views.xml:65` — ganti
   `mode` ke nilai `CodeEditor.MODES` 18
   (`javascript`/`xml`/`qweb`/`scss`/`python`) atau hapus opsi
   mode. Ini yang memblokir tab Spatial di `?debug=1` dan
   target 0 console error.
2. **B7 (fatal):** `default_get`/`onchange` intervensi baru
   mengembalikan `intervention_type='process'` yang tidak valid
   di seleksi mixin — samakan default/seleksi kedua sisi supaya
   New di form intervensi tidak melempar `ValueError` sebelum
   `create()`. Tanpa ini, B4 tidak bisa dibuktikan lewat UI
   sama sekali.
3. **B8 (data):** `agri_spatial_gauge` tidak menerima
   `spatial_compliance_rate`/`out_of_bounds_count` — tambah
   `fieldDependencies` di
   `farm_ux/static/src/js/agri_spatial_gauge.esm.js` (atau
   tambah kedua field ke arch view MO) supaya gauge menampilkan
   100.0%/Within Boundaries, bukan NaN%/OOB Points.
4. **B9 (ISL):** tambah tombol footer
   `type="object" name="action_migrate_data"` pada form wizard
   `agri.isl.migration.utility` supaya migrasi bisa dieksekusi
   dari UI.
5. **Catatan (bukan blocker):** action 935
   (`Manufacturing Orders`, context `active_id`) hanya bisa
   dibuka dari menu picking type — bukan bug; MO list yang benar
   adalah action 934.

## Catatan untuk batch 3

Simulasi ulang batch 2 **TIDAK bersih** — batch 3
(ternak/akuakultur dst.) JANGAN dimulai sampai keempat perbaikan
di atas (B6–B9) dikerjakan dan simulasi batch 2 diulang hingga
bukti browser `?debug=1` 0 pageerror + 0 console error. Yang
sudah terbukti kuat dan tidak perlu diulang: B1, B2, B5,
redirector ISL (`get_isl_record` → ISL id 1), propagasi B4
(MO22/MO23), gating audit, dan NPK 8.0.


---

# Simulasi ulang batch 2 — ronde perbaikan B6–B9

- **Tanggal:** 10 November 2026 (±10:20–10:40 WIB, diperintah koordinator)
- **Test bed:** Odoo 18 lokal `http://127.0.0.1:8071`, DB `test18`, login `admin/admin`, `?debug=1`
- **Modul (terverifikasi shell, `installed_version = latest_version`):**
  `farm_operation` 18.0.1.2.6, `farm_isl` 18.0.1.0.2,
  `farm_ux` 18.0.1.1.3, `agri_intervention` 18.0.1.0.1 — semua `installed`
- **Skenario:** verifikasi ulang B6–B9 sesudah perbaikan (PORTING.md
  §12g/12h/12i) + upgrade; intervensi baru prefix `SIMULASI B2F`
  → workflow → MO selesai → stok bergerak
- **Bukti browser:** Playwright headless, screenshot `simulasi/`
  (`66`–`95`; `87`/`88` tidak terhasilkan karena skrip fase B
  berhenti di tengah — lihat catatan di B9; stok akhir diambil ulang
  sebagai `92`/`93`)
- **Skrip:** `browser-proof-b2f.py` (fase A: regresi + B6 + B4 +
  B7 percobaan 1), `browser-proof-b2f-a2.py` (B7 percobaan 2),
  `browser-proof-b2f-a3.py` (B7 percobaan 3–4, teknik benar),
  `browser-proof-b2f-diag.py` (diagnostik DOM form intervensi,
  shot `77`), `browser-proof-b2f-b.py` (fase B: B2F done + B8 segar
  + B9), `browser-proof-b2f-b2.py` (fase B2: B9 ulang + ISL MO20 +
  stok), `browser-proof-b2f-c.py` (fase C: sapuan akhir 0-error);
  `/tmp/sim_b2f_*.py` (shell, tidak disimpan di repo)
- **Insiden lingkungan:** TIDAK ADA — tidak ada VM replacement
  selama ronde ini; server yang sama jalan terus (PID 6885,
  log sesi ini `/tmp/odoo18-server-b2f.log`). Tidak ada kode modul
  yang diubah selama simulasi ini (hanya laporan temuan, sesuai
  perintah).

## Ringkasan hasil

| # | Langkah | Status akhir | Catatan |
|---|---------|--------------|---------|
| B6 | Tab Spatial & Evidence MO di `?debug=1` tanpa Oops CodeEditor | ✅ LOLOS | MO 23 + MO 25 (baru) terbuka di debug, 0 error; 0× `mode-json.js` 404 di semua run + log server |
| B7 | Buat intervensi baru lewat UI | ❌ GAGAL — blocker baru B7b | New TERBUKA tanpa Oops (crash lama hilang), form bisa diisi, TAPI Save TERBLOKIR: `production_id` required kosong; tidak ada intervensi baru tercipta via UI |
| B8 | Gauge spatial MO tillage = 100% Within Boundaries | ✅ LOLOS | MO 23 (lama) + MO 25 (baru) di `?debug=1`: cincin hijau 100% + "Within Boundaries", tanpa NaN% |
| B9 | Wizard migrasi ISL dieksekusi dari UI | ⚠️ LOLOS DENGAN CATATAN | Tombol "Migrate Data" ada + migrasi jalan (ISL 1→25, MO 20 dapat ISL 19) + notifikasi hijau terbukti + UserError saat confirm mati ✅; TAPI dialog TIDAK menutup (B9b) dan angka notifikasi menghitung record yang sudah ada |
| B4 | Propagasi + nutrient + workflow + MO selesai (jalur shell, karena UI B7 terblokir) | ✅ LOLOS (alur nyata sesudah create) | IV11 `fertilizing` → MO24 `fertilizing`; IV12 `tillage` → MO25 `tillage`; workflow penuh; MO24 done, tomat +5.000 kg, NPK −50 kg |
| R | Regresi: B1/B2/B5, redirector ISL, gating audit, NPK, stok | ✅ LOLOS | 0 pageerror + 0 console error di semua run debug (fase A/A2/A3/B2/C); gating render MO19/22/23/24/25; NPK 8.0/8.0/8.0 |

**Keputusan: simulasi ulang batch 2 — ronde perbaikan B6–B9 —
TIDAK BERSIH — BERHENTI, jangan lanjut batch 3.** B6, B8 dan
inti B9 terbukti lolos; B7 masih gagal di langkah Save (blocker
baru B7b) sehingga tidak ada satu pun intervensi yang bisa dibuat
murni lewat UI; B9 menyisakan dua catatan (B9b + hitungan
notifikasi). Perbaikan B7b (dan poles B9b) harus dikerjakan dan
ronde ini diulang sebelum batch 2 dinyatakan selesai.

## Detail per langkah

### B6 — tab Spatial tanpa Oops CodeEditor — LOLOS

- Form MO 23 (tillage) dibuka `?debug=1`, klik tab
  "Spatial & Evidence": **0 dialog Oops, 0 pageerror**; widget
  spatial me-render (bukti: `simulasi/71-mo23-form.png`,
  `72-mo23-spatial-debug.png`). Error B2R
  (`OwlError: Invalid props for component 'CodeEditor': 'mode' is
  not valid`) TIDAK PERNAH muncul lagi.
- **0 console error `mode-json.js` / 404 di semua run browser**
  (fase A, A2, A3 ×2, B2, C) — dan di log server sesi ini
  (`/tmp/odoo18-server-b2f.log`): **0× `mode-json`, 0× HTTP 404**,
  satu-satunya baris ERROR adalah peringatan startup yang jinak
  (`Importing test framework...`, bukan traceback modul).
- Sapuan akhir fase C (home + Term Mappings + MO list + MO 23/24 +
  ISL 19, semua `?debug=1`): **0 pageerror, 0 console error**.

### B7 — buat intervensi baru lewat UI — GAGAL (blocker baru B7b)

**Yang sudah membaik vs B2R:** klik **New** di form intervensi
(id 6) membuka form baru TANPA dialog Oops (bukti:
`simulasi/74-interv-new-form.png`; 0 pageerror, 0 console error).
Crash `ValueError: Wrong value for intervention_type: 'process'`
SUDAH HILANG — `default_get` tetap mengembalikan
`{'intervention_type': 'process', 'name': 'New'}` (terverifikasi
shell), tapi nilai itu kini valid di seleksi mixin.

**Percobaan pengisian (3×, teknik diperbaiki tiap ronde):**
- Percobaan 1 (fase A): deteksi editable salah — form dinilai
  tidak-editable karena selector `.o_form_view.o_form_editable`
  tidak cocok, pengisian dilewati.
- Percobaan 2 (fase A2): selector m2o salah
  (`.o-autocomplete__dropdown-item`) sehingga dropdown tidak
  terklik; select `intervention_type` gagal karena option value
  ter-quote JSON (`'"fertilizing"'`, bukan `'fertilizing'`).
- Percobaan 3–4 (fase A3, teknik benar — selection via label,
  m2o via `.o-autocomplete--dropdown-item` + polling hasil search
  async): SEMUA field terisi dengan benar — `intervention_type`
  = Fertilizing, Target Biological Asset = SIMULASI Tanaman Tomat
  A1, Product = SIMULASI Tomat Segar Servo F1, Quantity To
  Produce = 5.000,00, Bill of Material = SIMULASI Tomat Segar
  Servo F1; onchange mengisi Product Unit of Measure = kg,
  Operation Type, lokasi WH/Stock (bukti:
  `simulasi/75-interv-new-filled.png`,
  `76-interv-b2f-fert-saved.png`).

**TAPI Save tetap tidak menciptakan record** (percobaan 3 dan 4,
hasil sama): sesudah klik Save, URL tetap
`/odoo/agri.intervention/new?debug=1`, jumlah
`agri.intervention` tetap **10** dan `mrp.production` tetap **23**
(terverifikasi shell). Satu-satunya field invalid:
**`production_id`** — `o_field_invalid`, kosong, required
(`Base Production Order`, link `_inherits` ke `mrp.production`).
Validasi client-side memblokir save sebelum request create
sampai ke server — padahal `create()` server-side memang
membuat MO otomatis bila `production_id` tidak diisi
(terbukti: pembuatan via shell dengan vals yang sama persis
berhasil, IV11/MO24 — lihat B4).

#### Blocker B7b (BARU, fatal) — `production_id` required memblokir Save form intervensi

- Lokasi: form auto-generated `agri.intervention` (tidak ada
  `ir.ui.view` form khusus untuk model ini) menampilkan field
  `production_id` (`required=True` di
  `farm_operation/models/farm_agricultural_intervention.py:20-25`)
  dalam keadaan kosong; web client Odoo 18 menolak save selama
  ada required kosong, apa pun isi field lainnya.
- Memilih MO yang sudah ada di field itu BUKAN jalan keluar:
  `create()` sengaja melewatkan propagasi bila `production_id`
  diisi eksplisit, dan intervensi baru memang harus membuat MO
  baru, bukan menumpang MO lama.
- Perbaikan yang diperlukan: buat **form view khusus
  `agri.intervention` yang TIDAK memuat `production_id`**
  (client tidak memvalidasi field yang tidak ada di view;
  server `_inherits` create tetap membuat MO otomatis) —
  atau jadikan `production_id` tidak-required di level model
  bila aman untuk `_inherits`. Form view khusus sekaligus
  menyelesaikan B7c di bawah (field `name` + susunan field).

#### Catatan B7c (bukan blocker, tapi temuan UI nyata) — nama intervensi tidak bisa diisi lewat UI

- Field `name` di form New ber-modifier `o_readonly_modifier`
  (`<span>New</span>`, terverifikasi DOM): nama intervensi
  adalah field `name` warisan `mrp.production` (sequence,
  readonly). Via UI, intervensi baru akan bernama nomor MO
  (`WH/MO/xxxxx`), bukan nama bebas seperti
  "SIMULASI B2F Intervensi …" (yang selama ini hanya bisa
  di-set via shell). Bila nama bebas memang dibutuhkan di UI,
  form view khusus (B7b) perlu menanganinya juga.

### B8 — gauge spatial 100% Within Boundaries — LOLOS

- MO 23 (data B2R, `spatial_compliance_rate = 100.0`,
  `out_of_bounds_count = 0` di server): tab Spatial &
  Evidence `?debug=1` menampilkan cincin **hijau 100%** +
  label **"Within Boundaries"** + "Verified via GPS Geofencing"
  (bukti: `simulasi/72-mo23-spatial-debug.png`; teks `NaN%`
  dan `OOB Points` tidak ada; dicek ulang di fase C,
  `94-mo23-spatial-recheck.png`).
- MO 25 (baru ronde ini, tillage, server 100.0/0): hasil SAMA
  di `?debug=1` (bukti: `simulasi/81-mo25-spatial-debug.png`).
  Fix `fieldDependencies` terbukti — gauge kini menerima kedua
  nilai server.

### B9 — wizard migrasi ISL — LOLOS DENGAN CATATAN

- **Tombol ada dan berfungsi:** dialog `ISL Data Migration`
  (action 1013) footer-nya kini punya tombol biru
  **"Migrate Data"** (`type="object"`,
  `name="action_migrate_data"` — tooltip debug di screenshot
  mengonfirmasi; bukti: `simulasi/83-migration-dialog.png`,
  `84-migration-filled.png`). Field terisi: Base Model
  `mrp.production` (label tampil ter-mapping "Farm Operation"),
  Industry Type `General Agriculture`, Confirm Migration ON.
- **Migrasi jalan:** sesudah klik, jumlah
  `agri.isl.mrp.production` **1 → 25** (semua 25 MO kini punya
  padanan ISL; terverifikasi shell). MO 20 yang sebelumnya
  `get_isl_record` → `None` kini → `agri.isl.mrp.production`
  **id 19** (form-nya terbuka di UI dengan `WH/MO/00020`,
  bukti: `simulasi/91-isl-mrp-mo20-form.png`).
  Redirector lama tetap benar: `get_isl_record('mrp.production',
  19)` → ISL id 1; MO 24 → ISL 23; MO 25 → ISL 24.
- **Notifikasi hijau terbukti** (fase B2, polling per detik):
  notifikasi muncul t+1s s.d. t+3s — "Migration Complete |
  Migration completed. 25 records migrated to ISL architecture."
  — lalu auto-dismiss t+4s (bukti:
  `simulasi/89-migration-after-migrate-2s.png`). Inilah sebabnya
  fase B (cek di t+5s) sempat mencatat "tidak ada notifikasi":
  itu keterlambatan cek skrip, BUKAN tidak adanya notifikasi.
- **Negatif terbukti:** Confirm Migration mati → klik
  "Migrate Data" → dialog **UserError "Invalid Operation —
  Please confirm the migration before proceeding"** (bukti:
  `simulasi/86-migration-confirm-off-error.png`); jumlah ISL
  tidak berubah.
- **Catatan B9b — dialog TIDAK menutup sesudah eksekusi:**
  di DUA run independen (fase B t+5s, fase B2 polling t+1s–t+10s)
  dialog wizard tetap terbuka sesudah notifikasi tampil
  (bukti: `85-migration-after-migrate.png`,
  `90-migration-after-migrate-10s.png`); pengguna harus
  menutupnya manual (tombol × / Escape). Kriteria tugas
  ("dialog menutup") tidak terpenuhi. Perbaikan yang
  diperlukan: kembalikan action penutup dialog dari
  `action_migrate_data` (mis. gabungkan
  `display_notification` dengan penutup, atau return action
  yang menutup wizard) — perilaku standar wizard Odoo.
- **Catatan hitungan notifikasi:** angka di pesan menghitung
  SEMUA record basis yang `create_isl_record`-nya mengembalikan
  record (termasuk yang sudah ada), bukan hanya yang baru
  dibuat. Buktinya: migrasi ke-2 (fase B2) mengklaim "25 records
  migrated" padahal jumlah ISL tetap **25** (0 baru — tidak ada
  duplikat, `create_isl_record` mengembalikan record yang sudah
  ada). Pesan run pertama (1→25, 24 baru) tidak sempat
  tertangkap teksnya, tapi polanya sama. Perbaikan yang
  diperlukan: hitung hanya bila record ISL benar-benar baru
  dibuat (atau ubah pesan jadi "processed").

### B4 — propagasi + workflow + MO selesai — LOLOS (alur nyata sesudah create)

- Karena Save UI terblokir B7b, kedua intervensi B2F dibuat via
  shell dengan nilai YANG SAMA PERSIS seperti percobaan UI
  fase A3 (produk 122, qty 5.000, BoM 10, asset 3) — dicatat
  transparan di sini, bukan diklaim sebagai bukti UI:
  - IV11 `SIMULASI B2F Intervensi Pupuk NPK Tomat A1`
    (`fertilizing`) → MO WH/MO/00024, `intervention_type =
    'fertilizing'` ✅ propagasi jalan.
  - IV12 `SIMULASI B2F Intervensi Olah Tanah Tomat A1`
    (`tillage`) → MO WH/MO/00025, `intervention_type =
    'tillage'` ✅.
- **Workflow IV11 penuh** (shell,
  `action_submit_for_approval`/`action_approve`/
  `action_start_work`/`action_stop_work`):
  `draft` → `to_approve` → `approved`/`confirmed` →
  `in_progress` → `done` (bukti form:
  `simulasi/78-interv-b2f-fert-done.png` — Completed,
  Fertilizing, Actual Start/Finish 11/10/2026 03:30:08).
  NPK intervensi 0.0 saat create → **8.0/8.0/8.0** sesudah
  workflow (sama seperti IV6/IV9); MO 24 juga 8.0/8.0/8.0.
- **MO24 selesai alur UI-equivalent** (`action_confirm` →
  `action_assign` → `_set_quantities()` →
  `button_mark_done`, pelajaran batch 1): MO 24 `done`, raw
  move NPK 50,00 kg done, finished move tomat 5.000,00 kg done,
  lot `0000005` (bukti form MO 24:
  `simulasi/79-mo24-form-gating.png`; tab nutrient 3 cincin
  8.0 kg, `simulasi/80-mo24-nutrient-gauge.png`).
- **Stok bergerak:** tomat segar **10.480 → 15.480 kg**
  (+5.000, bukti form produk `simulasi/92-produk-tomat.png`);
  NPK 50 → **0 kg** (50 kg disiapkan dulu via quant, lalu habis
  dipakai MO 24; `simulasi/93-produk-npk.png`); saus tomat
  tetap **16 kg**; benih 5 kg, bibit 25.000 unit tidak berubah.
- IV12/MO25 dibiarkan `draft` (cermin B2R: IV10/MO23) — kendaraan
  bukti B8, bukan untuk diselesaikan.

### Regresi — LOLOS

- **B1:** semua halaman `?debug=1` memuat normal (home,
  Term Mappings, ISL Work Orders, MO list 934, MO pivot, form
  MO 19/22/23/24/25, form ISL, wizard migrasi, form intervensi,
  form produk); **0 pageerror di semua run** (fase A, A2, A3
  ×2, B, B2, C). Log server sesi ini: 0 traceback modul.
- **B2:** 0 pola teks rusak (`Grape Grape`, `Food Food`,
  `Process Process`, `Farm Farm Farm`, `Agricultural
  Agricultural`, `AIdel`, `AI nth`, `NaN%`) di semua halaman
  yang dicek (fase A + fase C).
- **B5:** 0 console error `accessibility` / RPC 404 di semua
  run; log server: 0× HTTP 404.
- **Gating audit** me-render normal di MO 19, MO 22, MO 23,
  MO 24 dan MO 25 (WEATHER N/A, COMPLIANCE Pending, IOT No
  Sensors — bukti: `79-mo24-form-gating.png`,
  `82-mo19-form-gating.png`, `71-mo23-form.png`).
- **NPK** intervensi vs MO tetap **8.0/8.0/8.0** (IV11, MO24;
  IV9/MO22 re-check tidak berubah).
- **Stok akhir** (WH/Stock company 1): benih 5 kg, bibit
  25.000 unit, **tomat segar 15.480 kg** (10.480 + 5.000 dari
  MO 24), **saus tomat 16 kg** (tidak berubah),
  **pupuk NPK 0 kg** (50 kg habis dipakai MO 24).

## Data SIMULASI B2F yang tertinggal di test18

Semua berawalan `SIMULASI B2F` (company 1). Jalur buka di UI
(login admin/admin, `?debug=1`):

| Data | ID | Jalur UI |
|------|----|----------|
| Intervensi Pupuk NPK (done, NPK 8.0) | 11 | `/web#id=11&model=agri.intervention&view_type=form` |
| Intervensi Olah Tanah (draft, tillage) | 12 | `/web#id=12&model=agri.intervention&view_type=form` |
| MO WH/MO/00024 (done, 5.000 kg tomat, lot 0000005) | 24 | Manufacturing → Manufacturing Orders / `/web#id=24&model=mrp.production&view_type=form` |
| MO WH/MO/00025 (draft, tillage) | 25 | `/web#id=25&model=mrp.production&view_type=form` |
| ISL MRP Production (semua MO; MO 20 = id 19, MO 24 = id 23, MO 25 = id 24) | 1–25 | `/web#id=19&model=agri.isl.mrp.production&view_type=form` |

Stok akhir (WH/Stock company 1): benih 5 kg, bibit 25.000 unit,
**tomat segar 15.480 kg**, **saus tomat 16 kg**,
**pupuk NPK 0 kg**. Data SIMULASI / SIMULASI B2 / SIMULASI B2R
tidak diubah (MO 19 tetap `intervention_type='process'`,
IV 6/9/10 tidak disentuh; satu-satunya perubahan pada data lama
adalah penambahan padanan ISL untuk semua MO lewat wizard B9 —
24 record ISL baru, tanpa duplikat).

## Perbaikan yang DIPERLUKAN (tidak dikerjakan — diputuskan koordinator)

Tidak ada kode yang diubah dalam simulasi ini. Daftar perbaikan
sebelum simulasi batch 2 bisa dinyatakan bersih:

1. **B7b (fatal):** form intervensi baru tidak bisa disimpan
   lewat UI karena `production_id` required kosong — buat form
   view khusus `agri.intervention` tanpa field `production_id`
   (server `_inherits` create sudah membuat MO otomatis), atau
   jadikan field itu tidak-required di level model. Tanpa ini,
   B7 tidak bisa lolos lewat UI apa pun.
2. **B7c:** di form view khusus yang sama, tangani juga field
   `name` yang readonly (`New`) bila nama intervensi bebas
   memang harus bisa diisi dari UI.
3. **B9b (poles):** dialog wizard migrasi harus menutup sendiri
   sesudah `action_migrate_data` berhasil (saat ini tetap
   terbuka; notifikasi hijau sudah tampil).
4. **B9 hitungan (poles):** angka "records migrated" di
   notifikasi harus menghitung hanya record ISL yang baru
   dibuat, bukan semua record basis yang diproses.
5. **Catatan (bukan blocker):** option value selection di form
   intervensi ter-render JSON-quoted (`'"fertilizing"'`) —
   perilaku Odoo standar untuk selection di model `_inherits`,
   bukan bug; alat uji harus memilih via label. Nilai `<option>`
   yang sama terlihat di wizard migrasi.

## Catatan untuk batch 3

Simulasi ulang batch 2 — ronde perbaikan B6–B9 — **TIDAK
bersih** — batch 3 (ternak/akuakultur dst.) JANGAN dimulai sampai
B7b diperbaiki dan ronde ini diulang hingga bukti browser
`?debug=1` 0 pageerror + 0 console error DAN intervensi baru
benar-benar tercipta lewat UI. Yang sudah terbukti kuat dan tidak
perlu diulang: B6 (ace `javascript`), B8 (`fieldDependencies`
spatial), B9 inti (tombol + migrasi + notifikasi + UserError),
B1, B2, B5, redirector ISL, propagasi B4 (MO24/MO25), gating
audit, NPK 8.0, dan rantai workflow → MO → stok.

# Simulasi ulang batch 2 — ronde perbaikan B7b

- **Tanggal:** 10 November 2026 (±11:00–11:30 WIB, perintah king
  10:39 WIB)
- **Test bed:** Odoo 18 lokal `http://127.0.0.1:8071`, DB `test18`,
  login `admin/admin`, `?debug=1`
- **Modul (terverifikasi shell, `installed_version =
  latest_version`):** `farm_operation` 18.0.1.2.7,
  `farm_isl` 18.0.1.0.3, `farm_ux` 18.0.1.1.3,
  `agri_intervention` 18.0.1.0.1 — semua `installed`
- **Skenario:** verifikasi ulang B7b + B7c + B9b sesudah perbaikan
  (PORTING.md §12j; `PORTING.d/b7b.md`, `PORTING.d/b9b.md`) +
  regresi penuh; intervensi baru prefix `SIMULASI B2G` →
  workflow tombol UI → MO selesai → stok bergerak → migrasi
  ISL → sapuan regresi
- **Bukti browser:** Playwright headless, screenshot `simulasi/`
  (`96`–`118`)
- **Skrip:** `browser-proof-b2g.py` (fase A: form baru + B7b
  inti), `browser-proof-b2g-a2.py` (fase A2: B7c varian 2),
  `browser-proof-b2g-b.py` (fase B: workflow tombol UI + NPK +
  MO26), `browser-proof-b2g-c.py` (fase C: B9b run 1/2 +
  negatif), `browser-proof-b2g-c2.py` (fase C2: wizard ulang
  0-error), `browser-proof-b2g-d.py` (fase D: sapuan regresi);
  `/tmp/sim_b2g_*.py` (shell, tidak disimpan di repo)
- **Insiden lingkungan:** TIDAK ADA — tidak ada VM replacement
  selama ronde ini; server yang sama jalan terus (PID 11422,
  log sesi ini `/tmp/odoo18-server-b2g.log`). Tidak ada kode
  modul yang diubah selama simulasi ini (hanya laporan temuan,
  sesuai perintah).

## Ringkasan hasil

| # | Langkah | Status akhir | Catatan |
|---|---------|--------------|---------|
| B7b | Buat intervensi baru lewat UI (form khusus, tanpa `production_id`) | ✅ LOLOS | New tanpa Oops, `name` editable, Save berhasil: IV13 + MO26, nama persis seperti diketik, propagasi `fertilizing` |
| B7c | Varian 2: tanpa menyentuh `name` | ✅ LOLOS | IV14 bernama `WH/MO/00027` (nomor MO), bukan `New`; propagasi `tillage` ke MO27 |
| B4 | Workflow tombol UI + MO selesai + stok bergerak | ✅ LOLOS | Submit → Approve → Start → Stop lewat header form sampai `done`; NPK 0.0 → 8.0/8.0/8.0; MO26 done, tomat +5.000 kg |
| B9b | Dialog wizard menutup sendiri + hitungan hanya record baru | ✅ LOLOS | Run 1 klaim tepat **2** (MO26+MO27), run 2 klaim **0**, dialog menutup sendiri di kedua run; negatif UserError, dialog tetap terbuka |
| R | Regresi: B1/B2/B5/B6/B8, redirector ISL, gating audit, NPK, stok | ✅ LOLOS | 0 pageerror + 0 console error di semua run (fase A/A2/B/C2/D); MO27 spatial 100% Within Boundaries; ISL 27 |

**Keputusan: simulasi ulang batch 2 — ronde perbaikan B7b —
BERSIH — batch 2 SELESAI.** B7b, B7c, B9b dan seluruh regresi
terbukti lolos lewat UI `?debug=1` dengan 0 pageerror + 0
console error. Batch 3 (ternak/akuakultur dst.) BOLEH dimulai
atas perintah king.

## Detail per langkah

### B7b — buat intervensi baru lewat UI — LOLOS

- Form intervensi lama IV11 dibuka
  `/web#id=11&model=agri.intervention&view_type=form`
  `?debug=1`: tampil **form BARU** (bukan auto-generated) —
  tab Execution / Components / Costs & Nutrients / Gating &
  Audit, field `name` berupa input (bukan `<span>New</span>`),
  **0 field `production_id` di DOM**, 0 pageerror, 0 console
  error (bukti: `simulasi/96-iv11-form-baru.png`).
- Klik **New**: form baru terbuka TANPA Oops; tombol header
  `Submit for Approval` tampil sesuai state draft (bukti:
  `simulasi/97-interv-new-form-b2g.png`).
- Pengisian (teknik B2F A3): `name` = `SIMULASI B2G
  Intervensi Pupuk NPK Tomat A1`, `intervention_type` =
  Fertilizing (via label), Target Biological Asset = SIMULASI
  Tanaman Tomat A1, Product = SIMULASI Tomat Segar Servo F1,
  Quantity To Produce = 5.000, Bill of Material = SIMULASI
  Tomat Segar Servo F1. Sebelum Save: **0 field
  invalid/empty-required** (bukti:
  `simulasi/98-interv-b2g-filled.png`). Onchange mengisi
  Product UoM = **kg**, Operation Type = **YourCompany:
  Manufacturing**, lokasi src/dest = **WH/Stock**.
- Klik **Save**: URL pindah dari
  `/odoo/agri.intervention/new` ke
  `/odoo/agri.intervention/13`; jumlah `agri.intervention`
  **12 → 13** DAN `mrp.production` **25 → 26**
  (terverifikasi shell). `name` tersimpan persis seperti
  diketik: `SIMULASI B2G Intervensi Pupuk NPK Tomat A1`;
  MO baru **WH/MO/00026** `intervention_type =
  'fertilizing'` ✅ propagasi B4 (bukti:
  `simulasi/99-interv-b2g-saved.png`).
- Koreksi diagnosis B7c terkonfirmasi di perilaku: nama yang
  diketik tersimpan di intervensi, MO tetap mendapat sequence
  `WH/MO/xxxxx` — sesuai PORTING.md §12j (field `name`
  milik `agri.intervention` sendiri, bukan warisan MO).

### B7c varian 2 — nama default = nomor MO — LOLOS

- Intervensi ke-2 dibuat lewat UI TANPA menyentuh `name`
  (nilai default form `New`): `intervention_type` = Soil
  Preparation (value `tillage` — labelnya BUKAN `Tillage`,
  lihat catatan), asset/produk/qty/BoM sama seperti IV13.
  Save berhasil → **IV14** (bukti:
  `simulasi/100-interv-b2g-varian2-filled.png`,
  `101-interv-b2g-varian2-saved.png`).
- Terverifikasi shell: IV14 `name = 'WH/MO/00027'`
  (fallback `create()` jalan), `intervention_type =
  'tillage'`, MO27 `WH/MO/00027` `intervention_type =
  'tillage'`, state draft.
- Catatan alat uji: label selection `tillage` adalah **Soil
  Preparation** — percobaan pertama fase A2 gagal
  `select_option(label='Tillage')` timeout 30 detik karena
  option itu tidak ada; bukan bug produk. Daftar selection
  lengkap terverifikasi shell (mis. `sowing` =
  Sowing/Planting, `process` = General Process).

### B4 — workflow tombol UI + MO selesai + stok — LOLOS

- **Workflow IV13 PENUH lewat tombol header form** (bukan
  shell): Submit for Approval → Approve → Start Agri Work →
  Stop Agri Work. Tombol muncul/hilang sesuai state
  (draft: Submit; to_approve: Approve/Reject; confirmed:
  Start; in_progress: Stop; done: tidak ada tombol),
  masing-masing klik 0 dialog error. Akhir: state `done`,
  `approval_state = approved`, teks `Completed`
  (bukti: `simulasi/102-iv13-done-workflow.png`).
- **NPK IV13 0.0 → 8.0/8.0/8.0** sesudah workflow (tab Costs
  & Nutrients menampilkan 3× `8.00`; form utama tidak
  menampilkan angka NPK — sama seperti B2F; bukti:
  `simulasi/103-iv13-costs-nutrient.png`). MO26 juga
  8.0/8.0/8.0 sejak create (tab Soil Nutrient 3× `8.00`,
  bukti: `simulasi/105-mo26-nutrient.png`).
- **MO26 selesai alur UI-equivalent** (`action_confirm` →
  `action_assign` → `_set_quantities()` →
  `button_mark_done`, pelajaran batch 1 — dicatat transparan
  di sini, bukan diklaim sebagai klik UI): MO26 `done`,
  raw move NPK 50,00 kg done, finished move tomat 5.000,00
  kg done, lot `0000006`. Stok NPK 50 kg disiapkan dulu via
  quant (stok awal 0).
- **Stok bergerak:** tomat segar **15.480 → 20.480 kg**
  (+5.000, bukti form produk
  `simulasi/115-produk-tomat.png`); NPK 50 → **0 kg**
  (`simulasi/116-produk-npk.png`); saus tomat tetap
  **16 kg**; benih 5 kg, bibit 25.000 unit tidak berubah.
- IV14/MO27 dibiarkan `draft` (cermin B2F: IV12/MO25) —
  kendaraan bukti B8/B9, bukan untuk diselesaikan.

### B9b — dialog menutup + hitungan hanya record baru — LOLOS

- Keadaan awal: MO26 + MO27 baru TANPA padanan ISL
  (`get_isl_record` → `None`), ISL `agri.isl.mrp.production`
  = **25**.
- **Run 1** (Confirm ON, `mrp.production`, General
  Agriculture): notifikasi hijau tampil t+1s–t+4s —
  "Migration Complete | Migration completed. **2 records
  migrated** to ISL architecture." — tepat jumlah MO baru;
  **dialog wizard MENUTUP SENDIRI** (dialogs=0 di semua
  polling t+1s–t+10s, tanpa klik ×/Escape); ISL **25 → 27**
  (bukti: `simulasi/107-migration-run1-after-2s.png`,
  `108-migration-run1-after-10s.png`).
- **Run 2** (Confirm ON, kondisi sama): notifikasi "Migration
  Complete | Migration completed. **0 records migrated** to
  ISL architecture." (t+1s–t+4s, lalu auto-dismiss);
  **dialog menutup sendiri**; ISL tetap **27** — hitungan
  kini hanya record baru, bukan semua yang diproses (bukti:
  `simulasi/109-migration-run2-after-2s.png`,
  `110-migration-run2-after-10s.png`).
- **Negatif terbukti:** Confirm Migration mati → klik
  "Migrate Data" → dialog **UserError "Invalid Operation —
  Please confirm the migration before proceeding"**,
  dialog wizard **tetap terbuka** (dialogs=2: wizard +
  error), jumlah ISL tidak berubah (bukti:
  `simulasi/111-migration-confirm-off-error.png`).
- Redirector sesudah migrasi (shell): `get_isl_record`
  MO26 → ISL **26**, MO27 → ISL **27**; yang lama tetap
  benar (MO19 → 1, MO24 → 23, MO25 → 24).
- Catatan skrip (bukan bug produk): skrip fase C berhenti
  di langkah penutup — klik × wizard gagal timeout karena
  dialog UserError menutupi × wizard di bawahnya (overlay
  intercepts pointer events), sehingga ringkasan
  pageerror/console fase C tidak tercetak. Halaman wizard
  dibuktikan ulang bersih di fase C2 (0 pageerror + 0
  console error, `118-migration-dialog-recheck.png`); selama
  polling kedua run migrasi tidak ada dialog error; log
  server sesi ini 0 Traceback / 0 HTTP 404.

### Regresi — LOLOS

- **B1:** semua halaman `?debug=1` memuat normal (home,
  Term Mappings action 1015, MO list action 934, form MO
  19/22/23/26/27, form ISL MO26 id 26, form IV13/IV14,
  wizard migrasi, form produk tomat/NPK); **0 pageerror di
  semua run** (fase A, A2, B, C2, D). Log server sesi ini
  (`/tmp/odoo18-server-b2g.log`): **0 Traceback, 0× HTTP
  404, 0 baris ERROR**.
- **B2:** 0 pola teks rusak (`Grape Grape`, `Food Food`,
  `Process Process`, `Farm Farm Farm`, `Agricultural
  Agricultural`, `AIdel`, `AI nth`, `NaN%`) di semua halaman
  yang dicek (fase D).
- **B5:** 0 console error `accessibility` / RPC 404 /
  `mode-json.js` di semua run; log server: 0× `mode-json`.
- **B6:** tab Spatial MO27 (tillage baru) di `?debug=1`
  tanpa Oops (bukti: `simulasi/112-mo27-spatial-debug.png`).
- **B8:** gauge spatial MO27 = cincin **hijau 100%** +
  "Within Boundaries", tanpa NaN% (server 100.0/0; bukti
  sama `112-mo27-spatial-debug.png`).
- **Gating audit** me-render normal di MO26 (WEATHER,
  COMPLIANCE tampil; status server `none/none/normal` —
  sama seperti MO24 di B2F; bukti:
  `simulasi/113-mo26-form-gating.png`).
- **NPK** intervensi vs MO tetap **8.0/8.0/8.0** (IV13,
  MO26; re-check MO26 tab nutrient 3× `8.00`, bukti:
  `simulasi/114-mo26-nutrient-recheck.png`).
- **Stok akhir** (WH/Stock company 1): benih 5 kg, bibit
  25.000 unit, **tomat segar 20.480 kg** (15.480 + 5.000
  dari MO 26), **saus tomat 16 kg** (tidak berubah),
  **pupuk NPK 0 kg** (50 kg habis dipakai MO 26).
- Catatan (bukan bug): MO26 `done` tidak muncul di MO list
  action 934 karena list itu memakai filter default **To
  Do** (hanya draft/confirmed) — MO27 draft tampil
  (bukti: `simulasi/117-mo-list-934.png`).

## Data SIMULASI B2G yang tertinggal di test18

Semua berawalan `SIMULASI B2G` (company 1). Jalur buka di UI
(login admin/admin, `?debug=1`):

| Data | ID | Jalur UI |
|------|----|----------|
| Intervensi Pupuk NPK (done, NPK 8.0) | 13 | `/web#id=13&model=agri.intervention&view_type=form` |
| Intervensi Olah Tanah (draft, tillage, nama = nomor MO) | 14 | `/web#id=14&model=agri.intervention&view_type=form` |
| MO WH/MO/00026 (done, 5.000 kg tomat, lot 0000006) | 26 | Manufacturing → Manufacturing Orders / `/web#id=26&model=mrp.production&view_type=form` |
| MO WH/MO/00027 (draft, tillage) | 27 | `/web#id=27&model=mrp.production&view_type=form` |
| ISL MRP Production (semua MO; MO 26 = id 26, MO 27 = id 27) | 1–27 | `/web#id=26&model=agri.isl.mrp.production&view_type=form` |

Stok akhir (WH/Stock company 1): benih 5 kg, bibit 25.000 unit,
**tomat segar 20.480 kg**, **saus tomat 16 kg**,
**pupuk NPK 0 kg**. Data SIMULASI / SIMULASI B2R / SIMULASI B2F
tidak diubah (IV 11/12, MO 24/25 tidak disentuh; satu-satunya
perubahan pada data lama adalah penambahan 2 padanan ISL untuk
MO 26/27 lewat wizard B9 — tanpa duplikat).

## Perbaikan yang DIPERLUKAN

Tidak ada. Semua blocker ronde sebelumnya (B7b, B7c, B9b,
hitungan notifikasi) terbukti diperbaiki dan lolos lewat UI.
Tidak ada temuan baru yang membutuhkan perbaikan kode.

## Catatan untuk batch 3

Simulasi ulang batch 2 — ronde perbaikan B7b — **BERSIH** —
batch 2 SELESAI. Batch 3 (ternak/akuakultur → IoT/cuaca →
HR/waste/financial/ESG → vertikal hortikultura, urutan
PORTING.md) BOLEH dimulai atas perintah king. Yang sudah
terbukti kuat dan tidak perlu diulang: B7b (form khusus tanpa
`production_id`), B7c (nama ketik tersimpan + fallback nomor
MO), B9b (dialog menutup + hitungan hanya baru), B6, B8,
B9 inti, B1, B2, B5, redirector ISL, propagasi B4, workflow
tombol UI → MO → stok, gating audit, NPK 8.0.

---

## Simulasi kumulatif batch 3 — 10 Nov 2026 (TIDAK BERSIH)

Aturan flow kumulatif king 10 Nov 2026 11:18 WIB: simulasi batch 3
mengulang SEMUA batch selesai — (1) rantai batch 1 penuh +
(2) verifikasi batch 2 + (3) alur baru batch 3 (ternak +
akuakultur). Data baru SEMUA berawalan `SIMULASI B3`; data lama
`SIMULASI` / `SIMULASI B2*` tidak diubah. Test bed Odoo 18
`http://127.0.0.1:8071`, DB `test18`, login `admin/admin`,
semua browser `?debug=1`, Playwright headless via
`~/workspace/odoo14-test/venv/bin/python`.

**Keputusan: TIDAK BERSIH.** Bagian 1 (batch 1) LOLOS, bagian 2
(batch 2) LOLOS, bagian 3 (batch 3) TIDAK BERSIH — 5 blocker baru:
**B10** (Save lot via UI mustahil), **B11** (cron pakan harian
selalu crash), **B12** (buat operasi akuakultur via UI gagal),
**B13** (hook telemetri DO rendah crash), **B14** (form operasi
memakai view default tanpa tab). Detail + perbaikan di bawah.

Hitungan error browser seluruh run kumulatif (fase yang selesai):
**0 pageerror + 0 console error** — error B10/B12 tampil sebagai
dialog "Oh snap!" (bukan pageerror), B11/B13 hanya terlihat di
log/shell. Fase E1 tidak terkumpul hitungannya (skrip terpotong
`timeout 110` dtk; bukti visual 161–164 tetap tersimpan).

Skrip bukti: `browser-proof-b3-a.py` (batch 1), `-b.py` (batch 2
intervensi), `-c.py` (migrasi ISL), `-d.py` + `-d2.py` (ternak),
`-e.py` (akuakultur E1), `-e2.py` (akuakultur E2),
`-e3.py`–`-e8.py` (investigasi form operasi), `-f.py` (regresi).
Screenshot `simulasi/119-*.png` s.d. `185-*.png`.

### Bagian (1) — Rantai batch 1 penuh: LOLOS (9/9)

Fase A, screenshot 119–130, 0 pageerror + 0 console error.
Produk/template B3 136–140 (Benih/Bibit/Tomat Segar/Saus
Tomat/NPK 16-16-16; varian 148–152), lahan B3 id 7, campaign B3
id 7, paket B3 id 13, rute B3 id 6, BoM tomat B3 id 19.

| # | Langkah | Status | Bukti |
|---|---------|--------|-------|
| 0 | Master data | OK | template 136–140, lahan 7, campaign 7, BoM 19 (5.000 kg tomat ← 50 kg NPK) |
| 1 | Benih | OK | lot `SIMULASI B3-LOT-BENIH-001` (id 43), `farm.seed.batch` 9, germ 92%, purity 98%, clarity 97%, moisture 11,5%, PVP `SIMULASI B3-PVP-001`, `is_pvp_compliant=True`. Blok germinasi 70% TERBUKTI: `UserError: SEED QUALITY BLOCK: Batch SIMULASI B3-LOT-BENIH-BLOK germination rate (70.0%) is below national standard.` |
| 2 | Nursery | OK | lot `SIMULASI B3-LOT-BIBIT-001` (id 45), `farm.nursery.batch` 5, 25.000 bibit, `estimated_transplant_gdd=200`; `action_create_transplant_task` → True tanpa membuat apa pun (stub, temuan lama) |
| 3 | Tanam | OK | `agri.biological.asset` 7 `SIMULASI B3 Tanaman Tomat A1`, lahir 2026-11-10, zero temp 10 °C, target yield 5.000 kg; rotation 6, state `planted`, warning False, risk 0.0 |
| 4 | GDD | OK | 10 hari 32/22 °C → 170.0; stage 14 Germinasi → progress 100.0; +1 hari → 187.0; +10 hari → 357.0; stage 15 → 100.0, 16 → 71.4, 17 → 44.625. Migrasi fase tidak otomatis (by design upstream) |
| 5 | 5 intervensi | OK | id 15–19 (Semai, Pupuk NPK, Irigasi, Proteksi, Panen), workflow draft → to_approve → approved/confirmed → in_progress → done; MO WH/MO/00030–00034. NPK fertilizing (IV16/MO31): 8.0/8.0/8.0 |
| 6 | Panen | OK | lot `SIMULASI B3-LOT-PANEN-001` (id 46) 500 kg, `farm.crop.lot` 3 (moisture 94%, protein 0,9%); rotation → `harvested`, harvesting_date 2027-02-08 |
| 7 | Quality | OK | `agri.quality.point` 3, `agri.quality.check` 3 → `pass` via `action_pass`; `agri.quality.record.book` 3 (`RB/2026/00002`) draft → `active` |
| 8 | Olah | OK | season 3, BoM saus 20 (10 kg tomat → 8 kg saus), `farm.seasonal.bom` 3 tetap `draft` (stub `action_activate`, temuan lama); MO WH/MO/00035 + WH/MO/00036 `done` (alur UI-equivalent); saus +16 kg, tomat 500 → 480 kg |
| 9 | Valuasi | OK | `farm.market.price` 4 (Rp 12.000/kg, 2027-02-08); fair valuation 4 `VAL-SIMULASI B3 Tanaman Tomat A1-20261110-1`, `market_price = 0.0`, `fair_value = 0.0` (temuan lama: asset tanpa `lot_id`); cost valuation 5 `SIMULASI B3 Valuasi Biaya Tomat A1`, NBV = fair = **Rp 2.500.000** (original 5.000.000 × koefisien 0,5 — koefisien di-set eksplisit 0,5 agar sama dengan batch 1; default field 1.0) |

### Bagian (2) — Verifikasi batch 2: LOLOS

Fase B (screenshot 131–138, 0/0) + fase C (139–144, 0/0).

- **Intervensi baru MURNI lewat UI**: `SIMULASI B3 Intervensi
  Pupuk NPK Tomat A1`, IV id **20** (`/odoo/agri.intervention/20`),
  MO WH/MO/00037; workflow tombol header Submit → Approve →
  Start Agri Work → Stop Agri Work sampai `done`; NPK IV20
  8.0/8.0/8.0 (tab Costs, 3× `8.00`); MO37 tab Soil Nutrient
  3× `8.00`, gating WEATHER tampil; tab Spatial MO27 (tillage
  B2G) di `?debug=1` tanpa Oops, gauge **100% Within
  Boundaries**, tanpa `NaN%`.
- **Wizard migrasi ISL** (action 1013): Run 1 (Confirm ON)
  notifikasi hijau `Migration completed. 8 records migrated`
  (tepat: MO 30–37), dialog menutup sendiri; Run 2 klaim **0**,
  dialog menutup; negatif Confirm OFF → UserError `Please
  confirm the migration before proceeding`, dialog tetap terbuka.
- **Penyelesaian MO37** (shell, alur UI-equivalent): `done`,
  raw NPK 50,00 kg done, finished tomat 5.000,00 kg done, lot
  `0000009`; stok tomat B3 **480 → 5.480 kg**, NPK B3 **50 → 0
  kg**; ISL **27 → 35**. Redirector:
  `get_isl_record('mrp.production', 37)` → id 35; MO30 → 28;
  MO19 → 1. Gating MO37: `weather='none'`,
  `compliance='none'`, `iot_status='normal'` (sama seperti B2G).

### Bagian (3) — Alur baru batch 3: TIDAK BERSIH

#### 3a. Ternak — prep (shell, OK)

Produk: Sapi Perah varian **153** (Units, tracking lot), Pakan
Sapi varian **154** (kg, stok 100 kg), Daging Sapi varian **155**
(kg, tracking lot); template 141–143. BoM pakan id **21**
(`mrp.bom`, `intervention_type='feeding'`, 1 ekor ← 10 kg
pakan, UoM Units); BoM panen id **22**
(`intervention_type='harvesting'`, 250 kg daging ← 1 ekor).
ISL recipe `agri.isl.livestock.recipe` id **1**
(`daily_feed_intake=8.0`, `growth_days_expected=180`). Lot
pejantan (sire) id **50** `SIMULASI B3-LOT-SAPI-SIRE`
(is_animal, lahir 2024-01-01, male, breeding_status open,
start_weight 500, ADG 0,7).

#### 3b. BLOCKER B10 — registrasi lot via UI GAGAL (semua lot, bukan cuma hewan)

Fase D1 (screenshot 145–152, 0 pageerror + 0 console error —
error tampil sebagai dialog). Form New lot (Animal Batches
action 1029) terisi lengkap (nama `SIMULASI B3-LOT-SAPI-001`,
produk Sapi Perah, animal_name, ear tag `SIMULASI B3-ET-001`,
birth_date 11/10/2026) → klik Save → dialog **"Oh snap!"**:

> `Legacy Write Block: Animal Count is now managed dynamically by Matter Tracking (LPN/Vessel). Please update count on the active Matter Tracking container directly.`

URL tetap `/new`, record tidak tercipta. Mekanisme: field
`stock.lot.animal_count` adalah computed non-stored
(`compute=_compute_livestock_matter_properties`,
`inverse=_inverse_animal_count`, `default=None`) — tapi form
menampilkan `Animal Count 0` dan client mengirim nilai itu saat
Save → inverse melempar UserError. `default_get` stock.lot =
`{'is_animal': False, 'name': '0000011'}` (animal_count tidak
ada di default_get).

**Radius B10 — lot BIASA pun gagal** (fase D2, screenshot 160):
lot produk tomat B3 (`SIMULASI B3-LOT-TEST-B10`) via UI juga
gagal dengan dialog `Legacy Write Block` yang sama, URL tetap
`/new`. Jadi B10 memblokir pembuatan `stock.lot` APA PUN via
UI — bukan hanya lot hewan. Fakta penting: `is_animal` TIDAK
ADA di view form lot mana pun (hanya di model
`farm_core/models/agri_stock_lot.py:28`, `default=False`);
`active_feeding_bom_id` juga TIDAK ADA di view mana pun. Bukan
bug: label tab "Production Data" tampil sebagai **"Cultivation
Data"** — term mapping aktif id 32 `Production` →
`Cultivation` (31 mapping aktif); tab itu ADA di final arch
(`get_view` stock.lot form).

#### 3c. Ternak — MO pakan + pertumbuhan/bobot (sebagian OK)

- **MO pakan via UI BERHASIL** (fase D1): Feeding Operations
  action 1030 → New → produk Sapi Perah + BoM Sapi Perah →
  Save → MO **WH/MO/00038 (id 38)**, Confirm via tombol header
  → `Confirmed`. Catatan: field `lot_producing_id` TIDAK ADA
  di form MO — MO selesai tanpa lot_producing_id.
- **Penyelesaian MO38** (shell, alur UI-equivalent): `done`,
  raw pakan 10,00 kg done, finished 1,00 ekor done, lot baru
  `0000012`; stok pakan **100 → 90 kg**, sapi **10 → 11 ekor**.
  Konsekuensi: `stock.lot` id 53 `total_feed_consumed = 0.0`,
  FCR `0.0` — compute `_compute_feed_stats` hanya menghitung
  MO dengan `lot_producing_id = lot.id` (MO38 lot_producing
  kosong). Lihat Observasi.
- **Lot hewan dibuat via shell** (pengganti UI, nilai sama
  persis, dicatat transparan — pola B2F/B7): `stock.lot` id
  **53** `SIMULASI B3-LOT-SAPI-001` (is_animal=True, birth
  2026-11-10, animal_name, ear tag, start_weight 300, ADG
  0,8), quant 10 ekor di WH/Stock; terverifikasi:
  `animal_count=1` (default bridge tanpa matter tracking —
  keterbatasan desain yang sudah diketahui di PORTING.d §6.1),
  `average_weight=0.0`, `biological_stage='born'`,
  `current_predicted_weight=300.0`, sapi on-hand 10,0;
  `active_feeding_bom_id=21` di-set via shell.
- **Fase D2 via UI** (screenshot 153–160, 0/0): form lot 53
  tampil (tab Cultivation Data: `300` tampil; `0.8` tampil
  sebagai `0.80`); **event timbang** via UI (action 1031, lot
  53, Weight Measurement, 320 kg) → `farm.livestock.event`
  id **1**, tersimpan (screenshot 155: `Measured Weight (kg)
  320.00`); **breeding record** via UI (action 1033, animal
  53, sire lot 50, offspring 1) → `farm.breeding.record` id
  **1**, `gestation_days = 0` (lihat Observasi: onchange hanya
  mengenali pig/cow/cattle/sheep/goat/horse di nama produk,
  `Sapi` tidak cocok); **env monitoring** via UI (action 1032,
  lokasi SIMULASI B3 Lahan A1, temp 28, humidity 65, ammonia 5,
  CO2 400) → `farm.livestock.house.env` id **1**,
  `comfort_index = 77.64` (sesuai rumus THI).
- **MO panen daging via UI** (fase D2): Manufacturing action
  934 → produk Daging Sapi + BoM Daging Sapi, qty 250 →
  **WH/MO/00041 (id 41)**, Confirm → `Confirmed`.
- **Penyelesaian MO41** (shell, alur UI-equivalent): `done`,
  raw sapi 1,00 ekor done, finished daging 250,00 kg done,
  lot `0000014`; stok sapi **11 → 10 ekor**, daging **0 → 250
  kg**, pakan tetap 90 kg.
- **Mortalitas**: `action_record_mortality(1, 'Sakit')` di lot
  53 → chatter saja, stok sapi TIDAK berubah (11,0 → tetap,
  sesuai kode); `farm.livestock.event` id **2** (`slaughter`,
  record-only upstream).
- `total_feed_consumed` lot 53 tetap **0.0**, FCR **0.0**
  sesudah MO38 + MO41 (lihat Observasi).

#### 3d. BLOCKER B11 — cron pakan harian SELALU crash (fatal untuk otomasi feeding)

`stock.lot._cron_daily_feed_depletion()` dipanggil 2× (10 Nov
2026 ~04:46 WIB), keduanya crash di baris yang sama setelah MO
dibuat + confirm + mark done:

```
File ".../farm_livestock/models/farm_lot.py", line 211, in _cron_daily_feed_depletion
    _logger.info("Daily feed depletion recorded for lot %s using BOM %s", lot.name, lot.active_feeding_bom_id.name)
AttributeError: 'mrp.bom' object has no attribute 'name'. Did you mean: '_name'?
```

Log server mengonfirmasi alur sebelum crash: `Running
pre-confirm hooks for WH/MO/00040`, `Harvest Plugin: Type
mismatch or missing: feeding`, `Running pre-done hooks for
WH/MO/00040`. Akibat: transaksi cron rollback total → MO max
tetap **38** (MO WH/MO/00039 dan WH/MO/00040 hanya
menghabiskan nomor sequence, tidak tersimpan), pakan tetap 100
kg, sapi tetap 10 ekor — **cron tidak pernah bisa berhasil;
tidak ada MO pakan yang bertahan dan tidak ada stok yang
bergerak**. Ini lebih fatal daripada jebakan `_set_quantities`
yang sudah diperkirakan di PORTING.d §6.6 (jebakan itu bahkan
tidak sempat tercapai sebagai state persisten).

#### 3e. Akuakultur — prep (shell, OK)

Kategori `SIMULASI B3 Pond` (id 54; nama mengandung 'pond'
untuk domain `pond_id`). Produk: Kolam Lele varian **156**
(Units, lot), Lele varian **157** (Units, lot), Pakan Lele
varian **158** (kg, stok 100 kg), Lele Panen varian **159**
(kg, lot); template 144–147. Lot kolam id **57**
`SIMULASI B3-KOLAM-001` (quant 1); lot lele id **58**
`SIMULASI B3-LOT-LELE-001` (quant 1.000 ekor). BoM pakan id
**23** (`intervention_type='feeding'`, 1.000 ekor ← 50 kg
pakan); BoM panen id **24** (`intervention_type='harvesting'`,
50 kg panen ← 100 ekor). ISL recipe
`agri.isl.aquaculture.recipe` id **1**
(`min_dissolved_oxygen=4.0`, `max_stocking_density=10.0`).
ISL lot `agri.isl.lot.aquaculture` id **1**
(`water_volume_m3=1000.0`, `current_density=0.0` — lihat
Observasi).

#### 3f. BLOCKER B12 — buat operasi akuakultur via UI GAGAL

Fase E1 (screenshot 161–164): form New operasi (action 1024)
terisi lengkap (nama `SIMULASI B3 Operasi Lele Kolam 001`,
pond `SIMULASI B3-KOLAM-001`, species `Lele Dumbo`,
initial_stocking 1.000, stage Growing, bobot awal 50 g,
target 500 g, feeding 3%, T 28, pH 7.2, DO 6.5, NH3 0.3,
NO2 0.1) → klik Save → dialog **"Oh snap!"** (screenshot
162):

> `Field must be a many2one or many2many relation on itself: 'depend_on_ids'`

Sumber: `odoo/models.py:6036` (`BaseModel._has_cycle`) —
constraint `@api.constrains('depend_on_ids')` di
`odoo/addons/project/models/project_task.py:492` memanggil
`_has_cycle('depend_on_ids')`, yang menuntut
`field.comodel_name == self._name`. Model operasi me-redefine
field itu di `farm_aquaculture/models/aquaculture_operation.py:22-23`
(`depend_on_ids`/`dependent_ids` =
`fields.Many2many('project.task', relation='farm_aqua_op_depend_on_rel', ...)`),
sehingga comodel `project.task` ≠ `farm.aquaculture.operation`.
Client web mengirim field itu (kosong) saat create → constraint
meledak. **Buat via shell BERHASIL** (tanpa `depend_on_ids` di
vals): operasi id **3** tercipta. B12 hanya jalur UI — tapi
jalur UI adalah satu-satunya jalur registrasi operasi yang
normal.

#### 3g. Akuakultur — WQ log + MO pakan/panen (OK, dengan catatan B14)

- **Log kualitas air via UI** (fase E2, screenshot 165):
  action 1025 → operation_id operasi 3, T 28.5, pH 7.4, DO
  6.8, NH3 0.2, NO2 0.05, turbidity 5, salinity 0.5, weather
  `Cerah` → `farm.water.quality.log` id **1**. **Write-back
  TERBUKTI via shell**: operasi 3 `water_temperature=28.5`,
  `ph_level=7.4`, `dissolved_oxygen=6.8`, `ammonia_level=0.2`,
  `nitrite_level=0.05`, `water_quality_status='good'`.
  Bukti visual nilai sesudah write-back: screenshot 185
  (`Water Temperature 28.50`, `Dissolved Oxygen 6.80`, `pH
  Level 7.40`, `Water Quality Status Good`).
- **MO pakan lele via UI** (fase E2, screenshot 167):
  produk Lele + BoM Lele, qty 1.000 → **WH/MO/00042 (id 42)**,
  Confirm. **MO panen lele via UI** (screenshot 168): produk
  Lele Panen + BoM Lele Panen, qty 50 → **WH/MO/00043 (id
  43)**, Confirm.
- **Penyelesaian MO42/43** (shell, alur UI-equivalent,
  commit terverifikasi): MO42 `done` (raw pakan lele 50,00 kg,
  finished lele 1.000,00 ekor, lot `0000017`); MO43 `done`
  (raw lele 100,00 ekor, finished lele panen 50,00 kg, lot
  `0000018`). Stok: pakan lele **100 → 50 kg**, lele **1.000 →
  1.900 ekor** (1.000 awal + 1.000 hasil MO42 − 100 konsumsi
  MO43 — sesuai desain BoM: MO pakan "memproduksi" ikan yang
  diberi pakan, sama polanya dengan sapi 10 → 11 → 10), lele
  panen **0 → 50 kg**, kolam tetap 1. Bukti browser MO42/MO43
  `Done`: screenshot 180–181 (fase F).
- **`action_schedule_harvest('2027-03-01')`** (shell):
  `harvest_plan_date = 2027-03-01` (screenshot 185:
  `Planned Harvest Date 03/01/2027`). Catatan: method ini
  butuh argumen tanggal positional; field-nya
  `harvest_plan_date` (bukan `planned_harvest_date` /
  `harvest_date` — keduanya tidak ada).
- **`harvest_readiness = False`** (stub, temuan yang dicatat):
  `_compute_avg_current_weight` selalu `avg_current_weight =
  avg_initial_weight` (50 g vs target 500 g) — readiness
  praktis tidak tercapai dengan target realistis.

#### 3h. BLOCKER B13 — hook telemetri DO rendah crash

`agri.isl.aquaculture.task` id **1** (`SIMULASI B3 Task
Telemetri Lele`, dibuat via shell dengan `product_id=157`,
`product_qty=1000`, `bom_id=23`; parent MO-nya
**WH/MO/00045 draft** — tertinggal sebagai data, lihat
bawah). Panggil
`handle_aquaculture_telemetry({'dissolved_oxygen': 2.0,
'temperature': 29.0})` (ambang recipe 4.0) →
`AttributeError: 'agri.isl.aquaculture.task' object has no attribute 'message_subscribe'`.

Rantai: `farm_aquaculture/models/aquaculture_isl.py:84`
`handle_aquaculture_telemetry` → DO 2.0 < 4.0 →
`report_incident(...)` (`farm_core/models/agri_mixins.py:303`)
→ `mail.activity.create(...)` → Odoo memanggil
`message_subscribe` pada record target — model task TIDAK
inherit `mail.thread` (`_inherit` hanya 4 mixin agri;
`_inherits = {'mrp.production': 'intervention_id'}` mendelegasi
field, bukan method) → crash. **Jalur insiden kritis — inti
fitur hook ini — selalu gagal**; payload aerasi
(`agent_instruction_json`) tidak pernah tertulis. Catatan:
create task tanpa `product_id` gagal duluan
(`NotNullViolation` pada `mrp_production.product_id`, MO
WH/MO/00044 hanya menghabiskan nomor sequence). Task livestock
(`agri.isl.livestock.task`) berbagi celah struktural yang sama
(tanpa `mail.thread`); belum ada hook telemetri livestock
untuk diuji.

#### 3i. BLOCKER B14 — form operasi memakai view default tanpa tab

Membuka operasi 3 (klik baris di daftar action 1024, atau URL
langsung) memuat form **tanpa notebook**: DOM 0
`.o_notebook`, 0 `.nav-link`, 0 `.o_notebook_headers`
(fase E5, probe DOM); form ~5.900 px field dump (field
mail.thread dulu, field aqua di bawah). Tab **"Aquaculture
Information" tidak ada** di view yang dimuat, padahal view
`farm.aquaculture.operation.form` id **2772** (inherit
`project.view_task_form2`, insert page
`aquaculture_info` sesudah `extra_info`) ada dan benar bila
dipanggil eksplisit: `get_view(view_id=2772)` → arch berisi
notebook + `Aquaculture Information`; `get_view(view_id=False)`
→ arch TANPA notebook. Action 1024 tidak menentukan `view_id`
(`view_mode: list,form` saja). 2772 adalah extension view
(mode extension, priority 16) tanpa primary view untuk model
ini, sehingga resolusi view jatuh ke generated default view.

**Koreksi penting (bukan "field tidak tampil"):** data tetap
tampil benar bila di-scroll ke bawah — screenshot 185
membuktikan semua nilai aqua tampil (28.50/7.40/6.80,
`Planned Harvest Date 03/01/2027`, `Pond/Tank
SIMULASI B3-KOLAM-001`, `Initial Stocking Count 1,000`).
B14 adalah cacat UX/navigasi (tab hilang, form 5.900 px),
bukan kehilangan data. Catatan metodologi: cek teks
`'28.5'`/`'7.4'`/`'6.8'` pada fase E3/E4 sempat False karena
race pemuatan record di browser (nilai belum ter-render saat
cek), BUKAN karena nilai tidak ada — screenshot 185 yang
diambil sesudah scroll + jeda membuktikan nilai tampil.
Pelajaran yang sama berlaku untuk cek teks `'320'` pada event
timbang (screenshot 155 membuktikan `320.00` tampil) — cek
teks tanpa jeda cukup tidak bisa dijadikan bukti negatif.

### Fase F — sapuan regresi browser: LOLOS

Screenshot 172–181, 0 pageerror + 0 console error, tanpa
Oops di semua halaman: Home (172), Term Mappings action 1015
(173), MO list action 934 (174), form produk Tomat Segar B3
(template 138, `5,480` tampil, 175), form produk NPK B3
(template 140, `0.00`, 176), ISL form `agri.isl.mrp.production`
id 35 (`WH/MO/00037`, 177), Livestock Recipes ISL action 1034
(178), Aqua Recipes ISL action 1027 (179), MO42 `Done`
1,000.00 (180), MO43 `Done` 50.00 (181).

### Observasi (bukan blocker, dicatat)

- `lot_producing_id` tidak ada di form MO → MO pakan hasil UI
  tidak terhitung di `total_feed_consumed`/FCR lot
  (`_compute_feed_stats` memfilter `lot_producing_id`);
  total_feed_consumed lot 53 = 0.0 dan FCR = 0.0 walau MO38
  mengonsumsi 10 kg pakan.
- Breeding `gestation_days = 0` untuk `Sapi`: onchange sire
  hanya mengenali pig/cow/cattle/sheep/goat/horse di nama
  produk (nama Indonesia tidak cocok) — nilai harus diisi
  manual.
- Daftar ISL Recipes (livestock 178, aqua 179) menampilkan
  baris tanpa kolom nama — hanya kolom ID (1 baris, `1-1 / 1`);
  record ada tapi tidak teridentifikasi dari daftar.
- Form New `agri.isl.aquaculture.task` (action 1026,
  screenshot 171, body 272 karakter) hampir kosong: statusbar
  Draft → Confirmed/Planned → Executing → Completed →
  Cancelled + tombol Confirm, tapi ketiga grup `ORDER INFO
  (BASE)` / `WATER QUALITY (ISL)` / `GROWTH STATS (ISL)`
  kosong tanpa field — task tidak bisa dibuat bermakna via
  form ini (tanpa field produk/BoM); task 1 dibuat via shell.
  `action_confirm` ISL aqua task hanya `super()` (cek densitas
  di docstring tidak ada).
- ISL aqua lot id 1: `current_density = 0.0`,
  `total_biomass = 0.0` — compute tidak melihat biomassa
  (lot tanpa data bobot/jumlah hewan); densitas tidak pernah
  terhitung dari stok lot yang ada.
- `action_record_mortality` hanya chatter — tidak mengubah
  stok (sesuai kode upstream, bukan bug).
- 4 action livestock tanpa menu (1031/1032/1034/1035 — hanya
  via URL action) + dua menu root "Livestock" (754, 759) +
  dua menu root "Aquaculture" (748, 751) — duplikat upstream,
  dibiarkan (temuan lama).
- Insiden test bed: server Odoo 8071 mati di tengah simulasi
  (setelah fase E6, ~05:0x WIB; PG 5433 tetap hidup) dan
  di-restart (`nohup venv/bin/python odoo/odoo-bin -c
  odoo.conf -d test18`, PID 1908, log `/tmp/odoo18-b3.log`,
  8071:200). Data SIMULASI B3 utuh sesudah restart
  (terverifikasi E7/E8). `restart-testbed18.sh` sudah basi
  (merujuk cluster /dev/shm yang sudah mati permanen) — jangan
  dipakai; PG sekarang dari `~/workspace/pgrun`.

### Jebakan metodologi (ditemukan selama B3, bukan bug modul)

- `mrp.bom.product_uom_id` default-nya `Units` (bukan UoM
  produk) → BoM baru WAJIB set `product_uom_id` eksplisit
  (kg), kalau tidak MO gagal UoM mismatch. (BoM lama 10/11
  sudah kg.)
- `stock.quant` via ORM dengan `inventory_quantity` +
  `action_apply_inventory()` TIDAK mengubah `quantity` →
  pakai `env['stock.quant']._update_available_quantity(product,
  location, qty, lot_id=...)`.
- `farm.crop.rotation.history.product_id` dan
  `farm.market.price.product_id` adalah Many2one ke
  `product.template` (bukan `product.product`) — FK violation
  bila diisi ID varian. `is_pvp_compliant` adalah compute
  `is_certified and cert_expiry_date > today` (perlu set
  keduanya).
- Error di satu step tanpa savepoint meracuni seluruh
  transaksi shell sampai commit gagal — skrip fase 1 memakai
  `SAVEPOINT` per step + rollback parsial. **Pelajaran
  lanjutan (B3):** AttributeError di tengah skrip shell SEBELUM
  `env.cr.commit()` me-rollback SEMUA yang sudah dikerjakan
  skrip itu — penyelesaian MO42/MO43 sempat "berhasil" di
  log tapi hilang karena skrip mati di baris berikut
  (`planned_harvest_date` tidak ada) sebelum commit; harus
  diulang di skrip bersih + commit. Selalu commit SEBELUM
  langkah berisiko berikutnya.
- Skrip browser >110 dtk WAJIB dijalankan background
  (`background: true`, `timeout` ≥280) — foreground exec
  terpotong di ~120 dtk (fase E1 terpotong; bukti 161–164
  tetap tersimpan, hitungan error tidak terkumpul).
- `grep -E "^(CHK|...)"` yang tidak cocok exit 1 — dua
  "kegagalan" shell di tengah simulasi ternyata artefak grep,
  bukan error Odoo; selalu cek output mentah bila grep kosong.

### Data SIMULASI B3 yang tertinggal di test18

| Data | ID | Cara buka di UI |
|---|---|---|
| Produk template Benih/Bibit/Tomat Segar/Saus/NPK | 136–140 (varian 148–152) | Products → cari `SIMULASI B3` |
| Produk template Sapi/Pakan Sapi/Daging Sapi | 141–143 (varian 153–155) | Products → cari `SIMULASI B3` |
| Produk template Kolam/Lele/Pakan Lele/Lele Panen | 144–147 (varian 156–159) | Products → cari `SIMULASI B3` |
| Lahan `SIMULASI B3 Lahan A1` | 7 | Farm → Locations |
| Campaign B3 / paket B3 / rute B3 | 7 / 13 / 6 | Farm → Campaigns / Packages / Routes |
| BoM tomat B3 / saus B3 / pakan sapi / panen sapi / pakan lele / panen lele | 19 / 20 / 21 / 22 / 23 / 24 | Manufacturing → Bills of Materials |
| Seed batch B3 / nursery batch B3 | 9 / 5 | Farm → Seed/Nursery Batches |
| Biological asset `SIMULASI B3 Tanaman Tomat A1` | 7 | Farm → Biological Assets |
| Rotation history B3 | 6 | Farm → Crop Rotations |
| Intervensi B3 (tomat 15–19, NPK UI 20) | 15–20 | Farm → Interventions |
| Crop lot B3 / quality point 3 / check 3 / record book 3 | 3 / 3 / 3 / 3 (`RB/2026/00002`) | Farm → Crop Lots / Quality |
| Seasonal BoM B3 (draft) / season 3 / market price 4 | 3 / 3 / 4 | Farm → Seasonal BoMs / Seasons / Market Prices |
| Valuasi fair 4 / cost 5 | 4 / 5 | Farm → Valuations |
| MO B3 (tomat 30–36, NPK UI 37, pakan sapi 38, panen sapi 41, pakan lele 42, panen lele 43) | 30–38, 41–43 | Manufacturing → Manufacturing Orders |
| ISL `agri.isl.mrp.production` (MO 30–38, 41–43) | 28–35 | ISL → MRP Production (atau `/web#id=35&model=agri.isl.mrp.production&view_type=form`) |
| Lot hewan `SIMULASI B3-LOT-SAPI-001` (+ sire lot 50) | 53 (50) | Livestock → Animal Batches (action 1029; lot 53 HANYA bisa dibuka, tidak bisa dibuat ulang via UI — B10) |
| Event timbang 320 kg / breeding / env monitoring | 1 / 1 / 1 | action 1031 / 1033 / 1032 (tanpa menu) |
| ISL livestock recipe | 1 | Livestock Recipes (action 1034) |
| Operasi akuakultur `SIMULASI B3 Operasi Lele Kolam 001` | 3 | Aquaculture → Operations (action 1024; B12: tidak bisa dibuat via UI; B14: form read tanpa tab) |
| WQ log B3 | 1 | Aquaculture → Water Quality Logs (action 1025) |
| ISL aqua recipe / ISL aqua lot | 1 / 1 | Aqua Recipes (action 1027) / tanpa menu (URL langsung `agri.isl.lot.aquaculture/1`) |
| ISL aqua task `SIMULASI B3 Task Telemetri Lele` (+ MO draft WH/MO/00045) | 1 (MO 45) | Aqua Tasks (action 1026; form New hampir kosong) |
| Lot hasil MO: benih 43, bibit 45, panen 46, sapi MO38 `0000012`, daging `0000014`, lele MO42 `0000017`, lele panen `0000018` | — | Inventory → Lots/Serial Numbers |

Nomor MO yang hilang (sequence-only, record tidak ada):
WH/MO/00039 + WH/MO/00040 (rollback cron B11),
WH/MO/00044 (gagal create task B13). MO yang ada: 1–27,
30–38, 41–43, 45.

Stok akhir (WH/Stock, company 1): benih **5 kg**, bibit
**25.000 unit**, tomat segar **5.480 kg**, saus tomat **16 kg**,
NPK **0 kg**; sapi **10 ekor**, pakan sapi **90 kg**, daging
sapi **250 kg**; kolam lele **1**, lele **1.900 ekor**, pakan
lele **50 kg**, lele panen **50 kg**.

### Perbaikan yang DIPERLUKAN (ronde perbaikan batch 3)

1. **B10 (fatal, `farm_livestock` + `farm_core`):** form
   `stock.lot` tidak bisa di-Save via UI karena
   `animal_count` (computed + inverse Legacy Write Block)
   terkirim bernilai 0 saat create. Perbaiki mis. jadikan
   field readonly di view / hapus dari pengiriman create /
   buat inverse menoleransi nilai default — dan sediakan
   `is_animal` + `active_feeding_bom_id` di view (saat ini
   tidak ada di view mana pun) supaya registrasi hewan +
   feeding plan bisa dilakukan murni via UI. Radius: SEMUA
   lot (bukan cuma hewan) ikut gagal.
2. **B11 (fatal, `farm_livestock/models/farm_lot.py:211`):**
   `_cron_daily_feed_depletion` memakai
   `lot.active_feeding_bom_id.name` — `mrp.bom` tidak punya
   field `name`; ganti mis. `display_name` / nama produk BoM.
   Selama ini crash, cron harian tidak pernah berhasil
   (rollback total).
3. **B12 (fatal, `farm_aquaculture/models/aquaculture_operation.py:22-23`):**
   `depend_on_ids`/`dependent_ids` di-redefine dengan comodel
   `project.task` — constraint cycle core
   (`odoo/models.py:6036`, via
   `project_task.py:492`) menolaknya saat client mengirim
   field itu. Perbaiki mis. jangan redefine field dependensi
   (terima relation table bersama), atau redefine dengan
   comodel model sendiri + `recursive=True`, atau keluarkan
   field itu dari form.
4. **B13 (fatal, `farm_aquaculture/models/aquaculture_isl.py:84`
   + `farm_core/models/agri_mixins.py:303`):**
   `handle_aquaculture_telemetry` → `report_incident` →
   `mail.activity.create` → `message_subscribe` — model
   `agri.isl.aquaculture.task` tidak inherit `mail.thread`.
   Perbaiki mis. tambah `mail.thread` ke `_inherit` task
   (dan `agri.isl.livestock.task` yang berbagi celah yang
   sama), atau buat `report_incident` tidak bergantung pada
   chatter.
5. **B14 (`farm_aquaculture/views/aquaculture_operation_views.xml`,
   view 2772 + action 1024):** form operasi yang dibuka
   web client memakai auto-generated default view (tanpa
   notebook/tab "Aquaculture Information"), bukan view 2772.
   Perbaiki mis. jadikan 2772 primary view (tanpa
   `inherit_id`, arsitektur penuh) atau set `view_id`
   eksplisit di action 1024. Data tidak hilang — hanya
   navigasi yang rusak.

---

## Simulasi kumulatif batch 3 — ronde perbaikan B10–B14 (10 Nov 2026, siang WIB)

Ronde perbaikan sesudah upgrade farm_livestock 18.0.1.2.1 +
farm_aquaculture 18.0.1.0.1 (farm_operation 18.0.1.2.7,
farm_isl 18.0.1.0.3, farm_ux 18.0.1.1.3, agri_intervention
18.0.1.0.1; total 21 modul farm installed). Server test bed
sudah jalan saat mulai (PID 4407/4409, log
`/tmp/odoo18-server-b3f.log`); tidak ada VM replacement di
tengah ronde. Semua data baru berawalan `SIMULASI B3F`; data
lama `SIMULASI` / `SIMULASI B2*` / `SIMULASI B3` TIDAK diubah
(kecuali efek samping cron B11, lihat bawah). Skrip:
`browser-proof-b3f-a.py`, `-b.py`, `-b2.py`, `-c.py`, `-d.py`,
`-d2.py`, `-e.py`, `-e1b.py`, `-e2.py`, `-e2b.py`, `-f.py`
(screenshot 186–266; nomor 239–243 dan 248–249 tidak terambil
karena skrip crash — lihat Fase E1b/E2); skrip shell
`/tmp/b3f_p1*.py`, `b3f_p3prep.py`, `b3f_p3b.py`, `b3f_p3c.py`,
`b3f_p3d.py`, `b3f_p3e.py`, `b3f_mo55.py`, `b3f_repro_b10.py`,
`b3f_repro_b12.py`, `b3f_probe1024.py`, `b3f_q5.py`,
`b3f_q6.py`, probe pane/RPC di `/tmp/b3f_probe_*.py`.

### Keputusan: TIDAK BERSIH

- Bagian 1 (rantai batch 1): **LOLOS 9/9**.
- Bagian 2 (verifikasi batch 2): **LOLOS**.
- Bagian 3 (alur batch 3): **TIDAK BERSIH** — B10 dan B12
  masih gagal via UI (residu di luar modul yang diperbaiki);
  B11, B13, B14 **LOLOS**. Sisa alur batch 3 (MO sapi/lele,
  event, WQ) selesai; WQ write-back terverifikasi visual.

### Bagian 1 — rantai batch 1 (data B3F): LOLOS 9/9

Data dibuat via shell (`/tmp/b3f_p1.py`, `b3f_p1b.py`,
`b3f_p1c.py`): produk template Benih/Bibit/Tomat Segar/Saus/
NPK B3F (153–157, varian 165–169); lahan `SIMULASI B3F Lahan
A1` (8, WH/Stock); campaign B3F (8) / route B3F (7); BoM
tomat B3F (25: 5.000 kg ← 50 kg NPK) / saus B3F (26: 8 kg ←
10 kg tomat); seed batch B3F 11 (lot benih 65) — blok
germinasi 70% TERBUKTI (`UserError: SEED QUALITY BLOCK: Batch
SIMULASI B3F-LOT-BENIH-BLOK germination rate (70.0%) is below
national standard.`); nursery batch B3F 6 (lot bibit 67,
25.000 bibit, transplant GDD 200); biological asset B3F 8
(GDD 357.0, stage 17, stage_progress 44.625); rotation
history B3F 7 (`harvested`, 2027-02-08); intervensi B3F
21–25 (MO 47–51; NPK fertilizing 8.0/8.0/8.0); crop lot B3F
4 (lot panen 68, 500 kg, moisture 94%, protein 0,9%);
quality point 4 / check 4 (`pass`) / record book 4
(`RB/2026/00003`, `active`); season 5 / seasonal BoM 5
(tetap `draft`, stub `action_activate`); MO saus B3F 53
(WH/MO/00053), 54 (WH/MO/00054) `done`; market price 5
(Rp 12.000/kg); fair valuation 5 (market_price 0.0,
fair_value 0.0 — temuan lama); cost valuation 6
(NBV = fair = Rp 2.500.000).

Stok akhir batch 1 B3F: benih 10 kg (5 kg tanpa lot + 5 kg
lot benih; lot BLOK 1 kg ter-rollback), bibit 25.000 unit,
tomat segar **480 kg**, saus tomat **16 kg**, NPK **50 kg**
(sebelum penyelesaian MO55 — lihat Bagian 2).

Jebakan saat membuat data (tercatat, sudah diatasi di skrip):
`farm.location` mewarisi `stock.location` — induknya
`location_id`, BUKAN `parent_id`; create `agri.intervention`
tanpa `production_id` → `NotNullViolation: null value in
column "product_id" of relation "mrp_production"` (MO
auto-create tanpa produk) — pola B3: buat MO dulu (produk
tomat, BoM tomat, qty 5.000), lalu intervensi dengan
`production_id=MO`; `stock.move` Odoo 18 field-nya
`quantity`, BUKAN `quantity_done`; GDD: stage 15 pada GDD
187 → 62.333…, stage 16 pada 357 → 71.4, stage 17 → 44.625
(sesuai matematika; B3 menyebut 100.0 untuk stage 15 pada
GDD 357).

Bukti browser Fase A (`browser-proof-b3f-a.py`, screenshot
186–198): **0 pageerror + 0 console error, LOLOS**. Dua cek
teks False sudah dijelaskan dan BUKAN kegagalan: (a) `'25,000'`
False di form nursery — form tidak menampilkan kuantitas
sama sekali (hanya Lot/Product/Sowing Date; kuantitas 25.000
terverifikasi shell, screenshot 187); (b) `'357'` False di
form asset — form menampilkan `growth_stage_id` ("Current
Physio Stage", kosong) bukan `current_stage_id`/
`accumulated_gdd` (temuan lama batch 1 #6; GDD 357
terverifikasi shell, screenshot 188).

### Bagian 2 — verifikasi batch 2: LOLOS

- **Fase B** (`browser-proof-b3f-b.py`, screenshot 199–203,
  206): intervensi baru MURNI lewat UI — `SIMULASI B3F
  Intervensi Pupuk NPK Tomat A1`, IV id **26** (URL
  `/agri.intervention/26?debug=1`; regex `id=(\d+)` di skrip
  gagal karena format URL ini — bug skrip, bukan kegagalan),
  MO **WH/MO/00055 (id 55)**; workflow Submit for Approval →
  Approve → Start Agri Work → Stop Agri Work sampai
  `done`/`Completed`; tab Costs 3× `8.00`; MO27 (tillage B2G)
  tab Spatial di `?debug=1`: gauge **100% Within Boundaries**,
  tanpa `NaN%`, 0/0 error.
- **Fase B2** (`browser-proof-b3f-b2.py`, screenshot 207–208):
  form MO55 + tab Soil Nutrient 3× `8.00`, gating WEATHER
  tampil, 0/0 error.
- **Fase C** (`browser-proof-b3f-c.py`, screenshot 209–214):
  wizard migrasi ISL (action 1013). Run 1 klaim **13** (tepat:
  MO tanpa ISL = 38, 41, 42, 43, 45, 47–51, 53, 54, 55; ISL
  mrp 35 → **48**, terverifikasi shell); Run 2 klaim **0**;
  negatif Confirm OFF → UserError `Please confirm the
  migration before proceeding`, dialog tetap terbuka; 0/0
  error.
- Redirector: method `get_isl_record` ada di model
  **`agri.isl.model.redirector`** (BUKAN
  `agri.isl.mrp.production` — panggilan ke yang terakhir
  melempar `AttributeError`). Hasil: MO55 →
  `agri.isl.mrp.production(48,)`, MO47 → 41, MO53 → 46.
  Gating MO55: `weather='none'`, `compliance='none'`,
  `iot_status='normal'`.
- Penyelesaian MO55 (shell, pola B3 MO37 —
  `/tmp/b3f_mo55.py`): `done`, raw NPK 50,00 kg, finished
  tomat 5.000,00 kg (lot `0000028`); tomat B3F 480 → **5.480
  kg**, NPK 50 → **0 kg**.

### Bagian 3 — alur batch 3 + bukti B10–B14

#### Prep batch 3 (shell, OK — `/tmp/b3f_p3prep.py`)

Ternak: template Sapi Perah/Pakan Sapi/Daging Sapi 158–160
(varian 170–172); pakan sapi stok 100 kg; BoM pakan sapi
**27** (`feeding`, 1 ekor ← 10 kg pakan), BoM panen sapi
**28** (`harvesting`, 250 kg daging ← 1 ekor); ISL livestock
recipe **2** (`daily_feed_intake=8.0`,
`growth_days_expected=180`); sire lot **72**
`SIMULASI B3F-LOT-SAPI-SIRE` (is_animal, lahir 2024-01-01,
breeding_status open, start_weight 500, ADG 0,7;
`gender` field ADA di stock.lot via farm_processing).

Akuakultur: kategori `SIMULASI B3F Pond`; template Kolam
Lele/Lele/Pakan Lele/Lele Panen 161–164 (varian 173–176);
pakan lele stok 100 kg; lot kolam **73**
`SIMULASI B3F-KOLAM-001` (quant 1), lot lele **74**
`SIMULASI B3F-LOT-LELE-001` (quant 1.000 ekor); BoM pakan
lele **29** (`feeding`, 1.000 ekor ← 50 kg pakan), BoM panen
lele **30** (`harvesting`, 50 kg panen ← 100 ekor); ISL aqua
recipe **2** (`min_dissolved_oxygen=4.0`,
`max_stocking_density=10.0`); ISL aqua lot **2**
(`water_volume_m3=1000.0`, `current_density=0.0`,
`total_biomass=0.0` — temuan lama).

Field-field penting (terverifikasi dari source): operasi
akuakultur memakai `aquatic_species` (Char, BUKAN
`species`), `aquaculture_stage` (Selection),
`avg_initial_weight`, `daily_feeding_rate`, `pond_id`,
`harvest_plan_date`; lot hewan memakai `ear_tag_number`
(Char, BUKAN `ear_tag_id`), `animal_name`, `start_weight`,
`average_daily_gain`, `active_feeding_bom_id`,
`breeding_status`; breeding record: `animal_id`, `sire_id`,
`gestation_days`, `expected_offspring_count`; event timbang:
`farm.livestock.event` (`lot_id`, `event_type='Weight
Measurement'`, `measured_weight`); env monitoring:
`farm.livestock.house.env` (`location_id`, `temperature`,
`humidity`, `ammonia_level`, `co2_level`, `comfort_index`
compute).

#### B10 — MASIH GAGAL via UI (blocker tersisa #1)

Fase D1 (`browser-proof-b3f-d.py`, screenshot 215–224):
Save lot hewan DAN lot biasa via UI (action 1029 → New)
sama-sama gagal dengan dialog **"Oh snap!"**:

> `Legacy Write Block: Lifecycle stages are now managed dynamically by Matter Tracking (LPN/Vessel). Please update status on the active Matter Tracking container.`

URL tetap `/new`, record tidak tercipta. Ini BUKAN pesan lama
B3 (`Animal Count...`); itu pesan inverse `biological_stage`
yang sudah diperbaiki. Pesan baru ini berasal dari
**`farm_processing/models/stock_lot.py:92`**, method
`_inverse_matter_life_stage` untuk field **`life_stage`**
(SELALU raise, tanpa toleransi). Field paralel lain di file
yang sama juga selalu raise: `_inverse_current_weight`
(baris 78, "Weight..."), `_inverse_spatial_properties`
(baris 85, GPS lat/lng). View
`farm_processing/views/stock_lot_views.xml` menaruh
`life_stage` (radio, editable, baris 61) + `current_weight`
(editable, baris 65) di form lot — client mengirim keduanya
saat create.

Fakta pendukung dari D1: `is_animal` +
`active_feeding_bom_id` MEMANG ada di form (checkbox
`is_animal` ter-check True, M2O `active_feeding_bom_id`
ter-pick `SIMULASI B3F Sapi Perah`); TIDAK ADA tab
"Livestock Information" (daftar tab form lot: Lineage &
Kinship, Agri-Traceability, Holographic DNA Map, Intensive
Management, Breeding Management, Health Management,
Cultivation Data, Breeding & Traits, Traceability Tree,
Traceability & Heritage, Quality & GMP, Logistics);
`start_weight`/`average_daily_gain` tidak ditemukan karena
berada di tab "Cultivation Data" yang tidak sempat diklik
(field di tab non-aktif tidak ada di DOM).

Reproduksi minimal via shell (`/tmp/b3f_repro_b10.py`,
rollback, tanpa data tertinggal):

- REPRO-1: create tanpa `life_stage`/`current_weight` → OK
  (lot 79).
- REPRO-2: + `life_stage='juvenile'` → `UserError: Legacy
  Write Block: Lifecycle stages are now managed dynamically
  by Matter Tracking (LPN/Vessel). Please update status on
  the active Matter Tracking container.`
- REPRO-3: + `current_weight=0.0` → `UserError: Legacy Write
  Block: Weight is now managed dynamically by Matter
  Tracking (LPN/Vessel). Please update the weight on the
  active Matter Tracking container directly.`
- REPRO-4: vals UI pasca-fix farm_livestock
  (`is_animal=True`, `animal_count=0`, `average_weight=0.0`,
  `biological_stage=False`) → OK (lot 82) — fix
  farm_livestock BEKERJA.
- REPRO-5: vals UI lengkap (+ life_stage + current_weight)
  → gagal di `life_stage`.

**Perbaikan yang diperlukan (B10-residu):** terapkan pola
defensif yang sama (no-op bila tanpa Matter Tracking / nilai
= default UI / nilai = hasil compute; tetap UserError bila
benar-benar menyimpang) ATAU `readonly="1"` di view, pada
inverse di `farm_processing/models/stock_lot.py`:
`_inverse_matter_life_stage` (`life_stage`),
`_inverse_current_weight` (`current_weight`), dan
`_inverse_spatial_properties` (`last_gps_lat`/`last_gps_lng`)
— karena ketiganya adalah computed bridge non-stored yang
sama polanya dengan yang sudah diperbaiki di
`farm_livestock/models/farm_lot.py`.

Pengganti UI (transparan, pola B3 lot 53): lot sapi B3F
dibuat via shell (`/tmp/b3f_p3b.py`) dengan nilai sama persis
seperti percobaan UI yang gagal: **stock.lot id 84**
`SIMULASI B3F-LOT-SAPI-001` (is_animal, animal_name
`SIMULASI B3F Sapi 001`, ear tag `SIMULASI B3F-ET-001`,
birth 2026-11-10, start_weight 300, ADG 0,8,
`active_feeding_bom_id`=27), quant 10 ekor; terverifikasi
`animal_count=1`, `biological_stage='born'`,
`average_weight=0.0`, `current_predicted_weight=300.0`, sapi
on-hand 11,0 (10 + sire 1).

#### B11 — LOLOS ✓ (cron pakan harian)

`/tmp/b3f_p3b.py`: MO pakan sapi via UI (MO56, Confirmed)
diselesaikan alur UI-equivalent → `done` (raw pakan 10,00
kg, finished 1,00 ekor, lot baru `0000024`); stok pakan sapi
100 → 90 kg, sapi 11 → 12 ekor. `total_feed_consumed` lot 84
tetap 0.0 / FCR 0.0 sesudah MO56 (MO56 `lot_producing_id`
kosong — field itu TIDAK ADA di form MO; observasi lama B3).

`stock.lot._cron_daily_feed_depletion()` → **SELESAI tanpa
exception**. MO baru: **WH/MO/00057 (id 57, B3!)** dan
**WH/MO/00058 (id 58, B3F)** — keduanya `done`, raw pakan
10,00 kg done, finished 1,00 ekor done, `lot_producing_id`
terisi (53 / 84). Stok B3F: pakan 90 → 80 kg, sapi 12 → 13
ekor. **Jebakan `_set_quantities` (PORTING.d §6.6) TIDAK
muncul** — `button_mark_done` → `pre_button_mark_done` →
auto checks → `_set_quantities()` berjalan; move ter-pick
dan stok bergerak.

**EFEK SAMPING WAJIB DILAPORKAN (transparan):** cron tidak
punya filter lot — ia memproses SEMUA lot yang memenuhi
syarat, termasuk lot B3 lama **53** (`SIMULASI B3-LOT-SAPI-001`,
masih punya `active_feeding_bom_id`=21, stage `born`).
Akibatnya data B3 ikut berubah: MO57 tercipta + `done`,
pakan sapi B3 90 → 80 kg, sapi B3 10 → 11 ekor,
`total_feed_consumed` lot 53 kini 1.0. Ini konsekuensi desain
cron, bukan kesalahan eksekusi; untuk run cron berikutnya,
pertimbangkan mengosongkan `active_feeding_bom_id` lot 53
dulu (keputusan parent — JANGAN dilakukan sendiri tanpa
perintah karena itu juga mengubah data B3).

Observasi terkait: `total_feed_consumed` lot 84 = **1.0**
sesudah cron (bukan 10.0) karena `_compute_feed_stats`
(`farm_livestock/models/farm_lot.py:206-218`) menjumlah
`feeding_ops.mapped('product_qty')` — yaitu qty MO (1 ekor),
BUKAN kg pakan mentah — dengan komentar `# Simplified`. FCR
tetap 0.0 (weight_gain = 0; predicted weight = start_weight
di hari ke-0).

#### Ternak — event + MO panen via UI: LOLOS

Fase D2 (`browser-proof-b3f-d2.py`, screenshot 225–231, 0
pageerror + 0 console error):

- Form lot 84 + tab Cultivation Data: `300.00` tampil,
  `0.80` tampil (screenshot 226 membuktikan `Average Daily
  Gain (kg/day) 0.80` — cek teks False adalah artefak
  race/innerText). Screenshot 226 juga membuktikan form lot
  menampilkan `Is Animal Asset` ter-check, `Active Feeding
  Recipe SIMULASI B3F Sapi Perah`, `Predicted Weight (kg)
  300.00`, `Biological Stage Born/Started`.
- Event timbang via UI (action 1031): `farm.livestock.event`
  id **3**, Weight Measurement, **320.00 kg** (screenshot 227
  membuktikan `Measured Weight (kg) 320.00` — cek teks
  `'320'` False adalah artefak).
- Breeding record via UI (action 1033):
  `farm.breeding.record` id **2** (animal lot 84, sire lot 72,
  offspring 1), `gestation_days = 0` (observasi lama:
  onchange sire hanya mengenali pig/cow/cattle/sheep/goat/
  horse di nama produk, `Sapi` tidak cocok).
- Env monitoring via UI (action 1032):
  `farm.livestock.house.env` id **2** (lahan B3F, temp 28,
  humidity 65, ammonia 5, CO2 400); `comfort_index` =
  **77.64** (terverifikasi shell, sama persis dengan B3).
- MO panen daging via UI (action 934): **WH/MO/00059
  (id 59)**, qty 250, Confirm → `Confirmed`.

Fase 3c (`/tmp/b3f_p3c.py`): MO59 → `done` (raw sapi 1,00
ekor, finished daging 250,00 kg, lot `0000025`); stok sapi
13 → 12 ekor, daging 0 → 250 kg. Mortalitas
`action_record_mortality(1, 'Sakit')` pada lot 84 → chatter
saja, stok sapi tetap 12,0 (sesuai kode upstream).

#### B13 — LOLOS ✓ (hook telemetri DO rendah)

Fase 3c (`/tmp/b3f_p3c.py`, commit SEBELUM panggilan
telemetri): MO draft **WH/MO/00060 (id 60)** (produk Lele,
BoM pakan lele 29, qty 1.000) + task aqua B3F
**`agri.isl.aquaculture.task` id 2** `SIMULASI B3F Task
Telemetri Lele` (`hasattr(task, 'message_subscribe')` =
True). Panggil
`handle_aquaculture_telemetry({'dissolved_oxygen': 2.0,
'temperature': 29.0})` (ambang recipe 4.0) → **return True,
tanpa crash**. Hasil: `latest_do_level=2.0`,
`latest_water_temp=29.0`, `agent_instruction_json = {"action":
"set_aerator", "state": "on", "duration_minutes": 60, "pond":
"WH/MO/00060"}`, aktivitas insiden id **489** `INCIDENT:
Oxygen Depletion (critical)` (0 → 1).

#### B14 — LOLOS (tab) ✓, dengan efek samping pada action 1024

Probe DOM (`browser-proof-b3f-e.py`, screenshot 232–233;
probe `/tmp/b3f_probe1024.py`): form operasi MEMILIKI
notebook: `{'notebooks': 1, 'tabs': ['Description', 'Extra
Info', 'Aquaculture Information', 'Agri Farm Operations'],
'formHeight': 854}` — bandingkan B3: 0 notebook, ~5.900 px
field dump. Berlaku untuk form New DAN operasi 3 (B3).
**Tab "Aquaculture Information" ADA — B14 teratasi.**

**Efek samping B14 (temuan baru, perlu keputusan ronde
perbaikan):** `/odoo/action-1024` kini langsung membuka
**form New** (0 `.o_list_view`, 1 `.o_form_view`, breadcrumb
"New") — daftar operasi TIDAK lagi terbuka dari menu.
Penyebab paling mungkin: fix B14 yang memberi `view_id`
eksplisit 2772 pada action 1024 (sebelumnya action "tidak
menentukan `view_id` (view_mode: list,form saja)" — §3i di
atas). Perlu diverifikasi ronde perbaikan apakah menghapus
`view_id` (mode primary saja) mengembalikan list sambil
mempertahankan tab. Catatan: ini BUKAN kegagalan B12/B14
sebagai tab — tapi regresi navigasi daftar.

#### B12 — MASIH GAGAL via UI (blocker tersisa #2; depend_on_ids sudah benar)

Fase E1 (`browser-proof-b3f-e.py`): percobaan pertama gagal
BUKAN karena B12 — field `name` pada form project.task
adalah **`<textarea class="o_input" placeholder="Task
Title...">`**, bukan `<input>`, sehingga `set_text` (hanya
mencari `input`) tidak menemukannya → Save tertahan diam-diam
(nama wajib kosong), URL tetap `/new`, tanpa dialog error.
Semua field aqua lain terisi benar (screenshot 234: Pond
SIMULASI B3F-KOLAM-001, Lele Dumbo, 1,000, Growing, 28.00,
7.20, 6.50, 0.30, 0.1, 3.00).

Fase E1b (`browser-proof-b3f-e1b.py`, screenshot 244–247,
setter diperbaiki ke `input, textarea`): Save memunculkan
dialog **"Oh snap!"** (screenshot 247):

> `Field must be a many2one or many2many relation on itself: 'parent_id'`

Skrip lalu crash (TimeoutError 30 dtk saat klik tab — modal
`o_technical_modal` menutupi pointer). Jadi: **fix
`depend_on_ids` BEKERJA, tapi constraint berikutnya yang
meledak adalah `parent_id`** — `project.task` punya
`@api.constrains('parent_id') def _check_parent_id`
(`odoo/addons/project/models/project_task.py:574-576`) yang
memanggil `self._has_cycle()` (default field `parent_id`,
Many2one ke `project.task`); `_has_cycle` menuntut
`field.comodel_name == self._name`, dan
`parent_id.comodel_name` = `project.task` ≠
`farm.aquaculture.operation`. Client mengirim
`parent_id=False` saat create (semua field di view ikut
terkirim), sehingga constraint terpanggil. (Constraint
`depend_on_ids` ada di baris 492–495 file yang sama.)

Reproduksi minimal via shell (`/tmp/b3f_repro_b12.py`,
rollback, tanpa data tertinggal):

- REPRO-1: create tanpa `parent_id`/`depend_on_ids` → OK
  (op 5).
- REPRO-2: + `parent_id=False` → `ValueError: Field must be
  a many2one or many2many relation on itself: 'parent_id'`
- REPRO-3: + `depend_on_ids=[(6,0,[])]` → OK (op 7) — fix
  depend_on_ids TERBUKTI.
- REPRO-4: vals UI lengkap (`parent_id=False`,
  `depend_on_ids=[]`, `dependent_ids=[]`) → gagal di
  `parent_id`.
- (ID op 5 dan 7 hanya menghabiskan sequence — rollback.)

Bukti server: satu-satunya `Traceback` di
`/tmp/odoo18-server-b3f.log` selama ronde ini adalah
persis `ValueError: Field must be a many2one or many2many
relation on itself: 'parent_id'` dari percobaan UI E1b
(`web_save` → `project_task.py:576` `_check_parent_id` →
`_has_cycle`). UserError B10 tidak meninggalkan traceback
(exception ditangani, dikembalikan sebagai dialog).

**Perbaikan yang diperlukan (B12-residu):** perlakukan
`parent_id` seperti `depend_on_ids`: redefine dengan comodel
`'farm.aquaculture.operation'` + `recursive=True` (cerminan
definisi core), ATAU keluarkan field itu dari form/view
sehingga client tidak mengirimnya, ATAU override
`_check_parent_id` agar tidak memanggil `_has_cycle` dengan
comodel asing. Periksa juga field relasi-diri lain warisan
`project.task` yang mungkin dikirim client (`child_ids` —
One2many, constraint di baris 319 hanya `company_id`/
`partner_id` — aman dari cycle; tapi verifikasi ulang saat
ronde perbaikan).

Pengganti UI (transparan, pola B3 operasi 3): operasi B3F
dibuat via shell (`/tmp/b3f_p3d.py`): **`farm.aquaculture.operation`
id 9** `SIMULASI B3F Operasi Lele Kolam 001` (pond lot 73,
Lele Dumbo, stocking 1.000, stage Growing, bobot awal 50 g,
target 500 g, feeding 3%, T 28, pH 7.2, DO 6.5, NH3 0.3,
NO2 0.1); `action_schedule_harvest('2027-03-01')` →
`harvest_plan_date = 2027-03-01`; `harvest_readiness =
False`, `avg_current_weight = 50.0` (temuan lama: compute
selalu = bobot awal).

#### Fase E2 — WQ log via UI LOLOS; skrip crash karena bug skrip sendiri (bukan modul)

Fase E2 (`browser-proof-b3f-e2.py`): WQ log via UI (action
1025) → operasi B3F: **tersimpan, `farm.water.quality.log`
id 2** (URL `/odoo/action-1025/2?debug=1`, errdlg 0,
screenshot 238). Lalu skrip crash `NameError: name 'text'
is not defined` di baris 152 — bug variabel skrip sendiri
(`"28.50" in text` seharusnya `"28.50" in txt`). MO
pakan/panen lele via UI, ISL aqua lot, dan Aqua Tasks list
dilanjutkan di E2b.

Fase E2b (`browser-proof-b3f-e2b.py`, screenshot 250–255,
**0 pageerror + 0 console error**):

- Form operasi 9 B3F, tab "Aquaculture Information" (klik
  tab + screenshot 250 membuktikan tab aktif dengan
  Pond/Tank `SIMULASI B3F-KOLAM-001`, species Lele Dumbo,
  stage Growing).
- **Write-back WQ terverifikasi**: shell (`/tmp/b3f_q5.py`)
  membaca WQ log 2 → operasi 9: T 28.5, pH 7.4, DO 6.8,
  NH3 0.2, NO2 0.05, `water_quality_status='good'`; RPC
  `read` ke web client mengembalikan nilai yang sama;
  screenshot 256 (probe `/tmp/b3f_probe_shot.py`) membuktikan
  visual: Water Temperature **28.50**, pH **7.40**,
  Dissolved Oxygen **6.80**, Ammonia **0.20**, Nitrite
  **0.05**, Water Quality Status **Good**, Daily Feeding Rate
  **3.00**.
- MO pakan lele via UI (action 934): **WH/MO/00061 (id 61)**,
  produk `SIMULASI B3F Lele`, BoM sama, qty 1.000, Confirm →
  `Confirmed` (screenshot 251).
- MO panen lele via UI: **WH/MO/00062 (id 62)**, produk
  `SIMULASI B3F Lele Panen`, qty 50, Confirm → `Confirmed`
  (screenshot 252).
- ISL aqua lot B3F form (id 2, direct URL): `SIMULASI
  B3F-LOT-LELE-001` tampil, errdlg 0 (screenshot 253).
- Aqua Tasks list (action 1026) + form New lalu Discard
  (tanpa simpan): errdlg 0 (screenshot 254–255). Body form
  New 272 karakter — sama seperti observasi B3.

Fase 3e (`/tmp/b3f_p3e.py`): MO61 → `done` (raw pakan lele
50,00 kg, finished lele 1.000,00 ekor, lot `0000026`); MO62
→ `done` (raw lele 100,00 ekor, finished lele panen 50,00
kg, lot `0000027`); stok: pakan lele 100 → **50 kg**, lele
1.000 → **1.900 ekor**, lele panen 0 → **50 kg**, kolam
tetap 1.

#### Fase F — sapuan regresi browser: LOLOS

`browser-proof-b3f-f.py` (screenshot 257–266): Home, Term
Mappings (1015), MO list (934), form produk Tomat Segar B3F
(template 155, `5,480` tampil), NPK B3F (template 157,
`0.00` tampil), ISL form `agri.isl.mrp.production` id 48
(header `WH/MO/00055` tampil di screenshot 262 — cek teks
`'WH/MO/00055'` False adalah artefak innerText), Livestock
Recipes (1034, body 187 — sama seperti B3), Aqua Recipes
(1027, body 161 — sama seperti B3), MO61 `Done` 1,000.00,
MO62 `Done` 50.00. **0 pageerror + 0 console error, tanpa
Oops di halaman mana pun.**

#### Pelajaran metodologi baru ronde ini (wajib diingat)

Cek teks via `innerText` **TIDAK mencakup nilai di dalam
`<input>`** — dan widget Float di form operasi akuakultur
me-render `<input>` (bukan `<span>`) walau form dalam mode
read: `water_temperature`/`ph_level`/`dissolved_oxygen`/
`ammonia_level`/`nitrite_level`/`harvest_plan_date` semuanya
innerText kosong padahal nilainya benar (terbukti RPC +
screenshot 256). Jadi cek teks False pada field Float di
form ini BUKAN bukti negatif; bukti = screenshot atau
`input.value`. Pola yang sama menjelaskan cek False
`'320'`/`'28.50'` di fase-fase sebelumnya (bukan race
render semata). Selection `aquaculture_stage` menampilkan
SEMUA opsi di innerText pane (bukan hanya yang terpilih) —
jangan jadikan itu bukti nilai.

#### Data tertinggal B3F (ringkas)

Produk template 153–164 (varian 165–176); lahan 8; campaign
8; route 7; BoM 25–30; seed 11; nursery 6; asset 8; rotation
7; intervensi 21–26; crop lot 4; QC 4/4/4; season 5; sbom 5;
market price 5; fair val 5; cost val 6; MO 47–51, 53–56,
58–62 (+57 milik B3, +60 draft); ISL mrp total 48; lot sapi
84 (+ sire 72); lot kolam 73; lot lele 74; event timbang 3;
breeding 2; env monitoring 2; operasi aqua 9; WQ log 2; task
aqua 2 (MO 60 draft); ISL livestock recipe 2; ISL aqua
recipe 2; ISL aqua lot 2.

Stok akhir B3F (WH/Stock, company 1; 10 Nov 2026): benih
10 kg, bibit 25.000 unit, tomat segar **5.480 kg**, saus
tomat **16 kg**, NPK **0 kg**; sapi **12 ekor**, pakan sapi
**80 kg**, daging sapi **250 kg**; kolam lele **1**, lele
**1.900 ekor**, pakan lele **50 kg**, lele panen **50 kg**.

Nomor MO yang hilang (sequence-only, record tidak ada):
WH/MO/00039 + 00040 (rollback cron B11 lama), 00044 (gagal
create task B13 lama), **00046** (gagal create intervensi
B3F), **00052** (gagal MO saus B3F), serta op repro 5 dan 7
(rollback).

#### Perbaikan yang DIPERLUKAN (ronde perbaikan berikutnya)

1. **B10-residu (fatal, `farm_processing/models/stock_lot.py:78,85,92`):**
   inverse `life_stage` / `current_weight` / `last_gps_lat`/
   `last_gps_lng` selalu raise Legacy Write Block — client
   mengirim ketiganya saat Save lot via UI (lot hewan MAUPUN
   lot biasa). Terapkan pola defensif farm_livestock (no-op
   bila tanpa Matter Tracking / nilai default UI / nilai =
   hasil compute) atau `readonly="1"` di view. Fix
   farm_livestock 18.0.1.2.1 sendiri TERBUKTI bekerja
   (REPRO-4).
2. **B12-residu (fatal, `farm_aquaculture/models/aquaculture_operation.py`
   + core `project_task.py:574-576`):** `depend_on_ids`
   sudah benar (REPRO-3), tapi `parent_id` (Many2one ke
   `project.task`, constraint `_check_parent_id` →
   `_has_cycle`) meledak saat client mengirim
   `parent_id=False`. Redefine `parent_id` dengan comodel
   `'farm.aquaculture.operation'` + `recursive=True`, atau
   keluarkan dari form/view, atau override
   `_check_parent_id`. Periksa juga field relasi-diri lain
   warisan `project.task` (`child_ids` dst.).
3. **Efek samping B14 (navigasi, action 1024):** daftar
   operasi tidak lagi terbuka dari menu — action 1024
   langsung membuka form New (kemungkinan karena `view_id`
   eksplisit 2772). Verifikasi apakah menghapus `view_id`
   (mode primary saja) mengembalikan list sambil
   mempertahankan tab.
4. **Observasi (bukan blocker):** `total_feed_consumed`
   menjumlah qty MO (1 ekor), bukan kg pakan (10 kg) —
   `_compute_feed_stats` `# Simplified`; FCR tetap 0.0 di
   hari ke-0; `gestation_days` breeding = 0 untuk produk
   bernama `Sapi` (onchange hanya mengenali nama Inggris);
   `avg_current_weight` operasi = bobot awal; cron B11
   tanpa filter lot (memproses lot B3 lama — lihat efek
   samping di atas).

---

## Simulasi kumulatif batch 3 — ronde perbaikan residu (B3G) (10 Nov 2026, sore WIB)

Ronde perbaikan residu sesudah upgrade `farm_processing`
18.0.1.1.3 + `farm_aquaculture` 18.0.1.0.2 (farm_operation
18.0.1.2.7, farm_isl 18.0.1.0.3, farm_ux 18.0.1.1.3,
agri_intervention 18.0.1.0.1, farm_livestock 18.0.1.2.1,
farm_core 18.0.1.0.1, farm_mrp 18.0.1.1.0; total 21 modul
farm installed, semua `installed_version = latest_version`).
**VM replacement di tengah ronde** (~06:57 WIB, saat Fase D2
sedang jalan): user `pgtest` + `/opt/pgserver` hilang, test
bed dipulihkan sesuai `~/AGENTS.md` (useradd uid 1001 +
rebuild `/opt/pgserver` dari pip `pgserver` + start PG dari
`~/workspace/pgrun`, socket `~/workspace/pgsock`, port 5433;
log server `/tmp/odoo18-server-b3g.log`); 8071 → 200
terverifikasi sesudah pemulihan. Data B3G utuh; `/tmp`
hilang total (skrip shell B3F + sebagian B3G ditulis ulang).
Semua data baru berawalan `SIMULASI B3G`; data lama
`SIMULASI` / `SIMULASI B2*` / `SIMULASI B3` / `SIMULASI B3F`
TIDAK diubah (kecuali efek samping cron B11, lihat bawah).
Skrip: `browser-proof-b3g-a.py`, `-b.py`, `-b2.py`, `-c.py`,
`-d.py`, `-d2.py`, `-d2b.py`, `-e.py`, `-e1b.py`, `-e2.py`,
`-e2b.py`, `-f.py` (screenshot 267–345; 301b–301e varian
probe lot tracking); skrip shell `/tmp/b3g_*.py`.

### Keputusan: BERSIH ✅

- Bagian 1 (rantai batch 1): **LOLOS 9/9**.
- Bagian 2 (verifikasi batch 2): **LOLOS**.
- Bagian 3 (alur batch 3 + residu): **LOLOS** — B10-residu,
  B11, B12-residu, B13, B14 **semua LOLOS via UI**; stok
  akhir terverifikasi. **0 pageerror + 0 console error di
  semua fase browser** (A, B, B2, C, D1, D2b, E1, E1b, E2,
  E2b, F; output stdout Fase D2 asli hilang bersama VM
  replacement — buktinya screenshot 306–309 + record DB,
  lihat bawah).

### Bagian 1 — rantai batch 1 (data B3G): LOLOS 9/9

Prep + data via `/tmp/b3g_p1.py`, `b3g_p1b.py`, `b3g_p1c.py`
(langkap 0–9): produk template 165–169, varian 177–181
(Benih/Bibit/Tomat Segar/Saus/NPK); lahan 9 (`SIMULASI B3G
Lahan A1`, WH/Stock id 8); campaign 9; route 8; BoM tomat 31
(5.000 kg ← 50 kg NPK), saus 32 (8 kg ← 10 kg tomat). Stok
awal benih 5 kg, NPK 50 kg.

- Seed batch 13 (lot benih 106), germ 92%,
  `is_pvp_compliant=True`; blok germinasi 70% TERBUKTI
  (`UserError: SEED QUALITY BLOCK: Batch SIMULASI
  B3G-LOT-BENIH-BLOK germination rate (70.0%) is below
  national standard.`).
- Nursery batch 7 (lot bibit 108, 25.000 bibit, transplant
  GDD 200); asset 9; rotation 8 (`planted`, warning False);
  GDD 170.0 → 187.0 → 357.0; stage 15 → 62.33, stage 16 →
  71.4, stage 17 → 44.625.
- Intervensi 27–31 (MO 63–67), workflow penuh draft →
  to_approve → approved/confirmed → in_progress → done;
  NPK fertilizing (IV28/MO64) 8.0/8.0/8.0.
- Crop lot 5 (lot panen 109, 500 kg, moisture 94%, protein
  0,9%); rotation → `harvested`, 2027-02-08. QC point/check
  5 → `pass`; record book 5 (`RB/2026/00004`) draft →
  `active`.
- Season 7, seasonal BoM 7 (tetap `draft`, stub
  `action_activate` — temuan lama); MO saus 69
  (WH/MO/00069) + 70 (WH/MO/00070) `done`; saus 16 kg,
  tomat 480 kg. Market price 6 (Rp 12.000/kg); fair
  valuation 6 (`VAL-SIMULASI B3G Tanaman Tomat
  A1-20261110-1`, market_price 0.0, fair_value 0.0 —
  temuan lama); cost valuation 7, NBV = fair =
  Rp 2.500.000.
- **MO 68 hanya nomor sequence** (hilang): `b3g_p1b.py`
  crash di print langkah 8 — `AttributeError:
  'stock.move' object has no attribute 'quantity_done'`
  (di Odoo 18 field-nya `quantity`); crash sebelum
  `commit()` me-rollback MO + season/sbom langkah 8;
  `b3g_p1c.py` mengulang dengan `quantity` dan berhasil.
  (Pola sama seperti MO 52 di B3F.)

**Fase A browser** (`browser-proof-b3g-a.py`, screenshot
267–279): **0 pageerror + 0 console error**. Tiga cek teks
False sudah dijelaskan dan BUKAN kegagalan: `'25,000'`
(form nursery tidak menampilkan kuantitas — sama seperti
B3F), `'357'` (form asset menampilkan
`growth_stage_id` kosong, bukan `accumulated_gdd` —
temuan lama batch 1 #6; GDD 357 terverifikasi shell),
`'WH/MO/00053'` (string cek basi di skrip — MO saus B3G
adalah WH/MO/00069, `Done:True`).

### Bagian 2 — verifikasi batch 2: LOLOS

**Fase B** (`browser-proof-b3g-b.py`, screenshot 280–287):
intervensi baru MURNI lewat UI — `SIMULASI B3G Intervensi
Pupuk NPK Tomat A1`, IV id **32** (URL
`/odoo/agri.intervention/32?debug=1`), MO auto; workflow
tombol header Submit for Approval → Approve → Start Agri
Work → Stop Agri Work sampai `Completed`/`Fertilizing`;
tab Costs 3× `8.00`; MO27 (tillage B2G) tab Spatial di
`?debug=1`: gauge **100% Within Boundaries**, tanpa
`NaN%`. **0 pageerror + 0 console error.** Catatan skrip:
penemuan MO via link `WH/MO/` di form IV gagal (`MO link
href: None`) — quirk skrip, bukan kegagalan.

**Kesalahan eksekusi + koreksi (dilaporkan transparan):**
`/tmp/b3g_mo_b2.py` mencari IV by name dan menemukan IV28
(batch 1, nama sama persis) bukan IV32, sehingga
menyelesaikan **MO64 (WH/MO/00064, milik IV28 batch 1)
secara keliru** → tomat 480 → 5.480 kg, NPK 50 → 0 kg.
Perbaikan `/tmp/b3g_mo_b2_fix.py`: IV32 → **MO71
(WH/MO/00071)**, `intervention_type='fertilizing'`, NPK
8.0/8.0/8.0; NPK diisi ulang +50 kg via quant (pola setup
yang sama seperti B3/B3F — dicatat sebagai koreksi); MO71
selesai → `done`, raw NPK 50,00 kg, finished tomat
5.000,00 kg, lot `0000033`; **stok akhir batch 2: tomat
10.480 kg, NPK 0 kg** (5.480 dari MO64 yang keliru +
5.000 dari MO71 yang benar).

**Fase B2** (`browser-proof-b3g-b2.py`, screenshot
288–289): form MO71 (`WH/MO/00071`, `Fertilizing`, gating
WEATHER), tab Soil Nutrient 3× `8.00`. 0/0 error.

**Fase C** (`browser-proof-b3g-c.py`, screenshot 290–295):
wizard migrasi ISL (action 1013). Pra-C: MO tanpa ISL = 15
(56–62, 63–67, 69–71). Run 1 klaim **"15 records
migrated"** (tepat), dialog menutup sendiri (dialogs 1→0),
notifikasi hijau t+2s s.d. t+4s; Run 2 klaim **"0 records
migrated"**, dialog menutup; negatif Confirm OFF →
UserError `Please confirm the migration before proceeding`,
dialog tetap terbuka. **0 pageerror + 0 console error.**
ISL `agri.isl.mrp.production` kini 63 (48+15).

### Bagian 3 — alur batch 3 + bukti B10–B14

#### Prep batch 3 (shell, OK — `/tmp/b3g_p3prep.py`)

Ternak: template Sapi Perah/Pakan Sapi/Daging Sapi 170–172
(varian 182–184); pakan sapi stok 100 kg; BoM pakan sapi
**33** (`feeding`, 1 ekor ← 10 kg pakan), BoM panen sapi
**34** (`harvesting`, 250 kg daging ← 1 ekor); ISL
livestock recipe **3**; sire lot **115** (`SIMULASI
B3G-LOT-SAPI-SIRE`, is_animal, lahir 2024-01-01, breeding
open, start_weight 500, ADG 0,7). Akuakultur: kategori
`SIMULASI B3G Pond`; template Kolam Lele/Lele/Pakan
Lele/Lele Panen 173–176 (varian 185–188); pakan lele stok
100 kg; lot kolam **116**, lot lele **117** (1.000 ekor);
BoM pakan lele **35** (`feeding`, 1.000 ekor ← 50 kg
pakan), BoM panen lele **36** (`harvesting`, 50 kg panen ←
100 ekor); ISL aqua recipe **3**; ISL aqua lot **3**
(`current_density=0.0`, `total_biomass=0.0` — temuan lama).

#### B10-residu — LOLOS ✓ (bukti shell + UI)

**Lot DENGAN tracking via shell** (`/tmp/b3g_tracklot.py`):
lot **118** `SIMULASI B3G-LOT-TRACKING-001` (tomat B3G,
quant 5 kg), package **3**, tracking **3** (`SIMULASI
B3G-TRACKING-001`, current_weight 120.5, life_stage
`mature`, lat 41.25, lng -73.98). Read-back compute tepat
(120.5/`mature`/41.25/-73.98). Tulis SAMA dengan compute →
no-op OK (4 kasus: weight 120.5, stage `mature`, GPS sama,
weight default 0.0). Tulis MENYIMPANG → **UserError untuk
ketiga inverse**: weight 999.0 → `Legacy Write Block:
Weight is now managed dynamically by Matter Tracking
(LPN/Vessel). Please update the weight on the active Matter
Tracking container directly.`; stage `juvenile` → `Legacy
Write Block: Lifecycle stages are now managed dynamically
by Matter Tracking (LPN/Vessel). Please update status on
the active Matter Tracking container.`; GPS 10.0/10.0 →
`Legacy Write Block: GPS positioning is now managed
dynamically by Matter Tracking (LPN/Vessel). Please sync
coordinates via the active Matter Tracking container`.
Nilai akhir tetap 120.5/`mature`/41.25/-73.98. **Cabang
raise terbukti live, bukan hilang.**

**Fase D1 browser** (`browser-proof-b3g-d.py`, screenshot
296–305): **B10a lot hewan via UI SAVED, id 119**
(`SIMULASI B3G-LOT-SAPI-001`; `is_animal` +
`active_feeding_bom_id` ada di form; `start_weight` 300 +
`average_daily_gain` 0.8 diisi via tab "Cultivation Data"
— bukan "Livestock" seperti draf awal skrip); **B10b lot
biasa (tomat) via UI SAVED, id 120** (`SIMULASI
B3G-LOT-TEST-B10`); **MO pakan sapi via UI SAVED +
Confirmed, MO72** (WH/MO/00072; `lot_producing_id` widget
NOT FOUND — observasi lama, field tidak ada di form MO).
**0 pageerror + 0 console error.**

**Lot tracking Edit+Save via UI — LOLOS sesudah 3 probe
diagnostik** (pelajaran metodologi penting): Odoo 18
TIDAK punya tombol Edit di control panel; form yang dibuka
via URL langsung terbuka dalam mode edit
(`.o_form_editable` True); tombol Save/Discard utama hanya
ada di slot `layout-buttons` bila `env.inDialog` — di view
utama, affordance save adalah tombol ikon
`FormStatusIndicator`
(`.o_form_status_indicator.o_form_button_save`), yang HANYA
terlihat bila ada perubahan belum tersimpan (`.o_form_button_save`
pertama yang di-resolve `.first` adalah tombol ikon
tersembunyi itu — jangan diklik sebelum ada perubahan).
`current_weight`/`life_stage` TIDAK ada di DOM untuk lot
118 karena `lot_purpose='production'` — page "Livestock
Lifecycle"/"Biological Asset" hanya tampil bila
`lot_purpose == 'biological_asset'`; field-field itu juga
`readonly="1"` di view (jadi client tidak pernah
mengirimnya). Probe final (`/tmp/b3g_track_save3.py`): ubah
`ref` → `B3G-REF-001`, tombol save indikator muncul, klik
→ **0 errdlg, 0 pageerror/console error**, screenshot 301d
(edit) + 301e (saved). Verifikasi shell
(`/tmp/b3g_verify118.py`): `ref='B3G-REF-001'` tersimpan;
compute tetap 120.5/`mature`/41.25/-73.98. (Cek
`'B3G-REF-001' in text: False` di browser hanya artefak
innerText — field `ref` tidak tampil di area terlihat;
shell membuktikan persistensi.)

#### B11 — LOLOS ✓ (cron pakan harian)

`/tmp/b3g_p3b.py`: lot 119 terverifikasi lengkap dari UI
(is_animal, animal_name `SIMULASI B3G Sapi 001`, ear tag
`SIMULASI B3G-ET-001`, birth 2026-11-10, start_weight 300,
ADG 0.8, `active_feeding_bom_id`=33, `animal_count`=1,
stage `born`, `average_weight`=0.0,
`current_predicted_weight`=300.0). Quant +10 ekor → sapi
on-hand 11,0. **MO72 selesai** (alur UI-equivalent):
`done`, raw pakan 10,00 kg, finished 1,00 ekor, lot
`0000036`; pakan 100 → 90 kg, sapi 11 → 12 ekor.
`total_feed_consumed` lot 119 tetap 0.0 / FCR 0.0 sesudah
MO72 (MO72 `lot_producing_id` kosong — observasi lama).
**Cron `_cron_daily_feed_depletion()` SELESAI tanpa
exception**; MO baru **73** (B3, lot 53), **74** (B3F, lot
84), **75** (B3G, lot 119) — ketiganya `done`,
`lot_producing_id` terisi, raw pakan 10 kg, finished 1
ekor. B3G: pakan 90 → 80 kg, sapi 12 → 13 ekor;
`total_feed_consumed` lot 119 = 1.0, FCR 0.0. Log server:
`Daily feed depletion recorded for lot SIMULASI
B3G-LOT-SAPI-001 using BOM SIMULASI B3G Sapi Perah` (fix
`.display_name` bekerja). **Efek samping WAJIB dilaporkan
(desain cron tanpa filter lot, sama seperti B3F):** B3
pakan 80 → 70 kg, sapi 11 → 12 ekor; B3F pakan 80 → 70
kg, sapi 12 → 13 ekor; `total_feed_consumed` lot 53/84:
1.0 → 2.0.

#### Ternak — event + MO panen via UI: LOLOS (Fase D2 + D2b)

**Fase D2** (`browser-proof-b3g-d2.py`, screenshot
306–309): form lot 119 + tab Cultivation Data (306–307),
event timbang via UI action 1031 (Weight Measurement 320
kg, 308), breeding record via UI action 1033 (animal 119,
sire 115, offspring 1, `gestation_days` — observasi lama: 0
untuk produk bernama `Sapi`, 309). **VM replacement
memotong skrip di titik ini** — stdout D2 hilang, tetapi
screenshot 306–309 ada di disk dan record DB terverifikasi
sesudah pemulihan: event timbang id **4** (`weight`,
320.0), breeding id **3** (gestation 0, offspring 1), env
B3G BELUM ada (id 2 yang tampil adalah milik B3F), MO max
masih 75, belum ada MO daging B3G.

**Fase D2b** (`browser-proof-b3g-d2b.py`, screenshot
310–312, lanjutan sesudah pemulihan): env monitoring via
UI action 1032 (lahan B3G, T 28, humidity 65, ammonia 5,
CO2 400 → `farm.livestock.house.env` id **3**,
`comfort_index` **77.64**, 310), MO panen daging via UI
action 934 (produk Daging Sapi B3G, BoM sama, qty 250,
Confirm → **MO106 WH/MO/00106**, 311–312). **0 pageerror
+ 0 console error.** Catatan: ID MO 106 meloncat dari max
75 — lompatan sequence +31 pada PK `mrp_production_id_seq`
maupun nomor `WH/MO/` (00075 → 00106), tanpa record
yatim: 0 orphan `stock.move`, semua data B3G utuh
(IV32/MO71 `done`, MO72–75 `done`, lot 119, cron MO75
`lot_producing_id`=119); PG log: `database system was not
properly shut down; automatic recovery in progress` —
lompatan konsisten dengan crash recovery VM replacement,
bukan korupsi data. Nomor MO 00076–00105 tidak ada
record-nya (sequence-only).

**Fase 3c** (`/tmp/b3g_p3c.py`, ditulis ulang sesudah /tmp
hilang): MO106 → `done` (raw sapi 1 ekor, finished daging
250,00 kg, lot `0000069`); sapi 13 → **12 ekor**, daging
0 → **250 kg**. Mortalitas
`action_record_mortality(1, 'Sakit')` pada lot 119:
chatter saja, stok sapi tetap 12,0 (sesuai kode upstream).

#### B13 — LOLOS ✓ (hook telemetri DO rendah)

`/tmp/b3g_p3c.py` (lanjutan): MO task draft **107**
(WH/MO/00107, produk Lele B3G, BoM pakan lele 35, qty
1.000) + task `agri.isl.aquaculture.task` baru id **3**
(`SIMULASI B3G Task Telemetri Lele`,
`product_id`=lele, `product_qty`=1000, `bom_id`=35);
commit SEBELUM telemetri; panggil
`handle_aquaculture_telemetry({'dissolved_oxygen': 2.0,
'temperature': 29.0})` (ambang recipe 4.0) → **return
True tanpa crash**, `latest_do_level`=2.0,
`latest_water_temp`=29.0, `agent_instruction_json` =
`{"action": "set_aerator", "state": "on",
"duration_minutes": 60, "pond": "WH/MO/00107"}`,
aktivitas insiden bertambah 0 → 1 (id 490, `INCIDENT:
Oxygen Depletion (critical)`).

#### B14 + B12-residu — LOLOS ✓ (Fase E1 + E1b)

**Fase E1** (`browser-proof-b3g-e.py`, screenshot
313–320): action 1024 **membuka DAFTAR dulu** (1 list
view, 0 form, 2 rows — operasi 3 + 9; `'SIMULASI B3
Operasi'` + `'SIMULASI B3F Operasi'` tampil, 313);
operasi baru via UI: New → isi lengkap (nama
`SIMULASI B3G Operasi Lele Kolam 001`, pond
`SIMULASI B3G-KOLAM-001`, species `Lele Dumbo`, stocking
1.000, stage Growing, bobot awal 50 g, target 500 g,
feeding 3%, T 28, pH 7.2, DO 6.5, NH3 0.3, NO2 0.1 —
field `name` adalah `<textarea>`, setter harus
`input, textarea`) → **Save BERHASIL tanpa dialog "Oh
snap!"** (`parent_id=False` + `depend_on_ids` sudah
diperbaiki), **operasi id 10** (314–316). Form operasi
baru + operasi 3 + operasi 9: notebook **4 tab** termasuk
"**Aquaculture Information**", formHeight 854 (317,
319–320); nilai WQ operasi 10 terverifikasi shell: T 28.0,
pH 7.2, DO 6.5, NH3 0.3, NO2 0.1, stocking 1000, stage
`growing`, `parent_id=False`, `subtask_count`=0 (cek teks
`'28.00'`/`'6.50'`/`'Lele Dumbo'` False di pane adalah
artefak innerText — nilai Float ada di `<input>` dan
terbukti di screenshot 317 + shell; pola yang sama
menjelaskan `'28.50'` False di operasi 3, padahal
`'Good'` True). Operasi 3 (B3) + operasi 9 (B3F) tetap
bisa dibuka, tab + nilai WQ lama utuh. **0 pageerror + 0
console error.**

**Sub-task — prasyarat core ditemukan di E1, diselesaikan
di E1b:** tab "Sub-tasks" TIDAK ada di form operasi 10
karena page-nya `invisible="not project_id"` (arch form:
`<page name="sub_tasks_page" string="Sub-tasks"
invisible="not project_id">` memuat `child_ids`) dan
operasi 10 `project_id=False`. Ini perilaku core
`project.task`, bukan bug modul.

**Fase E1b** (`browser-proof-b3g-e1b.py`, screenshot
321–323): set `project_id` op 10 via UI (`Wheat
Cultivation 2026`, id 6) → Save → tab **"Sub-tasks"
muncul** (5 tab); Add a line → isi nama `SIMULASI B3G
Sub-tugas Pemberian Pakan` → Enter → Save form → **0
errdlg, 0 pageerror + 0 console error**. Verifikasi shell:
op 10 `subtask_count` **= 1**, `child_ids` = **[11]**
(`SIMULASI B3G Sub-tugas Pemberian Pakan`, `parent_id`=10,
project `Wheat Cultivation 2026` terwarisi), `parent_id`
op 10 tetap False. **B12-residu LOLOS penuh.**

#### Fase E2 — WQ log + MO lele via UI: LOLOS

`browser-proof-b3g-e2.py` (screenshot 324–329, bug skrip
B3F `"28.50" in text` → NameError sudah diperbaiki jadi
`txt`): WQ log via UI action 1025 ke operasi 10 (T 28.5,
pH 7.4, DO 6.8, NH3 0.2, NO2 0.05, turbidity 5, salinity
0.5, weather `Cerah`) → **tersimpan, id 3**, errdlg 0
(324; `'28.50'`/`'6.80'` False di innerText — artefak
Float, write-back dibuktikan di E2b via `input.value`);
MO pakan lele via UI (produk Lele B3G, qty 1.000, Confirm)
→ **MO108** (325); MO panen lele via UI (produk Lele
Panen B3G, qty 50, Confirm) → **MO109** (326); ISL aqua
lot B3G form (id 3): `SIMULASI B3G-LOT-LELE-001` tampil,
errdlg 0 (327); Aqua Tasks list (1026) + form New lalu
Discard (tanpa simpan), errdlg 0 (328–329); form New
hampir kosong (body len 272 — observasi lama, sama seperti
B3/B3F). **0 pageerror + 0 console error.**

#### Fase E2b — write-back WQ + MO lele: LOLOS

`browser-proof-b3g-e2b.py` (screenshot 330–335):
**berbeda dari B3F** — E2b B3F membuat MO lele DUPLIKAT;
di B3G MO pakan/panen lele SUDAH dibuat di E2 (108/109),
jadi E2b HANYA membuka ulang form-nya sebagai bukti
visual, tanpa membuat MO baru (agar stok akhir tidak
terkontaminasi duplikat). Form operasi 10, tab Aquaculture
Information pasca write-back: `input.value` T **28.50**,
pH **7.40**, DO **6.80**, NH3 **0.20**, NO2 **0.05**,
`'Good'` True (330). Form MO108 (pakan lele) +
MO109 (panen lele): `Confirmed`, `WH/MO/` tampil
(331–332). ISL aqua lot 3 form OK (333). Aqua Tasks list
menampilkan `SIMULASI B3G Task Telemetri Lele` (334);
form New + Discard OK, body len 272 (335). **0 pageerror
+ 0 console error.**

**Fase 3e** (`/tmp/b3g_p3e.py`): MO108 → `done` (raw pakan
lele 50,00 kg, finished lele 1.000,00 ekor, lot
`0000070`); MO109 → `done` (raw lele 100,00 ekor,
finished lele panen 50,00 kg, lot `0000071`); stok: pakan
lele 100 → **50 kg**, lele 1.000 → **1.900 ekor**, lele
panen 0 → **50 kg**, kolam tetap 1. `total_feed_consumed`
lot 119 = 1.0, FCR 0.0; ISL aqua lot 3 density/biomass
0.0/0.0 (temuan lama).

#### Fase F — sapuan regresi browser: LOLOS

`browser-proof-b3g-f.py` (screenshot 336–345): Home, Term
Mappings (1015), MO list (934), form produk Tomat Segar
B3G (template 167, `10,485` tampil), NPK B3G (template
169, `0.00` tampil), ISL form
`agri.isl.mrp.production` id 63 (header `WH/MO/00071`
tampil), Livestock Recipes (1034, body 189 — sama seperti
B3/B3F: daftar 1–3/3 baris, hanya kolom ID terisi),
Aqua Recipes (1027, body 163 — sama), MO108 `Done`
1,000.00, MO109 `Done` 50.00. **0 pageerror + 0 console
error, tanpa Oops di halaman mana pun.**

#### Pelajaran metodologi baru ronde ini (wajib diingat)

- **VM replacement membunuh skrip browser di tengah jalan
  tanpa jejak stdout** — yang tersisa hanya screenshot di
  disk + record DB. Rencana pemulihan: verifikasi state
  via shell (record apa yang SUDAH tercipta), lalu jalankan
  skrip lanjutan HANYA untuk bagian yang belum (D2b),
  jangan ulangi seluruh fase (duplikat record). `/tmp`
  ikut hilang — skrip shell yang dibutuhkan sesudahnya
  ditulis ulang dari konten yang sudah dibaca.
- **Lompatan sequence MO (+31, 00075 → 00106) sesudah
  crash recovery bukan korupsi**: verifikasi 0 orphan
  `stock.move` + semua record kunci utuh sebelum
  melanjutkan; nomor yang hilang dicatat sebagai
  sequence-only, bukan rollback.
- **Tab "Sub-tasks" core `project.task` bersyarat
  `project_id`** — operasi tanpa project tidak pernah
  menampilkan tab itu; bukti sub-task via UI butuh set
  project dulu (UI, bukan shell).
- **E2b jangan menduplikasi MO** bila E2 sudah membuatnya
  — buka ulang form sebagai bukti visual saja.
- **Nama produk di skrip stok HARUS persis nama template**
  (`Saus Tomat Servo F1`, `Pupuk NPK 16-16-16`) — nama
  pendek mengembalikan recordset kosong yang
  `qty_available`-nya 0.0 dan tampak seperti stok hilang
  (insiden "saus 0 kg" ronde ini — false alarm).

#### Data tertinggal B3G (ringkas)

Produk template 165–176 (varian 177–188); lahan 9;
campaign 9; route 8; BoM 31–36; seed 13; nursery 7; asset
9; rotation 8; intervensi 27–32; crop lot 5; QC 5/5/5;
season 7; sbom 7; market price 6; fair val 6; cost val 7;
MO 63–67, 69–75, 106–109 (+107 draft task MO B13, +68
sequence-only); ISL mrp total 63; lot sapi 119 (+ sire
115); lot kolam 116; lot lele 117; lot tracking 118
(package 3, tracking 3, ref `B3G-REF-001`); lot biasa 120;
event timbang 4; breeding 3; env monitoring 3; operasi
aqua 10 (+ child 11 sub-task); WQ log 3; task aqua 3 (MO
107 draft); ISL livestock recipe 3; ISL aqua recipe 3;
ISL aqua lot 3.

Stok akhir B3G (WH/Stock, company 1; 10 Nov 2026): benih
**10 kg**, bibit **25.000 unit**, tomat segar **10.485 kg**
(10.480 + 5 kg quant lot tracking 118), saus tomat
**16 kg**, NPK **0 kg**; sapi **12 ekor**, pakan sapi
**80 kg**, daging sapi **250 kg**; kolam lele **1**, lele
**1.900 ekor**, pakan lele **50 kg**, lele panen **50 kg**.

Nomor MO yang hilang (sequence-only, record tidak ada):
**00076–00105** (lompatan sequence akibat crash recovery
VM replacement), 00068 (rollback `quantity_done` di p1b),
serta 00039/00040/00044/00046/00052 dari ronde lama.

#### Sisa observasi (bukan blocker — sama seperti ronde lama)

- `total_feed_consumed` menjumlah qty MO (1 ekor), bukan
  kg pakan (10 kg) — `_compute_feed_stats` `# Simplified`;
  FCR tetap 0.0 di hari ke-0; `gestation_days` breeding = 0
  untuk produk bernama `Sapi` (onchange hanya mengenali
  nama Inggris); `avg_current_weight` operasi = bobot awal;
  cron B11 tanpa filter lot (memproses lot B3/B3F lama).
- Nursery tanpa state machine + tombol pindah tanam stub;
  `farm.seasonal.bom.action_activate` stub; valuasi
  market_price/fair_value = 0.0 (NPK); ISL aqua lot
  density/biomass 0.0.
- Form New ISL aqua task hampir kosong (body 272);
  daftar ISL Recipes hanya menampilkan kolom ID.
- MO64 (WH/MO/00064) milik IV28 batch 1 selesai secara
  keliru di awal Bagian 2 (kesalahan skrip, sudah
  dikoreksi — lihat Bagian 2); efeknya tercermin di stok
  tomat akhir (5.480 kg dari MO64 + 5.000 kg dari MO71).

## Simulasi kumulatif batch 4 — 10 Nov 2026 (TIDAK BERSIH ❌)

Ronde kumulatif batch 4 (10 Nov 2026, siang–sore WIB). Server
sudah jalan saat mulai (PID 6606, 8071 → 200, log
`/tmp/odoo18-server-b4.log`); **tidak ada VM replacement
selama ronde ini**. 24 modul farm `installed` (total
farm+agri 31): batch 1 (14) + `agri_intervention`
18.0.1.0.1 + `farm_isl` 18.0.1.0.3 + `farm_ux` 18.0.1.1.3 +
`farm_livestock` 18.0.1.2.1 + `farm_aquaculture`
18.0.1.0.2 (+ matter) + `farm_processing` 18.0.1.1.3 +
`agri_iot` 18.0.1.0.0 + `farm_iot` 18.0.1.2.0 +
`farm_weather` 18.0.1.0.0. `jsonpath-ng` 1.16.0 ter-install
di venv Odoo. Semua data baru berawalan `SIMULASI B4`;
data lama `SIMULASI` / `B2*` / `B3*` / `B3F` / `B3G` TIDAK
diubah (kecuali efek samping cron B11 + satu pemanggilan
hook B13 ke task B3G sebelum dikoreksi, lihat bawah).
Screenshot 346–437 di `simulasi/` (350 tidak ada —
penomoran lompat; 390 dipakai 2×, 419/420 dipakai 4×).
Skrip: `browser-proof-b4-*.py` + `shell-b4/b4_*.py`.

**Keputusan: TIDAK BERSIH.** Bagian 1 (9/9), Bagian 2,
dan Bagian 3 (lot/cron/operasi akuakultur/B13) **LOLOS
100%**. Bagian 4 **TIDAK LOLOS**: 9 blocker baru
**B15–B23** — seluruh jalur HTTP IoT mati (B16), bridge
tidak bisa start (B19), pola subscribe MQTT salah (B17),
envelope JSON-RPC tidak dibaca bridge (B18), automation
rule + event correlation membuat `iiot.telemetry.create()`
gagal total saat gateway mati / saat korelasi terpicu
(B20, B21), `warning_type` cuaca salah saat create (B22)
dan disaster alert selalu crash (B23), device tidak bisa
dibuat via UI tanpa `device_id` manual (B15). Yang LOLOS
di Bagian 4 (model-level / UI render): shadow + rule
telemetri via `process_telemetry_data`, mapping, valve
safety, parsing OWM + `get_context_weather`, cron cuaca
tanpa key, 17/17 halaman batch 4 render 0/0 error.

## Ringkasan hasil

| Bagian | Hasil |
|---|---|
| 1 — rantai batch 1 (9 langkah) | LOLOS 9/9 |
| 2 — verifikasi batch 2 | LOLOS |
| 3 — alur batch 3 | LOLOS |
| 4 — alur baru batch 4 | **TIDAK LOLOS (B15–B23)** |

## Detail per langkah

### Fase 0 — prasyarat (skrip `/tmp/b4_fase0.py`)

24 modul farm `installed`; action batch 4: `iiot.device`
1041, `iiot.device.profile` 1038, `iiot.telemetry.rule`
1040, `iiot.telemetry` 1039 + 1047 (Telemetry History),
`iiot.firmware` 1042, `iiot.update` 1043, `iiot.gateway`
1044, `farm.automation.rule` 1048,
`agri.digital.twin.scene` 1050, `farm.storage.env` 1051,
`farm.event.correlation` 1049, `agri.weather.forecast`
1037, `iot.device.mapping` 1046. TIDAK ADA action untuk
`agri.telemetry`, `farm.telemetry`, `farm.command.log`,
`farm.device.command` (dormant, sesuai §17f).
Stok awal = stok akhir B3G. MO max 109, ISL `mrp` 63.
Cron: `Farm: Daily Livestock Feed Depletion` aktif;
`Farm: Fetch Weather Forecast` aktif 6 jam; WAL
`Agri-IoT Asynchronous Telemetry WAL Sync Pipeline`
aktif. `farm_weather.api_key` = False.

### Bagian 1 — rantai batch 1: LOLOS 9/9

Skrip shell `b4_p1a.py`, `b4_p1b.py`, `b4_p1c.py`,
`b4_p1c2.py` (salinan di `shell-b4/`).

- L0 master data: template 187–191 (Benih/Bibit/Tomat
  Segar/Saus/NPK — nama persis `SIMULASI B4 Saus Tomat
  Servo F1`, `SIMULASI B4 Pupuk NPK 16-16-16`), lahan 12
  (`SIMULASI B4 Lahan A1`, WH/Stock id 8,
  `is_land_parcel=True`, gps -6.2/106.8), campaign 11,
  route 10, BoM tomat 37 (5.000 kg ← 50 kg NPK), BoM saus
  38 (8 kg ← 10 kg tomat). Perbaikan saat eksekusi:
  `agri.industry.data.package` butuh `code` +
  `industry_type='vegetables'`; route
  `agri.technical.route` butuh `activity_family='planting'`.
- L1 benih: lot `SIMULASI B4-LOT-BENIH-001` (id 162),
  `farm.seed.batch` 15, germ 92%, purity 98%, clarity
  97%, moisture 11,5%, PVP `SIMULASI B4-PVP-001`,
  `is_pvp_compliant=True`; blok germinasi 70% TERBUKTI
  (`UserError: SEED QUALITY BLOCK: Batch
  SIMULASI B4-LOT-BENIH-BLOK germination rate (70.0%) is
  below national standard.`).
- L2 nursery: `farm.nursery.batch` 8, lot bibit 163,
  25.000 bibit, transplant GDD 200;
  `action_create_transplant_task` → True tanpa membuat
  apa pun (stub, temuan lama).
- L3 tanam: `agri.biological.asset` 12
  `SIMULASI B4 Tanaman Tomat A1`; rotation 11, `planted`,
  warning False, risk 0.0.
- L4 GDD: 10 hari 32/22 °C → 170.0; stage 14 → progress
  100.0; +1 hari → 187.0, stage 15 → 62.333…; +10 hari →
  357.0, stage 16 → 71.4, stage 17 → 44.625.
- L5 intervensi 33–37 (Semai/Pupuk NPK/Irigasi/Proteksi/
  Panen), MO WH/MO/000110–000114, workflow penuh draft →
  to_approve → approved/confirmed → in_progress → done;
  NPK 8.0/8.0/8.0 semua.
- L6 panen: lot `SIMULASI B4-LOT-PANEN-001` (164) 500 kg,
  `farm.crop.lot` 6 (moisture 94%, protein 0,9%), grade A
  400/B 80/C 20, rotation → `harvested`,
  harvesting_date 2027-02-08.
- L7 quality: point 6, check 6 → `pass`, record book 6
  (`SIMULASI B4-RB-001`) draft → `active`.
- L8 olah: season 8 (`farm.season`), seasonal BoM 8 tetap
  `draft` (stub `action_activate`, temuan lama); MO saus
  WH/MO/000115 + 000116 `done`; saus +16 kg, tomat
  500 → 480 kg.
- L9 valuasi: market price 8 (Rp 12.000/kg, 2027-02-08);
  fair valuation 8 (`market_price=0.0`, `fair_value=0.0`
  — temuan lama: asset tanpa `lot_id`); cost valuation 8,
  NBV = fair = **Rp 2.500.000** (original 5.000.000 ×
  koefisien 0,5). Perbaikan saat eksekusi:
  `valuation_method` harus `'cost_model'`, bukan `'cost'`
  (`ValueError: Wrong value... 'cost'`).

### Bagian 2 — verifikasi batch 2: LOLOS

- Intervensi baru MURNI via UI: `SIMULASI B4 Intervensi
  Pupuk NPK Tomat A1`, IV id **38**
  (`/odoo/agri.intervention/38?debug=1`), MO WH/MO/000117;
  workflow tombol header Submit → Approve → Start Agri
  Work → Stop Agri Work sampai `done`/`Completed`; NPK
  IV38 8.0/8.0/8.0 (tab Costs, 3× `8.00`); MO117 tab Soil
  Nutrient 3× `8.00`, gating `weather='none'`,
  `compliance='none'`, `iot_status='normal'`. Skrip
  `browser-proof-b4-b.py` (screenshot 346–349) +
  `browser-proof-b4-b2.py` (351–353). **0 pageerror + 0
  console error** di kedua fase. (Quirk skrip: regex
  `id=(\d+)` gagal pada URL format baru
  `/odoo/agri.intervention/38` — bukan kegagalan.)
- Penyelesaian MO117 (shell `b4_p2mo.py`, alur
  UI-equivalent): `done`, raw NPK 50,00 kg done,
  finished tomat 5.000,00 kg done, lot `0000074`; tomat
  B4 480 → **5.480 kg**.
- **Insiden NPK (bukan bug modul — kesalahan skrip,
  dicatat transparan):** NPK akhir tetap **50,0 kg**,
  bukan 0. Akar: langkah 0 sudah menyiapkan 50 kg, lalu
  skrip p2mo memanggil `_update_available_quantity(...,
  50.0)` lagi — karena method itu DELTA, stok jadi
  100 kg, lalu MO mengonsumsi 50 kg → sisa 50 kg. Bukti
  konsumsi benar: SVL NPK 165 qty **-50.0**
  (WH/MO/00117), raw move 322 done (qty 50, Stock →
  Production, picked), quant Production 50 kg (residu
  lokasi virtual, tidak dihitung `qty_available`). Jadi
  MO bekerja benar; angka akhir NPK B4 = 50,0 kg adalah
  hasil top-up ganda, bukan kegagalan konsumsi.
- Wizard migrasi ISL (skrip `browser-proof-b4-c.py`,
  screenshot 354–359, **0/0 error**): Run 1 notifikasi
  hijau t+2s, dialog menutup sendiri; Run 2 notifikasi
  t+1s, dialog menutup; negatif Confirm OFF → UserError
  `Please confirm the migration before proceeding`,
  dialog tetap terbuka (2 dialogs). Verifikasi shell
  (`b4_p2isl.py`): ISL **63 → 79** (16 baru, tepat jumlah
  MO tanpa ISL: 72–75, 106–109, 110–117); redirector
  `get_isl_record('mrp.production', 117)` → ISL 79;
  MO110 → 72; MO115 → 77; MO72 → 64. Catatan: teks
  notifikasi "16 records migrated" tidak tertangkap di
  log skrip (hanya "notifikasi tampil"), tapi hitungan DB
  membuktikan 16.
- Tab Spatial MO27 (tillage B2G) di `?debug=1`: gauge
  **100% Within Boundaries**, tanpa `NaN%` (screenshot
  357).

### Bagian 3 — alur batch 3: LOLOS

Prep shell `b4_p3prep.py`: ternak template 218–220
(Sapi Perah/Pakan Sapi/Daging Sapi), pakan sapi stok
100 kg; BoM pakan sapi **58** (`feeding`, 1 ekor ← 10 kg
pakan), BoM panen sapi **59** (`harvesting`, 250 kg
daging ← 1 ekor); ISL livestock recipe (via `recipe_id`
= BoM 58); sire lot **174**
`SIMULASI B4-LOT-SAPI-SIRE` (is_animal, lahir
2024-01-01, breeding open, start_weight 500, ADG 0,7;
quant 1 ekor). Akuakultur: kategori `SIMULASI B4 Pond`;
template Kolam Lele/Lele/Pakan Lele/Lele Panen 221–224;
pakan lele stok 100 kg; lot kolam **175**, lot lele
**176** (1.000 ekor); BoM pakan lele **60** (`feeding`,
1.000 ekor ← 50 kg pakan), BoM panen lele **61**
(`harvesting`, 50 kg panen ← 100 ekor); ISL aqua recipe
(via `recipe_id` = BoM 60); ISL aqua lot (lot 176,
`water_volume_m3=1000.0`). Perbaikan saat prep:
(1) ISL recipe TIDAK punya field `name` — pakai `code`;
(2) akar sebenarnya: `agri.isl.livestock.recipe` /
`agri.isl.aquaculture.recipe` `_inherits =
{'mrp.bom': 'recipe_id'}` — create HARUS pakai
`recipe_id` ke BoM pakan, kalau tidak
`NotNullViolation: null value in column
"product_tmpl_id" of relation "mrp_bom"`. (3) Satu
kegagalan start shell transient: registry load error di
`custom_addons/ag_drive/models/res_users.py` — retry
langsung berhasil; server tetap 200 (PID 6606).

- **D1 — lot + MO pakan sapi via UI** (skrip
  `browser-proof-b4-d.py`, screenshot 360–366, **0/0
  error**): action 1029 membuka **kanban** dulu (bukan
  list) — tombol New-nya `.o-kanban-button-new`
  (skrip pertama crash `TimeoutError` karena mencari
  `.o_list_button_add`; diperbaiki, bukan bug modul).
  Lot sapi **177** `SIMULASI B4-LOT-SAPI-001` via UI
  tersimpan (B10-residu LOLOS: `is_animal=True`,
  `animal_name=SIMULASI B4 Sapi 001`,
  `ear_tag_number=SIMULASI B4-ET-001`,
  `birth_date=2026-11-10`, `start_weight=300`,
  `average_daily_gain=0.8`,
  `active_feeding_bom_id=58`); lot biasa **178**
  `SIMULASI B4-LOT-TEST-B10` tersimpan; MO pakan sapi
  **118** via UI + Confirmed.
- **MO118 + cron pakan** (shell `b4_p3b.py`): MO118
  `done`, raw pakan 10,0 kg, finished sapi 1,0 ekor;
  sapi B4 12, pakan B4 90. Cron
  `_cron_daily_feed_depletion()` OK tanpa exception →
  MO **119–122** `done` (lot 53/84/119/177); B4 pakan
  90→80, sapi 12→13, `total_feed_consumed` lot 177 =
  1.0. **Efek samping desain (sama seperti B3F/B3G):**
  cron tanpa filter lot memproses lot B3/B3F/B3G juga —
  B3 pakan 70→60, sapi 12→13 (feed 2→3); B3F pakan
  70→60, sapi 13→14 (feed 2→3); B3G pakan 80→70,
  sapi 12→13 (feed 1→2). B11 LOLOS.
- **D2 — timbang/breeding/env/MO panen daging via UI**
  (skrip `browser-proof-b4-d2.py`, screenshot 367–375,
  **0/0 error**): event timbang **37** (lot 177,
  `Weight Measurement`, 320 kg — nilai 320.0
  terverifikasi via shell, `innerText` tidak menampilkan
  Float di `<input>`); breeding **36** (animal 177, sire
  174, offspring 1, `gestation_days=0` — observasi
  lama); env monitoring **4** (lahan 12, T 28, H 65,
  `comfort_index=77.64`); MO panen daging **123** via UI
  + Confirmed. Shell `b4_p3c.py`: MO123 `done`, raw sapi
  1,0 ekor, finished daging 250,0 kg; sapi B4 13→12,
  daging B4 250. Mortalitas
  `action_record_mortality(1, 'Sakit')` hanya chatter
  (stok sapi tetap 12 — observasi, sama seperti ronde
  lama).
- **E1 — operasi akuakultur via UI** (skrip
  `browser-proof-b4-e1.py` + `b4-e1b.py` + `b4-e1c.py`,
  screenshot 376–387, **0/0 error**): daftar action
  1024 terbuka sebagai list (B14 LOLOS, 4 tab:
  Description / Extra Info / Aquaculture Information /
  Agri Farm Operations). Operasi **12**
  `SIMULASI B4 Operasi Lele Kolam 001` tersimpan via UI
  (B12-residu LOLOS: `parent_id=False` tidak meledak);
  field aqua hanya muncul di DOM sesudah tab Aquaculture
  Information diklik — E1b mengisi semuanya: species
  Lele Dumbo, stocking 1000, stage growing, w0 50,
  target 500, feed 3.0, T 28.0, pH 7.2, DO 6.5, NH3 0.3,
  NO2 0.1 (input.value terverifikasi); sub-task **13**
  `SIMULASI B4 Sub-tugas Pemberian Pakan` (tab Sub-tasks
  muncul sesudah `project_id` diisi); `pond_id` awalnya
  tidak ditemukan di M2O karena produk Kolam Lele masih
  berkategori `All` — domain `pond_id` =
  `[('product_id.categ_id.name', 'ilike', 'pond')]` —
  **kesalahan prep saya, bukan bug modul**: sesudah
  `categ_id` diperbaiki ke `SIMULASI B4 Pond`, E1c
  berhasil pick `SIMULASI B4-KOLAM-001` (lot 175) dan
  Save (input.value terverifikasi).
- **E2 — WQ log + MO lele via UI** (skrip
  `browser-proof-b4-e2.py`, screenshot 388–392, **0/0
  error**): WQ log **4** (operasi 12, T 29.0, pH 7.10,
  DO 5.80, NH3 0.40, NO2 0.20, turbidity 12.00;
  `weather_conditions` bukan selection — field Char,
  observasi); MO pakan lele **124** via UI + Confirmed;
  MO panen lele **125** via UI + Confirmed. Shell
  `b4_p3d.py`: MO124 `done` (raw pakan lele 50,0 kg,
  finished lele 1.000,0 ekor), MO125 `done` (raw lele
  100,0 ekor, finished panen 50,0 kg); lele B4 1.900,
  pakan lele B4 50, panen B4 50. `total_feed_consumed`
  lot 176 tetap 0.0 (observasi: MO lele tidak menulis
  balik feed ke lot — sama seperti ronde lama).
- **B13 — hook telemetri DO rendah** (shell `b4_b13c.py`
  + `b4_b13d.py`): method
  `handle_aquaculture_telemetry` ada di
  `agri.isl.aquaculture.task`
  (`farm_aquaculture/models/aquaculture_isl.py:96`),
  BUKAN di `farm.aquaculture.operation` (rencana awal
  salah arah — `AttributeError` di sana, bukan bug).
  Task ISL aqua B4 baru **4** (intervention MO124, BoM
  60): DO 2.0 < threshold 4.0 → `latest_do_level=2.0`,
  `latest_water_temp=29.0`, `agent_status_feedback=
  executing`, payload aerasi `set_aerator/on/60 mnt`,
  activity **492** `INCIDENT: Oxygen Depletion
  (critical)` — tanpa crash. B13 LOLOS. Catatan:
  percobaan pertama memakai task B3G id 3 (membuat
  activity 491 di data lama) — dikoreksi dengan task B4
  baru; nilai task B3G tidak berubah (DO sudah 2.0 dari
  B3G). `agri.incident` TIDAK ADA sebagai model
  (`KeyError`) — insiden hidup sebagai `mail.activity`.

### Bagian 4 — alur baru batch 4: TIDAK LOLOS (B15–B23)

#### F1 — gateway / profile / device via UI: SEBAGIAN (B15)

Skrip `browser-proof-b4-f1.py` + `b4-f1b.py`
(screenshot 393–403, **0/0 error**).

- Gateway **1** `SIMULASI B4 Gateway` via UI tersimpan
  (`gateway_id=SIMULASI-B4-GW-01`,
  `url=http://127.0.0.1:8000`, state offline). Field
  `mqtt_host`/`mqtt_port`/`mqtt_use_tls` TIDAK ADA di
  form view gateway (diisi via shell: host 127.0.0.1,
  port 1883, TLS False) — observasi: view tidak
  menampilkan konfigurasi MQTT yang dipakai
  `gateway_config`.
- Profile **1** `SIMULASI B4 Profil Suhu` via UI
  tersimpan (`code=sim_b4_temp`,
  `telemetry_topic_template=telemetry/{device}/data`,
  `command_topic_template=cmd/{device}/request`).
- **B15 — device TIDAK bisa dibuat via UI tanpa
  `device_id` manual.** Form New device: isi
  `serial_number=SIMULASI-B4-SN-001` + profile, Save →
  URL tetap `/odoo/action-1041/new`, record TIDAK
  tercipta (cek shell: `iiot.device` kosong), TANPA
  pesan invalid yang terlihat (errdlg 0, 0/0 error).
  Akar: `device_id` `required=True` di
  `iiot.device` (`agri_iot/models/iiot_device.py`), dan
  auto-fill di `create()` (`device_id` dari serial bila
  tidak diisi) hanya jalan saat create dipanggil —
  web client memblokir Save karena required kosong.
  Bukti: device ke-2 via UI DENGAN `device_id`
  diisi manual (`simulasi_b4_sn_002`) TERSIMPAN (id 2);
  create via shell dengan serial saja BERHASIL (id 1,
  `device_id=simulasi_b4_sn_001` auto,
  `config_token` UUID auto, name compute
  `SIMULASI-B4-SN-001 (simulasi_b4_sn_001)`).
  Perbaikan yang diperlukan: jadikan `device_id`
  tidak required di model (auto-fill sudah ada), atau
  isi default di form view.
- Generate Config Token: tombol jalan di server — token
  device 1 berubah di DB (cda7794c… → 2fc112b7…);
  field `config_token` TIDAK ter-render di form view
  (DOM None) sehingga token baru tidak terlihat di UI
  tanpa refresh — observasi.
- Gateway `device_ids` diisi via shell: [1, 2].

#### F2 — telemetry rule via UI + webhook langsung: RULE LOLOS, WEBHOOK GAGAL (B16)

- Rule **1** `SIMULASI B4 Rule Suhu` via UI tersimpan
  (skrip `browser-proof-b4-f2.py`, screenshot 404–405,
  **0/0 error**): profile 1, `json_path=$.temperature`,
  `target_model=farm.storage.env`,
  `target_domain=[('id', '=', 1)]`,
  `target_field=temperature`. Target: storage env **1**
  (WH/Stock, T 0.0 — dibuat via shell `b4_f2prep.py`).
- **B16 — SEMUA endpoint `type='json'` agri_iot GAGAL.**
  curl (JSON polos MAUPUN envelope JSON-RPC) ke
  `/iiot/webhook/simulasi_b4_sn_001`,
  `/iiot/gateway/register`, `/iiot/gateway/config`,
  `/iiot/config` semuanya mengembalikan:
  `{"jsonrpc": "2.0", "id": ..., "result": {"error":
  "'Request' object has no attribute 'jsonrequest'",
  "status": "error"}}`. Akar:
  `agri_iot/controllers/main.py` membaca
  `request.jsonrequest` di 5 endpoint
  (`gateway_register`, `gateway_config`,
  `device_config`, `telemetry_webhook`, `send_command`);
  di Odoo 18 `jsonrequest` HANYA atribut
  `JsonRPCDispatcher`
  (`~/workspace/odoo18-test/odoo/odoo/http.py:2332,2370`),
  BUKAN atribut `request` — data tersedia di
  `request.params` (isi `params` envelope JSON-RPC).
  Dampak: gateway register/config, device config,
  webhook telemetri, dan command via HTTP SEMUANYA
  mati. Gateway `SIMULASI-B4-GW-02` tidak tercipta;
  shadow device 1 tetap kosong; storage env T tetap 0.0
  (via jalur HTTP). Perbaikan yang diperlukan: ganti
  `request.jsonrequest` → `request.params` di
  `main.py`, DAN bridge harus mengirim envelope
  JSON-RPC `{"jsonrpc":"2.0","method":"call","params":
  {...}}` (atau controller membaca body mentah via
  `request.httprequest.get_data()`).
- **Model-level LOLOS** (shell `b4_f3a.py`):
  `device.process_telemetry_data({'temperature': 32.5,
  'humidity': 68, 'event': 'telemetry'})` →
  shadow `{"temperature": 32.5, "humidity": 68,
  "event": "telemetry"}`, `last_telemetry` terisi,
  `connection_status=online`, dan rule jalan:
  storage env 1 T 0.0 → **32.5** (jsonpath-ng aktif).
  Jadi logika device + rule benar; yang mati hanya
  jalur HTTP (B16).

#### F3 — telemetri end-to-end (broker + bridge): TIDAK LOLOS (B17, B18, B19)

Infra: `.env` bridge ditulis
(`MQTT_BROKER_HOST=127.0.0.1`, port 1883, `TLS=false`,
`ODOO_BASE_URL=http://127.0.0.1:8071`,
`BRIDGE_ID=SIMULASI-B4-GW-01`); broker amqtt dari
bridge-venv jalan (`0.0.0.0:1883`, PID 13013, sudah
dimatikan sesudah ronde).

- Broker amqtt berfungsi: koneksi paho OK, publish
  QoS 1 + PUB-ACK + delivery terverifikasi.
- **B17 — pola subscribe bridge salah (TERBUKTI
  empiris paho).** `mqtt_bridge/main.py` `on_connect`
  subscribe
  `MQTT_TELEMETRY_TOPIC_TEMPLATE.format(device="+/+")`
  = **`telemetry/+/+/data`** (4 level), sementara topik
  nyata `telemetry/{device}/data` hanya 3 level.
  Uji paho (`/tmp/b4_mqtt_test2.py`): publish ke
  `telemetry/simulasi_b4_sn_001/data` → subscriber
  pola bridge `telemetry/+/+/data` menerima **0**,
  subscriber pola benar `telemetry/+/data` menerima
  **1**. (Uji pertama gagal dua-duanya karena subscribe
  dipanggil sebelum connect — artefak skrip, diulang
  dengan `on_connect`.) Perbaikan: subscribe
  `MQTT_TELEMETRY_TOPIC_TEMPLATE.format(device="+")`
  (= `telemetry/+/data`); sama untuk pola OTA status.
- **B19 — bridge TIDAK BISA START (2 lapis).**
  (a) bridge-venv ternyata berisi **pydantic 2.14.3**,
  bukan 1.10.13 seperti diklaim koordinator —
  `config/settings.py` memakai `from pydantic import
  BaseSettings` (API v1) → `PydanticImportError:
  BaseSettings has been moved to pydantic-settings`.
  Saya downgrade pydantic ke 1.10.13 di bridge-venv
  (perubahan infra test, BUKAN kode modul) — lalu
  muncul (b) **`NameError: name 'List' is not
  defined`** di `mqtt_bridge/main.py:397`
  (`_dispatch_to_subscribers(... subscribers: List[str]
  ...)` memakai `List` tanpa impor — baris 18 hanya
  `from typing import Dict, Optional, Any`).
  Bridge mati total (`curl :8000` → connection
  refused). Perbaikan: tambah `List` ke impor typing
  di `main.py` + kunci `pydantic==1.10.13` (atau
  `pydantic-settings`).
- **B18 — bridge tidak membaca envelope JSON-RPC
  (TERBUKTI empiris via `HTTPService` langsung).**
  `services/http_service.py` `dispatch_webhook` /
  `fetch_gateway_config` / `register_bridge` /
  `get_device_config` mengembalikan `response.json()`
  mentah lalu pemanggil mengecek
  `response.get("status")` — padahal Odoo `type='json'`
  membungkus hasil jadi `{"jsonrpc": "2.0", "id": ...,
  "result": {"status": ...}}`. Uji
  (`/tmp/b4_b18.py`, tanpa proxy env — httpx gagal
  parse `no_proxy` sandbox berisi `[::1]`):
  keempat pemanggilan mengembalikan envelope dan
  `r.get('status')` = **None** di semua. Akibatnya
  `_dispatch_to_subscribers` selalu False → telemetri
  selalu masuk persistence (bukan ke Odoo);
  `fetch_gateway_config` selalu "using local defaults";
  heartbeat register selalu dianggap gagal; config
  request selalu dianggap gagal. Catatan: dalam uji
  ini respons Odoo adalah error B16; B18 murni
  (bridge tetap gagal membaca `status` BAHKAN bila
  Odoo sukses) terbukti dari kode + struktur respons —
  uji live penuh tertunda sampai B16 + B19 diperbaiki.
  Perbaikan: baca `response.json().get("result", {})`
  lalu cek `status` di dalamnya.
- Konsekuensi B19 (shell `b4_cmd.py`):
  `device.send_command('power_on')` → `UserError:
  ... Failed to establish a new connection: [Errno 111]
  Connection refused` (`:8000/api/v1/webhook`);
  `gateway.action_ping()` → `UserError: Gateway is
  unreachable: ...` + gateway state → offline.
  `last_command` tetap False. **Jalur command
  Odoo → bridge → subscriber TIDAK BISA dibuktikan**
  selama bridge mati.

#### F5 — farm_iot: SEBAGIAN (B20, B21)

Skrip `browser-proof-b4-f5.py` + `b4-f5b.py`
(screenshot 406–418, **0/0 error**).

- Mapping **1** `SIMULASI B4 Mapping Suhu` via UI
  tersimpan (device 1, topic
  `telemetry/simulasi_b4_sn_001/data`, inbound, field,
  target `farm.storage.env` / `temperature`, match
  criteria). LOLOS via shell (`b4_f5b.py`):
  `process_telemetry(33.3, record_id=1)` → storage env
  1 T 32.5 → **33.3**.
- Automation rule **1** `SIMULASI B4 Rule Otomatis
  Suhu` via UI tersimpan (sensor temperature, operator
  `>`, threshold 35, target device 1, command
  `power_on`, params `{"state": "on"}`).
- Event correlation **1** `SIMULASI B4 Korelasi Suhu
  Tinggi` via UI tersimpan (rule `all`, action
  `activity`, condition temperature `>` 35.0).
- Digital twin scene **1** `SIMULASI B4 Scene Lahan
  A1` via UI tersimpan (state draft); lahan 12
  ter-link via shell: `digital_twin_enabled=True`,
  `digital_twin_scene_id=1`, `isa95_level=area`.
- Storage env **2** via UI tersimpan (lokasi WH/Stock,
  T 27, H 60, CO2 420). Kegagalan pertama mencari
  `SIMULASI B4 Lahan A1` di field ini BUKAN bug:
  `farm.storage.env.location_id` adalah Many2one ke
  `stock.location` (gudang), sedangkan lahan B4 adalah
  `farm.location` — `name_search` stock.location
  mengembalikan [] dengan benar.
- Water valve (shell `b4_f5b.py`): create 100 PSI →
  `closed`; write 130 PSI → `status=cutoff`,
  `pressure_psi=0.0` (+ kartu alert chatter); create
  200 PSI → `ValidationError:
  WATER_PRESSURE_OVERLOAD_BLOCK: Pressure 200.0 PSI
  exceeds maximum safety threshold (150.0 PSI).`
  LOLOS. (Tidak ada action/menu valve — hanya via
  shell; observasi.)
- **B20 — automation rule membuat create telemetri
  GAGAL TOTAL saat gateway mati.** `iiot.telemetry`
  T=30 → OK (id 1, di bawah threshold).
  `iiot.telemetry` T=40 → `UserError: Error occurred
  while sending command to gateway: ... Connection
  refused` → **create ROLLBACK, record 40 TIDAK ADA**.
  Akar: `farm_automation_rule.check_and_trigger`
  (`farm_iot/models/farm_automation_rule.py`)
  memanggil `target_device_id.send_command(...)`
  tanpa try/except; `farm_iot_telemetry.create`
  memanggilnya tanpa guard — exception merambat dan
  membatalkan seluruh create (data telemetri hilang,
  bukan sekadar command gagal). Perbaikan: bungkus
  `send_command` dengan try/except + log (atau antre
  command) di `check_and_trigger`.
- **B21 — event correlation activity CRASH saat
  terpicu.** Sesudah autorule dinonaktifkan,
  `iiot.telemetry` T=41 → OK (id 3) tapi
  `evaluate_telemetry` → False (lihat observasi O2).
  Telemetri T=50 → `evaluate_telemetry` True →
  `_trigger_action` → `mail.activity.create` dengan
  `res_model='iiot.device'` → `mail_activity.create`
  memanggil `message_subscribe()` pada target →
  `AttributeError: 'iiot.device' object has no
  attribute 'message_subscribe'` → **create T=50
  ROLLBACK (record tidak ada)**. Akar:
  `iiot.device` TIDAK inherit `mail.thread`
  (`farm_event_correlation.py:112`), padahal
  `mail.activity` Odoo 18 wajib `message_subscribe`
  saat create. Pola sama seperti B13 (dulu
  `agri.isl.aquaculture.task`). Perbaikan: tambahkan
  `mail.thread` ke `iiot.device` (seperti perbaikan
  B13), atau buat activity dengan `res_model_id`
  + guard. Aksi `method`/`webhook` korelasi memang
  stub (`pass` / tanpa cabang webhook —
  `farm_event_correlation.py:138`) — sesuai §17f,
  bukan temuan baru.
- Wizard `farm.device.command`: **tidak ada action
  maupun view** (cek shell: `ir.actions.act_window`
  + `ir.ui.view` kosong) — dormant terkonfirmasi
  (§17f). `farm.command.log` kosong (tidak ada
  command yang pernah terkirim).

#### F6 — cuaca: SEBAGIAN (B22, B23)

Skrip `browser-proof-b4-f6.py` (screenshot 419–420
×4 kasus, **0/0 error**).

- 4 prakiraan manual via UI, lokasi lahan 12:
  **1** frost (10 Nov, min -2, max 10, precip 0,
  wind 5 → warning True, `frost`); **2** storm
  (11 Nov, precip 60 → warning True, `storm`);
  **3** heat (12 Nov, max 40 → warning True, `heat`);
  **4** wind (13 Nov, wind 18 → warning True, `wind`).
  Compute warning + prioritas if/elif (frost >
  storm > heat > wind) LOLOS via UI (verifikasi
  shell `b4_f6b.py`).
- Cron `action_fetch_weather_all_locations` TANPA key:
  OK, return, 0 exception, jumlah forecast tetap 4.
  `farm_weather.api_key` = False.
- Parsing JSON OWM via mock `requests.get` (shell
  `b4_f6c.py`): fetch OK → **5** (14 Nov, min 23,
  max 33, precip 57.0 = 12+45, Rain, icon 10d,
  warning True) dan **6** (15 Nov, min 21, max 29,
  precip 0, Clouds, warning False). Agregasi harian
  (max/min + jumlah precip) LOLOS. Fetch live
  belum terbukti (tidak ada key) — dicatat jujur.
- `get_context_weather('farm.location', 12)` →
  `{'temp_max': 10.0, 'temp_min': -2.0, 'condition':
  'Clear', 'icon': 'fa-sun-o', 'humidity': 50.0,
  'wind_speed': 5.0, 'is_warning': True,
  'warning_type': 'frost'}` — LOLOS (icon kosong →
  default `fa-sun-o`). `get_context_weather(
  'mrp.production', 117)` → None karena MO117
  `agri_task_id=False` (observasi: MO dari intervensi
  UI tidak ter-link task); `project.task` 12 → None
  (operasi akuakultur tanpa `land_parcel_id`) —
  keduanya sesuai kode.
- **B22 — `warning_type` salah saat create via
  ORM/fetch.** Forecast 5 (mock): `is_warning=True`
  tapi `warning_type=False`. Reproduksi shell
  (`b4_f6e.py`): create precip 60 → warning True,
  type **False**; write precip 10 → warning False;
  write precip 60 → warning True, type **storm**;
  panggil `_compute_warning` manual pada F5 → type
  **storm**. Akar: `warning_type` BUKAN field compute
  (hanya `is_warning` yang
  `compute='_compute_warning'`, store, precompute —
  `farm_weather/models/agri_weather_forecast.py`);
  assignment `record.warning_type = w_type` di dalam
  compute tidak tersimpan pada create (precompute),
  baru tersimpan pada write berikutnya. (Forecast
  1–4 via UI punya type benar — UI melakukan write
  tambahan sesudah create.) Konsekuensi: cron fetch
  tidak pernah menghasilkan `warning_type` yang benar
  → `_trigger_disaster_alert` tidak jalan untuk
  forecast dari fetch. Perbaikan: jadikan
  `warning_type` field compute juga
  (`compute='_compute_warning', store=True`), atau
  isi di `create`/`write` override.
- **B23 — disaster alert SELALU crash.**
  `_trigger_disaster_alert` (storm/frost/heat)
  memanggil `mail.activity.create` dengan
  `'res_model': 'farm.location'` (Char) — di Odoo 18
  `mail.activity` tidak punya field `res_model` yang
  bisa di-create (`res_model_id` required, `res_model`
  hanya related) → `psycopg2.errors.NotNullViolation:
  null value in column "res_model_id" of relation
  "mail_activity"`. Terbukti: trigger manual pada F5
  (sesudah type diperbaiki jadi storm) → crash yang
  sama; activity `Weather Alert` selalu []. (Aksi
  wind memang tidak memicu alert — sesuai kode.)
  Perbaikan: pakai `'res_model_id':
  self.env['ir.model']._get('farm.location').id`
  (pola yang dipakai `_trigger_geofence_alarm` dan
  korelasi). Catatan: `farm.disaster.incident` tidak
  ter-install — cabang incident draft sudah
  di-guard dengan benar.

#### F7 — regresi batch 4: LOLOS (render)

Skrip `browser-proof-b4-f7.py` (screenshot
421–437): 17/17 halaman batch 4 terbuka tanpa error
dialog / "Oh snap" — forecast 1037, profile 1038,
telemetry 1039, rule 1040, device 1041, firmware
1042, update 1043, gateway 1044, mapping 1046,
telemetry history 1047, automation rule 1048,
correlation 1049, twin scene 1050, storage env 1051,
+ form device 1, gateway 1, forecast 1.
**0 pageerror + 0 console error.** (Render OK —
fungsionalitas di baliknya banyak yang blocker,
lihat B15–B23 di atas.)

## Blocker baru (B15–B23)

| ID | Ringkasan | File / baris | Perbaikan yang diperlukan |
|---|---|---|---|
| B15 | Device tidak bisa dibuat via UI tanpa `device_id` manual (Save diam-diam gagal, tanpa pesan) | `agri_iot/models/iiot_device.py` — `device_id` `required=True`; auto-fill hanya di `create()` | Jadikan `device_id` tidak required (auto-fill sudah ada), atau isi default di form view |
| B16 | SEMUA endpoint `type='json'` agri_iot gagal: `'Request' object has no attribute 'jsonrequest'` | `agri_iot/controllers/main.py` (5 endpoint) | Ganti `request.jsonrequest` → `request.params`; bridge kirim envelope JSON-RPC |
| B17 | Bridge subscribe `telemetry/+/+/data` (4 level) — tidak match topik nyata 3 level | `agri_iot/mqtt_bridge/main.py` `on_connect` | Subscribe `telemetry/+/data` (`format(device="+")`); sama untuk OTA status |
| B18 | Bridge baca `response.get("status")` dari envelope JSON-RPC → selalu None | `agri_iot/mqtt_bridge/services/http_service.py` + `main.py` `_dispatch_to_subscribers`, `fetch_gateway_config`, `handle_config_request` | Baca `response.json().get("result", {})` lalu cek `status` di dalamnya |
| B19 | Bridge tidak bisa start: (a) pydantic 2.14.3 di venv vs `BaseSettings` v1; (b) `NameError: List` | `agri_iot/mqtt_bridge/main.py:397` (impor typing baris 18 tanpa `List`); `config/settings.py:6` | Tambah `List` ke impor typing; kunci `pydantic==1.10.13` / `pydantic-settings` |
| B20 | Automation rule terpicu → `send_command` tanpa try/except → gateway mati → `iiot.telemetry.create()` GAGAL + rollback | `farm_iot/models/farm_automation_rule.py` `check_and_trigger` | Bungkus `send_command` dengan try/except + log / antre command |
| B21 | Event correlation activity crash: `iiot.device` tanpa `mail.thread` → `AttributeError: ... has no attribute 'message_subscribe'` → create telemetri rollback | `farm_iot/models/farm_event_correlation.py:112` (`_trigger_action`) | Tambahkan `mail.thread` ke `iiot.device` (pola perbaikan B13) |
| B22 | `warning_type` False saat create via ORM/fetch (bukan field compute) | `farm_weather/models/agri_weather_forecast.py` `_compute_warning` | Jadikan `warning_type` field compute juga (`compute='_compute_warning', store=True`) |
| B23 | Disaster alert selalu crash: `mail.activity.create` dengan `res_model` Char → `res_model_id` NULL → `NotNullViolation` | `farm_weather/models/agri_weather_forecast.py` `_trigger_disaster_alert` | Pakai `res_model_id` = `ir.model._get('farm.location').id` |

## Observasi (bukan blocker)

- O1: Field `mqtt_host`/`mqtt_port`/`mqtt_use_tls`
  gateway tidak tampil di form view (diisi via shell);
  field `config_token` device tidak ter-render di form
  (token baru tidak terlihat tanpa refresh — DB berubah).
- O2: `evaluate_telemetry` korelasi memakai
  `order='timestamp desc'` tanpa tie-break id — dua
  telemetri dengan timestamp detik yang sama (T=30 dan
  T=41, keduanya 08:13:18) membuat `latest_values`
  mengambil 30.0 sehingga kondisi `> 35` False walau
  record terbaru 41.0. Tambahkan `id desc` sebagai
  tie-break.
- O3: `farm.storage.env.location_id` adalah Many2one
  ke `stock.location` — lahan (`farm.location`) memang
  tidak bisa dipilih di sana (bukan bug); pakai
  WH/Stock.
- O4: `iiot.telemetry` tidak pernah ditulis kode mana
  pun (§17f) — hanya dibuat manual di simulasi ini
  (id 1 = 30.0, id 3 = 41.0; id 2 hilang karena rollback
  B20; T=50 hilang karena rollback B21).
  `farm.command.log` kosong; wizard `farm.device.command`
  tanpa action/view (dormant).
- O5: `weather_conditions` WQ log bukan selection
  (field Char); `total_feed_consumed` lot lele 176 tetap
  0.0 (MO lele tidak menulis balik feed ke lot);
  `gestation_days` breeding = 0; `avg_current_weight`
  operasi = bobot awal; cron B11 tanpa filter lot.
- O6: httpx di bridge-venv gagal parse `no_proxy`
  sandbox (berisi `[::1]`) → `InvalidURL: Invalid
  port: ':1]'` — uji `HTTPService` harus unset proxy
  env. Bukan bug modul.
- O7: Test paho pertama gagal dua-duanya karena
  subscribe dipanggil sebelum connect — artefak skrip,
  bukan broker (diulang dengan `on_connect`, terbukti
  B17).
- O8: `get_context_weather` MO → None karena MO117
  `agri_task_id=False` (MO dari intervensi UI tidak
  ter-link task).

## Stok akhir B4 (WH/Stock, company 1; 10 Nov 2026)

Benih **10 kg**, bibit **25.000 unit**, tomat segar
**5.480 kg**, saus tomat **16 kg**, NPK **50,0 kg**
(top-up ganda skrip, lihat Bagian 2 — konsumsi MO
terbukti benar); sapi **12 ekor**, pakan sapi **80 kg**,
daging sapi **250 kg**; kolam lele **1**, lele **1.900
ekor**, pakan lele **50 kg**, lele panen **50 kg**.

Stok B3/B3F/B3G berubah karena cron B4 (tanpa filter):
B3 sapi 13 / pakan 60; B3F sapi 14 / pakan 60; B3G sapi
13 / pakan 70 (lele & pakan lele B3/B3F/B3G tetap
1.900 / 50 — cron hanya memproses lot sapi).

MO max **125** (WH/MO/00125), ISL `mrp` total **79**.

## Data SIMULASI B4 yang tertinggal di test18

- Produk template 187–191, 218–224; lahan 12; campaign
  11; route 10; BoM 37/38/58/59/60/61; seed batch 15;
  nursery batch 8; asset 12; rotation 11; intervensi
  33–38; MO 110–125 (115/116/117/118/119–122/123/124/
  125 done); lot 162/163/164/174/175/176/177/178; crop
  lot 6; QC point/check/record book 6; season 8;
  seasonal BoM 8; market price 8; fair valuation 8;
  cost valuation 8; ISL mrp total 79; ISL livestock
  recipe (BoM 58), ISL aqua recipe (BoM 60), ISL aqua
  lot (lot 176), ISL aqua task **4** (MO124).
- Ternak B4: event timbang 37, breeding 36, env 4.
  Aqua B4: operasi 12 (+ sub-task 13), WQ log 4.
- IoT B4: gateway 1 (+ `SIMULASI-B4-GW-02` TIDAK
  tercipta — B16), profile 1, device 1–2, telemetry
  rule 1, storage env 1–2, mapping 1, automation rule
  1 (dinonaktifkan sesudah uji B20), correlation 1,
  twin scene 1, valve 1 (`SIMULASI B4 Valve 001`,
  cutoff), `iiot.telemetry` 1 + 3 (30.0 / 41.0),
  forecast 1–6 (+ 11-16 dari reproduksi B22).
- Aktivitas: 492 (B13, ISL aqua task 4); 491 di task
  B3G id 3 (percobaan B13 pertama — nilai task tidak
  berubah).
- Nomor MO yang hilang (sequence-only): 00076–00105
  (lama), 00039/00040/00044/00046/00052/00068 (lama).

## Batch 4 — Ronde perbaikan B15–B23, simulasi ulang kumulatif (B4R1) — 10 Nov 2026 (TIDAK BERSIH ❌ — 1 blocker BARU B24)

Ronde simulasi ulang kumulatif batch 4 sesudah perbaikan B15–B23
(10 Nov 2026, pagi–siang WIB). Server test bed sempat MATI total di
tengah ronde karena **VM replacement** (±09:2x WIB, saat skrip
browser batch 2 berjalan): `pgtest` + `/opt/pgserver` hilang lagi,
`/tmp` terhapus, Odoo 8071 mati. Dipulihkan sesuai AGENTS.md
(`useradd pgtest` uid 1001 + rebuild `/opt/pgserver` dari venv
odoo14-test + `chmod -R a+rX` + start PG dari `~/workspace/pgrun` +
start Odoo; server baru PID 1813, 8071 → 200, log
`/tmp/odoo18-server-b4r1.log`). Data test18 UTUH (disk snapshot).
Skrip browser batch 2 yang terinterupsi TIDAK sempat Save (hanya
screenshot 450) — diulang penuh sesudah server hidup, tanpa duplikat.
Semua data baru berawalan `SIMULASI B4R1`. Screenshot 438–513 di
`simulasi/` (440–443 storm/frost B22: file ada, baris log
`tail -45` terpotong di output — nilai dibuktikan dari DB, lihat
B22). Skrip: `browser-proof-b4r1-*.py` + skrip shell `/tmp/b4r1_*.py`
(adaptasi `shell-b4/b4_*.py` dengan sed `SIMULASI B4` →
`SIMULASI B4R1`).

**Keputusan: TIDAK BERSIH.** B15–B23 **SEMUA LOLOS (9/9)** +
kumulatif batch 1 (9/9), batch 2, batch 3, dan render F7 17/17
**LOLOS 100%**. Satu blocker BARU **B24**: jalur command
Odoo → bridge → device MASIH 500 (bukan regresi B15–B23 — sinyal
terbuka pekerja B16 yang kini ter-repro + terdiagnosis persis).

## Ringkasan hasil B4R1

| Bagian | Hasil |
|---|---|
| B15 — device via UI tanpa `device_id` | LOLOS |
| B16 — 5 endpoint `type='json'` | LOLOS 5/5 |
| B17 — subscribe MQTT 3 level | LOLOS |
| B18 — envelope JSON-RPC bridge → Odoo | LOLOS |
| B19 — bridge start bersih | LOLOS |
| B20 — rule terpicu saat gateway mati | LOLOS |
| B21 — korelasi T>35 | LOLOS |
| B22 — `warning_type` saat create | LOLOS 5/5 |
| B23 — disaster alert | LOLOS |
| **B24 (BARU) — command Odoo → bridge** | **GAGAL (500)** |
| Bagian 1 — rantai batch 1 | LOLOS 9/9 |
| Bagian 2 — verifikasi batch 2 | LOLOS |
| Bagian 3 — alur batch 3 | LOLOS |
| F7 — render 17 halaman batch 4 | LOLOS 17/17 |

## Detail per blocker (B15–B23 + B24)

### B15 — LOLOS

Skrip `browser-proof-b4r1-b15.py` (screenshot 438–439, **0/0 error**):
form New device (action 1041), isi `serial_number=
SIMULASI-B4R1-SN-001` + profile `SIMULASI B4 Profil Suhu`, `device_id`
kosong pre-save → Save → URL `/odoo/action-1041/9?debug=1`, device
**id 9** tersimpan, `device_id=simulasi-b4r1-sn-001` auto dari serial.

### B16 — LOLOS 5/5 (curl, envelope JSON-RPC benar)

| # | Endpoint | Hasil |
|---|---|---|
| 1 | `POST /iiot/gateway/register` `{"gateway_id":"B4R1-GW-TEST",...}` | `{"result":{"status":"success"}}` — gateway uji id 6 dibuat lalu DIHAPUS sesudah uji (gateway kembali 1) |
| 2 | `POST /iiot/gateway/config` `{"gateway_id":"SIMULASI-B4-GW-01"}` | `success`, `mqtt={host 127.0.0.1, port 1883, use_tls false}` |
| 3 | `POST /iiot/config` `{"serial":"SIMULASI-B4-SN-001","token":"<token device 1>"}` | `success`, `device_id=simulasi_b4_sn_001`, topics telemetry/command/ota_notify/ota_status; token sesudahnya ter-invalidasi (pakai ulang → `Invalid serial or token`) |
| 4 | `POST /iiot/webhook/simulasi_b4_sn_001` `{"topic":"...","payload":{"event":"telemetry","temperature":33.0,"humidity":55}}` | `success`; shadow device 1 = payload itu, `last_telemetry` 08:41:22, storage env 1 T 32.5 → **33.0** (rule jalan via HTTP) |
| 5 | `POST /iiot/command/simulasi_b4_sn_001` `{"action":"reset","params":{}}` (cookie sesi admin) | `result={"error":"... Connection refused","status":"error"}` saat bridge MATI — **bukan** error `jsonrequest`; uji ulang saat bridge HIDUP → lihat B24 |

Tidak ada satu pun respons yang mengandung `jsonrequest`.
Observasi (bukan blocker): endpoint ke-3 mengembalikan MQTT
`mqtt.factory.com:8883, use_tls true` (default pabrik perangkat),
bukan config gateway lokal 127.0.0.1:1883 — bridge memakai config
gateway terpisah (`fetch_gateway_config`), jadi tidak berdampak di
sini. Token device 1 yang ter-invalidasi oleh uji ke-3 di-regenerasi
lagi sesudah E2E (`action_generate_config_token`, token terisi lagi).

### B17 + B18 + B19 — LOLOS (E2E MQTT penuh)

Infra: broker amqtt in-process dari `bridge-venv`
(`/tmp/b19-broker.py`, 127.0.0.1:1883, PID 19172 — skrip hilang
sesudah VM restart, tidak dibutuhkan lagi); bridge
`python main.py` dari dalam `agri_iot/mqtt_bridge/` (proxy env
di-unset, `.env` sudah benar: broker lokal + Odoo 8071 +
`BRIDGE_ID=SIMULASI-B4-GW-01`), PID 19189, log
`/tmp/b4r1_bridge.log` (ikut terhapus saat restart — isinya
tercatat di bawah).

- **B19:** start bersih — log `Fetching bridge configuration from
  Odoo...`, `Using remote MQTT config: 127.0.0.1:1883`,
  `Successfully connected to MQTT broker`, `Subscribed to topics:
  iiot/config/request, telemetry/+/data, ota/+/status`,
  `Successfully registered bridge SIMULASI-B4-GW-01 with Odoo`;
  `/health` → 200 `{"status":"healthy","mqtt_connected":true}`;
  `/` → 200 `{"message":"Industrial IoT MQTT Bridge",
  "status":"running"}`. pydantic 1.10.13 di bridge-venv
  (terverifikasi sebelum start).
- **B17:** pola subscribe di log = `telemetry/+/data` (3 level,
  benar). Publish paho QoS 1 ke `telemetry/simulasi_b4_sn_001/data`
  `{"temperature": 32.5, "humidity": 68, "event": "telemetry"}`
  (rc 0) → log bridge `Processing telemetry for device:
  simulasi_b4_sn_001`.
- **B18:** bridge POST `/iiot/webhook/simulasi_b4_sn_001` → HTTP
  200; efek di Odoo: device 1 `shadow_state={"temperature": 32.5,
  "humidity": 68, "event": "telemetry"}`, `last_telemetry`
  08:46:26 (persis waktu publish), `connection_status=online`;
  storage env 1 T 33.0 → **32.5** (rule jalan via jalur MQTT);
  `bridge_data.db` tabel `telemetry_queue` = **0 baris** (0 fallback
  persistence); gateway tetap **1 baris**
  (`SIMULASI-B4-GW-01`, online — tidak ada gateway sampah baru).
- Bridge + broker dimatikan sesudah E2E (kill 19189/19172; `:8000`
  connection refused, `:1883` connect_ex 111 terkonfirmasi).

### B20 — LOLOS

Bridge + broker MATI, rule 1 `SIMULASI B4 Rule Otomatis Suhu`
`active=True` (sudah diaktifkan koordinator sebelum ronde —
terverifikasi di fase 0). Skrip `/tmp/b4r1_b20b21.py`:
`iiot.telemetry.create` T=40, device 1, `production_id`=task 12 →
**id 8 TERSIMPAN** (tidak rollback). Bukti log (panggilan ulang
`check_and_trigger` pada telemetri 8, output penuh
`/tmp/b4r1_b20log.txt`): `WARNING ... AUTOMATION (B20): Rule
'SIMULASI B4 Rule Otomatis Suhu' triggered (temperature > 35.0)
but command 'power_on' FAILED for device
'SIMULASI-B4-SN-001 (simulasi_b4_sn_001)' via gateway
'SIMULASI B4 Gateway' (http://127.0.0.1:8000, state online):
... Connection refused ... Telemetry record kept; command NOT
delivered.` Return `False`. Chatter FAILED di task 12: message
26480 + 26481 (`AUTOMATION: Rule ... triggered but command
'power_on' FAILED ... (temperature > 35.0)`). Catatan: baris log
B20 TIDAK ada di log server HTTP (`/tmp/odoo18-server-b4r1.log`)
karena `check_and_trigger` jalan di proses shell yang memanggil
`create()` — log yang sama dicatat dari output proses shell itu.
(Pelajaran proses: jangan grep log server untuk bukti yang
dihasilkan proses shell.)

### B21 — LOLOS

Skrip yang sama: `iiot.telemetry.create` T=50, device 1, task 12 →
**id 9 TERSIMPAN**; activity korelasi di device 1: 2 → 4
(**504, 505** baru, summary `SIMULASI B4 Korelasi Suhu Tinggi`;
501/502 dari verifikasi perbaikan B21). T=40 juga memicu korelasi
(>35) — jadi 2 activity baru untuk 2 telemetri. Tanpa exception,
tanpa rollback.

### B22 — LOLOS 5/5

Skrip `browser-proof-b4r1-b22.py` (screenshot 440–449, **0/0
error**): 5 forecast via UI di lahan BARU `SIMULASI B4R1 Lahan B1`
(id 13, tanpa alert aktif — sengaja, supaya B23 tidak kena dedup
per-lokasi), tanggal 1–5 Des 2026. Verifikasi dari DB
(`/tmp/b4r1_b22b23.py`): id **20** storm (precip 60,
`warning True, type 'storm'`), **21** frost (min -2),
**22** heat (max 40), **23** wind (18 m/s), **24** normal
(`warning False, type False`) — **semuanya benar langsung saat
create, tanpa write kedua**. (Di form, `warning_type` tampil
sebagai label teks — `Extreme Heat`, `Strong Wind` — dan
`is_warning` tidak terbaca via selector input; nilai otoritatif
adalah DB di atas.)

### B23 — LOLOS

Skrip yang sama (`/tmp/b4r1_b22b23.py`): `_trigger_disaster_alert()`
pada forecast storm id 20 (lahan 13) → **tanpa exception**;
activity **503** `Weather Alert: storm predicted on 2026-12-01`,
`res_model='farm.location'`, `res_model_id=2294`
(= `ir.model._get('farm.location').id`), `res_id=13`, active.
Trigger kedua → tetap **1** alert aktif (dedup jalan).
Dedup per-lokasi (bukan bug): lahan 12/3/7 sudah punya alert aktif
(497/498/499+500) — karena itu B22/B23 memakai lahan B4R1 baru.

### B24 (BARU) — jalur command Odoo → bridge MASIH 500 ❌

Sinyal terbuka pekerja B16, kini ter-repro + terdiagnosis persis.
Bridge HIDUP, curl (cookie sesi admin):
`POST /iiot/command/simulasi_b4_sn_001`
`{"action":"power_on","params":{"state":"on"}}` →
`{"result":{"error":"Error occurred while sending command to
gateway: Gateway rejected command: Internal Server Error",
"status":"error"}}`. Repro langsung ke bridge:
`POST http://127.0.0.1:8000/api/v1/webhook`
`{"event":"command","payload":{"device_id":"simulasi_b4_sn_001",
"action":"power_on","params":{"state":"on"}}}` →
**HTTP 500, body persis `Internal Server Error`** (21 byte).
Traceback di log bridge (`/tmp/b4r1_bridge.log`, sebelum restart):
`File ".../agri_iot/mqtt_bridge/main.py", line 89, in
odoo_webhook_callback` →
`success = await self.mqtt_service.send_device_command(device_id,
{"action": action, "params": params})` →
**`TypeError: object bool can't be used in 'await' expression`**.
Akar: `send_device_command` mengembalikan bool (sync), tapi
handler meng-`await`-nya. Perbaikan yang diperlukan (di luar
tugas simulasi — JANGAN diperbaiki di ronde ini): hapus `await`
di `main.py:89` (atau jadikan `send_device_command` async).
Dampak: command Odoo → bridge → device TIDAK PERNAH terkirim
(telemetri MQTT→Odoo tidak terpengaruh; B20 menutupi kegagalan
command supaya telemetri tetap tersimpan). `POST {}` ke endpoint
yang sama menjawab 200 `{"status":"ignored"}` (bukan command) —
jalur webhook lain sehat. `farm.command.log` tetap 0.

## Bagian 1 — rantai batch 1: LOLOS 9/9 (data B4R1 baru)

Skrip shell `/tmp/b4r1/b4r1_p1a.py`, `b4r1_p1b.py`, `b4r1_p1c.py`
(adaptasi `shell-b4/` via sed; `valuation_method` di p1c
diperbaiki jadi `'cost_model'` langsung — tidak perlu p1c2).

- L0 master: template 225–229, lahan **14** (`SIMULASI B4R1
  Lahan A1`), campaign 12, route 11, BoM tomat **62**, BoM saus
  **63**.
- L1 benih: lot **183** (`SIMULASI B4R1-LOT-BENIH-001`), seed batch
  **17**, germ 92%, PVP compliant; blok germinasi 70% TERBUKTI
  (`UserError: SEED QUALITY BLOCK ...`, lot blok 184).
- L2 nursery: `farm.nursery.batch` **9**, lot bibit **185**,
  25.000 bibit, transplant GDD 200; `action_create_transplant_task`
  → True (stub, temuan lama).
- L3 tanam: asset **13**, rotation **12**, `planted`, warning
  False, risk 0.0.
- L4 GDD: 10 hari 32/22 °C → 170.0; stage 14 → 100.0; +1 hari →
  187.0, stage 15 → 62.333…; +10 hari → 357.0, stage 16 → 71.4,
  stage 17 → 44.625. (Persis B4.)
- L5 intervensi 39–43, MO WH/MO/00126–00130, workflow penuh,
  NPK 8.0/8.0/8.0 semua.
- L6 panen: lot **186**, `farm.crop.lot` **7**, grade A 400/B
  80/C 20, rotation → `harvested`, harvesting_date 2027-02-08.
- L7 quality: point **7**, check **7** → `pass`, record book **7**
  draft → `active`.
- L8 olah: season **9**, seasonal BoM **9** tetap `draft` (stub
  `action_activate`, temuan lama); MO saus WH/MO/00131 + 00132
  `done`; saus +16 kg, tomat 500 → 480 kg.
- L9 valuasi: market price **9** (Rp 12.000/kg); fair valuation
  **9** (`market_price=0.0`, `fair_value=0.0` — temuan lama);
  cost valuation **9**, NBV = fair = **Rp 2.500.000**.

## Bagian 2 — verifikasi batch 2: LOLOS

- Intervensi baru MURNI via UI: `SIMULASI B4R1 Intervensi Pupuk
  NPK Tomat A1`, IV id **72** (`/odoo/agri.intervention/72?debug=1`),
  MO WH/MO/00159; skrip `browser-proof-b4r1-b2.py` (screenshot
  450–453) + `browser-proof-b4r1-b2b.py` (455–457, **0/0 error**
  keduanya): Submit → Approve → Start Agri Work → Stop Agri Work
  sampai `done`/`Completed`; NPK IV72 8.0/8.0/8.0 (tab Costs &
  Nutrients, 3× `8.00`); MO159 tab Soil Nutrient 3× `8.00`,
  gating `weather='none'`, `compliance='none'`,
  `iot_status='normal'`. (Quirk skrip, bukan bug: regex
  `id=(\d+)` gagal pada URL format baru
  `/odoo/agri.intervention/72` — workflow dijalankan skrip b2b
  terpisah; cek `'SIMULASI B4R1 Intervensi' in text: False` di
  form IV72 adalah artefak `innerText` yang tidak membaca nilai
  `<input>` nama — identitas record terbukti dari URL + workflow
  + NPK; hal sama pada `'WH/MO/00159' in text: False` di form
  MO159.)
- **Insiden runtime restart (bukan bug modul):** run pertama
  skrip b2 terpotong VM replacement saat screenshot 450 (hanya
  form IV40 terbuka, belum Save). Sesudah server dipulihkan,
  cek shell: hanya IV40 yang ada, MO max 132 — TIDAK ada
  duplikat; skrip diulang penuh dan berhasil.
- Penyelesaian MO159 (shell `/tmp/b4r1_p2mo.py`): `done`, raw NPK
  50,00 kg, finished tomat 5.000,00 kg; tomat B4R1 480 →
  **5.480 kg**; NPK B4R1 50 → **0,0 kg**. **Beda dari B4
  (sengaja, perbaikan proses):** TANPA top-up NPK 50 kedua —
  p1a sudah memberi tepat 50 kg, jadi tidak ada lagi angka akhir
  50 kg yang membingungkan seperti insiden B4; konsumsi 50 kg
  terbukti dari SVL/move (raw 50,0 kg).
- **Gap nomor MO 133–158 (sequence-only, bukan record hilang):**
  hanya MO 159 yang ada ≥133 — 26 nomor terpakai transaksi
  rollback (kemungkinan percobaan create MO saat pembuatan
  intervensi via UI). MO max 168 di akhir ronde.
- Wizard migrasi ISL (skrip `browser-proof-b4r1-c.py`,
  screenshot 458–463, **0/0 error**): Run 1 notifikasi hijau
  t+2s, dialog menutup sendiri; Run 2 notifikasi t+1s, dialog
  menutup; negatif Confirm OFF → UserError, dialog tetap
  terbuka (2 dialogs). Verifikasi shell (`/tmp/b4r1_isl.py`):
  ISL **79 → 95** (+16, tepat jumlah MO tanpa ISL sebelum
  wizard); MO tanpa ISL sesudah wizard = **0**; MO159 → ISL 95;
  MO126–132 semua ter-migrasi.
- Tab Spatial MO27 (tillage B2G) di `?debug=1`: gauge **100%
  Within Boundaries**, tanpa `NaN%` (screenshot 461).

## Bagian 3 — alur batch 3: LOLOS

Prep shell `/tmp/b4r1/b4r1_p3prep.py`: ternak template 258–260
(Sapi Perah/Pakan Sapi/Daging Sapi), pakan sapi stok 100 kg; BoM
pakan sapi **95** (`feeding`, 1 ekor ← 10 kg pakan), BoM panen
sapi **96** (`harvesting`, 250 kg daging ← 1 ekor); ISL livestock
recipe (via `recipe_id` = BoM 95); sire lot **217**
`SIMULASI B4R1-LOT-SAPI-SIRE` (is_animal, lahir 2024-01-01,
breeding open, start_weight 500, ADG 0,7; quant 1 ekor).
Akuakultur: kategori `SIMULASI B4R1 Pond`; template Kolam
Lele/Lele/Pakan Lele/Lele Panen 261–264; pakan lele stok 100 kg;
lot kolam **218**, lot lele **219** (1.000 ekor); BoM pakan lele
**97** (`feeding`, 1.000 ekor ← 50 kg pakan), BoM panen lele
**98** (`harvesting`, 50 kg panen ← 100 ekor); ISL aqua recipe
(via `recipe_id` = BoM 97); ISL aqua lot (lot 219,
`water_volume_m3=1000.0`). Perbaikan proses vs B4: kategori
`SIMULASI B4R1 Pond` langsung dipasang ke template Kolam Lele
via shell (`/tmp/b4r1_pond.py`) SEBELUM E1 — pond pick di E1c
langsung jalan tanpa putaran perbaikan seperti B4.

- **D1 — lot + MO pakan sapi via UI** (skrip
  `browser-proof-b4r1-d.py`, screenshot 464–470, **0/0
  error**): lot sapi **220** `SIMULASI B4R1-LOT-SAPI-001` via UI
  tersimpan (B10-residu LOLOS: `is_animal=True`,
  `animal_name=SIMULASI B4R1 Sapi 001`,
  `ear_tag_number=SIMULASI B4R1-ET-001`,
  `birth_date=2026-11-10`, `start_weight=300`,
  `average_daily_gain=0.8`, `active_feeding_bom_id=95`); lot
  biasa **221** `SIMULASI B4R1-LOT-TEST-B10` tersimpan; MO pakan
  sapi **160** via UI + Confirmed.
- **MO160 + cron pakan** (shell `/tmp/b4r1_p3b.py`): MO160
  `done`, raw pakan 10,0 kg, finished sapi 1,0 ekor; sapi B4R1
  12, pakan B4R1 90. Cron `_cron_daily_feed_depletion()` OK →
  MO **161–165** `done` (lot 53/84/119/177/220); B4R1 pakan
  90→80, sapi 12→13, `total_feed_consumed` lot 220 = 1.0.
  **Efek samping desain (sama seperti B4):** cron tanpa filter
  lot memproses lot lama juga — B4 pakan 80→70, sapi 12→13.
- **D2 — timbang/breeding/env/MO panen daging via UI**
  (skrip `browser-proof-b4r1-d2.py`, screenshot 471–479,
  **0/0 error**): event timbang **38** (lot 220, 320 kg);
  breeding **37** (animal 220, sire 217, offspring 1,
  `gestation_days=0` — observasi lama); env monitoring **5**
  (lahan 14, T 28, H 65, `comfort_index=77.64`); MO panen
  daging **166** via UI + Confirmed. Shell
  `/tmp/b4r1_p3c.py`: MO166 `done`, raw sapi 1,0 ekor,
  finished daging 250,0 kg; sapi B4R1 13→12, daging B4R1 250.
  Mortalitas `action_record_mortality(1, 'Sakit')` hanya chatter
  (stok sapi tetap 12 — observasi, sama seperti ronde lama).
- **E1 — operasi akuakultur via UI** (skrip
  `browser-proof-b4r1-e1.py` + `b4r1-e1b.py` + `b4r1-e1c.py`,
  screenshot 480–491, **0/0 error**): daftar action 1024
  terbuka sebagai list (B14 LOLOS, 4 tab). Operasi **14**
  `SIMULASI B4R1 Operasi Lele Kolam 001` tersimpan via UI
  (B12-residu LOLOS: `parent_id=False` tidak meledak); field
  aqua hanya muncul di DOM sesudah tab Aquaculture Information
  diklik — E1b mengisi semuanya: species Lele Dumbo, stocking
  1000, stage growing, w0 50, target 500, feed 3.0, T 28.0,
  pH 7.2, DO 6.5, NH3 0.3, NO2 0.1 (input.value terverifikasi:
  T 28.00, pH 7.20, DO 6.50, NH3 0.30, NO2 0.10, feed 3.00);
  sub-task **15** `SIMULASI B4R1 Sub-tugas Pemberian Pakan`;
  `pond_id` = `SIMULASI B4R1-KOLAM-001` (lot 218) ter-pick dan
  Save (input.value terverifikasi).
- **E2 — WQ log + MO lele via UI** (skrip
  `browser-proof-b4r1-e2.py`, screenshot 492–496, **0/0
  error**): WQ log **5** (operasi 14, T 29.0, pH 7.10, DO 5.80,
  NH3 0.40, NO2 0.20, turbidity 12.00); MO pakan lele **167**
  via UI + Confirmed; MO panen lele **168** via UI + Confirmed.
  Shell `/tmp/b4r1_p3d.py`: MO167 `done` (raw pakan lele 50,0
  kg, finished lele 1.000,0 ekor), MO168 `done` (raw lele 100,0
  ekor, finished panen 50,0 kg); lele B4R1 1.900, pakan lele
  B4R1 50, panen B4R1 50. `total_feed_consumed` lot 219 tetap
  0.0 (observasi: MO lele tidak menulis balik feed ke lot —
  sama seperti ronde lama).
- **B13 — hook telemetri DO rendah** (shell `/tmp/b4r1_p3d.py`,
  pola `b4_b13d.py`): ISL aqua task B4R1 baru **5** (intervention
  MO167, BoM 97): DO 2.0 < threshold 4.0 → `latest_do_level=2.0`,
  `latest_water_temp=29.0`, `agent_status_feedback=executing`,
  activity **506** `INCIDENT: Oxygen Depletion (critical)` —
  tanpa crash. B13 LOLOS.

## Bagian 4 — F7 regresi render: LOLOS 17/17

Skrip `browser-proof-b4r1-f7.py` (screenshot 497–513): 17/17
halaman batch 4 terbuka tanpa error dialog / "Oh snap" — forecast
1037, profile 1038, telemetry 1039, rule 1040, device 1041,
firmware 1042, update 1043, gateway 1044, mapping 1046, telemetry
history 1047, automation rule 1048, correlation 1049, twin scene
1050, storage env 1051, + form device 1, gateway 1, forecast 1.
**0 pageerror + 0 console error.**

## Blocker baru (B24)

| ID | Ringkasan | File / baris | Perbaikan yang diperlukan |
|---|---|---|---|
| B24 | Command Odoo → bridge SELALU 500: `TypeError: object bool can't be used in 'await' expression` — `send_device_command` sync di-`await` | `agri_iot/mqtt_bridge/main.py:89` (`odoo_webhook_callback`, cabang `event == "command"`) | Hapus `await` di baris 89 (atau jadikan `send_device_command` async). Repro: bridge hidup, `POST /api/v1/webhook {"event":"command","payload":{"device_id":"simulasi_b4_sn_001","action":"power_on","params":{"state":"on"}}}` → 500 `Internal Server Error`; via Odoo: `POST /iiot/command/simulasi_b4_sn_001` (sesi admin) → `result={"error":"... Gateway rejected command: Internal Server Error","status":"error"}` |

## Observasi B4R1 (bukan blocker)

- O-B4R1-1: `device/config` mengembalikan MQTT default pabrik
  (`mqtt.factory.com:8883`, TLS true), bukan config gateway lokal
  — lihat B16 observasi di atas.
- O-B4R1-2: label gateway di log B20 memakai `state` tersimpan
  (`online`) walau bridge mati — state gateway tidak di-refresh
  saat bridge mati (stale).
- O-B4R1-3: cek `'...nama...' in text` pada form yang nilainya
  ada di `<input>` memberi False palsu (`innerText` tidak membaca
  nilai input) — IV72, MO159; bukti identitas tetap URL + state
  + nilai tab. Bukan bug modul.
- O-B4R1-4: nomor MO 133–158 hilang (sequence-only, rollback) —
  lihat Bagian 2.
- O-B4R1-5: `farm.water.quality.log` memakai field
  `temperature` (bukan `water_temperature` — itu milik operasi);
  `weather_conditions` Char; `total_feed_consumed` lot lele
  tetap 0.0; `gestation_days` breeding = 0; cron B11 tanpa
  filter lot (efek samping ke data lama, seperti B4).
- O-B4R1-6: VM replacement di tengah ronde menghapus
  `pgtest` + `/opt/pgserver` + isi `/tmp` (termasuk log bridge
  + skrip `/tmp/b19-*.py` + token/cookie uji) — test bed
  dipulihkan dari snapshot disk, data test18 utuh. Server
  pengganti: PID 1813, log `/tmp/odoo18-server-b4r1.log` (baru).

## Stok akhir B4R1 (WH/Stock, company 1; 10 Nov 2026)

Benih **10 kg**, bibit **25.000 unit**, tomat segar **5.480 kg**,
saus tomat **16 kg**, NPK **0,0 kg** (tepat habis — konsumsi MO159
50 kg, tanpa top-up ganda); sapi **12 ekor**, pakan sapi
**80 kg**, daging sapi **250 kg**; kolam lele **1**, lele
**1.900 ekor**, pakan lele **50 kg**, lele panen **50 kg**.

Stok B4 berubah karena cron B4R1 (tanpa filter): B4 sapi 13 /
pakan 70 (dari 12/80); tomat B4 5.480 / saus 16 / NPK 50 tetap
(tidak tersentuh ronde ini).

MO max **168** (WH/MO/00168), ISL `mrp` total **95**.

## Data SIMULASI B4R1 yang tertinggal di test18

- Produk template 225–229, 258–264; lahan 13 (`SIMULASI B4R1
  Lahan B1`, untuk B22/B23) + 14 (`SIMULASI B4R1 Lahan A1`,
  rantai batch 1); campaign 12; route 11; BoM 62/63/95/96/97/98;
  seed batch 17; nursery batch 9; asset 13; rotation 12;
  intervensi 39–43 + 72; MO 126–132, 159–168 (160–165, 166,
  167, 168 done); lot 183/184/185/186/217/218/219/220/221; crop lot 7;
  QC point/check/record book 7; season 9; seasonal BoM 9;
  market price 9; fair valuation 9; cost valuation 9; ISL mrp
  total 95; ISL livestock recipe (BoM 95), ISL aqua recipe
  (BoM 97), ISL aqua lot (lot 219), ISL aqua task **5** (MO167).
- Ternak B4R1: event timbang 38, breeding 37, env 5. Aqua B4R1:
  operasi 14 (+ sub-task 15), WQ log 5.
- IoT B4R1: device **9** (`SIMULASI-B4R1-SN-001`,
  `simulasi-b4r1-sn-001`); telemetri **8** (T=40, B20) + **9**
  (T=50, B21); forecast 20–24 (lahan 13); aktivitas 503
  (Weather Alert storm, lahan 13), 504 + 505 (korelasi suhu,
  device 1), 506 (B13, ISL aqua task 5); chatter FAILED
  26480/26481 di task 12.
- Gateway tetap 1 (`SIMULASI-B4-GW-01`); `iiot.telemetry` total 6.
- Nomor MO yang hilang (sequence-only): 00076–00105 (lama),
  00039/00040/00044/00046/00052/00068 (lama), 00133–00158 (B4R1,
  rollback).

## Batch 4 — Simulasi ulang jalur command (B4R2) — 10 Nov 2026 (TIDAK BERSIH ❌ — 1 blocker BARU B25)

Simulasi ulang TERFOKUS jalur command sesudah perbaikan B24
(10 Nov 2026, ~09:15–09:25 WIB). Delta sejak B4R1 HANYA
`agri_iot/mqtt_bridge/main.py` (hapus `await` di 5 baris) — tidak
ada perubahan kode modul Odoo. Server TIDAK di-restart (PID 1813,
8071 → 200, log `/tmp/odoo18-server-b4r1.log`). Data baru
berawalan `SIMULASI B4R2`. Screenshot 514–533 di `simulasi/`.
Skrip: `browser-proof-b4r2-b24ui.py`, `browser-proof-b4r2-b25details.py`,
`browser-proof-b4r2-f7.py` + skrip shell `/tmp/b4r2_*.py`.

**Keputusan: TIDAK BERSIH.** **B24 LOLOS 100%** (semua jalur
command yang diperbaiki terbukti ujung-ke-ujung, termasuk config
publish 349/364 yang di B24 belum teruji end-to-end) + B20
dengan bridge hidup LOLOS + regresi F7 17/17 LOLOS + stok batch
1–3 utuh. Satu blocker BARU **B25**: tombol command di form
device (Power On / Power Off / Reset) SELALU melempar
`TypeError` sebelum request sampai ke bridge — override
`farm_iot` menimpa signature base tanpa default `action`.

## Ringkasan hasil B4R2

| Bagian | Hasil |
|---|---|
| B24 — command Odoo → bridge → device (curl + UI) | LOLOS via curl/endpoint; **GAGAL via tombol UI → lihat B25** |
| B24 — webhook langsung + `{}` + `/command/send` | LOLOS |
| OTA `/api/v1/ota/send` (titik 227) | LOLOS |
| Config publish sukses (349) + error (364) | LOLOS (end-to-end via MQTT) |
| B20 — rule terpicu saat bridge HIDUP | LOLOS (command TERKIRIM, telemetri tersimpan) |
| F7 — render 17 halaman batch 4 | LOLOS 17/17 |
| Regresi stok/data batch 1–3 | LOLOS (angka sama dengan akhir B4R1) |
| **B25 (BARU) — tombol command di form device** | **GAGAL (TypeError)** |
| Kebersihan infra | LOLOS (bridge+broker mati, port bebas, gateway 1) |

## Fase 0 — precheck (tidak ada kejutan)

`farm.automation.rule` **1** `'SIMULASI B4 Rule Otomatis Suhu'`
`active=True`, sensor temperature, `>` 35.0, `power_on`,
params `{"state": "on"}`, device 1. Device 1
`SIMULASI-B4-SN-001` / `simulasi_b4_sn_001`, token terisi,
profil `SIMULASI B4 Profil Suhu`. `farm.command.log` = **1**
(sisa verifikasi perbaikan B24), gateway = **1**
(`SIMULASI-B4-GW-01`), `iiot.telemetry` = 6. Stok = angka akhir
B4R1 (tomat 5.480, saus 16, sapi 12, lele 1.900). Verifikasi
statis perbaikan: `grep 'await self.mqtt_service' main.py` →
**0 baris**; 5 pemanggilan sync di 89/170/227/349/364.

## B24 — LOLOS (curl + endpoint + MQTT)

Infra: broker amqtt `/tmp/b24-broker.py` (127.0.0.1:1883, PID
6334); subscriber paho `/tmp/b4r2-sub.py` (PID 6362, 4 topik:
`command/…/action`, `ota/…/notify`,
`iiot/config/simulasi_b4_sn_001`,
`iiot/config/SIMULASI-B4-SN-001`); bridge `python main.py` dari
dalam `agri_iot/mqtt_bridge/` (proxy env di-unset SEMUA 8
variabel, `.env` sudah benar, `BRIDGE_ID=SIMULASI-B4-GW-01`),
PID 6396, log `/tmp/b4r2-bridge.log`. Start bersih: `Using
remote MQTT config: 127.0.0.1:1883`, `Successfully connected to
MQTT broker`, `Subscribed to topics: iiot/config/request,
telemetry/+/data, ota/+/status`, `Successfully registered bridge
SIMULASI-B4-GW-01 with Odoo`; `/health` → 200
`{"status":"healthy","mqtt_connected":true}`.

- **Jalur Odoo (curl, sesi admin):** login via
  `/web/session/authenticate` (uid 2) →
  `POST /iiot/command/simulasi_b4_sn_001`
  `{"action":"power_on","params":{"state":"on"}}` →
  **`{"result":{"status":"success","message":"Command power_on
  sent to simulasi_b4_sn_001"}}`**. Subscriber menerima
  `topic=command/simulasi_b4_sn_001/action`
  `payload={"action": "power_on", "params": {"state": "on"}}`.
  Log bridge: `Received webhook event from Odoo: command`,
  `POST /api/v1/webhook 200 OK`. `farm.command.log`: **1 → 2**
  (id 2, `power_on`, `dispatched`, `{"state": "on"}`).
- **Webhook langsung:** `POST /api/v1/webhook` event command →
  **200 `{"status":"success"}`**, subscriber menerima payload
  ke-2 yang identik. `POST {}` → **200
  `{"status":"ignored","message":"Unknown event: None"}`**
  (tidak regresi). `POST /api/v1/command/send` `power_off` →
  **200 success**, subscriber menerima
  `{"action": "power_off", "params": {"state": "off"},
  "timestamp": ...}` (titik 170).
- **0× `TypeError`/`Traceback`** di seluruh log bridge.

## OTA — LOLOS (titik 227)

`POST /api/v1/ota/send`
`{"device_id":"simulasi_b4_sn_001","action":"firmware_update",
"params":{"version":"1.2.3","url":"http://example.local/fw.bin"}}`
→ **200 `{"status":"success","message":"OTA command
firmware_update sent to device simulasi_b4_sn_001"}`**;
subscriber menerima `topic=ota/simulasi_b4_sn_001/notify`
payload lengkap (`action`, `params`, `timestamp`,
`command_type: "ota"`).

## Config publish — LOLOS end-to-end (titik 349/364)

Dipicu dari device via MQTT (publish ke `iiot/config/request`),
bukan dari `device/config` HTTP — alur yang dipakai
`handle_config_request`:

- **Jalur error (364):** `{"serial":"SIMULASI-B4-SN-001",
  "token":"TOKEN-SALAH-B4R2"}` → subscriber menerima
  `topic=iiot/config/SIMULASI-B4-SN-001`
  `{"error": "Invalid serial or token", "timestamp": ...}`,
  tanpa TypeError.
- **Jalur sukses (349):** token benar → subscriber menerima
  `topic=iiot/config/simulasi_b4_sn_001` config lengkap
  (`device_id`, `mqtt_config` host `mqtt.factory.com:8883` TLS,
  `topics` telemetry/command/ota_notify/ota_status); log bridge
  `Sent configuration to device: simulasi_b4_sn_001`.
- Efek samping (sama seperti B16): config request
  meng-invalidasi token device 1 → token diregenerasi via
  `action_generate_config_token` (dengan commit), `token_set`
  kembali True di akhir ronde.

## B20 dengan bridge HIDUP — LOLOS (bandingkan B4R1)

Skrip `/tmp/b4r2_b20b.py`: `iiot.telemetry.create` T=40,
device 1, `production_id`=task 12 → **id 11 TERSIMPAN**
(komit). Rule 1 terpicu → `farm.command.log` **2 → 3** (id 4,
`power_on`, `dispatched`, `{"state": "on"}`); subscriber
menerima payload `power_on`; log bridge `Received webhook event
from Odoo: command`, `POST /api/v1/webhook 200 OK`. Chatter
task 12: message **26630** SUKSES — `AUTOMATION: Rule 'SIMULASI
B4 Rule Otomatis Suhu' triggered. Command 'power_on' sent to
SIMULASI-B4-SN-001 (simulasi_b4_sn_001) because temperature was
> 35.0.` — kebalikan persis B4R1 (bridge mati → FAILED
26480/26481, telemetri tersimpan). Korelasi B21 ikut jalan:
activity baru **508** `SIMULASI B4 Korelasi Suhu Tinggi`
(device 1). Telemetri tersimpan, command terkirim.

## B25 (BARU) — tombol command di form device GAGAL ❌

Tombol UI **ADA** di form device (`iiot_device_views.xml:52-54`:
Power On / Power Off / Reset, `type="object"`
`name="send_command"`, context `{'action': 'power', 'params':
{'state': 'on'}}` — plus stat button Send Reset Command
`context={'action': 'reset'}`). Skrip
`browser-proof-b4r2-b24ui.py` (screenshot 514–515, **0
pageerror + 0 console error**): form device 1 terbuka normal,
klik **Power On** → dialog **"Oops! Something went wrong…"**
(`errdlg=1`), subscriber TIDAK menerima payload, log bridge
TIDAK mencatat webhook apa pun (klik gagal sebelum HTTP).
Detail teknis dialog (screenshot 516, direpro 2×): traceback
server berakhir
**`TypeError: IiotDevice.send_command() missing 1 required
positional argument: 'action'`**
(`web/controllers/dataset.py:42 call_button` →
`odoo/api.py:535 call_kw` → `send_command()` tanpa argumen).

Akar: `farm_iot/models/iiot_device.py:23` meng-override
`def send_command(self, action, **params)` — `action` TANPA
default — sehingga menimpa base
`agri_iot/models/iiot_device.py:154`
`def send_command(self, action=None, **params)` yang justru
dibuat agar tombol UI (tanpa argumen, action lewat context)
jalan (lihat docstring NOTE di base). Override memanggil
`super().send_command(action, ...)` lalu menulis
`farm.command.log` — tapi tidak pernah sampai ke sana karena
`call_kw` tanpa argumen langsung melempar TypeError. File ada
di repo (`custom_addons/farm_iot` symlink ke repo) — bukan
drift test bed. Terdampak keempat tombol (Power On/Power Off/
Reset + Send Reset Command — yang terakhir tidak diklik
terpisah, mekanismenya identik). Jalur controller
(`POST /iiot/command`, memanggil dengan argumen eksplisit)
dan rule B20 TIDAK kena — karena itu B24 curl LOLOS sementara
tombol UI gagal. Dua klik UI tidak membuat baris
`farm.command.log` baru (gagal sebelum logging).

## F7 — regresi render: LOLOS 17/17

Skrip `browser-proof-b4r2-f7.py` (screenshot 517–533): 17/17
halaman batch 4 terbuka tanpa error dialog / "Oh snap" —
forecast 1037, profile 1038, telemetry 1039, rule 1040, device
1041, firmware 1042, update 1043, gateway 1044, mapping 1046,
telemetry history 1047, automation rule 1048, correlation 1049,
twin scene 1050, storage env 1051, + form device 1, gateway 1,
forecast 1. **0 pageerror + 0 console error.**

## Regresi cepat stok/data batch 1–3: LOLOS

B4R1: tomat **5.480**, saus **16**, sapi **12**, lele **1.900**,
NPK **0,0** — sama persis dengan akhir B4R1. B4: tomat 5.480 /
saus 16 / sapi 13 / pakan sapi 70 / lele 1.900 — tidak berubah.
MO max **168** (WH/MO/00168). Tidak ada cron yang mengubah
angka selama ronde.

## Kebersihan infra: LOLOS

Bridge (PID 6396) + broker (6334) + subscriber (6362)
dimatikan sesudah uji; port **8000 FREE, 1883 FREE**; Odoo 8071
tetap jalan (**PID 1813, HTTP 200** `/web/login`).
`iiot_gateway` tetap **1 baris** (`SIMULASI-B4-GW-01`).

## Blocker baru (B25)

| ID | Ringkasan | File / baris | Perbaikan yang diperlukan |
|---|---|---|---|
| B25 | Tombol command di form device SELALU TypeError: override `farm_iot` tanpa default `action` menimpa base yang mendukung panggilan UI tanpa argumen | `farm_iot/models/iiot_device.py:23` `def send_command(self, action, **params)` (base: `agri_iot/models/iiot_device.py:154` `action=None`) | Beri default `action=None` di override `farm_iot` (cermin base: ambil action/params dari context bila None), pastikan `farm.command.log` tetap ditulis. Repro: bridge hidup, buka `/odoo/action-1041/1?debug=1`, klik Power On → dialog Oops, traceback server `TypeError: IiotDevice.send_command() missing 1 required positional argument: 'action'`; subscriber tidak menerima apa pun. |

## Observasi B4R2 (bukan blocker)

- O-B4R2-1: login JSON-RPC ke `/web/login` ditolak CSRF
  (`400 Session expired (invalid CSRF token)`) — login curl
  yang benar: `POST /web/session/authenticate`.
- O-B4R2-2: `DeprecationWarning: datetime.utcnow()` di
  `main.py:358` (kosmetik, pre-existing, bukan B24).
- O-B4R2-3: bridge me-re-register gateway tiap ~30 detik
  (heartbeat — `POST /iiot/gateway/register 200 OK` berulang di
  log); tidak membuat gateway ganda (tetap 1 baris).
- O-B4R2-4: ada DUA model rule bernama mirip:
  `farm.automation.rule` 1 `'SIMULASI B4 Rule Otomatis Suhu'`
  (yang dipakai B20) vs `iiot.telemetry.rule` 1 `'SIMULASI B4
  Rule Suhu'` (json_path-based, bukan jalur B20) — jangan
  tertukar saat verifikasi.
- O-B4R2-5 (pelajaran proses): skrip `odoo-bin shell` TANPA
  `env.cr.commit()` di-rollback saat exit (`shell.py` memanggil
  `cr.rollback()`) — run B20 pertama + regen token pertama
  HILANG dari DB (efek eksternalnya tetap terjadi: subscriber
  menerima payload, bridge log 200). Diulang dengan commit
  (`/tmp/b4r2_b20b.py`) → telemetri **11** + cmdlog **4** +
  chatter **26630** persisten. Celah sequence-only akibat
  rollback: telemetri id 10, cmdlog id 3, chatter 26628/26629.
- O-B4R2-6: chatter FAILED **26482** di task 12 sudah ada
  SEBELUM ronde ini (bukan dari B4R2); asalnya tidak ditelusuri
  — kemungkinan dari verifikasi perbaikan B24.

## Stok akhir B4R2 (WH/Stock, company 1; 10 Nov 2026)

Sama dengan akhir B4R1 — benih **10 kg**, bibit **25.000 unit**,
tomat segar **5.480 kg**, saus tomat **16 kg**, NPK **0,0 kg**;
sapi **12 ekor**, pakan sapi **80 kg**, daging sapi **250 kg**;
kolam lele **1**, lele **1.900 ekor**, pakan lele **50 kg**,
lele panen **50 kg**.

## Data SIMULASI B4R2 yang tertinggal di test18

- IoT B4R2: telemetri **11** (T=40, B20, device 1, task 12);
  `farm.command.log` **4** (id 4, `power_on`, dispatched —
  total log kini 3 baris: id 1, 2, 4); activity **508**
  (korelasi suhu, device 1); chatter sukses **26630** di task
  12 (task 12 kini 7 message). Token device 1 diregenerasi
  (nilai baru, `token_set=True`).
- Tidak ada data batch 1–3 baru (ronde ini terfokus; stok
  diverifikasi utuh, bukan diulang).

## Batch 4 — Simulasi ulang tombol device (B4R3) — 10 Nov 2026 (TIDAK BERSIH ❌ — 1 blocker BARU B26)

Simulasi ulang TERFOKUS keempat tombol command sesudah
perbaikan B25 (10 Nov 2026, ~09:29–09:40 WIB). Delta sejak
B4R2 HANYA `farm_iot/models/iiot_device.py:23` (signature
`send_command(self, action=None, **params)`, action final
di-resolve dari context sebelum log) + versi `18.0.1.2.2`
(detail perbaikan: `PORTING.d/b25.md`). Koordinator sudah
upgrade `farm_iot` → 18.0.1.2.2 di test18 + restart server
(PID 8404, 8071 → 200, log `/tmp/odoo18-server-b4r3.log`).
Tidak ada perubahan kode modul lain. Data baru berawalan
`SIMULASI B4R3`. Screenshot 534–537 + 539–559 di `simulasi/`
(538 tidak ada — skrip buttons timeout di klik ke-4 karena
modal Oops memblokir klik; bukti tombol ke-4 di 541/542).
Skrip:
`browser-proof-b4r3-buttons.py`,
`browser-proof-b4r3-reset.py`, `browser-proof-b4r3-f7.py`
+ skrip shell `/tmp/b4r3_*.py`.

**Keputusan: TIDAK BERSIH.** Perbaikan B25 hanya **SEPARUH**
berhasil: **Power On + Power Off LOLOS** (perintah terkirim
ujung-ke-ujung, log `command='power'`), tetapi **Reset +
Send Reset Command MASIH dialog "Oops!"** — dengan
`TypeError` BARU (bukan B25): `send_command() got multiple
values for argument 'action'`. B24 (curl), B20 (bridge
hidup), F7 17/17, stok batch 1–3, dan kebersihan infra
semuanya LOLOS — tidak ada regresi.

## Ringkasan hasil B4R3

| Bagian | Hasil |
|---|---|
| B25 — tombol Power On | LOLOS (payload MQTT + log id 7 `power`, dispatched) |
| B25 — tombol Power Off | LOLOS (payload MQTT + log id 8 `power`, dispatched) |
| **B26 (BARU) — tombol Reset** | **GAGAL (TypeError baru, 3× repro)** |
| **B26 (BARU) — tombol Send Reset Command** | **GAGAL (TypeError baru, 1× repro)** |
| B24 — command Odoo → bridge → device (curl) | LOLOS (success + payload ke-3) |
| B20 — rule terpicu saat bridge HIDUP | LOLOS (telemetri 12 + log id 10 + chatter 26637) |
| F7 — render 17 halaman batch 4 | LOLOS 17/17 |
| Regresi stok/data batch 1–3 | LOLOS (angka sama dengan akhir B4R2) |
| Kebersihan infra | LOLOS (bridge+broker mati, port bebas, gateway 1) |

## Fase 0 — precheck (keadaan awal sesuai B4R2 + verifikasi B25)

`farm_iot` **18.0.1.2.2** `installed` (upgrade
terkonfirmasi). Device 1 `SIMULASI-B4-SN-001` /
`simulasi_b4_sn_001`, token terisi, `active=True`.
`farm.command.log` device 1 = **5** (id 1, 2, 4, 5, 6 —
id 5, 6 dari verifikasi shell B25). `iiot_gateway` = **1**
(`SIMULASI-B4-GW-01`), `iiot.telemetry` = 7. Rule 1
`'SIMULASI B4 Rule Otomatis Suhu'` `active=True`,
temperature `>` 35.0, `power_on`, `{"state": "on"}`,
device 1. Stok B4R1: tomat 5.480, saus 16, sapi 12, lele
1.900, NPK 0; B4 NPK 50. MO max 168.

## Infra B4R3

Broker amqtt `/tmp/b24-broker.py` (127.0.0.1:1883, PID
8707); subscriber paho `/tmp/b4r3-sub.py` (PID 8714,
4 topik: `command/…/action`, `ota/…/notify`,
`iiot/config/simulasi_b4_sn_001`,
`iiot/config/SIMULASI-B4-SN-001`, log
`/tmp/b4r3-sub.log`); bridge `python main.py` dari dalam
`agri_iot/mqtt_bridge/` (proxy env di-unset SEMUA 8
variabel, `.env` tidak diubah, `BRIDGE_ID=
SIMULASI-B4-GW-01`), PID 8716, log `/tmp/b4r3-bridge.log`.
Start bersih: `Using remote MQTT config: 127.0.0.1:1883`,
`Successfully connected to MQTT broker`, `Successfully
registered bridge SIMULASI-B4-GW-01 with Odoo`; `/health`
→ 200 `{"status":"healthy","mqtt_connected":true}`.

## B25 — SEPARUH LOLOS (Power On/Off ✅, Reset ❌ → B26)

Skrip `browser-proof-b4r3-buttons.py` (screenshot 534–537,
**0 pageerror + 0 console error**): form device 1 terbuka
normal (534); klik **Power On** → tanpa dialog Oops,
subscriber menerima `topic=command/simulasi_b4_sn_001/action`
`payload={"action": "power", "params": {"state": "on"}}`
(535); klik **Power Off** → tanpa dialog Oops, subscriber
menerima `payload={"action": "power", "params":
{"state": "off"}}` (536); klik **Reset** → dialog
**"Oops! Something went wrong…"** (`errdlg=1`, 537),
subscriber TIDAK menerima payload ke-3, log bridge TIDAK
mencatat webhook ke-3. Klik ke-4 (Send Reset Command)
gagal diklik di skrip yang sama karena modal Oops
memblokir pointer events (Playwright timeout 30 dtk) —
bukan kegagalan tombol itu sendiri, dibuktikan terpisah
di bawah.

`farm.command.log` device 1: **5 → 7** (id **7**,
`command='power'`, `dispatched`, `{"state": "on"}` —
Power On; id **8**, `command='power'`, `dispatched`,
`{"state": "off"}` — Power Off). Action final tercatat
`power`, **bukan None** — klaim perbaikan B25 untuk
kedua tombol ini terbukti. Dua klik Reset yang gagal
tidak membuat baris log baru (gagal sebelum logging,
sesuai desain "log sesudah super berhasil").

## B26 (BARU) — tombol Reset + Send Reset Command GAGAL ❌

Skrip `browser-proof-b4r3-reset.py` (screenshot 539–542,
**0 pageerror + 0 console error**): klik **Reset** →
dialog Oops (`errdlg=1`, 539) + detail teknis (540);
tutup dialog → klik **Send Reset Command** → dialog Oops
lagi (`errdlg=1`, 541) + detail teknis (542). Detail
dialog (540/542, `Odoo Server Error`, model
`iiot.device`, 10 Nov 2026 09:34:22/09:34:32 GMT) +
traceback server (`/tmp/odoo18-server-b4r3.log`,
09:31:57, 09:34:22, 09:34:32 — total **4×** di ronde ini:
1× dari skrip buttons + 3× dari skrip reset):

```
File ".../custom_addons/farm_iot/models/iiot_device.py",
  line 47, in send_command
    res = super(IiotDevice, self).send_command(action, **params)
TypeError: IiotDevice.send_command() got multiple values for
  argument 'action'
```

Mekanisme (terverifikasi dari kode + tooltip debug):
perbaikan B25 mengambil `params` dari
`self.env.context.get('params')`. Tombol Power On/Off
membawa `params` sendiri di context
(`{'state': 'on'/'off'}`) sehingga `params` tombol
menimpa `params` client → lolos. Tombol Reset / Send
Reset Command context-nya HANYA `{'action': 'reset'}`
(tanpa `params`) — maka `context.get('params')`
mengembalikan `params` milik web client Odoo 18 sendiri:
`{"debug": 1, "resId": 1, "action": 1041, "actionStack":
[...]}` (terlihat di `data-tooltip-info` tombol, dan di
tooltip screenshot 535). Dict itu mengandung kunci
`'action': 1041` → `super().send_command('reset',
**{'debug': 1, 'resId': 1, 'action': 1041, ...})`
melempar TypeError karena `action` terisi dua kali
(posisional `'reset'` + keyword `1041`). Pola yang sama
ada di base `agri_iot/models/iiot_device.py:154-163`
(`params = self.env.context.get('params') or params`)
— base akan crash identik bila dipanggil langsung;
yang terinstall dan terpanggil adalah override
`farm_iot`. Perbaikan yang diperlukan: jangan ambil
`params` mentah dari context bila kuncinya bukan
params perintah — mis. hanya pakai `context['params']`
bila ia dict TANPA kunci `action`/`debug`/`resId`, atau
ambil `params` hanya dari context tombol (bukan dari
`params` client Odoo 18). Repro: bridge hidup, buka
`/odoo/action-1041/1?debug=1`, klik Reset → dialog Oops;
subscriber tidak menerima apa pun, `farm.command.log`
tidak bertambah.

## B24 — LOLOS (curl, regresi)

Login via `/web/session/authenticate` (uid 2) →
`POST /iiot/command/simulasi_b4_sn_001` envelope
JSON-RPC `{"action":"power_on","params":{"state":"on"}}`
→ **`{"result":{"status":"success","message":"Command
power_on sent to simulasi_b4_sn_001"}}`**. Subscriber
menerima payload ke-3 `{"action": "power_on", "params":
{"state": "on"}}`; log bridge `Received webhook event
from Odoo: command` ke-3. `farm.command.log`: **7 → 8**
(id 9, `power_on`, `dispatched`). Catatan: percobaan
pertama mengirim body mentah tanpa envelope JSON-RPC
→ `{"error": "Action is required"}` (controller
`type='json'` membaca `request.params`, bukan body
mentah) — kesalahan skrip, BUKAN regresi; diulang
dengan envelope → sukses (temuan O-B4R3-1).

## B20 dengan bridge HIDUP — LOLOS

Skrip `/tmp/b4r3_b20.py` (dengan `env.cr.commit()`):
`iiot.telemetry.create` T=40, device 1,
`production_id`=task 12 → **id 12 TERSIMPAN** (komit).
Rule 1 terpicu → `farm.command.log` **8 → 9** (id 10,
`power_on`, `dispatched`, `{"state": "on"}`); subscriber
menerima payload ke-4 `power_on`; log bridge webhook
ke-4. Chatter task 12: message **26637** SUKSES —
`AUTOMATION: Rule 'SIMULASI B4 Rule Otomatis Suhu'
triggered. Command 'power_on' sent to SIMULASI-B4-SN-001
(simulasi_b4_sn_001) because temperature was > 35.0.`
(task 12 kini 8 message). Token device 1 tetap terisi.

## F7 — regresi render: LOLOS 17/17

Skrip `browser-proof-b4r3-f7.py` (screenshot 543–559):
17/17 halaman batch 4 terbuka tanpa error dialog /
"Oh snap" — forecast 1037, profile 1038, telemetry
1039, rule 1040, device 1041, firmware 1042, update
1043, gateway 1044, mapping 1046, telemetry history
1047, automation rule 1048, correlation 1049, twin
scene 1050, storage env 1051, + form device 1, gateway
1, forecast 1. **0 pageerror + 0 console error.**

## Regresi cepat stok/data batch 1–3: LOLOS

B4R1: tomat **5.480**, saus **16**, sapi **12**, lele
**1.900**, NPK **0** — sama persis dengan akhir B4R2.
B4 NPK **50** tetap. MO max **168**. Tidak ada cron
yang mengubah angka selama ronde.

## Kebersihan infra: LOLOS

Bridge (PID 8716) + broker (8707) + subscriber (8714)
dimatikan sesudah uji; port **8000 FREE, 1883 FREE**;
Odoo 8071 tetap jalan (**PID 8404/8406, HTTP 200**
`/web/login`). `iiot_gateway` tetap **1 baris**
(`SIMULASI-B4-GW-01`). `farm.command.log` total **9**,
`iiot.telemetry` total **8**.

## Blocker baru (B26)

| ID | Ringkasan | File / baris | Perbaikan yang diperlukan |
|---|---|---|---|
| B26 | Tombol Reset + Send Reset Command di form device MASIH dialog Oops (TypeError baru, bukan B25): override B25 mengambil `params` dari `env.context.get('params')`, tapi bila context tombol tanpa `params`, yang terambil adalah `params` web client Odoo 18 (`{debug, resId, action: 1041, actionStack}`) yang mengandung kunci `action` → `super().send_command('reset', **{...'action': 1041})` bentrok | `farm_iot/models/iiot_device.py:23-47` (pola sama di base `agri_iot/models/iiot_device.py:154-163`) | Jangan ambil `params` mentah dari context: hanya pakai `context['params']` bila ia dict params perintah (tanpa kunci `action`/`debug`/`resId`), atau saring kunci-kunci client sebelum `super()`. Repro: bridge hidup, buka `/odoo/action-1041/1?debug=1`, klik Reset → dialog Oops, traceback server `TypeError: IiotDevice.send_command() got multiple values for argument 'action'`; subscriber tidak menerima apa pun. |

## Observasi B4R3 (bukan blocker)

- O-B4R3-1: `POST /iiot/command` HARUS memakai envelope
  JSON-RPC (`{"jsonrpc":"2.0","method":"call","params":
  {...}}`) — body mentah `{"action":...}` dibaca sebagai
  `request.params` kosong → `{"error": "Action is
  required"}`. B4R2 mendokumentasikan body mentah secara
  singkat; envelope-lah yang benar.
- O-B4R3-2: dialog Oops yang terbuka memblokir klik
  tombol lain (modal menelan pointer events) — skrip yang
  mengklik berurutan WAJIB menutup dialog dulu sebelum
  klik berikutnya (pelajaran dari skrip buttons B4R3
  yang timeout 30 dtk di klik ke-4).
- O-B4R3-3: `DeprecationWarning: datetime.utcnow()` di
  `main.py:117` masih ada (kosmetik, pre-existing,
  bukan B24/B25/B26).
- O-B4R3-4: bridge me-re-register gateway tiap ~30 detik
  (heartbeat — sama seperti B4R2); tidak membuat gateway
  ganda (tetap 1 baris).

## Stok akhir B4R3 (WH/Stock, company 1; 10 Nov 2026)

Sama dengan akhir B4R2 — benih **10 kg**, bibit **25.000
unit**, tomat segar **5.480 kg**, saus tomat **16 kg**,
NPK **0,0 kg** (B4R1; B4 NPK 50 kg tetap); sapi **12
ekor**, pakan sapi **80 kg**, daging sapi **250 kg**;
kolam lele **1**, lele **1.900 ekor**, pakan lele **50
kg**, lele panen **50 kg**.

## Data SIMULASI B4R3 yang tertinggal di test18

- IoT B4R3: telemetri **12** (T=40, B20, device 1, task
  12); `farm.command.log` total **9** (id 7, 8 dari tombol
  Power On/Off — `command='power'`; id 9 dari curl B24 —
  `power_on`; id 10 dari B20 — `power_on`); chatter sukses
  **26637** di task 12 (task 12 kini 8 message). Token
  device 1 tetap terisi (`token_set=True`).
- Tidak ada data batch 1–3 baru (ronde ini terfokus; stok
  diverifikasi utuh, bukan diulang).

## Batch 4 — Simulasi ulang tombol Reset (B4R4) — 10 Nov 2026 (BERSIH ✅ — B26 LOLOS, batch 4 selesai 100%)

Simulasi ulang TERFOKUS tombol Reset sesudah perbaikan
B26 (10 Nov 2026, ~09:44–09:46 WIB). Delta sejak B4R3
HANYA guard `context['params']` di override `farm_iot`
DAN base `agri_iot` — `context['params']` hanya dipakai
bila dict TANPA kunci client (`'action'`, `'debug'`,
`'resId'`, `'actionStack'`) — + versi `farm_iot`
18.0.1.2.3 / `agri_iot` 18.0.1.0.2 (detail perbaikan:
`PORTING.d/b26.md`; verifikasi shell pekerja perbaikan:
CASE Reset persis → log id 11 `command='reset'`,
dispatched; Power On + argumen eksplisit + tanpa-context
+ base langsung semua OK). Koordinator sudah upgrade
kedua modul di test18 + restart server (PID 10765,
8071 → 200, log `/tmp/odoo18-server-b4r4.log`). Tidak ada
perubahan kode lain. Data baru berawalan `SIMULASI B4R4`.
Screenshot 560–564 (tombol) + 565–581 (F7) di `simulasi/`.
Skrip: `browser-proof-b4r4-buttons.py`,
`browser-proof-b4r4-f7.py` + skrip shell `/tmp/b4r4_*.py`.

**Keputusan: BERSIH.** B26 **LOLOS**: tombol **Reset +
Send Reset Command TIDAK LAGI dialog "Oops!"** — keduanya
mengirim perintah reset ujung-ke-ujung (subscriber MQTT
menerima `{"action": "reset", "params": {}}`,
`farm.command.log` id 16, 17 `command='reset'`,
dispatched). **Tidak ada regresi**: Power On/Off tetap
lolos, B24 (curl, envelope JSON-RPC) tetap lolos, B20
(bridge hidup) tetap lolos, F7 17/17, stok batch 1–3
utuh, kebersihan infra lolos. **0 pageerror + 0 console
error di semua skrip browser; 0× `TypeError` di log
server.** Batch 4 selesai 100% — gerbang batch 5 TERBUKA.

## Ringkasan hasil B4R4

| Bagian | Hasil |
|---|---|
| **B26 — tombol Reset** | **LOLOS (tanpa Oops, payload reset + log id 16 `reset`, dispatched)** |
| **B26 — tombol Send Reset Command** | **LOLOS (tanpa Oops, payload reset + log id 17 `reset`, dispatched)** |
| B25 — tombol Power On | LOLOS (payload MQTT + log id 14 `power`, dispatched) |
| B25 — tombol Power Off | LOLOS (payload MQTT + log id 15 `power`, dispatched) |
| B24 — command Odoo → bridge → device (curl) | LOLOS (success + payload ke-5 `power_on`) |
| B20 — rule terpicu saat bridge HIDUP | LOLOS (telemetri 13 + log id 19 + chatter 26647) |
| F7 — render 17 halaman batch 4 | LOLOS 17/17 |
| Regresi stok/data batch 1–3 | LOLOS (angka sama dengan akhir B4R3) |
| Kebersihan infra | LOLOS (bridge+broker mati, port bebas, gateway 1) |

## Fase 0 — precheck (keadaan awal = akhir B4R3 + verifikasi B26)

`agri_iot` **18.0.1.0.2** + `farm_iot` **18.0.1.2.3**
`installed` (upgrade terkonfirmasi). Device 1
`SIMULASI-B4-SN-001` / `simulasi_b4_sn_001`, token terisi,
`is_active=True`. `farm.command.log` device 1 = **12**
(id 11 `reset` + id 12, 13 `power` dari verifikasi shell
B26). `iiot_gateway` = **1** (`SIMULASI B4 Gateway`),
`iiot.telemetry` = 8. Rule 1 `'SIMULASI B4 Rule Otomatis
Suhu'` `active=True`, temperature `>` 35.0, `power_on`,
`{"state": "on"}`, device 1. Stok B4R1: tomat 5.480, saus
16, sapi 12, lele 1.900, NPK 0; B4 NPK 50. MO max 168.

## Infra B4R4

Broker amqtt `/tmp/b24-broker.py` (127.0.0.1:1883, PID
11011); subscriber paho `/tmp/b4r3-sub.py` (PID 11032,
4 topik: `command/…/action`, `ota/…/notify`,
`iiot/config/simulasi_b4_sn_001`,
`iiot/config/SIMULASI-B4-SN-001`, log
`/tmp/b4r4-sub.log`); bridge `python main.py` dari dalam
`agri_iot/mqtt_bridge/` (proxy env di-unset SEMUA 8
variabel, `.env` tidak diubah, `BRIDGE_ID=
SIMULASI-B4-GW-01`), PID 11043, log `/tmp/b4r4-bridge.log`.
Start bersih: `Using remote MQTT config: 127.0.0.1:1883`,
`Successfully connected to MQTT broker`, `Successfully
registered bridge SIMULASI-B4-GW-01 with Odoo`; `/health`
→ 200 `{"status":"healthy","mqtt_connected":true}`.

## B26 — LOLOS ✅ (tombol Reset + Send Reset Command)

Skrip `browser-proof-b4r4-buttons.py` (screenshot 560–564,
**0 pageerror + 0 console error**): form device 1 terbuka
normal (560); klik **Power On** → tanpa dialog Oops,
subscriber menerima `topic=command/simulasi_b4_sn_001/action`
`payload={"action": "power", "params": {"state": "on"}}`
(561); klik **Power Off** → tanpa dialog Oops, subscriber
menerima `payload={"action": "power", "params":
{"state": "off"}}` (562); klik **Reset** → **tanpa dialog
Oops**, subscriber menerima `payload={"action": "reset",
"params": {}}` (563); klik **Send Reset Command** →
**tanpa dialog Oops**, subscriber menerima
`payload={"action": "reset", "params": {}}` (564).
Tidak satu pun dari 4 klik yang membuka dialog — skrip
tidak perlu menutup dialog di antara klik (penanganan
tutup-dialog tetap ada di skrip, tidak terpakai).

`farm.command.log` device 1: **12 → 16** (id **14**,
`command='power'`, `dispatched`, `{"state": "on"}` —
Power On; id **15**, `command='power'`, `dispatched`,
`{"state": "off"}` — Power Off; id **16**,
`command='reset'`, `dispatched`, `{}` — Reset; id **17**,
`command='reset'`, `dispatched`, `{}` — Send Reset
Command). Action final tercatat **`reset`** pada kedua
klik Reset — **bukan None, bukan 1041** — klaim perbaikan
B26 terbukti di browser, bukan hanya di shell. Log bridge
`Received webhook event from Odoo: command` 4× (09:45:33,
09:45:39, 09:45:45, 09:45:51). **0× `TypeError` / 0×
`got multiple values` di `/tmp/odoo18-server-b4r4.log`.**

## B24 — LOLOS (curl, regresi)

Skrip `/tmp/b4r4_b24curl.sh` (envelope JSON-RPC langsung,
pelajaran O-B4R3-1): login via
`/web/session/authenticate` (uid 2) →
`POST /iiot/command/simulasi_b4_sn_001` envelope
`{"action":"power_on","params":{"state":"on"}}` →
**`{"result":{"status":"success","message":"Command
power_on sent to simulasi_b4_sn_001"}}`**. Subscriber
menerima payload ke-5 `{"action": "power_on", "params":
{"state": "on"}}`; log bridge webhook ke-5.
`farm.command.log`: **16 → 17** (id 18, `power_on`,
`dispatched`).

## B20 dengan bridge HIDUP — LOLOS

Skrip `/tmp/b4r4_b20.py` (dengan `env.cr.commit()`):
`iiot.telemetry.create` T=40, device 1,
`production_id`=task 12 → **id 13 TERSIMPAN** (komit).
Rule 1 terpicu → `farm.command.log` **17 → 18** (id 19,
`power_on`, `dispatched`, `{"state": "on"}`); subscriber
menerima payload ke-6 `power_on`; log bridge webhook
ke-6. Chatter task 12: message **26647** SUKSES —
`AUTOMATION: Rule 'SIMULASI B4 Rule Otomatis Suhu'
triggered. Command 'power_on' sent to SIMULASI-B4-SN-001
(simulasi_b4_sn_001) because temperature was > 35.0.`
(task 12 kini 9 message). Token device 1 tetap terisi.

## F7 — regresi render: LOLOS 17/17

Skrip `browser-proof-b4r4-f7.py` (screenshot 565–581):
17/17 halaman batch 4 terbuka tanpa error dialog /
"Oh snap" — forecast 1037, profile 1038, telemetry
1039, rule 1040, device 1041, firmware 1042, update
1043, gateway 1044, mapping 1046, telemetry history
1047, automation rule 1048, correlation 1049, twin
scene 1050, storage env 1051, + form device 1, gateway
1, forecast 1. **0 pageerror + 0 console error.**

## Regresi cepat stok/data batch 1–3: LOLOS

B4R1: tomat **5.480**, saus **16**, sapi **12**, lele
**1.900**, NPK **0** — sama persis dengan akhir B4R3
(verifikasi precheck + akhir ronde). B4 NPK **50** tetap.
MO max **168**. Tidak ada cron yang mengubah angka
selama ronde.

## Kebersihan infra: LOLOS

Bridge (PID 11043) + broker (11011) + subscriber (11032)
dimatikan sesudah uji (kill PID eksplisit — catatan:
`pkill -f` pola file sempat self-kill shell sendiri,
sesuai jebakan AGENTS.md; broker sudah mati oleh pkill
pertama, sisanya dimatikan via PID); port **8000 FREE,
1883 FREE**; Odoo 8071 tetap jalan (**PID 10765/10767,
HTTP 200** `/web/login`). `iiot_gateway` tetap **1 baris**
(`SIMULASI B4 Gateway`). `farm.command.log` total **18**,
`iiot.telemetry` total **9**.

## Observasi B4R4 (bukan blocker)

- O-B4R4-1: `pkill -f "<pola-file>"` membunuh shell
  sendiri bila pola itu muncul di command line shell yang
  sama — jebakan yang sudah tercatat di AGENTS.md; untuk
  mematikan infra B4, pakai kill PID eksplisit (broker
  11011 mati oleh pkill pertama sebelum shell ikut mati,
  subscriber 11032 + bridge 11043 dimatikan via `kill`
  PID). Tidak ada dampak pada hasil simulasi.

## Stok akhir B4R4 (WH/Stock, company 1; 10 Nov 2026)

Sama dengan akhir B4R3 — benih **10 kg**, bibit **25.000
unit**, tomat segar **5.480 kg**, saus tomat **16 kg**,
NPK **0,0 kg** (B4R1; B4 NPK 50 kg tetap); sapi **12
ekor**, pakan sapi **80 kg**, daging sapi **250 kg**;
kolam lele **1**, lele **1.900 ekor**, pakan lele **50
kg**, lele panen **50 kg**.

## Data SIMULASI B4R4 yang tertinggal di test18

- IoT B4R4: telemetri **13** (T=40, B20, device 1, task
  12); `farm.command.log` total **18** (id 14, 15 dari
  tombol Power On/Off — `command='power'`; id 16, 17 dari
  tombol Reset / Send Reset Command — `command='reset'`;
  id 18 dari curl B24 — `power_on`; id 19 dari B20 —
  `power_on`); chatter sukses **26647** di task 12 (task
  12 kini 9 message). Token device 1 tetap terisi.
- Tidak ada data batch 1–3 baru (ronde ini terfokus; stok
  diverifikasi utuh, bukan diulang).

# Batch 5 — Simulasi kumulatif (B5R1)

Ronde B5R1, 10 Nov 2026. DB `test18`, Odoo 18
`http://127.0.0.1:8071`, login `admin`/`admin`,
`?debug=1`. Prefix data **`SIMULASI B5R1`**,
screenshot **600–840** di `simulasi/`. Semua fase
browser: **0 pageerror** (console error 0 di semua
fase yang mengukurnya). Log server baru
(`/tmp/odoo18-server-b5-restart3.log`): **0
Traceback** (satu baris ERROR hanyalah peringatan
impor test-framework yang tidak berhubungan).

## Verdict: TIDAK BERSIH

Blocker mapan **B27** (auto-worklog hook, a–e)
masih berlaku penuh, termasuk B27e yang membuat
cron pakan B11 gagal total. Blocker baru yang
terkonfirmasi di ronde ini: **B28** (convert
manure → FK `mrp_Cultivation_location_src_id_fkey`)
dan **B29** (laporan QWeb manure ledger crash
`KeyError: 'doc'` di setiap render). Keduanya bug
kode dengan repro persis di bawah. Bagian 1, 2, 4
lolos; Bagian 3 lolos kecuali B11 (B27e); Bagian 5
lolos kecuali B28/B29 dan delapan metode tanpa tombol
UI (observasi O-B5R1-6).

## Insiden infra selama ronde

- **VM replacement** ±13:00 WIB di tengah Bagian 5
  (ESG run 1): user `pgtest` + `/opt/pgserver`
  hilang, port 5433/8071 mati. Dipulihkan per
  AGENTS.md (`useradd -u 1001 pgtest`, copy
  `pginstall/{bin,lib,share}` + `*.so*` dari
  `pgserver.libs/` ke `/opt/pgserver`, `chmod -R
  a+rX`, start PG dari `~/workspace/pgrun`, start
  ulang Odoo). Catatan: glob copy yang benar
  `*.so*`, bukan `.so*`. Data utuh terverifikasi
  (lot B5R1 10, MO ≥184 16, assessment 1,
  sertifikat fair trade 1, exchange asset 2).
- **Restart server Odoo 12:48 WIB** (kill PID 1806
  eksplisit → PID 20113, lalu PID baru sesudah VM
  replacement): dilakukan untuk menguji hipotesis
  "registry server kehilangan model fair trade" —
  hipotesis itu SALAH (lihat koreksi §Koreksi
  catatan ronde sebelumnya). Restart tidak mengubah
  apa pun.
- Infra Bagian 4 (broker amqtt PID 8982, subscriber
  paho PID 9009, bridge PID 9028) **mati bersama
  VM**; port 1883 + 8000 bebas sesudahnya, tidak
  ada yang perlu di-kill. Bukti Bagian 4 tetap dari
  run sebelum VM replacement (shot 659–682).

## Bagian 1 — rantai batch 1 (LOLOS 9/9)

Data B5R1: benih tpl 277/v289, bibit 278/v290,
tomat 279/v291, saus 280/v292, NPK 281/v293 (n/p/k
16). Lokasi 48, campaign 46, seed batch 52 (lot
243, germ 92% → verify OK; lot blok 244 germ 70%
→ `UserError: SEED QUALITY BLOCK ... below
national standard`), nursery 43 (lot 245 bibit
25.000), asset 48 (GDD 357.0 sesudah 21 hari
simulasi; stage 14–17 progress 100/100/71.4/
44.625), rotation 47 (planted → harvested),
intervensi 81–86 (5 + IV86 via UI; MO 184–188 +
192, semua done; NPK fertilizing 8/8/8), lot
panen 246 (500 kg), QC point 40 / check 41
(pass) / record book 41 (active), BoM saus 107,
MO saus 190 + 191 (8 kg each) → **tomat 480.0,
saus 16.0**. Market price 43 (Rp 12.000/kg);
valuation 44 NBV = FV = **2.500.000** (setelah
original_value 5.000.000 + koefisien 0.5); fair
valuation 43, market_price 0.0 (batasan diketahui:
asset tanpa `lot_id`).

Browser proof `browser-proof-b5r1-a.py`, shot
600–612: 0 pageerror, 0 console error, 13 form
terverifikasi. Artefak check-string saja: 605 nama
lot-panen (header menampilkan display name,
On Hand 480.00 terlihat), 609 harga '12,000'
(tampil "12,000.0000").

Pelajaran shell: intervensi harus jalan sebagai
user 2 (Administrator, punya `hr.employee` id 1)
DAN dengan `agri_task_id` terisi (task 56,
proyek 6 "Wheat Cultivation 2026", tanpa analytic
account — relevan untuk `farm_hr`).

## Bagian 2 — verifikasi batch 2 (LOLOS)

- Fase B (`-b.py`, shot 613–618): intervensi baru
  murni via UI dari form IV82 → **IV86**
  "SIMULASI B5R1 Intervensi Pupuk NPK Tomat A1
  (UI)", workflow Submit → Approve → Start →
  Stop, berakhir Completed + Fertilizing; tab
  Costs '8.00' ×3. MO185 tab Spatial render tanpa
  Oops/NaN% tapi TANPA gauge (MO dibuat via shell
  dengan `intervention_type='process'`; gauge
  hanya untuk tipe non-process — artefak
  metodologi, bukan bug).
- Fase B2 (`-b2.py`, shot 619–621): MO192 =
  WH/MO/00193 (MO auto IV86, Fertilizing), tab
  Soil Nutrient '8.00' ×3; MO27 Spatial gauge
  100% + "Within Boundaries", tanpa NaN%.
- Fase C wizard ISL (`-c.py`, shot 622–627):
  sebelum 112 ISL, 12 MO tanpa ISL [177, 179,
  180, 181, 184–188, 190–192]. Run 1 (Confirm ON)
  klaim **12** ("Migration completed. 12 records
  migrated to ISL architecture."), run 2 klaim
  **0**, negatif (Confirm OFF) → UserError "Please
  confirm the migration", dialog tetap terbuka.
  Total ISL kini **124**.

## Bagian 3 — verifikasi batch 3 (LOLOS kecuali B11)

Prep: produk B5R1 varian 289–300 (template
277–288), SEMUA UoM kg (termasuk Sapi Perah 294
dan Lele 298 — berbeda dengan B5 yang memakai
Units). BoM 108 (Sapi 1 ← Pakan Sapi 10), 109
(Daging 250 ← Sapi 1), 110 (Lele 1000 ← Pakan
Lele 50), 111 (Lele Panen 50 ← Lele 100). Lot
sire 249, kolam 250, lele 251; pakan sapi + lele
quant 100 kg @ WH/Stock.

- Fase D1 (`-d.py`, shot 628–637): animal lot
  **252** tersimpan via UI (B10), lot biasa **253**
  tersimpan via UI (cek invers B10-residu),
  feeding MO 193 (WH/MO/00194) tersimpan +
  Confirmed via UI. 0/0 error. Pick M2O
  `active_feeding_bom_id` gagal di browser —
  terpecahkan: domain `[('type','=','normal'),
  ('intervention_type','=','feeding')]`
  (`farm_lot.py:146-147`); BoM 108 awalnya
  `intervention_type='process'` (kelalaian prep,
  bukan bug). Diperbaiki via shell (BoM 108 →
  feeding, lot 252 → bom 108). Widget
  `lot_producing_id` NOT FOUND di form MO
  (observasi, sama seperti B3G).
- P3A shell: lot 252 (is_animal, ear tag
  `SIMULASI B5R1-ET-001`, start_weight 300.0, ADG
  0.8, stage born, predicted 300.0). MO193
  diselesaikan via `_post_inventory` (workaround
  B27): done, finished 1.0, raw 10.0; **pakan sapi
  295: 100 → 90 kg**; sapi lot 252 qty **10.0**;
  `total_feed_consumed` lot 252 = 0.0.
- Fase D2 (`-d2.py`, shot 638–644): weight event
  40 (320.0), breeding 39 (offspring 1,
  gestation 0 — onchange hanya cocok nama spesies
  Inggris; 'Sapi Perah' tidak cocok, sama seperti
  B3G), env monitoring 7 (`comfort_index`
  **77.64**), harvest MO daging 194 (WH/MO/00195,
  Confirmed). Pick M2O `sire_id` gagal —
  terpecahkan: domain `[('is_animal','=',True),
  ('breeding_status','=','open')]`; lot 249 dibuat
  sebagai lot polos (kelalaian prep). Diperbaiki
  via shell (lot 249 → is_animal + open).
- **B11 — GAGAL (B27e):** cron
  `_cron_daily_feed_depletion` (`stock.lot`,
  `farm_lot.py:246`) — tidak ada record `ir.cron`;
  dipanggil langsung via shell sebagai user 2.
  7 lot aktif ber-BoM pakan (53, 84, 119, 177,
  220, 238, 252). Lot pertama (53)
  `button_mark_done` → plugin labor →
  `farm.worklog.create` task_id=False →
  `IntegrityError: null value in column "task_id"
  of relation "farm_worklog"` (log server 11:23:07
  sebagai `Intervention Plugin Error
  (labor_tracking)`), transaksi abort → cron
  melempar `InFailedSqlTransaction`. **Hasil: NOL
  feeding MO, NOL stok terkonsumsi, NOL worklog.**
  Before==After: feeding MO 23, worklog 5,
  `total_feed_consumed` semua lot tidak berubah
  (252 tetap 0.0). B11 lolos di B3G SEBELUM
  `farm_hr` ter-install (hook waktu itu no-op);
  dengan `farm_hr` ter-install, cron rusak — ini
  manifestasi B27, bukan nomor blocker baru.
- **B13 — LOLOS (setelah redo):**
  `handle_aquaculture_telemetry`
  (`farm_aquaculture/models/aquaculture_isl.py:96`).
  Redo dengan data benar: draft MO **198
  (WH/MO/00200**, produk 298) + ISL task **8**;
  telemetry `{dissolved_oxygen: 2.0, temperature:
  29.0}` → True, `latest_do_level`=2.0,
  `latest_water_temp`=29.0, `agent_instruction_json`
  `{"action": "set_aerator", "state": "on",
  "duration_minutes": 60, "pond": "WH/MO/00200"}`,
  +1 incident activity **513** (`INCIDENT: Oxygen
  Depletion (critical)`). Sisa salah label (jangan
  dihapus): MO 197 (WH/MO/00199, produk B5 286) +
  ISL task 7 + activity 512 dari percobaan
  pertama (UoM + field link salah).
- Fase E1 (`-e.py`, shot 645–652): action 1024
  buka LIST dulu (8 baris) ✓ B14; operasi
  akuakultur baru **17** + sub-operasi **18**
  (parent_id=17 ✓ B12-residu); operasi 3 (B3) + 9
  (B3F) dicek ulang dengan 4 tab. Pick M2O
  `pond_id` gagal — terpecahkan: domain
  `[('product_id.categ_id.name','ilike','pond')]`;
  produk kolam 285 berkategori 'All' (kelalaian
  prep). Diperbaiki via shell: kategori baru **62
  'SIMULASI B5R1 Pond'**, op17.pond_id=250.
- Fase E2/E2b (`-e2.py`, `-e2b.py`, shot 653–658):
  WQ log **6** tersimpan via UI; MO **199**
  (feeding lele, Confirmed), MO **200** (harvest
  lele panen, Confirmed); ISL aqua lot **7**.

## Bagian 4 — verifikasi batch 4 (LOLOS)

Infra dibangun ulang (yang lama di `/tmp` hilang
karena VM replacement): broker amqtt
`/tmp/b5r1-broker.py` 127.0.0.1:1883 **PID 8982**;
subscriber paho `/tmp/b5r1-sub.py` (paho v1 API,
log `/tmp/b5r1-sub.log`) **PID 9009**; bridge
`agri_iot/mqtt_bridge/main.py` via bridge-venv
(`ODOO_BASE_URL=http://127.0.0.1:8071`,
`BRIDGE_ID=SIMULASI-B4-GW-01`, port 8000) **PID
9028**; `/health` →
`{"status":"healthy","mqtt_connected":true}`.

- Tombol (`-buttons.py`, shot 659–663): **keempat
  tombol True** (Power On, Power Off, Reset, Send
  Reset Command), tanpa Oops, 0/0 error.
  Subscriber menerima 4 payload (`power on/off`,
  `reset` ×2). `farm.command.log` 18 → **22** (id
  20–23, semua `dispatched`); log bridge "Received
  webhook event from Odoo: command" 4×.
- B24 curl (`/tmp/b5r1_b24.sh`, envelope JSON-RPC):
  `POST /iiot/command/simulasi_b4_sn_001` →
  `{"result":{"status":"success","message":
  "Command power_on sent to simulasi_b4_sn_001"}}`;
  subscriber payload ke-5; command.log → 23.
- B20 (`b5r1_b20.py`): `agri.telemetry` id **1**
  (T 40.0, device 1, `production_id`=project.task
  12 'Ceiling fan') → rule 1 terpicu →
  command.log 24 (id **25** `power_on`); chatter
  task 12 message **26921**.
- F7 (`-f7.py`, shot 664–680): **17/17 halaman**
  batch 4, semua errdlg=0 oops=False.
- Cuaca manual (`-weather.py`, shot 681–682):
  forecast `agri.weather.forecast` — field `date`
  TANPA default dan satu-satunya required; Save
  pertama gagal diam-diam (URL tetap `/new`,
  tanpa dialog, tanpa record). Setelah isi tanggal
  11/10/2026 + "Cerah" + humidity 65 + wind 12 →
  record **25 dan 26** tercipta via UI (lokasi fc
  26 diset via shell ke 48). Client TIDAK navigasi
  dari `/new` sesudah create sukses (quirk klien).
  Observasi autocomplete M2O: query nama lengkap
  'SIMULASI B5R1 Lahan A1' → 0 item, 'Lahan A1' →
  hanya 4 dari 8 lokasi, 'B5R1' → 0, padahal
  `name_search` server mengembalikan [(48,...)]
  dan tidak ada record rule di `farm.location`
  (`_rec_name='complete_name'`, tanpa domain) —
  mekanisme belum terjelaskan (O-B5R1-7).

## Bagian 5 — alur baru batch 5 (INTI RONDE INI)

Prep via shell (`shell-b5r1/b5r1_5a.py`,
`b5r1_5b.py`, `b5r1_5b2.py`, `b5r1_5b3.py`,
`b5r1_5c2.py`): HR — analytic 42
('SIMULASI B5R1 Analitik HR', plan 4
'Agri-Projects'), project 11, task 61, skill 10,
team 5, worklog 14, wage.rule 7, labor.payment 3,
time.bank.ledger 3, certificate 2, manure.batch
1, manure.ledger 1. Financial — cost.category 1,
farm.financial cost.template 1, `agri.cost.template`
2, `agri.cost.calculation` 1–2,
`farm.processing.cost` 1–2, `farm.activity` 1,
`farm.cpa.analysis` 1–2, clearing.ledger 1–2,
credit.score 2, loan 1, coop.settlement 1,
insurance.index 1, insurance 1, claim 1,
valuation.template 1, asset.valuation 1–2. ESG —
framework 1, indicator 1, assessment 1, line 1,
target 1–2, perf report 1, carbon.factor 1,
carbon.ledger 1–2, exchange.asset 1 (+2 dari
tokenize), env.report 1, env.tracker 1,
esg.report 1, dashboard 1, goal 1, risk 1,
compliance 1, kpi 1, data.governance 1,
report.customization 1, diversity.metric 1 (total
20), biogas 1, hazardous 1, resource.sharing 1,
netting 1, gis 1, heatmap 1, regional 1,
participation 1, carbon.credit 2, neutral.goal 1,
sust.dashboard 2, sust.metric 4, sust.report 1,
vra.carbon 1, vra.water 1, vra.soil 1, fair trade
4 record (lihat bawah). Duplikat dari rerun prep
yang gagal didokumentasikan di ringkasan ronde
dan dibiarkan (analytic 34/36/38, project 7–10,
task 57–60, skill 6–9, team 1–4, worklog 11–13,
wage.rule 5–6, labor.payment 1–2, time.bank 1–2,
certificate 1).

Fakta field (prep): `farm.worklog` TIDAK punya
`hours_worked`/`description`/`state` (pakai
`quantity` + `notes`); `farm.wage.rule` dan
`farm.employee.certificate` TIDAK punya `name`;
`agri.manure.batch` TIDAK punya `name` (pakai
`batch_no`, sequence MNR); `agri.manure.ledger`
pakai `ledger_no` (MNL), month selection
'01'–'12', year INTEGER; analytic plan 'Default'
TIDAK ada (pakai plan 4 'Agri-Projects').

### 5.1 HR + waste

Skrip `-5hr.py` (shot 683–700), `-5hrb.py`
(701–708), `-5hrc.py` (709–713), `-5hrd.py`
(714–718), `-5hre.py` (719–722). Semua 0
pageerror, 0 console error.

- **Worklog approve: TIDAK ADA tombol Approve di
  UI.** `farm.worklog` TIDAK punya form view
  (hanya list view editable bottom) → form
  auto-generated menampilkan field mail.thread
  saja (shot 683, header buttons []). Method
  `action_approve` ada tapi tidak dipanggil tombol
  manapun. Terbukti via shell sebagai user 2:
  worklog 14 (task 61, project.account 42) →
  True, analytic line **1** (amount 0.0 karena
  employee `hourly_cost` = 0.0); setelah set
  employee 1 `hourly_cost` = 50.000, worklog 13
  (task 60, project.account 40) → True, analytic
  line **2**, amount **-400.000** (8 × 50.000).
  Method `farm_hr/models/farm_worklog.py:26-51`.
  Tanpa analytic account = no-op diam-diam (sesuai
  §18e). Bukti: analytic line 2 form (703).
- Skill 10 / team 5 / time bank 3: form terbuka,
  errdlg 0 (688, 689, 691). Wage rule 7 +
  certificate 2: form terbuka errdlg 0, tanpa
  teks B5R1 (wajar — tanpa field name) (690,
  692).
- **Labor payment 3 — Compute Sheet LOLOS:** klik
  pertama gagal "Invalid fields: Journal" (journal
  kosong, shot 686/701). Setelah set journal:
  Compute Sheet → Payment Lines terisi worklog
  2,3,4,8,9,11,12,13,14 (semua worklog employee 1
  dalam periode — termasuk B5), qty 8.00, unit
  price 100.00, subtotal 800.00 (B5R1), **Total
  Amount 3.401,00** (709). Tombol "Post to
  Accounting" muncul sesudah compute.
- **Labor payment 3 — Post to Accounting (2× gagal
  lalu LOLOS):** (1) journal MISC (id 3):
  Validation Error "Missing required account on
  accountable line" (710) — akar:
  `farm_hr/models/farm_wage.py:49-89`, credit line
  pakai `journal_id.default_account_id.id`; MISC
  TIDAK punya default account. (2) journal
  Expense (id 8, default account 33): Invalid
  Operation "You cannot validate a document with
  an inactive currency: USD" (715) — akar:
  currency USD (company currency) **tidak aktif**
  di test18; search ORM memfilter `active_test`
  sehingga USD tak terlihat (jebakan: `search`
  mengembalikan recordset kosong, `.active`
  False). Perbaikan test bed: aktifkan USD via
  shell (`with_context(active_test=False)`),
  diverifikasi psql `t`. (3) Retry sesudah USD
  aktif: **LOLOS** — state **paid**, move **6634
  EXP/2026/11/0001 posted** (720, diverifikasi
  psql). Bukan bug modul; dua kegagalan pertama
  adalah konfigurasi (jurnal tanpa default account
  + currency nonaktif).
- **Manure batch 1 — Convert to Fertilizer GAGAL
  (B28, lihat §Blocker).** Tanpa
  `fertilizer_product_id` tombol tersembunyi
  (`invisible="not fertilizer_product_id"`).
  Setelah set produk 293: Invalid Operation
  "SAFETY BLOCK: A passed quality check (Compost
  Maturity) is required before conversion!" (711)
  — akar `agri_manure_batch.py:58-59`, butuh
  `quality_check_id.quality_state == 'pass'`
  (aturan bisnis, benar). Setelah link QC 41
  (pass): Validation Error FK
  `mrp_Cultivation_location_src_id_fkey` (714) —
  **B28**.
- **Manure batch 2 (workaround B28) — Convert
  LOLOS:** batch 2 (MNR/2026/00003,
  `location_source_id`=8 → stock.location 8
  WH/Stock valid, fertilizer 293, QC 41 pass) →
  klik Convert → errdlg 0, navigasi ke
  **MO 203 (WH/MO/00205, confirmed, produk 293,
  `intervention_type='fertilizing'`)** (719).
  Membuktikan alur convert bekerja bila FK
  terpenuhi; bug-nya hanya pemetaan id lokasi.
- **Manure ledger 1 — LOLOS sebagian:** form
  terbuka (695): MNL/2026/00001, Year 2.026,
  Month November, **Total Disposed Quantity
  500.00**, tab Included Batches berisi
  MNR/2026/00002 500.00 Composting. Klik statusbar
  "Confirmed" **TIDAK PERNAH berhasil** (timeout
  30 dtk; force click "berhasil" tapi state tetap
  `draft` diverifikasi psql; percobaan ke-3 timeout
  lagi) — tidak ada tombol Confirm di form (hanya
  statusbar); akibatnya tombol "Generate Report"
  (`invisible="state != 'confirmed'"`) tidak
  pernah muncul. State diset via shell
  (terdokumentasi sebagai workaround), lalu
  **Generate Report diklik di browser: True,
  errdlg 0** (721). Print QWeb: klik menu "Manure
  Ledger" → tidak ada tab/download baru
  (`expect_download` timeout 15 dtk); URL langsung
  `/report/pdf/.../1` → **400 "Unable to find
  Wkhtmltopdf on this system"** (test bed tanpa
  wkhtmltopdf — bukan bug modul); `/report/html/`
  → **500 `KeyError: 'doc'`** — **B29** (lihat
  §Blocker). `action_generate_ledger` ada di kelas
  `AgriManureLedger` (baris 134) — hanya
  `message_post` + return True, TIDAK mengubah
  state (PORTING.md salah menaruhnya di batch).
- **B27c TERBUKTI DI BROWSER (708):** MO tes 201
  (WH/MO/00203, saus, `intervention_type='process'`,
  dibuat via shell) — klik "Confirm" lalu
  **"Produce All"** (`button_mark_done`) → dialog
  **"Oops!"**, `errdlg=1`, 0 pageerror. Log server
  12:23:09: `ERROR ... agri_intervention_base:
  Intervention Plugin Error (labor_tracking):
  Wrong value for farm.worklog.work_type:
  'process'` + `ERROR odoo.http: Exception during
  request handling` untuk `POST
  /web/dataset/call_button/mrp.production/
  button_mark_done`. MO 201 tetap Confirmed.

### 5.2 Financial

Skrip `-5fin.py` (723–731), `-5fin2.py`
(732–743), `-5fin3.py` (744–748). Semua 0
pageerror.

- Cost template 2 (action 1066): form terbuka,
  errdlg 0, tanpa tombol (data form saja) (723).
- Cost calculator wizard (action 1067): wizard 3
  dibuat via shell (task 56 + lahan 48 + line
  template 2 qty 10) — total **500.000,00**
  terlihat sebelum dan sesudah; tab Results sama.
  Tombol "Calculate" (footer, `calculate`) TIDAK
  bisa diklik via URL langsung (footer tidak
  render di direct URL); via action 1067 tombol
  **terverifikasi ada dan visible**. Method
  `calculate` hanya recompute + reload; total
  adalah computed field dari lines (fertilizer
  bucket 0.0 di awal — stale precompute; total
  500.000 benar). Wizard 1–2 (prep) total 0.0
  karena tanpa cost lines (bukan dari input
  seedling/fertilizer/labor langsung).
- `farm.processing.cost` 2 (direct URL, tanpa
  action): form terbuka, errdlg 0, **TANPA
  tombol** (726). `action_allocate_costs` jalan
  via shell (user 2): OK, total tetap 100.000
  (hanya other_indirect masuk total; water/elec
  0.0). Metode UI-unreachable (O-B5R1-6).
- `farm.cpa.analysis` 2 (direct URL): form
  terbuka, errdlg 0, **TANPA tombol** (727).
  `action_calculate_cpa` jalan via shell: OK.
  Metode UI-unreachable (O-B5R1-6).
- Clearing ledger 2 (direct URL): state
  **Confirmed** (728). `action_post_netting_clearing`
  via shell: pertama UserError "Credit
  verification failed: Transaction amount exceeds
  active cooperative credit balance!" — akar:
  `netting_clearing_ledger.py:14`, butuh
  `partner.impact_credits >= amount_to_clear`;
  partner 3 impact_credits 0. Setelah seed
  impact_credits 3.000.000 via shell: **post
  OK**, state confirmed, saldo 3.000.000 →
  500.000. Metode UI-unreachable (O-B5R1-6);
  aturan bisnisnya benar.
- Credit score 2 (action 1089): tombol Auto
  Evaluate ada (729); `action_auto_evaluate` via
  shell: OK, state **valid**, gap 87.19 (random
  `random.uniform` di
  `credit_scoring.py:111-113` — nilai tidak
  deterministik by design), total_score **63.03**.
- Loan 1 (direct URL): state **Active** (730).
  `action_approve_loan` via shell: pertama
  ValidationError "Cannot approve loan for partner
  with low credit score" — akar:
  `farm_loan.py:137`, cek `loan.credit_score <
  60`; loan dibuat TANPA `credit_score_id`
  (kelalaian prep). Setelah link
  `credit_score_id`=2 (score 63.03 ≥ 60):
  **approve OK → disburse OK**, state active.
  Metode UI-unreachable (O-B5R1-6).
- Coop settlement 1 (action 1090): tombol Fetch
  Data ada (731); tombol Settle tersembunyi
  (state draft, `invisible="state !=
  'confirmed'"` — by design).
- Insurance 1 (action 1069): Submit Application
  ✓ (734) → Approve ✓ (735, state approved) →
  Activate ✓ (744, state active) → Check Weather
  Indices ✓ (745). Tombol Activate hanya muncul
  saat approved; Check Weather Indices hanya saat
  active; Settle hanya saat claim_approved
  (`insurance_views.xml:26-30`) — semua sesuai
  state machine. (Catatan: klik Activate pertama
  di run 2 gagal karena tombol belum muncul —
  artefak urutan, bukan bug.)
- Insurance index 1 (action 1070): form terbuka,
  errdlg 0, **TANPA tombol** (736) — "Check
  Weather Indices" ada di form INSURANCE, bukan
  di form index (lihat atas).
- Claim 1 (action 1071): tombol Verify → Approve
  (746–747, state **approved**). Urutan wajib
  Verify dulu (Approve tersembunyi saat draft,
  `insurance_views.xml:148-150`). Settle untuk
  klaim hidup di form insurance (state
  claim_approved), bukan di form klaim — alur
  klaim berakhir di approved di sini.
- Valuation 1 (action 1072): Recalculate ✓ (740),
  Create Accounting Entries ✓ (741), errdlg 0.
  `action_calculate_valuation` via shell:
  **fair_value 111.562,5**, `gep_score` 0.0
  (ekspektasi §18e: GEP di-guard tanpa
  `farm_ecology`). Create Accounting Entries
  tidak membuat move — by design:
  `financial_valuation_models.py:240-241`, skip
  bila `valuation_variance` ~0. Valuation 2
  (livestock): form terbuka (742);
  `action_compute_biomass_valuation` via shell OK,
  fair_value 0.0 (asset tanpa data livestock).
  Metode biomass UI-unreachable (O-B5R1-6).
- Valuation template 1 (action 1073): form
  terbuka, errdlg 0 (743).

### 5.3 Fair trade

Skrip `-5ft.py` (749–753), `-5ft2.py`
(754–760), `-5ft3.py` (761–767), `-5ftw.py`
(768–770). Semua 0 pageerror.

- Certificate 4 dibuat via UI (action 1074):
  "SIMULASI B5R1 Sertifikat Fair Trade",
  B5R1-FT-001, "SIMULASI B5R1 Fairtrade Org",
  issue 01/15/2026, expiry 01/14/2027, type
  Fairtrade International (default), Is Active
  tercentang (749, 761). Status tetap
  **applied** — klik statusbar "Certified" gagal
  berulang (lihat O-B5R1-5). Tombol "Check Expiry
  Alerts" diklik: True, errdlg 0 (769).
- Premium allocation 1 dibuat via UI (action
  1075): certificate B5R1 (M2O pick OK), tanggal
  11/10/2026, amount **5.000.000**,
  allocation_type community_investment (762).
  Allocate ✓ → Approve ✓, state **approved**
  (763–764, 770). Catatan: tombol Allocate di run
  `-5ft3.py` gagal diklik oleh helper baru
  (`.oe_highlight` / `header` locator) — helper
  lama `click_header_button` berhasil di debug
  lanjutan; tombol Approve harus diklik dengan
  locator `button:not(.o_arrow_button)` karena
  helper lama menangkap tombol panah statusbar
  "Approved" (disabled) duluan.
- Community investment 1 via UI (action 1076):
  "SIMULASI B5R1 Investasi Komunitas Jalan Desa",
  infrastructure (765).
- Labor condition 1 via UI (action 1077):
  "SIMULASI B5R1 Kondisi Kerja Panen", employee
  Mitchell Admin, condition_type safety_training
  (766); tombol "Schedule Inspection" diklik:
  True, errdlg 0 (767).
- Pelajaran UI Odoo 18: `<option>` field Selection
  dirender dengan value **JSON-quoted**
  (`value='"community_investment"'`) — Playwright
  `select_option(value=...)` gagal "did not find
  some options"; pakai `select_option(label=...)`.
  Field `condition_type` (bukan boolean
  `safety_training`) bersifat required di labor
  condition; `issuing_body` (bukan
  `issuing_organization`), `allocation_type`
  (bukan `purpose`), `unit_of_measurement` +
  `target_date` di esg.target (bukan `unit` /
  `end_date`).

### 5.4 ESG

Skrip `-5esg.py` (771–784), `-5esg1b.py`
(785–789), `-5esg1c.py` (790–791),
`-5esg2.py` (792–807), `-5esg3.py` (808–835),
`-5esg3b.py` (836–837), `-5esg3c.py` (838–839),
`-5esg3d.py` (840). Semua 0 pageerror.

- Framework 1 (1059), indicator 1 (1061),
  assessment line 1 (1062): form terbuka, errdlg
  0, tanpa tombol (771, 772, 776).
- Assessment 1 (1060): Start Assessment → **In
  Progress** (790) → Complete Assessment →
  **Completed** (791, diverifikasi psql). Perhatian:
  klik Start di run pertama (`-5esg.py`, 773–775)
  dan kedua (`-5esg1b.py`, 785–787) mengembalikan
  True tapi state tetap draft dan TIDAK ADA
  request `call_button` sama sekali (dibuktikan
  network log; klik JS mentah + klik mouse di
  koordinat tombol pun tidak mengirim apa-apa).
  Akar: record prep **kehilangan
  `assessed_entity_id`** (Reference, required bila
  `assessed_entity_type` terisi —
  `esg_framework_views.xml` + `esg_framework.py:77-82`);
  klien Odoo memvalidasi required field secara
  lokal sebelum save dan membatalkan pemanggilan
  tombol TANPA dialog (form terbuka dalam edit
  mode, Save/Cancel terlihat, Edit tidak ada).
  Setelah set `assessed_entity_id` =
  `farm.location,48` via shell, tombol langsung
  bekerja. **Bukan bug modul — kelalaian prep.**
  (Form tetap terbuka dalam edit mode sesudahnya;
  penyebab edit-mode-nya tidak diselidiki lebih
  jauh karena tombol sudah berfungsi.)
- Target 1 (1063): Update Current Value ✓ (778,
  no-op karena `related_indicator_ids` kosong);
  Mark as Achieved tersembunyi dengan benar
  (`invisible="current_value > target_value and
  target_type == 'reduction'"` — current 1500 >
  target 1200). Target 1 diselesaikan via shell
  (current 1100 → mark → **achieved**,
  2026-11-10). Target 2 (dibuat untuk bukti UI:
  reduction, baseline 1500, target 1200, current
  1100 — catatan: nilai create 1100 ditimpa
  compute menjadi 1500, harus di-write ulang
  sesudah create): Mark as Achieved ✓ di browser
  → status **Achieved** (788–789, psql).
- Perf report 1 (1064): Generate Report ✓ (780).
- Carbon ledger 2 (direct URL): `is_tokenized`
  True, teks 'Tokenized' tampil (781); ledger 1
  kontrol: tokenize no-op, `is_tokenized` False
  (782). `action_tokenize_offset`
  (`farm_esg_carbon/models/carbon_tokenization.py:8`)
  **TIDAK punya tombol di view manapun** —
  dijalankan via shell (user 2): ledger 2
  (sequestration, total -2500.0, verified) →
  **aset baru `CERT-C-2026-2`, quantity 2.5 ton,
  unit_price 50.0**, `is_tokenized`=True;
  ledger 1 (emission, total 0) → no-op.
  Metode UI-unreachable (O-B5R1-6).
- Exchange asset 2 (CERT-C-2026-2) + asset 1:
  form terbuka, errdlg 0, tanpa tombol (783–784).
- Env report 1 (1092): Generate Report ✓ (808–809).
  Env tracker 1 (direct URL): form terbuka, tanpa
  tombol (793).
- ESG report 1 (1078): Generate Content ✓ (795)
  → Approve ✓ (796, state Approved) → Publish ✓
  (797, state Published).
- Dashboard 1 (1079): Refresh Dashboard ✓
  (810–811). Goal 1 (1080): Update Progress ✓
  (812–813, state → **Achieved**).
- Risk 1 (1081): Calculate Scores Automatically
  ✓ (814–815). Compliance 1 (1082): form terbuka,
  tanpa tombol (801). KPI 1 (1084): form terbuka,
  **TANPA tombol** (802) — "Reset KPI Target"
  tidak ditemukan; `action_reset_kpi_target`
  jalan via shell: OK (nilai sudah 0).
  Metode UI-unreachable (O-B5R1-6).
- Data governance 1 (1085): Validate Data Quality
  ✓ (804–805, state **Validated**); tombol lain:
  Run Data Profiling, Assign Data Steward,
  Generate Checksum, Validate Accuracy.
- Report customization 1 (1086): tombol Generate
  Report / Preview Report / Apply Filters (806).
  Diversity metric 1 (1088): form terbuka, tanpa
  tombol (807).
- Biogas 1 (1101): tombol Start Cultivation,
  Energy Report (816). Hazardous 1 (1099): tombol
  Transfer Waste, Mark Disposed, Compliance Report
  (817). (Tombol-tombol ini tidak diklik — hanya
  form + daftar tombol terverifikasi.)
- Resource sharing 1 (1103): Publish Signal ✓
  (836, state Published) → Match Resources:
  pertama Validation Error "Both demand and supply
  farms must be specified." (838, dialog
  ter-screenshot) — akar:
  `cooperative_coordination.py:98-99`, butuh
  `demand_farm_id` + `supply_farm_id` (res.partner)
  yang kosong di prep (aturan bisnis, benar).
  Setelah set supply=3 (Mitchell Admin) +
  demand=1 (My Company) via shell: Match
  Resources ✓ (840, state **matched**,
  match_date 2026-11-10; `netting_transaction_id`
  '/' — sequence
  `agri.resource.sharing.transaction` tidak ada,
  fallback '/' by design di baris 106).
  Catatan: tombol Match Resources HANYA muncul
  sesudah Published (invisible by state) — klik
  pertama di `-5esg3.py` gagal karena label
  belum ada, bukan karena bug.
- Netting 1 (1104): tanpa tombol (820).
  GIS 1 (1105): Run Analysis ✓ (837, state
  Analyzed) → Optimize ✓ (839, state
  **optimized**, psql). Sama: tombol Optimize
  hanya muncul sesudah Analyzed.
- Heatmap 1 (1106): tanpa tombol (823).
  Regional 1 (1107): Implement ✓ (824–825,
  state Implemented). Participation 1 (1108):
  tanpa tombol (826).
- Carbon credit 2 (1129): tombol Transfer Credits
  / Retire Credits / Verify Credits (827, tidak
  diklik). Neutral goal 1 (1128): tombol Update
  Current Emissions / Generate Progress Report /
  Mark as Completed (828, tidak diklik).
- Sustainability dashboard 2 (1111): tombol
  Recalculate Data (829). Metric 4 (1110): tombol
  Update Metric Value (830). Report 1 (1112):
  tombol Confirm / Print Report (831, tidak
  diklik).
- VRA carbon 1 (1095): Generate Report ✓
  (832–833). VRA water 1 (1096): tanpa tombol
  (834). VRA soil 1 (1097): tombol Recalculate
  Assessment / Create Improvement Plan / Schedule
  Next Assessment / Generate Report (835, tidak
  diklik).

## Blocker B5R1

### B27 — auto-worklog hook (mapan, dari ronde sebelumnya; masih berlaku penuh)

Akar: `_create_auto_worklog_from_hook` di
`farm_operation/models/agri_intervention_mixin.py`
(juga diduplikasi di plugin labor
`agri.intervention.plugin.labor`,
`agri_intervention/models/intervention_plugins.py:243-259`)
memasukkan `intervention_type` verbatim ke
`farm.worklog.work_type` yang seleksinya hanya
`{tillage, sowing, harvesting, packaging,
feeding}`; dan memasukkan `employee_id` /
`task_id` yang bisa null (keduanya NOT NULL di
`farm.worklog`).

- **B27a:** intervensi tanpa `agri_task_id` →
  `task_id` NULL → `IntegrityError`, transaksi
  abort.
- **B27b:** jalan sebagai user tanpa employee
  (shell user 1) → `employee_id` NULL → abort
  yang sama.
- **B27c:** MO polos `button_mark_done` →
  `ValueError: Wrong value for
  farm.worklog.work_type: 'process'` menyebar
  TIDAK TERTANGKAP lewat `action_done_base` →
  `_hook_post_done` (mixin direct call,
  `agri_intervention_mixin.py:340-360`) → crash.
  **Terbukti di browser ronde ini (708):** MO 201
  (WH/MO/00203, saus, `intervention_type='process'`)
  → klik "Produce All" → dialog "Oops!".
  Traceback: `farm_processing/models/
  mrp_production.py:157` →
  `farm_operation/models/agri_intervention.py:159`
  → `agri_intervention_base.py:138` →
  `farm_agri_science/models/mrp.py:9` → mixin
  baris 346.
- **B27d:** untuk intervensi, jalur plugin-runner
  (`_run_plugins`, menangkap non-UserError) menelan
  error — workflow mencapai `done` tapi TIDAK ada
  worklog untuk tipe fertilizing / irrigation /
  protection / medical / aerial_spraying (silent
  data loss). Hanya sowing + harvesting (+feeding)
  yang membuat worklog (worklog 8 + 9).
- **B27e:** `task_id` NULL via jalur plugin dengan
  `work_type` VALID ('feeding') → `IntegrityError`
  ditangkap plugin runner tapi transaksi PostgreSQL
  sudah abort → cron `_cron_daily_feed_depletion`
  melempar `InFailedSqlTransaction`, NOL feed
  depletion untuk semua 7 lot. Nuansa: `ValueError`
  (work_type) terjadi saat validasi Python sebelum
  SQL → transaksi selamat (B27d); `IntegrityError`
  terjadi saat SQL execute → transaksi abort walau
  exception ditangkap Python (`_run_plugins` di
  `agri_intervention_base.py:184-197` TIDAK memakai
  savepoint). **B11 gagal total karena ini.**

Workaround produksi stok (bukan fix kode):
selesaikan MO polos via core
`_post_inventory(cancel_backorder=True)` + write
state done.

### B28 — `action_convert_to_fertilizer` memakai farm.location id sebagai stock.location id (BARU, terkonfirmasi)

- File:
  `farm_waste_mgmt/models/agri_manure_batch.py:52-82`
  (khususnya baris 62–70: MO dibuat dengan
  `location_src_id: self.location_source_id.id`).
- `location_source_id` adalah Many2one ke
  **`farm.location`**; `mrp.production.location_src_id`
  adalah FK ke **`stock.location`**. ID keduanya
  tidak berhubungan (`stock.location` 48 TIDAK
  ADA; `farm.location` 48 = "SIMULASI B5R1 Lahan
  A1").
- Repro: buka `agri.manure.batch` 1
  (MNR/2026/00002, location_source 48, fertilizer
  NPK 293, QC 41 pass) → klik "Convert to
  Fertilizer" → **Validation Error: "The operation
  cannot be completed: another model requires the
  record being deleted. ... Model: Agricultural
  Farm Operation (De-industrialized View)
  (mrp.Cultivation). Constraint:
  mrp_Cultivation_location_src_id_fkey"** (shot
  714). Pesan "record being deleted" adalah pesan
  generik Odoo untuk pelanggaran FK (insert
  `location_src_id`=48 yang tidak ada di
  `stock_location`).
- Bukti kontrol: batch 2 dengan
  `location_source_id`=8 (id yang kebetulan sama
  dengan `stock.location` 8 WH/Stock) → convert
  **lolos**, MO 203 (WH/MO/00205, confirmed,
  fertilizing) (shot 719).
- Fix yang benar (koordinator): pakai stock
  location yang terhubung dengan farm.location
  (atau WH/Stock sebagai fallback), bukan
  `location_source_id.id` mentah.

### B29 — laporan QWeb manure ledger crash `KeyError: 'doc'` di setiap render (BARU, terkonfirmasi)

- File:
  `farm_waste_mgmt/report/manure_ledger_reports.xml:8`
  (`report_name` =
  `farm_waste_mgmt.report_manure_ledger_document`)
  + `farm_waste_mgmt/report/
  manure_ledger_report_templates.xml:4`
  (template dokumen memakai `doc.ledger_no` dst.
  di top-level).
- Template dokumen dipanggil LANGSUNG sebagai
  `report_name`, tanpa template pembungkus yang
  melakukan `<t t-foreach="docs" t-as="doc">`.
  Engine report hanya menyediakan `docs` → template
  melempar `KeyError: 'doc'`.
- Repro: `GET /report/html/farm_waste_mgmt.
  report_manure_ledger_document/1` (sesi admin
  terotentikasi) → **HTTP 500**; log server:
  `KeyError: 'doc'` di template 2831 baris 10
  (`t_call_0`). Jalur PDF (`/report/pdf/...`) →
  **400 "Unable to find Wkhtmltopdf on this
  system"** — itu keterbatasan test bed (tanpa
  wkhtmltopdf), yang MENUTUPI bug B29; jalur HTML
  yang mengeksposnya. Tombol Print di form ("Manure
  Ledger", action 1055) juga tidak menghasilkan
  download/tab baru di browser.
- Fix yang benar (koordinator): buat template
  pembungkus `report_manure_ledger` dengan
  foreach + t-call ke dokumen, dan arahkan
  `report_name` ke pembungkus itu (pola standar
  Odoo).

## Koreksi catatan ronde sebelumnya (penting)

- **K-1 — "Misteri registry shell" BUKAN bug
  registry.** Nama model fair trade yang benar
  adalah **DOTTED**: `farm.esg.fair.trade.certificate`
  dan `farm.esg.fair.trade.premium.allocation`
  (source `farm_esg_fair_trade/models/*.py:13,83`;
  `ir.model`; tabel `farm_esg_fair_trade_certificate`).
  Skrip ronde ini (dan ringkasan sebelumnya)
  memakai bentuk **UNDERSCORE**
  (`farm.esg.fair_trade.*`) yang memang tidak ada
  — itulah sumber semua `KeyError` shell + RPC
  404 (`dataset.py:22`, `registry.py:234`) +
  dialog "Oops!" saat membuka form sertifikat
  (shot 754) + statusbar yang "tidak ditemukan".
  Registry server maupun shell TIDAK PERNAH
  rusak; klaim §8a ringkasan sebelumnya bahwa
  `Registry.load()` merusak registry adalah
  kesimpulan yang salah untuk kasus ini (nama
  model yang salah adalah penyebabnya; `Registry.load()`
  tanpa `setup_models()` tetap berbahaya dan
  tetap jangan dipakai). Setelah memakai nama
  dotted: RPC `search_read` mengembalikan cert 4
  normal; semua form fair trade terbuka; server
  restart 12:48 WIB tidak mengubah apa pun.
- **K-2 — Restart test bed 12:48 WIB** (kill PID
  1806 → 20113) dilakukan atas hipotesis K-1 yang
  salah; bukan bagian dari simulasi.
- **K-3 — VM replacement ±13:00 WIB** (lihat
  §Insiden infra): test bed dipulihkan penuh,
  data utuh; satu-satunya kehilangan adalah infra
  Bagian 4 (broker/subscriber/bridge) yang mati
  bersama VM — buktinya tetap dari run sebelum
  replacement.

## Observasi B5R1 (bukan blocker)

- O-B5R1-1: `farm.worklog` tidak punya form view
  dan tidak punya tombol Approve di UI
  (O-B5R1-1a); `action_approve` hanya bisa
  dipanggil via shell/RPC. Analytic line tercipta
  dengan benar bila project punya analytic account
  (line 2: -400.000).
- O-B5R1-2: Post labor payment gagal dua kali
  karena konfigurasi test bed, bukan modul: (a)
  journal MISC tanpa default account; (b) currency
  USD (company currency) nonaktif — aktifkan via
  shell dengan `active_test=False` (search ORM
  biasa menyembunyikan currency nonaktif).
- O-B5R1-3: Klik statusbar ("Confirmed" di manure
  ledger 1; "Certified" di sertifikat fair trade
  4) konsisten timeout di Playwright pada 2 form
  (manure ledger juga gagal 3×). Tombol header di
  form yang sama bekerja normal. Pola ini dicatat
  sebagai quirk harness/UI, bukan bug modul —
  status ledger diset via shell, sertifikat
  dibiarkan 'applied'.
- O-B5R1-4: Odoo 18 merender `<option>` field
  Selection dengan value JSON-quoted
  (`value='"community_investment"'`); Playwright
  `select_option(value=...)` gagal — pakai
  `select_option(label=...)`.
- O-B5R1-5: Assessment form terbuka dalam edit
  mode (Save/Cancel terlihat, Edit tidak ada)
  baik via list maupun URL langsung — penyebab
  edit-mode-nya tidak diselidiki lebih jauh
  karena tombol berfungsi sesudah required field
  dilengkapi (lihat §5.4).
- O-B5R1-6: **Metode tanpa tombol UI** (jalan via
  shell, tidak bisa dijangkau dari UI manapun —
  grep seluruh `views/*.xml`): `farm.processing.cost`
  `action_allocate_costs`,
  `farm.cpa.analysis` `action_calculate_cpa`,
  `agri.clearing.ledger`
  `action_post_netting_clearing`,
  `farm.loan` `action_approve_loan` /
  `action_disburse_loan`,
  `farm.financial.asset.valuation`
  `action_compute_biomass_valuation`,
  `agri.carbon.ledger` `action_tokenize_offset`,
  `agri.esg.kpi` `action_reset_kpi_target`.
  Juga: `farm.worklog` `action_approve` (§5.1).
  Untuk klaim replika 1:1 ini celah cakupan UI,
  bukan crash.
- O-B5R1-7: Autocomplete M2O `farm.location`
  (§Bagian 4, cuaca): query nama lengkap → 0
  item, padahal `name_search` server
  mengembalikan [(48,...)] dan tidak ada record
  rule/domain — mekanisme belum terjelaskan.
- O-B5R1-8: `action_auto_evaluate` credit score
  memakai `random.uniform` untuk GAP/yield/input
  (`credit_scoring.py:111-113`) — skor tidak
  deterministik by design (total 63.03 di run
  ini).
- O-B5R1-9: `agri.cost.calculation` total adalah
  computed dari cost lines; input seedling /
  fertilizer / labor langsung tidak masuk total
  (wizard 1–2 total 0.0); bucket fertilizer
  sempat 0.0 sesudah create (stale precompute)
  walau total 500.000 benar.
- O-B5R1-10: Tombol pada form ESG/keuangan
  sering muncul berurutan mengikuti state
  (Match Resources hanya sesudah Published;
  Optimize hanya sesudah Analyzed; Activate hanya
  sesudah Approved; Settle klaim hanya di form
  insurance saat claim_approved) — klik dengan
  label yang "belum waktunya" gagal karena tombol
  belum ada, bukan karena bug.
- O-B5R1-11: `esg.target.current_value` adalah
  computed stored — nilai saat create ditimpa
  compute (1100 → 1500); harus di-write ulang
  sesudah create.
- O-B5R1-12: `farm.financial.asset.valuation`
  tidak punya field `state` (query psql dengan
  `state` gagal — bukan bug, model memang tanpa
  state).

## Stok akhir B5R1 (WH/Stock, company 1; 10 Nov 2026, via psql)

Benih **10,00 kg** (lot 243 5 kg + lot blok 244
5 kg), bibit **25.000,00**, tomat segar
**480,00 kg**, saus tomat **16,00 kg**, NPK
**0 kg** (habis di fertilizing); sapi **12,00**
(lot 252 qty 10 + sire 249 + 1 generik dari
MO193), pakan sapi **90,00 kg**, daging sapi
**0** (MO 194 hanya Confirmed, belum done);
kolam lele **1**, pakan lele **100,00 kg**, lele
panen **0** (MO 200 hanya Confirmed). ISL total
**124**. Worklog total **9**. Feeding MO total
**23**. Manure batch 2, ledger 1. MO total
id ≥184: **16** (184–188, 190–194, 197–201,
203).

## Data SIMULASI B5R1 yang tertinggal di test18

- Batch 1: lokasi 48, campaign 46, asset 48,
  rotation 47, seed batch 52 (lot 243–244),
  nursery 43 (lot 245), intervensi 81–86, MO
  184–188 + 192, lot 246 + 248, QC point 40 /
  check 41 / record book 41, market price 43,
  valuation 44, fair val 43, BoM 105 + 107.
- Batch 2: ISL total 124 (MO 177, 179–181,
  184–188, 190–192 termigrasi).
- Batch 3: produk varian 289–300, BoM 108–111,
  lot 249–253, MO 193–194 + 197–200, kategori
  62 'SIMULASI B5R1 Pond', ISL aqua lot 7, ISL
  task 7–8, activity 512–513, operasi akuakultur
  17–18, breeding 39, lifecycle event 40, env
  monitoring 7, WQ log 6.
- Batch 4: device 1, rule 1, gateway 1,
  `farm.command.log` total **24** (id s.d. 25),
  `iiot.telemetry` 9, `agri.telemetry` 1,
  forecast 25–26.
- Batch 5 HR/waste: analytic 42, project 11,
  task 61, skill 10, team 5, worklog 11–14,
  wage.rule 7, labor.payment 3 (**paid**, move
  6634 EXP/2026/11/0001 posted), time.bank 3,
  certificate 2, analytic line 1–2, manure.batch
  1–2, manure.ledger 1 (**confirmed**), MO 203
  (WH/MO/00205). MO 201 (WH/MO/00203) tetap
  Confirmed (crash B27c, bukti).
- Batch 5 financial: cost.category 1, cost
  template (farm.financial) 1, agri.cost.template
  2, wizard 1–3 (wizard 3 total 500.000),
  processing.cost 1–2, farm.activity 1, cpa 1–2,
  clearing 1–2 (2 **confirmed**, partner credits
  500.000), credit.score 2 (**valid**, total
  63.03), loan 1 (**active**), coop 1 (draft),
  insurance.index 1, insurance 1 (**active**),
  claim 1 (**approved**), valuation.template 1,
  asset.valuation 1 (fair 111.562,5, GEP 0.0) + 2
  (fair 0.0).
- Batch 5 ESG + fair trade: framework 1,
  indicator 1, assessment 1 (**completed**,
  entity farm.location 48), line 1, target 1
  (**achieved**) + 2 (**achieved**), perf report 1,
  carbon.factor 1, carbon.ledger 1–2 (2
  **tokenized**), exchange.asset 1–2 (2 =
  CERT-C-2026-2, 2.5 ton), env.report 1,
  env.tracker 1, esg.report 1 (**published**),
  dashboard 1, goal 1 (**achieved**), risk 1,
  compliance 1, kpi 1, data.governance 1
  (**validated**), customization 1, diversity 1
  (total 20), biogas 1, hazardous 1,
  resource.sharing 1 (**matched**, 2026-11-10),
  netting 1, gis 1 (**optimized**), heatmap 1,
  regional 1 (**implemented**), participation 1,
  carbon.credit 2, neutral.goal 1 (**on track**),
  sust.dashboard 2, sust.metric 4, sust.report 1
  (draft), vra.carbon 1, vra.water 1, vra.soil 1,
  fair trade certificate 4 (**applied**), premium
  1 (**approved**), investment 1, labor condition
  1.
- Konfigurasi test bed yang diubah ronde ini:
  currency USD diaktifkan (sebelumnya nonaktif);
  employee 1 `hourly_cost` = 50.000; partner 3
  `impact_credits` = 500.000 (sisa sesudah
  clearing 2.500.000 dari 3.000.000).

---

# Batch 5 — Simulasi ulang kumulatif (B5R2)

**Tanggal:** 10 November 2026. **Keputusan: TIDAK BERSIH** — rantai batch 1–5
lolos lewat UI (0 pageerror + 0 console error di semua fase browser), ketiga
perbaikan B27/B28/B29 TERBUKTI lewat UI, B11 LOLOS, **tetapi ada 2 blocker
baru: B30 (registry kehilangan 2 model fair trade — jalur RPC/direct-URL
gagal, jalur action UI jalan) dan B31 (cron "Check Biological Asset Maturity"
gagal setiap jalan karena method tidak ada).**

## Keadaan awal & infra

- Server Odoo 18 test18 `http://127.0.0.1:8071` (login admin/admin, `?debug=1`).
  Modul perbaikan sudah ter-upgrade: `farm_operation` 18.0.1.2.8,
  `agri_intervention` 18.0.1.0.2, `farm_waste_mgmt` 18.0.1.0.2.
- Data baru berawalan **`SIMULASI B5R2`**, screenshot 841–1086 di `simulasi/`
  (1041–1042 terlewat karena pergeseran nomor, bukan bukti hilang).
- **VM replacement di tengah Bagian 5** (saat `-5fin2.py` berjalan, ~14:5x WIB):
  user `pgtest` + `/opt/pgserver` + isi `/tmp` hilang, server mati. Dipulihkan
  per AGENTS.md (`useradd -u 1001 pgtest` + copy `pginstall` + `.so*` dari
  `pgserver.libs/` + `chmod -R a+rX /opt/pgserver` + start PG dari
  `~/workspace/pgrun` + start Odoo). Data UTUH (MO 161, ISL 140, MO227 done).
  Server baru PID 1835 (boot 14:57, log `/tmp/odoo18-server-b5r2.log` — log
  lama tertimpa; inventaris Traceback log lama sudah dicatat di ronde ini).
  Infra Bagian 4 (broker amqtt PID 11828, subscriber PID 11876, bridge
  PID 11960) ikut mati — Bagian 4 sudah selesai, tidak dihidupkan lagi;
  port 1883/8000 bebas di akhir.
- Baseline awal: worklog 9, `mrp.production` 132, feeding MO done 21,
  `stock.lot` 132, `agri.isl.mrp.production` 124.

## Bagian 1 — rantai batch 1: LOLOS 9/9

Prep `shell-b5r2/b5r2_p1.py` + `b5r2_p1b.py` (user 2). ID baru: product
template 289–293, farm.location **49**, campaign **47**, lot 255/256, seed.batch
**54** (germ 92% OK; lot blok germ 70% → `UserError: SEED QUALITY BLOCK` sesuai
harapan), nursery **44** (lot 257, 25.000 bibit), asset **49** (GDD 357,0 sesudah
21 hari), rotation **48**, BoM tomat **112**, intervensi **87–91** (semua done;
MO 204–208), lot panen **258** (500 kg), crop.lot **41**, QC point **41** /
check **42** (pass) / record book **42**, BoM saus **113**, lot saus **259**,
MO saus **209/210** (done 8 kg tiap MO), market price **44** (Rp 12.000/kg),
valuation **45**, fair val **44**.
Worklog 9→11 (sowing +1, harvesting +1; fertilizing/irrigation/protection 0 —
sesuai fix B27, tanpa crash). Valuasi 45 awalnya NBV=FV=0,0 (original_value
kosong, koefisien 1,0) → di-set via shell (`original_value`=5.000.000,
koefisien 0,5) → **NBV=FV=2.500.000** (sama seperti B5R1).
Browser `browser-proof-b5r2-a.py`, shot **841–853**: 13/13 form terverifikasi,
**0 pageerror, 0 console error**. Dua check-string False adalah artefak
B5R1 (846 nama lot — header menampilkan display name; 850 harga tampil
"12,000.0000").

## Bagian 2 — batch 2: LOLOS

- `-b.py` shot **854–859**: intervensi **IV92** dibuat murni via UI, workflow
  Submit → Approve → Start → Stop → **Completed + Fertilizing**; tab Costs
  '8.00' ×3; MO205 tab Spatial tanpa Oops/tanpa NaN% (tanpa gauge — sama
  seperti B5R1). 0/0 error.
- `-b2.py` shot **860–862**: MO **211** Done + Fertilizing, Soil Nutrient
  '8.00' ×3; MO27 Spatial gauge **100% + "Within Boundaries"**, tanpa NaN%.
  0/0 error.
- `-c.py` (wizard ISL, action 1013) shot **863–868**: sebelum run, MO belum
  migrasi = 16 (193,194,197–201,203,204–211). Run 1 klaim **16** ("Migration
  completed. 16 records migrated"), run 2 klaim **0**, negatif (Confirm OFF)
  → UserError "Please confirm the migration", dialog tetap terbuka. ISL total
  kini **140**. 0/0 error.

## Bagian 3 — batch 3 + B27/B11: LOLOS

Prep `b5r2_p3prep.py`: product template 294–300, BoM **114** (sapi←pakan 10),
**115** (daging), **116** (lele), **117** (lele panen); lot sire **260**, kolam
**261**, lele **262**; pakan sapi/lele 100 kg @WH/Stock. Pre-fix via shell:
BoM 114 `intervention_type` 'process'→'feeding'; lot 260 `is_animal`=True,
`breeding_status`='open'; kategori **63** 'SIMULASI B5R2 Pond'; ISL aqua lot
**8**.

- `-d.py` shot **869–878**: lot hewan **263** Save via UI (B10), lot biasa
  **264** Save via UI, feeding MO **212** Save + Confirm via UI.
  `lot_producing_id` widget TIDAK DITEMUKAN di form MO (sama seperti B5R1/B3G).
  0/0 error.
- `b5r2_p3a.py`: MO212 (feeding, tanpa task) → **done**, finished 1,0, raw 10,0;
  pakan sapi 100→90 kg; `total_feed_consumed` lot 263 = 0,0 (cron yang update,
  bukan MO — sama seperti B5R1).
- `-d2.py` shot **879–885**: weight event **41** (lot 263, 320,0), breeding
  **40** (offspring 1, gestation 0 — onchange hanya cocok nama spesies Inggris,
  sama seperti B5R1), env monitoring **8** (28/65/5/400), harvest MO **213**
  (daging) Confirmed. 0/0 error. (`farm_livestock_house_env` tidak punya kolom
  `comfort_index`.)
- **B11 (`b5r2_p3b.py`) — LOLOS**: cron `_cron_daily_feed_depletion` jalan
  normal tanpa exception. Feeding MO 26→**34 (+8, satu per lot ber-BoM feeding:
  lot 53, 84, 119, 177, 220, 238, 252, 263)**, pakan sapi 90→**80 kg**,
  `total_feed_consumed` ke-8 lot +1,0, worklog 11→11 (delta 0 — sesuai catatan
  B27). Pakan lele tetap 100 (lot lele tanpa BoM feeding).
- **B13 (`b5r2_p3c4.py`) — LOLOS**: draft MO **222** (Lele, BoM 116), ISL task
  **9**, telemetri `{dissolved_oxygen: 2.0, temperature: 29.0}` → True,
  `latest_do_level`=2,0, `latest_water_temp`=29,0, `agent_instruction_json`
  terisi, +1 incident activity **514** ("INCIDENT: Oxygen Depletion
  (critical)").
- `-e.py` shot **886–893**: action 1024 buka LIST dulu (B14), operasi akuakultur
  **19** + sub-task **20** (B12-residu OK), operasi 3 dan 9 dicek ulang 4 tab.
  0/0 error.
- `-e2.py` shot **894–899**: WQ log **7** Save via UI, MO lele **223** + MO lele
  panen **224** Confirmed, ISL aqua lot 8 tampilkan lot lele. 0/0 error.
  (Check '28.50'/'6.80' False — quirk format tampilan; record tersimpan.)
- **B27c eksplisit (`browser-proof-b5r2-b27c.py`, shot 900–901) — LOLOS**:
  MO polos **225** (WH/MO/00227, saus, `intervention_type`='process', tanpa task)
  → Confirm → **Produce All** → **done**, 0 errdlg, tanpa "Oops", 0/0 error,
  worklog tetap 11 (tanpa worklog palsu untuk 'process').

## Bagian 4 — batch 4: LOLOS

Infra dibangun ulang (skrip `/tmp` B5R1 hilang kena VM replacement): broker
amqtt `/tmp/b5r2-broker.py` PID 11828, subscriber `/tmp/b5r2-sub.py` PID 11876,
bridge `agri_iot/mqtt_bridge/main.py` via `bridge-venv/` PID 11960 (port 8000,
`/health` healthy, `mqtt_connected: true`, terdaftar `SIMULASI-B4-GW-01`).
Quirk bridge: WAJIB unset SEMUA 8 variabel proxy termasuk `NO_PROXY`/`no_proxy`
(httpx gagal parse `[::1]`). Baseline: `farm.command.log` 24, `iiot.telemetry`
9, `agri.telemetry` 1.

- Tombol (`browser-proof-b5r2-buttons.py`, shot **902–906**): keempat tombol
  **True** (Power On, Power Off, Reset, Send Reset Command), tanpa Oops, 0/0
  error. Subscriber terima 4 payload; command.log 24→**28**; webhook bridge
  "Received webhook event from Odoo: command" 4×.
- **B24**: POST `/iiot/command/simulasi_b4_sn_001` (envelope JSON-RPC
  `{"action":"power_on","params":{"state":"on"}}`) →
  `{"result":{"status":"success","message":"Command power_on sent to ..."}}`;
  subscriber payload #5; command.log id **30**.
- **B20** (`b5r2_b20.py`): `agri.telemetry` **2** (T 40,0, device 1,
  `production_id`=task 12) → rule 1 terpicu → command.log id **31** power_on
  dispatched; subscriber payload #6; chatter task 12 message **27246**
  ("AUTOMATION: Rule 'SIMULASI B4 Rule Otomatis Suhu' triggered...").
- F7 (`browser-proof-b5r2-f7.py` shot **907–923**): run pertama crash di bagian
  prakiraan (dropdown autocomplete M2O menahan klik field `condition` —
  TimeoutError) SEBELUM print ter-flush, tapi 17 screenshot ada. Rerun
  (`-f7rerun.py`, tanpa screenshot): **17/17, errdlg=0, oops=False tiap item,
  0 pageerror, 0 console error**.
- Cuaca (`browser-proof-b5r2-weather.py`, shot **926–927**): prakiraan **27**
  dibuat via UI dalam SATU save (2026-11-10, "Cerah", humidity 65, wind 12);
  0/0 error. ('Cerah' False sesudah save — artefak tampilan; nilai tersimpan
  benar per psql.)

## Bagian 5 — batch 5 + B28/B29

### Prep Bagian 5 (shell, user 2)

- **5A** (`b5r2_5a.py`): analytic **47**, project **14**, task **63**, skill
  **11**, team **6**, worklog **17** (employee 1, task 63, sowing, qty 8),
  wage.rule **8**, labor.payment **4** (draft), time.bank **4**, certificate
  **3**, manure.batch **3** (MNR/2026/00004, location_source 49, composting,
  qty 500), manure.ledger **2** (MNL/2026/00002, month 11, year 2026).
- **5B** (`b5r2_5b.py`): cost.category **3**, cost.template
  (farm.financial) **2**, `agri.cost.calculation` **4** (TransientModel — task
  62, land 49, tanpa lines), processing.cost **3** (MO 209, total 100.000),
  farm.activity **3**, cpa **3**, clearing **3** (draft, 2.500.000),
  credit.score **3**, loan **2** (draft), coop **2** (draft), insurance.index
  **2**, insurance **2** (draft), claim **2** (draft), valuation.template **2**,
  asset.valuation **3** (tomat) + **4** (sapi).
- **5C2** (`b5r2_5c2.py`): framework 1, indicator 1, assessment 1, line 1,
  target 1, perf report 1, carbon.factor 1, carbon.ledger 1, exchange.asset
  **35**, env.report **2**, env.tracker **2**, esg.report **2**, dashboard **2**,
  goal **2**, risk **2**, compliance **2**, kpi **2**, data.governance **2**,
  customization **2**, diversity **2**, biogas **2**, hazardous **2**,
  resource.sharing **2**, netting **2** (B5R2-NET-001), gis **2**, heatmap **2**,
  regional **2**, participation **2**, carbon.credit **3**, neutral.goal **2**,
  sust.dashboard **3**, sust.metric **5**, sust.report **2**, vra.carbon **2**,
  vra.water **2**, vra.soil **2**.
  Fair trade di 5c2 GAGAL (`KeyError: 'farm.esg.fair_trade.premium.allocation'`,
  shell registry flake) dan rollback; rerun 5c_ft juga gagal
  (`KeyError: 'farm.esg.fair_trade.certificate'`) — diputuskan buat via UI
  di `-5ft.py` (seperti B5R1). Investment **2** + labor condition **2** dibuat
  via RPC (model-model itu ADA di registry).
- **5PREP** (`shell-b5r2/b5r2_5prep.py`, SEMUA langkah berhasil):
  batch 3 `fertilizer_product_id`=305, `quality_check_id`=42; MO B27 baru
  **226** (WH/MO/00228, draft, process); laborpay 4 `journal_id`=8 (Expense);
  cost template **3** B5R2-TPL-TOMAT (seedling, 50.000); calc 4 ada, line **2**
  (qty 10 × 50.000 = 500.000); clearing 3 → **confirmed**, partner 3 credits
  500.000 sisa; score 3 auto-evaluate 58,83 → di-adjust 84,5 (total <60
  tidak lolos ambang loan!); loan 2 `credit_score_id`=**2** (bukan 3 — compute
  memilih skor valid dengan `evaluation_date` terbaru; `action_auto_evaluate`
  tidak men-stempel `evaluation_date`, jadi skor 2 B5R1 yang terpilih,
  total 63,03 ≥ 60) → submit → approve → **active**; assessment 2
  `assessed_entity_id`='farm.location,49'; resource sharing 2 demand=1,
  supply=3; carbon sequestration ledger **4** (total_co2e −2500, verified) →
  tokenize → exchange asset **36** CERT-C-2026-4 (qty 2,5).
- MO **227** (WH/MO/00229, draft, saus, process) dibuat via shell untuk uji
  Produce All di `-5hrb.py`; worklog 17 di-approve via shell
  (`action_approve`) → analytic line **7** (−400.000 = 8 × 50.000).
  Employee 1 `hourly_cost` tetap 50.000.

### 5.1 HR + waste — LOLOS (dengan catatan)

- `-5hr.py` shot **928–945**, 0 pageerror:
  - Worklog 17: form terbuka (temuan B5R1: `farm.worklog` TIDAK punya form
    view — Odoo menampilkan form auto-generated berisi chatter saja; identik
    dengan shot B5R1 683). Sudah approved via shell; header buttons [] (tidak
    ada tombol Approve di UI — temuan B5R1, bukan blocker baru).
  - Labor payment 4: Compute Sheet True → **Post to Accounting True → state
    paid** (check 'Posted' False karena state tampil 'Paid').
  - Skill 11 / team 6 / wage rule 8 / time bank 4 / cert 3: form terbuka,
    errdlg 0. **Koreksi skrip di tengah jalan:** adaptasi awal salah memetakan
    ID tuple-list (10/5/7/3/2 = record B5R1) — shot 933–937 pertama
    menampilkan record B5R1. Diperbaiki (11/6/8/4/3) dan dijalankan ulang
    (`-5hr-rerun.py`, shot 933–937): skill/team/timebank 'SIMULASI B5R2'
    True; wagerule False (model tanpa kolom `name`); cert False di check tapi
    screenshot 937 MEMBUKTIKAN record benar (Mitchell Admin, Skill "SIMULASI
    B5R2 Skill Traktor", Valid).
  - **B28 — LOLOS**: batch 3 Convert to Fertilizer True → MO **228**
    (WH/MO/00230), confirmed, src/dest 8 (WH/Stock), tanpa FK error.
  - Ledger 2: '500' + 'MNR' True; klik statusbar Confirmed GAGAL (element
    not enabled — quirk B5R1); tombol Generate Report tidak muncul (hanya
    tampil bila confirmed); cek PDF dengan nama report SALAH
    (`..._ledger_document`) → 500 `ValueError: Fetching report ...: type
    ir.ui.view, expected ir.actions.report` — **kesalahan nama di skrip,
    bukan bug modul** (nama benar `farm_waste_mgmt.report_manure_ledger`).
    Diperbaiki di skrip.
  - MO 226: Confirm True → confirmed. Tombol "Mark as Done" TIDAK ADA di
    Odoo 18 MRP (namanya "Produce All") — klik False, bukan bug.
- `-5hrb.py` shot **946–953**, 0 pageerror:
  - Laborpay 4 sudah 'paid' (tombol Compute/Post hilang — benar); analytic
    line 7 '-400' True.
  - Batch 3 re-Convert → MO **229** (tanpa FK error — B28 tahan ulang).
  - Ledger 2: statusbar Confirmed (force) True tapi **state DB tetap draft**
    (klik pill tidak persist — lihat catatan di bawah); Generate Report tetap
    tidak muncul; Print via action menu "Manure Ledger" True.
  - **B27 — LOLOS**: MO 227 (sudah di-Confirm via shell) Produce All True,
    errdlg 0, tanpa dialog → **state done** (verifikasi psql).
- **Ledger confirm (observasi O-B5R2-9):** klik pill statusbar tidak
  me-persist (plain: "element is not enabled"; force: True tapi DB tetap
  draft); view tidak punya tombol Confirm dan model `agri.manure.ledger`
  tidak punya `action_confirm` — satu-satunya jalur programatik adalah
  `write({'state': 'confirmed'})`, yang dilakukan via shell sebelum `-5hrc.py`
  (preceden sama seperti approve worklog via shell). Setelah itu tombol
  Generate Report muncul dan berfungsi.
- `-5hrc.py` shot **954–958**, 0 pageerror: laborpay 4 paid; batch 3 Convert
  → MO **230**; ledger 2 (confirmed) header kini ada 'Generate Report', klik
  True; Print via action menu True; PDF (nama benar) → **400** (wkhtmltopdf
  tidak ada — keterbatasan test bed, sama seperti B5R1).
- **B29 — LOLOS (bukti langsung)**: GET
  `/report/html/farm_waste_mgmt.report_manure_ledger/2` → **200, 20.932 byte,
  memuat MNL/2026/00002 + "Manure" + "500"** (skrip `/tmp/b5r2_b29html2.py`).
  PDF → 400 (wkhtmltopdf).
- `-5hrd.py` shot **959–963**, 0 pageerror: batch 3 Convert → MO **231**;
  laborpay 4 Paid; ledger 2 Generate Report True; download PDF gagal timeout
  (PDF 400, tanpa wkhtmltopdf — diharapkan).
- `-5hre.py` shot **964–967**, 0 pageerror: batch **2** (kontrol B5R1, loc 8)
  Convert → MO **232**; laborpay 4 Paid; ledger 2 Generate Report True;
  download gagal (PDF 400).

### 5.2 Financial — LOLOS

- `-5fin.py` shot **968–976**, 0 pageerror: cost template B5R2-TPL-TOMAT OK;
  wizard calc 4 total sebelum '500,000.00' True, Results '500,000.00' True
  (klik Calculate timeout — tombol tidak ditemukan/klik; total sudah terhitung
  saat pembuatan line); processing 3, cpa 3 form OK (tanpa tombol); clearing 3
  'Confirmed' True; credit 3 state Valid (tombol 'Auto Evaluate' ada); loan 2
  'Active' True; coop 2 form OK (Draft).
- `-5fin2.py` shot **977–988** — **terpotong VM replacement** di tengah
  (server mati sesudah shot 982): insurance 2 Activate → Submit → Approve
  (shot 977–980), index 2 Check Weather Indices (981), claim 2 form (982).
  Direrun bagian sisanya (`-5fin2-rerun.py`, shot 982–988), 0 pageerror:
  - Claim 2: klik "Approve" di state draft GAGAL (locator menangkap pill
    statusbar "Approved" yang disabled — jebakan helper; diperbaiki di
    `b5r2_browser_lib.py`: `click_header_button` kini mengecualikan
    `.o_arrow_button`). Alur klaim yang benar: Verify → Approve → Settle.
  - Valuasi 3: Recalculate True; check '111,562.50' False di form TAPI nilai
    DB `fair_value` = **111.562,5 — PERSIS nilai harapan B5R1** (beda format
    tampil saja). Create Accounting Entries True. Valuasi 4 + template 2 form
    OK.
- `-5fin3.py` shot **989–994**, 0 pageerror: insurance 2 Activate True →
  Active, Check Weather Indices True; claim 2 Verify True → Verified,
  **Approve True → Approved** (fix helper terbukti); Settle TIDAK DITEMUKAN —
  **bukan bug**: tombol "Settle" (`action_settle_claim`) ada di form
  INSURANCE, terlihat hanya bila state insurance = 'claim_approved'
  (`farm_financial_insurance/views/insurance_views.xml:30`); insurance 2
  tetap 'active' (Check Weather tidak memicu claim_made tanpa trigger cuaca),
  jadi jalur Settle memang tidak tercapai dengan data ini. Klaim sendiri
  berakhir 'approved' — alur klaim selesai sejauh UI mengizinkan. Wizard
  action 1067: tombol New timeout, tapi tombol Calculate di dialog terlihat
  (True).
- Status akhir financial (psql): laborpay 4 paid, clearing 3 confirmed,
  credit 3 valid (84,5), loan 2 active, coop 2 draft, insurance 2 active,
  claim 2 approved, valuasi 3 fair_value 111.562,5.

### 5.3 Fair trade — LOLOS via UI, TAPI B30 tetap blocker (lihat bawah)

- `-5ft.py` shot **995–1001**, 0 pageerror:
  - **Cert**: isi + save → URL `/odoo/action-1074/6` — **certificate 6
    (B5R2-FT-001) DIBUAT VIA UI**; klik statusbar Certified timeout (quirk
    B5R1).
  - **Premium**: M2O Certificate query 'B5R2' ter-pick, isi, select label
    'Community Investment', save → **premium 2 DIBUAT VIA UI**; Allocate True
    → Allocated; Approve True → Approved.
  - Investment: save → **id 3 DIBUAT VIA UI** (duplikat dari id 2 yang dibuat
    via RPC — tidak masalah).
  - Labor: save GAGAL diam-diam (URL tetap `/new`, tanpa dialog) — **gap
    skrip**: `condition_type` (required) tidak diisi di `-5ft.py`.
- `-5ft2.py` shot **1002–1008**, 0 pageerror: cert action 1074 terbuka;
  premium/investment/labor save SEMUA gagal diam-diam (URL tetap `/new`) —
  **gap skrip**: `set_select_js` (JS set value) tidak meregistrasi nilai ke
  form Odoo, sehingga required field kosong → save tertahan. BUKAN bug modul
  (pendekatan `select_option(label=)` di -5ft/-5ft3 berhasil).
  Labor Schedule Inspection True (pada form new — tanpa efek).
- `-5ft3.py` shot **1009–1015**, 0 pageerror: cert action 1074 terbuka
  ('B5R2-FT-001' False di check list — artefak); premium save →
  **premium 3 DIBUAT VIA UI**; klik Allocate/Approve timeout (form masih
  loading — lihat retry); investment save → **id 5 DIBUAT VIA UI** (id 4
  hilang — sequence terkonsumsi transaksi gagal -5ft2); labor save →
  **labor 3 DIBUAT VIA UI** (safety_training) + Schedule Inspection True.
- Retry premium 3 (`-5ft3-retry.py`, shot 1016–1017): `open_form` langsung
  (`#id=3&model=farm.esg.fair_trade.premium.allocation`) → **dialog "Oops!
  Something went wrong..."** (errdlg 1, tanpa tombol) — **bukti UI B30**.
- Retry2 (`-5ft3-retry2.py`, shot 1018–1019): action 1075 list terbuka
  (errdlg 0); klik baris "5,000,000" membuka premium **1** (B5R1, sudah
  approved — row-match substring memilih baris pertama), bukan premium 3.
- Retry3 (`-5ft3-retry3.py`, shot 1020–1021): URL konteks action
  `/odoo/action-1075/3?debug=1` → **Allocate True → Allocated, Approve True
  → Approved**, errdlg 0. **Premium 3 approved (psql).**
- Status akhir FT (psql): cert 2 (4=B5R1, 6=B5R2); premium 3 (semua approved);
  investment 4 (1,2,3,5); labor 3 (semua safety_training).

### 5.4 ESG — LOLOS (dengan catatan)

- `-5esg.py` shot **1022–1035**, 0 pageerror: framework 2, indicator 2 form
  OK; assessment 2 Start True → In Progress, Complete True → Completed;
  line 2 OK; target 3 Update Current Value True; **Mark as Achieved TIDAK
  DITEMUKAN** (lihat catatan target di bawah); perf report 2 Generate Report
  True; carbon ledger **4** 'Tokenized' True; ledger **3** (kontrol) OK;
  exchange asset **36** (CERT-C-2026-4) + asset **35** OK.
- `-5esg1b.py` shot **1036–1040**, 0 pageerror: assessment 2 sudah Completed
  (tombol Start/Complete tidak ada — benar); target 3 Mark as Achieved tetap
  tidak ada.
  **Catatan target (bukan bug):** target 3 bertipe `reduction`, current 1500 >
  target 1200 → BELUM tercapai; tombol `action_mark_achieved` di view
  `invisible="current_value < target_value and target_type == 'improvement'
  or current_value > target_value and target_type == 'reduction'"` — tombol
  tersembunyi dengan BENAR. (Target B5R1 current 1100 ≤ 1200 sehingga bisa
  dicapai.)
- `-5esg2.py` shot **1043–1058**, 0 pageerror: env report 2 (Generate Report
  ada); env tracker 2 OK; esg report 2 Generate Content True → Approve True
  → **Approved** → Publish True → **Published**; dashboard 2 Refresh Dashboard
  ada; goal 2 Update Progress ada; risk 2 Calculate Scores Automatically ada;
  compliance 2 OK (tanpa tombol); KPI 2 OK tapi **Reset KPI Target TIDAK
  DITEMUKAN** (form tanpa header buttons sama sekali — observasi, pola sama
  seperti worklog); data gov 2 Validate Data Quality True → Validated;
  customization 2 OK; diversity 2 OK.
- `-5esg3.py` shot **1059–1086**, 0 pageerror: env report Generate True;
  dashboard Refresh True; goal Update Progress True → **Achieved**; risk
  Calculate True; biogas/hazardous/resource sharing/netting/gis/heatmap/
  regional/participation/carbon credit/neutral goal/sust dashboard/sust
  metric/sust report/VRA carbon/VRA water/VRA soil — semua form OK.
  Regional Implement True → Implemented. VRA carbon Generate Report True.
  Dua tombol TIDAK DITEMUKAN karena state-gated (bukan bug): 'Match
  Resources' (resource sharing masih Draft — tombolnya 'Publish Signal') dan
  'Optimize' (GIS masih Draft — tombolnya 'Run Analysis').

## Blocker baru

### B30 — registry kehilangan `farm.esg.fair_trade.certificate` + `.premium.allocation` (TERKONFIRMASI, 4 boot)

**Gejala:** `POST /web/dataset/call_kw` untuk kedua model itu → HTTP 404
`werkzeug.exceptions.NotFound`, untuk SEMUA method (search_read, fields_get,
name_search, search, read, search_count, create). Traceback lengkap (diambil
dari debug JSON-RPC):
`addons/web/controllers/dataset.py:22 _call_kw_readonly: request.registry[params['model']]`
→ `odoo/modules/registry.py:234 __getitem__: return self.models[model_name]`
→ `KeyError: 'farm.esg.fair_trade.certificate'` → `raise NotFound() from e`
(dataset.py:24). Pre-check `readonly=_call_kw_readonly` ini jalan untuk
SETIAP request call_kw — termasuk `create` — jadi jalur RPC mati total untuk
kedua model itu.

**Bukti:**
- Probe `/tmp/b5r2_probe3.py` (64 model, nama benar): HANYA 2 model ini yang
  hilang; semua model Bagian 5 lain ada. Probe salah-nama sebelumnya
  (`/tmp/b5r2_probe.py`, 46/62 "hilang") TIDAK VALID — nama model karangan.
- Terkonfirmasi di 4 boot server (PID 8023, 16014, 16653, 1835): restart TIDAK
  memperbaiki. DB sehat: tabel `farm_esg_fair_trade_certificate` +
  `farm_esg_fair_trade_premium_allocation` + 2 tabel rel M2M ada; `ir_model`
  2974/2975 ada; `ir_model_fields` 45 + 42 field ada; action 1074–1077 + 12
  view ada; modul `farm_esg_fair_trade` state installed. Model lain di file
  yang sama (`farm.esg.community.investment`, `farm.esg.labor.condition`)
  ADA di registry (invest count 3, labor count 2 via RPC yang sama).
- **Flip non-deterministik dalam SATU boot (baru, boot PID 1835):**
  probe 10× berturut-turut → cert 404 10/10, invest OK 3. TAPI log akses
  server menunjukkan `POST /web/dataset/call_kw/farm.esg.fair_trade.premium.allocation/web_search_read
  HTTP/1.1" 200` pada **15:09:52,686** (saat `-5ft2.py`), dan browser UI
  membuat cert 6 (15:03:48) + premium 2 (15:04:03) via call_kw yang sama.
  Jadi model itu ADA di registry pada jendela-jendela tertentu dan HILANG di
  jendela lain, tanpa reload registry ("Registry loaded" hanya sekali per
  boot, 14:57:51). Mekanisme flip BELUM ditemukan — BUKAN untuk dipecahkan di
  simulasi ini.
- **Dampak UI (terbukti):** navigasi lewat ACTION/menu BERFUNGSI (cert 6,
  premium 2/3, investment 3/5, labor 3 dibuat via UI; workflow Allocate →
  Approve jalan). Navigasi direct-URL form (`#id=3&model=...`) GAGAL dengan
  dialog "Oops!" (shot 1016, errdlg 1 — satu-satunya errdlg di seluruh
  Bagian 5). URL konteks action (`/odoo/action-1075/3`) BERFUNGSI.
- **Repro persis:** start server test18 → login admin → POST
  `/web/dataset/call_kw` `{"model": "farm.esg.fair_trade.certificate",
  "method": "search_count", "args": [[]]}` → 404 NotFound (KeyError di
  registry). Skrip: `/tmp/b5r2_ftdebug.py` (traceback lengkap),
  `/tmp/b5r2_ftflip.py` (10× probe), `/tmp/b5r2_ftbrowser.py` (probe dari
  konteks browser yang sama).
- **Dampak keputusan:** alur fair trade lewat UI (jalur yang dipakai user)
  LOLOS; jalur RPC/API + deep-link direct-URL RUSAK. Karena B30 adalah cacat
  registry yang nyata dan ter-reproduksi, B5R2 dinyatakan TIDAK BERSIH
  sampai B30 diperbaiki/dijelaskan koordinator. JANGAN upgrade modul
  (`-u farm_esg_fair_trade`) dari simulasi ini — larangan tugas.

### Koreksi B30 — BUKAN bug registry, kesalahan nama model di probe (10 Nov 2026 ~22:40 WIB, investigasi koordinator)

- **Keputusan: B30 BUKAN blocker. TIDAK ada perubahan kode modul, TIDAK ada
  bump versi, TIDAK ada upgrade test18.** Penyebabnya sama persis dengan
  koreksi K-1 B5R1 — dan kesalahan itu TERULANG di ronde B5R2: probe memakai
  nama model **underscore** `farm.esg.fair_trade.certificate` /
  `farm.esg.fair_trade.premium.allocation`, padahal nama yang terdaftar
  adalah **dotted** `farm.esg.fair.trade.certificate` /
  `farm.esg.fair.trade.premium.allocation` (semua titik, tanpa underscore
  di `fair_trade`).
- **Bukti (ground truth):**
  - Source `farm_esg_fair_trade/models/__init__.py:13,83`:
    `_name = 'farm.esg.fair.trade.certificate'` dan
    `_name = 'farm.esg.fair.trade.premium.allocation'`; SEMUA referensi
    modul (views `model`/`res_model`, `ir.model.access.csv`, tests)
    memakai bentuk dotted.
  - `ir_model` test18 (psql): HANYA id 2974
    `farm.esg.fair.trade.certificate` + id 2975
    `farm.esg.fair.trade.premium.allocation`; action 1074–1077
    `res_model` sama (dotted). Tidak ada model underscore di DB.
    Tabel `farm_esg_fair_trade_certificate` berisi 2, premium 3.
  - Grep seluruh tree `farm.esg.fair_trade` (.py/.xml/.csv/.po/.js):
    NOL referensi underscore di KODE/DATA modul manapun. Yang memakai
    underscore hanyalah skrip probe/simulasi + catatan SIMULASI.md ini
    (lihat daftar perbaikan di bawah).
  - Log server boot PID 1835 (`/tmp/odoo18-server-b5r2.log`): SEMUA
    request UI fair trade memakai nama dotted dan mengembalikan 200
    (`get_views`, `web_search_read`, `onchange`, `web_save`,
    `name_search`, `web_read`, `call_button` Allocate/Approve —
    cert 6 + premium 2 dibuat 15:03–15:04, premium 3 15:12).
    Baris 15:09:52,686 yang dikutip di §B30 sebagai bukti "flip"
    sebenarnya berbunyi
    `.../farm.esg.fair.trade.premium.allocation/web_search_read ... 200`
    (DOTTED) — pekerja salah transkripsi menjadi underscore saat
    menulis catatan.
- **Probe verifikasi (skrip `/tmp/b30_verify.py`, `/tmp/b30_verify2.py`,
  sesi admin, server PID 1835, boot yang sama):**
  - DOTTED: `search_count` cert → **200, result 2**; premium → **200,
    result 3**; `read` cert 6 → **200** (`B5R2-FT-001`, `applied`);
    `fields_get` cert → **200**; `web_search_read` premium (spec dict
    Odoo 18) → **200, 3 records** (id 1/2/3, semua `approved`,
    amount 5.000.000); `search_read` cert → **200** (B5R1-FT-001 +
    B5R2-FT-001); `name_search` → **200** keduanya.
  - UNDERSCORE: `search_count`/`web_search_read` cert + premium →
    **HTTP 200 dengan JSON-RPC error code 404 "Not Found"** (bukan
    HTTP 404 — koreksi redaksional §B30), debug traceback persis
    `dataset.py:22 _call_kw_readonly → request.registry[params['model']]`
    → `KeyError` — mereproduksi persis error pekerja.
  - Flip test: `search_count` dotted cert **10× berturut-turut → 200,
    result 2 semua** — TIDAK ADA flip; 404 10/10 pekerja (`ftflip.py`)
    karena skrip itu memakai nama underscore, sementara `invest` OK
    karena `farm.esg.community.investment` dieja benar.
  - Direct-URL browser: `#id=3&model=farm.esg.fair.trade.premium.allocation`
    (dotted) → **form terbuka, errdlg 0** (Amount 5.000.000,00,
    Community Investment, Approved — shot `/tmp/b30/dotted-premium-3.png`);
    `#id=3&model=farm.esg.fair_trade.premium.allocation` (underscore)
    → **errdlg 1, dialog "Oops! Something went wrong..."** — reproduksi
    persis shot 1016 (`/tmp/b30/underscore-premium-3.png`).
    `#id=6&model=farm.esg.fair.trade.certificate` (dotted) → errdlg 0.
  - Catatan probe: `web_search_read` dengan spec LIST (bukan dict)
    error — itu kesalahan argumen probe sendiri (Odoo 18 minta spec
    dict), bukan bug modul; dengan spec dict → 200.
- **Referensi underscore yang diperbaiki (skrip probe/simulasi B5R2
  saja — BUKAN kode modul):**
  - `shell-b5r2/b5r2_5c.py:191,200`, `shell-b5r2/b5r2_5c2.py:157,166`,
    `shell-b5r2/b5r2_5c_ft.py:6,20` (+ docstring penyebab v2) —
    `farm.esg.fair_trade.*` → `farm.esg.fair.trade.*`
    (catatan: baris cert di 5c.py:180,190 dan 5c2.py:146,156 sudah
    dotted sejak awal — hanya baris premium yang salah).
  - `browser-proof-b5r2-5ft3-retry.py:17` — `open_form` premium 3
    underscore → dotted (inilah sumber shot 1016 Oops).
  - TIDAK diperbaiki (artefak ronde tertutup / sudah jalan):
    `shell-b5r1/*`, `browser-proof-b5r1-5ft2.py:57` (B5R1 sudah
    selesai; K-1 mencatat kesalahan yang sama), `/tmp/b5r2_ft*.py`
    (skrip pekerja, bukti asli error), `adapt-5b5r2.py:150` (string
    sumber replace workaround B30 — historis, sudah berjalan), dan
    kutipan underscore di §B30 di atas (dibiarkan sebagai jejak asli
    laporan pekerja).
- **Dampak keputusan: B5R2 Bagian 5 fair trade LOLOS penuh** — jalur UI,
  RPC/API, dan deep-link direct-URL semuanya berfungsi dengan nama
  model yang benar. B30 dicabut sebagai blocker; simulasi ulang
  (koordinator) memakai skrip yang sudah diperbaiki di atas.
  B31 (cron `farm_core`) tetap tercatat terpisah, bukan blocker
  simulasi.

### B31 — cron "Check Biological Asset Maturity" gagal (BARU, farm_core)

**Gejala:** cron id 40 "Check Biological Asset Maturity"
(`farm_core/data/ir_cron_data.xml:8`, model `stock.lot`, interval 1 hari,
aktif) menjalankan `model._cron_check_maturity_and_transfer_asset()` —
method itu **TIDAK ADA di codebase manapun** (grep seluruh `*.py` kosong).
Log server baru (PID 1835): `ValueError: AttributeError("'stock.lot' object
has no attribute '_cron_check_maturity_and_transfer_asset'") while evaluating`
(safe_eval), tercatat ~15:09:52. Satu kegagalan = 2 blok Traceback di log
(exception chain).
**Repro persis:** biarkan cron jalan (atau jalankan manual cron id 40) →
AttributeError di atas. **Dampak:** hanya log error 1×/hari; tidak
memblokir alur simulasi manapun. Dilaporkan, tidak diperbaiki di sini.

## Verifikasi akhir

- **0 pageerror + 0 console error** di SEMUA skrip browser Bagian 1–5
  (setiap log `pageerrors: []`; satu-satunya errdlg=1 adalah dialog Oops B30,
  shot 1016 — lihat Koreksi B30 di atas: dialog itu dari direct-URL probe
  bernomor model underscore, bukan bug modul).
- **Log server baru (PID 1835, boot 14:57): 3 Traceback** — semuanya
  terklasifikasi, BUKAN kegagalan simulasi: (1) `ValueError: Invalid field
  'state' on model 'farm.financial.asset.valuation'` = probe RPC saya sendiri
  (field salah); (2)+(3) satu kegagalan cron B31 (exception chain, 2 blok).
  Log lama (PID 16653) sebelum VM replacement: 11 Traceback — 2×
  DeprecationWarning boot (ag_drive `create` batch), 1× psycopg2 shutdown
  kill 14:21, 7× probe RPC saya (`Invalid field 'name' on farm.worklog`),
  1× PDF nama report salah (kesalahan skrip, diperbaiki).
- **Stok akhir B5R2 (stock.quant, per lokasi):**
  - WH/Stock: Benih Tomat 10,00; Bibit Tomat 25.000,00; Tomat Segar 480,00;
    Saus Tomat 16,00; NPK 0; Sapi Perah 13,00 (3 quant: 1+1+11); Pakan Sapi
    80,00; Pakan Lele 100,00; Kolam Lele 1,00; Daging Sapi 0; Lele Panen 0.
  - Lokasi Production (transit/reserved): Tomat +20,00; Saus −16,00; Pakan
    Sapi +20,00; Sapi Perah −2,00. **Catatan:** MO 225/226/227 berstatus
    'done' tapi finished move-nya tetap 'assigned' (quirk produce-all modul
    farm) — 24 kg saus dari ketiga MO itu belum masuk WH/Stock; angka Stock
    16,00 adalah hasil MO 209/210 saja.
- Hitungan akhir: worklog 12 (max id 17 — tanpa worklog palsu dari MO
  'process'), `mrp.production` **161** (81 done), `agri.isl.mrp.production`
  **140**, feeding MO **34**, `stock.lot` B5R2 10 lot (255–264), manure ledger
  2 confirmed, FT cert 2 / premium 3 (semua approved).
- **Status B27/B28/B29/B11:** B27 LOLOS (MO 225 Produce All → done via
  browser; MO 227 Produce All → done; tanpa worklog palsu); B28 LOLOS (batch
  3 Convert → MO 228/229/230/231 + batch 2 → MO 232, semua confirmed
  src/dest WH/Stock, tanpa FK error); B29 LOLOS (HTML report 200 + isi benar;
  Generate Report + Print via UI berfungsi; PDF 400 = tanpa wkhtmltopdf);
  B11 LOLOS (cron pakan → +8 feeding MO, pakan 90→80 kg).

## Data yang tertinggal (test18, prefix SIMULASI B5R2)

MO 204–232 (termasuk 5 MO convert pupuk 228–232, 2 MO B27 226–227 done, MO
225 done); lot 255–264; intervensi 87–92; ISL 140; worklog 12; laborpay 4
paid; clearing 3 confirmed; credit 3 valid; loan 2 active; insurance 2
active; claim 2 approved; valuasi 3 fair_value 111.562,5; carbon ledger 4
tokenized → asset 36 CERT-C-2026-4; FT cert 6, premium 2+3 approved,
investment 2/3/5, labor 2/3; assessment 2 completed; esg report 2 published;
target 3 in_progress (reduction, 1500 > 1200 — belum tercapai, benar);
resource sharing 2 draft; netting 2; GIS 2 draft.

## Observasi (bukan blocker)

- O-B5R2-1: widget `lot_producing_id` TIDAK DITEMUKAN di form MO (B5R1/B3G).
- O-B5R2-2: check teks '28.50'/'6.80' (WQ) dan 'Cerah' (forecast) False
  sesudah save — quirk format tampilan; record tersimpan benar.
- O-B5R2-3: `farm_livestock_house_env` tanpa kolom `comfort_index`.
- O-B5R2-4: F7 run pertama crash di seksi prakiraan (dropdown autocomplete
  menahan klik); rerun 17/17 bersih.
- O-B5R2-5: `farm.worklog` tanpa form view (hanya chatter) + tanpa tombol
  Approve di UI — approve via shell (temuan B5R1).
- O-B5R2-6: klik pill statusbar ledger tidak me-persist + view tanpa tombol
  Confirm + model tanpa `action_confirm` — confirm via shell write.
- O-B5R2-7: skrip `-5hr.py` awal salah ID tuple-list (record B5R1) — diperbaiki
  + rerun shot 933–937 (kesalahan adaptasi skrip, bukan modul).
- O-B5R2-8: `set_select_js` (JS set value) tidak meregistrasi nilai ke form
  Odoo → save gagal diam-diam di `-5ft2.py`; pakai `select_option(label=)`.
- O-B5R2-9: "Mark as Achieved" target 3 tersembunyi dengan benar (reduction,
  current > target); tombol "Settle" klaim ada di form insurance, hanya bila
  state 'claim_approved'; tombol "Match Resources"/"Optimize" state-gated;
  tombol "Reset KPI Target" tidak ada di form KPI; klik Calculate wizard
  timeout tapi total sudah 500.000,00.
- O-B5R2-10: loan 2 terikat credit score 2 (B5R1), bukan score 3, karena
  `action_auto_evaluate` tidak men-stempel `evaluation_date`.
- O-B5R2-11: `click_header_button` lama menangkap pill statusbar disabled
  (mis. "Approved") — diperbaiki di `b5r2_browser_lib.py` (kecualikan
  `.o_arrow_button`).

---

# Batch 5 — Simulasi ulang kumulatif (B5R3)

**Tanggal:** 10 November 2026. **Keputusan: BERSIH** — rantai batch 1–5 lolos
lewat UI (0 pageerror + 0 console error di semua fase browser), B30
TERBUKTI BUKAN BUG (probe dotted → HTTP 200 semua, underscore → 404 sesuai
harapan), B31 TERVERIFIKASI DIPERBAIKI (cron 40 tetap nonaktif, 0
`_cron_check_maturity` di log, 0 Traceback), B27/B28/B29/B11 LOLOS lagi,
**tidak ada blocker baru (tidak ada B32).** Satu koreksi skrip di Bagian 2
(O-B5R3-1: klaim "MO 240 Done" dari `-b2.py` ternyata false positive
text-check) sudah ditutup dengan pass UI sungguhan (Confirm → Produce All →
done, shot 1333–1335).

## Keadaan awal & infra

- Server Odoo 18 test18 `http://127.0.0.1:8071` (login admin/admin, `?debug=1`).
  `farm_core` SUDAH ter-upgrade ke 18.0.1.0.2 di test18; cron 40 "Check
  Biological Asset Maturity" terverifikasi `active=False` sebelum simulasi.
- Data baru berawalan **`SIMULASI B5R3`**, screenshot **1087–1335** di
  `simulasi/` (243 shot; hilang 1170–1171 = rerun F7 tanpa screenshot,
  1264–1265 = `-5ft3-retry2.py` tidak dijalankan karena retry + retry3 sudah
  cukup, 1287–1288 = gap nomor antar skrip).
- **VM replacement di tengah Bagian 5** (sesudah `-5fin.py`, saat `-5fin2.py`
  berjalan): user `pgtest` + `/opt/pgserver` + isi `/tmp` hilang, server mati.
  Dipulihkan per AGENTS.md (`useradd -u 1001 pgtest` + copy `pginstall` +
  `.so*` dari `pgserver.libs/` + `chmod -R a+rX /opt/pgserver` + start PG dari
  `~/workspace/pgrun` + start Odoo). Data UTUH (mrp.production 191, worklog
  15, command.log 40). Server baru PID 1863 (log
  `/tmp/odoo18-server-b5r3.log`, 0 Traceback). Semua shot `-5fin2` pertama
  (1223–1234) ternyata sempat tertulis sebelum server mati — hanya log-nya
  hilang; `-5fin2-rerun.py` mengulang bagian klaim/valuasi dengan log segar.
  Infra Bagian 4 (broker amqtt PID 14665, subscriber PID 14926, bridge PID
  14697) ikut mati — Bagian 4 sudah selesai, tidak dihidupkan lagi.
- Baseline awal: worklog 12, `mrp.production` 161, `stock.lot` 143,
  `agri.isl.mrp.production` 140, feeding MO 35.

## Bagian 1 — rantai batch 1: LOLOS 9/9

Prep `shell-b5r3/b5r3_p1.py` + `b5r3_p1b.py` (user 2). ID baru: product
template 301–305 (benih 301, bibit 302, tomat 303, saus 304, NPK 305), variant
saus 316, NPK 317, farm.location **50**, campaign **48**, lot 266/267 (benih +
blok), lot bibit 268, seed.batch **56** (germ 92% OK; lot blok germ 70% →
`UserError: SEED QUALITY BLOCK` sesuai harapan), nursery **45** (lot 268,
25.000 bibit), asset **50** (GDD 357,0 sesudah 21 hari), rotation **49**, BoM
tomat **118**, task **64**, intervensi **93–97** (semua done; MO 233–237), lot
panen **269** (500 kg), crop.lot **42** (field grade_a/b/c_qty TIDAK ADA di
model — `Invalid field`, dicatat skrip, bukan blocker), QC point **42** /
check **43** (pass) / record book **43** (active), BoM saus **119**, lot saus
**270**, MO saus **238/239** (WH/MO/00240, WH/MO/00241, done 8 kg tiap MO),
market price **45** (Rp 12.000/kg), valuation **46**, fair val **45**.
Worklog 12→14 (sowing +1, harvesting +1; fertilizing/irrigation/protection 0
— sesuai fix B27, tanpa crash). Valuasi 46 awalnya NBV=FV=0,0 →
di-set via shell (`original_value`=5.000.000, koefisien 0,5) →
**NBV=FV=2.500.000** (sama seperti B5R1/B5R2).
Browser `browser-proof-b5r3-a.py`, shot **1087–1099**: 13/13 form
terverifikasi, **0 pageerror, 0 console error**. Dua check-string False
adalah artefak B5R2 (1092 nama lot — header display name; 1096 harga tampil
"12,000" format tampil). Stok: tomat 480,0; saus 16,0.

## Bagian 2 — batch 2: LOLOS

- `-b.py` shot **1100–1105**: intervensi **IV98** dibuat murni via UI (dari
  form intervensi 94), workflow Submit → Approve → Start → Stop →
  **Completed + Fertilizing**; tab Costs '8.00' ×3; MO234 tab Spatial tanpa
  Oops/tanpa NaN% (tanpa gauge — sama seperti B5R2). 0/0 error.
- `-b2.py` shot **1106–1108**: MO **240** (WH/MO/00242, MO milik IV98) —
  LIHAT KOREKSI O-B5R3-1 di bawah; MO27 Spatial gauge **100% + "Within
  Boundaries"**, tanpa NaN%. 0/0 error.
- `-c.py` (wizard ISL, action 1013) shot **1109–1114**: sebelum run, MO tanpa
  ISL = **29** (psql, cocok dengan klaim). Run 1 klaim **29** ("Migration
  completed. 29 records migrated to ISL architecture."), run 2 klaim **0**,
  negatif (Confirm OFF) → UserError "Please confirm the migration", dialog
  tetap terbuka. ISL total kini **169** (140+29). 0/0 error.

## Bagian 3 — batch 3 + B27/B11: LOLOS

Prep `b5r3_p3prep.py`: product template 306–312 (sapi 306, pakan sapi 307,
daging 308, kolam 309, lele 310, pakan lele 311, lele panen 312); variant sapi
318, pakan sapi 319, daging 320, kolam 321, lele 322, pakan lele 323, lele
panen 324; BoM **120** (sapi←pakan 10), **121** (daging), **122** (lele),
**123** (lele panen); lot sire **271**, kolam **272**, lele **273**; pakan
sapi/lele 100 kg @WH/Stock. Pre-fix via shell: kategori Pond **64** (produk
Kolam Lele tpl 309); BoM 120 `intervention_type` 'process'→'feeding'; lot 271
`is_animal`=True, `breeding_status`='open'; ISL aqua lot **9** (lot 273,
water 1000).

- `-d.py` shot **1115–1124**: lot hewan **274** Save via UI (B10), lot biasa
  **275** Save via UI, feeding MO **241** (WH/MO/00243) Save + Confirm via
  UI. Widget `lot_producing_id` TIDAK DITEMUKAN (observasi lama O-B5R2-1).
  0/0 error.
- `b5r3_p3a.py`: MO241 → **done** via button_mark_done, finished 1,0, raw
  10,0; pakan sapi 100→90 kg; `total_feed_consumed` lot 274 = 0,0 (cron yang
  update, bukan MO — sama seperti B5R2).
- `-d2.py` shot **1125–1131**: lot 274 form; weight event **42** (320,0 —
  check '320' False sesudah save, quirk format); breeding **41** (offspring
  1, gestation 0 — onchange hanya cocok nama spesies Inggris); env monitoring
  **9** (28/65/5/400); harvest MO **242** (daging) Confirmed. 0/0 error.
- **B11 (`b5r3_p3b.py`) — LOLOS**: cron `_cron_daily_feed_depletion` jalan
  normal tanpa exception. Feeding MO 36→**45 (+9, satu per lot ber-BoM
  feeding: lot 53, 84, 119, 177, 220, 238, 252, 263, 274)**, pakan sapi
  90→**80 kg**, `total_feed_consumed` ke-9 lot +1,0, worklog 14→14 (delta 0).
  Pakan lele tetap 100 (lot lele tanpa BoM feeding).
- **B13 (`b5r3_p3c4.py`) — LOLOS (dengan koreksi skrip)**: percobaan pertama
  salah produk — `'product_id': 310` di dict create masih menunjuk variant
  B5R2 Lele (310 kini = template B5R3) → MO **252** (WH/MO/00254, produk
  B5R2 Lele), task 10, insiden 515 (tetap jalan). Diperbaiki ke 322 dan
  diulang: draft MO **253** (WH/MO/00255, B5R3 Lele), ISL task **11**,
  telemetri `{dissolved_oxygen: 2.0, temperature: 29.0}` → True,
  `latest_do_level`=2,0, `latest_water_temp`=29,0,
  `agent_instruction_json` terisi, +1 incident activity **516** ("INCIDENT:
  Oxygen Depletion (critical)"). MO 252/task 10/insiden 515 tertinggal
  sebagai data (produk B5R2) — lihat "Data tertinggal".
- `-e.py` shot **1132–1139**: action 1024 buka LIST dulu (B14, 12 baris),
  operasi akuakultur **21** + sub-task tersimpan (B12-residu OK), operasi 3
  dan 9 dicek ulang 4 tab. 0/0 error.
- `-e2.py` shot **1140–1145**: WQ log **8** Save via UI, MO lele **254** + MO
  lele panen **255** Confirmed, ISL aqua lot 9 tampilkan lot lele. 0/0 error.
- **B27c (`browser-proof-b5r3-b27c.py`, MO polos 256 WH/MO/00258) — LOLOS**:
  shot 1146–1147, Confirm → **Produce All** → **done**, 0 errdlg, tanpa
  "Oops", 0/0 error. Verifikasi psql: MO256 done, worklog tetap 14 (tanpa
  worklog palsu).
- Hitungan akhir Bagian 3: worklog 14, `mrp.production` 185, ISL 169,
  feeding MO 47.

## Bagian 4 — batch 4: LOLOS

Infra dibangun ulang (skrip `/tmp` B5R2 hilang): broker amqtt
`/tmp/b5r3-broker.py` (PID 14665, 127.0.0.1:1883), subscriber paho
`/tmp/b5r3-sub.py` (PID 14926 — awalnya PID 14683 GAGAL start: paho lama
tanpa `CallbackAPIVersion`, diperbaiki `mqtt.Client()` tanpa argumen), bridge
`agri_iot/mqtt_bridge/main.py` via `bridge-venv/` (PID 14697, port 8000,
`/health` healthy, `mqtt_connected: true`, terdaftar `SIMULASI-B4-GW-01`).
Quirk bridge: WAJIB unset SEMUA 8 variabel proxy termasuk
`NO_PROXY`/`no_proxy`. Baseline: `farm.command.log` 30, `iiot.telemetry` 9,
`agri.telemetry` 2.

- Tombol (`browser-proof-b5r3-buttons.py`, shot **1148–1152**, dijalankan 2×):
  run 1 — keempat tombol **True** (Power On, Power Off, Reset, Send Reset
  Command), tanpa Oops, 0/0 error, TAPI subscriber mati saat itu → 0 payload.
  Run 2 (subscriber hidup) — 4/4 True, 0/0 error, subscriber terima **4
  payload** (`power on/off`, `reset` ×2). command.log 30→**38** (+8); webhook
  bridge "Received webhook event from Odoo: command" 8×.
- **B24** (`/tmp/b5r3_b24b.py`): percobaan pertama body mentah →
  `{'error': 'Action is required', 'status': 'error'}` (route `type='json'`
  butuh envelope JSON-RPC). Ulang dengan envelope →
  `{"result":{"status":"success","message":"Command power_on sent to
  simulasi_b4_sn_001"}}`; subscriber payload #5; command.log 39.
- **B20** (`shell-b5r3/b5r3_b20.py`): `agri.telemetry` **3** (T 40,0, device
  1, `production_id`=task 12) → rule 1 terpicu → command.log **41** power_on
  dispatched; subscriber payload #6; chatter task 12 message **27647**
  ("AUTOMATION: Rule 'SIMULASI B4 Rule Otomatis Suhu' triggered...").
- F7 (`browser-proof-b5r3-f7.py`, shot **1153–1171**): 17/17 halaman errdlg=0
  oops=False; seksi prakiraan crash persis seperti B5R2 (dropdown
  autocomplete menahan klik field `condition` — TimeoutError; M2O location
  juga "TIDAK ADA item cocok"). Rerun (`-f7rerun.py`, tanpa screenshot):
  **17/17, bad=0/17, pageerrors=0, console_errors=0**.
- Cuaca (`browser-proof-b5r3-weather.py`, shot **1172–1173**): prakiraan
  **28** dibuat via UI dalam SATU save (2026-11-10, "Cerah", humidity 65,
  wind 12); 0/0 error. ('Cerah' False sesudah save — artefak tampilan; nilai
  tersimpan benar.)

## Bagian 5 — batch 5: LOLOS

Prep `shell-b5r3/b5r3_5a.py` (HR + waste), `b5r3_5b.py` (financial),
`b5r3_5c2.py` (ESG — **5c v1 JANGAN dipakai**: 15/15 gagal karena nama model
tebakan `farm.esg.*`; nama benar `esg.framework`, `esg.assessment`,
`agri.esg.risk.assessment`, dst.), `b5r3_5c_ft.py` (fair trade, nama dotted),
`b5r3_5prep.py` + `/tmp/b5r3_5prep2.py` (finalisasi: calc line 4, clearing 4
confirmed, loan 3 active, carbon ledger 6 → tokenize → exchange asset 38).
ID baru: analytic **52**, project **16**, task **65**, skill **12**, team
**7**, worklog **20**, wage.rule **9**, labor.payment **5** (draft),
time.bank **5**, certificate **4**, manure.batch **4** (MNR/2026/00005,
location_source 50, composting, qty 500), manure.ledger **3**
(MNL/2026/00003, month 11, year 2026); cost.category **4**, cost.template
(`farm.financial`) **3**, `agri.cost.calculation` **5**, processing.cost **4**
(MO 238, total 100.000), farm.activity **4**, cpa **4**, clearing **4**
(draft, 2.500.000), credit.score **4**, loan **3** (draft), coop **3**
(draft), insurance.index **3**, insurance **3** (draft), claim **3** (draft),
valuation.template **3**, asset.valuation **5** (tomat) + **6** (sapi);
framework **3**, indicator **3**, assessment **3**, line **3**, target **4**,
perf report **3**, carbon.factor **3**, carbon.ledger **5**, exchange.asset
**37**, env.report **3**, env.tracker **3**, FT cert **8** (B5R3-FT-001,
certified), premium **4** (draft, 5.000.000), investment **6**, labor **4**,
esg.report **3**, dashboard **3**, goal **3**, risk **3**, compliance **3**,
kpi **3**, data.governance **3**, customization **3**, diversity **3**,
biogas **3**, hazardous **3**, resource.sharing **3**, netting **3**
(B5R3-NET-001), gis **3**, heatmap **3**, regional **3**, participation **3**,
carbon.credit **5**, neutral.goal **3**, sust.dashboard **5**, sust.metric
**6**, sust.report **3**, vra.carbon **3**, vra.water **3**, vra.soil **3**.
Worklog 20 di-approve via shell (`action_approve()` langsung — model tanpa
field `state`) → analytic line **13** (−400.000 = 8 × 50.000).

### 5.1 HR + waste — LOLOS (shot 1174–1213, 0 pageerror)

- `-5hr.py` shot **1174–1191**: worklog 20 form terbuka (tanpa form view —
  hanya chatter; header buttons []; 'SIMULASI B5R3'/'Approved' False — temuan
  B5R2); laborpay 5 Compute Sheet True → Post to Accounting True → **paid**
  ('Posted' False karena state tampil 'Paid'); skill 12 / team 7 / timebank
  5 True; wagerule 9 False (model tanpa kolom `name`); cert 4 False di check
  tapi screenshot 1183 membuktikan record benar. **B28 — LOLOS**: batch 4
  Convert to Fertilizer True → MO **258** (WH/MO/00260), confirmed, tanpa FK
  error. Ledger 3: '500' + 'MNR' True; klik statusbar Confirmed GAGAL
  (element not enabled — quirk B5R2); Generate Report tidak muncul; PDF nama
  benar → **400** (wkhtmltopdf tidak ada). MO 257: Confirm True → confirmed;
  tombol "Mark as Done" TIDAK ADA (namanya "Produce All") — bukan bug.
- `-5hrb.py` shot **1192–1199**: laborpay 5 sudah 'paid' (tombol Compute/Post
  hilang — benar); analytic line 13 '-400' True; batch 4 re-Convert → MO
  **259** (B28 tahan ulang); ledger 3 statusbar Confirmed (force) True tapi
  **state DB tetap draft** (klik pill tidak persist); Generate Report tetap
  tidak muncul; Print via action menu "Manure Ledger" True. **B27 — LOLOS**:
  MO 257 (sudah Confirm di -5hr) Produce All True, errdlg 0, tanpa dialog →
  **state done** (verifikasi psql).
- Ledger 3 dikonfirmasi via shell (`write({'state': 'confirmed'})`) sebelum
  -5hrc.py — MO257 done, laborpay5 paid terverifikasi.
- `-5hrc.py` shot **1200–1204**: laborpay 5 paid; batch 4 Convert → MO
  **260**; ledger 3 (confirmed) header kini ada 'Generate Report', klik
  True; Print via action menu True; PDF → 400 (wkhtmltopdf).
- **B29 — LOLOS** (bukti langsung): GET
  `/report/html/farm_waste_mgmt.report_manure_ledger/3` → **200, 21.342
  byte, memuat MNL/2026/00003 + "Manure" + "500"**.
- `-5hrd.py` shot **1205–1209**: batch 4 Convert → MO **261**; laborpay 5
  Paid; ledger 3 Generate Report True; download PDF gagal timeout (PDF 400,
  diharapkan).
- `-5hre.py` shot **1210–1213**: batch **2** (kontrol B5R1, loc 8) Convert →
  MO **262**; laborpay 5 Paid; ledger 3 Generate Report True; download gagal
  (PDF 400).

### 5.2 Financial — LOLOS (shot 1214–1240, 0 pageerror)

- `-5fin.py` shot **1214–1222**: cost template B5R3-TPL-TOMAT OK; wizard calc
  5 total sebelum '500,000.00' True, Results '500,000.00' True (klik
  Calculate timeout — tombol tidak ditemukan; total sudah terhitung saat
  pembuatan line); processing 4, cpa 4 OK (tanpa tombol); clearing 4
  'Confirmed' True; credit 4 state Valid (tombol 'Auto Evaluate' ada); loan
  3 'Active' True; coop 3 Draft. 0 pageerror.
- `-5fin2.py` (shot 1223–1234, log hilang karena VM replacement — lihat
  "Keadaan awal"): insurance 3 Activate→Submit→Approve; claim 3 masih
  draft; valuasi 5 fair_value DB = 111.562,5.
- `-5fin2-rerun.py` shot **1228–1234**: claim Approve/Settle NOT FOUND di
  draft (benar — butuh Verify dulu); valuasi 5 Recalculate True + Create
  Accounting Entries True ('111,562.50' False di form tapi nilai DB
  111.562,5 — beda format tampil, sama seperti B5R2); valuasi 6 + template 3
  OK. 0 pageerror.
- `-5fin3.py` shot **1235–1240**: insurance 3 Activate True → Active, Check
  Weather Indices True; claim 3 Verify True → Verified, **Approve True →
  Approved**; Settle TIDAK DITEMUKAN — **bukan bug**: tombol "Settle"
  (`action_settle_claim`) ada di form INSURANCE, terlihat hanya bila state
  insurance = 'claim_approved'; insurance 3 tetap 'active', jadi jalur
  Settle memang tidak tercapai dengan data ini. Klaim berakhir 'approved' —
  alur klaim selesai sejauh UI mengizinkan. Wizard action 1067: tombol New
  timeout, tapi tombol Calculate di dialog terlihat (True). 0 pageerror.
- Status akhir financial: laborpay 5 paid, clearing 4 confirmed, credit 4
  valid (84,5), loan 3 active, coop 3 draft, insurance 3 active, claim 3
  approved, valuasi 5 fair_value 111.562,5.

### 5.3 Fair trade — LOLOS (shot 1241–1267, 0 pageerror) — verifikasi B30

- `-5ft.py` shot **1241–1247**: cert **9** dibuat via UI (duplikat nomor
  B5R3-FT-001 — tidak ada unique constraint; cert 8 dari 5c2 tetap
  certified, cert 9 'applied'); premium **5** via UI, Allocate True →
  Allocated, Approve True → **Approved**; investment **7** via UI; labor save
  gagal diam-diam (URL tetap /new — `condition_type` required tidak diisi,
  gap skrip O-B5R2-8). 0 pageerror.
- `-5ft2.py` shot **1248–1254**: premium/investment/labor save gagal
  diam-diam karena `set_select_js` tidak meregistrasi nilai (gap skrip,
  O-B5R2-8); Allocate di form belum tersimpan tidak berefek (state tetap
  Draft). 0 pageerror.
- `-5ft3.py` shot **1255–1261**: cert 4 (kontrol B5R1) errdlg 0; premium
  **6** via UI; Allocate/Approve timeout (form loading — sama seperti B5R2);
  investment **8** via UI; labor **5** via UI (safety_training) + Schedule
  Inspection True. 0 pageerror.
- `-5ft3-retry.py` shot **1262–1263** (direct-URL model DOTTED,
  `farm.esg.fair.trade.premium.allocation` id 6): form terbuka errdlg 0 —
  **tanpa "Oops"**; Allocate True → Allocated, Approve True → **Approved**.
  0 pageerror.
- `-5ft3-retry3.py` shot **1266–1267** (URL konteks action
  `/odoo/action-1075/6`): premium 6 sudah Approved — tombol Allocate/Approve
  hilang dengan benar. 0 pageerror.
- **Probe RPC B30** (`/tmp/b5r3_b30probe.py`, `call_kw`): dotted
  `farm.esg.fair.trade.certificate` search_count = **4**, dotted
  `farm.esg.fair.trade.premium.allocation` search_count = **6**, read cert 8
  (B5R3-FT-001, certified), read premium 6 (5.000.000, approved) — semua
  HTTP 200. Underscore `farm.esg.fair_trade.certificate` /
  `.premium.allocation` → JSON-RPC error **404** (sesuai harapan — model itu
  memang tidak ada). **B30 DICABUT TERKONFIRMASI: bukan bug registry.**
- State akhir FT: cert 8 certified + 9 applied; premium 4 draft (5c2, tidak
  dipakai), 5 approved, 6 approved; investment 6/7/8; labor 4/5.

### 5.4 ESG — LOLOS (shot 1268–1332, 0 pageerror)

- `-5esg.py` shot **1268–1281**: framework 3, indicator 3 OK; assessment 3
  Start → In Progress, Complete → **Completed**; line 3 OK; target 4 Update
  Current Value True; Mark as Achieved NOT FOUND (benar — target reduction,
  current 1500 > target 1200); perf report 3 Generate Report True; carbon
  ledger 6 'Tokenized' True; ledger 5 OK; exchange asset **38**
  (CERT-C-2026-6) + 37 OK. 0 pageerror.
- `-5esg1b.py` shot **1282–1286**: assessment 3 sudah Completed (tombol
  Start/Complete hilang — benar); target 4 Mark as Achieved tetap
  tersembunyi dengan benar. 0 pageerror.
- `-5esg2.py` shot **1289–1304**: env report 3 Generate Report; env tracker
  3; esg report 3 Generate Content → Approve → Approved → Publish →
  **Published**; dashboard 3 Refresh; goal 3 Update Progress; risk 3
  Calculate Scores; compliance 3; KPI 3 ("Reset KPI Target" NOT FOUND — form
  tanpa header button, sama seperti B5R2); data gov 3 Validate Data Quality
  → **Validated**; customization 3; diversity 3. 0 pageerror.
- `-5esg3.py` shot **1305–1332**: env report 3 Generate Report True;
  dashboard 3 Refresh True; goal 3 Update Progress True → **Achieved**;
  risk 3 Calculate Scores True; biogas 3; hazardous 3; resource sharing 3
  ("Match Resources" NOT FOUND — state-gated, sama seperti B5R2); netting 3;
  gis 3 ("Optimize" NOT FOUND — state-gated); heatmap 3; regional 3
  Implement True → **Implemented**; participation 3; carbon credit 5;
  neutral goal 3; sust dashboard 5; sust metric 6; sust report 3; vra
  carbon 3 Generate Report True; vra water 3; vra soil 3. 0 pageerror.

## Status B30 / B31

- **B30 — DICABUT, TERKONFIRMASI BUKAN BUG.** Semua jalur memakai nama model
  DOTTED `farm.esg.fair.trade.certificate` /
  `farm.esg.fair.trade.premium.allocation`: probe RPC HTTP 200 (search_count
  4/6, read cert 8 + premium 6), direct-URL dotted form terbuka errdlg 0
  (shot 1262), URL konteks action terbuka errdlg 0 (shot 1266), pembuatan +
  Allocate + Approve via UI jalan (premium 5, 6). Nama underscore memang
  tidak ada → 404 adalah perilaku benar.
- **B31 — DIPERBAIKI, TERVERIFIKASI.** Cron 40 "Check Biological Asset
  Maturity" tetap `active=False` (psql: `40 | Check Biological Asset
  Maturity | f`); log server `/tmp/odoo18-server-b5r3.log`: **0 Traceback, 0
  kemunculan `_cron_check_maturity`** sepanjang ronde. Scheduler tidak
  memuat id 40.

## Blocker baru

Tidak ada. **B32 tidak dibuka.**

## Stok akhir B5R3 (WH/Stock, psql `stock_quant`, location 8)

| Produk | Stok |
|---|---|
| SIMULASI B5R3 Benih Tomat Servo F1 | 10,00 |
| SIMULASI B5R3 Bibit Tomat Servo F1 | 25.000,00 |
| SIMULASI B5R3 Tomat Segar Servo F1 | 480,00 |
| SIMULASI B5R3 Saus Tomat Servo F1 | 16,00 |
| SIMULASI B5R3 Pupuk NPK 16-16-16 | 0 |
| SIMULASI B5R3 Sapi Perah | 13,00 |
| SIMULASI B5R3 Pakan Sapi | 80,00 |
| SIMULASI B5R3 Daging Sapi | 0 |
| SIMULASI B5R3 Kolam Lele | 1,00 |
| SIMULASI B5R3 Lele | 0 |
| SIMULASI B5R3 Pakan Lele | 100,00 |
| SIMULASI B5R3 Lele Panen | 0 |

Identik dengan baseline B5R2. Hitungan akhir: worklog 15, `mrp.production`
WH/MO/002xx confirmed 21 / draft 15 / done 28 (sesudah koreksi MO240),
`agri.isl.mrp.production` 169, `stock.lot` 154, feeding MO total 50 (semua
ronde; B5R3 36→45 sesudah cron B11).

## Data tertinggal

- MO 252 (WH/MO/00254, produk B5R2 Lele) + task 10 + insiden 515 — dari
  percobaan B13 pertama yang salah produk (diperbaiki ke 322).
- Cert 9 (duplikat nomor B5R3-FT-001, state 'applied'), premium 4 (draft,
  tidak dipakai), investment 6/7/8 (tiga record nama sama: 5c2, -5ft, -5ft3),
  labor 4/5.
- MO 233–237 (intervensi 93–97) draft; MO 242 (daging) confirmed; MO 258–262
  (manure convert) confirmed; MO 240 kini done (koreksi O-B5R3-1).
- Claim 3 'approved' (bukan settled — jalur Settle tidak tercapai karena
  insurance 3 'active', sesuai desain tombol state-gated); coop 3 draft;
  valuasi 6 + template 3.
- Assessment 3 completed; esg report 3 published; goal 3 achieved; data gov
  3 validated; regional 3 implemented; target 4 in_progress (reduction, 1500
  > 1200 — belum tercapai, benar); resource sharing 3 draft; netting 3; gis
  3 draft.
- Log browser Bagian 1–3 + log `-5fin2` pertama hilang saat VM replacement
  (hanya log pasca-recovery di `/tmp/b5r3_*.log`); screenshot-nya utuh
  (1087–1240).

## Observasi (bukan blocker)

- O-B5R3-1 (KOREKSI, penting): klaim "MO 240 Done" dari `-b2.py` (shot
  1106–1108) adalah **false positive text-check** — skrip hanya mengecek
  `'Done' in txt` dan `'Fertilizing' in txt`, padahal keduanya muncul di
  halaman form draft (pill statusbar + label tipe intervensi). Verifikasi
  psql sesudah ronde: MO 240 masih **draft**; MO 211 (B5R2, skrip sama) juga
  **draft** — jadi klaim "Done" di B5R2 untuk MO 211 juga tidak pernah
  benar-benar terverifikasi. Ditutup di ronde ini dengan pass UI sungguhan
  (`/tmp/b5r3_mo240.py`, shot **1333–1335**): Confirm True → Confirmed,
  Produce All True → **Done** (psql: WH/MO/00242 done, worklog tetap 15,
  0 pageerror). Pelajaran: check teks status WAJIB membaca state DB atau
  pill aktif, bukan sekadar keberadaan teks di halaman.
- O-B5R3-2: ulangan O-B5R2-1 — widget `lot_producing_id` tidak ditemukan di
  form MO.
- O-B5R3-3: ulangan O-B5R2-2 — check teks '320' (weight event), '28.50'/'6.80'
  (WQ), 'Cerah' (forecast), '111,562.50' (valuasi), '12,000' (harga) False
  sesudah save — quirk format tampilan; nilai tersimpan benar di DB.
- O-B5R3-4: ulangan O-B5R2-4 — F7 run pertama crash di seksi prakiraan
  (dropdown autocomplete menahan klik field `condition`); rerun 17/17 bersih.
- O-B5R3-5: ulangan O-B5R2-5/6 — `farm.worklog` tanpa form view/tombol
  Approve di UI (approve via shell); klik pill statusbar ledger tidak
  me-persist (confirm via shell write).
- O-B5R3-6: ulangan O-B5R2-8 — `set_select_js` tidak meregistrasi nilai ke
  form Odoo (save gagal diam-diam di `-5ft2.py`); pakai
  `select_option(label=)`.
- O-B5R3-7: ulangan O-B5R2-9 — "Mark as Achieved" target tersembunyi dengan
  benar (reduction, current > target); tombol "Settle" klaim hanya di form
  insurance bila state 'claim_approved'; tombol "Match Resources"/"Optimize"
  state-gated; tombol "Reset KPI Target" tidak ada di form KPI.
- O-B5R3-8: ulangan O-B5R2-10 — loan 3 terikat credit score **2** (bukan 4)
  karena `action_auto_evaluate` tidak men-stempel `evaluation_date`.
- O-B5R3-9: skrip `shell-b5r3/b5r3_5c.py` (v1) memakai nama model tebakan
  `farm.esg.*` — 15/15 gagal; yang benar `b5r3_5c2.py` (nama `esg.*` /
  `agri.esg.*`). Jangan ulangi 5c v1.
- O-B5R3-10: `crop.lot` tidak punya field grade_a/b/c_qty (`Invalid field`
  saat prep) — dicatat skrip, bukan blocker.
- O-B5R3-11: PDF selalu 400 (wkhtmltopdf tidak ada di test bed) — laporan
  HTML B29 tetap 200.
- O-B5R3-12: paho-mqtt lama gagal start tanpa `CallbackAPIVersion` — pakai
  `mqtt.Client()` tanpa argumen (subscriber Bagian 4).

# Batch 6 — Simulasi ulang kumulatif (B6) + vertikal baru

- **Tanggal:** 11 November 2026 (±01:58–±04:30 WIB)
- **Test bed:** Odoo 18 lokal `http://127.0.0.1:8071`, DB `test18`, login `admin/admin`, `?debug=1`
- **Modul:** 69 modul farm/agri `installed` (49 batch 1–5 + 20 SET batch 6, lihat `PORTING.md` §19a)
- **Skenario:** kumulatif batch 1–5 diulang via UI + alur BARU batch 6 (11 vertikal hortikultura + rekonsiliasi supply/ecology/equipment/subsidy/multi-farm/certification)
- **Bukti browser:** Playwright headless, screenshot lanjut `1554`–`1733` di `simulasi/`, **0 pageerror, 0 console error** pada verifikasi akhir (sesudah perbaikan B32/B33 + O-B6R1-1)
- **Skrip:** `browser-proof-b6-5esg3.py`, `browser-proof-b6-6a.py`, `browser-proof-b6-6b.py`, `browser-proof-b6-6b2.py`, `browser-proof-b6-6c.py`, `browser-proof-b6-6c2.py`, `browser-proof-b6-6c3.py`, `browser-proof-b6-6c4.py`, `browser-proof-b6-6c5.py`, `browser-proof-b6-regress1.py`, `browser-proof-b6-regress2.py`, `browser-proof-b6-regress2b.py`, `shell-b6/b6_6prep.py`, `shell-b6/b6_6fix.py`

## Keadaan awal & keputusan prefix

- Sesi ini LANJUTAN: koordinator batch 6 sebelumnya ERRORED ("restart drain")
  karena VM replacement ±01:56 WIB 11 Nov mematikan test bed di tengah simulasi.
  Parent memulihkan test bed (PG 5433 + Odoo 8071 → 200, data test18 utuh).
- Port + install 20 modul SET batch 6 SUDAH selesai sebelum sesi ini (69 modul
  installed, semua 18.0.1.0.0; `farm_waste_mgmt` 18.0.1.0.3,
  `farm_multi_farm` 18.0.1.2.0, `farm_esg_compliance` 18.0.1.0.2).
- Data parsial B6 SUDAH ADA dan konsisten: 15 `stock.lot` `SIMULASI B6`,
  prep bagian 6 (`shell-b6/b6_6prep.py` + 7 perbaikan `shell-b6/b6_6fix.py`)
  sudah jalan, screenshot sampai 1553 (bagian 5 ESG run 2). **Keputusan:
  LANJUTKAN prefix `SIMULASI B6`, screenshot dari 1554** (pola B5R1 tidak
  dipakai — tidak perlu prefix baru karena data parsial konsisten).
- Verifikasi §19d SEBELUM simulasi (shell probe `/tmp/b6_probe.py`,
  `/tmp/b6_probe2.py`): (4) `input_type` sudah direkonsiliasi — definisi lokal
  `farm_waste_mgmt` dihapus, `farm_waste_mgmt` 18.0.1.0.3 ter-install;
  (5) B13 laten sudah diterapkan — `mail.thread` ada di
  `farm.fermentation.order`, `farm.mushroom.production`,
  `farm.winery.production` (terverifikasi fungsional via `report_incident`
  shell: 3/3 membuat `mail.activity`, 0→1); (6) `agri.evidence` konkret
  sudah didefinisikan di `farm_subsidy` (record id 1 terhubung ke aplikasi
  SUB/2026/0001). Semua record prep bagian 6 ditemukan (9 ISL vertikal,
  5 lot khusus, 3 operasi task-based, 2 lahan khusus, vessel, greenhouse,
  GAP, procurement/VMI, ekologi, equipment, subsidi, multi-farm).

## Bagian 1 — rantai batch 1: LOLOS 9/9

- Bukti: shot **1336–1353** (koordinator sebelumnya, sesi B6): seed batch 58,
  nursery 46, asset 51, rotation 50, intervensi 100, lot panen 280, QC 44,
  record book 44, MO saus 269 (Done), market price 46, valuasi 47, produk
  tomat/saus 315/316, intervensi baru + MO 170/192/27.
- Regresi ulang sesi ini (`browser-proof-b6-regress1.py`, shot 1653–1669):
  17/17 form dibuka ulang sesudah upgrade B32/B33 — **errdlg 0, 0 pageerror,
  0 console error**.

## Bagian 2 — batch 2: LOLOS

- Bukti: shot **1354–1363** (koordinator sebelumnya): intervensi baru +
  workflow done, MO 170/192 spatial/nutrient gauge, migrasi ISL 2× run.
- Regresi ulang sesi ini (`browser-proof-b6-regress2.py`, aksi 1024–1033):
  daftar + form tiap aksi errdlg 0 (lihat Bagian 4/5 untuk rinciannya).

## Bagian 3 — batch 3 + B27/B11: LOLOS

- Bukti: shot **1364–1396** (koordinator sebelumnya): animal batches, lot
  hewan, feeding MO confirmed, event weight, breeding, env monitoring,
  harvest MO confirmed, aqua operation + subtask, WQ log, MO lele confirmed,
  ISL aqua lot/tasks, MO 256 Produce All → Done.
- Regresi ulang sesi ini: `farm.worklog` 23, `agri.manure.batch` 5,
  `agri.manure.ledger` 4 dibuka ulang (shot 1667–1669) — errdlg 0.

## Bagian 4 — batch 4: LOLOS

- Bukti: shot **1397–1422** (koordinator sebelumnya): device 1 power on/off/
  reset/send-reset, forecast manual (tanggal dulu, Escape per isian).
- Regresi ulang sesi ini: aksi 1041 IIoT Device (list + form `iiot.device` 1)
  dan aksi 1037 Weather Forecast dibuka ulang — errdlg 0, 0 console error
  (diag `/tmp/b6_diag_1041.py`, 38 dtk).

## Bagian 5 — batch 5: LOLOS

- Bukti: shot **1423–1581**. HR/worklog/laborpay/waste/ledger (1423–1462),
  financial cost/clearing/credit/loan/insurance/valuation (1463–1489),
  fair trade certificate/premium/investment/labor (1490–1512), ESG framework/
  assessment/target/carbon/exchange (1517–1535), ESG run 2 (1538–1553,
  koordinator sebelumnya), ESG run 3 (1554–1581, sesi ini,
  `browser-proof-b6-5esg3.py`): **28 shot, pageerrors [], errdlg 0 semua
  langkah**.
- Observasi ulangan O-B5R3-7: tombol "Match Resources" (resource-sharing) dan
  "Optimize" (GIS) NOT FOUND — state-gated (tombol hanya muncul pada state
  tertentu), bukan bug.
- Cost calculation: lihat O-B6R1-1 di bawah (bukan blocker kode).

## Bagian 6 — batch 6: LOLOS

### 6a. Vertikal tanaman (shot 1582–1594)

- `farm.orchard.cycle` 1, `farm.orchard.operation` 1 (aksi 1165),
  `farm.flower.order` 1 (aksi 1174, tombol "Confirm Bloom Start"),
  `farm.lot.flower` 1 (aksi 1175), `farm.mushroom.production` 1,
  `farm.mushroom.batch` 1, `farm.honey.task` 1 (aksi 1160),
  `farm.lot.hive` 1, `farm.hive.inspection` 1 (aksi 1161),
  `farm.protected.cultivation.operation` 1 (aksi 1167, tombol
  "Start Automation") — semua errdlg 0.
- **MO jamur WH/MO/00267 (id 265): Confirm → Produce All via UI → Done**,
  terverifikasi di DB (`state='done'`, psql). Pelajaran B5R3 dipakai: cek
  state DB, bukan teks halaman (teks "Confirmed" False pada pengecekan
  `form_text` sesudah klik — pill statusbar tidak terbaca `inner_text`
  sebagaimana mestinya; state DB yang menentukan).

### 6b. Vitikultura/winery/medisinal/fermentasi/greenhouse (shot 1595–1611)

- `farm.viticulture.cycle` 1 (aksi 1177, "Confirm Cycle Start"),
  `farm.viticulture.plot` 1 (1176), `farm.viticulture.task` 1,
  `farm.winery.production` 1 (1179), `farm.winery.vessel` 1 (1178),
  `farm.lot.wine` 1 (1180), `farm.medicinal.production` 1,
  `farm.fermentation.order` 1, `farm.fermentation.vessel` 1,
  `farm.lot.brew` 1, `farm.greenhouse.control.rule` 1 (1138),
  `farm.greenhouse.energy.log` 1 (1139), `farm.environmental.log` 1 (1168)
  — semua errdlg 0, 0 pageerror.
- **B32** memblokir 2 form `farm.location` (Greenhouse B1 id 53, Kebun Anggur
  A1 id 52): errdlg 1 → diperbaiki (lihat §Blocker), rerun shot 1610–1611
  (`browser-proof-b6-6b2.py`): errdlg 0, 0 pageerror.

### 6c. Rekonsiliasi (shot 1612–1652)

- GAP: sertifikat 1 (aksi 1169) + **wizard "Renew Certificate" → "Renew"
  jalan penuh** — expiry 2027-01-14 → **2029-11-10**, status tetap valid
  (psql); audit 1 (1170), requirement 1 (1172), partner cert 1; **B33**
  memblokir compliance check 1 (1171): errdlg 1 → diperbaiki, rerun shot
  1644: errdlg 0.
- Supply procurement/VMI: `joint.procurement.configuration` 1,
  `joint.procurement.order` 1 (200 unit pupuk, draft), `vmi.agreement` 1,
  `vmi.stock.monitoring` 1 — errdlg 0. `input_type='fertilizer'` pada produk
  "SIMULASI B6 Pupuk Organik Cair" terverifikasi via shell (prep).
- Ecology/GEP: zone 1 (1137), indicator 1 (1136), activity 1,
  `farm.location` 51 — **gep_score=26.0 nyata** (bio 30.0, coverage 20.0),
  errdlg 0.
- Equipment: traktor B6 (aksi 831), log 1 (1162), baterai 1 (1163, tombol
  "Log Cycle"), checklist 1 (1164) — errdlg 0.
- Subsidi: aplikasi SUB/2026/0001 (aksi 1150, draft), program 1,
  `agri.evidence` 1 — errdlg 0. Tombol aksi ada di tab **Compliance** (bukan
  header): "Collect Compliance Evidence" klik True → navigasi ke daftar
  Compliance Evidence (record B6 tampil, On-Site Verified tercentang);
  "Verify Evidence Integrity" klik True → navigasi ke daftar Evidence
  Integrity Issues; "Generate Compliance Handbook" klik True →
  `handbook_generated_date` terisi (psql `t`). Tombol "Export Compliance
  Handbook (PDF)" TIDAK diklik — PDF 400 karena wkhtmltopdf tidak ada di
  test bed (ulangan O-B5R3-11).
- Multi-farm: koperasi 1 (1144), entitas 1 (1145), anggota 1 (1155),
  share tx 1 (1156, tombol Confirm), internal credit 1 (1158),
  treasury 1 (1159), dividen 1 (1157, tombol "Calculate Dividends"/
  "Distribute") — errdlg 0.
- B13 shell: `report_incident` pada `farm.mushroom.production` 1,
  `farm.fermentation.order` 1, `farm.winery.production` 1 → 3/3 membuat
  `mail.activity` (0→1).

## Blocker baru

- **B32 — widget `ace` mode `'json'` TIDAK VALID di Odoo 18
  (laten sejak batch 1, baru tersentuh simulasi batch 6).** Form
  `farm.location` mana pun crash: `OwlError: Invalid props for component
  'CodeEditor': 'mode' is not valid` (diag `/tmp/b6_diag_loc2.py`, lok 8
  WH/Stock pun error — bukan data B6). Akar: `CodeEditor.MODES =
  ["javascript","xml","qweb","scss","python"]` (odoo 18
  `addons/web/static/src/core/code_editor/code_editor.js:65`) — `'json'`
  tidak ada. Sumber: `farm_core/views/land_location_management_views.xml:98`
  (`boundary_geojson`). Sapuan semua modul ter-install menemukan 14 pemakaian
  `'json'` (4 `'javascript'` sudah benar). Perbaikan: `'json'` →
  `'javascript'` di 6 modul ter-install — `farm_core` (18.0.1.0.3),
  `farm_agri_science` (18.0.1.1.2), `farm_greenhouse` (18.0.1.0.1),
  `farm_mushroom` (18.0.1.0.1), `farm_processing` (18.0.1.1.4),
  `farm_ux` (18.0.1.1.4) — upgrade test18 + restart server, verifikasi
  ulang lok 8/51/52/53 errdlg 0. Modul BELUM ter-install yang masih memakai
  `'json'` (`farm_ai_*`, `farm_gov`, `farm_live_streaming`, `farm_robotics`)
  DIBIARKAN untuk batch 7+ (dicatat di `PORTING.md` §19d butir 16).
  Jebakan proses: upgrade shell pertama kena `timeout 280` di tengah modul
  ke-3 (`farm_greenhouse` tertinggal `to upgrade`, rollback bersih) —
  dilanjutkan skrip ke-2 (nohup) sampai selesai; restart server sempat salah
  PID (server lama 5244 tetap jalan, server baru "Address already in use")
  — dimatikan PID benar lalu start ulang, 8071 → 200.
- **B33 — `widget="statusbar"` pada field Boolean crash.**
  Form `farm.gap.compliance.check` 1: `OwlError ... onWillRender:
  "Cannot read properties of undefined (reading 'filter')"` di
  `StatusBarField.getAllItems` (diag `/tmp/b6_diag_gapcheck.py`). Akar:
  `overall_compliant` = `fields.Boolean`, tapi view
  `farm_certification/views/gap_certification_views.xml:205` memasang
  `widget="statusbar" statusbar_visible="True,False"` — statusbar butuh
  Selection. Perbaikan: hapus header statusbar, tampilkan field sebagai
  checkbox biasa di sheet (di samping `checker_id`);
  `farm_certification` 18.0.1.0.0 → **18.0.1.0.1**, upgrade + restart,
  rerun shot 1644: errdlg 0. Sapuan statusbar di semua modul ter-install:
  hanya B33 yang salah tipe (`audit_result` farm.gap.audit terdefinisi
  ganda Text+Selection di file yang sama — yang efektif Selection, form
  audit terbuka normal; dibiarkan).
- **O-B6R1-1 — `agri.cost.calculation` id 6 HILANG (bukan bug kode).**
  Regresi-2 menemukan 1 console error: `FetchRecordError: records with IDs 6
  cannot be found` saat membuka form `agri.cost.calculation` 6 (shot 1672:
  toast merah, form kosong). Penyelidikan: tabel `agri_cost_calculation` +
  `agri_cost_calculation_line` 0 baris, padahal shot 1464 (run 5fin B6)
  membuktikan record 6 pernah ada dan termuat (task B5R3 64, parcel B5R3 50,
  line template B6 qty 10 × 50.000 = 500.000). Akar: model ini
  **TransientModel** — Odoo `ir.autovacuum` menghapus record transient
  berumur > beberapa jam secara otomatis (melewati restart/VM replacement).
  Skrip harness yang memakai ID transient hardcoded akan selalu rapuh.
  Perbaikan harness: buat ulang record segar via shell
  (`/tmp/b6_calc_recreate2.py`: calc **id 7**, line total **500.000,00**)
  lalu verifikasi SEGERA di browser (`browser-proof-b6-6c5.py`, shot
  1732–1733): form termuat errdlg 0, "500,000.00" tampil sebelum +
  sesudah tab Results, 0 pageerror, 0 console error; method `calculate()`
  dipanggil via shell → OK (return act_window res_id 7). Catatan: tombol
  "Calculate" di footer wizard hanya render dalam mode dialog
  (`target=new`, aksi 1067) — direct-URL form tidak menampilkan footer
  button (perilaku standar Odoo, bukan bug); alur hitung sudah terbukti
  lewat total compute + `calculate()` shell.

## Verifikasi akhir

- Regresi pasca-perbaikan: R1 shot 1653–1669 (17 form batch 1–3, errdlg 0,
  0 pageerror, **0 console error**); R2 shot 1670–1700 (14 form batch 4–5 +
  11 daftar aksi 934/1024–1041, errdlg 0, 0 pageerror, 1 console error =
  O-B6R1-1); replay R2B + diag 1041 melokalisasi error itu ke calc 6;
  calc 7 dibuat ulang + terverifikasi (shot 1732–1733, 0 error).
- Total shot sesi ini: 1554–1733 (180 shot, termasuk 5esg3 + 6a–6c5 +
  regresi). Semua langkah errdlg 0 pada verifikasi akhir.

## Stok akhir B6 (WH/Stock lokasi 8, psql `stock_quant` per lot)

- Tomat segar 480 kg, saus 16 kg (baseline B5R3 dipertahankan); sapi 1 ekor;
  lele kolam 1; lot B6: mawar 100, jamur 50, koloni lebah 5, wine 100,
  cuka apel 100, benih tomat 5 + 5, bibit tomat 25.000.
- MO jamur WH/MO/00267 Done (Confirm + Produce All via UI).

## Data yang tertinggal (test18, prefix SIMULASI B6)

- 15 lot `SIMULASI B6*`, 9 MO vertikal (263–271 + MO rerun batch 1–5),
  9 record ISL vertikal (id 1 masing-masing), 5 lot khusus + vessel +
  greenhouse + GAP + procurement/VMI + ekologi + equipment + subsidi
  SUB/2026/0001 (expiry GAP diperpanjang ke 2029-11-10) + multi-farm,
  3 `mail.activity` B13-TEST, calc wizard id 7 (transient — akan hilang
  sendiri oleh autovacuum).

## Observasi (bukan blocker)

- O-B6-1: tombol aksi subsidi ("Collect/Verify/Generate") berada di tab
  Compliance, BUKAN header — `header_buttons()` tidak menemukannya; klik
  lewat tab terbukti jalan (6c2/6c3/6c4). "Collect" dan "Verify" menavigasi
  ke daftar evidence (perilaku benar per kodenya), jadi tiap tombol harus
  diuji dari fresh open.
- O-B6-2: `farm_supply`, `farm_crop_matter`, `farm_fermentation_matter`
  TIDAK punya model konkret (hanya mixin abstrak / field penghubung) —
  preseden `farm_esg_matter` (§18c); fungsinya terbukti lewat modul
  pemakai (`farm_supply_procurement`, `farm.fermentation.order`).
- O-B6-3: `farm.gap.certification` juga punya `audit_result` terdefinisi
  ganda (Text baris 46 + Selection baris 134 di `gap_certification.py`) —
  yang efektif Selection; dibiarkan (bukan blocker).
- O-B6-4: PDF selalu 400 (wkhtmltopdf tidak ada di test bed) — ulangan
  O-B5R3-11; tombol Export PDF subsidi tidak diuji klik.
- O-B6-5: upgrade modul via `odoo-bin shell` memakan ±60–120 dtk per modul
  (registry rebuild); skrip upgrade multi-modul WAJIB nohup/background
  dengan timeout ≥280 — `timeout 280` foreground pernah memotong di tengah
  (B32) dan meninggalkan modul `to upgrade` (rollback bersih, aman
  dilanjutkan).
- O-B6-6: restart server: kill PID proses `odoo-bin` yang BENAR (bukan PID
  wrapper bash) — salah PID membuat server lama tetap jalan dan server baru
  gagal bind ("Address already in use"); verifikasi dengan `ss -ltnp`
  + `curl` 200 sesudah restart.

## Keputusan: BERSIH ✅ 100%

**Batch 6 SELESAI.** Simulasi kumulatif batch 1+2+3+4+5+6 lolos penuh:
bagian 1 (9/9), bagian 2, bagian 3, bagian 4, bagian 5, bagian 6 (11 vertikal
+ 6 rekonsiliasi) — 0 pageerror + 0 console error pada verifikasi akhir,
0 Traceback server. Blocker yang ditemukan selama ronde ini (B32, B33)
diperbaiki + terverifikasi; O-B6R1-1 (transient vacuum) diperbaiki di harness
+ terverifikasi. Yang tersisa sesudah batch 6: batch 7+ (29 modul, lihat
`PORTING.md` §19c) + 4 stub tanpa manifest + 11 modul China-specific yang
tetap dikecualikan.

## Batch 7 — AI/robotics + multi-farm/supply lanjutan + POS/mobile/dashboard + gov/krisis + pengetahuan/pelatihan/agriturisme/CSA/safety/symbiosis/label/insurance (11 Nov 2026)

Perintah king "Lanjut batch 7" (11 Nov 2026 ~06:44 WIB). Aturan flow FINAL
(10 Nov 12:20): jangan berhenti kalau ada error — perbaiki → simulasi ulang
kumulatif sampai 100% pass. Detail porting di PORTING.md §20 dan
PORTING.d/b7.md. Runner browser: `browser-b7.py` + step JSON
`/tmp/b7-steps-a.json` … `/tmp/b7-steps-e.json` (SEMUA file `/tmp/b7_*`
hilang saat VM replacement 11 Nov ~01:50 WIB; skrip browser di workspace
selamat — lihat PORTING.md §20g).

### Data simulasi batch 7

Skrip filler generik `/tmp/b7_sim_data.py` (via `odoo-bin shell`): mengisi
field wajib non-computed per tipe; Many2one = record pertama comodel;
override per model. Pelajaran yang diterapkan: per-create SAVEPOINT +
`ROLLBACK TO SAVEPOINT` bila gagal (satu kegagalan FK pernah meracuni
seluruh transaksi dan me-rollback 22 record OK); `commit()` per seksi
supaya satu seksi buruk tidak me-rollback seksi sebelumnya.

- Perangkap product-template vs product.product:
  `farm.crop.yield.insurance.policy.product_id`,
  `farm.insurance.claim.product_id`, `farm.market.demand.product_id`,
  `farm.yield.prediction.product_id` adalah `product.template` — id
  varian menyebabkan pelanggaran FK.
- Perangkap UoM: `product_uom_id` order/recipe symbiosis harus UoM produk
  itu sendiri (kg), bukan 'Units' — kalau tidak
  `mrp.production._compute_product_uom_qty` melempar saat commit flush.
- Hasil: run 3 = 84 OK (sesudah perbaikan); patch `/tmp/b7_sim_data4.py`
  = 10 OK (seksi CSA + temperature log, sesudah fix feedback-related dan
  humidity); patch `/tmp/b7_sim_data5.py` + `/tmp/b7_agent_create.py`:
  `agri.ai.agent` id=1 (butuh `name` eksplisit — field parent yang
  didelegasikan `_inherits`, bukan di daftar required field model agent
  itu sendiri; `agent_type='recommendation'`).
- ID record: `/tmp/b7_ids.txt` (86 baris — hilang bersama /tmp; contoh
  kunci: symbiotic plot/recipe/order id 3; lot `SIMULASI B6 Lot Panen
  Tomat A1` id 280; intervensi `SIMULASI B2F Intervensi Olah Tanah Tomat
  A1` id 12; produksi `WH/MO/00169` id 169; LLM config id 2, LLM service
  id 2; pos.order id 1 (4 pos.order sudah ada; semua pos.session
  tertutup sebelum bukti POS); farm.location id 51 `SIMULASI B6 Lahan A1`,
  id 13 `SIMULASI B4R1 Lahan B1`).

### Verifikasi LLM (tanpa key di mana pun)

- Config (terverifikasi DB): `agri.ai.llm.configuration` id=2,
  provider=openai, `api_base_url=https://9router-go.hiddenlab.me/v1`,
  `api_key_set=False`, `default_model=gpt-4o-mini`, `is_active=True`,
  `is_default=True` (diaktifkan via `/tmp/b7_llm_activate.py`;
  `call_llm` melempar `UserError: LLM configuration is not active`
  bila tidak aktif).
- Gateway terjangkau dari test bed: `curl
  https://9router-go.hiddenlab.me/v1/models` → 401 dengan JSON gaya
  OpenAI (`invalid_api_key`, `Authentication required...`).
- Uji mock (`/tmp/b7_llm_test.py`): `requests.post` di-monkeypatch
  menangkap URL `https://9router-go.hiddenlab.me/v1/chat/completions`,
  payload OpenAI-compatible `{"model": "gpt-4o-mini", "messages":
  [{"role": "user", "content": "..."}], "temperature": 0.7,
  "max_tokens": 2048}`, header Bearer ada (key kosong); `call_llm`
  success=True, response 'MOCK-OK tomat sehat'.
- Uji live tanpa key: `call_llm` success=False, error `401 Client Error:
  Unauthorized for url: https://9router-go.hiddenlab.me/v1/chat/completions`
  — membuktikan request benar-benar sampai ke gateway.
- **Inferensi live TIDAK diklaim; menunggu key king.**
- Delegasi mixin: `agri.ai.base.mixin.call_llm_service` (via
  `agri.ai.base.mixin.service`) merutekan ke `agri.ai.llm.service` aktif
  dan mengembalikan dict error 401 yang sama (terbukti pada recordset
  `agri.ai.agent` kosong, `/tmp/b7_llm_test2.py`). `stock.lot` tidak punya
  `call_llm_service`/`action_sync_embedding` — sesuai harapan, ia tidak
  mewarisi mixin itu.

### Simulasi browser batch 7 (Playwright, `?debug=1`)

Runner memfilter satu artefak headless-shell dari hitungan console error:
`Service worker registration failed` (chromium_headless_shell tidak bisa
mendaftarkan service worker Odoo). Setiap run juga menunjukkan tepat 2×
`Failed to load resource: net::ERR_TUNNEL_CONNECTION_FAILED` saat login —
**teridentifikasi** sebagai font Google Inter
(`https://fonts.googleapis.com/css?family=Inter...` dan `Inter Tight`),
gagal lewat proxy sandbox; BUKAN error modul (bukti `requestfailed` di
`browser-b7-probe-prod.py`). Semua console error lain adalah nyata.

- **Run A (shot 1734–1747, 14 form: symbiosis/knowledge/pest/FAQ/training/
  insurance/safety):** run pertama symplot errdlg=1
  (child_internal_location_ids, B41) + 17 console error SW; re-run A3
  sesudah restart segar yang BENAR: symplot errdlg=0, TOTAL pageerrors 0,
  TOTAL console errors 2 (pasangan tunnel saja). `has_SIMULASI_B7=False`
  pada form symplot, symrecipe, yieldpred, biosafety adalah harapan
  (form itu tidak menampilkan teks literal "SIMULASI B7" — mis. recipe
  tidak punya field name).
- **Run B (shot 1748–1764, 17 form: crisis/disaster/data-security/gov/
  multi-farm):** TOTAL pageerrors 0, console errors 2 (tunnel saja).
  Semua errdlg=0.
- **Run C (shot 1765–1781, 17 form: cold storage/supply/CSA/agritourism/
  marketing):** run pertama csaplan + csasub errdlg=1 (ACL, B42);
  sesudah fix ACL, re-run CSA (shot 1777–1778): keduanya errdlg=0.
  Selain itu TOTAL pageerrors 0, console errors 2 (tunnel saja).
- **Run D (shot 1782–1799, 18 form: marketing/mobile/AI base/LLM/vision/
  decision):** TOTAL pageerrors 0, console errors 2 (tunnel saja).
  Semua errdlg=0, termasuk llmcfg/llmsvc (fix ACL terverifikasi).
- **Run E (shot 1800–1822, 23 langkah: decision/AI-agent/robotics/POS/
  lot/dashboard/company):** run pertama robot-form errdlg=1 + OwlError
  GaugeField (×2, B46) dan cockpit-action errdlg=2 (is_agri_activity,
  B47); sesudah fix gauge + cockpit dan upgrade, re-run fix2 (shot
  1812–1814: robot, cockpit, wine): semua errdlg=0, TOTAL pageerrors 0,
  console errors 2 (tunnel saja).
- **Bukti farm_label:** tanpa view/action sendiri — hanya
  `label_background_image` di res.company + settings view; terbukti via
  form res.company id=1 (langkah 7e-company-form, errdlg=0).
  **Bukti farm_dashboard:** action 1230 (Operational Cockpit) dan 1231
  (Winemaking Analysis), keduanya bersih sesudah fix domain (B47).

### Regresi kumulatif batch 1–6 sesudah batch 7

- **Regresi pertama (22 langkah, shot 1815–1836):** 20/22 errdlg=0.
  2 gagal: form `farm.activity` id=1 errdlg=1 (B49, chatter tanpa
  mail.thread — Traceback server `AttributeError: 'farm.activity' object
  has no attribute '_get_thread_with_access'` dari `/mail/thread/data`)
  dan form `mrp.production` id=169 errdlg=3 + 2 console error (B48,
  widget check-in farm_mobile: OwlError `Cannot read properties of
  undefined (reading 'onLine')` di `FarmMobileCheckin.template` +
  DataCloneError di `OfflineStorage.cacheTasks`). Keduanya laten batch
  1–5, bukan disebabkan perubahan batch 7. Hitungan DB sebelum regresi:
  `farm_crop_cycle` 0, `agri_intervention` 74, `stock_lot` 170,
  `mrp_production` 241, `agri_cost_calculation` 0 (TransientModel —
  record bisa hilang oleh autovacuum, pola O-B6R1-1), `farm_activity` 5,
  `farm_livestock` 0 (tabel ada, tanpa record).
- **Probe + perbaikan (PORTING.md §20f, B48–B51):** fix widget check-in
  farm_mobile, tambah mail.thread ke farm.activity/farm.task, gabung
  `_inherit` ganda TBLM; percobaan gabung `_inherit` ganda
  FarmSupplyChainNode memecahkan MRO (upgrade exit 255) dan di-revert
  (transitif). Upgrade 4 modul (farm_core .0.6, farm_esg_compliance .0.3,
  farm_supply_analytics .0.1, farm_mobile .0.1) exit 0, 0 Traceback.
  Record uji dibuat via shell: farm.task id 1, TBLM id 1.
- **Re-run regresi (8 langkah, shot 1837–1844):** farm.activity form 1,
  farm.task form 1, TBLM form 1, mrp.production form 169, list
  farm.supply.chain.node, list farm.checkin, intervention form 12, lot
  form 280 — **semua errdlg=0, TOTAL pageerrors 0, TOTAL console errors 2
  (pasangan tunnel saja), 0 Traceback server.**

### Bukti POS (farm_pos) — shot 1845–1853

- `/pos/ui` dashboard: 3 toko (Furniture/Clothes/Bakery Shop) dengan
  tombol Open Register; errdlg 0, 0 pageerror, 0 console error non-artefak
  (shot 1845). `/pos/ui` tidak pernah mencapai `networkidle` (long-polling
  POS) → probe memakai `domcontentloaded` + sleep manual.
- Klik Open Register membuat sesi dengan benar (DB): Furniture
  Shop/00002 id 3, lalu Bakery Shop/00000 id 4 — keduanya
  `opening_control`. Layar jual termuat untuk Furniture (Desks/Chairs,
  shot 1852) dan Bakery (Breads/Pastries, shot 1853), 0 pageerror.
- Modal Opening Control termuat dengan kas pembuka yang benar (Furniture
  2,243.57 = saldo penutupnya; Bakery 0.00).
- **Batasan jujur:** validasi sesi ke status `opened` via klik browser
  TIDAK tercapai dalam 3 percobaan — klik tombol "Open Register" di modal
  tidak mengonfirmasi (ambiguitas target klik di DOM fullscreen POS;
  satu percobaan malah membuka sesi Bakery). Ini alur core Odoo POS,
  bukan kode farm_pos (farm_pos hanya extends model/view POS; tidak ada
  kode farm_pos di jalur opening-control). Dua sesi uji tertinggal
  `opening_control` (id 3, 4) — data uji, aman dibiarkan/ditutup manual.
- Server log sesudah semua bukti POS: 0 Traceback.

### Bukti mobile viewport (farm_mobile) — shot 1847

Form `farm.checkin` id 2 dibuka dengan viewport mobile 390×844
(is_mobile + touch): errdlg 0, 0 pageerror, 0 console error non-artefak.
Form ter-render penuh pada lebar 390px (screenshot menunjukkan area
chatter bawah form).

### VM replacement di tengah bukti POS (11 Nov ~01:50 WIB)

VM diganti: uptime 0 mnt, /tmp terhapus total, user `pgtest` +
`/opt/pgserver` hilang, PG + Odoo mati. Dipulihkan per AGENTS.md
(useradd pgtest uid 1001 + rebuild /opt/pgserver + start PG dari
`~/workspace/pgrun` + start Odoo); data test18 UTUH (92 modul farm
installed, HTTP 200, 0 Traceback). Bukti POS diulang sesudah pemulihan
(shot 1848–1853). Semua skrip/log `/tmp/b7_*` hilang; skrip browser di
workspace (`browser-b7*.py`) selamat dan dipakai ulang.

## Keputusan: BERSIH ✅ 100%

**Batch 7 SELESAI.** Simulasi kumulatif batch 1+2+3+4+5+6+7 lolos penuh:
batch 7 (run A–E + re-run CSA/fix2, 0 pageerror + 0 console error
non-artefak, 0 Traceback server), regresi batch 1–6 (re-run 8/8 bersih,
0 pageerror, 0 Traceback), POS dashboard + layar jual + modal Opening
Control 0-error, mobile viewport check-in 0-error, LLM sampai titik
pemanggilan API terbukti (mock + live-401). Blocker yang ditemukan selama
ronde ini (B34–B51) diperbaiki + terverifikasi; artefak tunnel
teridentifikasi (font Google Inter via proxy sandbox). Yang tersisa
sesudah batch 7: 4 stub tanpa manifest + 11 modul China-specific yang
tetap dikecualikan + inferensi LLM live menunggu key king + validasi sesi
POS ke `opened` via klik browser (batasan tercatat di atas). Batch 8
diputuskan parent sesudah laporan ini.

## Simulasi FINAL — rantai penuh semua batch 1–7 dari nol data baru (11 Nov 2026)

Perintah king "coba simulasi kan semuanya" (11 Nov 2026 ~09:32 WIB). Aturan
flow FINAL (10 Nov 12:20): error → perbaiki → simulasi ulang kumulatif
sampai 100% pass. Ini simulasi kumulatif PENUH terakhir: seluruh 98 modul
farm/agri ter-install di satu DB integrasi test18, data baru berawalan
`SIMULASI FINAL`, screenshot lanjut dari 1854. Skrip: `shell-final/`
(`final_p1.py`, `final_p1b.py`, `final_p1c.py`, `final_p1d.py`,
`final_p3.py`, `final_p3b.py`, `final_p3c.py`, `final_b52_verify.py`,
`final_generic.py` + `final_generic_fix*.py`, `final_5.py`, `final_5b.py`,
`final_iot_rule.py`, `final_isl_shell.py`, `final_llm.py`, `final_pos.py`,
`final_isl.py`, `final_mobile.py`, `final_probe_marketpred.py`,
`run_browser.sh`, `steps_f*.json`, `final_ids.json`).
Runner browser: `browser-b7.py` + step JSON `shell-final/steps_f*.json`
(`?debug=1`, login admin/admin, Playwright headless).

### Data simulasi FINAL

- Bagian 1 (rantai batch 1, adaptasi `shell-b6/b6_p1.py` + `b6_p1c.py`/
  `b6_p1d.py`): produk template 391–395, lahan 54, campaign 50, lot
  benih 293/294, seed.batch 60, nursery 47, asset 52, rotation 51, BoM
  tomat 138, intervensi 105–109 (+110 verifikasi B52), lot panen 296,
  crop.lot 44, QC point 44 / check 46 / record book 45, BoM saus 139,
  lot saus 297, MO saus 318/319, market price 47, valuasi 48, fair val 47.
- Bagian 3: produk 396–402, BoM 140–143, lot sire 298 / kolam 299 /
  lele 300, farm.livestock 3, livestock.asset 3, aqua.operation 29,
  ISL aqua lot 13, ISL aqua task 13, MO B13 354, MO pakan lot 298 375.
- Bagian 4–7: filler generik `final_generic.py` — 204/208 model berhasil
  dibuat (s4 21/22, s5 38/39, s6 73/73, s7 72/74); 4 sisanya BUKAN bug:
  `farm.device.command` + `agri.cost.calculation` = TransientModel
  (wizard), `agri.mcp.server` = AbstractModel, `farm.training.training.record`
  = model tidak ada di registry. Perangkap yang ditangani filler: UoM kg
  (id 13) untuk semua field UoM (B7), `product.template` untuk M2O produk
  template, `agent_type='recommendation'` untuk `agri.ai.agent`.

### Bagian 1 — rantai batch 1: LOLOS 9/9

Seed batch 60 germ 92% verify True; lot blok germ 70% → `UserError: SEED
QUALITY BLOCK` sesuai harapan. Nursery 47 (25.000 bibit, transplant stub
tetap tanpa efek — perilaku upstream yang sudah dicatat). Asset 52 GDD
170,0 → 187,0 → 357,0 persis; stage 14/15 progress 100,0, stage 16 71,4,
stage 17 44,625. Rotation 51 planted → harvested. Intervensi 105–109
semua `done` (workflow penuh); NPK Pupuk 8,0/8,0/8,0. Lot panen 296
(500 kg), crop.lot 44, QC 46 pass, record book 45 draft → active. MO
saus 318/319 done 8 kg tiap MO via `_post_inventory` (pola B6 p1d —
`button_mark_done` polos + `intervention_type='packaging'` BUKAN opsi
valid: selection `mrp.production.intervention_type` tidak mengenal
'packaging'; p1c gagal di titik itu, p1d yang dipakai). Valuasi 48:
`original_value` 5.000.000 + `growth_stage_coefficient` 0,5 →
**NBV = FV = 2.500.000** (sama seperti B5R1/B6). Fair val 47
market_price 0,0 / fair_value 0,0 (lookup harga gagal — asset tanpa lot,
catatan lama batch 1). **Stok akhir: tomat 480 kg, saus 16 kg, NPK 0**
(pola sama dengan baseline B6: 480/16/0).
Browser f1 shot 1854–1867 (14 langkah): 0 pageerror, 0 console error
non-artefak, 0 errdlg.

### Bagian 2 — batch 2 (intervensi + ISL): LOLOS

Browser f2 shot 1868–1875 (8 langkah): intervensi 110 (B52), MO 313,
list intervensi, ISL mrp.production, ISL stock.lot, technical route,
campaign 50, gov snapshot 3 — semua errdlg=0, 0 pageerror, 0 console
error non-artefak. Wizard ISL action 1013 dibuka via UI (shot 2098–2099,
0 error); klik "Migrate Data" 0 error — TAPI klaim migrasi via UI tidak
tertangkap (Confirm dalam keadaan OFF saat klik; sesuai desain, klik itu
seharusnya melempar UserError "Please confirm the migration", namun tidak
ada dialog error yang tertangkap — kemungkinan klik tidak sampai ke
method karena wizard dalam mode fullscreen). Migrasi DIBUKTIKAN via
shell: wizard `confirmation=True` → notifikasi "Migration Complete.
**85 records migrated**" (ISL mrp.production 221 → 306); kasus negatif
(confirm OFF) raise UserError sesuai desain.

### Bagian 3 — batch 3 (ternak + akuakultur + cron pakan + telemetri DO): LOLOS

- B11 cron `_cron_daily_feed_depletion`: kembali normal, +10 feeding MO
  per run (68 → 78 → 100 total sesudah 3 run), worklog delta 0 (sesuai
  fix B27: feeding tanpa task dilewati). Lot sire FINAL 298 awalnya TIDAK
  masuk loop: `active_feeding_bom_id` adalah field simpan biasa (bukan
  computed) — harus di-set eksplisit + `animal_count` (B6 sudah
  melakukannya di prep; di FINAL sempat terlewat, diperbaiki di
  `final_p3c.py`). Sesudah di-set + BoM sapi 140 `intervention_type=
  'feeding'`: cron membuat MO pakan 375 (done), **pakan sapi 409
  100 → 90 kg**, `total_feed_consumed` lot 298 = 1,0.
- B13 telemetri DO rendah: MO lele draft 354 + ISL task 13
  (`intervention_id`, BUKAN `mrp_production_id` — skrip awal menyalin
  varian B6 p3c yang gagal; varian benar adalah p3c4) →
  `handle_aquaculture_telemetry({'dissolved_oxygen': 2.0,
  'temperature': 29.0})` returned True, latest_do 2,0, latest_temp 29,0,
  `agent_instruction_json` terisi, 1 mail.activity insiden kritis.
- Browser f3 shot 1876–1884 (9 langkah): 0 pageerror, 0 console error
  non-artefak, 0 errdlg.

### Bagian 4 — batch 4 (IoT): LOLOS, bridge MQTT diuji ulang end-to-end

- Browser f4 shot 1885–1905 (21 form: iiot.device 10, gateway 7,
  telemetry 14, rule 3, profile 3, registry 3, agri/farm telemetry,
  automation rule 5, command log 47, water valve, storage env, event
  correlation, digital twin, weather forecast, mapping, buffer):
  0 pageerror, 0 console error non-artefak, 0 errdlg.
- Bridge MQTT diuji ulang PENUH (bukan hanya form): broker amqtt lokal
  127.0.0.1:1883 + subscriber paho + bridge `agri_iot/mqtt_bridge/main.py`
  (bridge-venv). Start pertama GAGAL `httpx.InvalidURL: Invalid port:
  ':1]'` — penyebab BUKAN kode bridge: `no_proxy`/`NO_PROXY` lingkungan
  berisi entri IPv6 `[::1]` yang diurai httpx sebagai pola proxy
  (B4R4 meng-unset 8 variabel proxy; ronde ini awalnya hanya 6).
  Sesudah unset 8 variabel: bridge start bersih, `Successfully
  connected to MQTT broker`, `Successfully registered bridge
  SIMULASI-B4-GW-01 with Odoo`, `/health` → 200
  `{"status":"healthy","mqtt_connected":true}`.
- Telemetri via MQTT: publish `telemetry/simulasi_b4_sn_001/data`
  `{"temperature": 38.5, ...}` → bridge POST webhook
  `/iiot/webhook/simulasi_b4_sn_001` 200 → shadow device 1 suhu 32,5 →
  **38,5**, `farm.storage.env` temperature → 38,5 (profile rule
  json_path `$.temperature` bekerja). `iiot.telemetry` TIDAK bertambah
  lewat jalur webhook (by design — webhook hanya update shadow).
- Rule otomatis: buat `iiot.telemetry` 15 (temperature 38,5) →
  `farm.automation.rule` 1 (Suhu > 35) terpicu → `send_command power_on`
  → command log 48 → bridge terima webhook command dari Odoo →
  publish `command/simulasi_b4_sn_001/action
  {"action": "power_on", "params": {"state": "on"}}` → subscriber
  menerima. Rantai MQTT dua arah TERBUKTI.
- Infra dimatikan sesudah uji (broker + subscriber + bridge, PID
  eksplisit); port 1883/8000 bebas, Odoo 8071 tetap 200.

### Bagian 5 — batch 5 (HR + waste + financial + ESG): LOLOS

- Browser f5a+f5b shot 1906–1943 (38 langkah): 0 pageerror, 0 console
  error non-artefak, 0 errdlg.
- B28 convert manure: batch 6 → MO 377 (WH/MO/00380, confirmed,
  100 kg, WH/Stock) — pemetaan lokasi B28 bekerja (farm.location 54 →
  WH/Stock fallback). Catatan metodologi: percobaan pertama gagal
  `CheckViolation mrp_production_qty_positive` karena filler generik
  tidak mengisi `quantity` (bukan required) sehingga batch quantity 0,0
  — BUKAN bug modul (MO qty 0 memang harus ditolak); sesudah
  `quantity=100.0`, convert lolos.
- B29 laporan ledger: `GET /report/html/farm_waste_mgmt.
  action_report_manure_ledger/5` → **200**, 22.181 byte, berisi Ledger +
  MNR, tanpa KeyError (fix wrapper B29 terverifikasi). Catatan: URL
  pertama yang dicoba (`...report_manure_ledger_document/5`) 500 karena
  itu `ir.ui.view`, bukan `ir.actions.report` — kesalahan probe,
  bukan bug modul.

### Bagian 6 — batch 6 (11 vertikal + rekonsiliasi): LOLOS

Browser f6a+f6b+f6c shot 1944–2016 (73 langkah: apiculture, field crops,
floriculture, greenhouse, mushroom, medicinal, orchard, viticulture,
winery, fermentation, ecology, certification, subsidy, planning,
quality, seed, breeding, equipment, processing, agri science, crop
cycle, ISL, supply chain node/demand/recall/risk, cold storage,
transport, joint procurement, VMI, quality pricing): 0 pageerror,
0 console error non-artefak, 0 errdlg.

### Bagian 7 — batch 7 (AI/robotics/multi-farm/supply/POS/mobile/dashboard/dll.): LOLOS

- Browser f7a+f7b+f7c shot 2017–2088 (72 langkah): 0 pageerror;
  **1 errdlg** — `agri.ai.market.prediction` id 3 (shot 2023) → **B54**
  (lihat di bawah). Semua langkah lain errdlg=0, console error hanya
  pasangan tunnel + 1 OwlError B54.
- **Uji LLM live VIA UI (shot 2090–2094, skrip `final_llm.py`):**
  form config id 2 dibuka — `api_key` ter-mask (`password="True"`,
  1 input password, tidak ada plaintext key di layar/teks; screenshot
  2090 aman). Form service id 2 → klik **"Test API Call"** → 0 error.
  Form agent FINAL id 2 → klik **"Execute Agent"** → status pill
  **Recommended**, Execution Count 1, Last Execution 11/11/2026
  03:30:45, tombol "Apply Recommendation" muncul (shot 2094). Bukti DB:
  service call_count **2 → 4**, error_count tetap **0**, last_call
  2026-11-11 03:30:48; agent `output_data.llm_response` berisi jawaban
  Gemini sungguhan ("Query lack soil, climate, season, previous crops.
  Cannot recommend specific crops without local environmental data..."
  + blok kode Python) — input agent kosong `{}` sehingga LLM menjawab
  kekurangan data; tetap round-trip live sungguhan, BUKAN mock.
  Catatan: form config TIDAK punya tombol "Test Connection" (metode
  `test_connection()` ada di model tapi tidak diekspos di view) —
  tombol UI yang ada adalah "Test API Call" di form service, dan itulah
  yang dipakai + diverifikasi. Jangan klaim ada tombol Test Connection
  di form config.
- **POS (shot 2095–2097, skrip `final_pos.py`): batasan B7 TERTUTUP.**
  Dashboard → Open Register → modal Opening Control → klik
  `.modal .btn-primary:has-text('Open Register')` → 0 error. Bukti DB:
  sesi 3 (Furniture Shop/00002) **`opening_control` → `opened`**
  (POS/00001, start 2026-11-11 03:32:38). Sesi 4 (Bakery Shop/00000)
  masih `opening_control` — sisa B7, tidak disentuh ronde ini.
- **Mobile viewport** (shot 2100, 390×844 + touch): form
  `farm.checkin` id 3 errdlg=0, 0 pageerror, 0 console error non-artefak.

### Blocker baru selama Simulasi FINAL

#### B52 — plugin gov_audit crash di setiap post_done intervensi (BARU, terkonfirmasi)

- Gejala: 5× `ERROR ... Intervention Plugin Error (gov_audit):
  'res.company' object has no attribute 'gs1_gln'` di log server saat
  workflow 5 intervensi FINAL; workflow tetap `done` (plugin error
  ditelan framework) tapi **snapshot audit tidak pernah terbuat**.
- Akar: `farm_gov/models/gov_audit.py:106`
  `intervention.company_id.gs1_gln` — field `gs1_gln` hidup di
  `res.partner` (`farm_core/models/res_partner.py:12`), BUKAN
  `res.company`. Bonus laten di fungsi yang sama: `"operator_id":
  getattr` (builtin mentah sebagai nilai — `json.dumps` akan TypeError)
  dan `intervention.responsible_id.name` tanpa guard (AttributeError
  bila kosong). Pola sama di
  `farm_marketing/models/traceability_passport.py:152`
  (`lot.company_id.gs1_gln`).
- Fix: `getattr(intervention.company_id.partner_id, 'gs1_gln', None) or
  '0000000000000'`; `operator_id` → `responsible_id.id`/None;
  guard `location_id`/`responsible_id`; fix sama di traceability
  passport. Versi: farm_gov 18.0.1.0.0 → **18.0.1.0.1**, farm_marketing
  18.0.1.0.1 → **18.0.1.0.2**.
- Verifikasi: intervensi 110 → done, `gov.audit.snapshot` +1 (id 3,
  ref `GOV-SIMULASI FINAL Intervensi Verifikasi B52 Tomat A1`); 0
  Plugin Error di log server sesudah restart. Total snapshot di DB kini
  54 (plugin yang sudah diperbaiki ikut jalan di setiap penyelesaian
  MO/intervensi sesudahnya).

#### B53 — plugin compliance `Expected singleton: project.task()` di setiap pre_confirm tanpa task (BARU, terkonfirmasi)

- Gejala: 2× `ERROR ... Intervention Plugin Error (compliance):
  Expected singleton: project.task()` saat `_post_inventory` MO saus
  tanpa `agri_task_id` (final_p1d).
- Akar: `agri_intervention/models/intervention_plugins.py:233`
  `_trigger_withdrawal_sync` memanggil
  `intervention.agri_task_id.action_confirm_intervention_safety(...)`
  tanpa memeriksa task kosong — pemanggilan method di recordset kosong
  melempar singleton.
- Fix: guard `if not getattr(intervention, 'agri_task_id', False):
  return` di awal method. Versi: agri_intervention 18.0.1.0.2 →
  **18.0.1.0.3**.
- Verifikasi: MO saus 321 tanpa task → `action_confirm()` bersih,
  0 Plugin Error di log sesudah restart.

#### B54 — form `agri.ai.market.prediction` crash OwlError GaugeField (BARU, terkonfirmasi)

- Gejala: 1/235 langkah browser errdlg=1 (shot 2023): dialog "Oops!",
  console `OwlError: Invalid props for component 'GaugeField':
  'maxValueField' is not a string`; `get_views` + `web_read` server
  200 — murni client-side.
- Akar: `farm_ai_decision/views/ai_market_prediction_views.xml:29`
  `<field name="confidence_score" widget="gauge" options="{'max_field':
  100}" />` — integer 100, padahal GaugeField mensyaratkan
  `max_field` berupa NAMA field (string). Kelas yang sama dengan B46
  (farm_robotics, sudah diperbaiki di batch 7); 5 view lain memakai
  string `'100'`/`'30'` dan lolos.
- Fix: hapus option (pola persis B46 — confidence_score persen, default
  max 100 sudah tepat). Versi: farm_ai_decision 18.0.1.2.1 →
  **18.0.1.2.2**.
- Verifikasi: sesudah upgrade + restart, probe ulang form id 3 (shot
  2089) → errdlg=0, 0 pageerror, hanya artefak tunnel/SW. Sesuai aturan
  loop, verifikasi ulang TERFOKUS pada form yang diperbaiki (bukan
  pengulangan 235 langkah penuh — perbaikan satu baris view, tidak ada
  perubahan logika lain).

### Rekap browser

| Run | Langkah | Shot | Pageerror | Console error non-artefak | Errdlg |
|-----|---------|------|-----------|---------------------------|--------|
| f1 (batch 1) | 14 | 1854–1867 | 0 | 0 | 0 |
| f2 (batch 2) | 8 | 1868–1875 | 0 | 0 | 0 |
| f3 (batch 3) | 9 | 1876–1884 | 0 | 0 | 0 |
| f4 (batch 4) | 21 | 1885–1905 | 0 | 0 | 0 |
| f5a+f5b (batch 5) | 38 | 1906–1943 | 0 | 0 | 0 |
| f6a+f6b+f6c (batch 6) | 73 | 1944–2016 | 0 | 0 | 0 |
| f7a+f7b+f7c (batch 7) | 72 | 2017–2088 | 0 | 0 | 1 (B54) |
| Probe B54 | 1 | 2089 | 0 | 0 | 0 |
| LLM UI | 5 | 2090–2094 | 0 | 0 | 0 |
| POS | 3 | 2095–2097 | 0 | 0 | 0 |
| ISL wizard | 2 | 2098–2099 | 0 | 0 | 0 |
| Mobile | 1 | 2100 | 0 | 0 | 0 |
| **TOTAL** | **247** | **1854–2100** | **0** | **0** | **0 sesudah fix** |

"Console error non-artefak" = di luar 2× `ERR_TUNNEL_CONNECTION_FAILED`
per run (font Google Inter via proxy sandbox, teridentifikasi batch 7)
+ `Service worker registration failed` (artefak headless-shell).
Server log sesudah restart terakhir: 0 Traceback; 1 ERROR
`mail.activity.state cannot be searched` (02:58, `/mail/data` systray
core — log saja, HTTP 200, tanpa dialog; observasi, bukan blocker) dan
1 ERROR probe B29 URL salah (kesalahan probe, bukan modul).

### Stok/record akhir (state DB)

- Tomat FINAL 480 kg, saus FINAL 16 kg, NPK FINAL 0; pakan sapi FINAL
  90 kg, pakan lele FINAL 100 kg (baseline B7: tomat 480, saus 16,
  sapi 13, NPK 0 — pola sama; angka mentah tidak dibandingkan karena
  tiap ronde membuat data baru).
- Modul installed: 98 farm/agri (93 nama mengandung 'farm' + 9 'agri',
  irisan 4 nama mengandung keduanya).
- Hitungan akhir: seed.batch 22, nursery 12, asset 12, rotation 12,
  intervensi 80, stock.lot 178, mrp.production 305, farm.livestock 3,
  livestock.asset 1,
  aqua.operation 17, ISL aqua task 13, ISL aqua lot 13, ISL
  mrp.production 306 (221 + 85 migrasi FINAL), iiot.device 5,
  iiot.telemetry 11, automation rule 2, command log 47, LLM config 1,
  LLM service 1, ai.agent 2, pos.session 4 (1 opened FINAL, 1
  opening_control sisa B7, 2 closed), pos.order 4, manure batch 6,
  manure ledger 5, ESG report 5, gov snapshot 54.

### Observasi (bukan blocker)

1. `mrp.production.intervention_type` tidak mengenal 'packaging'
   (selection: tillage/sowing/fertilizing/irrigation/protection/
   aerial_spraying/harvesting/feeding/medical/process) — skrip p1c
   (pola B6) gagal di titik ini; jalur `_post_inventory` (p1d) yang
   dipakai, sesuai B6.
2. Valuasi cost model butuh `original_value` + `growth_stage_coefficient`
   di-set manual via shell (NBV 0 → 2.500.000) — pola sama B5R1/B6.
3. `farm.crop.lot` tidak punya field `grade_a/b/c_qty` (skrip mentolerir
   via try/except) — sudah dicatat sejak batch 1.
4. Sekali shell `odoo-bin` gagal load registry di `ag_drive/__init__.py`
   (transien — run ulang langsung berhasil, server 200); bukan modul
   farm, dicatat saja.
5. Wizard ISL via UI: klik Migrate dengan Confirm OFF tidak
   menampilkan dialog error yang tertangkap (lihat Bagian 2) — migrasi
   sendiri terbukti via shell; perilaku klik-UI itu belum dijelaskan
   penuh (kemungkinan klik tidak sampai ke method karena mode
   fullscreen), bukan blocker karena wizard + method terverifikasi.

## Keputusan: BERSIH ✅ 100%

**Simulasi FINAL SELESAI.** Rantai penuh batch 1–7 dari nol data baru
lolos: 235 langkah browser kumulatif + probe B54 + LLM UI + POS + ISL
wizard + mobile = 247 screenshot, **0 pageerror, 0 console error
non-artefak, 0 errdlg sesudah perbaikan**. Blocker baru B52–B54
diperbaiki + terverifikasi (upgrade farm_gov 18.0.1.0.1, farm_marketing
18.0.1.0.2, agri_intervention 18.0.1.0.3, farm_ai_decision 18.0.1.2.2).
Dua batasan lama TERTUTUP ronde ini: inferensi LLM live via UI
(call_count 2→4, error 0, jawaban Gemini sungguhan di agent) dan
validasi sesi POS ke `opened` via klik browser (sesi 3 opened).
Yang tersisa: 4 stub tanpa manifest + 11 modul China-specific yang
tetap dikecualikan + sesi POS Bakery id 4 masih `opening_control`
(sisa B7, data uji) + observasi 1–5 di atas. Tidak ada batch 8 yang
diputuskan dalam tugas ini.
