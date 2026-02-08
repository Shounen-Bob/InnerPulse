import tkinter as tk
from tkinter import ttk
import numpy as np
import sounddevice as sd
import queue
import time
import math
import random

# ==========================================
#  Audio Engine (Random Logic Added)
# ==========================================
class AudioEngine:
    def __init__(self):
        self.stream = None
        self.is_running = False
        self.sr = 48000
        self.waves = {} 
        self.params = {
            "bpm": 120, "beats_per_bar": 4,
            "play_bars": 3, "mute_bars": 2,
            "vol_master": 0.8,
            "vol_acc": 0.8, "vol_4th": 0.0, "vol_8th": 0.0, "vol_16th": 0.0, "vol_trip": 0.0,
            "random_mode": False # ★ New
        }
        self.state = {
            "total_samples": 0, "next_tick_sample": 0, "tick_counter": 0,
            "beat": 0, "bar": 0, "is_mute": False, "active_voices": [],
            "warmup": True, "zero_offset": 0,
            # Random Logic State
            "rnd_phase": "play", # 'play' or 'mute'
            "rnd_bars_left": 0
        }
        self.queue = queue.Queue()

    def update(self, key, val):
        self.params[key] = val

    def _make_wave(self, type="sine", freq=1000, duration=0.1):
        length = int(self.sr * duration)
        t = np.linspace(0, duration, length, endpoint=False)
        if type == "bell": 
            w = np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 2 * t)
            wave = w * np.exp(-t * 8) * 0.3
        elif type == "click": 
            wave = np.tanh(np.sin(2 * np.pi * freq * t) * 5) * np.exp(-t * 20) * 0.5
        elif type == "hihat": 
            wave = np.random.uniform(-0.9, 0.9, length) * np.exp(-t * 80) * 0.9 
        elif type == "shaker": 
            noise = np.random.uniform(-0.8, 0.8, length)
            att = np.linspace(0, 1, int(self.sr * 0.005))
            dec = np.linspace(1, 0, length - len(att))
            wave = noise * np.concatenate([att, dec]) * 0.8
        elif type == "wood": 
            f_sw = np.linspace(freq, freq/2, length)
            ph = np.cumsum(f_sw) / self.sr * 2 * np.pi
            wave = np.sin(ph) * np.exp(-t * 30) * 0.6
        else: wave = np.zeros(length)
        return wave.astype(np.float32)

    def start(self):
        if self.is_running: return "Running"
        try:
            dev = sd.query_devices(kind='output')
            target_sr = 48000
            bs = 512 
            try:
                self.stream = sd.OutputStream(
                    channels=dev['max_output_channels'],
                    callback=self._cb, latency='low', blocksize=bs,
                    samplerate=target_sr
                )
            except Exception:
                self.stream = sd.OutputStream(
                    channels=dev['max_output_channels'],
                    callback=self._cb, latency='high',
                    samplerate=target_sr
                )
            self.stream.start()
            self.sr = int(self.stream.samplerate)
            
            self.waves = {
                "accent": self._make_wave("bell", 2000, 0.15),
                "4th":    self._make_wave("click", 800, 0.08),
                "8th":    self._make_wave("hihat", 0, 0.05),
                "16th":   self._make_wave("shaker", 0, 0.04),
                "trip":   self._make_wave("wood", 1000, 0.06)
            }
            # Initialize State
            self.state = {
                "total_samples": 0, "next_tick_sample": 0, "tick_counter": 0,
                "beat": 0, "bar": 0, "is_mute": False, "active_voices": [], "warmup": True,
                "zero_offset": 0,
                # Random Init: Start with 2 bars PLAY (Fixed)
                "rnd_phase": "play",
                "rnd_bars_left": 2 
            }
            self.is_running = True
            return f"{dev['name']} ({self.sr}Hz)"
        except Exception as e:
            print(e); self.stop(); return str(e)

    def stop(self):
        self.is_running = False
        if self.stream: self.stream.stop(); self.stream.close(); self.stream = None

    def _cb(self, outdata, frames, time_info, status):
        if status:
            try: self.queue.put_nowait({"type": "warn", "msg": str(status)})
            except: pass

        outdata.fill(0)
        st = self.state
        
        if st["warmup"]:
            if st["total_samples"] < self.sr * 0.2:
                st["total_samples"] += frames
                st["next_tick_sample"] = st["total_samples"]
                return
            st["warmup"] = False
            st["zero_offset"] = st["total_samples"]

        start_sample = st["total_samples"]
        end_sample = start_sample + frames
        
        while st["next_tick_sample"] < end_sample:
            offset = int(st["next_tick_sample"] - start_sample)
            if 0 <= offset < frames: self._trigger_tick(offset)
            
            bpm = self.params["bpm"] if self.params["bpm"] > 0 else 120
            samples_per_tick = (self.sr * 60 / bpm) / 12
            st["next_tick_sample"] += samples_per_tick
            st["tick_counter"] += 1

        next_voices = []
        for cursor, wave, vol, start_offset in st["active_voices"]:
            wave_cursor = int(cursor)
            buf_start = int(max(0, start_offset))
            length = min(frames - buf_start, len(wave) - wave_cursor)
            if length > 0:
                outdata[buf_start : buf_start+length] += (wave[wave_cursor : wave_cursor+length] * vol)[:, None]
                if wave_cursor + length < len(wave):
                    next_voices.append([wave_cursor + length, wave, vol, start_offset - frames])
            elif start_offset > frames: 
                next_voices.append([cursor, wave, vol, start_offset - frames])

        st["active_voices"] = next_voices
        outdata *= self.params["vol_master"]
        
        bpm = self.params["bpm"] if self.params["bpm"] > 0 else 120
        musical_sample = end_sample - st["zero_offset"]
        current_beat_pos = (musical_sample / self.sr) * (bpm / 60.0)
        
        try:
            self.queue.put_nowait({
                "type": "vis", "beat_pos": current_beat_pos,
                "mute": st["is_mute"], "bpm": bpm
            })
        except: pass
        
        st["total_samples"] += frames

    def _trigger_tick(self, offset):
        st, p = self.state, self.params
        ticks_per_bar = 12 * p["beats_per_bar"]
        
        # --- Logic for Bar/Phase Switching ---
        if st["tick_counter"] % ticks_per_bar == 0:
            # Bar Start
            if p["random_mode"]:
                # ★ Random Mode Logic
                st["rnd_bars_left"] -= 1
                if st["rnd_bars_left"] <= 0:
                    # Switch Phase
                    if st["rnd_phase"] == "play":
                        st["rnd_phase"] = "mute"
                        st["rnd_bars_left"] = random.randint(1, 2) # Random Mute 1-2
                    else:
                        st["rnd_phase"] = "play"
                        st["rnd_bars_left"] = random.randint(1, 2) # Random Play 1-2
                
                st["is_mute"] = (st["rnd_phase"] == "mute")
            else:
                # ★ Normal Mode Logic (Modulo)
                cycle = p["play_bars"] + p["mute_bars"]
                current_bar_idx = st["tick_counter"] // ticks_per_bar
                st["is_mute"] = (current_bar_idx % cycle) >= p["play_bars"]

        # Calculate musical position for display
        bar_count = (st["tick_counter"] // ticks_per_bar) + 1
        pos_in_bar = st["tick_counter"] % ticks_per_bar
        beat = (pos_in_bar // 12) + 1
        tick = pos_in_bar % 12
        total_beats = st["tick_counter"] // 12
        
        is_mute = st["is_mute"]
        
        voices = []
        if not is_mute:
            if tick == 0:
                if beat == 1 and p["vol_acc"] > 0: voices.append(("accent", p["vol_acc"])) # Beat 1
                elif p["vol_4th"] > 0: voices.append(("4th", p["vol_4th"]))
            if tick == 6 and p["vol_8th"] > 0: voices.append(("8th", p["vol_8th"]))
            if (tick == 3 or tick == 9) and p["vol_16th"] > 0: voices.append(("16th", p["vol_16th"]))
            if (tick == 4 or tick == 8) and p["vol_trip"] > 0: voices.append(("trip", p["vol_trip"]))

        for n, v in voices: st["active_voices"].append([0, self.waves[n], v, offset])
        
        r_type = ""
        vis_diff = 0.0
        
        if tick == 0: 
            r_type = "4th"
            musical_sample = st["next_tick_sample"] - st["zero_offset"]
            exact_beat_pos = (musical_sample / self.sr) * (p["bpm"] / 60.0)
            current_angle = 30.0 * math.cos(exact_beat_pos * math.pi)
            vis_diff = 30.0 - abs(current_angle)
            
        elif tick == 6: r_type = "8th"
        
        if r_type != "":
            try: self.queue.put_nowait({
                "type": "event", "ts": time.perf_counter(), 
                "mute": is_mute, "beat": beat, "bar": bar_count, "tick": tick,
                "bpm": p["bpm"], "r_type": r_type,
                "total_beats": total_beats,
                "vis_diff": vis_diff,
                "rnd_mode": p["random_mode"]
            })
            except: pass

# ==========================================
#  GUI (Random UI + LED Fix)
# ==========================================
class InnerPulseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("InnerPulse (v2.2)")
        self.root.geometry("500x880")
        self.root.configure(bg="#222222")
        self.eng = AudioEngine()
        
        self.vars = {
            "bpm": tk.IntVar(value=120), "bpb": tk.IntVar(value=4),
            "play": tk.IntVar(value=3), "mute": tk.IntVar(value=2),
            "random": tk.BooleanVar(value=False), # ★ New
            "bar": tk.StringVar(value="Bar: 0"), "dev": tk.StringVar(value="Ready")
        }
        self.vis_mode = "BAR"
        self.col = {"bg": "#222222", "fg": "#eeeeee", "on": "#44ff44", "off": "#111111", "dim": "#555", "acc": "#007acc"}
        
        self.last_beat_time = 0
        self.start_time = 0
        self.diff_history = []
        self.log_win = None
        self.log_buffer = []
        
        # References for disabling
        self.spin_play = None
        self.spin_mute = None
        
        self.build_ui()
        self.update_loop()

    def build_ui(self):
        f_t = tk.Frame(self.root, bg=self.col["bg"]); f_t.pack(pady=(10, 0))
        self.btn_mode = tk.Button(f_t, text="Mode: BAR", command=self.toggle_mode, bg="#444", fg="#fff", font=("Helvetica", 10), relief="flat", width=12)
        self.btn_mode.pack()

        self.cv = tk.Canvas(self.root, width=400, height=220, bg=self.col["bg"], bd=0, highlightthickness=0)
        self.cv.pack(pady=10)
        
        cx, cy, l = 200, 180, 150
        self.arc = self.cv.create_arc(cx-l, cy-l, cx+l, cy+l, start=60, extent=60, style="arc", outline="#444", width=3, state='normal')
        self.rod = self.cv.create_line(cx, cy, cx, cy-l, fill="#666", width=4, state='normal')
        self.ball = self.cv.create_oval(cx-20, cy-l-20, cx+20, cy-l+20, fill="#333", outline=self.col["on"], width=4, state='normal')
        
        # ★ LED Position Adjustment (Wider)
        # Old: 50/150, 250/350
        # New: 30/130, 270/370 (More spacing)
        self.dot_l = self.cv.create_oval(30, 60, 130, 160, fill=self.col["off"], outline="#333", width=2, state='hidden')
        self.dot_r = self.cv.create_oval(270, 60, 370, 160, fill=self.col["off"], outline="#333", width=2, state='hidden')
        
        self.txt_beat = self.cv.create_text(200, 110, text="STOP", font=("Impact", 36), fill=self.col["dim"])
        
        f_i = tk.Frame(self.root, bg=self.col["bg"]); f_i.pack(fill="x")
        tk.Label(f_i, textvariable=self.vars["bar"], font=("Helvetica", 16), bg=self.col["bg"], fg="#888").pack()
        tk.Label(f_i, textvariable=self.vars["dev"], font=("Helvetica", 9), bg=self.col["bg"], fg="#666").pack()

        f_c = tk.Frame(self.root, bg=self.col["bg"]); f_c.pack(pady=10, fill="x", padx=20)
        def spin(row, l, v, vmin, vmax, k):
            f = tk.Frame(row, bg=self.col["bg"]); f.pack(side="left", fill="x", expand=True, padx=5)
            tk.Label(f, text=l, bg=self.col["bg"], fg="#ccc", font=("Helvetica", 10)).pack(anchor="w")
            s = tk.Spinbox(f, from_=vmin, to=vmax, textvariable=v, font=("Helvetica", 14), width=5, justify="center")
            s.pack(fill="x")
            v.trace_add("write", lambda *a: self.safe_update(k, v))
            return s

        r1 = tk.Frame(f_c, bg=self.col["bg"]); r1.pack(fill="x", pady=5)
        spin(r1, "BPM", self.vars["bpm"], 40, 300, "bpm")
        spin(r1, "Beats", self.vars["bpb"], 1, 7, "beats_per_bar")
        
        r2 = tk.Frame(f_c, bg=self.col["bg"]); r2.pack(fill="x", pady=5)
        self.spin_play = spin(r2, "Play Bars", self.vars["play"], 1, 8, "play_bars")
        self.spin_mute = spin(r2, "Mute Bars", self.vars["mute"], 1, 8, "mute_bars")

        # ★ Random Checkbutton
        f_rnd = tk.Frame(f_c, bg=self.col["bg"]); f_rnd.pack(fill="x", pady=5)
        tk.Checkbutton(f_rnd, text="Random Training (Play->2, then Random 1-2)", variable=self.vars["random"], 
                       bg=self.col["bg"], fg="orange", selectcolor="#444", font=("Helvetica", 10, "bold"),
                       command=self.toggle_random).pack(side="left", padx=5)

        f_m = tk.LabelFrame(self.root, text="RHYTHM MIX", bg=self.col["bg"], fg="#aaa", font=("Helvetica", 10, "bold"), bd=1, relief="flat")
        f_m.pack(pady=10, padx=20, fill="both", expand=True)
        for lbl, k, val, c in [("MASTER","vol_master",0.8,"#fff"), ("ACC","vol_acc",0.8,"#fc0"), ("4TH","vol_4th",0.0,"#0cf"), 
                               ("8TH","vol_8th",0.0,"#0cf"), ("16TH","vol_16th",0.0,"#0cf"), ("TRIP","vol_trip",0.0,"#f6c")]:
            f = tk.Frame(f_m, bg=self.col["bg"]); f.pack(side="left", fill="y", expand=True, padx=2, pady=5)
            tk.Scale(f, from_=1.0, to=0.0, resolution=0.01, orient="vertical", length=150, bg=self.col["bg"], fg=self.col["bg"], troughcolor="#111", width=20, showvalue=0,
                     command=lambda v, key=k: self.eng.update(key, float(v))).set(val); f.winfo_children()[-1].pack(side="top", pady=5)
            tk.Label(f, text=lbl, bg=self.col["bg"], fg=c, font=("Helvetica", 8, "bold")).pack(side="bottom")

        f_b = tk.Frame(self.root, bg=self.col["bg"]); f_b.pack(pady=20, fill="x", padx=30)
        self.btn_log = tk.Button(f_b, text="LOG", command=self.open_log, bg="#333", fg="#888", font=("Helvetica", 10, "bold"), relief="flat", width=8)
        self.btn_log.pack(side="right", fill="y", padx=(10, 0))
        self.btn = tk.Button(f_b, text="START", command=self.toggle, bg=self.col["acc"], fg="white", font=("Helvetica", 16, "bold"), relief="flat", height=2)
        self.btn.pack(side="left", fill="both", expand=True)

    def toggle_random(self):
        is_rnd = self.vars["random"].get()
        state = "disabled" if is_rnd else "normal"
        self.spin_play.config(state=state)
        self.spin_mute.config(state=state)
        # Update Engine
        self.eng.update("random_mode", is_rnd)
        # If running, restart to apply logic cleanly
        if self.eng.is_running:
            self.toggle() # stop
            self.toggle() # start

    def toggle_mode(self):
        if self.vis_mode == "BAR":
            self.vis_mode = "LED"
            self.btn_mode.config(text="Mode: LED")
            self.cv.itemconfig(self.arc, state='hidden')
            self.cv.itemconfig(self.rod, state='hidden')
            self.cv.itemconfig(self.ball, state='hidden')
            if self.eng.is_running:
                self.cv.itemconfig(self.dot_l, state='normal')
                self.cv.itemconfig(self.dot_r, state='normal')
        else:
            self.vis_mode = "BAR"
            self.btn_mode.config(text="Mode: BAR")
            if self.eng.is_running:
                self.cv.itemconfig(self.arc, state='normal')
                self.cv.itemconfig(self.rod, state='normal')
                self.cv.itemconfig(self.ball, state='normal')
            self.cv.itemconfig(self.dot_l, state='hidden')
            self.cv.itemconfig(self.dot_r, state='hidden')

    def safe_update(self, key, var):
        try:
            val = int(var.get())
            if self.eng.is_running: self.toggle() 
            self.eng.update(key, val)
        except: pass

    def toggle(self):
        if self.eng.is_running:
            self.eng.stop(); self.btn.config(text="START", bg=self.col["acc"])
            self.cv.itemconfig(self.txt_beat, text="STOP", fill=self.col["dim"])
            self.cv.itemconfig(self.dot_l, state='hidden')
            self.cv.itemconfig(self.dot_r, state='hidden')
            self.cv.itemconfig(self.arc, state='hidden')
            self.cv.itemconfig(self.rod, state='hidden')
            self.cv.itemconfig(self.ball, state='hidden')
            
            elapsed = time.time() - self.start_time
            if self.diff_history:
                avg_diff = sum(map(abs, self.diff_history)) / len(self.diff_history)
                max_diff = max(map(abs, self.diff_history))
                self.log_print(f"[SUMMARY] Time: {elapsed:.1f}s | Avg Drift: {avg_diff:.2f}ms | Max Drift: {max_diff:.2f}ms")
                self.log_print("-" * 40)
        else:
            msg = self.eng.start(); self.vars["dev"].set(msg); self.btn.config(text="STOP", bg="#c30")
            
            if self.vis_mode == "BAR":
                self.cv.itemconfig(self.arc, state='normal')
                self.cv.itemconfig(self.rod, state='normal')
                self.cv.itemconfig(self.ball, state='normal')
            else:
                self.cv.itemconfig(self.dot_l, state='normal', fill=self.col["off"])
                self.cv.itemconfig(self.dot_r, state='normal', fill=self.col["off"])

            self.last_beat_time = 0; self.start_time = time.time(); self.diff_history = []
            v = self.vars
            mode_str = "RANDOM" if v["random"].get() else f"Play:{v['play'].get()} Mute:{v['mute'].get()}"
            self.log_print(f"[START] BPM:{v['bpm'].get()} Beats:{v['bpb'].get()} Mode:{mode_str}")

    def open_log(self):
        if self.log_win is not None and tk.Toplevel.winfo_exists(self.log_win):
            self.log_win.lift(); return
        self.log_win = tk.Toplevel(self.root)
        self.log_win.title("InnerPulse Log")
        self.log_win.geometry("550x350")
        self.log_win.configure(bg="#111")
        f = tk.Frame(self.log_win, bg="#111"); f.pack(fill="both", expand=True)
        sb = tk.Scrollbar(f); sb.pack(side="right", fill="y")
        self.log_text = tk.Text(f, bg="#111", fg="#0f0", font=("Consolas", 9), yscrollcommand=sb.set, state="disabled")
        self.log_text.pack(side="left", fill="both", expand=True)
        sb.config(command=self.log_text.yview)
        
        self.log_text.config(state="normal")
        for line in self.log_buffer:
            self.log_text.insert("end", line + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def log_print(self, msg):
        print(msg)
        self.log_buffer.append(msg)
        if self.log_win is not None and tk.Toplevel.winfo_exists(self.log_win):
            self.log_text.config(state="normal")
            self.log_text.insert("end", msg + "\n")
            self.log_text.see("end")
            self.log_text.config(state="disabled")

    def update_loop(self):
        try:
            latest_vis = None
            while True:
                d = self.eng.queue.get_nowait()
                
                if d["type"] == "warn":
                    self.log_print(f"[WARNING] Dropout: {d['msg']}")
                
                elif d["type"] == "event":
                    tick, beat = d["tick"], d["beat"]
                    mute = d["mute"]
                    
                    if tick == 0:
                        self.vars["bar"].set(f"Bar: {d['bar']}")
                        self.cv.itemconfig(self.txt_beat, text="MUTE" if mute else str(beat), fill=self.col["on"] if not mute else "#f44")
                        
                        now = d["ts"]
                        state = "MUTE" if mute else "PLAY"
                        log_line = f"[{state}] Bar:{d['bar']} Beat:{beat}"
                        if self.last_beat_time > 0:
                            interval = now - self.last_beat_time
                            target = 60.0 / d["bpm"]
                            diff = (interval - target) * 1000
                            vis_diff = d.get("vis_diff", 0.0)
                            log_line += f" | Int:{interval:.4f}s (Df:{diff:+.1f}ms) | Vis:{vis_diff:.4f}°"
                            self.diff_history.append(diff)
                        self.last_beat_time = now
                        self.log_print(log_line)
                        
                        if self.vis_mode == "LED":
                            fg = self.col["on"] if not mute else "#f44"
                            bg = self.col["off"]
                            if d["total_beats"] % 2 == 0:
                                self.cv.itemconfig(self.dot_l, fill=fg)
                                self.cv.itemconfig(self.dot_r, fill=bg)
                            else:
                                self.cv.itemconfig(self.dot_l, fill=bg)
                                self.cv.itemconfig(self.dot_r, fill=fg)

                    elif tick == 6 and self.vis_mode == "LED":
                        self.cv.itemconfig(self.dot_l, fill=self.col["off"])
                        self.cv.itemconfig(self.dot_r, fill=self.col["off"])

                elif d["type"] == "vis":
                    latest_vis = d

        except queue.Empty: pass

        if latest_vis and self.vis_mode == "BAR":
            d = latest_vis
            bpm, mute = d["bpm"], d["mute"]
            beat_pos = d["beat_pos"]
            beat_num = int(beat_pos) % self.vars["bpb"].get() + 1
            angle = 30 * math.cos(beat_pos * math.pi)

            col = self.col["on"] if not mute else "#f44"
            if not self.eng.is_running: col = self.col["dim"]
            
            self.cv.itemconfig(self.txt_beat, text="MUTE" if mute else str(beat_num), fill=col)
            self.cv.itemconfig(self.ball, outline=col)
            
            rad = math.radians(angle - 90)
            cx, cy, l = 200, 180, 150
            x, y = cx + l * math.cos(rad), cy + l * math.sin(rad)
            self.cv.coords(self.rod, cx, cy, x, y)
            self.cv.coords(self.ball, x-20, y-20, x+20, y+20)

        self.root.after(10, self.update_loop)

if __name__ == "__main__":
    root = tk.Tk()
    InnerPulseApp(root)
    root.mainloop()