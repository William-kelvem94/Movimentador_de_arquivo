
import os
import shutil
import mimetypes
import json
import logging
from PIL import Image
from tqdm import tqdm
from colorama import Fore, Style

class FileProcessor:
    def __init__(self):
        self.log_dir = os.path.join(os.path.expanduser("~"), "MovimentadorDeArquivos", "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, "processamento.log")
        logging.basicConfig(filename=self.log_file, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    def process_files(self, source, destination, update_progress, update_status, update_file_list, use_model, structure_model, check_cancelled):
        files = [f for f in os.listdir(source) if os.path.isfile(os.path.join(source, f))]
        total_files = len(files)

        if use_model and structure_model:
            try:
                structure = json.loads(structure_model)
            except json.JSONDecodeError:
                update_status("Erro: Modelo de estrutura inválido")
                return
        else:
            structure = None

        for i, file in enumerate(tqdm(files, desc="Processando arquivos", unit="arquivo")):
            if check_cancelled():
                update_status("Processamento cancelado")
                self.save_progress(i, total_files, source, destination)
                return

            source_path = os.path.join(source, file)
            try:
                if structure:
                    dest_folder = self.get_destination_folder(file, structure, destination)
                else:
                    file_type = self.get_file_type(source_path)
                    dest_folder = os.path.join(destination, file_type)

                os.makedirs(dest_folder, exist_ok=True)
                destination_path = os.path.join(dest_folder, file)

                if os.path.exists(destination_path):
                    destination_path = self.get_unique_filename(destination_path)

                if self.get_file_type(source_path) == "Imagens":
                    self.process_image(source_path, destination_path)
                else:
                    shutil.copy2(source_path, destination_path)

                update_file_list(file, "Sucesso")
                logging.info(f"Arquivo processado com sucesso: {file}")
                print(f"{Fore.GREEN}Sucesso: {file}{Style.RESET_ALL}")
            except Exception as e:
                error_msg = f"Erro ao processar {file}: {str(e)}"
                update_file_list(file, error_msg)
                logging.error(error_msg)
                print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")

            progress = int((i + 1) / total_files * 100)
            update_progress(progress)
            update_status(f"Processando: {file}")

        update_status("Processamento concluído")
        print(f"Log de processamento salvo em: {self.log_file}")

    def get_file_type(self, file_path):
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            main_type = mime_type.split('/')[0]
            if main_type == 'image':
                return "Imagens"
            elif main_type == 'video':
                return "Vídeos"
            elif main_type == 'audio':
                return "Áudios"
            elif 'pdf' in mime_type:
                return 'PDFs'
            elif 'text' in mime_type or 'document' in mime_type:
                return 'Documentos'
        return 'Outros'

    def process_image(self, source_path, destination_path):
        try:
            with Image.open(source_path) as img:
                # Redimensiona a imagem para um máximo de 1920x1080 pixels
                img.thumbnail((1920, 1080))
                # Salva a imagem com compressão
                img.save(destination_path, optimize=True, quality=85)
        except Exception as e:
            raise Exception(f"Erro ao processar imagem: {str(e)}")

    def get_destination_folder(self, file, structure, base_destination):
        for folder, patterns in structure.items():
            if any(file.lower().endswith(pat.lower()) for pat in patterns):
                return os.path.join(base_destination, folder)
        return os.path.join(base_destination, "Outros")

    def get_unique_filename(self, file_path):
        base, extension = os.path.splitext(file_path)
        counter = 1
        while os.path.exists(file_path):
            file_path = f"{base}_{counter}{extension}"
            counter += 1
        return file_path

    def save_progress(self, current_file, total_files, source, destination):
        progress_data = {
            "current_file": current_file,
            "total_files": total_files,
            "source": source,
            "destination": destination
        }
        progress_file = os.path.join(self.log_dir, "progress.json")
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f)
        print(f"Progresso salvo em: {progress_file}")

    def load_progress(self):
        progress_file = os.path.join(self.log_dir, "progress.json")
        if os.path.exists(progress_file):
            with open(progress_file, 'r') as f:
                return json.load(f)
        return None
