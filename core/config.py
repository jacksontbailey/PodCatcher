import os
import sys

from dotenv import load_dotenv, get_key


class Settings:
    def __init__(self) -> None:
        self._base_path = self._get_base_path()  # Get base path immediately

        self.dotenv_file = os.path.join(self._base_path, ".env")
        load_dotenv(self.dotenv_file)

        self.DRIVER_PATH = get_key(self.dotenv_file, "DRIVER_PATH")
        self.DRIVER_BASE_PATH = get_key(self.dotenv_file, "DRIVER_BASE_PATH")
        self.DEFAULT_PATH = get_key(self.dotenv_file, "DOWNLOAD_PATH")

        # - Replace these with the base path(s) for your user(s).
        self.ALICIA = get_key(self.dotenv_file, "ALICIA_BASE_PATH")
        self.JACKSON = get_key(self.dotenv_file, "JACKSON_BASE_PATH")

    def _get_base_path(self):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return base_path

    def resource_path(self, relative_path) -> str:
        """Returns the absolute path to a resource"""
        return os.path.join(self._base_path, relative_path)
    
PROJECT_SETTING = Settings()