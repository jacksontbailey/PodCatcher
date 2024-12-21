import os
import re
import requests
import shutil
import zipfile

def get_chrome_version():
    """Retrieve the installed Chrome version by checking the version directory."""
    chrome_path = r"C:\Program Files\Google\Chrome\Application"
    
    try:
        # List directories in the Chrome installation folder
        directories = os.listdir(chrome_path)
        
        # Use regex to find the version directory
        version_pattern = re.compile(r'^\d+\.\d+\.\d+\.\d+$')
        version_dirs = [d for d in directories if version_pattern.match(d)]
        
        if not version_dirs:
            raise RuntimeError("No version directory found for Chrome.")
        
        # Assume the latest version directory is the one with the highest version number
        latest_version_dir = max(version_dirs, key=lambda v: list(map(int, v.split('.'))))
        return latest_version_dir
    
    except Exception as e:
        raise RuntimeError(f"Error retrieving Chrome version: {e}")


class ChromeDriverUpdater:
    def __init__(self, download_dir, driver_path):
        self.download_dir = download_dir
        self.driver_path = driver_path
        self.base_url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"


    def get_latest_chromedriver_info(self):
        """Retrieve the latest ChromeDriver version info."""
        response = requests.get(self.base_url)
        data = response.json()
        return data['versions']


    def get_version_distance(self, version1, version2):
        """Calculate a numerical distance between two version strings."""
        v1_parts = list(map(int, version1.split('.')))
        v2_parts = list(map(int, version2.split('.')))
        # Normalize lengths by padding with zeros
        while len(v1_parts) < len(v2_parts):
            v1_parts.append(0)
        while len(v2_parts) < len(v1_parts):
            v2_parts.append(0)
        return sum(abs(a - b) for a, b in zip(v1_parts, v2_parts))


    def get_compatible_chromedriver_url(self, chrome_version):
        """Get the download URL for ChromeDriver compatible with the closest Chrome version."""
        versions = self.get_latest_chromedriver_info()
        closest_version = None
        min_distance = float('inf')
        
        for item in versions:
            version = item['version']
            distance = self.get_version_distance(chrome_version, version)
            if distance < min_distance:
                min_distance = distance
                closest_version = version
        
        if not closest_version:
            raise ValueError("No compatible ChromeDriver found for Chrome version.")
        
        # Find the download URL for the closest version
        for item in versions:
            if item['version'] == closest_version:
                for driver in item['downloads']['chromedriver']:
                    if driver['platform'] == 'win64':  # Assuming 'win64' platform; adjust as necessary
                        return driver['url']
        raise ValueError("No compatible ChromeDriver URL found for the closest version.")
                    

    def download_latest_driver(self, latest_version, download_url):
        """Download and update the ChromeDriver if compatible with installed Chrome."""
        try:
            zip_path = os.path.join(self.download_dir, "chromedriver.zip")

            # Download the zip file
            response = requests.get(download_url, stream=True)
            with open(zip_path, 'wb') as file:
                shutil.copyfileobj(response.raw, file)

            # Extract the zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.download_dir)

            # The extracted folder will have the name "chromedriver-win64"
            extracted_folder = os.path.join(self.download_dir, "chromedriver-win64")
            driver_executable = os.path.join(extracted_folder, "chromedriver.exe")  # Modify based on OS

            # Replace the old driver with the new one
            if os.path.exists(self.driver_path):
                os.remove(self.driver_path)
            shutil.move(driver_executable, self.driver_path)

        except Exception as e:
            print(f"Error during ChromeDriver download: {e}")


    def update_chromedriver(self):
        """Update ChromeDriver if necessary."""
        try:
            chrome_version = get_chrome_version()
            latest_chromedriver_url = self.get_compatible_chromedriver_url(chrome_version)
            # Extract the version from URL to use it in download method
            latest_version = latest_chromedriver_url.split('/')[-3]
            self.download_latest_driver(latest_version, latest_chromedriver_url)
        except Exception as e:
            print(f"Update failed: {e}")

# Example usage
if __name__ == "__main__":
    download_dir = "path_to_download_directory"
    driver_path = "path_to_existing_chromedriver.exe"
    updater = ChromeDriverUpdater(download_dir, driver_path)
    updater.update_chromedriver()
