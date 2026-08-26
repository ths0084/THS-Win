import subprocess
import sys
import os
import threading
import json
import re
from functools import partial

# Tentar importar customtkinter, se não existir, avisa o usuário
try:
    import customtkinter as ctk
    from tkinter import messagebox, scrolledtext
except ImportError:
    print("Erro: A biblioteca 'customtkinter' não está instalada.")
    print("Execute: pip install customtkinter")
    sys.exit(1)

# Verificar se está rodando no Windows
import platform
IS_WINDOWS = platform.system() == "Windows"

if not IS_WINDOWS:
    print("AVISO: Este aplicativo foi desenvolvido para Windows 10/11.")
    print("Algumas funcionalidades podem não funcionar corretamente neste sistema.")
    print("A interface gráfica será aberta, mas as instalações via Winget só funcionarão no Windows.")

# Configurações da Interface
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

# ==============================================================================
# BASE DE DADOS DE SOFTWARES
# Formato: { "nome": "ID_Winget_OU_URL", "tipo": "winget" ou "url", "categoria": "free" ou "commercial", "args": "argumentos_silenciosos" }
# Nota: Para URLs, seria necessário implementar o downloader específico. 
# Focaremos primariamente no Winget que cobre 95% da lista e é mais seguro.
# Para os poucos que não tem winget fácil, usaremos placeholders ou comandos específicos.

SOFTWARE_LIST = [
    # Navegadores
    {"name": "Google Chrome", "id": "Google.Chrome", "category": "free"},
    {"name": "Mozilla Firefox", "id": "Mozilla.Firefox", "category": "free"},
    {"name": "Brave", "id": "Brave.Brave", "category": "free"},
    {"name": "Opera", "id": "Opera.Opera", "category": "free"},
    {"name": "Microsoft Edge", "id": "Microsoft.Edge", "category": "free"},
    
    # Mídia e Codecs
    {"name": "VLC Media Player", "id": "VideoLAN.VLC", "category": "free"},
    {"name": "K-Lite Codec Pack", "id": "CodecGuide.KLiteCodecPack.Standard", "category": "free"},
    {"name": "HandBrake", "id": "HandBrake.HandBrake", "category": "free"},
    {"name": "OBS Studio", "id": "OBSProject.OBSStudio", "category": "free"},
    {"name": "Audacity", "id": "Audacity.Audacity", "category": "free"},
    {"name": "Spotify", "id": "Spotify.Spotify", "category": "free"},
    {"name": "iTunes", "id": "Apple.iTunes", "category": "free"},
    
    # Compactadores e Arquivos
    {"name": "7-Zip", "id": "7zip.7zip", "category": "free", "note": "Configurar .rar manualmente após instalação"},
    {"name": "WinRAR", "id": "RARLab.WinRAR", "category": "commercial"}, # Versão Trial
    {"name": "Everything", "id": "Voidtools.Everything", "category": "free"},
    
    # Escritório e PDF
    {"name": "LibreOffice", "id": "TheDocumentFoundation.LibreOffice", "category": "free"},
    {"name": "WPS Office", "id": "Kingsoft.WPSOffice", "category": "free"},
    {"name": "Adobe Acrobat Reader DC", "id": "Adobe.Acrobat.Reader.64-bit", "category": "free"},
    {"name": "Notepad++", "id": "Notepad++.Notepad++", "category": "free"},
    {"name": "Canva", "id": "Canva.Canva", "category": "free"},
    
    # Design e Criação
    {"name": "GIMP", "id": "GIMP.GIMP", "category": "free"},
    {"name": "Inkscape", "id": "Inkscape.Inkscape", "category": "free"},
    {"name": "Blender", "id": "BlenderFoundation.Blender", "category": "free"},
    {"name": "CapCut", "id": "CapCut.CapCut", "category": "free"},
    {"name": "DaVinci Resolve", "id": "BlackmagicDesign.DaVinciResolve", "category": "free"}, # Pode exigir login
    
    # Comunicação
    {"name": "Discord", "id": "Discord.Discord", "category": "free"},
    {"name": "Telegram Desktop", "id": "Telegram.TelegramDesktop", "category": "free"},
    {"name": "WhatsApp Desktop", "id": "WhatsApp.WhatsApp", "category": "free"},
    {"name": "Zoom", "id": "Zoom.Zoom", "category": "free"},
    {"name": "Microsoft Teams", "id": "Microsoft.Teams", "category": "free"},
    {"name": "Skype", "id": "Microsoft.Skype", "category": "free"},
    
    # Jogos e Launchers
    {"name": "Steam", "id": "Valve.Steam", "category": "free"},
    {"name": "Epic Games Launcher", "id": "EpicGames.EpicGamesLauncher", "category": "free"},
    
    # Utilitários de Sistema
    {"name": "PowerToys", "id": "Microsoft.PowerToys", "category": "free"},
    {"name": "Rufus", "id": "Rufus.Rufus", "category": "free"},
    {"name": "BleachBit", "id": "BleachBit.BleachBit", "category": "free"},
    {"name": "Revo Uninstaller Free", "id": "RevoUninstaller.RevoUninstallerFree", "category": "free"},
    {"name": "VirtualBox", "id": "Oracle.VirtualBox", "category": "free"},
    {"name": "Java (Oracle JDK)", "id": "Oracle.JavaRuntimeEnvironment", "category": "free"}, # Ou OpenJDK
    {"name": "Git", "id": "Git.Git", "category": "free"},
    {"name": "Visual Studio Code", "id": "Microsoft.VisualStudioCode", "category": "free"},
    {"name": "ShareX", "id": "ShareX.ShareX", "category": "free"},
    {"name": "FileZilla Client", "id": "FileZilla.Client", "category": "free"},
    {"name": "qBittorrent", "id": "qBittorrent.qBittorrent", "category": "free"},
    {"name": "Lively Wallpaper", "id": "rocksdanister.LivelyWallpaper", "category": "free"},
    
    # Segurança e Rede
    {"name": "Avast Free Antivirus", "id": "AVAST.Software.Avast", "category": "free"},
    {"name": "AVG AntiVirus Free", "id": "AVG.AVGAntiVirusFREE", "category": "free"},
    {"name": "Malwarebytes", "id": "Malwarebytes.Malwarebytes", "category": "free"},
    {"name": "ProtonVPN", "id": "ProtonTechnologies.ProtonVPN", "category": "free"},
    {"name": "Tor Browser", "id": "TorProject.TorBrowser", "category": "free"},
    {"name": "Radmin VPN", "id": "Radmin.VPN", "category": "free"}, # Verificar ID no winget, as vezes não está
    
    # Nuvem
    {"name": "Google Drive Desktop", "id": "Google.GoogleDrive", "category": "free"},
    {"name": "OneDrive", "id": "Microsoft.OneDrive", "category": "free"}, # Geralmente já vem no Windows
    
    # Acesso Remoto
    {"name": "RustDesk", "id": "RustDesk.RustDesk", "category": "free"},
    {"name": "AnyDesk", "id": "AnyDeskSoftwareGmbH.AnyDesk", "category": "free"},
    {"name": "TeamViewer", "id": "TeamViewer.TeamViewer", "category": "free"},

    # Específicos Brasil / Gov (Podem não estar no Winget, requerem tratamento especial)
    # Se não estiverem no winget, o script avisará que precisa de instalação manual ou URL
    {"name": "PJE (Instalador Manual)", "id": None, "category": "free", "note": "Baixar do site do TST manualmente"},
    {"name": "Assinador Livre", "id": None, "category": "free", "note": "Baixar do site oficial manualmente"},
]

class AutoElevate:
    """Classe para lidar com elevação de privilégios UAC"""
    @staticmethod
    def is_admin():
        try:
            return os.getuid() == 0
        except AttributeError:
            import ctypes
            try:
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except:
                return False

    @staticmethod
    def run_as_admin():
        if not AutoElevate.is_admin():
            import ctypes
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            except Exception as e:
                messagebox.showerror("Erro de Privilégio", f"Não foi possível obter permissão de administrador.\nErro: {e}\nO programa pode falhar ao instalar softwares.")
                return False
            sys.exit(0)
        return True

class InstallerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuração da Janela
        self.title("Instalador Automático de Softwares")
        self.geometry("1000x700")
        self.minsize(800, 600)
        
        # Variáveis de Estado
        self.checkboxes = {}
        self.categories = ["free", "commercial"]
        self.install_thread = None
        self.stop_flag = False

        # Layout Principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar (Menu Lateral)
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="INSTALLER\nPRO", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.btn_select_all = ctk.CTkButton(self.sidebar_frame, text="Selecionar Tudo", command=self.select_all)
        self.btn_select_all.grid(row=1, column=0, padx=20, pady=10)

        self.btn_deselect_all = ctk.CTkButton(self.sidebar_frame, text="Desmarcar Tudo", command=self.deselect_all, fg_color="gray")
        self.btn_deselect_all.grid(row=2, column=0, padx=20, pady=10)

        self.btn_start = ctk.CTkButton(self.sidebar_frame, text="INICIAR INSTALAÇÃO", height=50, font=ctk.CTkFont(size=14, weight="bold"), command=self.start_installation)
        self.btn_start.grid(row=3, column=0, padx=20, pady=20)

        # Área de Conteúdo (Scrollable)
        self.scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Selecione os Softwares")
        self.scrollable_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.scrollable_frame.grid_columnconfigure((0, 1), weight=1)

        # Renderizar Checkboxes
        self.render_checkboxes()

        # Área de Log (Inferior)
        self.log_frame = ctk.CTkFrame(self, height=150, corner_radius=10)
        self.log_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 20))
        self.log_frame.grid_propagate(False)
        
        self.log_label = ctk.CTkLabel(self.log_frame, text="Log de Instalação:", anchor="w")
        self.log_label.pack(fill="x", padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=6, bg="#2b2b2b", fg="white", font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_text.config(state='disabled')

    def render_checkboxes(self):
        row = 0
        col = 0
        for idx, app in enumerate(SOFTWARE_LIST):
            cat_color = "#2CC985" if app['category'] == 'free' else "#FF5D5D" # Verde para free, Vermelho para commercial
            cat_text = "GRÁTIS" if app['category'] == 'free' else "COMERCIAL/TRIAL"
            
            frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
            frame.grid(row=row, column=col, sticky="w", padx=10, pady=5)
            
            cb = ctk.CTkCheckBox(frame, text=f"{app['name']} ({cat_text})", variable=ctk.StringVar(value="off"))
            cb.pack(side="left")
            
            # Tag visual de categoria
            lbl_cat = ctk.CTkLabel(frame, text=cat_text, text_color=cat_color, font=ctk.CTkFont(size=10, weight="bold"))
            lbl_cat.pack(side="right", padx=10)
            
            self.checkboxes[app['name']] = {
                "checkbox": cb,
                "data": app,
                "status_var": cb.cget('variable')
            }

            col += 1
            if col > 1:
                col = 0
                row += 1

    def select_all(self):
        for item in self.checkboxes.values():
            item["checkbox"].select()

    def deselect_all(self):
        for item in self.checkboxes.values():
            item["checkbox"].deselect()

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert('end', message + "\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    def check_if_installed(self, app_id):
        """Verifica se o software já está instalado usando winget"""
        if not app_id:
            return False # Se não tem ID (casos manuais), considera não instalado para forçar ação ou aviso
            
        try:
            # winget list --id <ID> --exact
            result = subprocess.run(["winget", "list", "--id", app_id, "--exact"], 
                                    capture_output=True, text=True, shell=True)
            if result.returncode == 0 and app_id in result.stdout:
                return True
        except Exception:
            pass
        return False

    def install_app(self, app_data):
        name = app_data['name']
        app_id = app_data.get('id')
        note = app_data.get('note', '')

        if not app_id:
            self.log(f"[SKIP] {name}: Instalação automática não disponível. {note}")
            return "skip"

        # 1. Verificar se já está instalado
        if self.check_if_installed(app_id):
            self.log(f"[OK] {name}: Já está instalado. Ignorando.")
            return "installed"

        # 2. Executar Instalação via Winget
        self.log(f"[INSTALANDO] {name}...")
        try:
            # Comando: winget install --id <ID> --silent --accept-package-agreements --accept-source-agreements
            cmd = ["winget", "install", "--id", app_id, "--silent", "--accept-package-agreements", "--accept-source-agreements"]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            stdout, stderr = process.communicate()
            
            if process.returncode == 0 or "No package found" not in stderr.decode():
                 # Winget as vezes retorna 0 mesmo com avisos, checar stderr é mais seguro para erros críticos
                 if "Failed" in stderr.decode() or "Error" in stderr.decode():
                     raise Exception(stderr.decode())
                 
                 self.log(f"[SUCESSO] {name} instalado com sucesso.")
                 return "success"
            else:
                raise Exception(stderr.decode())

        except Exception as e:
            self.log(f"[ERRO] Falha ao instalar {name}. Detalhes: {str(e)}")
            return "failed"

    def start_installation(self):
        # Desabilitar botão durante processo
        self.btn_start.configure(state="disabled", text="Instalando...")
        
        selected_apps = []
        for name, item in self.checkboxes.items():
            if item["checkbox"].get() == 1: # 1 significa marcado no CustomTkinter
                selected_apps.append(item["data"])

        if not selected_apps:
            messagebox.showwarning("Atenção", "Nenhum software selecionado!")
            self.btn_start.configure(state="normal", text="INICIAR INSTALAÇÃO")
            return

        # Rodar em thread separada para não travar a GUI
        self.install_thread = threading.Thread(target=self.run_installation_process, args=(selected_apps,))
        self.install_thread.start()

    def run_installation_process(self, apps):
        reboot_needed = False
        
        for app in apps:
            if self.stop_flag:
                break
            status = self.install_app(app)
            if status == "success":
                # Verificar se algum software comum exige reboot (ex: Java, VC++ Redist)
                if "Java" in app['name'] or "Visual C++" in app['name']:
                    reboot_needed = True
            
            # Pequena pausa entre instalações para não sobrecarregar
            threading.Event().wait(2) 

        # Finalização
        self.after(0, self.finish_installation, reboot_needed)

    def finish_installation(self, reboot_needed):
        self.btn_start.configure(state="normal", text="INICIAR INSTALAÇÃO")
        self.stop_flag = False
        
        msg = "Processo de instalação finalizado!"
        if reboot_needed:
            msg += "\n\nAtenção: Alguns softwares instalados podem exigir reinicialização do sistema para funcionar corretamente."
            messagebox.showinfo("Concluído com Aviso", msg)
        else:
            messagebox.showinfo("Concluído", msg)

if __name__ == "__main__":
    # Verificar Admin
    if not AutoElevate.is_admin():
        # Se não for admin, tenta elevar
        AutoElevate.run_as_admin()
    
    app = InstallerApp()
    app.mainloop()
