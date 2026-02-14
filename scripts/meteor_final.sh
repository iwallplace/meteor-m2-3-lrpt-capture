#!/bin/bash
# METEOR M2-3 - TAM YAKALAMA + DEKOD
# Ham IQ kaydet, sonra SatDump ile tüm bantları dekod et
# 14 Şubat 2026, 21:36-21:48 TRT, 137.9 MHz, 66.3°

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BASE="/Volumes/Hangar/meteor_capture"
IQ_FILE="${BASE}/meteor_m23_RAW_${TIMESTAMP}.cs16"
DECODE_DIR="${BASE}/meteor_m23_DECODED_${TIMESTAMP}"
LOG="${BASE}/meteor_final_${TIMESTAMP}.log"

mkdir -p "${DECODE_DIR}"

log() {
    echo "[$(date +%H:%M:%S)] $1" | tee -a "${LOG}"
}

log "============================================"
log "  METEOR M2-3 - TAM YAKALAMA"
log "  137.9 MHz | 1024000 S/s | 30 dk kayit"
log "  Ham IQ -> ${IQ_FILE}"
log "  Dekod  -> ${DECODE_DIR}"
log "============================================"

# 21:22'de basla
while true; do
    CURRENT=$(date +%H:%M)
    if [[ "$CURRENT" > "21:21" ]] || [[ "$CURRENT" == "21:22" ]]; then
        log "KAYIT ZAMANI!"
        break
    fi
    echo -ne "\r[$(date +%H:%M:%S)] Bekleniyor... (21:22)  "
    sleep 5
done

# HAM IQ KAYIT - 30 dakika (gecisten 14dk once + 12dk gecis + 4dk sonra)
DURATION=1800
SAMPLES=$((1024000 * DURATION))
EXPECTED_SIZE=$((SAMPLES * 4 / 1024 / 1024 / 1024))
log "HAM IQ KAYIT BASLIYOR!"
log "  Sure: ${DURATION}s (30 dk)"
log "  Beklenen boyut: ~${EXPECTED_SIZE} GB"
log "  Disk bos: $(df -h /Volumes/Hangar | tail -1 | awk '{print $4}')"

rtl_sdr -f 137.9e6 -s 1024000 -g 44.5 -p 0 -n ${SAMPLES} "${IQ_FILE}" 2>&1 | tee -a "${LOG}"

IQ_SIZE=$(ls -lh "${IQ_FILE}" 2>/dev/null | awk '{print $5}')
log "IQ KAYIT TAMAMLANDI! Boyut: ${IQ_SIZE}"

# SATDUMP DEKOD - tum bantlar
log "SATDUMP DEKOD BASLIYOR..."
log "Pipeline: meteor_m2-x_lrpt (OQPSK 72k)"

satdump meteor_m2-x_lrpt baseband "${IQ_FILE}" "${DECODE_DIR}" \
    --samplerate 1024000 \
    --baseband_format cu8 \
    --satellite_number M2-3 \
    --fill_missing true 2>&1 | tee -a "${LOG}"

log "DEKOD TAMAMLANDI!"

# SONUCLAR
log "============================================"
log "  DOSYALAR:"
ls -la "${DECODE_DIR}"/ 2>/dev/null | tee -a "${LOG}"
log ""

PNG_COUNT=$(ls "${DECODE_DIR}"/*.png 2>/dev/null | wc -l)
log "  TOPLAM GORUNTU: ${PNG_COUNT} adet"

if [ "${PNG_COUNT}" -gt 0 ]; then
    log "  GORUNTULER:"
    ls -lh "${DECODE_DIR}"/*.png 2>/dev/null | tee -a "${LOG}"
    open "${DECODE_DIR}" 2>/dev/null
else
    log "  GORUNTU YOK - sinyal yetersiz olabilir"
    log "  Klasor icerigi:"
    ls -la "${DECODE_DIR}"/ 2>/dev/null | tee -a "${LOG}"
fi

log "============================================"
log "  Ham IQ: ${IQ_FILE} (${IQ_SIZE})"
log "  Dekod : ${DECODE_DIR}"
log "  Log   : ${LOG}"
log "============================================"
