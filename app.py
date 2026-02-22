import customtkinter as ctk
from tkinter import filedialog
import subprocess
import os
import threading
import urllib.request
import zipfile
import shutil
from sh_filter import filter_sh_level

ctk.set_appearance_mode("Dark")

class SharpWindowsApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sharp for Windows")
        self.geometry("450x480") # Made slightly taller for the progress bar
        self.filepath = None
        
        # Define isolated backend paths
        self.backend_dir = os.path.join(os.getcwd(), "backend_env")
        self.sharp_exe = os.path.join(self.backend_dir, "Scripts", "sharp.exe")

        # --- UI Setup ---
        self.label_status = ctk.CTkLabel(self, text="Checking dependencies...", text_color="yellow")
        self.label_status.pack(pady=(20, 5))

        # Progress Bar (Hidden by default)
        self.progress_bar = ctk.CTkProgressBar(self, width=300)
        self.progress_bar.set(0)
        # We don't pack it here so it remains invisible until needed

        self.btn_load = ctk.CTkButton(self, text="Select Image", command=self.load_image, state="disabled")
        self.btn_load.pack(pady=15)

        self.label_file = ctk.CTkLabel(self, text="No image selected")
        self.label_file.pack()

        self.label_sh = ctk.CTkLabel(self, text="Spherical Harmonics Level:")
        self.label_sh.pack(pady=(20, 0))
        
        self.sh_var = ctk.StringVar(value="3 (Default/High)")
        self.dropdown_sh = ctk.CTkOptionMenu(self, variable=self.sh_var, values=["0 (Base Color Only)", "1", "2", "3 (Default/High)"])
        self.dropdown_sh.pack(pady=10)

        self.btn_generate = ctk.CTkButton(self, text="Generate Splat", command=self.generate, state="disabled")
        self.btn_generate.pack(pady=20)

        # Trigger the first-run check when the app opens
        self.check_environment()

    def check_environment(self):
        if not os.path.exists(self.sharp_exe):
            self.label_status.configure(text="First run detected. Preparing to install ml-sharp...")
            self.progress_bar.pack(pady=5, after=self.label_status) # Show the progress bar
            # Run installation in the background
            threading.Thread(target=self.install_backend, daemon=True).start()
        else:
            self.label_status.configure(text="Ready to generate!", text_color="lightgreen")
            self.btn_load.configure(state="normal")
            self.btn_generate.configure(state="normal")

    def install_backend(self):
        try:
            c_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

            # 1. Check Python
            self.progress_bar.set(0.05)
            python_path = shutil.which("python")
            if not python_path:
                self.label_status.configure(text="Error: You must install Python to use this app!", text_color="red")
                return

            # 2. Download ml-sharp
            self.label_status.configure(text="Downloading ml-sharp from Apple...")
            url = "https://github.com/apple/ml-sharp/archive/refs/heads/main.zip"
            zip_path = "ml-sharp.zip"

            # Custom hook to track download progress
            def download_progress(count, block_size, total_size):
                if total_size > 0:
                    percent = min(1.0, (count * block_size) / total_size)
                    # Map download to 5% -> 40% of the overall progress bar
                    self.progress_bar.set(0.05 + (percent * 0.35))
                    self.update_idletasks() # Force UI refresh

            urllib.request.urlretrieve(url, zip_path, reporthook=download_progress)

            # 3. Extract the ZIP
            self.label_status.configure(text="Extracting files...")
            self.progress_bar.set(0.5)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip