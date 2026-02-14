#!/bin/bash
# METEOR M2-3 - TAM YAKALAMA + DEKOD
# Ham IQ kaydet, sonra SatDump ile tüm bantları dekod et
# Kullanici girisli — saat, frekans, sure sorulur

BASE="/Volumes/Hangar/meteor_capture"

echo "============================================"
echo "  METEOR M2-3 YAKALAMA ARACI"
echo "============================================"
echo ""

# Frekans
read -p "Frekans (MHz) [varsayilan: 137.9]: " FREQ_INPUT
FREQ=${FREQ_INPUT:-137.9}

# Kazanc
read -p "Kazanc (dB) [varsayilan: 44.5]: " GAIN_INPUT
GAIN=${GAIN_INPUT:-44.5}

# Kayit suresi
read -p "Kayit suresi (dakika) [varsayilan: 30]: " DUR_INPUT
DUR_MIN=${DUR_INPUT:-30}
DURATION=$((DUR_MIN * 60))

# Bekleme saati
read -p "Kayit baslama saati (HH:MM) [bos = hemen basla]: " START_TIME

# Ornekleme hizi
read -p "Ornekleme hizi (S/s) [varsayilan: 1024000]: " SR_INPUT
SAMPLERATE=${SR_INPUT:-1024000}

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
IQ_FILE="${BASE}/meteor_m23_RAW_${TIMESTAMP}.cu8"
DECODE_DIR="${BASE}/meteor_m23_DECODED_${TIMESTAMP}"
LOG="${BASE}/meteor_final_${TIMESTAMP}.log"

mkdir -p "${DECODE_DIR}"

log() {
    echo "[$(date +%H:%M:%S)] $1" | tee -a "${LOG}"
}

SAMPLES=$((SAMPLERATE * DURATION))

echo ""
log "============================================"
log "  YAKALAMA PARAMETRELERI"
log "  Frekans    : ${FREQ} MHz"
log "  Kazanc     : ${GAIN} dB"
log "  Ornekleme  : ${SAMPLERATE} S/s"
log "  Sure       : ${DUR_MIN} dk (${DURATION} s)"
log "  Baslama    : ${START_TIME:-HEMEN}"
log "  Ham IQ     : ${IQ_FILE}"
log "  Dekod      : ${DECODE_DIR}"
log "  Disk bos   : $(df -h /Volumes/Hangar | tail -1 | awk '{print $4}')"
log "============================================"

# Bekleme
if [ -n "$START_TIME" ]; then
    log "Bekleniyor: ${START_TIME}..."
    while true; do
        CURRENT=$(date +%H:%M)
        if [[ "$CURRENT" > "$START_TIME" ]] || [[ "$CURRENT" == "$START_TIME" ]]; then
            log "KAYIT ZAMANI!"
            break
        fi
        echo -ne "\r[$(date +%H:%M:%S)] Bekleniyor... (${START_TIME})  "
        sleep 5
    done
else
    log "Hemen baslatiliyor..."
fi

# HAM IQ KAYIT
log "HAM IQ KAYIT BASLIYOR!"

FREQ_HZ=$(echo "${FREQ} * 1000000" | bc | cut -d. -f1)

rtl_sdr -f ${FREQ_HZ} -s ${SAMPLERATE} -g ${GAIN} -p 0 -n ${SAMPLES} "${IQ_FILE}" 2>&1 | tee -a "${LOG}"

IQ_SIZE=$(ls -lh "${IQ_FILE}" 2>/dev/null | awk '{print $5}')
log "IQ KAYIT TAMAMLANDI! Boyut: ${IQ_SIZE}"

# SATDUMP DEKOD
log "SATDUMP DEKOD BASLIYOR..."
log "Pipeline: meteor_m2-x_lrpt (OQPSK 72k)"

satdump meteor_m2-x_lrpt baseband "${IQ_FILE}" "${DECODE_DIR}" \
    --samplerate ${SAMPLERATE} \
    --baseband_format cu8 \
    --satellite_number M2-3 \
    --fill_missing true 2>&1 | tee -a "${LOG}"

log "DEKOD TAMAMLANDI!"

# SONUCLAR
log "============================================"
log "  DOSYALAR:"
ls -la "${DECODE_DIR}"/ 2>/dev/null | tee -a "${LOG}"
log ""

PNG_COUNT=$(find "${DECODE_DIR}" -name "*.png" -not -name "._*" 2>/dev/null | wc -l)
log "  TOPLAM GORUNTU: ${PNG_COUNT} adet"

if [ "${PNG_COUNT}" -gt 0 ]; then
    log "  GORUNTULER:"
    find "${DECODE_DIR}" -name "*.png" -not -name "._*" -exec ls -lh {} \; 2>/dev/null | tee -a "${LOG}"
    open "${DECODE_DIR}" 2>/dev/null
else
    log "  GORUNTU YOK - sinyal yetersiz olabilir"
    log "  Klasor icerigi:"
    ls -la "${DECODE_DIR}"/ 2>/dev/null | tee -a "${LOG}"
fi

log "============================================"
log "  Ham IQ : ${IQ_FILE} (${IQ_SIZE})"
log "  Dekod  : ${DECODE_DIR}"
log "  Log    : ${LOG}"
log "============================================"
