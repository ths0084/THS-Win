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
    {"name": "PJE", "id": None, "category": "free", "url": "https://pje-office.pje.jus.br/pro/pjeoffice-pro-v2.5.16u-windows_x64.exe", "note": "Instalador via URL oficial"},
    {"name": "Assinador Livre", "id": None, "category": "free", "url": "http://www.tjrj.jus.br/documents/10136/33009/AssinadorLivre.exe", "note": "Instalador via URL oficial"},
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
        self.title("Instalador e Mantenedor de Softwares")
        self.geometry("1100x750")
        self.minsize(900, 650)
        
        # Variáveis de Estado
        self.checkboxes = {}
        self.categories = ["free", "commercial"]
        self.install_thread = None
        self.stop_flag = False

        # Criar sistema de abas
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Adicionar abas
        self.tab_instalacao = self.tabview.add("📦 Instalação de Softwares")
        self.tab_manutencao = self.tabview.add("🛠️ Manutenção do Sistema")

        # Setup das interfaces
        self.setup_instalacao_tab()
        self.setup_manutencao_tab()

    def setup_instalacao_tab(self):
        """Configura a aba de instalação de softwares"""
        # Layout Principal da Aba Instalação
        self.tab_instalacao.grid_columnconfigure(1, weight=1)
        self.tab_instalacao.grid_rowconfigure(0, weight=1)

        # Sidebar (Menu Lateral)
        self.sidebar_frame = ctk.CTkFrame(self.tab_instalacao, width=200, corner_radius=0)
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
        self.scrollable_frame = ctk.CTkScrollableFrame(self.tab_instalacao, label_text="Selecione os Softwares")
        self.scrollable_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.scrollable_frame.grid_columnconfigure((0, 1), weight=1)

        # Renderizar Checkboxes
        self.render_checkboxes()

        # Área de Log (Inferior)
        self.log_frame = ctk.CTkFrame(self.tab_instalacao, height=150, corner_radius=10)
        self.log_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 20))
        self.log_frame.grid_propagate(False)
        
        self.log_label = ctk.CTkLabel(self.log_frame, text="Log de Instalação:", anchor="w")
        self.log_label.pack(fill="x", padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=6, bg="#2b2b2b", fg="white", font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_text.config(state='disabled')

    def setup_manutencao_tab(self):
        """Configura a aba de manutenção do sistema"""
        # Frame principal da aba manutenção
        main_frame = ctk.CTkScrollableFrame(self.tab_manutencao, label_text="Ferramentas de Manutenção do Windows")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Título explicativo
        info_label = ctk.CTkLabel(
            main_frame, 
            text="Selecione uma ferramenta para executar. Algumas operações podem levar vários minutos.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        info_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Botões de Manutenção organizados em grid
        tools = [
            {
                "name": "🧹 Limpeza de Disco",
                "desc": "Remove arquivos temporários, cache e lixeira",
                "cmd": self.run_disk_cleanup,
                "row": 1, "col": 0
            },
            {
                "name": "🔧 Reparar Sistema (SFC)",
                "desc": "Verifica e corrige arquivos do sistema corrompidos",
                "cmd": self.run_sfc_scan,
                "row": 1, "col": 1
            },
            {
                "name": "🏥 DISM RestoreHealth",
                "desc": "Repara imagem do Windows via Windows Update",
                "cmd": self.run_dism_restore,
                "row": 1, "col": 2
            },
            {
                "name": "⚡ Otimizar Drives",
                "desc": "Desfragmenta HDs ou executa TRIM em SSDs",
                "cmd": self.run_drive_optimize,
                "row": 2, "col": 0
            },
            {
                "name": "🛡️ Verificação Defender",
                "desc": "Executa varredura rápida de vírus e malware",
                "cmd": self.run_defender_scan,
                "row": 2, "col": 1
            },
            {
                "name": "🚀 Gerenciar Inicialização",
                "desc": "Abre gerenciador de programas na inicialização",
                "cmd": self.run_startup_manager,
                "row": 2, "col": 2
            },
            {
                "name": "🔄 Windows Update",
                "desc": "Verifica e instala atualizações do sistema",
                "cmd": self.run_windows_update,
                "row": 3, "col": 0
            },
            {
                "name": "🌐 Reset de Rede",
                "desc": "Libera DNS e reseta configurações de rede",
                "cmd": self.run_network_reset,
                "row": 3, "col": 1
            },
            {
                "name": "📊 Informações do Sistema",
                "desc": "Exibe detalhes sobre hardware e software",
                "cmd": self.run_system_info,
                "row": 3, "col": 2
            }
        ]

        self.maintenance_buttons = {}
        for tool in tools:
            frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color="#2b2b2b")
            frame.grid(row=tool["row"], column=tool["col"], padx=10, pady=10, sticky="nsew")
            frame.grid_columnconfigure(0, weight=1)

            name_label = ctk.CTkLabel(frame, text=tool["name"], font=ctk.CTkFont(size=14, weight="bold"))
            name_label.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

            desc_label = ctk.CTkLabel(frame, text=tool["desc"], font=ctk.CTkFont(size=10), text_color="gray", wraplength=250, justify="left")
            desc_label.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="w")

            btn = ctk.CTkButton(frame, text="Executar", height=35, command=tool["cmd"])
            btn.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="ew")

            self.maintenance_buttons[tool["name"]] = btn

        # Área de Log da Manutenção
        self.maintenance_log_frame = ctk.CTkFrame(self.tab_manutencao, height=120, corner_radius=10)
        self.maintenance_log_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.maintenance_log_label = ctk.CTkLabel(self.maintenance_log_frame, text="Log de Manutenção:", anchor="w")
        self.maintenance_log_label.pack(fill="x", padx=10, pady=5)
        
        self.maintenance_log_text = scrolledtext.ScrolledText(self.maintenance_log_frame, height=4, bg="#2b2b2b", fg="white", font=("Consolas", 9))
        self.maintenance_log_text.pack(fill="both", expand=True, padx=10, pady=5)
        self.maintenance_log_text.config(state='disabled')

    def log_manutencao(self, message):
        """Adiciona mensagem ao log de manutenção"""
        self.maintenance_log_text.config(state='normal')
        self.maintenance_log_text.insert('end', message + "\n")
        self.maintenance_log_text.see('end')
        self.maintenance_log_text.config(state='disabled')

    def run_disk_cleanup(self):
        """Executa limpeza de disco"""
        self.log_manutencao("[INICIANDO] Limpeza de Disco...")
        try:
            # Limpar pasta TEMP
            temp_dir = os.environ.get('TEMP', '')
            if temp_dir and os.path.exists(temp_dir):
                self.log_manutencao(f"[INFO] Limpando pasta temporária: {temp_dir}")
                subprocess.run(f'del /q /f "{temp_dir}\\*"', shell=True, capture_output=True)
            
            # Executar cleanmgr
            self.log_manutencao("[INFO] Iniciando Assistente de Limpeza de Disco...")
            subprocess.Popen(['cleanmgr', '/d', 'C'], shell=True)
            self.log_manutencao("[SUCESSO] Limpeza de Disco iniciada. Siga as instruções na janela.")
        except Exception as e:
            self.log_manutencao(f"[ERRO] Falha na limpeza: {str(e)}")

    def run_sfc_scan(self):
        """Executa SFC /scannow"""
        self.log_manutencao("[INICIANDO] Verificação SFC (System File Checker)...")
        self.log_manutencao("[AVISO] Este processo pode levar 15-30 minutos. Não feche a janela.")
        try:
            process = subprocess.Popen(['sfc', '/scannow'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
            
            # Ler output em tempo real
            for line in process.stdout:
                self.log_manutencao(line.strip())
            
            process.wait()
            if process.returncode == 0:
                self.log_manutencao("[SUCESSO] Verificação SFC concluída.")
            else:
                self.log_manutencao(f"[COMPLETO] SFC finalizou com código {process.returncode}. Verifique o log acima.")
        except Exception as e:
            self.log_manutencao(f"[ERRO] Falha no SFC: {str(e)}")

    def run_dism_restore(self):
        """Executa DISM RestoreHealth"""
        self.log_manutencao("[INICIANDO] DISM RestoreHealth...")
        self.log_manutencao("[AVISO] Este processo requer internet e pode levar 10-20 minutos.")
        try:
            process = subprocess.Popen(
                ['DISM', '/Online', '/Cleanup-Image', '/RestoreHealth'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True
            )
            
            for line in process.stdout:
                self.log_manutencao(line.strip())
            
            process.wait()
            if process.returncode == 0:
                self.log_manutencao("[SUCESSO] DISM concluído com sucesso.")
            else:
                self.log_manutencao(f"[COMPLETO] DISM finalizou com código {process.returncode}.")
        except Exception as e:
            self.log_manutencao(f"[ERRO] Falha no DISM: {str(e)}")

    def run_drive_optimize(self):
        """Executa otimização de drives"""
        self.log_manutencao("[INICIANDO] Otimização de Drives...")
        try:
            self.log_manutencao("[INFO] Abrindo utilitário de Otimizar e Desfragmentar Unidades...")
            subprocess.Popen(['dfrgui'], shell=True)
            self.log_manutencao("[SUCESSO] Utilitário de otimização aberto.")
        except Exception as e:
            self.log_manutencao(f"[ERRO] Falha ao abrir otimizador: {str(e)}")

    def run_defender_scan(self):
        """Executa varredura rápida do Windows Defender"""
        self.log_manutencao("[INICIANDO] Varredura Rápida do Windows Defender...")
        try:
            # PowerShell command para scan rápido
            ps_command = 'Start-MpScan -ScanType QuickScan'
            self.log_manutencao("[INFO] Iniciando varredura...")
            subprocess.Popen(['powershell', '-Command', ps_command], shell=True)
            self.log_manutencao("[SUCESSO] Varredura iniciada. Resultados aparecerão no Centro de Segurança.")
        except Exception as e:
            self.log_manutencao(f"[ERRO] Falha ao iniciar varredura: {str(e)}")

    def run_startup_manager(self):
        """Abre gerenciador de inicialização"""
        self.log_manutencao("[INICIANDO] Gerenciador de Inicialização...")
        try:
            # Abre Task Manager na aba Startup
            subprocess.Popen(['taskmgr', '/0', '/startup'], shell=True)
            self.log_manutencao("[SUCESSO] Gerenciador de Tarefas (Aba Inicialização) aberto.")
        except Exception as e:
            self.log_manutencao(f"[ERRO] Falha ao abrir gerenciador: {str(e)}")

    def run_windows_update(self):
        """Abre Windows Update"""
        self.log_manutencao("[INICIANDO] Windows Update...")
        try:
            # URI scheme para abrir diretamente a página de updates
            subprocess.Popen(['start', 'ms-settings:windowsupdate'], shell=True)
            self.log_manutencao("[SUCESSO] Página do Windows Update aberta.")
        except Exception as e:
            self.log_manutencao(f"[ERRO] Falha ao abrir Windows Update: {str(e)}")

    def run_network_reset(self):
        """Reseta configurações de rede"""
        self.log_manutencao("[INICIANDO] Reset de Rede...")
        try:
            self.log_manutencao("[INFO] Liberando DNS...")
            subprocess.run(['ipconfig', '/flushdns'], shell=True, capture_output=True, text=True)
            self.log_manutencao("[INFO] Renovando IP...")
            subprocess.run(['ipconfig', '/renew'], shell=True, capture_output=True, text=True)
            self.log_manutencao("[SUCESSO] Configurações de rede resetadas.")
            messagebox.showinfo("Reset de Rede", "Comandos de rede executados.\nDNS liberado e IP renovado.")
        except Exception as e:
            self.log_manutencao(f"[ERRO] Falha no reset de rede: {str(e)}")

    def run_system_info(self):
        """Exibe informações do sistema"""
        self.log_manutencao("[INICIANDO] Coletando informações do sistema...")
        try:
            import platform
            info = f"""
=== INFORMAÇÕES DO SISTEMA ===
Sistema: {platform.system()}
Versão: {platform.version()}
Release: {platform.release()}
Arquitetura: {platform.machine()}
Processador: {platform.processor()}
Nó: {platform.node()}
==============================
            """
            self.log_manutencao(info)
            messagebox.showinfo("Informações do Sistema", info.strip())
        except Exception as e:
            self.log_manutencao(f"[ERRO] Falha ao coletar informações: {str(e)}")

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
        app_url = app_data.get('url')
        note = app_data.get('note', '')

        # Caso especial: Software com URL direta para download
        if not app_id and app_url:
            self.log(f"[INSTALANDO] {name} via download direto...")
            return self.install_from_url(name, app_url)

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

    def install_from_url(self, name, url):
        """Instala software baixando diretamente da URL"""
        import tempfile
        import urllib.request
        
        try:
            # Criar arquivo temporário para o instalador
            temp_dir = tempfile.gettempdir()
            installer_path = os.path.join(temp_dir, f"{name.replace(' ', '_')}_installer.exe")
            
            self.log(f"[DOWNLOAD] Baixando {name} de {url}...")
            
            # Download do instalador
            urllib.request.urlretrieve(url, installer_path)
            
            self.log(f"[INSTALANDO] Executando instalador de {name}...")
            
            # Executar instalador em modo silencioso (tentativa genérica)
            # Cada software pode ter flags diferentes (/S, /quiet, /verysilent, etc.)
            process = subprocess.Popen([installer_path, "/S"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            # Limpar arquivo temporário
            try:
                os.remove(installer_path)
            except:
                pass
            
            if process.returncode == 0:
                self.log(f"[SUCESSO] {name} instalado com sucesso.")
                return "success"
            else:
                # Alguns instaladores podem exigir flags diferentes
                self.log(f"[AVISO] {name} pode exigir intervenção manual. Tente executar o instalador novamente se necessário.")
                return "partial"
                
        except Exception as e:
            self.log(f"[ERRO] Falha ao instalar {name} via URL. Detalhes: {str(e)}")
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
