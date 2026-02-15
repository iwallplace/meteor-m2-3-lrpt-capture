# SDR Recorder — Kullanim Kilavuzu

## Dosyalar

| Dosya | Ne Yapar | Tek Basina Calisir mi? |
|-------|----------|----------------------|
| `meteor_capture.py` | **Her seyi yapar:** Zamanlayici + SDR kayit + Canli GUI + Otomatik decode | Evet — ana dosya |
| `sdr_monitor.py` | **Sadece izleme:** Mevcut IQ dosyasini canli izler (kayit yapmaz) | Evet — yardimci arac |
| `meteor_final.sh` | **Interaktif kayit:** Terminalden sorulu-cevapli basit kayit | Evet — bash scripti |

---

## Hangisi Ne Zaman Kullanilir?

### meteor_capture.py (Ana Sistem)

**Tek dosya acilinca her seyi yapar:**
- Belirlenen saate kadar bekler (countdown)
- SDR cihazini test eder
- Kaydi baslatir (rtl_sdr)
- Canli spektrum + waterfall + SNR ekrani acar
- Sure dolunca kaydi durdurur
- Meteor sinyali ise otomatik SatDump decode yapar
- Islem bitince GUI kapanir

**Kullanim:**
```bash
# Basit kullanim — hemen basla, 10 dakika kaydet
python3 meteor_capture.py --freq 137.9 --duration 10

# Zamanlanmis — saat 21:02'de basla
python3 meteor_capture.py --freq 137.9 --duration 24 --start 21:02 --label "Meteor"

# Balon kaydı — farkli frekans ve ornekleme hizi
python3 meteor_capture.py --freq 403.0 --duration 120 --start 14:58 --sr 250000 --label "Balon"

# Cikti dizini belirt
python3 meteor_capture.py --freq 137.9 --duration 24 --start 21:02 --output /Volumes/Hangar/data
```

### sdr_monitor.py (Sadece Izleme)

**Kayit yapmaz!** Zaten kayit edilen (veya edilmekte olan) bir IQ dosyasini acar ve canli izler.

Ne zaman kullanilir:
- Baska bir yontemle kayit yapiyorsan ve sadece izlemek istiyorsan
- Eski bir kaydi tekrar gorup analiz etmek istiyorsan
- meteor_capture.py disinda rtl_sdr ile kayit yapiyorsan

```bash
# Devam eden kaydi izle
python3 sdr_monitor.py /path/capture_137.9MHz.cu8 1024000 137.9

# Eski kaydi incele
python3 sdr_monitor.py /Volumes/Hangar/eski_kayit.cu8 250000 403.0
```

### meteor_final.sh (Basit Bash)

GUI yok, sadece terminal. Sorulara cevap verirsin, kaydi yapar.

```bash
bash meteor_final.sh
# Frekans? 137.9
# Kazanc? 44.5
# Sure? 24
# ...
```

---

## Parametreler (meteor_capture.py)

| Parametre | Varsayilan | Aciklama |
|-----------|-----------|----------|
| `--freq` | 137.9 | Merkez frekans (MHz) |
| `--gain` | 44.5 | RF kazanc (dB) |
| `--sr` | 1024000 | Ornekleme hizi (S/s) |
| `--duration` | 15 | Kayit suresi (dakika) |
| `--start` | — | Baslama saati (HH:MM format). Verilmezse hemen baslar |
| `--label` | "SDR_Capture" | Kayit etiketi (dosya adinda gorulur) |
| `--output` | bulundugun dizin | Dosyalarin kaydedilecegi klasor |

---

## Ornek Senaryolar

### Senaryo 1: Meteor Uydusu Yakalama

Aksam 21:02'de M2-4 ve M2-3 geciyor, 24 dakika kaydet:

```bash
python3 meteor_capture.py \
    --freq 137.9 \
    --gain 44.5 \
    --duration 24 \
    --start 21:02 \
    --label "Meteor_M2-4_M2-3" \
    --output /Volumes/Hangar/meteor_capture
```

Olacaklar:
1. Saat 21:02'ye kadar countdown gosterir
2. SDR testi yapar
3. Kayit + GUI baslar
4. 24 dk sonra kayit durur
5. SatDump ile otomatik decode
6. GUI kapanir

Cikti dosyalari:
- `Meteor_M2-4_M2-3_137.9MHz_YYYYMMDD_HHMM.cu8` (ham IQ)
- `decoded/` klasorunde goruntuler (SatDump ciktisi)

### Senaryo 2: Meteoroloji Balonu

Saat 15:00'te balon firlatiliyor, 120 dakika kaydet:

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

Not: 403 MHz icin SatDump decode calismaz (sadece meteor frekanslari icin). Ham IQ dosyasi kaydedilir, radiosonde_auto_rx ile ayrica decode edilebilir.

### Senaryo 3: Sirali Yakalama (Onco Balon, Sonra Meteor)

Iki farkli frekansi ayni gece yakalamak icin:

```bash
# Dosya: tonight.sh
#!/bin/bash

# 1. Balon (14:58 - ~17:00)
python3 meteor_capture.py --freq 403.0 --duration 120 --start 14:58 --sr 250000 --label "Balon"

# Balon bitmeden meteor baslamaz (sirali calisir)

# 2. Meteor (21:02 - ~21:26)
python3 meteor_capture.py --freq 137.9 --duration 24 --start 21:02 --label "Meteor"
```

```bash
chmod +x tonight.sh && ./tonight.sh
```

### Senaryo 4: Hemen Test

SDR calisiyormu diye hizli test:

```bash
python3 meteor_capture.py --freq 137.9 --duration 1 --label "Test"
```

1 dakika kayit yapar, GUI acar, spektrumu gorursun.

---

## GUI Panelleri

Canli monitor 3 panel icerir:

```
┌──────────────────────────────────┐
│         SPEKTRUM (FFT)           │  ← Anlik guc dagilimi
│   Frekans ekseninde sinyal gucu  │     Sari cizgi: peak hold
│   beyaz cizgi: anlik             │
├──────────────────────────────────┤
│         WATERFALL                │  ← Zaman-frekans haritasi
│   Yukari = eski, asagi = yeni    │     Sicak renkler = guclu sinyal
│   Inferno renk haritasi          │
├──────────────────────────────────┤
│         SNR GRAFIGI              │  ← Sinyal-gurultu orani
│   Zaman icinde SNR degisimi      │     Yesil = iyi, kirmizi = zayif
└──────────────────────────────────┘
```

---

## Bilinen Sorunlar ve Cozumler

### SDR bulunamadi hatasi
```
No supported devices found
```
**Cozum:** USB kablosunu cikart-tak veya Mac'i yeniden baslat.

### GUI acilmiyor (nohup ile)
PyQt5, ekran erisimi gerektirir. `nohup` ile calismaz.
**Cozum:** Dogrudan calistir veya `&` ile arka plana at:
```bash
python3 meteor_capture.py --freq 137.9 --duration 10 &
```

### Kayit dosyasi beklenenden buyuk
rtl_sdr, `cu8` formatinda kaydeder: her sample = 2 byte (1 byte I + 1 byte Q).
Formul: `dosya_boyutu = ornekleme_hizi × sure_saniye × 2`
Ornek: 1.024 MS/s × 24 dk × 60 = 2.95 GB

### SatDump decode basarisiz (0 goruntu)
- SNR 0 dB ise sinyal alinmamistir (anten/konum sorunu)
- Format hatasi: `--baseband_format cu8` kullanildigina emin ol
- Uydu gecisi sirasinda kayit yapildigina emin ol

---

## Gereksinimler

```bash
# macOS
brew install rtl-sdr
pip3 install numpy PyQt5

# Linux (Debian/Ubuntu)
sudo apt install rtl-sdr
pip3 install numpy PyQt5

# Opsiyonel: Meteor decode
# SatDump: https://github.com/SatDump/SatDump

# Opsiyonel: Radyosonde decode
# radiosonde_auto_rx: https://github.com/projecthorus/radiosonde_auto_rx
```

---

*SDR Capture Toolkit — Subat 2026*
