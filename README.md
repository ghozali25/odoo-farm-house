# odoo-farm-house

Port **odoo-farm** (Odoo 19) ke **Odoo 18** — 94 modul pertanian lengkap, diadaptasi untuk Indonesia / penggunaan universal.

Sumber: [jeffery9/odoo-farm](https://github.com/jeffery9/odoo-farm) branch `19.0`, commit `aaa0ab6`.
Lisensi: **AGPL-3.0** (sama seperti upstream).

> **Status: teruji penuh.** Simulasi end-to-end kumulatif batch 1–7 dari nol data baru di Odoo 18
> (11 Nov 2026) **BERSIH 100%** — 247 langkah browser, 0 pageerror, 0 console error, 0 Traceback.
> Rincian pengujian: [`SIMULASI.md`](SIMULASI.md). Rincian porting per modul: [`PORTING.md`](PORTING.md).

## Fitur

### 1. Rantai tanaman — benih sampai valuasi

Benih → pembibitan (nursery) → tanam berbasis **Growing Degree Days** (GDD, bukan tanggal kalender)
→ intervensi (semai, pupuk, siram, panen) → QC → pengolahan (MRP) → barang jadi → valuasi.

- Lahan = `stock.location`, panen = `stock.move` + lot, pengolahan = MRP standar Odoo.
- Intervensi terjadwal, ISL (Integrated Smart Logistics) untuk migrasi data produksi.
- Valuasi aset biologis (fair value) yang membuat **jurnal `account.move` sungguhan**.
- Modul: `farm_crop`, `farm_operation`, `farm_processing`, `farm_isl`, `farm_ux`,
  `agri_intervention`, `farm_seed_industry`, `farm_planning`, `farm_quality`, `farm_valuation`.

### 2. Ternak & akuakultur

- Ternak: siklus hidup, perkembangbiakan, pakan (cron otomatis), kesehatan, valuasi ternak.
- Akuakultur: operasi kolam, pakan, telemetri kualitas air.
- Modul: `farm_livestock`, `farm_livestock_matter`, `farm_livestock_valuation`,
  `farm_aquaculture`, `farm_aquaculture_matter`, `farm_breeding`.

### 3. IoT & cuaca

- Perangkat IoT, gateway, telemetri (MQTT), digital twin, aturan otomasi
  (mis. suhu > 35 °C → perintah `power_on`), korelasi event, katup air, lingkungan gudang.
- Prakiraan cuaca (mock OpenWeatherMap + input manual).
- Modul: `agri_iot`, `farm_iot`, `farm_weather`. Bridge MQTT (`agri_iot/mqtt_bridge/`)
  adalah infrastruktur terpisah — lihat [Instalasi](#instalasi).

### 4. HR, limbah, keuangan & ESG

- HR pertanian: skill, tim layanan, pembayaran upah, aturan gaji, worklog, bank waktu, sertifikat.
- Limbah: batch & ledger pupuk kandang (manure), limbah pengolahan, biogas, limbah B3.
- Keuangan: kategori & template biaya, clearing ledger, kredit & skor kredit,
  asuransi hasil panen & klaim, valuasi finansial.
- ESG: framework, indikator, assessment, target, laporan kinerja, ledger karbon,
  kredit karbon, keberlanjutan, risiko, sosial.
- Modul: `farm_hr`, `farm_waste_mgmt`, `farm_financial`, `farm_financial_basic`,
  `farm_financial_clearing`, `farm_financial_credit`, `farm_financial_government`,
  `farm_financial_insurance`, `farm_financial_valuation`, `farm_esg`,
  `farm_esg_carbon`, `farm_esg_circular`, `farm_esg_compliance`, `farm_esg_environmental`,
  `farm_esg_fair_trade`, `farm_esg_matter`, `farm_esg_report`, `farm_esg_risk`,
  `farm_esg_social`, `farm_esg_sustainability`, `farm_biological_valuation`.

### 5. Vertikal hortikultura & lainnya

Apikultur (lebah & madu), tanaman pangan, florikultura, greenhouse, jamur,
tanaman obat, kebun (orchard), vitikultura & winery, fermentasi, ekologi,
sertifikasi GAP, subsidi, skenario, rute teknis, kampanye, benih, breeding,
peralatan, musim, kemasan, kesehatan, geospasial, fisiologi, rantai pasok,
cold storage, kendaraan, pengadaan bersama, VMI, harga berbasis kualitas.

### 6. AI, robotik & multi-farm

- **AI/LLM**: agent AI, prediksi pertumbuhan & hasil panen, keputusan pemupukan,
  irigasi, kesehatan tanaman, hama & penyakit (deteksi gambar + visual sorting),
  prediksi pasar, grading kualitas, optimasi sumber daya, penilaian risiko.
  LLM memakai API OpenAI-compatible — default `https://9router-go.hiddenlab.me/v1`
  (isi API key sendiri di konfigurasi).
- Robotik: robot, misi, sewa robot, koordinasi swarm, orkestrator otonom.
- Multi-farm: entitas, franchise, settlement internal, berbagi sumber daya, order layanan.
- Modul: `farm_ai`, `farm_ai_agent`, `farm_ai_decision`, `farm_ai_llm_integration`,
  `farm_ai_robotics`, `farm_ai_vision`, `farm_robotics`, `farm_multi_farm`,
  `farm_multi_farm_equipment`, `farm_multi_farm_financial`,
  `farm_multi_farm_procurement`, `farm_multi_farm_quality`.

### 7. Penjualan, layanan & operasional

- **POS** (`farm_pos`, menarik `point_of_sale` standar): dashboard toko, buka register, sesi kasir.
- **Mobile** (`farm_mobile`): check-in lapangan, checklist, antrean sinkronisasi.
- Dashboard, pemasaran (demand, feedback, konektor pasar), pemerintahan (gov platform,
  snapshot audit), krisis & bencana (insiden, protokol darurat, penilaian kerugian),
  keamanan data, knowledge base & FAQ, pelatihan & sertifikasi, agritourism & booking,
  keselamatan (biosafety, pencegahan), simbiosis, label, asuransi, CSA (langganan panen).
- Modul: `farm_pos`, `farm_mobile`, `farm_dashboard`, `farm_marketing`, `farm_gov`,
  `farm_crisis`, `farm_disaster_risk`, `farm_data_security`, `farm_knowledge`,
  `farm_training`, `farm_agritourism`, `farm_csa`, `farm_safety`, `farm_symbiosis`,
  `farm_label`, `farm_insurance`, `farm_supply`, `farm_supply_analytics`,
  `farm_supply_logistics`, `farm_supply_procurement`, `farm_supply_quality`,
  `farm_agri_science`, `farm_agricultural_processing`, `farm_core`, `farm_mrp`,
  `farm_ecology`, `farm_equipment`, `farm_subsidy`, `farm_fermentation`,
  `farm_fermentation_matter`, `farm_field_crops`, `farm_floriculture`,
  `farm_greenhouse`, `farm_mushroom`, `farm_medicinal_plants`,
  `farm_orchard_horticulture`, `farm_protected_cultivation`, `farm_viticulture`,
  `farm_winery`, `farm_apiculture`, `farm_crop_matter`, `farm_esg_matter`.

### Integrasi Accounting & Inventory

Sudah terintegrasi **tanpa** 4 modul stub di bawah:

- **Inventory**: 19 modul depends `stock`. Stok, lot, lokasi, dan MRP memakai mesin standar Odoo.
- **Accounting**: valuasi membuat jurnal `account.move`; modul finansial mencakup
  biaya, clearing, kredit, asuransi, dan valuasi. 6 modul depends `account` langsung.

## Screenshot

Semua tangkapan layar dari simulasi FINAL (Odoo 18, `?debug=1`, 11 Nov 2026).

### Pembibitan & rantai tanaman

<img src="https://drive.google.com/uc?export=view&id=1unxSUm-Vaf9PtSvmUb19Q_FvgE8aiTi7" width="800" alt="Batch benih">

*Batch benih — SIMULASI FINAL Bibit Tomat Servo F1*

<img src="https://drive.google.com/uc?export=view&id=1njjCuCCaf5C2gAx-ABUYRyt-ivtUja91" width="800" alt="Pembibitan nursery">

*Pembibitan (nursery) — lot bibit dengan tanggal semai*

<img src="https://drive.google.com/uc?export=view&id=1AB5SECUsVDidbhPrep2Z6JhwYLbpzi7e" width="800" alt="Intervensi panen">

*Intervensi panen*

<img src="https://drive.google.com/uc?export=view&id=11amVEF7l9AMqwxaD_HjM6CBTDS4Z4BtI" width="800" alt="Pengolahan MRP saus tomat">

*Pengolahan (MRP) — MO saus tomat, status Done, komponen tomat segar*

<img src="https://drive.google.com/uc?export=view&id=1eYQY4ysyZNxYbYqvBcu2-WDhsbA3Mlny" width="800" alt="Valuasi aset biologis">

*Valuasi aset biologis (fair value)*

### Ternak & akuakultur

<img src="https://drive.google.com/uc?export=view&id=17C8fM8db8XGMVVbt6K8DrDVAwy0gengW" width="800" alt="Ternak">

*Ternak*

<img src="https://drive.google.com/uc?export=view&id=1dFLtnXT6qSjFdatVzW9DsjspsiiWv0dh" width="800" alt="Operasi akuakultur">

*Operasi akuakultur*

### IoT & cuaca

<img src="https://drive.google.com/uc?export=view&id=19I64rmVey4b7N2WVjtigOOPBQrLe_jBP" width="800" alt="Perangkat IoT">

*Perangkat IoT (iiot.device)*

<img src="https://drive.google.com/uc?export=view&id=1hM_T8fjP26qmhxSsRqzFc7UJtzSykrCx" width="800" alt="Prakiraan cuaca">

*Prakiraan cuaca pertanian*

### ESG & vertikal

<img src="https://drive.google.com/uc?export=view&id=10K9_y8vgbPTO9yk4jbEdZnsRGni1Z4IX" width="800" alt="Framework ESG">

*Framework ESG*

<img src="https://drive.google.com/uc?export=view&id=1M_z7Zk2tvQ5_Uz3InJRXivOPAfvvFmwL" width="800" alt="Batch jamur">

*Batch jamur (vertikal hortikultura)*

### AI, LLM, POS & mobile

<img src="https://drive.google.com/uc?export=view&id=14prl-Ah0t-Iu-IoJMcL5_diJdl6IbSEr" width="800" alt="AI Agent">

*AI Agent*

<img src="https://drive.google.com/uc?export=view&id=1u6YxD9AbMbe_g0hwLQGCKtU6vdAxUjcX" width="800" alt="Konfigurasi LLM">

*Konfigurasi LLM — provider OpenAI-compatible, API key ter-mask, default model tampil*

<img src="https://drive.google.com/uc?export=view&id=1Z7r9GbHsWwHZQQ60kKetYO3nKoJwcSgF" width="800" alt="Dashboard Point of Sale">

*Dashboard Point of Sale — Furniture, Clothes & Bakery Shop*

<img src="https://drive.google.com/uc?export=view&id=14UtkMRDen524j4WLpkl4S1YU3AkvErmH" width="800" alt="Check-in mobile">

*Check-in lapangan (mobile viewport 390px)*

## Instalasi

### Prasyarat

- Odoo **18.0** (Community/Enterprise), Python 3.12, PostgreSQL.
- Modul standar yang ditarik otomatis sebagai dependensi: `stock`, `mrp`, `account`,
  `sale`, `purchase`, `hr`, `project`, `point_of_sale` (untuk `farm_pos`), `mail`.

### Cara pasang

1. Clone repo ini, atau unduh ZIP-nya:
   ```bash
   git clone https://github.com/ghozali25/odoo-farm-house.git
   ```
2. Salin folder-folder modul (mis. `farm_core`, `farm_crop`, …) ke `addons_path` Odoo 18 Anda.
   Semua 94 modul bisa dipasang bersama dalam satu database — simulasi dilakukan
   dalam 1 DB integrasi, dan itu cara yang disarankan.
3. Di Odoo: **Apps → Update Apps List**, lalu install modul yang dibutuhkan.
   Dependensi antar-modul diselesaikan otomatis oleh Odoo; memasang `farm_core`
   saja belum cukup — pasang modul fitur yang Anda pakai (mis. `farm_livestock`,
   `farm_ai`, `farm_pos`).
4. Restart Odoo bila perlu, lalu hard refresh browser (`Ctrl+Shift+R`).

### Konfigurasi LLM (opsional, untuk modul AI)

1. Buka konfigurasi LLM (`agri.ai.configuration`).
2. `API Base URL` sudah default ke endpoint OpenAI-compatible
   (`https://9router-go.hiddenlab.me/v1`).
3. Isi `API Key` Anda sendiri dan atur `Default Model` ke model yang tersedia
   di gateway Anda (contoh teruji: `ag/gemini-2.5-flash-lite`).
4. Uji dengan tombol **Test API Call** di form service LLM, atau **Execute Agent**
   pada AI Agent — jawaban LLM sungguhan menandakan koneksi live.

### Bridge MQTT (opsional, untuk telemetri IoT live)

Telemetri MQTT butuh bridge terpisah (bukan bagian instalasi modul):

1. Jalankan broker MQTT (mis. `amqtt` / Mosquitto) di `127.0.0.1:1883`.
2. Jalankan bridge di `agri_iot/mqtt_bridge/` (Python, lihat `requirements.txt`):
   telemetri masuk → shadow device + `farm.storage.env` ter-update; aturan suhu
   (mis. > 35 °C) mengirim command kembali ke subscriber.
3. Tanpa bridge, modul IoT tetap bisa dipakai dengan input telemetri manual.

## Adaptasi Indonesia / universal

- Label Mandarin → Inggris + terjemahan `id_ID` di setiap modul (0 karakter CJK tersisa).
- Modul/fitur khusus regulasi China dikeluarkan atau digeneralisasi
  (mis. lisensi produksi SC menjadi `farm.production.license` generik dengan `country_id`,
  sehingga PIRT, halal, atau BPOM bisa ditambahkan sebagai data).
- 11 modul khusus China **tidak** di-port (lihat `PORTING.md` §19d).

## Batasan yang diketahui

- **4 modul stub menunggu upstream** (hanya `__init__.py` + `i18n/` + `tests/`,
  tanpa `__manifest__.py` sehingga tidak bisa di-install):
  `farm_finance_advanced`, `farm_finance_loan`, `farm_logistics`,
  `farm_supply_chain_smart`. Baru bisa di-port setelah upstream mengisinya.
- `farm_weather` memakai mock OpenWeatherMap + input manual — **bukan** integrasi live.
- Sesi POS uji dari simulasi (Bakery `opening_control`) adalah data uji, bukan bug.

## Lisensi & kredit

- **AGPL-3.0** — lihat [`LICENSE`](LICENSE).
- Kode sumber: [jeffery9/odoo-farm](https://github.com/jeffery9/odoo-farm) (AGPL-3.0).
  Port ini mempertahankan lisensi yang sama.
- Porting & pengujian end-to-end: Ahmad Ghozali ([ghozali25](https://github.com/ghozali25))
  dengan Muse.
