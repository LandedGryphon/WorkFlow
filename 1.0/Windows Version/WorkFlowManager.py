import sys
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QComboBox, QLabel, 
                             QFileDialog, QRadioButton, QButtonGroup, QMessageBox)
from PyQt5.QtCore import Qt

CONFIG_FILE = "config.json"

class AspireAutomator(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_config()

    def init_ui(self):
        self.setWindowTitle("Workflow Manager 1.0")
        self.setMinimumWidth(500)
        layout = QVBoxLayout()

        # --- Seleção de Pasta Base ---
        self.lbl_base = QLabel("Pasta Base: Não Selecionada")
        btn_base = QPushButton("Selecionar Pasta Base")
        btn_base.clicked.connect(self.select_base_path)
        layout.addWidget(self.lbl_base)
        layout.addWidget(btn_base)

        # --- Tipo de Projeto (Toggle) ---
        type_layout = QHBoxLayout()
        self.radio_cliente = QRadioButton("Cliente")
        self.radio_cliente.setChecked(True)
        self.radio_outros = QRadioButton("Outros")
        self.group_type = QButtonGroup()
        self.group_type.addButton(self.radio_cliente)
        self.group_type.addButton(self.radio_outros)
        type_layout.addWidget(self.radio_cliente)
        type_layout.addWidget(self.radio_outros)
        layout.addLayout(type_layout)

        # --- Campos de Texto ---
        self.ent_nome = QLineEdit()
        self.ent_nome.setPlaceholderText("Nome do Cliente ou Projeto")
        layout.addWidget(QLabel("Nome Principal:"))
        layout.addWidget(self.ent_nome)

        self.ent_subpastas = QLineEdit()
        self.ent_subpastas.setPlaceholderText("Subpastas (ex: Quarto/Armario/Gaveta)")
        layout.addWidget(QLabel("Subpastas (Opcional):"))
        layout.addWidget(self.ent_subpastas)

        self.ent_arquivo = QLineEdit()
        self.ent_arquivo.setPlaceholderText("Nome final do arquivo (sem extensão)")
        layout.addWidget(QLabel("Nome do Arquivo Final:"))
        layout.addWidget(self.ent_arquivo)

        # --- Templates ---
        template_layout = QHBoxLayout()
        self.combo_templates = QComboBox()
        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedWidth(40)
        btn_refresh.clicked.connect(self.refresh_templates)
        template_layout.addWidget(self.combo_templates)
        template_layout.addWidget(btn_refresh)
        layout.addWidget(QLabel("Template (.crvt3d):"))
        layout.addLayout(template_layout)

        # --- Botão Executar ---
        btn_run = QPushButton("Criar Projeto e Abrir")
        btn_run.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; height: 40px;")
        btn_run.clicked.connect(self.execute_workflow)
        layout.addWidget(btn_run)

        self.setLayout(layout)
        self.base_path = None

    # --- Lógica de Persistência ---
    def load_config(self):
        if Path(CONFIG_FILE).exists():
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                self.base_path = Path(data.get("base_path", ""))
                if self.base_path.exists():
                    self.lbl_base.setText(f"Pasta Base: {self.base_path}")
                    self.refresh_templates()

    def save_config(self, path):
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"base_path": str(path)}, f)

    def select_base_path(self):
        path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta Base")
        if path:
            self.base_path = Path(path)
            self.lbl_base.setText(f"Pasta Base: {self.base_path}")
            self.save_config(self.base_path)
            self.refresh_templates()

    def refresh_templates(self):
        if not self.base_path: return
        self.combo_templates.clear()
        template_dir = self.base_path / "Modelos"
        
        if template_dir.exists():
            templates = list(template_dir.glob("*.crvt3d"))
            self.combo_templates.addItems([t.name for t in templates])
        else:
            QMessageBox.warning(self, "Erro", "Pasta 'Modelos' não encontrada na base.")

    # --- Regras de Negócio ---
    def execute_workflow(self):
        if not self.base_path or not self.ent_nome.text() or not self.ent_arquivo.text():
            QMessageBox.critical(self, "Erro", "Preencha todos os campos obrigatórios!")
            return

        # 1. Definir Tempo
        agora = datetime.now()
        ano = str(agora.year)
        # Meses em PT-BR (ou use locale)
        meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                 "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        mes = meses[agora.month - 1]

        # 2. Construir Caminho
        categoria = "Clientes" if self.radio_cliente.isChecked() else "Outros"
        caminho_final = self.base_path / ano / categoria / mes / self.ent_nome.text()

        # Adicionar subpastas infinitas
        if self.ent_subpastas.text():
            caminho_final = caminho_final / self.ent_subpastas.text()

        # 3. Criar Diretórios
        try:
            caminho_final.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Erro de Sistema", f"Falha ao criar pastas: {e}")
            return

        # 4. Processar Arquivo
        template_selecionado = self.combo_templates.currentText()
        if not template_selecionado:
            QMessageBox.warning(self, "Erro", "Selecione um template.")
            return

        origem = self.base_path / "Modelos" / template_selecionado
        destino = caminho_final / f"{self.ent_arquivo.text()}.crv3d"

        try:
            shutil.copy2(origem, destino)
            
            # 5. Execução Cross-Platform
            if sys.platform == "win32":
                os.startfile(destino)
            else:
                QMessageBox.information(self, "Sucesso (Linux)", f"Arquivo criado em:\n{destino}")
        
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao copiar arquivo: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AspireAutomator()
    window.show()
    sys.exit(app.exec_())