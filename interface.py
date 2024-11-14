
import os
import psutil
import json
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QFileDialog, QProgressBar, QLabel, QTextEdit, QMessageBox, 
                             QListWidget, QListWidgetItem, QStyle, QApplication, QScrollArea,
                             QSplitter, QTreeView, QFileSystemModel, QCheckBox, QLineEdit,
                             QComboBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer, QSize, QDir
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette
from processador import FileProcessor
import pyqtgraph as pg

class ProcessingThread(QThread):
    update_progress = pyqtSignal(int)
    update_status = pyqtSignal(str)
    update_file_list = pyqtSignal(str, str)

    def __init__(self, processor, source, destination, structure_model):
        super().__init__()
        self.processor = processor
        self.source = source
        self.destination = destination
        self.structure_model = structure_model
        self.is_cancelled = False

    def run(self):
        self.processor.process_files(self.source, self.destination, 
                                     self.update_progress.emit, 
                                     self.update_status.emit,
                                     self.update_file_list.emit,
                                     self.structure_model,
                                     self.check_cancelled)

    def cancel(self):
        self.is_cancelled = True

    def check_cancelled(self):
        return self.is_cancelled

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.processor = FileProcessor()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Movimentador de Arquivos Inteligente")
        self.setGeometry(100, 100, 1200, 800)
        self.setup_theme()

        main_layout = QVBoxLayout()

        # Splitter para dividir a interface
        splitter = QSplitter(Qt.Horizontal)

        # Painel esquerdo: Árvore de diretórios
        self.file_system_model = QFileSystemModel()
        self.file_system_model.setRootPath(QDir.rootPath())
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.file_system_model)
        self.tree_view.setRootIndex(self.file_system_model.index(QDir.homePath()))
        self.tree_view.setAnimated(True)
        self.tree_view.setIndentation(20)
        self.tree_view.setSortingEnabled(True)
        self.tree_view.setColumnWidth(0, 250)
        splitter.addWidget(self.tree_view)

        # Painel direito: Controles e lista de arquivos
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Botões
        button_layout = QHBoxLayout()
        self.source_button = QPushButton("Selecionar Pasta de Origem", self)
        self.destination_button = QPushButton("Selecionar Pasta de Destino", self)
        self.structure_model_button = QPushButton("Selecionar Modelo de Estrutura", self)
        self.start_button = QPushButton("Iniciar Processamento", self)
        self.cancel_button = QPushButton("Cancelar Processamento", self)
        self.cancel_button.setEnabled(False)
        button_layout.addWidget(self.source_button)
        button_layout.addWidget(self.destination_button)
        button_layout.addWidget(self.structure_model_button)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.cancel_button)
        right_layout.addLayout(button_layout)

        # Checkbox para continuar de onde parou
        self.continue_checkbox = QCheckBox("Continuar de Onde Parou", self)
        right_layout.addWidget(self.continue_checkbox)

        # Barra de progresso e status
        self.progress_bar = QProgressBar(self)
        self.status_label = QLabel("Pronto para iniciar", self)
        right_layout.addWidget(self.progress_bar)
        right_layout.addWidget(self.status_label)

        # Lista de arquivos processados
        self.file_list = QListWidget(self)
        right_layout.addWidget(QLabel("Arquivos Processados:"))
        right_layout.addWidget(self.file_list)

        # Gráfico de informações do sistema
        self.system_info_graph = pg.PlotWidget()
        self.system_info_graph.setBackground('w')
        self.cpu_curve = self.system_info_graph.plot(pen='b')
        self.mem_curve = self.system_info_graph.plot(pen='r')
        self.disk_curve = self.system_info_graph.plot(pen='g')
        self.system_info_graph.setLabel('left', 'Utilização (%)')
        self.system_info_graph.setLabel('bottom', 'Tempo (s)')
        self.system_info_graph.setYRange(0, 100)
        right_layout.addWidget(self.system_info_graph)

        splitter.addWidget(right_panel)

        main_layout.addWidget(splitter)

        # Seletor de tema
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Tema:")
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Claro", "Escuro"])
        self.theme_selector.currentIndexChanged.connect(self.change_theme)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_selector)
        main_layout.addLayout(theme_layout)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.source_button.clicked.connect(self.select_source)
        self.destination_button.clicked.connect(self.select_destination)
        self.structure_model_button.clicked.connect(self.select_structure_model)
        self.start_button.clicked.connect(self.start_processing)
        self.cancel_button.clicked.connect(self.cancel_processing)
        self.tree_view.clicked.connect(self.on_tree_view_clicked)

        # Timer para atualizar informações do sistema
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_system_info)
        self.timer.start(1000)  # Atualiza a cada 1 segundo

        self.cpu_data = []
        self.mem_data = []
        self.disk_data = []
        self.time_data = []

    def setup_theme(self):
        self.light_palette = QPalette()
        self.dark_palette = QPalette()

        # Configuração da paleta clara
        self.light_palette.setColor(QPalette.Window, QColor(240, 240, 240))
        self.light_palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        self.light_palette.setColor(QPalette.Base, QColor(255, 255, 255))
        self.light_palette.setColor(QPalette.AlternateBase, QColor(230, 230, 230))
        self.light_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
        self.light_palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
        self.light_palette.setColor(QPalette.Text, QColor(0, 0, 0))
        self.light_palette.setColor(QPalette.Button, QColor(240, 240, 240))
        self.light_palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
        self.light_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        self.light_palette.setColor(QPalette.Link, QColor(0, 0, 255))
        self.light_palette.setColor(QPalette.Highlight, QColor(200, 200, 200))
        self.light_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))

        # Configuração da paleta escura
        self.dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        self.dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        self.dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        self.dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        self.dark_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        self.dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        self.dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
        self.dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        self.dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        self.dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        self.dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        self.dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        self.dark_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))

        # Aplicar tema claro por padrão
        self.setPalette(self.light_palette)

    def change_theme(self, index):
        if index == 0:  # Tema claro
            self.setPalette(self.light_palette)
            self.system_info_graph.setBackground('w')
            self.cpu_curve.setPen('b')
            self.mem_curve.setPen('r')
            self.disk_curve.setPen('g')
        else:  # Tema escuro
            self.setPalette(self.dark_palette)
            self.system_info_graph.setBackground('k')
            self.cpu_curve.setPen('c')
            self.mem_curve.setPen('m')
            self.disk_curve.setPen('y')

    def select_source(self):
        self.source_dir = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Origem")
        self.source_button.setText(f"Origem: {os.path.basename(self.source_dir)}")

    def select_destination(self):
        self.destination_dir = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Destino")
        self.destination_button.setText(f"Destino: {os.path.basename(self.destination_dir)}")

    def select_structure_model(self):
        self.structure_model_dir = QFileDialog.getExistingDirectory(self, "Selecionar Modelo de Estrutura")
        self.structure_model_button.setText(f"Modelo: {os.path.basename(self.structure_model_dir)}")

    def start_processing(self):
        if not hasattr(self, 'source_dir') or not hasattr(self, 'destination_dir'):
            QMessageBox.warning(self, "Aviso", "Por favor, selecione as pastas de origem e destino.")
            return

        if not hasattr(self, 'structure_model_dir'):
            QMessageBox.warning(self, "Aviso", "Por favor, selecione o modelo de estrutura.")
            return

        self.file_list.clear()
        self.processing_thread = ProcessingThread(self.processor, self.source_dir, self.destination_dir, self.structure_model_dir)
        self.processing_thread.update_progress.connect(self.progress_bar.setValue)
        self.processing_thread.update_status.connect(self.status_label.setText)
        self.processing_thread.update_file_list.connect(self.update_file_list)
        self.processing_thread.start()

        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

    def cancel_processing(self):
        if hasattr(self, 'processing_thread'):
            self.processing_thread.cancel()
            self.status_label.setText("Cancelando processamento...")
            self.cancel_button.setEnabled(False)

    def update_file_list(self, file_name, status):
        item = QListWidgetItem(f"{file_name} - {status}")
        if status == "Sucesso":
            item.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        else:
            item.setIcon(self.style().standardIcon(QStyle.SP_DialogCancelButton))
        self.file_list.addItem(item)
        self.file_list.scrollToBottom()

    def update_system_info(self):
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent

        self.cpu_data.append(cpu)
        self.mem_data.append(memory)
        self.disk_data.append(disk)
        self.time_data.append(len(self.time_data))

        if len(self.time_data) > 60:  # Manter apenas os últimos 60 segundos
            self.cpu_data = self.cpu_data[-60:]
            self.mem_data = self.mem_data[-60:]
            self.disk_data = self.disk_data[-60:]
            self.time_data = self.time_data[-60:]

        self.cpu_curve.setData(self.time_data, self.cpu_data)
        self.mem_curve.setData(self.time_data, self.mem_data)
        self.disk_curve.setData(self.time_data, self.disk_data)

    def on_tree_view_clicked(self, index):
        path = self.file_system_model.filePath(index)
        if os.path.isdir(path):
            self.source_dir = path
            self.source_button.setText(f"Origem: {os.path.basename(self.source_dir)}")
