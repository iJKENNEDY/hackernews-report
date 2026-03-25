from pypdf import PdfWriter
import os

def merge_pdfs(input_paths, output_path):
    """
    Une dos o más archivos PDF en uno solo.
    
    :param input_paths: Lista de rutas a los archivos PDF de entrada.
    :param output_path: Ruta del archivo PDF de salida.
    :return: True si fue exitoso, False en caso contrario.
    """
    if len(input_paths) < 2:
        raise ValueError("Se requieren al menos 2 archivos PDF para unir.")

    merger = PdfWriter()

    try:
        for pdf in input_paths:
            if not os.path.exists(pdf):
                raise FileNotFoundError(f"El archivo {pdf} no existe.")
            merger.append(pdf)

        with open(output_path, "wb") as output_file:
            merger.write(output_file)
        
        merger.close()
        return True
    except Exception as e:
        print(f"Error al unir PDFs: {e}")
        return False
