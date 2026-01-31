#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from html.parser import HTMLParser
from collections import Counter
import requests
import threading
import json
import os

API_URL = "https://ebbweb.stadt.bamberg.de/WasteManagementBamberg/WasteManagementServlet"
HISTORY_FILE = "history.json"

class HiddenInputParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._args = {}
    
    @property
    def args(self):
        return self._args
    
    def handle_starttag(self, tag, attrs):
        if tag == "input":
            d = dict(attrs)
            if str(d.get("type", "")).lower() == "hidden":
                self._args[d["name"]] = d.get("value", "")

def get_termine(street, house_number, address_suffix=""):
    session = requests.session()
    
    r = session.get(
        API_URL,
        params={"SubmitAction": "wasteDisposalServices", "InFrameMode": "TRUE"},
    )
    r.raise_for_status()
    r.encoding = "utf-8"
    
    parser = HiddenInputParser()
    parser.feed(r.text)
    args = parser.args
    
    args["Ort"] = street[0].upper()
    args["Strasse"] = street
    args["Hausnummer"] = str(house_number)
    args["Hausnummerzusatz"] = address_suffix
    args["SubmitAction"] = "CITYCHANGED"
    
    r = session.post(API_URL, data=args)
    r.raise_for_status()
    
    args["SubmitAction"] = "forward"
    for i in range(1, 10):
        args[f"ContainerGewaehlt_{i}"] = "on"
    
    r = session.post(API_URL, data=args)
    r.raise_for_status()
    
    args["ApplicationName"] = "com.athos.nl.mvc.abfterm.AbfuhrTerminModel"
    args["SubmitAction"] = "filedownload_ICAL"
    
    r = session.post(API_URL, data=args)
    r.raise_for_status()
    
    termine = []
    current_date = None
    current_date_sort = None
    
    for line in r.text.split('\n'):
        if line.startswith('DTSTART'):
            date = line.split(':')[1]
            current_date = f"{date[6:8]}.{date[4:6]}.{date[0:4]}"
            current_date_sort = date
        elif line.startswith('SUMMARY') and current_date:
            desc = line.split(':')[1].strip()
            termine.append((current_date_sort, current_date, desc))
            current_date = None
            current_date_sort = None
    
    termine.sort(key=lambda x: (x[0], x[2]))
    return [(datum, typ) for _, datum, typ in termine]

class SplashScreen:
    def __init__(self, parent):
        self.splash = tk.Toplevel()
        self.splash.title("Bamberg Abfuhrtermine")
        self.splash.overrideredirect(True)
        
        frame = tk.Frame(self.splash, bg="#2196F3", padx=60, pady=40)
        frame.pack()
        
        title = tk.Label(frame, text="🗑️ Bamberg Abfuhrtermine", 
                        font=("Arial", 24, "bold"), bg="#2196F3", fg="white")
        title.pack(pady=(0, 20))
        
        subtitle = tk.Label(frame, text="Abfuhrkalender für die Stadt Bamberg", 
                           font=("Arial", 12), bg="#2196F3", fg="white")
        subtitle.pack(pady=(0, 30))
        
        loading = tk.Label(frame, text="Wird geladen...", 
                          font=("Arial", 11), bg="#2196F3", fg="white")
        loading.pack(pady=(0, 20))
        
        author = tk.Label(frame, text="Entwickelt von Oliver Schlegel", 
                         font=("Arial", 9), bg="#2196F3", fg="#E3F2FD")
        author.pack()
        
        self.splash.update_idletasks()
        x = (self.splash.winfo_screenwidth() // 2) - (self.splash.winfo_width() // 2)
        y = (self.splash.winfo_screenheight() // 2) - (self.splash.winfo_height() // 2)
        self.splash.geometry(f"+{x}+{y}")
        
        self.splash.after(3000, self.close)
    
    def close(self):
        self.splash.destroy()

class AbfallApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bamberg Abfuhrtermine")
        self.root.geometry("900x650")
        self.history = self.load_history()
        self.current_termine = []
        self.dark_mode = False
        
        # menubar
        menubar = tk.Menu(root)
        root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="📄 Drucken", command=self.drucken)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=root.quit)
        
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ansicht", menu=view_menu)
        view_menu.add_command(label="🌙 Dark Mode", command=self.toggle_dark_mode)
        view_menu.add_command(label="📊 Statistik", command=self.zeige_statistik)
        
        self.build_ui()
    
    def get_colors(self):
        if self.dark_mode:
            return {
                'bg': '#1e1e1e', 'card': '#2d2d2d', 'primary': '#64B5F6',
                'primary_dark': '#42A5F5', 'text': '#e0e0e0', 'text_secondary': '#b0b0b0',
                'header': '#424242', 'status_bg': '#2d2d2d', 'input_bg': '#3d3d3d',
                'list_select': '#1976D2', 'border': '#404040'
            }
        else:
            return {
                'bg': '#fafafa', 'card': 'white', 'primary': '#2196F3',
                'primary_dark': '#1976D2', 'text': '#333', 'text_secondary': '#666',
                'header': '#f5f5f5', 'status_bg': '#f5f5f5', 'input_bg': 'white',
                'list_select': '#E3F2FD', 'border': '#ddd'
            }
    
    def build_ui(self):
        c = self.get_colors()
        
        # clear old widgets
        for widget in self.root.winfo_children():
            if not isinstance(widget, tk.Menu):
                widget.destroy()
        
        main_frame = tk.Frame(self.root, bg=c['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # left panel
        left_panel = tk.Frame(main_frame, bg=c['bg'], width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # input card
        input_card = tk.Frame(left_panel, bg=c['card'], relief='solid', bd=1, highlightbackground=c['border'], highlightthickness=1)
        input_card.pack(fill=tk.X, pady=(0, 15))
        
        title_frame = tk.Frame(input_card, bg=c['primary'], height=45)
        title_frame.pack(fill=tk.X)
        title_label = tk.Label(title_frame, text="🏠 Adresse eingeben", 
                              font=('Segoe UI', 11, 'bold'), 
                              bg=c['primary'], fg='white', anchor='w')
        title_label.pack(side=tk.LEFT, padx=15, pady=10)
        
        fields_frame = tk.Frame(input_card, bg=c['card'], padx=15, pady=15)
        fields_frame.pack(fill=tk.BOTH)
        
        tk.Label(fields_frame, text="Straße", font=('Segoe UI', 9), 
                bg=c['card'], fg=c['text_secondary']).pack(anchor='w', pady=(0, 5))
        self.strasse_entry = tk.Entry(fields_frame, font=('Segoe UI', 10), 
                                      relief='solid', bd=1, bg=c['input_bg'], fg=c['text'])
        self.strasse_entry.pack(fill=tk.X, ipady=6, pady=(0, 15))
        
        tk.Label(fields_frame, text="Hausnummer", font=('Segoe UI', 9), 
                bg=c['card'], fg=c['text_secondary']).pack(anchor='w', pady=(0, 5))
        self.hnr_entry = tk.Entry(fields_frame, font=('Segoe UI', 10), 
                                  relief='solid', bd=1, bg=c['input_bg'], fg=c['text'])
        self.hnr_entry.pack(fill=tk.X, ipady=6, pady=(0, 15))
        
        tk.Label(fields_frame, text="Zusatz (optional)", font=('Segoe UI', 9), 
                bg=c['card'], fg=c['text_secondary']).pack(anchor='w', pady=(0, 5))
        self.zusatz_entry = tk.Entry(fields_frame, font=('Segoe UI', 10), 
                                     relief='solid', bd=1, bg=c['input_bg'], fg=c['text'])
        self.zusatz_entry.pack(fill=tk.X, ipady=6, pady=(0, 15))
        
        self.suchen_btn = tk.Button(fields_frame, text="🔍  Termine abrufen", 
                                    command=self.suchen,
                                    font=('Segoe UI', 10, 'bold'),
                                    bg=c['primary'], fg='white',
                                    relief='flat', cursor='hand2',
                                    padx=20, pady=10)
        self.suchen_btn.pack(fill=tk.X)
        self.suchen_btn.bind('<Enter>', lambda e: self.suchen_btn.config(bg=c['primary_dark']))
        self.suchen_btn.bind('<Leave>', lambda e: self.suchen_btn.config(bg=c['primary']))
        
        # history card
        history_card = tk.Frame(left_panel, bg=c['card'], relief='solid', bd=1, highlightbackground=c['border'], highlightthickness=1)
        history_card.pack(fill=tk.BOTH, expand=True)
        
        history_title_frame = tk.Frame(history_card, bg=c['header'], height=40)
        history_title_frame.pack(fill=tk.X)
        history_title = tk.Label(history_title_frame, text="📋 Letzte Anfragen", 
                                font=('Segoe UI', 10, 'bold'),
                                bg=c['header'], fg=c['text'], anchor='w')
        history_title.pack(side=tk.LEFT, padx=15, pady=10)
        
        history_list_frame = tk.Frame(history_card, bg=c['card'])
        history_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.history_listbox = tk.Listbox(history_list_frame, 
                                         font=('Segoe UI', 9),
                                         relief='flat',
                                         highlightthickness=0,
                                         selectbackground=c['list_select'],
                                         selectforeground=c['primary_dark'],
                                         bg=c['card'], fg=c['text'])
        self.history_listbox.pack(fill=tk.BOTH, expand=True)
        self.history_listbox.bind('<Double-Button-1>', self.load_from_history)
        
        self.update_history_list()
        
        # right panel
        right_panel = tk.Frame(main_frame, bg=c['card'], relief='solid', bd=1, highlightbackground=c['border'], highlightthickness=1)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        result_header = tk.Frame(right_panel, bg=c['header'], height=45)
        result_header.pack(fill=tk.X)
        result_title = tk.Label(result_header, text="📅 Abfuhrtermine", 
                               font=('Segoe UI', 11, 'bold'),
                               bg=c['header'], fg=c['text'], anchor='w')
        result_title.pack(side=tk.LEFT, padx=15, pady=10)
        
        table_frame = tk.Frame(right_panel, bg=c['card'])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Custom.Treeview', 
                       font=('Segoe UI', 9),
                       rowheight=30,
                       background=c['card'],
                       fieldbackground=c['card'],
                       foreground=c['text'])
        style.configure('Custom.Treeview.Heading',
                       font=('Segoe UI', 10, 'bold'),
                       background=c['header'],
                       foreground=c['text'])
        
        self.tree = ttk.Treeview(table_frame, 
                                columns=("datum", "typ"), 
                                show="headings",
                                style='Custom.Treeview')
        self.tree.heading("datum", text="📅 Datum")
        self.tree.heading("typ", text="🗑️ Abfallart")
        self.tree.column("datum", width=120, anchor='center')
        self.tree.column("typ", width=400)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # colors for waste types
        self.tree.tag_configure('restmuell', background='#e0e0e0' if not self.dark_mode else '#424242', foreground='#000' if not self.dark_mode else '#e0e0e0')
        self.tree.tag_configure('biomuell', background='#d7ccc8' if not self.dark_mode else '#5d4037')
        self.tree.tag_configure('papier', background='#e3f2fd' if not self.dark_mode else '#1565c0')
        self.tree.tag_configure('gelb', background='#fff9c4' if not self.dark_mode else '#f9a825')
        
        # status bar
        status_frame = tk.Frame(self.root, bg=c['status_bg'], height=35)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status = tk.Label(status_frame, text="Bereit", 
                              font=('Segoe UI', 9),
                              bg=c['status_bg'], fg=c['text_secondary'],
                              anchor='w')
        self.status.pack(side=tk.LEFT, padx=15, pady=8)
        
        # reload termine if available
        if self.current_termine:
            self.zeige_termine(self.current_termine)
    
    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_history(self):
        with open(HISTORY_FILE, 'w') as f:
            json.dump(self.history[-10:], f)
    
    def update_history_list(self):
        self.history_listbox.delete(0, tk.END)
        for entry in reversed(self.history[-10:]):
            text = f"{entry['strasse']} {entry['hnr']}{entry['zusatz']}"
            self.history_listbox.insert(tk.END, text)
    
    def load_from_history(self, event):
        selection = self.history_listbox.curselection()
        if selection:
            idx = len(self.history) - 1 - selection[0]
            if 0 <= idx < len(self.history):
                entry = self.history[idx]
                self.strasse_entry.delete(0, tk.END)
                self.strasse_entry.insert(0, entry['strasse'])
                self.hnr_entry.delete(0, tk.END)
                self.hnr_entry.insert(0, entry['hnr'])
                self.zusatz_entry.delete(0, tk.END)
                self.zusatz_entry.insert(0, entry['zusatz'])
                self.suchen()
    
    def suchen(self):
        strasse = self.strasse_entry.get().strip()
        hnr = self.hnr_entry.get().strip()
        zusatz = self.zusatz_entry.get().strip()
        
        if not strasse or not hnr:
            messagebox.showerror("Fehler", "Bitte Straße und Hausnummer eingeben")
            return
        
        try:
            hnr_int = int(hnr)
        except ValueError:
            messagebox.showerror("Fehler", "Hausnummer muss eine Zahl sein")
            return
        
        entry = {'strasse': strasse, 'hnr': hnr, 'zusatz': zusatz}
        if entry not in self.history:
            self.history.append(entry)
            self.save_history()
            self.update_history_list()
        
        self.suchen_btn.config(state="disabled")
        self.status.config(text="⏳ Lade Termine...")
        
        def fetch():
            try:
                termine = get_termine(strasse, hnr_int, zusatz)
                self.root.after(0, lambda: self.zeige_termine(termine))
            except Exception as e:
                self.root.after(0, lambda: self.zeige_fehler(str(e)))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def zeige_termine(self, termine):
        self.current_termine = termine
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        letztes_datum = None
        for datum, typ in termine:
            if letztes_datum and letztes_datum != datum:
                self.tree.insert("", tk.END, values=("", ""), tags=('separator',))
            
            tag = ''
            if 'Restmüll' in typ or 'Restmuell' in typ:
                tag = 'restmuell'
            elif 'Bio' in typ:
                tag = 'biomuell'
            elif 'Papier' in typ:
                tag = 'papier'
            elif 'Gelb' in typ:
                tag = 'gelb'
            
            self.tree.insert("", tk.END, values=(datum, typ), tags=(tag,))
            letztes_datum = datum
        
        self.status.config(text=f"✅ {len(termine)} Termine gefunden")
        self.suchen_btn.config(state="normal")
    
    def zeige_fehler(self, fehler):
        messagebox.showerror("Fehler", f"Fehler beim Abrufen:\n{fehler}")
        self.status.config(text="❌ Fehler")
        self.suchen_btn.config(state="normal")
    
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.build_ui()
    
    def drucken(self):
        if not self.current_termine:
            messagebox.showinfo("Drucken", "Keine Termine zum Drucken vorhanden")
            return
        
        # druckvorschau fenster
        print_window = tk.Toplevel(self.root)
        print_window.title("Druckvorschau")
        print_window.geometry("600x700")
        
        text = scrolledtext.ScrolledText(print_window, font=('Courier', 10), wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # format für druck
        text.insert(tk.END, "=" * 60 + "\n")
        text.insert(tk.END, "        BAMBERG ABFUHRTERMINE\n")
        text.insert(tk.END, "=" * 60 + "\n\n")
        
        adresse = f"{self.strasse_entry.get()} {self.hnr_entry.get()}{self.zusatz_entry.get()}"
        text.insert(tk.END, f"Adresse: {adresse}\n")
        text.insert(tk.END, f"Erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n")
        text.insert(tk.END, "-" * 60 + "\n\n")
        
        letztes_datum = None
        for datum, typ in self.current_termine:
            if letztes_datum and letztes_datum != datum:
                text.insert(tk.END, "\n")
            text.insert(tk.END, f"{datum:12} | {typ}\n")
            letztes_datum = datum
        
        text.insert(tk.END, "\n" + "=" * 60 + "\n")
        text.insert(tk.END, "\nEntwickelt von Oliver Schlegel\n")
        
        text.config(state=tk.DISABLED)
        
        btn_frame = tk.Frame(print_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_txt():
            filename = f"abfuhrtermine_{datetime.now().strftime('%Y%m%d')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(text.get(1.0, tk.END))
            messagebox.showinfo("Gespeichert", f"Datei gespeichert als {filename}")
        
        tk.Button(btn_frame, text="Als TXT speichern", command=save_txt).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Schließen", command=print_window.destroy).pack(side=tk.LEFT)
    
    def zeige_statistik(self):
        if not self.current_termine:
            messagebox.showinfo("Statistik", "Keine Termine für Statistik vorhanden")
            return
        
        # statistik fenster
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Statistik")
        stats_window.geometry("500x400")
        
        c = self.get_colors()
        stats_window.configure(bg=c['bg'])
        
        # header
        header = tk.Label(stats_window, text="📊 Abfallstatistik", 
                         font=('Segoe UI', 16, 'bold'),
                         bg=c['bg'], fg=c['text'])
        header.pack(pady=20)
        
        # zähle abfallarten
        typen = [typ for _, typ in self.current_termine]
        counter = Counter(typen)
        
        # frame für statistik
        stats_frame = tk.Frame(stats_window, bg=c['card'], relief='solid', bd=1)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        tk.Label(stats_frame, text="Anzahl Termine pro Abfallart:", 
                font=('Segoe UI', 11, 'bold'),
                bg=c['card'], fg=c['text']).pack(pady=15)
        
        for typ, anzahl in counter.most_common():
            item_frame = tk.Frame(stats_frame, bg=c['card'])
            item_frame.pack(fill=tk.X, padx=20, pady=5)
            
            tk.Label(item_frame, text=typ, font=('Segoe UI', 10),
                    bg=c['card'], fg=c['text'], anchor='w').pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            tk.Label(item_frame, text=f"{anzahl}x", font=('Segoe UI', 10, 'bold'),
                    bg=c['card'], fg=c['primary']).pack(side=tk.RIGHT)
        
        # gesamt
        total_frame = tk.Frame(stats_frame, bg=c['header'], height=50)
        total_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=15, padx=20)
        
        tk.Label(total_frame, text="Gesamt:", font=('Segoe UI', 11, 'bold'),
                bg=c['header'], fg=c['text']).pack(side=tk.LEFT, padx=10)
        
        tk.Label(total_frame, text=f"{len(self.current_termine)} Termine", 
                font=('Segoe UI', 11, 'bold'),
                bg=c['header'], fg=c['primary']).pack(side=tk.RIGHT, padx=10)

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    splash = SplashScreen(root)
    
    def show_main():
        root.deiconify()
        app = AbfallApp(root)
    
    root.after(3000, show_main)
    root.mainloop()
