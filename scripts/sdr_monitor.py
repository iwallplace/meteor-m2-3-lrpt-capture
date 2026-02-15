#!/usr/bin/env python3
"""
SDR Canli Spektrum Monitoru — Saf PyQt5 (matplotlib yok)
Yag gibi akar, donma/kasma yok
"""
import sys, os, time
import numpy as np
from datetime import datetime

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QGridLayout)
from PyQt5.QtCore import QTimer, Qt, QRectF, QPointF
from PyQt5.QtGui import (QImage, QPixmap, QColor, QPainter, QFont, QPen,
    QLinearGradient, QPainterPath, QBrush)


class SpectrumCanvas(QWidget):
    """Saf QPainter ile cizim — sifir overhead"""
    def __init__(self, mode='spectrum'):
        super().__init__()
        self.mode = mode  # 'spectrum' veya 'waterfall' veya 'snr'
        self.data = None
        self.peak_data = None
        self.waterfall_data = None
        self.snr_data = None
        self.noise_floor = -50
        self.peak_val = -50
        self.peak_freq = 0
        self.snr = 0
        self.freqs = None
        self.is_signal = False
        self.setMinimumHeight(180 if mode != 'snr' else 100)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        w, h = self.width(), self.height()

        # Arka plan
        p.fillRect(0, 0, w, h, QColor('#0a0a1a'))

        if self.mode == 'spectrum' and self.data is not None:
            self._draw_spectrum(p, w, h)
        elif self.mode == 'waterfall' and self.waterfall_data is not None:
            self._draw_waterfall(p, w, h)
        elif self.mode == 'snr' and self.snr_data is not None:
            self._draw_snr(p, w, h)

        p.end()

    def _draw_spectrum(self, p, w, h):
        data = self.data
        n = len(data)
        margin_l, margin_r, margin_t, margin_b = 45, 10, 5, 20

        pw = w - margin_l - margin_r
        ph = h - margin_t - margin_b

        # Y eksen araligi
        y_min = self.noise_floor - 5
        y_max = max(self.peak_val + 5, self.noise_floor + 20)
        y_range = y_max - y_min
        if y_range < 1:
            y_range = 1

        # Grid
        p.setPen(QPen(QColor(51, 51, 102, 40), 1))
        for i in range(5):
            gy = margin_t + int(ph * i / 4)
            p.drawLine(margin_l, gy, w - margin_r, gy)
            val = y_max - (y_range * i / 4)
            p.setPen(QPen(QColor(150, 150, 150), 1))
            p.setFont(QFont('Menlo', 8))
            p.drawText(2, gy + 4, f"{val:.0f}")
            p.setPen(QPen(QColor(51, 51, 102, 40), 1))

        # Noise floor cizgisi
        nf_y = margin_t + int(ph * (y_max - self.noise_floor) / y_range)
        p.setPen(QPen(QColor(255, 170, 0, 80), 1, Qt.DashLine))
        p.drawLine(margin_l, nf_y, w - margin_r, nf_y)

        # Sinyal esigi
        thresh_y = margin_t + int(ph * (y_max - (self.noise_floor + 8)) / y_range)
        p.setPen(QPen(QColor(255, 68, 68, 50), 1, Qt.DashLine))
        p.drawLine(margin_l, thresh_y, w - margin_r, thresh_y)

        # Spektrum dolgu (gradient)
        path = QPainterPath()
        step = max(1, n // pw)
        first = True
        points = []

        for i in range(0, n, step):
            x = margin_l + int(pw * i / n)
            val = np.clip(data[i], y_min, y_max)
            y = margin_t + int(ph * (y_max - val) / y_range)
            points.append((x, y))
            if first:
                path.moveTo(x, y)
                first = False
            else:
                path.lineTo(x, y)

        # Dolgu icin path kapat
        fill_path = QPainterPath(path)
        fill_path.lineTo(margin_l + pw, margin_t + ph)
        fill_path.lineTo(margin_l, margin_t + ph)
        fill_path.closeSubpath()

        grad = QLinearGradient(0, margin_t, 0, margin_t + ph)
        grad.setColorAt(0, QColor(0, 255, 136, 60))
        grad.setColorAt(1, QColor(0, 255, 136, 5))
        p.fillPath(fill_path, QBrush(grad))

        # Spektrum cizgi
        p.setPen(QPen(QColor(0, 255, 136), 1.5))
        p.drawPath(path)

        # Peak hold
        if self.peak_data is not None:
            peak_path = QPainterPath()
            first = True
            for i in range(0, n, step):
                x = margin_l + int(pw * i / n)
                val = np.clip(self.peak_data[i], y_min, y_max)
                y = margin_t + int(ph * (y_max - val) / y_range)
                if first:
                    peak_path.moveTo(x, y)
                    first = False
                else:
                    peak_path.lineTo(x, y)
            p.setPen(QPen(QColor(255, 68, 68, 100), 1))
            p.drawPath(peak_path)

        # Peak isaretci
        if self.is_signal and self.freqs is not None:
            peak_idx = np.argmax(data)
            px = margin_l + int(pw * peak_idx / n)
            py = margin_t + int(ph * (y_max - self.peak_val) / y_range)
            p.setPen(QPen(QColor(255, 68, 68), 2))
            p.drawEllipse(QPointF(px, py), 4, 4)
            p.setFont(QFont('Menlo', 9, QFont.Bold))
            p.drawText(px + 8, py - 5, f"{self.peak_freq:.3f} MHz")
            p.drawText(px + 8, py + 10, f"SNR: {self.snr:.1f} dB")

    def _draw_waterfall(self, p, w, h):
        wf = self.waterfall_data
        rows, cols = wf.shape

        # Normalize
        vmin = self.noise_floor - 3
        vmax = self.noise_floor + 18
        rng = vmax - vmin
        if rng < 1:
            rng = 1

        # QImage olustur
        img = QImage(cols, rows, QImage.Format_RGB888)

        # Inferno benzeri renk tablosu (hizli lookup)
        for r in range(rows):
            for c in range(0, cols, max(1, cols // w)):
                val = (wf[r, c] - vmin) / rng
                val = max(0.0, min(1.0, val))

                # Inferno approx
                if val < 0.25:
                    cr = int(val * 4 * 80)
                    cg = 0
                    cb = int(val * 4 * 120)
                elif val < 0.5:
                    t = (val - 0.25) * 4
                    cr = 80 + int(t * 175)
                    cg = int(t * 50)
                    cb = 120 - int(t * 60)
                elif val < 0.75:
                    t = (val - 0.5) * 4
                    cr = 255
                    cg = 50 + int(t * 150)
                    cb = 60 - int(t * 60)
                else:
                    t = (val - 0.75) * 4
                    cr = 255
                    cg = 200 + int(t * 55)
                    cb = int(t * 100)

                img.setPixelColor(c, r, QColor(min(cr,255), min(cg,255), min(cb,255)))

        pixmap = QPixmap.fromImage(img).scaled(w, h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        p.drawPixmap(0, 0, pixmap)

    def _draw_snr(self, p, w, h):
        data = self.snr_data
        n = len(data)
        if n < 2:
            return

        margin_l, margin_r, margin_t, margin_b = 45, 10, 5, 15
        pw = w - margin_l - margin_r
        ph = h - margin_t - margin_b

        max_snr = max(max(data) + 5, 15)
        min_snr = 0

        # Grid
        p.setPen(QPen(QColor(51, 51, 102, 40), 1))
        for i in range(3):
            gy = margin_t + int(ph * i / 2)
            p.drawLine(margin_l, gy, w - margin_r, gy)

        # Sinyal esigi
        thresh_y = margin_t + int(ph * (max_snr - 8) / (max_snr - min_snr))
        p.setPen(QPen(QColor(255, 68, 68, 80), 1, Qt.DashLine))
        p.drawLine(margin_l, thresh_y, w - margin_r, thresh_y)
        p.setFont(QFont('Menlo', 7))
        p.setPen(QColor(255, 68, 68, 150))
        p.drawText(w - margin_r - 60, thresh_y - 3, "Sinyal esigi")

        # Cizgi
        path = QPainterPath()
        for i, val in enumerate(data):
            x = margin_l + int(pw * i / (n - 1))
            y = margin_t + int(ph * (max_snr - val) / (max_snr - min_snr))
            y = max(margin_t, min(margin_t + ph, y))
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

            # Nokta rengi
            color = QColor(255, 68, 68) if val > 8 else QColor(0, 255, 136)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(color))
            p.drawEllipse(QPointF(x, y), 2, 2)

        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(0, 255, 136, 100), 1))
        p.drawPath(path)


class SDRMonitor(QMainWindow):
    def __init__(self, iq_file, sample_rate=250000, center_freq=403.0, label="SDR Monitor"):
        super().__init__()
        self.iq_file = iq_file
        self.sample_rate = sample_rate
        self.center_freq = center_freq
        self.label = label
        self.FFT_SIZE = 1024  # Daha kucuk = daha hizli
        self.WATERFALL_ROWS = 80
        self.WF_COLS = 256  # Waterfall icin downsample

        self.freqs = np.linspace(center_freq - sample_rate/2e6, center_freq + sample_rate/2e6, self.FFT_SIZE)
        self.waterfall = np.full((self.WATERFALL_ROWS, self.FFT_SIZE), -50.0)
        self.peak_spectrum = np.full(self.FFT_SIZE, -80.0)
        self.snr_history = []
        self.start_time = time.time()
        self.window = np.hanning(self.FFT_SIZE).astype(np.float32)

        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(500)  # 500ms = 2 FPS, hafif

    def init_ui(self):
        self.setWindowTitle(f'SDR Monitor — {self.label}')
        self.setMinimumSize(900, 680)
        self.setStyleSheet("QMainWindow { background-color: #0d0d1a; }")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(4)
        layout.setContentsMargins(6, 6, 6, 6)

        # Baslik
        title = QLabel(f'  SDR Monitor — {self.label}')
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #00ff88; font-family: Menlo; padding: 2px;")
        layout.addWidget(title)

        # Stat satiri
        stat_bar = QWidget()
        stat_bar.setStyleSheet("background-color: #1a1a2e; border-radius: 4px;")
        stat_layout = QHBoxLayout(stat_bar)
        stat_layout.setContentsMargins(10, 4, 10, 4)

        self.stat_labels = {}
        for name in ["Durum", "SNR", "Peak", "Gurultu", "Dosya", "Sure"]:
            lbl = QLabel(f"{name}: —")
            lbl.setStyleSheet("color: #00ff88; font-family: Menlo; font-size: 11px;")
            stat_layout.addWidget(lbl)
            self.stat_labels[name] = lbl

        layout.addWidget(stat_bar)

        # Spektrum
        self.spectrum = SpectrumCanvas('spectrum')
        layout.addWidget(self.spectrum, stretch=3)

        # Waterfall
        self.waterfall_canvas = SpectrumCanvas('waterfall')
        layout.addWidget(self.waterfall_canvas, stretch=3)

        # SNR
        self.snr_canvas = SpectrumCanvas('snr')
        layout.addWidget(self.snr_canvas, stretch=1)

    def update_display(self):
        try:
            if not os.path.exists(self.iq_file):
                return

            file_size = os.path.getsize(self.iq_file)
            read_size = self.FFT_SIZE * 2 * 4

            if file_size < read_size:
                return

            with open(self.iq_file, 'rb') as f:
                f.seek(max(0, file_size - read_size))
                raw = f.read(read_size)

            data = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
            data = (data - 127.5) / 127.5
            iq = data[0::2] + 1j * data[1::2]

            if len(iq) < self.FFT_SIZE:
                return

            # FFT
            n_ffts = min(len(iq) // self.FFT_SIZE, 4)
            psd_avg = np.zeros(self.FFT_SIZE)
            for i in range(n_ffts):
                chunk = iq[i*self.FFT_SIZE:(i+1)*self.FFT_SIZE]
                fft_data = np.fft.fftshift(np.fft.fft(chunk * self.window))
                psd_avg += 20 * np.log10(np.abs(fft_data) + 1e-10)
            psd_avg /= n_ffts

            self.peak_spectrum = np.maximum(self.peak_spectrum * 0.995, psd_avg)

            self.waterfall = np.roll(self.waterfall, 1, axis=0)
            self.waterfall[0, :] = psd_avg

            noise_floor = np.median(psd_avg)
            peak_val = np.max(psd_avg)
            peak_freq = self.freqs[np.argmax(psd_avg)]
            snr = peak_val - noise_floor
            elapsed = file_size / (self.sample_rate * 2)
            size_mb = file_size / 1024 / 1024
            is_signal = snr > 8

            self.snr_history.append(snr)
            if len(self.snr_history) > 300:
                self.snr_history = self.snr_history[-300:]

            # Stats guncelle
            durum_color = '#ff4444' if is_signal else '#888'
            durum_text = "SINYAL!" if is_signal else "Tarama"
            self.stat_labels["Durum"].setText(f"Durum: {durum_text}")
            self.stat_labels["Durum"].setStyleSheet(f"color: {durum_color}; font-family: Menlo; font-size: 11px; font-weight: bold;")
            self.stat_labels["SNR"].setText(f"SNR: {snr:.1f} dB")
            self.stat_labels["Peak"].setText(f"Peak: {peak_freq:.3f} MHz ({peak_val:.0f} dB)")
            self.stat_labels["Gurultu"].setText(f"Taban: {noise_floor:.0f} dB")
            self.stat_labels["Dosya"].setText(f"{size_mb:.0f} MB")
            self.stat_labels["Sure"].setText(f"{elapsed/60:.1f} dk")

            # Canvas guncelle
            self.spectrum.data = psd_avg
            self.spectrum.peak_data = self.peak_spectrum
            self.spectrum.noise_floor = noise_floor
            self.spectrum.peak_val = peak_val
            self.spectrum.peak_freq = peak_freq
            self.spectrum.snr = snr
            self.spectrum.freqs = self.freqs
            self.spectrum.is_signal = is_signal
            self.spectrum.update()

            self.waterfall_canvas.waterfall_data = self.waterfall
            self.waterfall_canvas.noise_floor = noise_floor
            self.waterfall_canvas.update()

            self.snr_canvas.snr_data = list(self.snr_history)
            self.snr_canvas.update()

        except Exception as e:
            self.stat_labels["Durum"].setText(f"Hata: {str(e)[:30]}")


def main():
    if len(sys.argv) < 2:
        print("Kullanim: python3 sdr_monitor.py <iq_dosyasi> [sample_rate] [center_freq_mhz] [etiket]")
        print("")
        print("Ornekler:")
        print("  Balon:  python3 sdr_monitor.py sonde.cu8 250000 403.0 Radiosonde")
        print("  Meteor: python3 sdr_monitor.py meteor.cu8 1024000 137.9 'Meteor LRPT'")
        print("  SCADA:  python3 sdr_monitor.py scada.cu8 2048000 433.0 'SCADA 433'")
        sys.exit(1)

    iq_file = sys.argv[1]
    sample_rate = int(sys.argv[2]) if len(sys.argv) > 2 else 250000
    center_freq = float(sys.argv[3]) if len(sys.argv) > 3 else 403.0
    label = sys.argv[4] if len(sys.argv) > 4 else "SDR Monitor"

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    from PyQt5.QtGui import QPalette
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor('#0d0d1a'))
    pal.setColor(QPalette.WindowText, QColor('#00ff88'))
    app.setPalette(pal)

    mon = SDRMonitor(iq_file, sample_rate, center_freq, label)
    mon.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
