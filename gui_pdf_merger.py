import tkinter as tk
from tkinter import filedialog, messagebox, listbox
from src.utils.pdf_service import merge_pdfs
import os

class PDFMergerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hacker News Report - PDF Merger GUI")
        self.root.geometry("600x450")
        self.root.configure(bg="#f3f4f6")
        
        self.pdf_list = []
        
        self.setup_ui()

    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#ff6600", height=60)
        header.pack(fill="x")
        tk.Label(header, text="Unir Archivos PDF", bg="#ff6600", fg="white", font=("Arial", 16, "bold")).pack(pady=15)
        
        # Main Content
        main_frame = tk.Frame(self.root, bg="#f3f4f6", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Listbox for selected files
        tk.Label(main_frame, text="Archivos seleccionados:", bg="#f3f4f6", font=("Arial", 10, "bold")).pack(anchor="w")
        
        self.listbox = listbox.Listbox(main_frame, selectmode=tk.MULTIPLE, height=10, font=("Arial", 9))
        self.listbox.pack(fill="both", expand=True, pady=10)
        
        # Buttons Container
        btn_frame = tk.Frame(main_frame, bg="#f3f4f6")
        btn_frame.pack(fill="x", pady=10)
        
        tk.Button(btn_frame, text="Agregar PDFs", command=self.add_files, bg="#1e293b", fg="white", padx=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Quitar Seleccionados", command=self.remove_files, bg="#ef4444", fg="white", padx=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Limpiar Todo", command=self.clear_all, bg="#64748b", fg="white", padx=10).pack(side="left", padx=5)
        
        # Merge Action Button
        tk.Button(self.root, text="UNIR Y GUARDAR", command=self.process_merge, bg="#22c55e", fg="white", font=("Arial", 12, "bold"), pady=10).pack(fill="x", side="bottom")

    def add_files(self):
        files = filedialog.askopenfilenames(title="Selecciona archivos PDF", filetypes=[("Archivos PDF", "*.pdf")])
        if files:
            for f in files:
                if f not in self.pdf_list:
                    self.pdf_list.append(f)
                    self.listbox.insert(tk.END, os.path.basename(f))

    def remove_files(self):
        selected = self.listbox.curselection()
        for index in reversed(selected):
            self.pdf_list.pop(index)
            self.listbox.delete(index)

    def clear_all(self):
        self.pdf_list = []
        self.listbox.delete(0, tk.END)

    def process_merge(self):
        if len(self.pdf_list) < 2:
            messagebox.showwarning("Atención", "Selecciona al menos 2 archivos PDF para unir.")
            return
            
        output_file = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivo PDF", "*.pdf")],
            title="Guardar PDF unido como..."
        )
        
        if output_file:
            try:
                success = merge_pdfs(self.pdf_list, output_file)
                if success:
                    messagebox.showinfo("Éxito", f"Archivo creado exitosamente en:\n{output_file}")
                    self.clear_all()
                else:
                    messagebox.showerror("Error", "Hubo un problema al unir los archivos.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFMergerGUI(root)
    root.mainloop()
