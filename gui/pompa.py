import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import time
import re

class SyringePumpApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Control Pompă de Seringă (Manual + Auto)")
        self.root.geometry("740x670")
        self.root.configure(bg="#1e1e2e")

        self.ser = None
        self.is_connected = False

        self.construieste_interfata()

    def construieste_interfata(self):
        # 1. CONEXIUNE
        frame_conn = tk.LabelFrame(self.root, text=" 1. Conexiune USB ", bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 10, "bold"), padx=10, pady=8)
        frame_conn.pack(fill="x", padx=15, pady=6)

        tk.Label(frame_conn, text="Port:", bg="#1e1e2e", fg="#cdd6f4").pack(side="left", padx=5)
        self.combo_ports = ttk.Combobox(frame_conn, values=self.cauta_porturi(), width=12)
        self.combo_ports.pack(side="left", padx=5)
        if self.combo_ports['values']:
            self.combo_ports.current(0)

        tk.Button(frame_conn, text="Scan", command=self.refresh_porturi, bg="#45475a", fg="white", relief="flat").pack(side="left", padx=5)
        self.btn_conn = tk.Button(frame_conn, text="Conectează", command=self.conectare_arduino, bg="#89b4fa", fg="#11111b", font=("Segoe UI", 9, "bold"), width=12)
        self.btn_conn.pack(side="left", padx=10)

        self.btn_zero = tk.Button(frame_conn, text="📍 Setează Poziția Curentă ca ZERO", command=lambda: self.trimite_comanda("SET_ZERO"), bg="#fab387", fg="#11111b", font=("Segoe UI", 9, "bold"))
        self.btn_zero.pack(side="right", padx=5)

        # 2. CONTROL MANUAL (JOGGING)
        frame_jog = tk.LabelFrame(self.root, text=" 2. Control Manual (Ajustare Piston / Sanie) ", bg="#1e1e2e", fg="#89dceb", font=("Segoe UI", 10, "bold"), padx=10, pady=8)
        frame_jog.pack(fill="x", padx=15, pady=6)

        tk.Label(frame_jog, text="Retrage Pistonul (Înapoi):", bg="#1e1e2e", fg="#cdd6f4").grid(row=0, column=0, padx=5, pady=5)
        tk.Button(frame_jog, text="<< -1000 pași", command=lambda: self.trimite_comanda("JOG:-1000"), bg="#45475a", fg="white", width=12).grid(row=0, column=1, padx=3)
        tk.Button(frame_jog, text="< -200 pași", command=lambda: self.trimite_comanda("JOG:-200"), bg="#45475a", fg="white", width=10).grid(row=0, column=2, padx=3)

        tk.Label(frame_jog, text="Avansează Pistonul (Înainte):", bg="#1e1e2e", fg="#cdd6f4").grid(row=0, column=3, padx=15, pady=5)
        tk.Button(frame_jog, text="+200 pași >", command=lambda: self.trimite_comanda("JOG:200"), bg="#45475a", fg="white", width=10).grid(row=0, column=4, padx=3)
        tk.Button(frame_jog, text="+1000 pași >>", command=lambda: self.trimite_comanda("JOG:1000"), bg="#45475a", fg="white", width=12).grid(row=0, column=5, padx=3)

        # 3. DOZARE AUTOMATA
        frame_ctrl = tk.LabelFrame(self.root, text=" 3. Dozare Automată de Precizie ", bg="#1e1e2e", fg="#a6e3a1", font=("Segoe UI", 10, "bold"), padx=10, pady=8)
        frame_ctrl.pack(fill="x", padx=15, pady=6)

        tk.Label(frame_ctrl, text="Seringă:", bg="#1e1e2e", fg="#cdd6f4").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.combo_seringa = ttk.Combobox(frame_ctrl, values=[
            "0: Hamilton 0.5mL (3.26 mm)",
            "1: Popper 1.0mL (4.50 mm)",
            "2: CarlRoth 1.0mL (6.70 mm)"
        ], width=26, state="readonly")
        self.combo_seringa.current(2)
        self.combo_seringa.grid(row=0, column=1, padx=5, pady=5)
        self.combo_seringa.bind("<<ComboboxSelected>>", self.schimba_seringa)

        tk.Label(frame_ctrl, text="Volum (µL):", bg="#1e1e2e", fg="#cdd6f4").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_vol = tk.Entry(frame_ctrl, width=12, font=("Segoe UI", 10))
        self.entry_vol.insert(0, "10.0")
        self.entry_vol.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        tk.Button(frame_ctrl, text="Injectează Volum", command=self.injecteaza_manual, bg="#a6e3a1", fg="#11111b", font=("Segoe UI", 9, "bold"), width=15).grid(row=1, column=2, padx=10, pady=5)
        tk.Button(frame_ctrl, text="Trage Volum", command=self.extrage_manual, bg="#94e2d5", fg="#11111b", font=("Segoe UI", 9, "bold"), width=12).grid(row=1, column=3, padx=5, pady=5)
        tk.Button(frame_ctrl, text="STOP URGENȚĂ", command=lambda: self.trimite_comanda("STOP"), bg="#f38ba8", fg="#11111b", font=("Segoe UI", 9, "bold"), width=14).grid(row=1, column=4, padx=10, pady=5)

        # 4. ASISTENT PSEUDO-AI
        frame_ai = tk.LabelFrame(self.root, text=" 4. Asistent Inteligent (Comenzi în Limbaj Natural) ", bg="#1e1e2e", fg="#cba6f7", font=("Segoe UI", 10, "bold"), padx=10, pady=8)
        frame_ai.pack(fill="x", padx=15, pady=6)

        self.entry_ai = tk.Entry(frame_ai, font=("Segoe UI", 10), bg="#313244", fg="white", insertbackground="white")
        self.entry_ai.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.entry_ai.insert(0, "Scrie: 'seteaza zero', 'avanseaza 500 pasi', sau 'injecteaza 20 microlitri'")
        self.entry_ai.bind("<FocusIn>", lambda e: self.entry_ai.delete(0, "end") if self.entry_ai.get().startswith("Scrie:") else None)
        self.entry_ai.bind("<Return>", lambda e: self.proceseaza_ai())

        tk.Button(frame_ai, text="Execută AI", command=self.proceseaza_ai, bg="#cba6f7", fg="#11111b", font=("Segoe UI", 9, "bold")).pack(side="right", padx=5)

        # 5. CONSOLA
        frame_log = tk.LabelFrame(self.root, text=" Jurnal Operațiuni ", bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 9), padx=10, pady=5)
        frame_log.pack(fill="both", expand=True, padx=15, pady=6)

        self.log_box = tk.Text(frame_log, bg="#11111b", fg="#a6adc8", font=("Consolas", 9), height=7)
        self.log_box.pack(fill="both", expand=True)

    def log(self, mesaj):
        ora = time.strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{ora}] {mesaj}\n")
        self.log_box.see("end")

    def cauta_porturi(self):
        return [p.device for p in serial.tools.list_ports.comports()]

    def refresh_porturi(self):
        porturi = self.cauta_porturi()
        self.combo_ports['values'] = porturi
        if porturi:
            self.combo_ports.current(0)

    def conectare_arduino(self):
        if not self.is_connected:
            port = self.combo_ports.get()
            if not port:
                messagebox.showerror("Eroare", "Selectează un port COM!")
                return
            try:
                self.ser = serial.Serial(port, 115200, timeout=1)
                self.is_connected = True
                self.btn_conn.config(text="Deconectează", bg="#f38ba8")
                self.log(f"Conectat la {port}. Gata de lucru.")
                threading.Thread(target=self.asculta_arduino, daemon=True).start()
            except Exception as e:
                messagebox.showerror("Eroare", f"Nu m-am putut conecta la {port}.\nÎnchide Serial Monitor din Arduino IDE!\n{e}")
        else:
            self.is_connected = False
            if self.ser:
                self.ser.close()
            self.btn_conn.config(text="Conectează", bg="#89b4fa")
            self.log("Deconectat.")

    def asculta_arduino(self):
        while self.is_connected:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    linie = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if linie:
                        self.root.after(0, self.log, f"Arduino: {linie}")
            except Exception:
                break
            time.sleep(0.02)

    def trimite_comanda(self, cmd):
        if self.is_connected and self.ser:
            self.ser.write((cmd + "\n").encode())
            self.log(f">> {cmd}")
        else:
            self.log("EROARE: Conectează mai întâi placa Arduino!")

    def schimba_seringa(self, event=None):
        self.trimite_comanda(f"SYRINGE:{self.combo_seringa.current()}")

    def injecteaza_manual(self):
        vol = self.entry_vol.get().strip()
        self.trimite_comanda(f"DOSE:{vol}")

    def extrage_manual(self):
        vol = self.entry_vol.get().strip()
        if not vol.startswith("-"):
            vol = "-" + vol
        self.trimite_comanda(f"DOSE:{vol}")

    def proceseaza_ai(self):
        text = self.entry_ai.get().lower().strip()
        self.entry_ai.delete(0, "end")
        if not text:
            return
        self.log(f"Tu: {text}")

        if any(w in text for w in ["zero", "set zero", "calibreaza", "home"]):
            self.log("AI: Salvez poziția curentă ca noul Zero.")
            self.trimite_comanda("SET_ZERO")
            return

        if any(w in text for w in ["stop", "opreste", "frana"]):
            self.log("AI: Trimit oprire de urgență.")
            self.trimite_comanda("STOP")
            return

        # Comenzi de jogging din text: "avanseaza 500 pasi" sau "da inapoi 1000 pasi"
        jog_match = re.search(r"(\d+)\s*pasi", text)
        if jog_match:
            pasi = int(jog_match.group(1))
            if any(w in text for w in ["inapoi", "restrange", "trage", "scade"]):
                pasi = -pasi
            self.log(f"AI: Comand deplasare manuală cu {pasi} pași.")
            self.trimite_comanda(f"JOG:{pasi}")
            return

        # Dozare inteligenta
        dose_match = re.search(r"(\d+(?:\.\d+)?)\s*(ul|microlitri|ml)?", text)
        if dose_match and any(w in text for w in ["injecteaza", "dozeaza", "pune", "trage"]):
            val = float(dose_match.group(1))
            if dose_match.group(2) == "ml":
                val *= 1000.0
            if "trage" in text or "inapoi" in text:
                val = -val
                self.log(f"AI: Trag în seringă {abs(val)} µL.")
            else:
                self.log(f"AI: Dozez automat {val} µL.")
            self.trimite_comanda(f"DOSE:{val}")
            return

        self.log("AI: Nu am înțeles comanda. Încearcă 'seteaza zero', 'avanseaza 500 pasi' sau 'injecteaza 20 microlitri'.")

if __name__ == "__main__":
    root = tk.Tk()
    app = SyringePumpApp(root)
    root.mainloop()