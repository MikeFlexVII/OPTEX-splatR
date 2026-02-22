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
        self.geometry("450x480") 
        self.filepath = None
        
        # --- Set the Window Icon ---
        try:
            import sys
            if getattr(sys, 'frozen', False):
                self.iconbitmap(sys.executable) 
            else:
                self.iconbitmap("app.ico")
        except Exception:
            pass
        
        # Define isolated backend paths
        self.backend_dir = os.path.join(os.getcwd(), "backend_env")
        self.sharp_exe = os.path.join(self.backend_dir, "Scripts", "sharp.exe")

        # --- UI Setup ---
        self.label_status = ctk.CTkLabel(self, text="Checking dependencies...", text_color="yellow")
        self.label_status.pack(pady=(20, 5))

        self.progress_bar = ctk.CTkProgressBar(self, width=300)
        self.progress_bar.set(0)

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

        self.check_environment()

    def check_environment(self):
        if not os.path.exists(self.sharp_exe):
            self.label_status.configure(text="First run detected. Setting up engine...")
            self.progress_bar.pack(pady=5, after=self.label_status) 
            threading.Thread(target=self.install_backend, daemon=True).start()
        else:
            self.label_status.configure(text="Ready to generate!", text_color="lightgreen")
            self.btn_load.configure(state="normal")
            self.btn_generate.configure(state="normal")

    def install_backend(self):
        try:
            c_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            self.progress_bar.set(0.05)

            # 1. Smart Python Detection
            python_path = shutil.which("python") or shutil.which("python3") or shutil.which("py")
            
            # 2. Auto-Install Python if missing
            if not python_path:
                self.label_status.configure(text="Python missing. Downloading Python 3.11 silently...", text_color="yellow")
                self.progress_bar.configure(mode="indeterminate")
                self.progress_bar.start()
                
                installer_url = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
                installer_path = "python_installer.exe"
                urllib.request.urlretrieve(installer_url, installer_path)
                
                self.label_status.configure(text="Installing Python (This takes a minute)...")
                # Run installer silently for the current user only (No Admin/UAC prompts!)
                subprocess.run([installer_path, "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_test=0"], check=True, creationflags=c_flags)
                
                # Locate the freshly installed Python
                user_profile = os.environ.get('USERPROFILE', '')
                fresh_python = os.path.join(user_profile, 'AppData', 'Local', 'Programs', 'Python', 'Python311', 'python.exe')
                
                if os.path.exists(fresh_python):
                    python_path = fresh_python
                else:
                    self.label_status.configure(text="Error: Could not locate installed Python.", text_color="red")
                    self.progress_bar.stop()
                    return
                    
                if os.path.exists(installer_path):
                    os.remove(installer_path)
                
                self.progress_bar.stop()
                self.progress_bar.configure(mode="determinate")

            # 3. Download ml-sharp
            self.label_status.configure(text="Downloading ml-sharp from Apple...")
            url = "https://github.com/apple/ml-sharp/archive/refs/heads/main.zip"
            zip_path = "ml-sharp.zip"

            def download_progress(count, block_size, total_size):
                if total_size > 0:
                    percent = min(1.0, (count * block_size) / total_size)
                    self.progress_bar.set(0.05 + (percent * 0.35))
                    self.update_idletasks() 

            urllib.request.urlretrieve(url, zip_path, reporthook=download_progress)

            # 4. Extract the ZIP
            self.label_status.configure(text="Extracting files...")
            self.progress_bar.set(0.5)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(".")
            os.remove(zip_path)

            # 5. Create venv
            self.label_status.configure(text="Creating isolated AI environment...")
            self.progress_bar.set(0.6)
            subprocess.run([python_path, "-m", "venv", "backend_env"], check=True, creationflags=c_flags)

            # 6. Install PyTorch & Dependencies
            self.label_status.configure(text="Installing PyTorch & AI Dependencies (5-10 mins)...")
            self.progress_bar.configure(mode="indeterminate") 
            self.progress_bar.start() 
            
            pip_exe = os.path.join(self.backend_dir, "Scripts", "pip.exe")
            subprocess.run([pip_exe, "install", "./ml-sharp-main"], check=True, creationflags=c_flags)

            shutil.rmtree("ml-sharp-main", ignore_errors=True)

            self.progress_bar.stop()
            self.progress_bar.pack_forget() 
            self.label_status.configure(text="Installation complete! Ready to generate.", text_color="lightgreen")
            self.btn_load.configure(state="normal")
            self.btn_generate.configure(state="normal")

        except Exception as e:
            self.progress_bar.stop()
            self.label_status.configure(text=f"Install Error: {str(e)}", text_color="red")

    def load_image(self):
        self.filepath = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.heic")])
        if self.filepath:
            self.label_file.configure(text=os.path.basename(self.filepath))

    def generate(self):
        if not self.filepath:
            return
        
        self.btn_generate.configure(text="Generating...", state="disabled")
        self.label_status.configure(text="Running Apple SHARP model...", text_color="yellow")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.pack(pady=5, after=self.label_status)
        self.progress_bar.start()
        self.update()

        def run_generation():
            output_dir = os.path.dirname(self.filepath)
            temp_ply = os.path.join(output_dir, "temp_output.ply")
            final_ply = os.path.join(output_dir, "final_splat.ply")
            c_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

            try:
                subprocess.run([self.sharp_exe, self.filepath, "--output", temp_ply], check=True, creationflags=c_flags)
                
                selected_level = int(self.sh_var.get()[0])
                filter_sh_level(temp_ply, final_ply, selected_level)
                
                if os.path.exists(temp_ply):
                    os.remove(temp_ply)
                    
                self.label_status.configure(text="Done! Saved as final_splat.ply", text_color="lightgreen")
            except Exception as e:
                self.label_status.configure(text=f"Error: {str(e)}", text_color="red")

            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.btn_generate.configure(text="Generate Splat", state="normal")

        threading.Thread(target=run_generation, daemon=True).start()

if __name__ == "__main__":
    app = SharpWindowsApp()
    app.mainloop()