import os
from PIL import Image, ImageDraw, ImageFont

# --- Configuration ---
# IMPORTANT: Update this path to your downloaded Gujarati font file
FONT_PATH = '/Users/apatel/Downloads/Noto_Sans_Gujarati/NotoSansGujarati-VariableFont_wdth,wght.ttf' # CHANGE THIS
OUTPUT_DIR = '../backend/static/gujarati_letters' # Relative to script location
IMAGE_SIZE = (300, 300) # Width, Height in pixels
GUJ_FONT_SIZE = 180 # Adjust as needed to fit the letter nicely
ENG_FONT_SIZE = 40  # Font size for the English pronunciation
VERTICAL_PADDING = 10 # Space between Gujarati char and English text
BACKGROUND_COLOR = (255, 255, 255, 0) # Transparent background (RGBA)
TEXT_COLOR = (0, 0, 0, 255) # Black text (RGBA)
BOTTOM_LEFT_PADDING = 30 # Padding from bottom-left corner (Increased from 15)

# List of Gujarati Characters (Consonants and Vowels)
GUJARATI_CHARS = [
    # Vowels (Svar)
    'અ', 'આ', 'ઇ', 'ઈ', 'ઉ', 'ઊ', 'ઋ', 'એ', 'ઐ', 'ઓ', 'ઔ',
    # Consonants (Vyanjan)
    'ક', 'ખ', 'ગ', 'ઘ', # 'ઙ', # Uncomment if needed
    'ચ', 'છ', 'જ', 'ઝ', # 'ઞ', # Uncomment if needed
    'ટ', 'ઠ', 'ડ', 'ઢ', 'ણ',
    'ત', 'થ', 'દ', 'ધ', 'ન',
    'પ', 'ફ', 'બ', 'ભ', 'મ',
    'ય', 'ર', 'લ', 'વ',
    'શ', 'ષ', 'સ', 'હ',
    'ળ', 'ક્ષ', 'જ્ઞ'
]

# Pronunciation Mapping (Adjust as needed)
PRONUNCIATION_MAP = {
    'અ': 'A', 'આ': 'Aa', 'ઇ': 'I', 'ઈ': 'Ee', 'ઉ': 'U', 'ઊ': 'Oo',
    'ઋ': 'Ri', 'એ': 'E', 'ઐ': 'Ai', 'ઓ': 'O', 'ઔ': 'Au',
    # 'અં': 'An', 'અઃ': 'Ah', # Not currently in GUJARATI_CHARS
    'ક': 'Ka', 'ખ': 'Kha', 'ગ': 'Ga', 'ઘ': 'Gha', # 'ઙ': 'Na',
    'ચ': 'Cha', 'છ': 'Chha', 'જ': 'Ja', 'ઝ': 'Jha', # 'ઞ': 'ña',
    'ટ': 'Ta', 'ઠ': 'Tha', 'ડ': 'Da', 'ઢ': 'Dha', 'ણ': 'Na',
    'ત': 'Ta', 'થ': 'Tha', 'દ': 'Da', 'ધ': 'Dha', 'ન': 'Na',
    'પ': 'Pa', 'ફ': 'Pha', 'બ': 'Ba', 'ભ': 'Bha', 'મ': 'Ma',
    'ય': 'Ya', 'ર': 'Ra', 'લ': 'La', 'વ': 'Va',
    'શ': 'Sha', 'ષ': 'Sha', 'સ': 'Sa', 'હ': 'Ha',
    'ળ': 'La', 'ક્ષ': 'Ksha', 'જ્ઞ': 'Gnya'
}
# --- End Configuration ---

def generate_images():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load the fonts
    try:
        guj_font = ImageFont.truetype(FONT_PATH, GUJ_FONT_SIZE)
        eng_font = ImageFont.truetype(FONT_PATH, ENG_FONT_SIZE) # Assuming same font works for English
    except IOError:
        print(f"Error: Font file not found at '{FONT_PATH}'.")
        print("Please download a Gujarati .ttf font (e.g., Noto Sans Gujarati)")
        print("and update the FONT_PATH variable in this script.")
        return
    except OSError:
        print(f"Warning: Could not load font '{FONT_PATH}' for English text.")
        print("Pronunciation text might not render correctly.")
        # Optionally, define a fallback or ask for a separate English font path
        try:
            # Try loading a system default if available (may vary)
            eng_font = ImageFont.truetype("arial.ttf", ENG_FONT_SIZE)
            print("Using system 'arial.ttf' for English text as fallback.")
        except IOError:
             print("Could not load fallback font. English text will be missing.")
             eng_font = None # Ensure eng_font exists even if loading fails


    print(f"Generating {len(GUJARATI_CHARS)} images in '{OUTPUT_DIR}'...")

    for char in GUJARATI_CHARS:
        pronunciation_eng = PRONUNCIATION_MAP.get(char)
        pronunciation_display = ""
        if pronunciation_eng and eng_font:
            pronunciation_display = pronunciation_eng # Just the English pronunciation
        elif not pronunciation_eng:
             print(f"Warning: No pronunciation found for '{char}'. Skipping pronunciation text.")
             # Decide if you want to generate the image without pronunciation or skip entirely
             # continue # Uncomment to skip images without pronunciation

        # Create a new transparent image
        img = Image.new('RGBA', IMAGE_SIZE, BACKGROUND_COLOR)
        draw = ImageDraw.Draw(img)

        # --- Calculate positions ---
        # Get bounding boxes
        try:
            # Pillow >= 9.x.x
            guj_bbox = draw.textbbox((0, 0), char, font=guj_font)
            guj_width = guj_bbox[2] - guj_bbox[0]
            guj_height = guj_bbox[3] - guj_bbox[1]
            guj_y_offset = guj_bbox[1] # Offset from top for the Gujarati char

            eng_width, eng_height, eng_y_offset = 0, 0, 0
            if pronunciation_display and eng_font:
                eng_bbox = draw.textbbox((0,0), pronunciation_display, font=eng_font)
                eng_width = eng_bbox[2] - eng_bbox[0]
                # For positioning, we need the height from baseline to bottom
                eng_descent = eng_font.getmetrics()[1] # Get font descent
                eng_height_total = eng_bbox[3] - eng_bbox[1] # Total height including ascenders/descenders
                eng_ascent = eng_height_total - eng_descent # Approximate ascent+main height
                eng_y_offset = eng_bbox[1] # Offset from top for the Eng char

        except AttributeError:
            # Older Pillow < 9.x.x - Metrics are less accurate
            guj_width, guj_height = draw.textsize(char, font=guj_font)
            guj_y_offset = 0 # Approximation

            eng_width, eng_height_total = 0, 0
            if pronunciation_display and eng_font:
                 eng_width, eng_height_total = draw.textsize(pronunciation_display, font=eng_font)
            # Cannot easily get descent in older Pillow, approximate using total height
            eng_ascent = eng_height_total
            eng_y_offset = 0 # Approximation


        # --- Calculate top-left corner positions ---

        # Position for Gujarati Character (Centered Horizontally, Vertically centered in upper area)
        # Adjust vertical centering to account for text potentially at the bottom
        available_height_for_guj = IMAGE_SIZE[1] # Consider full height for now, adjust if needed
        guj_x = (IMAGE_SIZE[0] - guj_width) / 2
        # Center it slightly higher than absolute center maybe?
        # Let's try centering it within the top 80% of the image space.
        vertical_center_area = IMAGE_SIZE[1] * 0.8
        guj_y = (vertical_center_area - guj_height) / 2 - guj_y_offset

        # Position for English Pronunciation (Bottom-Center)
        # eng_x = BOTTOM_LEFT_PADDING # Old bottom-left positioning
        eng_x = (IMAGE_SIZE[0] - eng_width) / 2 if pronunciation_display and eng_font else 0 # Centered horizontally
        # Position using ascent, not total height, relative to bottom padding
        eng_y = IMAGE_SIZE[1] - eng_ascent - BOTTOM_LEFT_PADDING - eng_y_offset


        # --- Draw the texts ---
        # Draw Gujarati character
        draw.text((guj_x, guj_y), char, font=guj_font, fill=TEXT_COLOR)

        # Draw English pronunciation if available and font loaded
        if pronunciation_display and eng_font:
            draw.text((eng_x, eng_y), pronunciation_display, font=eng_font, fill=TEXT_COLOR)


        # Save the image
        file_name = f"{char}.png"
        file_path = os.path.join(OUTPUT_DIR, file_name)
        img.save(file_path)

    print("Image generation complete.")

if __name__ == "__main__":
    # Basic check if font path was updated
    if 'path/to/your/font' in FONT_PATH: # Made check more generic
         print("Warning: FONT_PATH might not have been updated in the script.")
         print("Please edit 'scripts/generate_letter_images.py' and set the correct path to your font file.")
    else:
        generate_images() 