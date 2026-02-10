import sys, numpy as np, sounddevice as sd, queue, time, math, random, json, os, platform, signal
from PySide6.QtCore import Qt, QTimer, QPointF, QRect, QEvent, QObject
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QGridLayout, QLabel, QComboBox, QPushButton, QSpinBox, 
                             QSlider, QFrame, QCheckBox, QTextEdit, QDialog, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QAbstractItemView)
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QCursor

# ==========================================
#  Constants & Config
# ==========================================
APP_NAME = "InnerPulse"
APP_VERSION = "v1.7.5"
JSON_FILENAME = "setlist.json"
CONFIG_FILENAME = "config.json"
DEFAULT_SONG = {"name": "Default", "bpm": 120, "bpb": 4}

# ★UI復元: 矢印が見えるスタイルに戻しました
MAIN_STYLE = """
    QMainWindow { background-color: #1e1e1e; }
    QLabel { color: #ccc; font-family: 'Helvetica Neue', Helvetica; }
    QFrame#ConfigBox, QFrame#SetlistBox { border: 1px solid #3d3d3d; border-radius: 8px; background: #262626; }
    QComboBox { background: #333; color: white; border: 1px solid #444; padding: 4px; border-radius: 4px; font-size: 11px; }
    QComboBox QAbstractItemView { background-color: #2a2a2a; color: #eee; selection-background-color: #5c6b8a; border: 1px solid #444; }
    
    QSpinBox { background: #111; color: #44ff44; padding: 5px; font-size: 16px; border-radius: 5px; font-weight: bold; border: 1px solid #333; }
    QSpinBox:disabled { color: #444; background: #222; }
    
    /* 矢印ボタンの視認性確保 */
    QSpinBox::up-button, QSpinBox::down-button { background: #333; border: 1px solid #444; border-radius: 2px; width: 20px; subcontrol-origin: border; }
    QSpinBox::up-button { subcontrol-position: top right; }
    QSpinBox::down-button { subcontrol-position: bottom right; }
    QSpinBox::up-button:hover, QSpinBox::down-button:hover { background: #444; }
    QSpinBox::up-button:pressed, QSpinBox::down-button:pressed { background: #555; }
    QSpinBox::up-arrow { width: 0; height: 0; border-left: 4px solid none; border-right: 4px solid none; border-bottom: 5px solid #ccc; }
    QSpinBox::down-arrow { width: 0; height: 0; border-left: 4px solid none; border-right: 4px solid none; border-top: 5px solid #ccc; }

    QPushButton#StartBtn { background: #007acc; color: white; font-size: 18px; font-weight: bold; border-radius: 8px; border: 1px solid #005a9e; }
    QPushButton#StartBtn:disabled { background: #333; color: #666; border: 1px solid #222; }
    QPushButton#ModeBtn, QPushButton#NavBtn { background: #444; color: #eee; border-radius: 6px; font-size: 11px; font-weight: bold; }
    QPushButton#LogBtn, QPushButton#EditBtn { background: #5c6b8a; color: #dae0ed; border-radius: 8px; font-weight: bold; font-size: 11px; }
    QCheckBox { color: #ffcc00; font-weight: bold; font-size: 12px; }
    QSlider::groove:vertical { background: #111; width: 8px; border-radius: 4px; }
    QSlider::handle:vertical { background: #999; height: 16px; margin: 0 -3px; border-radius: 3px; }
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
            "v_master": 0.8, "v_acc": 0.8, "v_4th": 0.5, "v_8th": 0.0, 
            "v_16th": 0.0, "v_trip": 0.0, "v_mute_dim": 0.0, 
            "rnd": False, "force_play": False
        }
        self.state = {"total_samples": 0, "next_tick": 0, "tick_count": 0, "is_mute": False, "active_voices": [], "zero_offset": 0, "rnd_phase": "play", "rnd_left": 3}
        self.queue = queue.Queue()
        self.current_device_name = "None"
        self.last_sent_pos = 0.0

    def update(self, key, val): self.params[key] = val

    def get_filtered_devices(self):
        try:
            devices = sd.query_devices(); hostapis = sd.query_hostapis(); candidates = []; has_high_perf = False
            for i, d in enumerate(devices):
                if d['max_output_channels'] > 0:
                    api_name = hostapis[d['hostapi']]['name']
                    is_good = any(x in api_name for x in ["ASIO", "WASAPI", "Core Audio"])
                    if is_good: has_high_perf = True
                    candidates.append((i, f"{api_name}: {d['name']}", is_good))
            return [c[:2] for c in candidates if not has_high_perf or c[2]]
        except: return []

    def _make_wave(self, type="sine", freq=1000, duration=0.1):
        length = int(self.sr * duration); t = np.linspace(0, duration, length, endpoint=False)
        if type == "bell": wave = (np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 2 * t)) * np.exp(-t * 8) * 0.3
        elif type == "click": wave = np.tanh(np.sin(2 * np.pi * freq * t) * 5) * np.exp(-t * 20) * 0.5
        elif type == "hihat": wave = np.random.uniform(-0.9, 0.9, length) * np.exp(-t * 80) * 0.9
        elif type == "shaker": wave = np.random.uniform(-0.8, 0.8, length) * np.exp(-t * 50) * 0.8
        elif type == "wood": wave = np.sin(np.cumsum(np.linspace(freq, freq/2, length)) / self.sr * 2 * np.pi) * np.exp(-t * 30) * 0.6
        else: wave = np.zeros(length)
        return wave.astype(np.float32)

    def boot(self):
        try:
            if self.stream: self.stream.stop(); self.stream.close()
            dev_info = sd.query_devices(self.device_index, 'output')
            self.sr = int(dev_info.get('default_samplerate', 48000))
            self.current_device_name = dev_info['name']
            self.waves = {"acc": self._make_wave("bell", 2000), "4th": self._make_wave("click", 800), "8th": self._make_wave("hihat"), "16th": self._make_wave("shaker"), "trip": self._make_wave("wood")}
            n_channels = min(2, int(dev_info['max_output_channels'])) 
            self.stream = sd.OutputStream(
                device=self.device_index, channels=n_channels, callback=self._cb, latency='low', 
                blocksize=self.buffer_size, samplerate=self.sr
            )
            self.stream.start(); self.state["total_samples"] = 0
            # ★ログ用にバッファサイズも含めて返す
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
                if st["rnd_left"] <= 0: st["rnd_phase"] = "mute" if st["rnd_phase"] == "play" else "play"; st["rnd_left"] = random.randint(1, 2)
                st["is_mute"] = (st["rnd_phase"] == "mute")
            else: st["is_mute"] = ((st["tick_count"] // tpb) % (p["play"] + p["mute"])) >= p["play"]
        
        if p["force_play"]:
            st["is_mute"] = False

        beat, tick, is_m = ((st["tick_count"] % tpb) // 12) + 1, st["tick_count"] % 12, st["is_mute"]
        vol_m = p["v_mute_dim"] if is_m else 1.0
        
        triggers = []
        if tick == 0:
            if beat == 1:
                if p["v_acc"] > 0 and vol_m > 0: triggers.append((self.waves["acc"], p["v_acc"]))
            else:
                if p["v_4th"] > 0 and vol_m > 0: triggers.append((self.waves["4th"], p["v_4th"]))
        
        if vol_m > 0:
            if tick == 6 and p["v_8th"] > 0: triggers.append((self.waves["8th"], p["v_8th"]))
            if (tick == 3 or tick == 9) and p["v_16th"] > 0: triggers.append((self.waves["16th"], p["v_16th"]))
            if (tick == 4 or tick == 8) and p["v_trip"] > 0: triggers.append((self.waves["trip"], p["v_trip"]))

        for w, v in triggers: st["active_voices"].append([0, w, v * vol_m, off])

        if tick == 0:
            angle = 30.0 * math.cos(self.last_sent_pos * math.pi)
            self.queue.put({"type": "evt", "ts": time.perf_counter(), "mute": is_m, "beat": beat, "bar": (st["tick_count"] // tpb) + 1, "vis_err": 30.0 - abs(angle)})

# ==========================================
#  UI Components
# ==========================================
class SetlistEditor(QDialog):
    def __init__(self, parent=None, setlist=[]):
        super().__init__(parent); self.setWindowTitle("Setlist Editor"); self.resize(400, 450)
        self.setStyleSheet("""
            QDialog { background: #222; color: #eee; }
            QTableWidget { background: #333; gridline-color: #444; }
            QTableWidget::item:selected { background-color: #007acc; color: white; }
            QHeaderView::section { background-color: #444; color: #ddd; border: 1px solid #555; }
        """)
        self.setlist = setlist; self.jump_to_index = -1; layout = QVBoxLayout(self)
        self.table = QTableWidget(len(setlist), 3); self.table.setHorizontalHeaderLabels(["Song Name", "BPM", "Beats"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows); self.table.cellDoubleClicked.connect(self.load_and_close)
        for i, s in enumerate(setlist):
            name_item = QTableWidgetItem(s["name"])
            if i == 0: name_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 0, name_item); self.table.setItem(i, 1, QTableWidgetItem(str(s["bpm"]))); self.table.setItem(i, 2, QTableWidgetItem(str(s["bpb"])))
        layout.addWidget(self.table)
        btn_layout = QGridLayout(); btn_add = QPushButton("+ Add Song"); btn_add.clicked.connect(self.add_row)
        btn_del = QPushButton("- Remove Selected"); btn_del.clicked.connect(self.del_row)
        btn_load = QPushButton("LOAD SELECTED"); btn_load.setStyleSheet("background: #007acc; color: white; font-weight: bold;"); btn_load.clicked.connect(self.load_and_close)
        btn_layout.addWidget(btn_add, 0, 0); btn_layout.addWidget(btn_del, 0, 1); btn_layout.addWidget(btn_load, 1, 0, 1, 2); layout.addLayout(btn_layout)
    def add_row(self):
        row = self.table.rowCount(); self.table.insertRow(row); self.table.setItem(row, 0, QTableWidgetItem(f"New Song {row}")); self.table.setItem(row, 1, QTableWidgetItem("120")); self.table.setItem(row, 2, QTableWidgetItem("4"))
    def del_row(self):
        idx = self.table.currentRow(); 
        if idx > 0: self.table.removeRow(idx)
    def load_and_close(self): self.jump_to_index = self.table.currentRow(); self.accept()
    def accept(self):
        self._sync_setlist_to_memory()
        super().accept()
    def _sync_setlist_to_memory(self):
        new_list = []
        for i in range(self.table.rowCount()):
            try: new_list.append({"name": self.table.item(i, 0).text(), "bpm": int(self.table.item(i, 1).text()), "bpb": int(self.table.item(i, 2).text())})
            except: continue
        self.setlist[:] = new_list

class LogWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(); self.setWindowTitle("InnerPulse Log"); self.resize(450, 350)
        self.setStyleSheet("background: #111; color: #0f0; font-family: 'Courier New', monospace;")
        layout = QVBoxLayout(self); self.text = QTextEdit(); self.text.setReadOnly(True); layout.addWidget(self.text); self.parent_app = parent
    def log(self, msg): self.text.append(msg); self.text.ensureCursorVisible()
    def toggle(self): self.hide() if self.isVisible() else (self.show(), self.raise_())

class VisualizerWidget(QWidget):
    def __init__(self): super().__init__(); self.setMinimumHeight(200); self.pos, self.mute, self.bpb, self.mode = -1.0, False, 4, "BAR"
    def update_pos(self, pos, mute, bpb): self.pos, self.mute, self.bpb = pos, mute, bpb; self.update()
    def reset_pos(self): self.pos = -1.0; self.update()
    def set_mode(self, mode): self.mode = mode; self.update()
    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing); cx = self.width()/2; col = QColor("#44ff44") if not self.mute else QColor("#f44")
        is_active = self.pos >= 0
        if self.mode == "BAR":
            cy = 160; angle = 30 * math.cos(self.pos * math.pi) if is_active else 0
            rad = math.radians(angle - 90); x, y = cx + 120 * math.cos(rad), cy + 120 * math.sin(rad)
            p.setPen(QPen(QColor("#3d3d3d"), 2)); p.drawArc(cx-120, cy-120, 240, 240, 60*16, 60*16)
            p.setPen(QPen(QColor("#555"), 3)); p.drawLine(cx, cy, x, y)
            p.setPen(QPen(col if is_active else QColor("#555"), 4)); p.setBrush(QColor("#222")); p.drawEllipse(QPointF(x, y), 18, 18)
        else:
            if is_active:
                p.setPen(Qt.NoPen); phase = int(self.pos) % 2
                p.setBrush(col if phase == 0 else QColor("#222")); p.drawEllipse(cx-100, 60, 60, 60)
                p.setBrush(col if phase == 1 else QColor("#222")); p.drawEllipse(cx+40, 60, 60, 60)
        p.setPen(col if is_active else QColor("#555")); p.setFont(QFont("Impact", 36))
        txt = ("MUTE" if self.mute else str(int(self.pos) % self.bpb + 1)) if is_active else "STOP"
        p.drawText(self.rect(), Qt.AlignCenter, txt)

# ==========================================
#  Main Application
# ==========================================
class InnerPulseQt(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle(f"{APP_NAME} {APP_VERSION}"); self.setFixedSize(400, 840)
        self.is_locked = False; self.setlist = []; self.setlist_idx = 0; self.vis_mode = "BAR"
        self.setStyleSheet(MAIN_STYLE)
        self.eng = AudioEngine(); self.log_win = LogWindow(self); self.last_bt, self.diffs = 0, []
        
        # Load Config & Setlist
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILENAME)
        self.json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), JSON_FILENAME)
        self.load_config()
        self.load_setlist_from_json()
        
        central = QWidget(); self.setCentralWidget(central)
        self.layout = QVBoxLayout(central); self.layout.setContentsMargins(15, 8, 15, 15); self.layout.setSpacing(8)
        
        self.setup_audio_ui(); self.setup_setlist_ui(); self.setup_visualizer_ui()
        self.setup_controls_ui(); self.setup_mixer_ui(); self.setup_footer_ui()

        QApplication.instance().installEventFilter(self)
        self.tmr = QTimer(); self.tmr.timeout.connect(self.poll_queue); self.tmr.start(10)
        
        # ★初期化の順序バグ修正: ここで強制的に変数を同期させる
        # change_dev() が呼ばれる前に buffer_size を適用しないと初期値128で起動してしまう
        if "buffer_size" in self.app_config:
            self.eng.buffer_size = int(self.app_config["buffer_size"])
        
        self.change_dev() # Initial boot

    # --- Config Management ---
    def load_config(self):
        self.app_config = {"audio_device": "", "buffer_size": "128"}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.app_config.update(json.load(f))
            except: pass

    def save_config(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.app_config, f, indent=2)
        except: pass

    # --- UI Helpers ---
    def setup_audio_ui(self):
        cfg_box = QFrame(); cfg_box.setObjectName("ConfigBox"); cfg_layout = QVBoxLayout(cfg_box)
        tk_dev_lbl = QLabel("AUDIO DEVICE / BUFFER (ASIO/WASAPI優先)")
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
        
        cfg_layout.addWidget(tk_dev_lbl); cfg_layout.addWidget(self.combo_dev); cfg_layout.addWidget(self.combo_buf); self.layout.addWidget(cfg_box)

    def setup_setlist_ui(self):
        sl_box = QFrame(); sl_box.setObjectName("SetlistBox"); sl_layout = QVBoxLayout(sl_box)
        top_sl = QHBoxLayout()
        self.btn_prev = QPushButton("<"); self.btn_prev.setObjectName("NavBtn"); self.btn_prev.setFixedSize(30, 30); self.btn_prev.clicked.connect(self.prev_song)
        self.lbl_song = QLabel("Default"); self.lbl_song.setAlignment(Qt.AlignCenter); self.lbl_song.setStyleSheet("font-weight: bold; color: #0cf; font-size: 14px")
        self.btn_next = QPushButton(">"); self.btn_next.setObjectName("NavBtn"); self.btn_next.setFixedSize(30, 30); self.btn_next.clicked.connect(self.next_song)
        top_sl.addWidget(self.btn_prev); top_sl.addWidget(self.lbl_song); top_sl.addWidget(self.btn_next)
        self.btn_edit = QPushButton("SETLIST EDITOR (LIST)"); self.btn_edit.setObjectName("EditBtn"); self.btn_edit.setFixedHeight(25); self.btn_edit.clicked.connect(self.open_editor)
        sl_layout.addLayout(top_sl); sl_layout.addWidget(self.btn_edit); self.layout.addWidget(sl_box)

    def setup_visualizer_ui(self):
        self.btn_mode = QPushButton("Mode: BAR"); self.btn_mode.setObjectName("ModeBtn"); self.btn_mode.setFixedSize(110, 25); self.btn_mode.clicked.connect(self.toggle_mode)
        self.layout.addWidget(self.btn_mode, 0, Qt.AlignCenter)
        self.canvas = VisualizerWidget(); self.layout.addWidget(self.canvas)
        self.lbl_bar = QLabel("Bar: 0"); self.lbl_bar.setAlignment(Qt.AlignCenter); self.lbl_bar.setStyleSheet("font-size: 20px; color: #555; font-weight: bold;"); self.layout.addWidget(self.lbl_bar)

    def setup_controls_ui(self):
        ctrl_grid = QGridLayout()
        self.sp_bpm_obj = self.create_spin("BPM", 40, 300, 120, "bpm"); self.sp_bpb_obj = self.create_spin("BEATS", 1, 8, 4, "bpb")
        ctrl_grid.addWidget(self.sp_bpm_obj[0], 0, 0); ctrl_grid.addWidget(self.sp_bpm_obj[1], 1, 0); ctrl_grid.addWidget(self.sp_bpb_obj[0], 0, 1); ctrl_grid.addWidget(self.sp_bpb_obj[1], 1, 1)
        self.sp_play_obj = self.create_spin("PLAY BARS", 1, 16, 3, "play"); self.sp_mute_obj = self.create_spin("MUTE BARS", 0, 16, 1, "mute")
        ctrl_grid.addWidget(self.sp_play_obj[0], 2, 0); ctrl_grid.addWidget(self.sp_play_obj[1], 3, 0); ctrl_grid.addWidget(self.sp_mute_obj[0], 2, 1); ctrl_grid.addWidget(self.sp_mute_obj[1], 3, 1)
        self.layout.addLayout(ctrl_grid)
        
        # Checkboxes layout (Random & Mute Off)
        chk_layout = QHBoxLayout()
        chk_layout.setAlignment(Qt.AlignCenter)
        self.chk_rnd = QCheckBox("RANDOM TRAINING (R)"); self.chk_rnd.stateChanged.connect(self.sync_random_ui)
        self.chk_mute_off = QCheckBox("MUTE OFF (M)"); self.chk_mute_off.stateChanged.connect(lambda state: self.eng.update("force_play", state == 2))
        chk_layout.addWidget(self.chk_rnd)
        chk_layout.addSpacing(20) # Spacer
        chk_layout.addWidget(self.chk_mute_off)
        self.layout.addLayout(chk_layout)

    def setup_mixer_ui(self):
        mix_layout = QHBoxLayout()
        for label, k, v, c in [("MST","v_master",0.8,"#fff"), ("ACC","v_acc",0.8,"#fc0"), ("4TH","v_4th",0.5,"#0cf"), ("8TH","v_8th",0.0,"#0cf"), ("16T","v_16th",0.0,"#0cf"), ("TRP","v_trip",0.0,"#f6c"), ("MUTE","v_mute_dim",0.0,"#888")]:
            v_box = QVBoxLayout(); v_box.setAlignment(Qt.AlignCenter); sld = QSlider(Qt.Vertical); sld.setRange(0, 100); sld.setValue(int(v*100)); sld.setFixedHeight(100); sld.setFocusPolicy(Qt.NoFocus); sld.valueChanged.connect(lambda val, key=k: self.eng.update(key, val/100.0))
            lbl = QLabel(label); lbl.setStyleSheet(f"color: {c}; font-weight: bold; font-size: 9px;"); v_box.addWidget(sld); v_box.addWidget(lbl); mix_layout.addLayout(v_box)
        self.layout.addLayout(mix_layout)

    def setup_footer_ui(self):
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("START"); self.btn_start.setObjectName("StartBtn"); self.btn_start.setFixedHeight(60); self.btn_start.clicked.connect(self.toggle)
        self.btn_log = QPushButton("LOG (L)"); self.btn_log.setObjectName("LogBtn"); self.btn_log.setFixedSize(70, 60); self.btn_log.clicked.connect(self.log_win.toggle)
        btn_layout.addWidget(self.btn_start); btn_layout.addWidget(self.btn_log); self.layout.addLayout(btn_layout)

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
            key = event.key()
            if key == Qt.Key_Space: self.toggle(); return True 
            elif key == Qt.Key_M: self.chk_mute_off.setChecked(not self.chk_mute_off.isChecked()); return True # Mute Off Toggle
            elif key == Qt.Key_L: self.log_win.toggle(); return True
            elif key == Qt.Key_R: self.chk_rnd.setChecked(not self.chk_rnd.isChecked()); return True
            elif key == Qt.Key_Left: self.prev_song(); return True
            elif key == Qt.Key_Right: self.next_song(); return True
        return super().eventFilter(obj, event)

    def toggle_mode(self): self.vis_mode = "LED" if self.vis_mode == "BAR" else "BAR"; self.btn_mode.setText(f"Mode: {self.vis_mode}"); self.canvas.set_mode(self.vis_mode)
    
    def open_editor(self):
        dlg = SetlistEditor(self, self.setlist)
        if dlg.exec():
            self.save_setlist_to_json()
            if dlg.jump_to_index >= 0:
                if self.eng.is_playing: self.toggle() 
                self.setlist_idx = dlg.jump_to_index; self.apply_song()
            else: self.update_song_display()

    def prev_song(self):
        if self.eng.is_playing: self.toggle() 
        self.setlist_idx = (self.setlist_idx - 1) % len(self.setlist); self.apply_song()
    def next_song(self):
        if self.eng.is_playing: self.toggle() 
        self.setlist_idx = (self.setlist_idx + 1) % len(self.setlist); self.apply_song()
    def apply_song(self): s = self.setlist[self.setlist_idx]; self.sp_bpm_obj[1].setValue(s["bpm"]); self.sp_bpb_obj[1].setValue(s["bpb"]); self.update_song_display()
    def update_song_display(self): self.lbl_song.setText(f"{self.setlist_idx+1}. {self.setlist[self.setlist_idx]['name']}")
    
    def change_dev(self): 
        self.is_locked=True; self.btn_start.setText("WAIT..."); self.eng.device_index=self.combo_dev.currentData(); msg = self.eng.boot(); self.log_win.log(f"[BOOT] {msg}") # Boot時のログ
        QTimer.singleShot(1500, self.unlock_controls)
        self.app_config["audio_device"] = self.combo_dev.currentText(); self.save_config() # Save on change

    def unlock_controls(self): self.is_locked = False; self.btn_start.setText("START"); self.btn_start.setEnabled(True)
    
    def change_buf(self): 
        self.is_locked=True; self.btn_start.setText("WAIT..."); self.eng.buffer_size=int(self.combo_buf.currentText()); msg = self.eng.boot(); self.log_win.log(f"[BOOT] {msg}")
        QTimer.singleShot(1000, self.unlock_controls)
        self.app_config["buffer_size"] = self.combo_buf.currentText(); self.save_config() # Save on change

    def toggle(self):
        if self.eng.is_playing: self.eng.pause(); self.btn_start.setText("START"); self.btn_start.setStyleSheet("background: #007acc;")
        else: self.canvas.reset_pos(); self.eng.request_start(); self.btn_start.setText("STOP"); self.btn_start.setStyleSheet("background: #c30; border: 1px solid #900;"); self.last_bt, self.diffs = 0, []; self.log_win.log(f"[START] BPM:{self.eng.params['bpm']} Dev:{self.eng.current_device_name} Buf:{self.eng.buffer_size}") # 再生時にもバッファ確認
    def create_spin(self, lbl, min_v, max_v, def_v, key):
        l = QLabel(lbl); l.setAlignment(Qt.AlignCenter); s = QSpinBox(); s.setRange(min_v, max_v); s.setValue(def_v); s.valueChanged.connect(lambda v: self.eng.update(key, v)); return l, s
    def sync_random_ui(self, state): is_rnd = (state == 2); self.eng.update("rnd", is_rnd); self.sp_play_obj[1].setEnabled(not is_rnd); self.sp_mute_obj[1].setEnabled(not is_rnd)
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
    app = QApplication(sys.argv); window = InnerPulseQt(); window.show(); sys.exit(app.exec())