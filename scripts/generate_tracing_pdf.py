import os
from fpdf import FPDF
from fpdf.enums import Align, XPos, YPos

# --- Configuration ---
# IMPORTANT: Ensure this path points to your downloaded Gujarati font file
#FONT_PATH = '/Users/apatel/Downloads/Noto_Sans_Gujarati/NotoSansGujarati-VariableFont_wdth,wght.ttf' # CHANGE IF NEEDED
FONT_PATH = '/Users/apatel/Downloads/Mukta_Vaani/MuktaVaani-Regular.ttf' # CHANGE IF NEEDED
FONT_NAME = 'NotoSansGujarati' # Logical name for the font in FPDF
OUTPUT_DIR = '../backend/static/tracing_sheets' # Relative to script location
PDF_FILENAME = 'gujarati_consonants_tracing_fpdf.pdf' # Changed filename slightly
FONT_SIZE = 60 # Size of the letters on the page (Reduced significantly)
TRACE_COLOR = (204, 204, 204) # RGB tuple for light gray (0-255)

# List of Gujarati Core Consonants (Vyanjan)
GUJARATI_CONSONANTS = [
    'ક', 'ખ', 'ગ', 'ઘ',
    'ચ', 'છ', 'જ', 'ઝ',
    'ટ', 'ઠ', 'ડ', 'ઢ', 'ણ',
    'ત', 'થ', 'દ', 'ધ', 'ન',
    'પ', 'ફ', 'બ', 'ભ', 'મ',
    'ય', 'ર', 'લ', 'વ',
    'શ', 'ષ', 'સ', 'હ', 'ળ',
    'ક્ષ', 'જ્ઞ' # Conjuncts added back
]

# Layout Configuration
PAGE_WIDTH_MM = 215.9 # Letter width in mm (8.5 inches)
PAGE_HEIGHT_MM = 279.4 # Letter height in mm (11 inches)
MARGIN_MM = 19.05 # 0.75 inches in mm
COLS = 6 # Number of columns for letters
ROWS = 6 # Number of rows for letters (Adjust if needed to fit all chars)
# --- End Configuration ---

def generate_tracing_pdf_fpdf():
    # Ensure output directory exists
    script_dir = os.path.dirname(__file__)
    output_path_dir = os.path.join(script_dir, OUTPUT_DIR)
    os.makedirs(output_path_dir, exist_ok=True)
    pdf_file_path = os.path.join(output_path_dir, PDF_FILENAME)

    # Create FPDF object (portrait, mm, Letter size)
    pdf = FPDF(orientation='P', unit='mm', format='Letter')
    pdf.set_auto_page_break(False) # We manage positioning manually
    pdf.add_page()

    # Add the Gujarati Unicode font
    try:
        # IMPORTANT: uni=True is essential for Unicode characters
        # pdf.add_font(FONT_NAME, '', FONT_PATH, uni=True)
        # Remove deprecated uni=True parameter
        pdf.add_font(FONT_NAME, '', FONT_PATH)
    except RuntimeError as e:
        print(f"Error: Could not add font at '{FONT_PATH}'.")
        print(f"Please ensure the path is correct and the file is a valid .ttf font.")
        print(f"FPDF error details: {e}")
        # Check if font file exists for a clearer message
        if not os.path.exists(FONT_PATH):
            print("Font file does not exist at the specified path.")
        return
    except Exception as e:
        print(f"An unexpected error occurred while adding the font: {e}")
        return

    print(f"Generating PDF: {pdf_file_path}")
    print(f"Using font: {FONT_PATH}")

    # Calculate usable area and cell dimensions in mm
    usable_width = PAGE_WIDTH_MM - 2 * MARGIN_MM
    usable_height = PAGE_HEIGHT_MM - 2 * MARGIN_MM
    cell_width = usable_width / COLS
    cell_height = usable_height / ROWS

    # Set font and color for tracing letters
    pdf.set_font(FONT_NAME, size=FONT_SIZE)
    pdf.set_text_color(TRACE_COLOR[0], TRACE_COLOR[1], TRACE_COLOR[2])

    # Draw the letters in a grid
    char_index = 0
    for r in range(ROWS):
        for col in range(COLS):
            if char_index >= len(GUJARATI_CONSONANTS):
                break

            char = GUJARATI_CONSONANTS[char_index]

            # Calculate top-left corner of the cell
            cell_x = MARGIN_MM + (col * cell_width)
            cell_y = MARGIN_MM + (r * cell_height)

            # Set position to the top-left of the cell for multi_cell
            pdf.set_xy(cell_x, cell_y)

            # Draw the character centered within the cell using multi_cell
            # multi_cell allows for alignment within a defined box
            # Use cell_height for height to allow vertical centering space
            # Align='C' centers horizontally. Vertical centering is approximated by the box.
            pdf.multi_cell(w=cell_width, h=cell_height, text=char, align=Align.C, new_x=XPos.RIGHT, new_y=YPos.TOP)

            char_index += 1

        if char_index >= len(GUJARATI_CONSONANTS):
            break

    # Add a simple title (optional)
    pdf.set_font("Helvetica", size=12) # Use a standard font for title
    pdf.set_text_color(0, 0, 0) # Black color
    pdf.set_y(MARGIN_MM / 2) # Position title near top margin
    pdf.cell(0, 10, "Gujarati Consonants Tracing Practice", align=Align.C)

    # Save the PDF
    try:
        pdf.output(pdf_file_path)
        print(f"Successfully generated {PDF_FILENAME} in {output_path_dir}")
    except Exception as e:
        print(f"Error saving PDF: {e}")

if __name__ == "__main__":
    # Basic check if font path seems valid (exists)
    if not os.path.exists(FONT_PATH):
         print(f"Warning: Font file not found at '{FONT_PATH}'.")
         print(f"Please edit script and set the correct font path.")
    else:
        generate_tracing_pdf_fpdf() 