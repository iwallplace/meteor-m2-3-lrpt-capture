# SDR Capture Toolkit — Uydu ve Radyo Sinyal Yakalama Sistemi

*RTL-SDR tabanli evrensel sinyal yakalama, canli izleme ve otomatik cozumleme araclari*

---

## Genel Bakis

Bu proje, RTL-SDR alicilarla radyo sinyallerini yakalamak, canli olarak izlemek ve islemek icin gelistirilmis acik kaynakli bir arac setidir. Meteoroloji uydularindan (Meteor M2-3, M2-4) radyosonde balonlarina, SCADA sinyallerinden ozel frekanslara kadar her turlu SDR yakalama senaryosu icin kullanilabilir.

### Ozellikler

- **Zamanlanmis yakalama** — Belirli saatte otomatik baslatma (uydu gecisleri, balon firlatisflari vb.)
- **SDR on-test** — Kayit oncesi cihaz kontrolu
- **Canli spektrum izleme** — PyQt5 tabanli yuksek performansli GUI (QPainter, ~10 FPS)
- **Waterfall goruntuleme** — Numpy vektorize renk haritasi ile akici waterfall
- **SNR takibi** — Gercek zamanli sinyal-gurultu orani grafigi
- **Otomatik cozumleme** — Meteor LRPT sinyalleri icin SatDump entegrasyonu
- **Evrensel** — Herhangi bir frekans, ornekleme hizi ve bant genisligi ile calisir

---

## Kurulum

### Gereksinimler

```bash
# Temel bagimliliklar
brew install rtl-sdr          # veya apt install rtl-sdr (Linux)
pip3 install numpy PyQt5

# Opsiyonel — Meteor uydu goruntusu decode
# https://github.com/SatDump/SatDump adresinden indirin
```

### Donanim

- **RTL-SDR** — RTL-SDR Blog V4 (R828D tuner) onerilir
- **Anten** — Hedef frekansa uygun anten (137 MHz icin V-dipol, 403 MHz icin genel amacli vb.)

---

## Kullanim

### meteor_capture.py — Ana Yakalama Sistemi

Tek komutla zamanlanmis kayit + canli GUI + otomatik decode:

```bash
# Meteor uydusu (137.9 MHz, 1024 kS/s, 24 dakika, saat 21:02'de basla)
python3 scripts/meteor_capture.py \
    --freq 137.9 --gain 44.5 --duration 24 --start 21:02 \
    --sr 1024000 --label "Meteor_M2-3"

# Radyosonde balon (403 MHz, 250 kS/s, 120 dakika, saat 14:58'de basla)
python3 scripts/meteor_capture.py \
    --freq 403.0 --gain 44.5 --duration 120 --start 14:58 \
    --sr 250000 --label "Radiosonde_Balon"

# Hemen basla (--start olmadan)
python3 scripts/meteor_capture.py \
    --freq 137.9 --gain 44.5 --duration 10 --label "Test"
```

**Parametreler:**

| Parametre | Varsayilan | Aciklama |
|-----------|-----------|----------|
| `--freq` | 137.9 | Merkez frekans (MHz) |
| `--gain` | 44.5 | RF kazanc (dB) |
| `--sr` | 1024000 | Ornekleme hizi (S/s) |
| `--duration` | 15 | Kayit suresi (dakika) |
| `--start` | — | Baslama saati (HH:MM). Belirtilmezse hemen baslar |
| `--label` | "SDR_Capture" | Kayit etiketi |
| `--output` | cwd | Cikti dizini |

**Calisma akisi:**
1. Belirtilen saate kadar bekler (countdown gosterir)
2. SDR cihazini test eder
3. `rtl_sdr` ile IQ kaydi baslatir
4. Canli spektrum + waterfall + SNR GUI acar
5. Sure dolunca kaydi durdurur
6. Meteor frekansi ise SatDump ile otomatik decode eder
7. 10 saniye sonra GUI kapanir

### sdr_monitor.py — Bagimsiz Canli Monitor

Herhangi bir IQ dosyasini canli izlemek icin (kayit devam ederken veya kayit bittikten sonra):

```bash
python3 scripts/sdr_monitor.py <iq_dosyasi> [ornekleme_hizi] [merkez_frekans_mhz]

# Ornekler:
python3 scripts/sdr_monitor.py capture_137.9MHz.cu8 1024000 137.9
python3 scripts/sdr_monitor.py radiosonde.cu8 250000 403.0
```

### meteor_final.sh — Interaktif Bash Scripti

Terminal uzerinden sorulu-cevapli yakalama:

```bash
bash scripts/meteor_final.sh
```

---

## Proje Yapisi

```
.
├── scripts/
│   ├── meteor_capture.py    # Ana yakalama sistemi (zamanlayici + GUI + decode)
│   ├── sdr_monitor.py       # Bagimsiz canli spektrum monitoru
│   └── meteor_final.sh      # Interaktif bash yakalama scripti
├── data/                    # Cozumlenmmis ciktilar (goruntuler, telemetri)
├── images/                  # Ornek goruntuler ve ekran goruntuleri
├── raw/                     # Ham IQ verileri (Git LFS)
└── README.md
```

---

## Desteklenen Sinyal Turleri

| Sinyal | Frekans | Ornekleme Hizi | Notlar |
|--------|---------|---------------|--------|
| Meteor M2-3 LRPT | 137.900 MHz | 1024 kS/s | OQPSK 72k sym/s, SatDump ile decode |
| Meteor M2-4 LRPT | 137.900 MHz | 1024 kS/s | Subat 2024'te firlatildi, ayni frekans |
| Radyosonde (balon) | ~403 MHz | 250 kS/s | GFSK modulasyon, radiosonde_auto_rx ile decode |
| ORBCOMM | 137.2–137.8 MHz | 1024 kS/s | Uydu sinyal testi icin kullanisli |
| Ozel frekans | Herhangi | Ayarlanabilir | rtl_sdr destekli herhangi bir sinyal |

---

## GUI Ekran Goruntuleri

Canli spektrum monitoru 3 panel icerir:

1. **Spektrum (FFT)** — Anlik guc dagilimi + peak hold
2. **Waterfall** — Zaman-frekans goruntuleme (inferno renk haritasi)
3. **SNR Grafigi** — Sinyal-gurultu orani gecmisi

GUI, PyQt5 + QPainter ile sifirdan yazilmistir (matplotlib kullanilmaz). Numpy vektorize islemler sayesinde kasma olmadan ~10 FPS canli guncelleme saglar.

---

## Vaka Calismasi: Meteor M2-3 LRPT — Sina Yarimadasi Termal Goruntuleme

*14 Subat 2026 — Manisa, Turkiye (38.63°N, 27.27°E)*

### Hedef Uydu

**Meteor M2-3** (NORAD 57166) — Roscosmos/Roshydromet tarafindan isletilen kutupsal yorungeli meteoroloji uydusu. 27 Haziran 2023'te firlatildi. 832 km irtifada gunes-senkron yorungede, MSU-MR cihazi ile 6 spektral kanalda 1 km cozunurluklu goruntuleme yapar. 137.900 MHz uzerinden LRPT protokoluyle sifrelenmemis veri yayinlar.

### Yer Istasyonu

- **Alici:** RTL-SDR Blog V4 (R828D, 8-bit ADC)
- **Anten:** V-Dipol, 2×53.4 cm, 120° aci, ic mekan (guneye bakan pencere)
- **Yapilandirma:** 137.9 MHz, 1.024 MS/s, 44.5 dB kazanc

### Gecis ve Sinyal

| Olay | Zaman (TRT) | Elevasyon |
|------|-------------|-----------|
| AOS | 21:34 | 0° (Guney) |
| Maks. elevasyon | 21:41 | 66.3° |
| LOS | 21:48 | 0° (Kuzey) |

Tepe SNR **9.7 dB** (21:39:30). Etkin sinyal suresi ~3.5 dk (gecis suresinin %25'i — ic mekan anteni kisiti). Elagik mesafe ~900 km'de.

### Sonuclar

SatDump ile **27 goruntu urunu** elde edildi (gece gecisi — sadece kizilotesi kanallar aktif):

- **Kapsam:** Kizildeniz, Sina Yarimadasi, Nil Deltasi, Suudi Arabistan, Libya, Basra Korfezi
- **Cozunurluk:** ~1 km (MSU-MR)
- **Telemetri:** 113 cozumlenen cerceve, 18 analog telemetri paketi
- **Anomali:** Sicak Govde #3 kalibrasyon referansi beklenen ~313 K yerine 222.65 K okuyor (termistor arizasi)

**Turkiye goruntulenememistir** — uydu Turkiye uzerindeyken antenin gorunemez bolgesindeydi. Bu kisit, 21 Subat'taki dag gecisinde (88.3° elevasyon, dis mekan) asilacaktir.

### Ham IQ Verisi

3.69 GB ham IQ dosyasi (cu8 formati) `raw/` dizininde Git LFS ile paylasilmaktadir. Bagimsiz dogrulama ve yeniden isleme icin:

```bash
satdump meteor_m2-x_lrpt baseband ham_iq.cu8 cikti/ \
    --samplerate 1024000 --baseband_format cu8 --fill_missing true
```

---

## Notlar

- **IQ Format:** rtl_sdr, `cu8` (unsigned 8-bit interleaved I/Q) formatinda kaydeder. SatDump'a `--baseband_format cu8` parametersi verilmelidir.
- **SDR USB Sorunu:** `kill` komutuyla rtl_sdr'yi durdurmak USB baglantisini bozabilir. Script icinde `SIGTERM` + graceful shutdown kullanilir.
- **Tek SDR = Tek Frekans:** Ayni anda iki farkli frekansi yakalayamazsinjz. Sirali yakalama planlayim.

---

## Lisans

MIT

---

*Ahmet Mersin — Manisa, Turkiye — Subat 2026*
*SDR ve Uydu Haberlesme Arastirmalari*
