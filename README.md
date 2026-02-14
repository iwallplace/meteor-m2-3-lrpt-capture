# Meteor M2-3 LRPT Sinyal Yakalama: Batı Türkiye'deki Bir Yer İstasyonundan Sina Yarımadası'nın Termal Görüntülenmesi

*14 Şubat 2026 — Manisa, Türkiye (38.63°N, 27.27°E)*

---

## Özet

Bu çalışma, Rus meteoroloji uydusu Meteor M2-3'ün (NORAD 57166) Batı Türkiye üzerinden gerçekleştirdiği gece geçişi sırasında 137.900 MHz frekansındaki LRPT (Low Rate Picture Transmission) sinyalinin başarıyla alınması ve çözümlenmesini belgelemektedir. Yazılım tanımlı radyo alıcı ve 137 MHz bandına optimize edilmiş V-dipol anten kullanılarak 30 dakikalık ham IQ verisi kaydedilmiştir. SatDump ile gerçekleştirilen çevrimdışı işleme sonucunda Doğu Akdeniz, Sina Yarımadası, Kızıldeniz havzası ve Arap Yarımadası'nı kapsayan kalibre edilmiş termal kızılötesi görüntüler elde edilmiştir. Görüntülerin yanı sıra uydu üzerindeki MSU-MR cihazının dedektör sıcaklıkları, kalibrasyon gövde okumaları ve cihaz durum bilgilerini içeren telemetri verisi de çıkarılarak analiz edilmiştir.

---

## 1. Hedef Uydu

**Meteor M2-3**, Roscosmos ve Rus Federal Hidrometeoroloji Servisi (Roshydromet) tarafından işletilen operasyonel bir kutupsal yörüngeli meteoroloji uydusudur. **27 Haziran 2023** tarihinde Vostochny Kozmodromu'ndan Soyuz-2.1b/Fregat fırlatma aracıyla yörüngeye yerleştirilmiştir.

| Parametre | Değer |
|-----------|-------|
| NORAD ID | 57166 |
| COSPAR ID | 2023-091A |
| Yörünge | Güneş-senkron, 832 km irtifa |
| Eğim | 98.77° |
| Yörünge periyodu | ~101 dakika |
| Ana cihaz | MSU-MR (Çok Spektrumlu Tarama Birimi — Orta Çözünürlük) |
| LRPT frekansı | 137.900 MHz |
| Modülasyon | OQPSK, 72.000 sembol/saniye |
| Protokol | CCSDS paketlenmiş telemetri |

MSU-MR cihazı, görünür ışıktan (0.5–0.7 µm) termal kızılötesine (11.5–12.5 µm) uzanan 6 spektral kanalda görüntüleme yapmaktadır. Yer çözünürlüğü yaklaşık 1 km, tarama genişliği ise 2.800 km'dir. Uydu, görüntü verisini 137.900 MHz üzerinden LRPT protokolüyle sürekli olarak yayınlamaktadır — şifrelenmemiş, açık erişimli bir downlink.

---

## 2. Yer İstasyonu Konfigürasyonu

### 2.1 Alıcı

Sinyal yakalama işlemi **RTL-SDR Blog V4** yazılım tanımlı radyo alıcısı ile gerçekleştirilmiştir. Bu birim, **Rafael Micro R828D** tuner entegresine sahip olup 24–1766 MHz etkin frekans aralığı, 8-bit ADC çözünürlüğü ve yaklaşık 2.56 MHz maksimum gerçek zamanlı bant genişliği sunmaktadır. Bu yakalama için aşağıdaki parametreler yapılandırılmıştır:

- **Merkez frekans:** 137.900.000 Hz
- **Örnekleme hızı:** 1.024.000 S/s
- **RF kazanç:** 44.5 dB (maksimum 49.6 dB'nin yakınında)
- **Kazanç modu:** Manuel
- **PPM düzeltmesi:** 0
- **Çıkış formatı:** cu8 (işaretsiz 8-bit arakatmanlı IQ)

### 2.2 Anten

137 MHz meteoroloji uydu bandı için özel olarak tasarlanmış bir **V-dipol anten** kullanılmıştır:

- **Eleman uzunluğu:** 2 × 53.4 cm (137 MHz'de çeyrek dalga boyu)
- **Eleman açısı:** 120° tepe açısı
- **Polarizasyon:** Zenitte RHCP yaklaşımı
- **Montaj:** Sabit, güneye bakan pencereye bitişik iç mekan yerleşimi

V-dipol geometrisi, üst yarımkürede çok yönlü alım deseni sağlamasıyla seçilmiştir — bu sayede geçiş sırasında uydu takibine gerek kalmamaktadır. 120° açı, yüksek elevasyon açılarında sağ elli dairesel polarizasyonun (RHCP) makul bir yaklaşımını sağlar — Meteor M2-3'ün RHCP yayınıyla uyumludur.

### 2.3 Yazılım Altyapısı

| Bileşen | Yazılım | Sürüm |
|---------|---------|-------|
| IQ kayıt | rtl_sdr (librtlsdr) | Güncel |
| Çözümleme ve görüntü işleme | SatDump | 1.2.2 |
| Sinyal analizi | Özel Python betikleri (NumPy/SciPy) | — |
| Yörünge tahmini | N2YO.com | — |

---

## 3. Geçiş Tahmini ve Yakalama Penceresi

14 Şubat 2026 akşamı için Manisa'dan görünen Meteor M2-3 geçişinin yörünge elemanları N2YO.com üzerinden hesaplanmıştır:

| Olay | Zaman (TRT, UTC+3) | Azimut | Elevasyon |
|------|---------------------|--------|-----------|
| AOS (Sinyal Yakalama Başlangıcı) | 21:34 | Güney | 0° |
| Maksimum elevasyon | 21:41 | Zenite yakın | 66.3° |
| LOS (Sinyal Kaybı) | 21:48 | Kuzey | 0° |

66.3° maksimum elevasyon mükemmel bir geçiş geometrisini temsil etmektedir — uydu neredeyse tam tepeden geçmekte ve eğik mesafe yol kaybını minimize etmektedir. Toplam teorik geçiş süresi yaklaşık 14 dakikadır.

Kayıt, tahmini AOS'tan 12 dakika önce **saat 21:22 TRT'de** başlatılmıştır — tam sinyal yakalama için geniş bir ön tampon bırakılmıştır. Kayıt 30 dakikalık kesintisiz IQ veri toplama için yapılandırılmış ve **3.69 GB ham IQ dosyası** elde edilmiştir.

---

## 4. Sinyal Analizi

Yakalama sonrası analiz, 30 dakikalık IQ kaydının 10 saniyelik bloklara bölünmesi ve her segment için LRPT passbandındaki sinyal-gürültü oranının (SNR) hesaplanmasıyla gerçekleştirilmiştir.

### 4.1 SNR Zaman Çizelgesi

```
Zaman (TRT)     SNR (dB)    Durum
──────────      ────────    ──────────────────────────
21:22–21:37       ~3.0      Gürültü tabanı (geçiş öncesi)
21:37:30           4.8      Zayıf sinyal başlangıcı
21:38:00           6.8      Sinyal algılandı (çözümleme eşiğinin üzerinde)
21:39:00           8.2      Güçlü sinyal
21:39:30           9.7      ZİRVE — maksimum SNR
21:40:00           4.8      Sinyal zayıflaması
21:41:30           3.0      Sinyal kaybı
21:41–21:52       ~3.0      Gürültü tabanı (geçiş sonrası)
```

### 4.2 Gözlemler

Etkin sinyal alım penceresi **yaklaşık 3.5 dakika** (21:38:00 – 21:41:30) olup toplam 14 dakikalık geçişin ~%25'ini temsil etmektedir. **9.7 dB** tepe SNR değeri 21:39:30'da kaydedilmiştir — LRPT sinyalinin güvenilir OQPSK demodülasyonu için gereken minimum ~5 dB eşiğinin oldukça üzerindedir.

Kısıtlı alım penceresi, antenin iç mekan yerleşiminden kaynaklanmaktadır. Güneye bakan pencereye bitişik konumlandırılmış V-dipol, bina yapısıyla sınırlı bir görüş alanına sahipti. Sinyal yalnızca uydu camdan görülebilen açısal pencereden geçerken alınabilmiştir — bu da yer istasyonunun güneyindeki yörünge izine, yani MSU-MR cihazının Doğu Akdeniz ve Sina bölgesini görüntülediği bölüme karşılık gelmektedir.

Tepe SNR'deki eğik mesafe yaklaşık **900 km** olarak hesaplanmıştır (832 km uydu irtifası + alım açısındaki geometrik ofset).

---

## 5. Çözümleme Hattı

### 5.1 SatDump İşleme

Ham IQ dosyası, SatDump'ın Meteor M2-x LRPT işleme hattından geçirilmiştir:

```bash
satdump meteor_m2-x_lrpt baseband \
    meteor_m23_RAW.cs16 \
    cikti_dizini/ \
    --samplerate 1024000 \
    --baseband_format cu8 \
    --fill_missing true
```

İşleme hattı aşağıdaki aşamaları sırasıyla yürütmektedir:
1. **Temelband filtreleme** — LRPT sinyaline merkezlenmiş bant geçiren filtre
2. **OQPSK demodülasyon** — 72k sembol/saniye hızında Ofset Dörtlü Faz Kaydırmalı Anahtarlama
3. **CCSDS çerçeve senkronizasyonu** — Geçerli telemetri çerçevelerinin tanımlanması
4. **Reed-Solomon hata düzeltme** — İleri hata düzeltme kod çözümü
5. **MSU-MR kanal ayrıştırma** — 6 spektral kanalın ayrılması
6. **Radyometrik kalibrasyon** — Uydu üzeri kalibrasyon verilerinin uygulanması
7. **Geometrik düzeltme** — Dünya eğriliği ve tarama geometrisi kompanzasyonu
8. **Harita katmanı bindirme** — Ülke sınırları ve kıyı çizgisi vektörleri

### 5.2 Format Düzeltmesi

İşleme sırasında karşılaşılan kritik bir husus: `rtl_sdr`, IQ verisini **cu8** formatında (işaretsiz 8-bit, 0–255 değer aralığı, 127.5 sıfır geçiş noktası) kaydetmektedir. İlk çözümleme denemesinde temelband formatı yanlışlıkla `cs16` (işaretli 16-bit kompleks) olarak belirtilmiş, bu da sıfır geçerli çerçeveyle tam çözümleme başarısızlığına yol açmıştır. Format parametresinin `cu8` olarak düzeltilmesiyle başarılı çıktı elde edilmiştir.

---

## 6. Sonuçlar

### 6.1 Görüntü Ürünleri

SatDump, birden fazla işleme modu ve spektral kombinasyonda toplam **27 görüntü ürünü** üretmiştir. **Gece geçişi** olduğundan yalnızca kızılötesi kanallar (3–6) kullanılabilir veri içermekteydi; görünür ışık kanalları (1–2) karanlıktı.

Başlıca görüntü ürünleri:

| Ürün | Açıklama | Kanallar |
|------|----------|----------|
| MCIR (Harita Renkli KÖ) | Coğrafi katmanlı yanlış renkli termal kompozit | 3, 4, 5 |
| MSA (Çok Spektrumlu Analiz) | Çok kanallı kompozit | 3, 4, 5, 6 |
| Kanal 4 Kalibre | Radyometrik kalibre termal KÖ (3.5–4.1 µm) | 4 |
| Kanal 5 | Termal KÖ (10.5–11.5 µm) | 5 |
| AVHRR Tarzı Yanlış Renk | NOAA uyumlu yanlış renk işleme | 1, 2, 4 |
| MSU-MR 124 Kompozit | Üç kanallı yanlış renk | 1, 2, 4 |

Her ürün dört varyantta üretilmiştir: temel görüntü, geometrik düzeltmeli, harita katmanlı ve düzeltmeli harita katmanlı.

### 6.2 Coğrafi Kapsam

Yakalanan görüntüler aşağıdaki bölgeyi kapsamaktadır:

- **Kızıldeniz** — Süveyş Körfezi'nden Babülmendep Boğazı'na kadar tam havza
- **Sina Yarımadası** — Tam kapsam, üçgen geometri net olarak çözünmüş
- **Nil Nehri ve Deltası** — Kuzeye uzanan termal kontrast çizgisi olarak görünür
- **Mısır** — Doğu Çölü ve Batı Çölü termal yapısı
- **Suudi Arabistan** — Batı Hicaz kıyısı ve iç çöl
- **Libya** — Doğu Kirenaika bölgesi
- **Irak / İran** — Görüntü periferisinde kısmi kapsam
- **Basra Körfezi** — Sıcak deniz yüzeyi belirgin şekilde ayrışmış

**Türkiye görüntülenememiştir.** MSU-MR'ın Türkiye topraklarını görüntülediği yörünge izi bölümünde, uydu iç mekan anteninin alım penceresinin dışında kalan yüksek kuzey elevasyon açısındaydı. Sinyal boşluğu, görüntülerin kuzey bölümünde beyaz bir şerit olarak görülmektedir.

### 6.3 Termal Yorumlama

Kızılötesi görüntüler **parlaklık sıcaklığını** temsil etmektedir — her piksel yüzey veya bulut tepesinin termal emisyon yoğunluğunu kodlamaktadır. Kalibre edilmiş Kanal 4 ürününde:

- **Koyu tonlar** = sıcak yüzeyler (çöl, deniz yüzeyi)
- **Açık tonlar** = soğuk yüzeyler (yüksek irtifa bulut tepeleri, yüksek rakımlı bölgeler)

Kızıldeniz yüzey sıcaklığı farkı açıkça görülmektedir — Akabe Körfezi'nin sığ kıyı suları, derin merkezi havzaya kıyasla belirgin şekilde farklı termal imzalar sergilemektedir.

---

## 7. Telemetri Analizi

Görüntülerin ötesinde, LRPT veri akışı uydu üzeri bakım telemetrisi de içermektedir. Çözümlenen 113 çerçevenin **18'i analog telemetri paketleri** barındırmaktadır.

### 7.1 Kamera Durumu

| Parametre | Değer | Yorum |
|-----------|-------|-------|
| Aktif kamera seti | **YEDEK Set #3** | Yedek sistem kullanımda (birincil değil) |
| Cihaz modu | Operasyonel görüntüleme | Tüm KÖ kanalları aktif |

Birincil set yerine yedek kamera setinin kullanılması, birincil cihaz zincirinde planlı bir operasyonel geçiş veya arıza kurtarma senaryosuna işaret etmektedir.

### 7.2 Kalibrasyon Gövdeleri

MSU-MR, radyometrik doğruluk için iki adet uydu üzeri kalibrasyon referansı kullanmaktadır:

| Kalibrasyon Kaynağı | Sıcaklık | İşlev |
|---------------------|----------|-------|
| Soğuk gövde | 262.65 K (−10.5°C) | Kazanç kalibrasyonu için düşük sıcaklık referansı |
| Sıcak gövde #1 | 317.37 K (+44.2°C) | Yüksek sıcaklık referansı |
| Sıcak gövde #2 | 318.00 K (+44.9°C) | Yüksek sıcaklık referansı (yedek) |
| Sıcak gövde #3 | **222.65 K (−50.5°C)** | **ANOMALİ — beklenen ~313 K** |

**Sıcak Gövde #3, beklenen değerlerin yaklaşık 90 K altında okuma vermektedir** — bu, gerçek bir sıcaklık sapmasından ziyade termistör bozulması veya açık devre arızasıyla tutarlıdır. Kalan kalibrasyon gövdeleri, doğru radyometrik ölçümler için yeterli referansı sağlamaktadır.

### 7.3 Dedektör Sıcaklıkları

| Dedektör | Okuma | Not |
|----------|-------|-----|
| KÖ Kanal 5 | 175–176 sayım | Kriyojenik soğutmalı, nominal |
| KÖ Kanal 6 | 141 sayım | En soğuk dedektör — en yüksek termal hassasiyet |
| Kalibrasyon lambası akımları | 138–144 | Tüm 6 lamba operasyonel |

---

## 8. Sinyal Bütçesi Analizi

### 8.1 Link Parametreleri

| Parametre | Değer |
|-----------|-------|
| Uydu EIRP | ~5 W (tahmini) |
| Frekans | 137.900 MHz |
| 900 km'de serbest uzay yol kaybı | ~145 dB |
| Anten kazancı (V-dipol, tahmini) | ~3 dBi |
| Alıcı gürültü figürü (R828D) | ~3.5 dB |
| Sistem gürültü sıcaklığı | ~600 K (tahmini, iç mekan ortamı) |
| Ölçülen tepe SNR | 9.7 dB |
| OQPSK çözümleme için gereken SNR | ~5 dB |
| Link marjı | ~4.7 dB |

4.7 dB link marjı, işlevsel ancak sınırlı bir bağlantıya işaret etmektedir. Açık ufuk görünürlüğüne sahip dış mekan anten yerleşimi ile SNR değerinin 15–25 dB aralığına yükselmesi ve geçişin tamamında gürbüz çözümleme marjı sağlanması beklenmektedir.

---

## 9. Kısıtlamalar ve Gelecek Çalışmalar

### 9.1 Mevcut Kısıtlamalar

1. **Sınırlı görüş alanı** — İç mekan anten yerleşimi, sinyal alımını toplam geçiş süresinin %25'iyle sınırlandırmış ve Türkiye topraklarını yakalanan görüntülerden dışlamıştır.

2. **Gece geçişi** — Yalnızca termal kızılötesi kanallar aktifti. Gündüz geçişinde 6 kanalın tamamı aktif olacak ve gerçek renkli ve bitki örtüsü indeksi ürünleri elde edilebilecektir.

3. **8-bit ADC kuantalama** — RTL-SDR'nin 8-bit ADC'si yaklaşık 48 dB dinamik aralık sağlamaktadır. 12–16 bit çözünürlüklü bir alıcı, düşük elevasyon açılarındaki zayıf sinyal performansını artıracaktır.

### 9.2 Planlanan İyileştirmeler

Sonraki yakalama girişimleri için:

- **Dış mekan anten konuşlandırması** — Engelsiz ufuk görünürlüğüne sahip yüksek bir kırsal konumda araç çatısına monte edilmiş V-dipol ile tam 360° gökyüzü kapsamı
- **Gündüz geçişi seçimi** — Görünür spektrum ve çok spektrumlu kompozit görüntüleme için
- **Genişletilmiş coğrafi kapsam** — Tam geçiş alımıyla görüntü şeridi Sahra-altı Afrika'dan Türkiye üzerinden İskandinavya'ya kadar uzanacaktır

---

## 10. Teknik Özet

| Parametre | Değer |
|-----------|-------|
| **Uydu** | Meteor M2-3 (NORAD 57166) |
| **Fırlatma tarihi** | 27 Haziran 2023, Vostochny Kozmodromu |
| **Yörünge** | Güneş-senkron, 832 km, 98.77° eğim |
| **Downlink** | 137.900 MHz LRPT, OQPSK 72k sym/s |
| **Yer istasyonu** | 38.63°N, 27.27°E — Manisa, Türkiye |
| **Alıcı** | RTL-SDR Blog V4 (R828D tuner) |
| **Anten** | V-Dipol, 2×53 cm, 120° geometri |
| **Örnekleme hızı** | 1.024.000 S/s |
| **RF kazanç** | 44.5 dB |
| **Ham IQ verisi** | 3.69 GB (cu8 formatı) |
| **Sinyal süresi** | ~3.5 dk / 14 dk geçiş |
| **Tepe SNR** | 9.7 dB |
| **Çözümlenen çerçeve** | 113 (18 telemetri içerikli) |
| **Görüntü ürünleri** | 27 PNG (termal KÖ) |
| **Coğrafi kapsam** | Doğu Akdeniz, Sina, Kızıldeniz, Arap Yarımadası |
| **Tepe eğik mesafe** | ~900 km |

---

## Sonuç

Bu yakalama, 832 km irtifadaki kutupsal yörüngeli bir meteoroloji uydusundan kalibre edilmiş termal görüntüler ve uydu üzeri cihaz telemetrisi dahil anlamlı meteorolojik verinin, yer tabanlı bir SDR alıcı ve pasif V-dipol anten ile başarıyla alınıp çözümlenebileceğini ortaya koymaktadır.

Elde edilen görüntüler gerçek bilimsel değer taşımaktadır: 1 km yer çözünürlüğünde, gömülü kalibrasyon verisi sayesinde kantitatif sıcaklık çıkarımına olanak tanıyan, Doğu Akdeniz ve Arap Yarımadası'nın radyometrik kalibre termal haritaları.

Bu ilk yakalamanın temel kısıtı anten yerleşimiydi. Dış mekan konuşlandırmasına ve engelsiz gökyüzü görünürlüğüne geçişle birlikte, tam geçiş alımı uydu'nun 2.800 km'lik görüntüleme şeridinin tamamını — Sahra-altı Afrika'dan Akdeniz üzerinden Kuzey Avrupa'ya kadar — kapsayacak ve gündüz geçişlerinin dahil edilmesi MSU-MR cihazının tam 6 kanallı spektral kapasitesini açığa çıkaracaktır.

Ham IQ verisi ve tüm görüntü ürünleri bağımsız doğrulama ve yeniden işleme için GitHub'da paylaşıma açık olacaktır.

---

*Ahmet Mersin*
*Manisa, Türkiye — Şubat 2026*
*SDR ve Uydu Haberleşme Araştırmaları*
