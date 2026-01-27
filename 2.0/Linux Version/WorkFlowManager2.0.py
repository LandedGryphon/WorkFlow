import sys
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QComboBox, QLabel, 
                             QFileDialog, QRadioButton, QButtonGroup, QMessageBox,
                             QTabWidget, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal # Importamos pyqtSignal aqui
from PyQt5.QtGui import QIcon, QFont

CONFIG_FILE = "config.json"

class SoftwareTab(QWidget):
    """Componente reutilizável para cada aba de software."""
    
    # Definimos um sinal customizado para avisar quando algo mudar
    config_updated = pyqtSignal()
    
    def __init__(self, software_name, template_ext, output_ext, parent=None):
        super().__init__(parent)
        self.software_key = software_name.lower()
        self.template_ext = template_ext
        self.output_ext = output_ext
        self.base_path = None
        self.custom_template_path = None
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # --- Seção de Configuração ---
        self.lbl_base = QLabel(f"Pasta Base {self.software_key.capitalize()}: Não Selecionada")
        self.lbl_base.setWordWrap(True)
        self.lbl_base.setStyleSheet("color: #7f8c8d; font-style: italic;")
        
        btn_base = QPushButton(f" Selecionar Pasta Base")
        btn_base.clicked.connect(self.select_base_path)
        
        self.lbl_templates = QLabel("Pasta de Modelos: Automática")
        self.lbl_templates.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        
        btn_custom_tpl = QPushButton("Alterar Pasta de Modelos (Opcional)")
        btn_custom_tpl.setStyleSheet("font-size: 10px; height: 20px;")
        btn_custom_tpl.clicked.connect(self.select_custom_template_path)

        layout.addWidget(self.lbl_base)
        layout.addWidget(btn_base)
        layout.addWidget(self.lbl_templates)
        layout.addWidget(btn_custom_tpl)

        layout.addWidget(self.create_separator())

        # --- Tipo de Projeto ---
        type_layout = QHBoxLayout()
        self.radio_cliente = QRadioButton("Cliente")
        self.radio_cliente.setChecked(True)
        self.radio_outros = QRadioButton("Outros")
        self.group_type = QButtonGroup(self)
        self.group_type.addButton(self.radio_cliente)
        self.group_type.addButton(self.radio_outros)
        type_layout.addWidget(self.radio_cliente)
        type_layout.addWidget(self.radio_outros)
        layout.addLayout(type_layout)

        # --- Campos de Texto ---
        self.ent_nome = QLineEdit()
        self.ent_nome.setPlaceholderText("Ex: João Silva ou Projeto Cozinha")
        layout.addWidget(QLabel("Nome do Cliente/Projeto:"))
        layout.addWidget(self.ent_nome)

        self.ent_subpastas = QLineEdit()
        self.ent_subpastas.setPlaceholderText("Subpastas (ex: Quarto/Armario)")
        layout.addWidget(QLabel("Subpastas (Opcional):"))
        layout.addWidget(self.ent_subpastas)

        self.ent_arquivo = QLineEdit()
        self.ent_arquivo.setPlaceholderText("Nome do arquivo final")
        layout.addWidget(QLabel("Nome do Arquivo:"))
        layout.addWidget(self.ent_arquivo)

        # --- Templates ---
        template_layout = QHBoxLayout()
        self.combo_templates = QComboBox()
        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedWidth(40)
        btn_refresh.clicked.connect(self.refresh_templates)
        template_layout.addWidget(self.combo_templates)
        template_layout.addWidget(btn_refresh)
        layout.addWidget(QLabel(f"Template ({self.template_ext}):"))
        layout.addLayout(template_layout)

        # --- Botão Executar ---
        btn_run = QPushButton(f"Criar Projeto {self.software_key.capitalize()}")
        btn_run.setObjectName("runButton")
        btn_run.clicked.connect(self.execute_workflow)
        layout.addWidget(btn_run)

        layout.addStretch()
        self.setLayout(layout)

    def create_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def select_base_path(self):
        path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta Base")
        if path:
            self.base_path = Path(path)
            self.lbl_base.setText(f"Base: {self.base_path}")
            self.refresh_templates()
            self.config_updated.emit() # Dispara o sinal para o pai salvar

    def select_custom_template_path(self):
        path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Modelos")
        if path:
            self.custom_template_path = Path(path)
            self.lbl_templates.setText(f"Modelos: {self.custom_template_path}")
            self.refresh_templates()
            self.config_updated.emit() # Dispara o sinal para o pai salvar

    def get_template_dir(self):
        if self.custom_template_path:
            return self.custom_template_path
        return self.base_path / "Modelos" if self.base_path else None

    def refresh_templates(self):
        tpl_dir = self.get_template_dir()
        self.combo_templates.clear()
        if tpl_dir and tpl_dir.exists():
            templates = list(tpl_dir.glob(f"*{self.template_ext}"))
            self.combo_templates.addItems([t.name for t in templates])
        else:
            self.lbl_templates.setText("Status: Pasta 'Modelos' não detectada.")

    def execute_workflow(self):
        if not self.base_path or not self.ent_nome.text() or not self.ent_arquivo.text():
            QMessageBox.critical(self, "Erro", "Preencha os campos obrigatórios!")
            return

        agora = datetime.now()
        meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                 "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        
        categoria = "Clientes" if self.radio_cliente.isChecked() else "Outros"
        caminho_final = self.base_path / str(agora.year) / categoria / meses[agora.month-1] / self.ent_nome.text()

        if self.ent_subpastas.text():
            caminho_final = caminho_final / self.ent_subpastas.text().strip("/")

        try:
            caminho_final.mkdir(parents=True, exist_ok=True)
            template_name = self.combo_templates.currentText()
            if not template_name: raise ValueError("Nenhum template selecionado.")

            origem = self.get_template_dir() / template_name
            destino = caminho_final / f"{self.ent_arquivo.text()}{self.output_ext}"

            if destino.exists():
                res = QMessageBox.question(self, "Substituir?", f"Sobrescrever {destino.name}?", QMessageBox.Yes|QMessageBox.No)
                if res == QMessageBox.No: return

            shutil.copy2(origem, destino)
            self.open_file(destino)
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def open_file(self, filepath):
        if sys.platform == "win32": os.startfile(filepath)
        else: subprocess.call(["xdg-open" if sys.platform == "linux" else "open", str(filepath)])


class WorkflowHub(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.apply_saved_config()

    def init_ui(self):
        self.setWindowTitle("Workflow Manager 2.0")
        self.setMinimumWidth(550)
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.tab_aspire = SoftwareTab("Aspire", ".crvt3d", ".crv3d")
        self.tab_sketchup = SoftwareTab("SketchUp", ".skp", ".skp")
        
        # CONEXÃO DOS SINAIS: Quando a aba avisar, a Janela Principal salva
        self.tab_aspire.config_updated.connect(self.save_config)
        self.tab_sketchup.config_updated.connect(self.save_config)

        self.tabs.addTab(self.tab_aspire, "Vectric Aspire")
        self.tabs.addTab(self.tab_sketchup, "SketchUp")

        self.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #dcdde1; background: white; }
            QTabBar::tab:selected { border-bottom: 2px solid #3498db; font-weight: bold; }
            QPushButton#runButton { background: #2ecc71; color: white; font-weight: bold; height: 40px; border-radius: 4px; }
        """)

        layout.addWidget(self.tabs)

    def save_config(self):
        """Salva as configurações de todas as abas no JSON."""
        data = {
            "aspire": {
                "base_path": str(self.tab_aspire.base_path or ""),
                "custom_template_path": str(self.tab_aspire.custom_template_path or "")
            },
            "sketchup": {
                "base_path": str(self.tab_sketchup.base_path or ""),
                "custom_template_path": str(self.tab_sketchup.custom_template_path or "")
            }
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def apply_saved_config(self):
        if not Path(CONFIG_FILE).exists(): return
        try:
            with open(CONFIG_FILE, 'r') as f:
                cfg = json.load(f)
                for key, tab in [("aspire", self.tab_aspire), ("sketchup", self.tab_sketchup)]:
                    s_cfg = cfg.get(key, {})
                    if s_cfg.get("base_path"):
                        tab.base_path = Path(s_cfg["base_path"])
                        tab.lbl_base.setText(f"Base: {tab.base_path}")
                    if s_cfg.get("custom_template_path"):
                        tab.custom_template_path = Path(s_cfg["custom_template_path"])
                        tab.lbl_templates.setText(f"Modelos: {tab.custom_template_path}")
                    tab.refresh_templates()
        except Exception as e:
            print(f"Erro ao carregar config: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = WorkflowHub()
    window.show()
    sys.exit(app.exec_())