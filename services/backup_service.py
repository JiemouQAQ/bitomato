import os
import zipfile
import datetime
import sys
import json
from services.config_service import ConfigService

class BackupService:
    def __init__(self, config):
        self.config = config
        self.root_dir = os.getcwd()
        self.backup_dir = os.path.join(self.root_dir, "backups")
        if not os.path.exists(self.backup_dir):
            try:
                os.makedirs(self.backup_dir)
            except Exception:
                pass

    def manual_backup(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}.zip"
        return self._create_zip(filename)

    def auto_backup(self):
        if self.is_auto_backup_enabled():
            return self._create_zip("auto_backup.zip")

    def _create_zip(self, filename):
        try:
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir)
            
            zip_path = os.path.join(self.backup_dir, filename)
            files_to_backup = ["stats.json", "config.json"]
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 1. Backup stats and config
                for file in files_to_backup:
                    file_path = os.path.join(self.root_dir, file)
                    if os.path.exists(file_path):
                        zipf.write(file_path, file)
                
                # 2. Backup current skin
                skin_id = self.config.get("skinId", "default")
                if os.path.isabs(skin_id):
                    skin_dir = skin_id
                else:
                    skin_dir = os.path.join(self.root_dir, "skins", skin_id)
                
                if os.path.exists(skin_dir) and os.path.isdir(skin_dir):
                    skin_base_name = os.path.basename(skin_dir)
                    for root, dirs, files in os.walk(skin_dir):
                        for file in files:
                            # Filter only image files and json metadata to be safe/clean
                            if file.lower().endswith('.png') or file.lower().endswith('.ico') or file.lower().endswith('.json'):
                                full_path = os.path.join(root, file)
                                # Preserve relative structure inside zip under "skin_backup/<skin_name>/"
                                rel_path = os.path.relpath(full_path, skin_dir)
                                arcname = os.path.join("skin_backup", skin_base_name, rel_path)
                                zipf.write(full_path, arcname)

            return zip_path
        except Exception as e:
            print(f"Backup failed: {e}")
            return None

    def import_backup(self, zip_path, stats_service):
        try:
            if not os.path.exists(zip_path):
                return False, "文件不存在"
            
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                # 1. Restore stats
                if "stats.json" not in zipf.namelist():
                    return False, "备份文件中未找到统计数据"
                
                with zipf.open("stats.json") as f:
                    data = json.load(f)
                    if not stats_service.import_data(data):
                        return False, "数据格式错误"

                # 1.1 Restore config (specifically textColor and outline settings)
                if "config.json" in zipf.namelist():
                    try:
                        with zipf.open("config.json") as f:
                            cfg = json.load(f)
                            updated = False
                            if "textColor" in cfg:
                                self.config["textColor"] = cfg["textColor"]
                                updated = True
                            if "textOutlineEnabled" in cfg:
                                self.config["textOutlineEnabled"] = cfg["textOutlineEnabled"]
                                updated = True
                            if "textOutlineColor" in cfg:
                                self.config["textOutlineColor"] = cfg["textOutlineColor"]
                                updated = True
                            if "textOutlineWidth" in cfg:
                                self.config["textOutlineWidth"] = cfg["textOutlineWidth"]
                                updated = True
                                
                            if updated:
                                ConfigService.save(self.config)
                    except Exception:
                        pass

                # 2. Restore skin if exists
                skin_files = [f for f in zipf.namelist() if f.startswith("skin_backup/")]
                if skin_files:
                    # Extract first folder name under skin_backup
                    # Structure: skin_backup/<skin_name>/...
                    first_file = skin_files[0]
                    parts = first_file.split('/')
                    if len(parts) >= 2:
                        skin_name = parts[1]
                        if skin_name:
                            target_skin_dir = os.path.join(self.root_dir, "skins", skin_name)
                            
                            # Extract files
                            for file in skin_files:
                                # Skip directory entries
                                if file.endswith('/'):
                                    continue
                                    
                                # Reconstruct path: skins/<skin_name>/<filename>
                                # file is like "skin_backup/<skin_name>/skin_001.png"
                                # rel_path is "skin_001.png"
                                rel_path = file.split('/', 2)[-1] 
                                target_path = os.path.join(target_skin_dir, rel_path)
                                
                                target_dir = os.path.dirname(target_path)
                                if not os.path.exists(target_dir):
                                    os.makedirs(target_dir)
                                    
                                with zipf.open(file) as source, open(target_path, "wb") as target:
                                    target.write(source.read())
                            
                            # Update config to use this skin
                            self.config["skinId"] = skin_name
                            ConfigService.save(self.config)

            return True, "导入成功"
        except json.JSONDecodeError:
            return False, "JSON文件损坏"
        except Exception as e:
            return False, str(e)

    def is_auto_backup_enabled(self):
        return self.config.get("autoBackup", False)

    def set_auto_backup_enabled(self, enabled: bool):
        self.config["autoBackup"] = enabled
        ConfigService.save(self.config)

    def open_backup_folder(self):
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        
        if sys.platform == 'win32':
            os.startfile(self.backup_dir)
