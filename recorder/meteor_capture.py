#!/usr/bin/env python3
"""
SDR Capture — Evrensel Yakalama Sistemi
Tek dosya: Zamanlanmis kayit + canli spektrum/waterfall/SNR GUI + otomatik decode

Kullanim:
  python3 meteor_capture.py --freq 137.9 --duration 24 --start 21:02 --label "Meteor"
  python3 meteor_capture.py --freq 403.0 --duration 120 --start 14:58 --sr 250000 --label "Balon"
  python3 meteor_capture.py --freq 137.9 --duration 10 --label "Test"
"""
import sys, os, time, signal, subprocess, threading, argparse
import numpy as np
from datetime import datetime

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel)
from PyQt5.QtCore import QTimer, Qt, QPointF
from PyQt5.QtGui import (QColor, QPainter, QFont, QPen,
    QLinearGradient, QPainterPath, QBrush, QPalette)


# ============================================================
# SPEKTRUM CANVAS
# ============================================================
class SpectrumCanvas(QWidget):
    def __init__(self, mode='spectrum'):
        super().__init__()
        self.mode = mode
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
        self.setMinimumHeight(160 if mode != 'snr' else 90)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        w, h = self.width(), self.height()
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
        ml, mr, mt, mb = 45, 10, 5, 20
        pw, ph = w - ml - mr, h - mt - mb

        y_min = self.noise_floor - 5
        y_max = max(self.peak_val + 5, self.noise_floor + 20)
        yr = max(y_max - y_min, 1)

        # Grid + dB labels
        p.setFont(QFont('Menlo', 8))
        for i in range(5):
            gy = mt + int(ph * i / 4)
            p.setPen(QPen(QColor(51, 51, 102, 40), 1))
            p.drawLine(ml, gy, w - mr, gy)
            p.setPen(QColor(150, 150, 150))
            p.drawText(2, gy + 4, f"{y_max - yr * i / 4:.0f}")

        # Noise floor
        nfy = mt + int(ph * (y_max - self.noise_floor) / yr)
        p.setPen(QPen(QColor(255, 170, 0, 80), 1, Qt.DashLine))
        p.drawLine(ml, nfy, w - mr, nfy)

        # Dolgu + cizgi
        path = QPainterPath()
        step = max(1, n // pw)
        first = True
        for i in range(0, n, step):
            x = ml + int(pw * i / n)
            y = mt + int(ph * (y_max - np.clip(data[i], y_min, y_max)) / yr)
            if first:
                path.moveTo(x, y)
                first = False
            else:
                path.lineTo(x, y)

        fill = QPainterPath(path)
        fill.lineTo(ml + pw, mt + ph)
        fill.lineTo(ml, mt + ph)
        fill.closeSubpath()
        grad = QLinearGradient(0, mt, 0, mt + ph)
        grad.setColorAt(0, QColor(0, 255, 136, 60))
        grad.setColorAt(1, QColor(0, 255, 136, 5))
        p.fillPath(fill, QBrush(grad))
        p.setPen(QPen(QColor(0, 255, 136), 1.5))
        p.drawPath(path)

        # Peak hold
        if self.peak_data is not None:
            pp = QPainterPath()
            first = True
            for i in range(0, n, step):
                x = ml + int(pw * i / n)
                y = mt + int(ph * (y_max - np.clip(self.peak_data[i], y_min, y_max)) / yr)
                if first:
                    pp.moveTo(x, y)
                    first = False
                else:
                    pp.lineTo(x, y)
            p.setPen(QPen(QColor(255, 68, 68, 100), 1))
            p.drawPath(pp)

        # Sinyal isaretci
        if self.is_signal and self.freqs is not None:
            idx = np.argmax(data)
            px = ml + int(pw * idx / n)
            py = mt + int(ph * (y_max - self.peak_val) / yr)
            p.setPen(QPen(QColor(255, 68, 68), 2))
            p.drawEllipse(QPointF(px, py), 4, 4)
            p.setFont(QFont('Menlo', 9, QFont.Bold))
            p.drawText(px + 8, py - 5, f"{self.peak_freq:.3f} MHz")
            p.drawText(px + 8, py + 10, f"SNR: {self.snr:.1f} dB")

    def _draw_waterfall(self, p, w, h):
        wf = self.waterfall_data
        rows, cols = wf.shape
        vmin = self.noise_floor - 1
        vrng = max(self.snr * 1.2, 8)

        # Numpy ile toplu renk hesapla
        norm = np.clip((wf - vmin) / vrng, 0, 1)

        # RGB dizisi olustur (inferno approx)
        r = np.zeros_like(norm, dtype=np.uint8)
        g = np.zeros_like(norm, dtype=np.uint8)
        b = np.zeros_like(norm, dtype=np.uint8)

        m1 = norm < 0.25
        m2 = (norm >= 0.25) & (norm < 0.5)
        m3 = (norm >= 0.5) & (norm < 0.75)
        m4 = norm >= 0.75

        r[m1] = (norm[m1] * 4 * 80).astype(np.uint8)
        b[m1] = (norm[m1] * 4 * 120).astype(np.uint8)

        t2 = (norm[m2] - 0.25) * 4
        r[m2] = (80 + t2 * 175).astype(np.uint8)
        g[m2] = (t2 * 50).astype(np.uint8)
        b[m2] = (120 - t2 * 60).astype(np.uint8)

        t3 = (norm[m3] - 0.5) * 4
        r[m3] = 255
        g[m3] = (50 + t3 * 150).astype(np.uint8)
        b[m3] = (60 - t3 * 60).astype(np.uint8)

        t4 = (norm[m4] - 0.75) * 4
        r[m4] = 255
        g[m4] = np.minimum(255, (200 + t4 * 55).astype(np.uint8))
        b[m4] = np.minimum(255, (t4 * 100).astype(np.uint8))

        # Downsample for speed
        target_w = min(w, cols)
        step = max(1, cols // target_w)
        r_ds = r[:, ::step]
        g_ds = g[:, ::step]
        b_ds = b[:, ::step]

        rgb = np.stack([r_ds, g_ds, b_ds], axis=-1).astype(np.uint8)
        rgb_cont = np.ascontiguousarray(rgb)
        dh, dw = rgb_cont.shape[:2]

        from PyQt5.QtGui import QImage, QPixmap
        img = QImage(rgb_cont.data, dw, dh, dw * 3, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(img).scaled(w, h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        p.drawPixmap(0, 0, pixmap)

    def _draw_snr(self, p, w, h):
        data = self.snr_data
        n = len(data)
        if n < 2:
            return

        ml, mr, mt, mb = 45, 10, 5, 15
        pw, ph = w - ml - mr, h - mt - mb
        smax = max(max(data) + 5, 15)

        p.setPen(QPen(QColor(51, 51, 102, 40), 1))
        for i in range(3):
            p.drawLine(ml, mt + int(ph * i / 2), w - mr, mt + int(ph * i / 2))

        ty = mt + int(ph * (smax - 8) / smax)
        p.setPen(QPen(QColor(255, 68, 68, 80), 1, Qt.DashLine))
        p.drawLine(ml, ty, w - mr, ty)

        path = QPainterPath()
        for i, val in enumerate(data):
            x = ml + int(pw * i / (n - 1))
            y = mt + max(0, min(ph, int(ph * (smax - val) / smax)))
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
            color = QColor(255, 68, 68) if val > 8 else QColor(0, 255, 136)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(color))
            if i % max(1, n // 100) == 0:
                p.drawEllipse(QPointF(x, y), 2, 2)

        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(0, 255, 136, 100), 1))
        p.drawPath(path)


# ============================================================
# ANA PENCERE
# ============================================================
class CaptureMonitor(QMainWindow):
    def __init__(self, args):
        super().__init__()
        self.args = args
        self.iq_file = None
        self.rtl_process = None
        self.recording = False
        self.decode_done = False
        self.waiting = True

        self.FFT_SIZE = 4096
        self.WATERFALL_ROWS = 120
        self.freqs = np.linspace(args.freq - args.sr/2e6, args.freq + args.sr/2e6, self.FFT_SIZE)
        self.waterfall = np.full((self.WATERFALL_ROWS, self.FFT_SIZE), -50.0)
        self.peak_spectrum = np.full(self.FFT_SIZE, -80.0)
        self.snr_history = []
        self.window = np.hanning(self.FFT_SIZE).astype(np.float32)

        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(500)

    def init_ui(self):
        a = self.args
        self.setWindowTitle(f'SDR Capture — {a.label}')
        self.setMinimumSize(950, 720)
        self.setStyleSheet("QMainWindow { background-color: #0d0d1a; }")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(4)
        layout.setContentsMargins(6, 6, 6, 6)

        # Baslik
        self.title_lbl = QLabel(f'  {a.label} — Bekleniyor...')
        self.title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #00ff88; font-family: Menlo;")
        layout.addWidget(self.title_lbl)

        # Stat bar
        stat_bar = QWidget()
        stat_bar.setStyleSheet("background-color: #1a1a2e; border-radius: 4px;")
        sl = QHBoxLayout(stat_bar)
        sl.setContentsMargins(10, 4, 10, 4)
        self.stats = {}
        for name in ["Durum", "SNR", "Peak", "Taban", "Dosya", "Sure", "Kalan"]:
            lbl = QLabel(f"{name}: —")
            lbl.setStyleSheet("color: #00ff88; font-family: Menlo; font-size: 11px;")
            sl.addWidget(lbl)
            self.stats[name] = lbl
        layout.addWidget(stat_bar)

        # Canvaslar
        self.spectrum = SpectrumCanvas('spectrum')
        layout.addWidget(self.spectrum, stretch=3)

        self.wf_canvas = SpectrumCanvas('waterfall')
        layout.addWidget(self.wf_canvas, stretch=3)

        self.snr_canvas = SpectrumCanvas('snr')
        layout.addWidget(self.snr_canvas, stretch=1)

        # Alt bilgi
        self.bottom_lbl = QLabel(f'  {a.freq} MHz | {a.sr/1000:.0f} kS/s | {a.gain} dB | {a.duration} dk')
        self.bottom_lbl.setStyleSheet("color: #555; font-family: Menlo; font-size: 10px;")
        layout.addWidget(self.bottom_lbl)

    def tick(self):
        if self.waiting:
            self._check_start_time()
        elif self.recording:
            self._update_recording()
        elif self.decode_done:
            pass  # Kapanacak

    def _check_start_time(self):
        a = self.args
        now = datetime.now().strftime('%H:%M')
        now_s = datetime.now().strftime('%H:%M:%S')

        if a.start:
            remaining = self._time_diff(now, a.start)
            self.title_lbl.setText(f'  {a.label} — Bekleniyor: {a.start}')
            self.stats["Durum"].setText(f"Durum: BEKLE")
            self.stats["Durum"].setStyleSheet("color: #ffaa00; font-family: Menlo; font-size: 11px; font-weight: bold;")
            self.stats["Kalan"].setText(f"Kalan: {remaining}")
            self.stats["Sure"].setText(f"Saat: {now_s}")

            if now >= a.start:
                self._start_recording()
        else:
            self._start_recording()

    def _time_diff(self, now_str, target_str):
        try:
            nh, nm = map(int, now_str.split(':'))
            th, tm = map(int, target_str.split(':'))
            diff = (th * 60 + tm) - (nh * 60 + nm)
            if diff < 0:
                diff += 1440
            return f"{diff} dk"
        except:
            return "?"

    def _start_recording(self):
        a = self.args
        self.waiting = False
        self.recording = True

        # SDR testi
        self.stats["Durum"].setText("Durum: SDR TEST")
        self.stats["Durum"].setStyleSheet("color: #ffaa00; font-family: Menlo; font-size: 11px; font-weight: bold;")
        QApplication.processEvents()

        test = subprocess.run(
            ['rtl_sdr', '-f', f'{a.freq}e6', '-s', str(a.sr), '-g', str(a.gain), '-n', str(a.sr), '/tmp/_sdr_test.cu8'],
            capture_output=True, text=True, timeout=10
        )
        os.remove('/tmp/_sdr_test.cu8') if os.path.exists('/tmp/_sdr_test.cu8') else None

        if 'Found' not in test.stderr and 'Found' not in test.stdout:
            self.stats["Durum"].setText("Durum: SDR YOK!")
            self.stats["Durum"].setStyleSheet("color: #ff4444; font-family: Menlo; font-size: 11px; font-weight: bold;")
            self.recording = False
            return

        # Dosya yolu
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        os.makedirs(a.output, exist_ok=True)
        self.iq_file = os.path.join(a.output, f'{a.label.replace(" ", "_")}_{ts}.cu8')
        self.decode_dir = os.path.join(a.output, f'{a.label.replace(" ", "_")}_{ts}_DECODED')
        self.log_file = os.path.join(a.output, f'{a.label.replace(" ", "_")}_{ts}.log')

        # Kayit basla
        samples = a.sr * a.duration * 60
        self.record_start = time.time()
        self.record_duration = a.duration * 60

        self.rtl_process = subprocess.Popen(
            ['rtl_sdr', '-f', f'{a.freq}e6', '-s', str(a.sr), '-g', str(a.gain), '-p', '0', '-n', str(samples), self.iq_file],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        self.title_lbl.setText(f'  {a.label} — KAYIT YAPILIYOR')
        self._log(f"Kayit basladi: {self.iq_file}")
        self._log(f"Frekans: {a.freq} MHz | SR: {a.sr} | Gain: {a.gain} dB | Sure: {a.duration} dk")

    def _update_recording(self):
        if not self.iq_file or not os.path.exists(self.iq_file):
            return

        # rtl_sdr bitti mi?
        if self.rtl_process and self.rtl_process.poll() is not None:
            self._finish_recording()
            return

        try:
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
            psd = np.zeros(self.FFT_SIZE)
            for i in range(n_ffts):
                chunk = iq[i*self.FFT_SIZE:(i+1)*self.FFT_SIZE]
                psd += 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(chunk * self.window))) + 1e-10)
            psd /= n_ffts

            self.peak_spectrum = np.maximum(self.peak_spectrum * 0.995, psd)
            self.waterfall = np.roll(self.waterfall, 1, axis=0)
            self.waterfall[0, :] = psd

            nf = np.median(psd)
            pv = np.max(psd)
            pf = self.freqs[np.argmax(psd)]
            snr = pv - nf
            elapsed = time.time() - self.record_start
            remaining = max(0, self.record_duration - elapsed)
            size_mb = file_size / 1024 / 1024
            is_sig = snr > 8

            self.snr_history.append(snr)
            if len(self.snr_history) > 300:
                self.snr_history = self.snr_history[-300:]

            # Stats
            dc = '#ff4444' if is_sig else '#00ff88'
            dt = "SINYAL!" if is_sig else "Kayit"
            self.stats["Durum"].setText(f"Durum: {dt}")
            self.stats["Durum"].setStyleSheet(f"color: {dc}; font-family: Menlo; font-size: 11px; font-weight: bold;")
            self.stats["SNR"].setText(f"SNR: {snr:.1f} dB")
            self.stats["Peak"].setText(f"Peak: {pf:.3f} MHz")
            self.stats["Taban"].setText(f"Taban: {nf:.0f} dB")
            self.stats["Dosya"].setText(f"{size_mb:.0f} MB")
            self.stats["Sure"].setText(f"{elapsed/60:.1f} dk")
            self.stats["Kalan"].setText(f"Kalan: {remaining/60:.1f} dk")

            # Canvas
            self.spectrum.data = psd
            self.spectrum.peak_data = self.peak_spectrum
            self.spectrum.noise_floor = nf
            self.spectrum.peak_val = pv
            self.spectrum.peak_freq = pf
            self.spectrum.snr = snr
            self.spectrum.freqs = self.freqs
            self.spectrum.is_signal = is_sig
            self.spectrum.update()

            self.wf_canvas.waterfall_data = self.waterfall
            self.wf_canvas.noise_floor = nf
            self.wf_canvas.snr = snr
            self.wf_canvas.update()

            self.snr_canvas.snr_data = list(self.snr_history)
            self.snr_canvas.update()

        except Exception as e:
            pass

    def _finish_recording(self):
        self.recording = False
        a = self.args
        size = os.path.getsize(self.iq_file) / 1024 / 1024 if os.path.exists(self.iq_file) else 0

        self.title_lbl.setText(f'  {a.label} — DECODE EDILIYOR...')
        self.stats["Durum"].setText("Durum: DECODE")
        self.stats["Durum"].setStyleSheet("color: #ffaa00; font-family: Menlo; font-size: 11px; font-weight: bold;")
        self.stats["Kalan"].setText("")
        self._log(f"Kayit tamamlandi: {size:.0f} MB")
        QApplication.processEvents()

        # SatDump decode (sadece meteor icin)
        if 'meteor' in a.label.lower() or a.freq < 140:
            os.makedirs(self.decode_dir, exist_ok=True)
            self._log("SatDump decode basliyor...")

            decode = subprocess.run(
                ['satdump', 'meteor_m2-x_lrpt', 'baseband', self.iq_file, self.decode_dir,
                 '--samplerate', str(a.sr), '--baseband_format', 'cu8', '--fill_missing', 'true'],
                capture_output=True, text=True, timeout=600
            )

            # Sonuc kontrol
            png_count = 0
            if os.path.exists(self.decode_dir):
                for root, dirs, files in os.walk(self.decode_dir):
                    png_count += sum(1 for f in files if f.endswith('.png') and not f.startswith('._'))

            self._log(f"Decode tamamlandi: {png_count} goruntu")

            if png_count > 0:
                self.title_lbl.setText(f'  {a.label} — BASARILI! {png_count} goruntu')
                self.stats["Durum"].setText(f"Durum: {png_count} PNG!")
                self.stats["Durum"].setStyleSheet("color: #00ff88; font-family: Menlo; font-size: 11px; font-weight: bold;")
                subprocess.run(['open', self.decode_dir])
            else:
                self.title_lbl.setText(f'  {a.label} — Goruntu yok')
                self.stats["Durum"].setText("Durum: 0 goruntu")
                self.stats["Durum"].setStyleSheet("color: #ff4444; font-family: Menlo; font-size: 11px; font-weight: bold;")
        else:
            self.title_lbl.setText(f'  {a.label} — Kayit tamamlandi ({size:.0f} MB)')
            self.stats["Durum"].setText("Durum: TAMAM")
            self.stats["Durum"].setStyleSheet("color: #00ff88; font-family: Menlo; font-size: 11px; font-weight: bold;")

        self.decode_done = True

        # 10 sn sonra kapat
        QTimer.singleShot(10000, self._quit)

    def _quit(self):
        self._log("Program kapaniyor.")
        QApplication.quit()

    def _log(self, msg):
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
        print(line)
        if hasattr(self, 'log_file') and self.log_file:
            try:
                with open(self.log_file, 'a') as f:
                    f.write(line + '\n')
            except:
                pass

    def closeEvent(self, event):
        if self.rtl_process and self.rtl_process.poll() is None:
            self.rtl_process.terminate()
        event.accept()


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser(description='SDR Capture — Kayit ve Izleme')
    parser.add_argument('--freq', type=float, default=137.9, help='Merkez frekans (MHz)')
    parser.add_argument('--gain', type=float, default=44.5, help='Kazanc (dB)')
    parser.add_argument('--duration', type=int, default=15, help='Kayit suresi (dakika)')
    parser.add_argument('--start', type=str, default=None, help='Baslama saati HH:MM (bos = hemen)')
    parser.add_argument('--sr', type=int, default=1024000, help='Sample rate (S/s)')
    parser.add_argument('--label', type=str, default='SDR_Capture', help='Etiket')
    parser.add_argument('--output', type=str, default='.', help='Cikti klasoru')

    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor('#0d0d1a'))
    pal.setColor(QPalette.WindowText, QColor('#00ff88'))
    app.setPalette(pal)

    mon = CaptureMonitor(args)
    mon.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
