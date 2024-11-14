
import os
import shutil
import mimetypes
from PIL import Image
from tqdm import tqdm
from colorama import Fore, Style

class FileProcessor:
    def process_files(self, source, destination, update_progress, update_status, update_file_list):
        files = [f for f in os.listdir(source) if os.path.isfile(os.path.join(source, f))]
        total_files = len(files)

        for i, file in enumerate(tqdm(files, desc="Processando arquivos", unit="arquivo")):
            source_path = os.path.join(source, file)
            file_type = self.get_file_type(source_path)
            dest_folder = os.path.join(destination, file_type)
            os.makedirs(dest_folder, exist_ok=True)
            destination_path = os.path.join(dest_folder, file)
            
            try:
                if file_type == "Imagens":
                    self.process_image(source_path, destination_path)
                else:
                    shutil.copy2(source_path, destination_path)
                update_file_list(file, "Sucesso")
                print(f"{Fore.GREEN}Sucesso: {file}{Style.RESET_ALL}")
            except Exception as e:
                error_msg = f"Erro ao processar {file}: {str(e)}"
                update_file_list(file, error_msg)
                print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
            
            progress = int((i + 1) / total_files * 100)
            update_progress(progress)
            update_status(f"Processando: {file}")

        update_status("Processamento concluído")

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
