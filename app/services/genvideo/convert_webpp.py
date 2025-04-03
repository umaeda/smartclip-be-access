import os
from PIL import Image

def convert_webp_to_png(input_dir, output_dir):
    """
    Converts all .webp files in the input directory to .png format
    and saves them in the output directory with the same name.

    Parameters:
    - input_dir (str): Path to the input directory containing .webp files.
    - output_dir (str): Path to the output directory to save .png files.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.webp'):
            input_path = os.path.join(input_dir, filename)
            output_filename = os.path.splitext(filename)[0] + '.png'
            output_path = os.path.join(output_dir, output_filename)

            try:
                with Image.open(input_path) as img:
                    img.convert('RGBA').save(output_path, 'PNG')
                print(f"Converted: {filename} -> {output_filename}")
            except Exception as e:
                print(f"Failed to convert {filename}: {e}")

# Example usage
input_directory = "C:\\Users\\ulisses.maeda\\OneDrive - ENFORCE GESTAO DE ATIVOS S.A\\Documents\\redesocial\\"  # Replace with your input directory
output_directory = "C:\\Users\\ulisses.maeda\\OneDrive - ENFORCE GESTAO DE ATIVOS S.A\\Documents\\redesocial\\"  # Replace with your output directory

convert_webp_to_png(input_directory, output_directory)
