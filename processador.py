import os
import shutil
import logging
import hashlib
from datetime import datetime

class FileProcessor:
    def __init__(self):
        self.logger = self.setup_logger()
        
    def setup_logger(self):
        logger = logging.getLogger("FileProcessor")
        logger.setLevel(logging.INFO)
        
        log_dir = os.path.expanduser("~/OrganizadorLogs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"processamento_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        return logger

    def calculate_total_files(self, sources):
        total = 0
        for source in sources:
            for root, _, files in os.walk(source):
                total += len(files)
        return total

    def process_file(self, file_path, root, source, model, destination):
        try:
            file_name = os.path.basename(file_path)
            rel_path = os.path.relpath(root, source)
            dest_dir = os.path.join(destination, rel_path)
            dest_path = os.path.join(dest_dir, file_name)

            os.makedirs(dest_dir, exist_ok=True)

            # Verifica duplicados
            if os.path.exists(dest_path):
                if self.file_hash(file_path) == self.file_hash(dest_path):
                    return {
                        'status': 'skipped',
                        'message': 'Arquivo duplicado - conteúdo idêntico'
                    }
                dest_path = self.generate_unique_name(dest_path)

            shutil.copy2(file_path, dest_path)
            
            self.logger.info(f"Arquivo processado: {file_path} -> {dest_path}")
            return {
                'status': 'success',
                'message': f"Arquivo movido para: {dest_path}"
            }

        except Exception as e:
            self.logger.error(f"Erro ao processar {file_path}: {str(e)}")
            return {
                'status': 'error',
                'message': f"Erro: {str(e)}"
            }

    def file_hash(self, file_path):
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def generate_unique_name(self, path):
        base, ext = os.path.splitext(path)
        counter = 1
        while os.path.exists(path):
            path = f"{base}_{counter}{ext}"
            counter += 1
        return path