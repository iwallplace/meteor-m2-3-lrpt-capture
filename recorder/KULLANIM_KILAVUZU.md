# SDR Capture — Kullanim Kilavuzu

## Tek Dosya: meteor_capture.py

Her seyi yapar: Zamanlayici + SDR test + Kayit + Canli GUI (spektrum/waterfall/SNR) + Otomatik decode

---

## Hizli Baslangic

```bash
# Meteor uydusu — saat 21:02'de basla, 24 dk kaydet
python3 meteor_capture.py --freq 137.9 --duration 24 --start 21:02 --label "Meteor"

# Radyosonde balon — saat 14:58'de basla, 120 dk kaydet
python3 meteor_capture.py --freq 403.0 --duration 120 --start 14:58 --sr 250000 --label "Balon"

# Hemen basla (test icin)
python3 meteor_capture.py --freq 137.9 --duration 5 --label "Test"
```

---

## Parametreler

| Parametre | Varsayilan | Aciklama |
|-----------|-----------|----------|
| `--freq` | 137.9 | Merkez frekans (MHz) |
| `--gain` | 44.5 | RF kazanc (dB) |
| `--sr` | 1024000 | Ornekleme hizi (S/s) |
| `--duration` | 15 | Kayit suresi (dakika) |
| `--start` | — | Baslama saati (HH:MM). Verilmezse hemen baslar |
| `--label` | "SDR_Capture" | Kayit etiketi (dosya adinda gorulur) |
| `--output` | bulundugun dizin | Dosyalarin kaydedilecegi klasor |

---

## Calisma Akisi

1. **Bekleme** — `--start` verilmisse o saate kadar countdown gosterir
2. **SDR Test** — rtl_sdr ile kisa test, cihaz calisiyor mu kontrol eder
3. **Kayit + GUI** — rtl_sdr kaydi baslar, canli spektrum/waterfall/SNR ekrani acilir
4. **Kayit Bitis** — Sure dolunca rtl_sdr durur
5. **Decode** — Meteor frekansi ise (<140 MHz) SatDump ile otomatik goruntu cikarir
6. **Kapanma** — 10 saniye sonra GUI kapanir

---

## GUI Panelleri

```
┌──────────────────────────────────┐
│         SPEKTRUM (FFT)           │  Anlik guc dagilimi
│   Yesil: anlik | Kirmizi: peak   │
├──────────────────────────────────┤
│         WATERFALL                │  Zaman-frekans haritasi
│   Sicak renkler = guclu sinyal   │
├──────────────────────────────────┤
│         SNR GRAFIGI              │  Sinyal-gurultu orani
│   Kirmizi: sinyal var (>8 dB)    │
│   Yesil: sinyal yok (<8 dB)     │
└──────────────────────────────────┘
```

---

## Ornek Senaryolar

### Meteor Uydusu

```bash
python3 meteor_capture.py \
    --freq 137.9 \
    --gain 44.5 \
    --duration 24 \
    --start 21:02 \
    --label "Meteor_M2-4_M2-3" \
    --output /Volumes/Hangar/meteor_capture
```

Cikti:
- `Meteor_M2-4_M2-3_YYYYMMDD_HHMMSS.cu8` — ham IQ
- `Meteor_M2-4_M2-3_YYYYMMDD_HHMMSS_DECODED/` — goruntuler

### Meteoroloji Balonu

```bash
python3 meteor_capture.py \
    --freq 403.0 \
    --gain 44.5 \
    --duration 120 \
    --start 14:58 \
    --sr 250000 \
    --label "Radiosonde_Balon" \
    --output /Volumes/Hangar/radiosonde
```

Not: 403 MHz icin otomatik decode calismaz. Ham IQ kaydedilir, radiosonde_auto_rx ile ayrica decode edilir.

### Sirali Yakalama (Balon + Meteor)

```bash
#!/bin/bash
# Onco balon, sonra meteor
python3 meteor_capture.py --freq 403.0 --duration 120 --start 14:58 --sr 250000 --label "Balon"
python3 meteor_capture.py --freq 137.9 --duration 24 --start 21:02 --label "Meteor"
```

---

## Bilinen Sorunlar

| Sorun | Cozum |
|-------|-------|
| "No supported devices found" | USB kablosunu cikart-tak veya Mac'i yeniden baslat |
| Dosya beklenenden buyuk | Normal: cu8 formati, her sample = 2 byte (I+Q) |
| SatDump 0 goruntu | SNR < 5 dB ise sinyal alinmamistir, anten/konum kontrol |
| GUI acilmiyor (nohup) | `nohup` ile calismaz, dogrudan calistir |

---

## Gereksinimler

```bash
# macOS
brew install rtl-sdr
pip3 install numpy PyQt5

# Linux
sudo apt install rtl-sdr
pip3 install numpy PyQt5

# Opsiyonel
# SatDump: https://github.com/SatDump/SatDump
```
