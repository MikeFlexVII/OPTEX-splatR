import customtkinter as ctk
from tkinter import filedialog
import subprocess
import os
from sh_filter import filter_sh_level

ctk.set_appearance_mode("Dark")

class SharpWindowsApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sharp for Windows")
        self.geometry("450x350")
        self.filepath = None

        self.btn_load = ctk.CTkButton(self, text="Select Image", command=self.load_image)
        self.btn_load.pack(pady=20)

        self.label_file = ctk.CTkLabel(self, text="No image selected")
        self.label_file.pack()

        self.label_sh = ctk.CTkLabel(self, text="Spherical Harmonics Level:")
        self.label_sh.pack(pady=(20, 0))
        
        self.sh_var = ctk.StringVar(value="3 (Default/High)")
        self.dropdown_sh = ctk.CTkOptionMenu(self, variable=self.sh_var, values=["0 (Base Color Only)", "1", "2", "3 (Default/High)"])
        self.dropdown_sh.pack(pady=10)

        self.btn_generate = ctk.CTkButton(self, text="Generate Splat", command=self.generate)
        self.btn_generate.pack(pady=20)

    def load_image(self):
        self.filepath = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if self.filepath:
            self.label_file.configure(text=os.path.basename(self.filepath))

    def generate(self):
        if not self.filepath:
            return
        
        self.btn_generate.configure(text="Generating...", state="disabled")
        self.update()

        output_dir = os.path.dirname(self.filepath)
        temp_ply = os.path.join(output_dir, "temp_output.ply")
        final_ply = os.path.join(output_dir, "final_splat.ply")

        # Call the ml-sharp CLI
        try:
            subprocess.run(["sharp", self.filepath, "--output", temp_ply], check=True)
            selected_level = int(self.sh_var.get()[0])
            filter_sh_level(temp_ply, final_ply, selected_level)
            
            if os.path.exists(temp_ply):
                os.remove(temp_ply)
                
            self.label_file.configure(text="Done! Saved as final_splat.ply")
        except Exception as e:
            self.label_file.configure(text=f"Error: {str(e)}")

        self.btn_generate.configure(text="Generate Splat", state="normal")

if __name__ == "__main__":
    app = SharpWindowsApp()
    app.mainloop()