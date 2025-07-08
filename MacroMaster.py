import tkinter as tk
from tkinter import ttk, messagebox, font
import threading, time, random
import pyautogui
import keyboard

class AutoTool(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.master = master
        master.title("MacroMaster")

        # ─── Global Font ─────────────────────────────────────────────────
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(family="Segoe UI", size=10)
        font.nametofont("TkMenuFont").configure(family="Segoe UI", size=10)
        font.nametofont("TkTextFont").configure(family="Segoe UI", size=10)

        # ─── Style & Theme ───────────────────────────────────────────────
        self.style = ttk.Style()
        # Light theme = 'clam' if available, else current
        self.light_theme = 'clam' if 'clam' in self.style.theme_names() else self.style.theme_use()
        self.style.theme_use(self.light_theme)

        # Header
        ttk.Label(self, text="Auto Clicker & Typer",
                  font=('Segoe UI', 18, 'bold')).pack(pady=(0, 10))

        # ─── Menubar ─────────────────────────────────────────────────────
        menubar = tk.Menu(master)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=master.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        master.config(menu=menubar)

        # ─── Notebook ────────────────────────────────────────────────────
        nb = ttk.Notebook(self)
        self.click_tab    = ttk.Frame(nb, padding=10)
        self.type_tab     = ttk.Frame(nb, padding=10)
        self.settings_tab = ttk.Frame(nb, padding=10)
        nb.add(self.click_tab,    text="Clicker")
        nb.add(self.type_tab,     text="Typer")
        nb.add(self.settings_tab, text="Settings")
        nb.pack(fill="both", expand=True)

        # Build tabs
        self._build_clicker_tab()
        self._build_typer_tab()
        self._build_settings_tab()

        # ─── Status Bar ─────────────────────────────────────────────────
        self.status = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status,
                  relief="sunken", anchor="w")\
            .pack(fill="x", pady=(5,0))

        # ─── State & Defaults ────────────────────────────────────────────
        self.clicking     = False
        self.typing       = False
        self.sequencing   = False
        self._click_count = 0
        self._type_count  = 0
        self.sequence_list = []

        # Default panic hotkey
        self.hotkey_panic = 'ctrl+alt+p'
        keyboard.add_hotkey(self.hotkey_panic, self._panic)

        # finalize layout
        self.pack(fill="both", expand=True)

        # initialize UI mode control (light by default)
        self.ui_mode.set('Light')
        self._apply_ui_mode()


    # ──────── Clicker Tab ─────────────────────────────────────────────
    def _build_clicker_tab(self):
        f = self.click_tab

        coord = ttk.LabelFrame(f, text="Position", padding=8)
        coord.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        coord.columnconfigure(1, weight=1)

        ttk.Label(coord, text="X:").grid(row=0, column=0, sticky="e")
        self.click_x = ttk.Spinbox(coord, from_=0, to=10000, width=8)
        self.click_x.set("0"); self.click_x.grid(row=0, column=1, padx=5)
        ttk.Label(coord, text="Y:").grid(row=0, column=2, sticky="e")
        self.click_y = ttk.Spinbox(coord, from_=0, to=10000, width=8)
        self.click_y.set("0"); self.click_y.grid(row=0, column=3, padx=5)
        ttk.Button(coord, text="📍 Pick", command=self._pick_position)\
            .grid(row=0, column=4, padx=5)

        s = ttk.LabelFrame(f, text="Click Settings", padding=8)
        s.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        s.columnconfigure(1, weight=1)

        ttk.Label(s, text="Button:").grid(row=0, column=0, sticky="e")
        self.click_button = ttk.Combobox(
            s, values=['left','right','middle'],
            state='readonly', width=8)
        self.click_button.set('left'); self.click_button.grid(row=0, column=1, padx=5)

        ttk.Label(s, text="Action:").grid(row=0, column=2, sticky="e")
        self.click_action = ttk.Combobox(
            s, values=['single','double','hold'],
            state='readonly', width=8)
        self.click_action.set('single')
        self.click_action.grid(row=0, column=3, padx=5)
        self.click_action.bind('<<ComboboxSelected>>', self._on_click_action_change)

        ttk.Label(s, text="Hold (s):").grid(row=0, column=4, sticky="e")
        self.click_hold = ttk.Spinbox(
            s, from_=0.01, to=10.0, increment=0.01,
            width=8, state='disabled')
        self.click_hold.set("0.5"); self.click_hold.grid(row=0, column=5, padx=5)

        ttk.Label(s, text="Interval (s):").grid(
            row=1, column=0, sticky="e", pady=(5,0))
        self.click_interval = ttk.Spinbox(
            s, from_=0.01, to=10.0,
            increment=0.01, width=8)
        self.click_interval.set("0.5")
        self.click_interval.grid(row=1, column=1, padx=5, pady=(5,0))

        ttk.Label(s, text="Count (0=∞):").grid(
            row=1, column=2, sticky="e", pady=(5,0))
        self.click_count = ttk.Spinbox(
            s, from_=0, to=100000, width=8)
        self.click_count.set("0")
        self.click_count.grid(row=1, column=3, padx=5, pady=(5,0))

        bf = ttk.Frame(f)
        bf.grid(row=2, column=0, sticky="ew", padx=5, pady=10)
        bf.columnconfigure((0,1), weight=1)

        self.btn_start_click = ttk.Button(
            bf, text="▶ Click", command=self.start_clicking)
        self.btn_start_click.grid(row=0, column=0, sticky="ew", padx=5)

        self.btn_stop_click = ttk.Button(
            bf, text="⏹ Stop", command=self.stop_clicking, state="disabled")
        self.btn_stop_click.grid(row=0, column=1, sticky="ew", padx=5)

    def _on_click_action_change(self, _):
        self.click_hold.config(
            state='normal' if self.click_action.get()=='hold' else 'disabled'
        )


    # ──────── Typer Tab ───────────────────────────────────────────────
    def _build_typer_tab(self):
        f = self.type_tab

        # Simple Typer
        simple = ttk.LabelFrame(f, text="Simple Typer", padding=8)
        simple.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        simple.columnconfigure(0, weight=1)

        self.type_text = ttk.Entry(simple)
        self.type_text.insert(0, "Hello, world!")
        self.type_text.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0,5))

        ttk.Label(simple, text="Interval (s):").grid(row=1, column=0, sticky="e")
        self.type_interval = ttk.Spinbox(
            simple, from_=0.01, to=10.0, increment=0.01, width=8)
        self.type_interval.set("1.0"); self.type_interval.grid(row=1, column=1, sticky="w")

        ttk.Label(simple, text="Count (0=∞):").grid(
            row=2, column=0, sticky="e", pady=(5,0))
        self.type_count = ttk.Spinbox(
            simple, from_=0, to=100000, width=8)
        self.type_count.set("0"); self.type_count.grid(row=2, column=1, sticky="w", pady=(5,0))

        bf = ttk.Frame(simple)
        bf.grid(row=3, column=0, columnspan=2, pady=5)
        bf.columnconfigure((0,1), weight=1)
        self.btn_start_type = ttk.Button(bf, text="▶ Type", command=self.start_typing)
        self.btn_start_type.grid(row=0, column=0, sticky="ew", padx=5)
        self.btn_stop_type = ttk.Button(
            bf, text="⏹ Stop", command=self.stop_typing, state="disabled")
        self.btn_stop_type.grid(row=0, column=1, sticky="ew", padx=5)

        # Sequence Typer
        seq = ttk.LabelFrame(f, text="Key Sequence", padding=8)
        seq.grid(row=1, column=0, sticky="ew", padx=5, pady=10)
        seq.columnconfigure(0, weight=1)

        self.seq_tree = ttk.Treeview(
            seq, columns=("Key","Interval"), show="headings", height=5)
        self.seq_tree.heading("Key", text="Key")
        self.seq_tree.heading("Interval", text="Interval (s)")
        self.seq_tree.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0,5))

        ctl = ttk.Frame(seq)
        ctl.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0,5))
        ctl.columnconfigure(1, weight=1); ctl.columnconfigure(3, weight=1)

        ttk.Label(ctl, text="Key:").grid(row=0, column=0, sticky="e")
        self.seq_key = ttk.Entry(ctl, width=12); self.seq_key.grid(row=0, column=1, sticky="w", padx=5)
        ttk.Label(ctl, text="Interval (s):").grid(row=0, column=2, sticky="e")
        self.seq_iv = ttk.Spinbox(ctl, from_=0.01, to=10.0, increment=0.01, width=8)
        self.seq_iv.set("1.0"); self.seq_iv.grid(row=0, column=3, sticky="w", padx=5)

        ttk.Button(ctl, text="➕ Add", command=self._add_sequence_item).grid(row=0, column=4, padx=5)
        ttk.Button(ctl, text="➖ Remove", command=self._remove_sequence_item).grid(row=0, column=5)

        sc = ttk.Frame(seq)
        sc.grid(row=2, column=0, columnspan=3, sticky="ew")
        sc.columnconfigure((1,2), weight=1)

        ttk.Label(sc, text="Repeat (0=∞):").grid(row=0, column=0, sticky="e")
        self.seq_repeat = ttk.Spinbox(sc, from_=0, to=1000, width=8)
        self.seq_repeat.set("1"); self.seq_repeat.grid(row=0, column=1, sticky="w", padx=5)

        self.btn_start_seq = ttk.Button(sc, text="▶ Seq", command=self.start_sequence)
        self.btn_start_seq.grid(row=0, column=2, sticky="ew", padx=5)
        self.btn_stop_seq = ttk.Button(sc, text="⏹ Stop", command=self.stop_sequence, state="disabled")
        self.btn_stop_seq.grid(row=0, column=3, sticky="ew", padx=5)


    # ──────── Settings Tab ────────────────────────────────────────────
    def _build_settings_tab(self):
        f = self.settings_tab

        ap = ttk.LabelFrame(f, text="Appearance Mode", padding=8)
        ap.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        ttk.Label(ap, text="Mode:").grid(row=0, column=0, sticky="e")
        self.ui_mode = tk.StringVar()
        ttk.Radiobutton(ap, text="Light", variable=self.ui_mode, value="Light",
                        command=self._apply_ui_mode).grid(row=0, column=1, padx=5)
        ttk.Radiobutton(ap, text="Dark",  variable=self.ui_mode, value="Dark",
                        command=self._apply_ui_mode).grid(row=0, column=2)

        hm = ttk.LabelFrame(f, text="Humanization", padding=8)
        hm.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        ttk.Label(hm, text="Interval jitter (%):").grid(row=0, column=0, sticky="e")
        self.jitter = ttk.Spinbox(hm, from_=0, to=100, increment=1, width=8); self.jitter.set("0")
        self.jitter.grid(row=0, column=1, padx=5)
        ttk.Label(hm, text="Click radius (px):").grid(row=0, column=2, sticky="e")
        self.radius = ttk.Spinbox(hm, from_=0, to=100, increment=1, width=8); self.radius.set("0")
        self.radius.grid(row=0, column=3, padx=5)

        hk = ttk.LabelFrame(f, text="Hotkeys (global)", padding=8)
        hk.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        hk.columnconfigure(1, weight=1)

        actions = [
            ("Start Click",   self.start_clicking, "hotkey_start_click"),
            ("Stop Click",    self.stop_clicking,  "hotkey_stop_click"),
            ("Start Type",    self.start_typing,   "hotkey_start_type"),
            ("Stop Type",     self.stop_typing,    "hotkey_stop_type"),
            ("Pick Pos",      self._pick_position, "hotkey_pick_pos"),
            ("Start Seq",     self.start_sequence, "hotkey_start_seq"),
            ("Stop Seq",      self.stop_sequence,  "hotkey_stop_seq"),
            ("Panic",         self._panic,         "hotkey_panic"),
        ]
        for i, (lbl, cb, attr) in enumerate(actions):
            ttk.Label(hk, text=f"{lbl}:").grid(row=i, column=0, sticky="e")
            entry = ttk.Entry(hk); entry.grid(row=i, column=1, sticky="ew", padx=5)
            setattr(self, attr + "_entry", entry)
            ttk.Button(hk, text="Set",
                       command=lambda c=cb, e=entry, a=attr: self._bind_hotkey(c, e, a))\
                .grid(row=i, column=2, padx=5)


    def _apply_ui_mode(self):
        if self.ui_mode.get() == "Dark":
            bg, fg = "#2E2E2E", "#E0E0E0"
            lf = "#383838"   # frame backgrounds
            bf = "#303030"   # button/entry background
            af = "#505050"   # active/hover
            s = self.style
            s.theme_use('clam')
            # overall
            s.configure('.', background=bg, foreground=fg)
            # panels & frames
            s.configure('TFrame', background=bg)
            s.configure('TLabelFrame', background=lf, foreground=fg)
            s.configure('TLabelframe.Label', background=bg, foreground=fg)
            # labels
            s.configure('TLabel', background=bg, foreground=fg)
            # entries/spinboxes/comboboxes
            s.configure('TEntry', fieldbackground=bf, foreground=fg)
            s.configure('TSpinbox', fieldbackground=bf, foreground=fg)
            s.configure('TCombobox', fieldbackground=bf, foreground=fg)
            # buttons
            s.configure('TButton', background=bf, foreground=fg, borderwidth=1)
            s.map('TButton',
                  background=[('active', af)],
                  foreground=[('disabled', '#7F7F7F')])
            # notebook tabs
            s.configure('TNotebook', background=bg, borderwidth=0)
            s.configure('TNotebook.Tab',
                        background=bf, foreground=fg, padding=(10,5))
            s.map('TNotebook.Tab',
                  background=[('selected', lf)],
                  foreground=[('selected', fg)])
        else:
            self.style.theme_use(self.light_theme)


    def _bind_hotkey(self, callback, entry, attr):
        self.status.set("Press your hotkey now…")
        def waiter():
            hot = keyboard.read_hotkey(suppress=False)
            prev = getattr(self, attr, None)
            if prev:
                try: keyboard.remove_hotkey(prev)
                except: pass
            setattr(self, attr, hot)
            keyboard.add_hotkey(hot, callback)
            self.master.after(0, lambda: (
                entry.delete(0, tk.END),
                entry.insert(0, hot),
                self.status.set(f"Bound '{hot}'")
            ))
        threading.Thread(target=waiter, daemon=True).start()


    def _panic(self):
        self.master.after(0, self._do_panic)
    def _do_panic(self):
        self.clicking = self.typing = self.sequencing = False
        for btn in (self.btn_start_click, self.btn_start_type, self.btn_start_seq):
            btn.state(["!disabled"])
        for btn in (self.btn_stop_click, self.btn_stop_type, self.btn_stop_seq):
            btn.state(["disabled"])
        self.status.set("‼ PANIC: All stopped ‼")


    def _pick_position(self):
        messagebox.showinfo("Pick Position",
            "After OK:\n1) Move mouse\n2) Press Ctrl+Shift")
        def wait():
            keyboard.wait("ctrl+shift")
            x,y = pyautogui.position()
            self.master.after(0, lambda: self._set_coords(x,y))
        threading.Thread(target=wait, daemon=True).start()

    def _set_coords(self, x, y):
        self.click_x.delete(0, tk.END); self.click_x.insert(0, str(x))
        self.click_y.delete(0, tk.END); self.click_y.insert(0, str(y))
        self.status.set(f"Position picked: ({x}, {y})")


    # ──────── Auto‑Clicker ─────────────────────────────────────────────
    def start_clicking(self):
        try:
            x0 = int(self.click_x.get()); y0 = int(self.click_y.get())
            base_iv = float(self.click_interval.get())
            count   = int(self.click_count.get())
            btn     = self.click_button.get()
            act     = self.click_action.get()
            hold    = float(self.click_hold.get()) if act=='hold' else 0
            jitter  = float(self.jitter.get())/100.0
            radius  = float(self.radius.get())
        except:
            return messagebox.showerror("Invalid", "Check click settings.")
        self.clicking=True; self._click_count=0
        self.btn_start_click.state(["disabled"]); self.btn_stop_click.state(["!disabled"])
        self.status.set("Clicker running…")
        def loop():
            while self.clicking and (count==0 or self._click_count< count):
                dx = random.uniform(-radius, radius)
                dy = random.uniform(-radius, radius)
                x,y = int(x0+dx), int(y0+dy)
                if act=='single':   pyautogui.click(x,y,button=btn)
                elif act=='double': pyautogui.doubleClick(x,y,button=btn)
                else:
                    pyautogui.mouseDown(x,y,button=btn); time.sleep(hold)
                    pyautogui.mouseUp(x,y,button=btn)
                self._click_count+=1
                self.status.set(f"Clicked {self._click_count}")
                iv = base_iv*(1+random.uniform(-jitter,jitter)); time.sleep(iv)
            self.stop_clicking()
        threading.Thread(target=loop, daemon=True).start()

    def stop_clicking(self):
        self.clicking=False
        self.btn_start_click.state(["!disabled"]); self.btn_stop_click.state(["disabled"])
        self.status.set("Clicker stopped")


    # ──────── Simple Typer ─────────────────────────────────────────────
    def start_typing(self):
        text=self.type_text.get()
        try:
            base_iv=float(self.type_interval.get())
            count=int(self.type_count.get())
            jitter=float(self.jitter.get())/100.0
        except:
            return messagebox.showerror("Invalid","Check typing settings.")
        if not text: return messagebox.showerror("Invalid","Enter text.")
        self.typing=True; self._type_count=0
        self.btn_start_type.state(["disabled"]); self.btn_stop_type.state(["!disabled"])
        self.status.set("Typer running…")
        def loop():
            while self.typing and (count==0 or self._type_count< count):
                pyautogui.typewrite(text); pyautogui.press("enter")
                self._type_count+=1
                self.status.set(f"Typed {self._type_count}")
                iv=base_iv*(1+random.uniform(-jitter,jitter)); time.sleep(iv)
            self.stop_typing()
        threading.Thread(target=loop,daemon=True).start()

    def stop_typing(self):
        self.typing=False
        self.btn_start_type.state(["!disabled"]); self.btn_stop_type.state(["disabled"])
        self.status.set("Typer stopped")


    # ──────── Sequence Typer ───────────────────────────────────────────
    def _add_sequence_item(self):
        key=self.seq_key.get().strip()
        try: iv=float(self.seq_iv.get())
        except: return messagebox.showerror("Invalid","Interval must be numeric.")
        if not key: return messagebox.showerror("Invalid","Enter a key.")
        self.sequence_list.append((key,iv))
        self.seq_tree.insert('', 'end', values=(key,iv))

    def _remove_sequence_item(self):
        for item in self.seq_tree.selection():
            vals=self.seq_tree.item(item,'values')
            try: self.sequence_list.remove((vals[0], float(vals[1])))
            except: pass
            self.seq_tree.delete(item)

    def start_sequence(self):
        if not self.sequence_list:
            return messagebox.showerror("Invalid","No sequence defined.")
        try:
            repeat=int(self.seq_repeat.get())
            jitter=float(self.jitter.get())/100.0
        except:
            return messagebox.showerror("Invalid","Repeat must be integer.")
        self.sequencing=True
        self.btn_start_seq.state(["disabled"]); self.btn_stop_seq.state(["!disabled"])
        self.status.set("Sequence running…")
        def loop():
            rounds=repeat if repeat>0 else float('inf')
            r=0
            while self.sequencing and r<rounds:
                for key,iv in self.sequence_list:
                    if not self.sequencing: break
                    pyautogui.press(key)
                    self.status.set(f"Sent '{key}'")
                    t=iv*(1+random.uniform(-jitter,jitter)); time.sleep(t)
                r+=1
            self.stop_sequence()
        threading.Thread(target=loop,daemon=True).start()

    def stop_sequence(self):
        self.sequencing=False
        self.btn_start_seq.state(["!disabled"]); self.btn_stop_seq.state(["disabled"])
        self.status.set("Sequence stopped")


if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(False, False)
    AutoTool(root)
    root.mainloop()
