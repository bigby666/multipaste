import keyboard
import pyperclip
import pyautogui
import time
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading
import pickle
import os
import queue

# Chemin du fichier de sauvegarde
SAVE_FILE = "multi_clipboard_data.pkl"

# Initialiser la base de données comme une liste avec 10 emplacements
base_donnee = [""] * 10
running = True

# File d'attente pour les communications entre threads
update_queue = queue.Queue()

# Fonction pour charger les données sauvegardées
def charger_donnees():
    global base_donnee
    try:
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'rb') as f:
                base_donnee = pickle.load(f)
                print(f"Données chargées depuis {SAVE_FILE}")
        else:
            print("Aucun fichier de sauvegarde trouvé, utilisation d'une base vide")
    except Exception as e:
        print(f"Erreur lors du chargement des données: {e}")
        base_donnee = [""] * 10

# Fonction pour sauvegarder les données
def sauvegarder_donnees():
    try:
        with open(SAVE_FILE, 'wb') as f:
            pickle.dump(base_donnee, f)
            print(f"Données sauvegardées dans {SAVE_FILE}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des données: {e}")

class SimpleTableViewer:
    def __init__(self, data):
        self.root = tk.Tk()
        self.root.title("Base de Données Multi-Clipboard")
        self.root.geometry("700x500")
        
        # Référence aux données
        self.data = data
        
        # Création du cadre principal
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        ttk.Label(self.main_frame, text="Contenu du Multi-Clipboard", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Création du tableau
        self.create_table()
        
        # Boutons
        buttons_frame = ttk.Frame(self.main_frame)
        buttons_frame.pack(pady=10)
        
        ttk.Button(buttons_frame, text="Actualiser", command=self.refresh_table).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Vider Tout", command=self.clear_base).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Masquer", command=self.hide_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Sauvegarder", command=self.save_data).pack(side=tk.LEFT, padx=5)
        
        # Pour cacher au lieu de fermer
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        # Configure la vérification périodique de la file d'attente
        self.check_queue()
    
    def create_table(self):
        # Cadre pour le tableau avec barre de défilement
        table_frame = ttk.Frame(self.main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Création de la barre de défilement
        scrolly = ttk.Scrollbar(table_frame)
        scrolly.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Création du tableau
        self.table = ttk.Treeview(table_frame, yscrollcommand=scrolly.set)
        self.table.pack(fill=tk.BOTH, expand=True)
        
        # Configuration de la barre de défilement
        scrolly.config(command=self.table.yview)
        
        # Définition des colonnes
        self.table['columns'] = ('information')
        
        # Formatage des colonnes
        self.table.column('#0', width=80, minwidth=50, anchor=tk.W)  # La première colonne pour l'indice
        self.table.column('information', width=600, minwidth=400, anchor=tk.W)
        
        # En-têtes des colonnes
        self.table.heading('#0', text='Emplacement', anchor=tk.W)
        self.table.heading('information', text='Contenu', anchor=tk.W)
        
        # Chargement initial des données
        self.load_data()
    
    def load_data(self):
        # Effacer toutes les données existantes
        for item in self.table.get_children():
            self.table.delete(item)
        
        # Charger les nouvelles données
        for i, texte in enumerate(self.data):
            if texte:
                apercu = texte[:50] + "..." if len(texte) > 50 else texte
                apercu = apercu.replace('\n', ' ').replace('\r', '')
            else:
                apercu = "<vide>"
            
            self.table.insert('', tk.END, text=f"{i+1}", values=(apercu,))
    
    def refresh_table(self):
        self.load_data()
    
    def check_queue(self):
        # Vérifie si des mises à jour sont en attente dans la file
        try:
            while True:
                # Non bloquant pour vider la file rapidement
                task = update_queue.get_nowait()
                if task == "update":
                    self.refresh_table()
                elif task == "clear":
                    self.load_data()  # Après avoir vidé la base
                update_queue.task_done()
        except queue.Empty:
            pass
        
        # Planifie la prochaine vérification
        self.root.after(100, self.check_queue)
    
    def show_window(self):
        # Actualise d'abord les données
        self.refresh_table()
        # Affiche la fenêtre et la met au premier plan
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def hide_window(self):
        # Cache la fenêtre
        self.root.withdraw()
    
    def clear_base(self):
        global base_donnee
        base_donnee = [""] * 10
        print("Base de données vidée")
        self.refresh_table()
        sauvegarder_donnees()  # Sauvegarde après avoir vidé
    
    def save_data(self):
        sauvegarder_donnees()
        messagebox.showinfo("Sauvegarde", "Données sauvegardées avec succès!")
    
    def start(self):
        # Démarre la boucle d'événements tkinter dans le thread principal
        self.root.mainloop()

# Fonction qui permet de clear la base de données
def clear_base():
    global base_donnee
    base_donnee = [""] * 10
    print("Base de données vidée")
    update_queue.put("clear")  # Notification pour mettre à jour l'interface
    sauvegarder_donnees()  # Sauvegarde après avoir vidé

# Fonction commune pour la copie avec gestion d'erreurs renforcée
def try_copy(index):
    try:
        print(f"Tentative de copie à l'emplacement {index+1}...")
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.5)
        for _ in range(3):
            texte_copier = pyperclip.paste()
            if texte_copier:
                base_donnee[index] = texte_copier
                print(f"Copié à l'emplacement {index+1}: {texte_copier[:20]}...")
                update_queue.put("update")  # Notification pour mettre à jour l'interface
                sauvegarder_donnees()  # Sauvegarde après chaque copie
                return
            time.sleep(0.5)
        print(f"Échec de la copie à l'emplacement {index+1}")
    except Exception as e:
        print(f"Erreur lors de la copie à l'emplacement {index+1}: {e}")

# Fonction commune pour le collage avec gestion d'erreurs renforcée
def try_paste(index):
    try:
        print(f"Tentative de collage depuis l'emplacement {index+1}...")
        if base_donnee[index]:
            texte = base_donnee[index]
            pyperclip.copy(texte)
            time.sleep(0.1)
            pyautogui.hotkey("ctrl", "v")
            print(f"Collé depuis l'emplacement {index+1}: {texte[:20]}...")
        else:
            print(f"L'emplacement {index+1} est vide")
    except Exception as e:
        print(f"Erreur lors du collage depuis l'emplacement {index+1}: {e}")

# Fonctions individuelles de copie pour chaque emplacement
def copie1(): try_copy(0)
def copie2(): try_copy(1)
def copie3(): try_copy(2)
def copie4(): try_copy(3)
def copie5(): try_copy(4)
def copie6(): try_copy(5)
def copie7(): try_copy(6)
def copie8(): try_copy(7)
def copie9(): try_copy(8)
def copie0(): try_copy(9)

# Fonctions individuelles de collage pour chaque emplacement
def coller1(): try_paste(0)
def coller2(): try_paste(1)
def coller3(): try_paste(2)
def coller4(): try_paste(3)
def coller5(): try_paste(4)
def coller6(): try_paste(5)
def coller7(): try_paste(6)
def coller8(): try_paste(7)
def coller9(): try_paste(8)
def coller0(): try_paste(9)

# Nouvelle fonction pour afficher la base de données
def afficher_base():
    global table_app
    
    # Afficher également dans la console pour la rétrocompatibilité
    print("Contenu de la base:")
    for i, texte in enumerate(base_donnee):
        if texte:
            apercu = texte[:20] + "..." if len(texte) > 20 else texte
            print(f"  {i+1}: {apercu}")
        else:
            print(f"  {i+1}: <vide>")
    
    # Afficher la fenêtre
    if table_app:
        table_app.root.after(0, table_app.show_window)  # Exécution dans le thread Tkinter

# Fonction pour sauvegarder manuellement
def sauvegarde_manuelle():
    sauvegarder_donnees()
    print("Sauvegarde manuelle effectuée")

# Fonction pour arrêter le programme
def stop_program():
    global running
    running = False
    print("Sauvegarde des données avant arrêt...")
    sauvegarder_donnees()  # Sauvegarde avant de quitter
    print("Arrêt du programme...")
    try:
        keyboard.unhook_all()
    except:
        pass
    print("Programme arrêté.")
    sys.exit(0)

# Fonction de gestion d'erreur globale
def secure_register_hotkey(combo, func, name):
    try:
        keyboard.add_hotkey(combo, func)
        print(f"Raccourci enregistré: {combo} pour {name}")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement du raccourci {combo}: {e}")

# Fonction pour exécuter le programme principal
def run_main_program():
    global running
    
    # Charger les données sauvegardées au démarrage
    charger_donnees()
    
    # Enregistrer les raccourcis clavier
    try:
        # Raccourcis pour copier
        secure_register_hotkey("ctrl+1", copie1, "copie1")
        secure_register_hotkey("ctrl+2", copie2, "copie2")
        secure_register_hotkey("ctrl+3", copie3, "copie3")
        secure_register_hotkey("ctrl+4", copie4, "copie4")
        secure_register_hotkey("ctrl+5", copie5, "copie5")
        secure_register_hotkey("ctrl+6", copie6, "copie6")
        secure_register_hotkey("ctrl+7", copie7, "copie7")
        secure_register_hotkey("ctrl+8", copie8, "copie8")
        secure_register_hotkey("ctrl+9", copie9, "copie9")
        secure_register_hotkey("ctrl+0", copie0, "copie0")

        # Raccourcis pour coller
        secure_register_hotkey("ctrl+shift+1", coller1, "coller1")
        secure_register_hotkey("ctrl+shift+2", coller2, "coller2")
        secure_register_hotkey("ctrl+shift+3", coller3, "coller3")
        secure_register_hotkey("ctrl+shift+4", coller4, "coller4")
        secure_register_hotkey("ctrl+shift+5", coller5, "coller5")
        secure_register_hotkey("ctrl+shift+6", coller6, "coller6")
        secure_register_hotkey("ctrl+shift+7", coller7, "coller7")
        secure_register_hotkey("ctrl+shift+8", coller8, "coller8")
        secure_register_hotkey("ctrl+shift+9", coller9, "coller9")
        secure_register_hotkey("ctrl+shift+$", coller0, "coller0")

        # Autres raccourcis
        secure_register_hotkey("ctrl+alt+b", afficher_base, "afficher_base")
        secure_register_hotkey("ctrl+alt+c", clear_base, "clear_base")
        secure_register_hotkey("ctrl+alt+q", stop_program, "stop_program")
        secure_register_hotkey("ctrl+alt+s", sauvegarde_manuelle, "sauvegarde_manuelle")
    except Exception as e:
        print(f"Erreur lors de l'initialisation des raccourcis: {e}")

    print("\n=== Programme de multi-copier-coller démarré ===")
    print("Utilisez:")
    print("- Ctrl+[1-0] pour copier dans les emplacements 1-10")
    print("- Ctrl+Shift+[1-9,`] pour coller depuis les emplacements 1-10")
    print("- Ctrl+Alt+B pour afficher tous les emplacements")
    print("- Ctrl+Alt+C pour vider tous les emplacements")
    print("- Ctrl+Alt+S pour sauvegarder manuellement")
    print("- Ctrl+Alt+Q pour quitter (sauvegarde automatique)")
    print("================================================\n")

    # Boucle principale avec gestion d'erreurs
    try:
        while running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Interruption clavier détectée.")
        stop_program()
    except Exception as e:
        print(f"Erreur dans la boucle principale: {e}")
        stop_program()

# Initialisation de l'application Tkinter
table_app = SimpleTableViewer(base_donnee)

# Démarre le programme principal dans un thread séparé
# (pour éviter de bloquer l'interface Tkinter)
main_thread = threading.Thread(target=run_main_program)
main_thread.daemon = True
main_thread.start()

# Démarre l'interface Tkinter (doit être dans le thread principal)
table_app.start()