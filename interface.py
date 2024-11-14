
import os
import psutil
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QFileDialog, QProgressBar, QLabel, QTextEdit, QMessageBox, 
                             QListWidget, QListWidgetItem, QStyle, QApplication, QScrollArea,
                             QSplitter, QTreeView, QFileSystemModel)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer, QSize, QDir
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette
from processador import FileProcessor

class ProcessingThread(QThread):
    update_progress = pyqtSignal(int)
    update_status = pyqtSignal(str)
    update_file_list = pyqtSignal(str, str)

    def __init__(self, processor, source, destination):
        super().__init__()
        self.processor = processor
        self.source = source
        self.destination = destination

    def run(self):
        self.processor.process_files(self.source, self.destination, 
                                     self.update_progress.emit, 
                                     self.update_status.emit,
                                     self.update_file_list.emit)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.processor = FileProcessor()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Movimentador de Arquivos Inteligente")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet('''
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                margin: 4px 2px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QProgressBar {
                border: 2px solid #3498db;
                border-radius: 5px;
                text-align: center;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #3498db;
            }
            QListWidget, QTreeView {
                background-color: #363636;
                color: #ffffff;
                border: 1px solid #3498db;
                border-radius: 4px;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
        ''')

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
        self.start_button = QPushButton("Iniciar Processamento", self)
        button_layout.addWidget(self.source_button)
        button_layout.addWidget(self.destination_button)
        button_layout.addWidget(self.start_button)
        right_layout.addLayout(button_layout)

        # Barra de progresso e status
        self.progress_bar = QProgressBar(self)
        self.status_label = QLabel("Pronto para iniciar", self)
        right_layout.addWidget(self.progress_bar)
        right_layout.addWidget(self.status_label)

        # Lista de arquivos processados
        self.file_list = QListWidget(self)
        right_layout.addWidget(QLabel("Arquivos Processados:"))
        right_layout.addWidget(self.file_list)

        # Informações do sistema
        self.system_info_label = QLabel(self)
        right_layout.addWidget(self.system_info_label)

        splitter.addWidget(right_panel)

        main_layout.addWidget(splitter)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.source_button.clicked.connect(self.select_source)
        self.destination_button.clicked.connect(self.select_destination)
        self.start_button.clicked.connect(self.start_processing)
        self.tree_view.clicked.connect(self.on_tree_view_clicked)

        # Timer para atualizar informações do sistema
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_system_info)
        self.timer.start(1000)  # Atualiza a cada 1 segundo

    def select_source(self):
        self.source_dir = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Origem")
        self.source_button.setText(f"Origem: {os.path.basename(self.source_dir)}")

    def select_destination(self):
        self.destination_dir = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Destino")
        self.destination_button.setText(f"Destino: {os.path.basename(self.destination_dir)}")

    def start_processing(self):
        if not hasattr(self, 'source_dir') or not hasattr(self, 'destination_dir'):
            QMessageBox.warning(self, "Aviso", "Por favor, selecione as pastas de origem e destino.")
            return

        self.file_list.clear()
        self.processing_thread = ProcessingThread(self.processor, self.source_dir, self.destination_dir)
        self.processing_thread.update_progress.connect(self.progress_bar.setValue)
        self.processing_thread.update_status.connect(self.status_label.setText)
        self.processing_thread.update_file_list.connect(self.update_file_list)
        self.processing_thread.start()

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
        self.system_info_label.setText(f"CPU: {cpu}% | Memória: {memory}% | Disco: {disk}%")

    def on_tree_view_clicked(self, index):
        path = self.file_system_model.filePath(index)
        if os.path.isdir(path):
            self.source_dir = path
            self.source_button.setText(f"Origem: {os.path.basename(self.source_dir)}")

