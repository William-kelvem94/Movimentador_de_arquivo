import os
import psutil
import traceback
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QProgressBar, QLabel, QListWidget, QListWidgetItem,
    QMessageBox, QFrame, QAction, QMenuBar
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QIcon, QFont
from processador import FileProcessor

class ProcessingThread(QThread):
    update_progress = pyqtSignal(int, str)  # (progress_percent, current_file)
    update_file = pyqtSignal(str, str, str) # (file_name, status, details)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, processor, sources, model, destination):
        super().__init__()
        self.processor = processor
        self.sources = sources
        self.model = model
        self.destination = destination
        self._is_running = True
        self._cancel_requested = False

    def run(self):
        try:
            total_files = self.processor.calculate_total_files(self.sources)
            if total_files == 0:
                self.error_occurred.emit("Nenhum arquivo encontrado para processar!")
                return

            current_count = 0
            for source in self.sources:
                for root, _, files in os.walk(source):
                    for file in files:
                        if self._cancel_requested:
                            self.update_file.emit(file, "Cancelado", "Processamento interrompido")
                            return

                        file_path = os.path.join(root, file)
                        try:
                            result = self.processor.process_file(
                                file_path, 
                                root,
                                source,
                                self.model,
                                self.destination
                            )
                            
                            current_count += 1
                            progress = int((current_count / total_files) * 100)
                            self.update_progress.emit(progress, file)
                            
                            if result['status'] == 'success':
                                self.update_file.emit(file, "Sucesso", result['message'])
                            else:
                                self.update_file.emit(file, "Erro", result['message'])

                        except Exception as e:
                            error_msg = f"Erro crítico: {str(e)}"
                            self.error_occurred.emit(error_msg)
                            self.update_file.emit(file, "Erro", error_msg)

            self.finished.emit()

        except Exception as e:
            self.error_occurred.emit(f"Erro no processamento: {traceback.format_exc()}")
        finally:
            self._is_running = False

    def cancel(self):
        self._cancel_requested = True

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.processor = FileProcessor()
        self.sources = []
        self.current_theme = 'light'
        self.init_ui()
        self.setup_themes()

    def init_ui(self):
        """Inicializa a interface do usuário."""
        self.setWindowTitle("Organizador de Arquivos Pro")
        self.setGeometry(100, 100, 1280, 800)
        self.setup_menu()
        self.setup_main_layout()
        self.setup_theme()
        self.setup_system_monitor()

    def setup_themes(self):
        """Configura os temas da aplicação."""
        self.set_theme('light')

    def setup_menu(self):
        """Configura o menu da aplicação."""
        menu_bar = self.menuBar()
        
        # Menu Arquivo
        file_menu = menu_bar.addMenu("Arquivo")
        exit_action = QAction("Sair", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Menu Tema
        theme_menu = menu_bar.addMenu("Tema")
        light_theme = QAction("Tema Claro", self)
        dark_theme = QAction("Tema Escuro", self)
        light_theme.triggered.connect(lambda: self.set_theme('light'))
        dark_theme.triggered.connect(lambda: self.set_theme('dark'))
        theme_menu.addAction(light_theme)
        theme_menu.addAction(dark_theme)

    def setup_main_layout(self):
        """Configura o layout principal da aplicação."""
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)

        # Painel Esquerdo (Controles)
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        
        self.btn_add_source = QPushButton("➕ Adicionar Origem", self)
        self.btn_add_source.clicked.connect(self.add_source)
        
        self.source_list = QListWidget()
        self.source_list.setMinimumWidth(300)
        
        self.btn_model = QPushButton("📁 Selecionar Modelo", self)
        self.btn_model.clicked.connect(lambda: self.select_folder('model'))
        
        self.btn_dest = QPushButton("📂 Selecionar Destino", self)
        self.btn_dest.clicked.connect(lambda: self.select_folder('destination'))
        
        self.btn_remove_source = QPushButton("➖ Remover Origem", self)
        self.btn_remove_source.clicked.connect(self.remove_source)
        
        left_layout.addWidget(self.btn_add_source)
        left_layout.addWidget(QLabel("Pastas Origem:"))
        left_layout.addWidget(self.source_list)
        left_layout.addWidget(self.btn_model)
        left_layout.addWidget(self.btn_dest)
        left_layout.addWidget(self.btn_remove_source)

        # Painel Direito (Progresso e Resultados)
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        
        self.progress_bar = QProgressBar()
        self.lbl_status = QLabel("Status: Pronto")
        
        self.file_list = QListWidget()
        self.file_list.setMinimumWidth(500)
        
        self.system_info = QLabel()
        self.system_info.setAlignment(Qt.AlignRight)
        
        control_layout = QHBoxLayout()
        self.btn_start = QPushButton("▶ Iniciar", self)
        self.btn_stop = QPushButton("⏹ Parar", self)
        self.btn_stop.setEnabled(False)
        self.btn_start.clicked.connect(self.start_processing)
        self.btn_stop.clicked.connect(self.stop_processing)
        
        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_stop)
        
        right_layout.addWidget(self.progress_bar)
        right_layout.addWidget(self.lbl_status)
        right_layout.addWidget(QLabel("Arquivos Processados:"))
        right_layout.addWidget(self.file_list)
        right_layout.addWidget(self.system_info)
        right_layout.addLayout(control_layout)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        self.setCentralWidget(main_widget)

    def setup_theme(self):
        """Configura o tema inicial da aplicação."""
        self.set_theme('light')

    def setup_system_monitor(self):
        """Configura o monitoramento do sistema."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_system_stats)
        self.timer.start(1000)

    def set_theme(self, theme):
        """Define o tema da aplicação."""
        self.current_theme = theme
        if theme == 'light':
            self.apply_light_theme()
        else:
            self.apply_dark_theme()

    def apply_light_theme(self):
        """Aplica o tema claro."""
        style = """
        QMainWindow {
            background-color: #F5F5F5;
            color: #333333;
        }
        QFrame {
            background-color: #FFFFFF;
            border-radius: 8px;
            padding: 10px;
        }
        QPushButton {
            background-color: #007AFF;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: #0063CC;
        }
        QListWidget {
            background-color: #FFFFFF;
            border: 1px solid #DDDDDD;
            border-radius: 4px;
        }
        QProgressBar {
            border: 1px solid #DDDDDD;
            border-radius: 4px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #007AFF;
        }
        """
        self.setStyleSheet(style)

    def apply_dark_theme(self):
        """Aplica o tema escuro."""
        style = """
        QMainWindow {
            background-color: #1E1E1E;
            color: #FFFFFF;
        }
        QFrame {
            background-color: #2D2D2D;
            border-radius: 8px;
            padding: 10px;
        }
        QPushButton {
            background-color: #0A84FF;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: #0063CC;
        }
        QListWidget {
            background-color: #3A3A3A;
            border: 1px solid #454545;
            border-radius: 4px;
        }
        QProgressBar {
            border: 1px solid #454545;
            border-radius: 4px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #0A84FF;
        }
        """
        self.setStyleSheet(style)

    def add_source(self):
        """Adiciona uma pasta de origem."""
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Origem")
        if folder:
            self.sources.append(folder)
            self.source_list.addItem(f"📁 Pasta {len(self.sources)}: {os.path.basename(folder)}")

    def remove_source(self):
        """Remove a pasta de origem selecionada."""
        selected_items = self.source_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Selecione uma pasta de origem para remover!")
            return
        for item in selected_items:
            index = self.source_list.row(item)
            self.source_list.takeItem(index)
            del self.sources[index]

    def select_folder(self, folder_type):
        """Seleciona uma pasta (modelo ou destino)."""
        folder = QFileDialog.getExistingDirectory(self, f"Selecionar Pasta {folder_type.capitalize()}")
        if folder:
            setattr(self, folder_type, folder)
            if folder_type == 'model':
                self.btn_model.setText(f"✅ Modelo: {os.path.basename(folder)}")
            elif folder_type == 'destination':
                self.btn_dest.setText(f"✅ Destino: {os.path.basename(folder)}")

    def validate_inputs(self):
        """Valida as entradas do usuário."""
        if not hasattr(self, 'model'):
            QMessageBox.warning(self, "Aviso", "Selecione a pasta modelo!")
            return False
        if not hasattr(self, 'destination'):
            QMessageBox.warning(self, "Aviso", "Selecione a pasta destino!")
            return False
        if not self.sources:
            QMessageBox.warning(self, "Aviso", "Adicione pelo menos uma pasta de origem!")
            return False
        return True

    def start_processing(self):
        """Inicia o processamento dos arquivos."""
        if not self.validate_inputs():
            return

        try:
            self.thread = ProcessingThread(
                self.processor,
                self.sources,
                self.model,
                self.destination
            )

            # Conexões de sinais
            self.thread.update_progress.connect(self.update_progress)
            self.thread.update_file.connect(self.update_file_status)
            self.thread.error_occurred.connect(self.show_error)
            self.thread.finished.connect(self.on_processing_finished)

            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.lbl_status.setText("Status: Processando...")
            self.file_list.clear()
            
            self.thread.start()

        except Exception as e:
            self.show_error(f"Erro ao iniciar processamento: {str(e)}")

    def stop_processing(self):
        """Para o processamento dos arquivos."""
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.cancel()
            self.lbl_status.setText("Status: Cancelando...")
            self.btn_stop.setEnabled(False)

    def update_progress(self, value, current_file):
        """Atualiza a barra de progresso."""
        self.progress_bar.setValue(value)
        self.lbl_status.setText(f"Processando: {current_file}")

    def update_file_status(self, file_name, status, details):
        """Atualiza o status de um arquivo processado."""
        item = QListWidgetItem()
        if status == "Sucesso":
            item.setIcon(QIcon.fromTheme("dialog-ok"))
            item.setText(f"✓ {file_name}")
            item.setToolTip(details)
        else:
            item.setIcon(QIcon.fromTheme("dialog-error"))
            item.setText(f"✗ {file_name} - {status}")
            item.setToolTip(details)
        self.file_list.addItem(item)
        self.file_list.scrollToBottom()

    def show_error(self, message):
        """Exibe uma mensagem de erro."""
        QMessageBox.critical(self, "Erro", message)
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_status.setText("Status: Erro ocorrido")

    def on_processing_finished(self):
        """Ações a serem tomadas quando o processamento for concluído."""
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_status.setText("Status: Processamento concluído")
        QMessageBox.information(self, "Concluído", "Processamento finalizado com sucesso!")

    def update_system_stats(self):
        """Atualiza as estatísticas do sistema."""
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        self.system_info.setText(
            f"CPU: {cpu:.1f}% | Memória: {mem:.1f}% | Disco: {disk:.1f}%"
        )