import customtkinter as ctk
from tkinter import filedialog
import subprocess
import os
import threading
import urllib.request
import zipfile
import shutil
import piexif
import open3d as o3d
from PIL import Image
from sh_filter import filter_sh_level

ctk.set_appearance_mode("Dark")

class SharpWindowsApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        # --- App Branding ---
        self.title("OPTEX Visual Systems | Image to Gaussian Splat Converter 1.0")
        self.geometry("450x680") 
        self.filepath = None
        
        # Define isolated backend paths
        self.backend_dir = os.path.join(os.getcwd(), "backend_env")
        self.sharp_exe = os.path.join(self.backend_dir, "Scripts", "sharp.exe")
        
        # The internal hidden file where the preview is temporarily stored
        self.preview_ply_path = os.path.join(self.backend_dir, "temp_preview.ply")

        # --- Set the Window Icon ---
        try:
            import sys
            if getattr(sys, 'frozen', False):
                self.iconbitmap(sys.executable) 
            else:
                self.iconbitmap("app.ico")
        except Exception:
            pass

        # --- UI Setup ---
        self.label_status = ctk.CTkLabel(self, text="Checking dependencies...", text_color="yellow")
        self.label_status.pack(pady=(20, 5))

        self.progress_bar = ctk.CTkProgressBar(self, width=300)
        self.progress_bar.set(0)

        self.btn_load = ctk.CTkButton(self, text="Select Image", command=self.load_image, state="disabled")
        self.btn_load.pack(pady=10)

        self.label_file = ctk.CTkLabel(self, text="No image selected")
        self.label_file.pack()

        # Focal Length Slider
        self.label_fl = ctk.CTkLabel(self, text="Focal Length (mm): 50")
        self.label_fl.pack(pady=(15, 0))
        
        self.slider_fl = ctk.CTkSlider(self, from_=10, to=150, command=self.update_fl_label)
        self.slider_fl.set(50)
        self.slider_fl.pack(pady=5)

        # Spherical Harmonics Dropdown
        self.label_sh = ctk.CTkLabel(self, text="Spherical Harmonics Level:")
        self.label_sh.pack(pady=(15, 0))
        
        self.sh_var = ctk.StringVar(value="3 (Default/High)")
        self.dropdown_sh = ctk.CTkOptionMenu(self, variable=self.sh_var, values=["0 (Base Color Only)", "1", "2", "3 (Default/High)"])
        self.dropdown_sh.pack(pady=5)

        # Generate Preview Button
        self.btn_preview = ctk.CTkButton(self, text="Generate Preview", command=self.generate_preview, state="disabled", fg_color="green", hover_color="darkgreen")
        self.btn_preview.pack(pady=15)

        # Export Button (Disabled until a preview is generated)
        self.btn_export = ctk.CTkButton(self, text="Export Final Splat", command=self.export_splat, state="disabled")
        self.btn_export.pack(pady=5)

        # --- Footer ---
        self.label_footer = ctk.CTkLabel(self, text="VC'd by Mike Flex (Gemini 3.1 CLI) 2026", text_color="gray", font=("Arial", 10))
        self.label_footer.pack(side="bottom", pady=15)

        self.check_environment()

    def update_fl_label(self, value):
        self.label_fl.configure(text=f"Focal Length (mm): {int(value)}")

    def check_environment(self):
        if not os.path.exists(self.sharp_exe):
            self.label_status.configure(text="First run detected. Setting up engine...")
            self.progress_bar.pack(pady=5, after=self.label_status) 
            threading.Thread(target=self.install_backend, daemon=True).start()
        else:
            self.label_status.configure(text="Ready to generate!", text_color="lightgreen")
            self.btn_load.configure(state="normal")
            self.btn_preview.configure(state="normal")

    def install_backend(self):
        try:
            c_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            self.progress_bar.set(0.05)

            python_path = shutil.which("python") or shutil.which("python3") or shutil.which("py")
            
            if not python_path:
                self.label_status.configure(text="Python missing. Downloading Python 3.11 silently...", text_color="yellow")
                self.progress_bar.configure(mode="indeterminate")
                self.progress_bar.start()
                
                installer_url = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
                installer_path = "python_installer.exe"
                urllib.request.urlretrieve(installer_url, installer_path)
                
                self.label_status.configure(text="Installing Python (This takes a minute)...")
                subprocess.run([installer_path, "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_test=0"], check=True, creationflags=c_flags)
                
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

            self.label_status.configure(text="Downloading ml-sharp from Apple...")
            url = "https://github.com/apple/ml-sharp/archive/refs/heads/main.zip"
            zip_path = "ml-sharp.zip"

            def download_progress(count, block_size, total_size):
                if total_size > 0:
                    percent = min(1.0, (count * block_size) / total_size)
                    self.progress_bar.set(0.05 + (percent * 0.35))
                    self.update_idletasks() 

            urllib.request.urlretrieve(url, zip_path, reporthook=download_progress)

            self.label_status.configure(text="Extracting files...")
            self.progress_bar.set(0.5)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(".")
            os.remove(zip_path)

            self.label_status.configure(text="Creating isolated AI environment...")
            self.progress_bar.set(0.6)
            subprocess.run([python_path, "-m", "venv", "backend_env"], check=True, creationflags=c_flags)

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
            self.btn_preview.configure(state="normal")

        except Exception as e:
            self.progress_bar.stop()
            self.label_status.configure(text=f"Install Error: {str(e)}", text_color="red")

    def load_image(self):
        self.filepath = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.heic")])
        if self.filepath:
            self.label_file.configure(text=os.path.basename(self.filepath))
            self.btn_export.configure(state="disabled")

    def inject_exif_focal_length(self, source_path, dest_path, focal_length_mm):
        img = Image.open(source_path)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        try:
            exif_dict = piexif.load(img.info.get("exif", b""))
        except Exception:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

        exif_dict["Exif"][piexif.ExifIFD.FocalLength] = (int(focal_length_mm * 10), 10)
        exif_bytes = piexif.dump(exif_dict)
        
        img.save(dest_path, "jpeg", exif=exif_bytes)

    def generate_preview(self):
        if not self.filepath:
            return
            
        self.btn_preview.configure(text="Generating...", state="disabled")
        self.btn_export.configure(state="disabled")
        self.label_status.configure(text="Running Apple SHARP model...", text_color="yellow")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.pack(pady=5, after=self.label_status)
        self.progress_bar.start()
        self.update()

        def run_generation():
            output_dir = os.path.dirname(self.filepath)
            temp_out_dir = os.path.join(output_dir, "sharp_temp_workspace")
            temp_img = os.path.join(output_dir, "temp_sharp_input.jpg")
            c_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

            try:
                # --- SSL Bypass ---
                site_packages = os.path.join(self.backend_dir, "Lib", "site-packages")
                site_customize = os.path.join(site_packages, "sitecustomize.py")
                if os.path.exists(site_packages) and not os.path.exists(site_customize):
                    with open(site_customize, "w") as f:
                        f.write("import ssl\n")
                        f.write("try:\n")
                        f.write("    ssl._create_default_https_context = ssl._create_unverified_context\n")
                        f.write("except AttributeError:\n")
                        f.write("    pass\n")

                os.makedirs(temp_out_dir, exist_ok=True)
                
                selected_fl = self.slider_fl.get()
                self.inject_exif_focal_length(self.filepath, temp_img, selected_fl)

                result = subprocess.run(
                    [self.sharp_exe, "predict", "-i", temp_img, "-o", temp_out_dir], 
                    capture_output=True, text=True, creationflags=c_flags
                )
                
                if result.returncode != 0:
                    error_text = result.stderr.strip()[-300:] 
                    raise RuntimeError(f"ml-sharp crash:\n{error_text}")
                
                generated_ply = None
                for file in os.listdir(temp_out_dir):
                    if file.endswith(".ply"):
                        generated_ply = os.path.join(temp_out_dir, file)
                        break
                        
                if not generated_ply:
                    raise FileNotFoundError("ml-sharp finished, but no .ply was found.")
                
                selected_level = int(self.sh_var.get()[0])
                
                # Save to the internal preview path instead of asking the user
                filter_sh_level(generated_ply, self.preview_ply_path, selected_level)
                
                if os.path.exists(temp_img): os.remove(temp_img)
                shutil.rmtree(temp_out_dir, ignore_errors=True)
                    
                self.label_status.configure(text="Preview generated! Check the 3D window.", text_color="lightgreen")
                
                # Automatically pop open the 3D viewer
                self.show_3d()

                # Enable the Export button now that a preview exists
                self.btn_export.configure(state="normal")
                
            except Exception as e:
                self.label_status.configure(text=f"Error: {str(e)}", text_color="red")

            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.btn_preview.configure(text="Generate Preview", state="normal")

        threading.Thread(target=run_generation, daemon=True).start()

    def show_3d(self):
        if not os.path.exists(self.preview_ply_path):
            return
            
        def launch_viewer():
            try:
                pcd = o3d.io.read_point_cloud(self.preview_ply_path)
                o3d.visualization.draw_geometries([pcd], window_name="Splat Preview - Close window to continue", width=1024, height=768)
            except Exception as e:
                print(f"Preview Error: {e}")
            
        threading.Thread(target=launch_viewer, daemon=True).start()

    def export_splat(self):
        if not os.path.exists(self.preview_ply_path):
            return
            
        save_path = filedialog.asksaveasfilename(
            defaultextension=".ply",
            filetypes=[("3D Gaussian Splat", "*.ply")],
            title="Export Final Splat As",
            initialfile="my_splat.ply"
        )
        
        if save_path:
            try:
                shutil.copy(self.preview_ply_path, save_path)
                self.label_status.configure(text=f"Exported successfully to {os.path.basename(save_path)}!", text_color="lightgreen")
            except Exception as e:
                self.label_status.configure(text=f"Export Error: {str(e)}", text_color="red")

if __name__ == "__main__":
    app = SharpWindowsApp()
    app.mainloop()