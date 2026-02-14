import sys, numpy as np, sounddevice as sd, queue, time, math, random, json, os, platform, signal
from PySide6.QtCore import Qt, QTimer, QPointF, QRect, QEvent, QObject
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QGridLayout, QLabel, QComboBox, QPushButton, QSpinBox,
                             QSlider, QFrame, QCheckBox, QTextEdit, QDialog, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView,
                             QLineEdit, QAbstractSpinBox, QMenu)
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QCursor, QAction, QActionGroup, QRadialGradient

# ==========================================
#  Constants & Config
# ==========================================
APP_NAME = "InnerPulse"
APP_VERSION = "v1.8.0"
JSON_FILENAME = "setlist.json"
CONFIG_FILENAME = "config.json"
DEFAULT_SONG = {"name": "Default", "bpm": 120, "bpb": 4}

MAIN_STYLE = """
    QMainWindow { background-color: #181818; }
    QLabel { color: #e0e0e0; font-family: 'Segoe UI', 'San Francisco', 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 13px; }
    
    QFrame#ConfigBox, QFrame#SetlistBox { 
        background: #252526; 
        border: 1px solid #333; 
        border-radius: 8px; 
    }
    
    /* Global PushButton Style - Premium Professional Look */
    QPushButton {
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #424242, stop:1 #333333);
        color: #f0f0f0;
        border: 1px solid #222;
        border-top: 1px solid #555;
        border-radius: 4px;
        padding: 5px 16px;
        font-weight: 600;
        font-size: 11px;
    }
    QPushButton:hover { 
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4a4a4a, stop:1 #3b3b3b);
        border-color: #444;
    }
    QPushButton:pressed { 
        background-color: #2b2b2b; 
        border: 1px solid #111;
        padding-top: 6px;
        padding-bottom: 4px;
    }
    QPushButton:disabled { background-color: #252526; color: #555; border-color: #333; }

    /* Start Button - Deep Gradient & Glow */
    QPushButton#StartBtn { 
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #00a4ef, stop:1 #007acc);
        color: white; 
        font-size: 16px; 
        border: 1px solid #005a9e;
        border-top: 1px solid #00c3ff;
        border-radius: 6px;
    }
    QPushButton#StartBtn:hover { 
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1eb1f5, stop:1 #008be6);
    }
    QPushButton#StartBtn:pressed { 
        background-color: #006bb3; 
        border: none;
    }
    
    /* Secondary Buttons (Mode, Nav, MuteOpts) */
    QPushButton#ModeBtn, QPushButton#NavBtn { 
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3c3c3c, stop:1 #2d2d30);
        border: 1px solid #1a1a1a;
        border-top: 1px solid #4a4a4a;
        color: #ccc;
    }
    QPushButton#NavBtn { padding: 0; }
    QPushButton#ModeBtn:hover, QPushButton#NavBtn:hover {
        background-color: #444;
        color: white;
    }

    QPushButton#EditBtn, QPushButton#LogBtn {
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4a4a4d, stop:1 #3a3a3d);
        border: 1px solid #2a2a2d;
        border-top: 1px solid #5a5a5d;
        color: #dae0ed;
    }
    QPushButton#EditBtn:hover { background-color: #4e4e52; }

    /* ComboBox */
    QComboBox { 
        background: #252526; 
        color: #e0e0e0; 
        border: 1px solid #3e3e42; 
        padding: 3px 8px; 
        border-radius: 4px;
        font-size: 11px;
    }
    QComboBox::drop-down { border: none; width: 20px; }
    QComboBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #888; margin-right: 8px; }
    QComboBox QAbstractItemView { background-color: #252526; color: #e0e0e0; selection-background-color: #007acc; border: 1px solid #3e3e42; outline: none; }

    /* SpinBox */
    QSpinBox { 
        background: #1e1e1e; 
        color: #4CAF50; 
        padding: 4px; 
        font-size: 14px; 
        border-radius: 4px; 
        font-weight: bold; 
        border: 1px solid #333; 
    }
    QSpinBox:disabled { color: #555; background: #252526; }
    QSpinBox::up-button, QSpinBox::down-button { width: 0; height: 0; } /* Hide buttons */

    /* CheckBox */
    QCheckBox { color: #ccc; font-weight: 600; font-size: 11px; spacing: 4px; }
    QCheckBox::indicator { width: 16px; height: 16px; border-radius: 3px; border: 1px solid #444; background: #1e1e1e; }
    QCheckBox::indicator:checked { background: #007acc; border-color: #007acc; }

    /* Slider - Pro Audio Look */
    QSlider::groove:vertical { 
        background: #222; 
        width: 8px; 
        border-radius: 4px; 
        border: 1px solid #333;
    }
    QSlider::handle:vertical { 
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #666, stop:1 #444);
        height: 12px; 
        margin: 0 -4px; 
        border-radius: 2px; 
        border: 1px solid #222;
        border-top: 1px solid #777;
    }
    QSlider::handle:vertical:hover { background: #777; }
    QSlider::sub-page:vertical { background: #111; border-radius: 4px; }
"""

SETLIST_STYLE = """
    QDialog { background: #222; color: #eee; }
    QTableWidget { background: #333; color: #eee; gridline-color: #444; font-size: 13px; }
    QTableWidget::item { padding: 4px; }
    QTableWidget::item:selected { background-color: #007acc; color: white; border: 1px solid #44ff44; }
    QHeaderView::section { background-color: #444; color: #ddd; border: 1px solid #555; font-size: 12px; font-weight: bold; padding: 5px; }
    QTableWidget QLineEdit {
        background-color: #ffffff;
        color: #000000;
        font-weight: bold;
        border: 2px solid #00aaff;
        selection-background-color: #007acc;
        selection-color: white;
    }
    QPushButton { font-size: 12px; padding: 6px; }
"""

# ==========================================
#  Audio Engine
# ==========================================
class AudioEngine:
    def __init__(self):
        self.stream = None
        self.sr = 48000
        self.is_playing = False
        self.pending_start = False
        self.device_index = None
        self.buffer_size = 128
        self.waves = {}
        self.params = {
            "bpm": 120, "bpb": 4, "play": 3, "mute": 1,
            "v_master": 0.8, "v_acc": 0.8, "v_backbeat": 0.0, "v_4th": 0.5, "v_8th": 0.0,
            "v_16th": 0.0, "v_trip": 0.0, "v_mute_dim": 0.0,
            "rnd": False, "force_play": False, "tone_mode": "electronic",
            "rnd_play_min": 1, "rnd_play_max": 2, "rnd_mute_min": 1, "rnd_mute_max": 2
        }
        self.mute_options = {
            "acc": False, "backbeat": False, "4th": False,
            "8th": False, "16th": False, "trip": False
        }
        self.state = {"total_samples": 0, "next_tick": 0, "tick_count": 0, "is_mute": False, "active_voices": [], "zero_offset": 0, "rnd_phase": "play", "rnd_left": 3}
        self.queue = queue.Queue()
        self.current_device_name = "None"
        self.last_sent_pos = 0.0

    def update(self, key, val): self.params[key] = val

    def set_tone_mode(self, mode):
        self.params["tone_mode"] = mode
        # Regenerate waves with new tone mode
        tone_mode = self.params.get("tone_mode", "electronic")
        self.waves = {
            "acc": self._make_wave("bell", 2000, mode=tone_mode),
            "backbeat": self._make_wave("snare", duration=0.15, mode=tone_mode),
            "4th": self._make_wave("click", 800, mode=tone_mode),
            "8th": self._make_wave("hihat", mode=tone_mode),
            "16th": self._make_wave("shaker", mode=tone_mode),
            "trip": self._make_wave("wood", mode=tone_mode)
        }

    def get_filtered_devices(self):
        try:
            devices = sd.query_devices()
            hostapis = sd.query_hostapis()
            candidates = []
            has_high_perf = False
            for i, d in enumerate(devices):
                if d['max_output_channels'] > 0:
                    api_name = hostapis[d['hostapi']]['name']
                    is_good = any(x in api_name for x in ["ASIO", "WASAPI", "Core Audio"])
                    if is_good:
                        has_high_perf = True
                    candidates.append((i, f"{api_name}: {d['name']}", is_good))
            return [c[:2] for c in candidates if not has_high_perf or c[2]]
        except: return []

    def _make_wave(self, type="sine", freq=1000, duration=0.1, mode="electronic"):
        length = int(self.sr * duration)
        t = np.linspace(0, duration, length, endpoint=False)

        if mode == "woody":
            # Pendulum metronome sounds: short, sharp clicks like a mechanical metronome
            if type == "bell":
                # Accent: louder pendulum click with slight metallic ring
                wave = np.sin(2 * np.pi * 600 * t) * np.exp(-t * 100) * 0.6
                wave += np.sin(2 * np.pi * 1200 * t) * np.exp(-t * 150) * 0.3
                wave += np.random.uniform(-0.05, 0.05, length) * np.exp(-t * 200) * 0.1
            elif type == "click":
                # Quarter notes: standard pendulum click
                wave = np.sin(2 * np.pi * 500 * t) * np.exp(-t * 110) * 0.5
                wave += np.sin(2 * np.pi * 1000 * t) * np.exp(-t * 160) * 0.2
            elif type == "hihat":
                # 8th notes: use electronic sound
                wave = np.random.uniform(-0.9, 0.9, length) * np.exp(-t * 80) * 0.9
            elif type == "shaker":
                # 16th notes: use electronic sound
                wave = np.random.uniform(-0.8, 0.8, length) * np.exp(-t * 50) * 0.8
            elif type == "wood":
                # Triplets: subtle click
                wave = np.sin(2 * np.pi * 580 * t) * np.exp(-t * 125) * 0.38
                wave += np.sin(2 * np.pi * 1150 * t) * np.exp(-t * 175) * 0.14
            elif type == "snare":
                # Backbeat: use electronic sound
                noise = np.random.uniform(-1.0, 1.0, length) * np.exp(-t * 30)
                tone = np.sin(2 * np.pi * 180 * t) * np.exp(-t * 15) * 0.5
                wave = (noise + tone) * 0.8
            else:
                wave = np.zeros(length)
        else:
            # Original electronic sounds
            if type == "bell": wave = (np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 2 * t)) * np.exp(-t * 8) * 0.3
            elif type == "click": wave = np.tanh(np.sin(2 * np.pi * freq * t) * 5) * np.exp(-t * 20) * 0.5
            elif type == "hihat": wave = np.random.uniform(-0.9, 0.9, length) * np.exp(-t * 80) * 0.9
            elif type == "shaker": wave = np.random.uniform(-0.8, 0.8, length) * np.exp(-t * 50) * 0.8
            elif type == "wood": wave = np.sin(np.cumsum(np.linspace(freq, freq/2, length)) / self.sr * 2 * np.pi) * np.exp(-t * 30) * 0.6
            elif type == "snare":
                noise = np.random.uniform(-1.0, 1.0, length) * np.exp(-t * 30)
                tone = np.sin(2 * np.pi * 180 * t) * np.exp(-t * 15) * 0.5
                wave = (noise + tone) * 0.8
            else: wave = np.zeros(length)

        return wave.astype(np.float32)

    def boot(self):
        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
            dev_info = sd.query_devices(self.device_index, 'output')
            self.sr = int(dev_info.get('default_samplerate', 48000))
            self.current_device_name = dev_info['name']
            tone_mode = self.params.get("tone_mode", "electronic")
            self.waves = {
                "acc": self._make_wave("bell", 2000, mode=tone_mode),
                "backbeat": self._make_wave("snare", duration=0.15, mode=tone_mode),
                "4th": self._make_wave("click", 800, mode=tone_mode),
                "8th": self._make_wave("hihat", mode=tone_mode),
                "16th": self._make_wave("shaker", mode=tone_mode),
                "trip": self._make_wave("wood", mode=tone_mode)
            }
            n_channels = min(2, int(dev_info['max_output_channels']))
            self.stream = sd.OutputStream(
                device=self.device_index, channels=n_channels, callback=self._cb, latency='low',
                blocksize=self.buffer_size, samplerate=self.sr
            )
            self.stream.start()
            self.state["total_samples"] = 0
            return f"{dev_info['name']} ({self.sr}Hz / {n_channels}ch / Buf:{self.buffer_size})"
        except Exception as e: return f"Error: {str(e)[:15]}"

    def request_start(self):
        while not self.queue.empty():
            try: self.queue.get_nowait()
            except: break
        self.pending_start = True

    def pause(self):
        self.is_playing = False; self.pending_start = False
        self.queue.put({"type": "vis", "pos": -1.0, "mute": False})

    def _cb(self, outdata, frames, time_info, status):
        outdata.fill(0); st = self.state; start_s = st["total_samples"]; st["total_samples"] += frames
        if self.pending_start:
            st["zero_offset"] = start_s; st["next_tick"] = start_s; st["tick_count"] = 0; st["active_voices"] = []; self.is_playing = True; self.pending_start = False
        if not self.is_playing: return
        end_s = start_s + frames
        while st["next_tick"] < end_s:
            off = int(st["next_tick"] - start_s)
            if 0 <= off < frames: self._trigger(off)
            st["next_tick"] += (self.sr * 60.0 / self.params["bpm"]) / 12.0; st["tick_count"] += 1
        new_voices = []
        for cur, wav, vol, s_off in st["active_voices"]:
            wav_cur, b_start = int(cur), int(max(0, s_off)); L = min(frames - b_start, len(wav) - wav_cur)
            if L > 0:
                outdata[b_start:b_start+L] += (wav[wav_cur:wav_cur+L] * vol)[:, None]
                if wav_cur + L < len(wav): new_voices.append([wav_cur+L, wav, vol, s_off-frames])
            elif s_off > frames: new_voices.append([cur, wav, vol, s_off-frames])
        st["active_voices"] = new_voices; outdata *= self.params["v_master"]
        self.last_sent_pos = ((end_s - st["zero_offset"]) / self.sr) * (self.params["bpm"] / 60.0) - 0.025 * (self.params["bpm"] / 60.0)
        self.queue.put({"type": "vis", "pos": max(-1.0, self.last_sent_pos), "mute": st["is_mute"]})

    def _trigger(self, off):
        st, p = self.state, self.params; tpb = 12 * p["bpb"]
        if st["tick_count"] % tpb == 0:
            if p["rnd"]:
                st["rnd_left"] -= 1
                if st["rnd_left"] <= 0:
                    st["rnd_phase"] = "mute" if st["rnd_phase"] == "play" else "play"
                    if st["rnd_phase"] == "play":
                        st["rnd_left"] = random.randint(p.get("rnd_play_min", 1), p.get("rnd_play_max", 2))
                    else:
                        st["rnd_left"] = random.randint(p.get("rnd_mute_min", 1), p.get("rnd_mute_max", 2))
                st["is_mute"] = (st["rnd_phase"] == "mute")
            else: st["is_mute"] = ((st["tick_count"] // tpb) % (p["play"] + p["mute"])) >= p["play"]

        if p["force_play"]:
            st["is_mute"] = False

        beat, tick, is_m = ((st["tick_count"] % tpb) // 12) + 1, st["tick_count"] % 12, st["is_mute"]
        vol_m = p["v_mute_dim"] if is_m else 1.0

        triggers = []
        if tick == 0:
            # Backbeat (2 & 4) Trigger
            if (beat == 2 or beat == 4) and p["v_backbeat"] > 0:
                if not is_m or self.mute_options.get("backbeat", False):
                    if vol_m > 0: triggers.append((self.waves["backbeat"], p["v_backbeat"]))

            if beat == 1:
                if p["v_acc"] > 0:
                    if not is_m or self.mute_options.get("acc", False):
                        if vol_m > 0: triggers.append((self.waves["acc"], p["v_acc"]))
            else:
                if p["v_4th"] > 0:
                    if not is_m or self.mute_options.get("4th", False):
                        if vol_m > 0: triggers.append((self.waves["4th"], p["v_4th"]))

        if tick == 6 and p["v_8th"] > 0:
            if not is_m or self.mute_options.get("8th", False):
                if vol_m > 0: triggers.append((self.waves["8th"], p["v_8th"]))
        if (tick == 3 or tick == 9) and p["v_16th"] > 0:
            if not is_m or self.mute_options.get("16th", False):
                if vol_m > 0: triggers.append((self.waves["16th"], p["v_16th"]))
        if (tick == 4 or tick == 8) and p["v_trip"] > 0:
            if not is_m or self.mute_options.get("trip", False):
                if vol_m > 0: triggers.append((self.waves["trip"], p["v_trip"]))

        for w, v in triggers: st["active_voices"].append([0, w, v * vol_m, off])

        if tick == 0:
            angle = 30.0 * math.cos(self.last_sent_pos * math.pi)
            self.queue.put({"type": "evt", "ts": time.perf_counter(), "mute": is_m, "beat": beat, "bar": (st["tick_count"] // tpb) + 1, "vis_err": 30.0 - abs(angle)})

# ==========================================
#  UI Components
# ==========================================
class SetlistEditor(QDialog):
    def __init__(self, parent=None, setlist=[], current_idx=0):
        super().__init__(parent)
        self.setWindowTitle("Setlist Editor")
        self.resize(400, 450)
        self.setStyleSheet(SETLIST_STYLE)
        self.setlist = setlist
        self.jump_to_index = -1
        layout = QVBoxLayout(self)
        self.table = QTableWidget(len(setlist), 3)
        self.table.setHorizontalHeaderLabels(["Song Name", "BPM", "Beats"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        for i, s in enumerate(setlist):
            name_item = QTableWidgetItem(s["name"])
            bpm_item = QTableWidgetItem(str(s["bpm"]))
            bpb_item = QTableWidgetItem(str(s["bpb"]))
            if i == 0:
                for item in (name_item, bpm_item, bpb_item):
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                    item.setBackground(QColor("#1a1a1a"))
                    item.setForeground(QColor("#666"))
            if i == current_idx:
                name_item.setText(f"> {s['name']}")
            self.table.setItem(i, 0, name_item)
            self.table.setItem(i, 1, bpm_item)
            self.table.setItem(i, 2, bpb_item)
        layout.addWidget(self.table)
        btn_layout = QGridLayout()
        btn_add = QPushButton("+ Add Song")
        btn_add.clicked.connect(self.add_row)
        btn_del = QPushButton("- Remove Selected")
        btn_del.clicked.connect(self.del_row)
        btn_load = QPushButton("LOAD && CLOSE")
        btn_load.setStyleSheet("background: #007acc; color: white; font-weight: bold;")
        btn_load.clicked.connect(self.load_and_close)
        btn_close = QPushButton("CLOSE")
        btn_close.setStyleSheet("background: #555; color: #ddd; font-weight: bold;")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_add, 0, 0)
        btn_layout.addWidget(btn_del, 0, 1)
        btn_layout.addWidget(btn_load, 1, 0)
        btn_layout.addWidget(btn_close, 1, 1)
        layout.addLayout(btn_layout)

    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(f"New Song {row}"))
        self.table.setItem(row, 1, QTableWidgetItem("120"))
        self.table.setItem(row, 2, QTableWidgetItem("4"))

    def del_row(self):
        idx = self.table.currentRow()
        if idx > 0: self.table.removeRow(idx)

    def load_and_close(self):
        self.jump_to_index = self.table.currentRow()
        self.accept()

    def accept(self):
        self._sync_setlist_to_memory()
        super().accept()

    def _sync_setlist_to_memory(self):
        new_list = []
        for i in range(self.table.rowCount()):
            try:
                name = self.table.item(i, 0).text()
                if name.startswith("> "): name = name[2:]
                new_list.append({"name": name, "bpm": int(self.table.item(i, 1).text()), "bpb": int(self.table.item(i, 2).text())})
            except: continue
        self.setlist[:] = new_list

class MuteOptionsDialog(QDialog):
    def __init__(self, parent=None, mute_opts=None):
        super().__init__(parent)
        self.setWindowTitle("Mute Options - Allow sounds during MUTE bars")
        self.resize(350, 300)
        self.setStyleSheet("""
            QDialog { background: #222; color: #eee; }
            QCheckBox { color: #ffcc00; font-weight: bold; font-size: 13px; padding: 8px; }
            QLabel { color: #ccc; font-size: 12px; }
            QPushButton { background: #007acc; color: white; font-weight: bold; padding: 8px; border-radius: 4px; }
        """)

        self.mute_opts = mute_opts if mute_opts else {
            "acc": False, "backbeat": False, "4th": False,
            "8th": False, "16th": False, "trip": False
        }

        layout = QVBoxLayout(self)

        info_lbl = QLabel("Check sounds to play even during MUTE bars:")
        info_lbl.setStyleSheet("color: #0cf; font-weight: bold; font-size: 11px; margin-bottom: 10px;")
        layout.addWidget(info_lbl)

        # Create checkboxes for each sound type
        self.checkboxes = {}
        sound_labels = [
            ("acc", "Accent (1st beat bell)"),
            ("backbeat", "Backbeat (2 & 4 snare)"),
            ("4th", "4th notes (2, 3, 4 beats)"),
            ("8th", "8th notes"),
            ("16th", "16th notes"),
            ("trip", "Triplets")
        ]

        for key, label in sound_labels:
            chk = QCheckBox(label)
            chk.setChecked(self.mute_opts.get(key, False))
            self.checkboxes[key] = chk
            layout.addWidget(chk)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("background: #555;")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def get_options(self):
        return {key: chk.isChecked() for key, chk in self.checkboxes.items()}

class RandomTrainingOptionsDialog(QDialog):
    def __init__(self, parent=None, params=None):
        super().__init__(parent)
        self.setWindowTitle("Random Training Settings")
        self.resize(300, 250)
        self.setStyleSheet("""
            QDialog { background: #222; color: #eee; }
            QLabel { color: #ccc; font-weight: bold; font-size: 11px; }
            QSpinBox { background: #333; color: #eee; padding: 4px; border-radius: 4px; font-size: 13px; }
            QPushButton { background: #007acc; color: white; font-weight: bold; padding: 8px; border-radius: 4px; }
        """)
        
        self.params = params if params else {}
        layout = QVBoxLayout(self)
        grid = QGridLayout()
        
        grid.addWidget(QLabel("NORMAL (PLAY) BARS:"), 0, 0, 1, 2)
        grid.addWidget(QLabel("Min:"), 1, 0)
        self.sp_p_min = QSpinBox()
        self.sp_p_min.setRange(1, 16)
        self.sp_p_min.setValue(self.params.get("rnd_play_min", 1))
        grid.addWidget(self.sp_p_min, 1, 1)
        
        grid.addWidget(QLabel("Max:"), 2, 0)
        self.sp_p_max = QSpinBox()
        self.sp_p_max.setRange(1, 16)
        self.sp_p_max.setValue(self.params.get("rnd_play_max", 2))
        grid.addWidget(self.sp_p_max, 2, 1)
        
        grid.addWidget(QLabel("MUTE BARS:"), 3, 0, 1, 2)
        grid.addWidget(QLabel("Min:"), 4, 0)
        self.sp_m_min = QSpinBox()
        self.sp_m_min.setRange(1, 16)
        self.sp_m_min.setValue(self.params.get("rnd_mute_min", 1))
        grid.addWidget(self.sp_m_min, 4, 1)
        
        grid.addWidget(QLabel("Max:"), 5, 0)
        self.sp_m_max = QSpinBox()
        self.sp_m_max.setRange(1, 16)
        self.sp_m_max.setValue(self.params.get("rnd_mute_max", 2))
        grid.addWidget(self.sp_m_max, 5, 1)
        
        layout.addLayout(grid)
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.validate_and_accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("background: #555;")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def validate_and_accept(self):
        if self.sp_p_min.value() > self.sp_p_max.value():
            self.sp_p_max.setValue(self.sp_p_min.value())
        if self.sp_m_min.value() > self.sp_m_max.value():
            self.sp_m_max.setValue(self.sp_m_min.value())
        self.accept()

    def get_ranges(self):
        return {
            "rnd_play_min": self.sp_p_min.value(),
            "rnd_play_max": self.sp_p_max.value(),
            "rnd_mute_min": self.sp_m_min.value(),
            "rnd_mute_max": self.sp_m_max.value()
        }

class LogWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("InnerPulse Log")
        self.resize(450, 350)
        self.setStyleSheet("background: #111; color: #0f0; font-family: 'Courier New', monospace;")
        layout = QVBoxLayout(self)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text)
        self.parent_app = parent

    def log(self, msg): self.text.append(msg); self.text.ensureCursorVisible()

    def toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()

class VisualizerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(200)
        self.pos = -1.0
        self.mute = False
        self.bpb = 4
        self.mode = "BAR"
        self.dark_mode = True

    def update_pos(self, pos, mute, bpb):
        self.pos = pos
        self.mute = mute
        self.bpb = bpb
        self.update()

    def reset_pos(self): self.pos = -1.0; self.update()
    def set_mode(self, mode): self.mode = mode; self.update()
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        # Colors & Gradients
        if self.dark_mode:
            bg_inactive = QColor("#2d2d30")
            pen_inactive = QColor("#444")
            arc_col = QColor("#333")
            text_col = QColor("#888")
            active_col = QColor("#007acc")
            mute_col = QColor("#d32f2f")
            glow_alpha = 100
        else:
            bg_inactive = QColor("#e0e0e0")
            pen_inactive = QColor("#ccc")
            arc_col = QColor("#ddd")
            text_col = QColor("#666")
            active_col = QColor("#007acc")
            mute_col = QColor("#f44336")
            glow_alpha = 80

        col = active_col if not self.mute else mute_col
        cx, cy = self.width() / 2, 160
        is_active = self.pos >= 0

        p.setPen(Qt.NoPen)

        if self.mode == "BAR":
            # Draw Arc/Track
            p.setPen(QPen(arc_col, 5, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(int(cx-120), int(cy-120), 240, 240, 60*16, 60*16)
            
            angle = 30 * math.cos(self.pos * math.pi) if is_active else 0
            rad = math.radians(angle - 90)
            x, y = cx + 120 * math.cos(rad), cy + 120 * math.sin(rad)
            
            # Draw Pendulum Line
            if is_active:
                p.setPen(QPen(col, 3, Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(cx, cy), QPointF(x, y))

            # Draw Pivot
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#555"))
            p.drawEllipse(QPointF(cx, cy), 4, 4)

            # Draw Ball (with glow)
            if is_active:
                # Glow
                glow_grad = QRadialGradient(x, y, 30)
                glow_grad.setColorAt(0, QColor(col.red(), col.green(), col.blue(), glow_alpha))
                glow_grad.setColorAt(1, Qt.transparent)
                p.setBrush(glow_grad)
                p.drawEllipse(QPointF(x, y), 30, 30)

                # Solid Core
                p.setBrush(col)
                p.drawEllipse(QPointF(x, y), 12, 12)
            else:
                p.setBrush(bg_inactive)
                p.drawEllipse(QPointF(x, y), 12, 12)

        else:
            # LED Mode: 4 dots
            p.setPen(Qt.NoPen)
            current_beat = int(self.pos) % self.bpb if is_active else -1
            dot_size = 36
            dot_spacing = 60
            start_x = cx - ((dot_spacing * (4-1)) / 2)
            dot_y = 100

            for i in range(4):
                dot_x = start_x + (i * dot_spacing)
                
                if i == current_beat:
                    # Active Glow
                    glow_grad = QRadialGradient(dot_x, dot_y, dot_size)
                    glow_grad.setColorAt(0, QColor(col.red(), col.green(), col.blue(), glow_alpha))
                    glow_grad.setColorAt(1, Qt.transparent)
                    p.setBrush(glow_grad)
                    p.drawEllipse(QPointF(dot_x, dot_y), dot_size*1.5, dot_size*1.5)
                    
                    p.setBrush(col)
                    p.drawEllipse(QPointF(dot_x, dot_y), dot_size/2, dot_size/2)
                else:
                    p.setBrush(bg_inactive)
                    p.drawEllipse(QPointF(dot_x, dot_y), dot_size/3, dot_size/3)

        # Draw Status Text
        p.setFont(QFont("Segoe UI", 32, QFont.Bold))
        txt = ("MUTE" if self.mute else str(int(self.pos) % self.bpb + 1)) if is_active else "STOP"
        
        text_rect = QRect(0, int(cy + 40), int(self.width()), 60)
        p.setPen(col if is_active else text_col)
        p.drawText(text_rect, Qt.AlignCenter, txt)

# ==========================================
#  Main Application
# ==========================================
class InnerPulseQt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.setFixedSize(380, 820)
        self.is_locked = False
        self.setlist = []
        self.setlist_idx = 0
        self.vis_mode = "BAR"
        self.setStyleSheet(MAIN_STYLE)
        self.eng = AudioEngine()
        self.log_win = LogWindow(self)
        self.last_bt = 0
        self.diffs = []

        # Load Config & Setlist
        if getattr(sys, 'frozen', False):
            _macos_dir = os.path.dirname(sys.executable)
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(_macos_dir)))
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        self.config_path = os.path.join(base_path, CONFIG_FILENAME)
        self.json_path = os.path.join(base_path, JSON_FILENAME)
        self.load_config()
        self.load_setlist_from_json()

        central = QWidget()
        self.setCentralWidget(central)
        self.layout = QVBoxLayout(central)
        self.layout.setContentsMargins(10, 5, 10, 10)
        self.layout.setSpacing(4)

        self.setup_audio_ui()
        self.setup_setlist_ui()
        self.setup_visualizer_ui()
        self.setup_controls_ui()
        self.setup_mixer_ui()
        self.setup_footer_ui()

        self.setup_menu_bar()
        self.setup_tool_bar()

        QApplication.instance().installEventFilter(self)
        self.tmr = QTimer()
        self.tmr.timeout.connect(self.poll_queue)
        self.tmr.start(10)

        if "buffer_size" in self.app_config:
            self.eng.buffer_size = int(self.app_config["buffer_size"])

        # Initial Tone set from config
        saved_tone = self.app_config.get("tone", "electronic")
        self.eng.set_tone_mode(saved_tone)
        if hasattr(self, 'btn_tone'):
            self.btn_tone.setText("♪ Wood" if saved_tone == "woody" else "♪ Elec")

        self.change_dev() # Initial boot

    # --- Config Management ---
    def load_config(self):
        self.app_config = {"audio_device": "", "buffer_size": "128", "tone": "electronic"}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.app_config.update(json.load(f))
                    # Apply random training ranges from config to engine if they exist
                    for key in ["rnd_play_min", "rnd_play_max", "rnd_mute_min", "rnd_mute_max"]:
                        if key in self.app_config:
                            self.eng.update(key, int(self.app_config[key]))
            except: pass

    def save_config(self):
        try:
            # Sync random training ranges from engine to config
            for key in ["rnd_play_min", "rnd_play_max", "rnd_mute_min", "rnd_mute_max"]:
                self.app_config[key] = self.eng.params.get(key)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.app_config, f, indent=2)
        except: pass

    # --- UI Helpers ---
    def setup_audio_ui(self):
        cfg_box = QFrame()
        cfg_box.setObjectName("ConfigBox")
        cfg_layout = QVBoxLayout(cfg_box)
        cfg_layout.setContentsMargins(8, 6, 8, 6)
        cfg_layout.setSpacing(4)
        tk_dev_lbl = QLabel("AUDIO DEVICE / BUFFER")
        tk_dev_lbl.setStyleSheet("font-size: 9px; color: #777; font-weight: bold;")

        self.combo_dev = QComboBox()
        saved_dev = self.app_config.get("audio_device", "")
        set_idx = 0
        for i, (idx, name) in enumerate(self.eng.get_filtered_devices()):
            self.combo_dev.addItem(name, idx)
            if name == saved_dev: set_idx = i
        self.combo_dev.setCurrentIndex(set_idx)
        self.combo_dev.currentIndexChanged.connect(self.change_dev)

        self.combo_buf = QComboBox()
        self.combo_buf.addItems(["64", "128", "256", "512"])
        self.combo_buf.setCurrentText(self.app_config.get("buffer_size", "128"))
        self.combo_buf.currentIndexChanged.connect(self.change_buf)

        cfg_row = QHBoxLayout()
        cfg_row.setContentsMargins(0, 0, 0, 0)
        cfg_row.setSpacing(4)
        cfg_row.addWidget(self.combo_dev, 7)
        cfg_row.addWidget(self.combo_buf, 3)
        
        cfg_layout.addWidget(tk_dev_lbl)
        cfg_layout.addLayout(cfg_row)
        self.layout.addWidget(cfg_box)

    def setup_setlist_ui(self):
        sl_box = QFrame()
        sl_box.setObjectName("SetlistBox")
        sl_layout = QVBoxLayout(sl_box)
        sl_layout.setContentsMargins(8, 6, 8, 6)
        sl_layout.setSpacing(4)
        
        top_sl = QHBoxLayout()
        top_sl.setSpacing(4)
        self.btn_prev = QPushButton("<")
        self.btn_prev.setObjectName("NavBtn")
        self.btn_prev.setFixedSize(24, 24)
        self.btn_prev.clicked.connect(self.prev_song)
        self.lbl_song = QLabel("Default")
        self.lbl_song.setAlignment(Qt.AlignCenter)
        self.lbl_song.setStyleSheet("font-weight: bold; color: #0cf; font-size: 13px")
        self.btn_next = QPushButton(">")
        self.btn_next.setObjectName("NavBtn")
        self.btn_next.setFixedSize(24, 24)
        self.btn_next.clicked.connect(self.next_song)
        top_sl.addWidget(self.btn_prev)
        top_sl.addWidget(self.lbl_song)
        top_sl.addWidget(self.btn_next)
        
        self.btn_edit = QPushButton("SETLIST EDITOR (LIST)")
        self.btn_edit.setObjectName("EditBtn")
        self.btn_edit.setFixedHeight(22)
        self.btn_edit.clicked.connect(self.open_editor)
        sl_layout.addLayout(top_sl)
        sl_layout.addWidget(self.btn_edit)
        self.layout.addWidget(sl_box)

    def setup_visualizer_ui(self):
        # Mode and Mute Options buttons in a row
        mode_layout = QHBoxLayout()
        mode_layout.setAlignment(Qt.AlignCenter)
        mode_layout.setSpacing(6)

        self.btn_mode = QPushButton("Mode: BAR")
        self.btn_mode.setObjectName("ModeBtn")
        self.btn_mode.setFixedSize(100, 22)
        self.btn_mode.clicked.connect(self.toggle_mode)

        self.btn_mute_opts = QPushButton("MUTE OPT")
        self.btn_mute_opts.setObjectName("ModeBtn")
        self.btn_mute_opts.setFixedSize(90, 22)
        self.btn_mute_opts.clicked.connect(self.open_mute_options)
        self.btn_mute_opts.setStyleSheet("QPushButton { background: #5c6b8a; color: #dae0ed; font-size: 10px; }")

        self.btn_tone = QPushButton("♪ Elec")
        self.btn_tone.setObjectName("ModeBtn")
        self.btn_tone.setFixedSize(72, 22)
        self.btn_tone.clicked.connect(self.toggle_tone)
        self.btn_tone.setStyleSheet("QPushButton { background: #4a5568; color: #cbd5e0; font-size: 10px; }")

        mode_layout.addWidget(self.btn_mode)
        mode_layout.addWidget(self.btn_mute_opts)
        mode_layout.addWidget(self.btn_tone)
        self.layout.addLayout(mode_layout)

        self.canvas = VisualizerWidget()
        self.layout.addWidget(self.canvas)
        self.lbl_bar = QLabel("Bar: 0")
        self.lbl_bar.setAlignment(Qt.AlignCenter)
        self.lbl_bar.setStyleSheet("font-size: 20px; color: #555; font-weight: bold;")
        self.layout.addWidget(self.lbl_bar)

    def setup_controls_ui(self):
        ctrl_grid = QGridLayout()
        ctrl_grid.setHorizontalSpacing(6)
        ctrl_grid.setVerticalSpacing(4)
        self.sp_bpm_obj = self.create_spin("BPM", 40, 300, 120, "bpm")
        self.sp_bpb_obj = self.create_spin("BEATS", 1, 8, 4, "bpb")
        ctrl_grid.addWidget(self.sp_bpm_obj[0], 0, 0)
        ctrl_grid.addWidget(self.sp_bpm_obj[1], 1, 0)
        ctrl_grid.addWidget(self.sp_bpb_obj[0], 0, 1)
        ctrl_grid.addWidget(self.sp_bpb_obj[1], 1, 1)
        self.sp_play_obj = self.create_spin("PLAY BARS", 1, 16, 3, "play")
        self.sp_mute_obj = self.create_spin("MUTE BARS", 0, 16, 1, "mute")
        ctrl_grid.addWidget(self.sp_play_obj[0], 2, 0)
        ctrl_grid.addWidget(self.sp_play_obj[1], 3, 0)
        ctrl_grid.addWidget(self.sp_mute_obj[0], 2, 1)
        ctrl_grid.addWidget(self.sp_mute_obj[1], 3, 1)
        self.layout.addLayout(ctrl_grid)

        # Checkboxes layout (Random & Mute Off)
        chk_layout = QHBoxLayout()
        chk_layout.setAlignment(Qt.AlignCenter)
        self.chk_rnd = QCheckBox("RANDOM TRAINING (R)")
        self.chk_rnd.stateChanged.connect(self.sync_random_ui)
        self.chk_mute_off = QCheckBox("MUTE OFF (M)")
        self.chk_mute_off.stateChanged.connect(lambda state: self.eng.update("force_play", state == 2))
        chk_layout.addWidget(self.chk_rnd)
        chk_layout.addSpacing(20) # Spacer
        chk_layout.addWidget(self.chk_mute_off)
        self.layout.addLayout(chk_layout)

    def setup_mixer_ui(self):
        self.layout.addSpacing(15)
        mix_layout = QHBoxLayout()
        mix_layout.setSpacing(2)
        controls = [
            ("MST", "v_master", 0.8, "#fff"),
            ("ACC", "v_acc", 0.8, "#fc0"),
            ("BACK", "v_backbeat", 0.0, "#ff66cc"),
            ("4TH", "v_4th", 0.5, "#0cf"),
            ("8TH", "v_8th", 0.0, "#0cf"),
            ("16T", "v_16th", 0.0, "#0cf"),
            ("TRP", "v_trip", 0.0, "#f6c"),
            ("MUTE", "v_mute_dim", 0.0, "#888")
        ]
        for label, k, v, c in controls:
            v_box = QVBoxLayout()
            v_box.setAlignment(Qt.AlignCenter)
            v_box.setSpacing(0)
            sld = QSlider(Qt.Vertical)
            sld.setRange(0, 100)
            sld.setValue(int(v*100))
            sld.setFixedHeight(120)
            sld.setFocusPolicy(Qt.NoFocus)
            sld.valueChanged.connect(lambda val, key=k: self.eng.update(key, val/100.0))
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {c}; font-weight: bold; font-size: 8px;")
            v_box.addWidget(sld)
            v_box.addWidget(lbl)
            mix_layout.addLayout(v_box)
        self.layout.addLayout(mix_layout)

    def setup_footer_ui(self):
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("START")
        self.btn_start.setObjectName("StartBtn")
        self.btn_start.setFixedHeight(45)
        self.btn_start.clicked.connect(self.toggle)
        btn_layout.addWidget(self.btn_start)
        self.layout.addLayout(btn_layout)

    # --- JSON Management ---
    def load_setlist_from_json(self):
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    self.setlist = json.load(f)
            except: self.setlist = []
        else: self.setlist = []
        if not self.setlist or self.setlist[0]["name"] != "Default": self.setlist.insert(0, DEFAULT_SONG)
        self.setlist_idx = 0

    def save_setlist_to_json(self):
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.setlist, f, indent=2, ensure_ascii=False)
        except Exception as e: print(f"Save Error: {e}")

    # --- Logic ---
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and not self.is_locked:
            focus_w = QApplication.focusWidget()

            # セットリストエディタの入力フィールドではホットキーを無効化
            if isinstance(focus_w, (QLineEdit, QTextEdit)):
                return super().eventFilter(obj, event)

            # BPM/BEATS/PLAYBARS/MUTEBARSのSpinBoxでは、ホットキーを有効にする
            # それ以外のSpinBoxでは無効化
            if isinstance(focus_w, QAbstractSpinBox):
                allowed_spinboxes = [
                    self.sp_bpm_obj[1],    # BPM
                    self.sp_bpb_obj[1],    # BEATS
                    self.sp_play_obj[1],   # PLAYBARS
                    self.sp_mute_obj[1]    # MUTEBARS
                ]
                if focus_w not in allowed_spinboxes:
                    return super().eventFilter(obj, event)

            key = event.key()
            if key == Qt.Key_Space:
                self.toggle()
                return True
            elif key == Qt.Key_M:
                self.chk_mute_off.setChecked(not self.chk_mute_off.isChecked())
                return True
            elif key == Qt.Key_L:
                self.log_win.toggle()
                return True
            elif key == Qt.Key_R:
                self.chk_rnd.setChecked(not self.chk_rnd.isChecked())
                return True
            elif key == Qt.Key_Left:
                self.prev_song()
                return True
            elif key == Qt.Key_Right:
                self.next_song()
                return True
        return super().eventFilter(obj, event)

    def setup_tool_bar(self):
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        import_act = QAction("📂 Import JSON", self)
        import_act.triggered.connect(self.import_setlist)
        toolbar.addAction(import_act)

    def setup_menu_bar(self):
        self.log_win.log("[DEBUG] Setting up Menu Bar...")
        menubar = self.menuBar()
        menubar.setNativeMenuBar(True)
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        import_act = QAction("&Import Setlist (JSON)...", self)
        import_act.triggered.connect(self.import_setlist)
        file_menu.addAction(import_act)
        
        # View Menu
        view_menu = menubar.addMenu("&View")
        
        log_act = QAction("Show &Log", self)
        log_act.setShortcut("L")
        log_act.triggered.connect(self.log_win.toggle)
        view_menu.addAction(log_act)

        # Options Menu
        options_menu = menubar.addMenu("&Options")
        rnd_opt_act = QAction("&Random Training Settings...", self)
        rnd_opt_act.triggered.connect(self.open_random_options)
        options_menu.addAction(rnd_opt_act)

    def import_setlist(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Import Setlist JSON", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    new_data = json.load(f)
                
                # Overwrite local setlist.json
                with open(self.json_path, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, indent=2)
                
                # Reload and refresh UI
                self.load_setlist_from_json()
                self.btn_edit.setText(f"SETLIST: {os.path.basename(path)}")
                self.update_song_display()
                self.log_win.log(f"[IMPORT] Loaded {len(self.setlist)} songs from {os.path.basename(path)}")
            except Exception as e:
                self.log_win.log(f"[ERROR] Failed to import: {str(e)}")

    def toggle_mode(self):
        self.vis_mode = "LED" if self.vis_mode == "BAR" else "BAR"
        self.btn_mode.setText(f"Mode: {self.vis_mode}")
        self.canvas.set_mode(self.vis_mode)

    def toggle_tone(self):
        current_mode = self.eng.params.get("tone_mode", "electronic")
        new_mode = "woody" if current_mode == "electronic" else "electronic"
        self.eng.set_tone_mode(new_mode)
        btn_text = "♪ Wood" if new_mode == "woody" else "♪ Elec"
        self.btn_tone.setText(btn_text)
        self.app_config["tone"] = new_mode
        self.save_config()
        self.log_win.log(f"[TONE] Switched to {new_mode.upper()} mode")

    def open_mute_options(self):
        dlg = MuteOptionsDialog(self, self.eng.mute_options)
        if dlg.exec():
            self.eng.mute_options = dlg.get_options()
            self.log_win.log(f"[MUTE OPTIONS] Updated: {self.eng.mute_options}")

    def open_random_options(self):
        dlg = RandomTrainingOptionsDialog(self, self.eng.params)
        if dlg.exec():
            ranges = dlg.get_ranges()
            for k, v in ranges.items():
                self.eng.update(k, v)
            self.save_config()
            self.log_win.log(f"[RND SETTINGS] Play:{ranges['rnd_play_min']}-{ranges['rnd_play_max']} | Mute:{ranges['rnd_mute_min']}-{ranges['rnd_mute_max']}")

    def open_editor(self):
        dlg = SetlistEditor(self, self.setlist, self.setlist_idx)
        if dlg.exec():
            self.save_setlist_to_json()
            if dlg.jump_to_index >= 0:
                if self.eng.is_playing: self.toggle()
                self.setlist_idx = dlg.jump_to_index
                self.apply_song()
            else:
                self.update_song_display()

    def prev_song(self):
        if self.eng.is_playing: self.toggle()
        self.setlist_idx = (self.setlist_idx - 1) % len(self.setlist)
        self.apply_song()

    def next_song(self):
        if self.eng.is_playing: self.toggle()
        self.setlist_idx = (self.setlist_idx + 1) % len(self.setlist)
        self.apply_song()

    def apply_song(self):
        s = self.setlist[self.setlist_idx]
        self.sp_bpm_obj[1].setValue(s["bpm"])
        self.sp_bpb_obj[1].setValue(s["bpb"])
        self.update_song_display()

    def update_song_display(self):
        self.lbl_song.setText(f"{self.setlist_idx+1}. {self.setlist[self.setlist_idx]['name']}")

    def change_dev(self):
        self.is_locked = True
        self.btn_start.setText("WAIT...")
        self.eng.device_index = self.combo_dev.currentData()
        msg = self.eng.boot()
        self.log_win.log(f"[BOOT] {msg}")
        QTimer.singleShot(1500, self.unlock_controls)
        self.app_config["audio_device"] = self.combo_dev.currentText()
        self.save_config()

    def unlock_controls(self):
        self.is_locked = False
        self.btn_start.setText("START")
        self.btn_start.setEnabled(True)

    def change_buf(self):
        self.is_locked = True
        self.btn_start.setText("WAIT...")
        self.eng.buffer_size = int(self.combo_buf.currentText())
        msg = self.eng.boot()
        self.log_win.log(f"[BOOT] {msg}")
        QTimer.singleShot(1000, self.unlock_controls)
        self.app_config["buffer_size"] = self.combo_buf.currentText()
        self.save_config()

    def toggle(self):
        if self.eng.is_playing:
            self.eng.pause()
            self.btn_start.setText("START")
            self.btn_start.setStyleSheet("background: #007acc;")
        else:
            self.canvas.reset_pos()
            self.eng.request_start()
            self.btn_start.setText("STOP")
            self.btn_start.setStyleSheet("background: #c30; border: 1px solid #900;")
            self.last_bt = 0
            self.diffs = []
            self.log_win.log(f"[START] BPM:{self.eng.params['bpm']} Dev:{self.eng.current_device_name} Buf:{self.eng.buffer_size}")

    def create_spin(self, lbl, min_v, max_v, def_v, key):
        l = QLabel(lbl)
        l.setAlignment(Qt.AlignCenter)
        s = QSpinBox()
        s.setRange(min_v, max_v)
        s.setValue(def_v)
        s.valueChanged.connect(lambda v: self.eng.update(key, v))
        return l, s

    def sync_random_ui(self, state):
        is_rnd = (state == 2)
        self.eng.update("rnd", is_rnd)
        self.sp_play_obj[1].setEnabled(not is_rnd)
        self.sp_mute_obj[1].setEnabled(not is_rnd)

    def poll_queue(self):
        while not self.eng.queue.empty():
            d = self.eng.queue.get()
            if d["type"] == "vis": self.canvas.update_pos(d["pos"], d["mute"], self.eng.params["bpb"])
            elif d["type"] == "evt":
                self.lbl_bar.setText(f"Bar: {d['bar']}")
                if self.last_bt > 0:
                    df = (d["ts"] - self.last_bt - (60.0/self.eng.params["bpm"])) * 1000
                    self.diffs.append(df); self.log_win.log(f"[{'MUTE' if d['mute'] else 'PLAY'}] Bar:{d['bar']} Beat:{d['beat']} (Df:{df:+.1f}ms) | Vis:{d['vis_err']:.4f}°")
                self.last_bt = d["ts"]

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    window = InnerPulseQt()
    window.show()
    sys.exit(app.exec())
