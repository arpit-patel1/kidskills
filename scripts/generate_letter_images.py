import os
from PIL import Image, ImageDraw, ImageFont

# --- Configuration ---
# IMPORTANT: Update this path to your downloaded Gujarati font file
FONT_PATH = '/Users/apatel/Downloads/Noto_Sans_Gujarati/NotoSansGujarati-VariableFont_wdth,wght.ttf' # CHANGE THIS
OUTPUT_DIR = '../backend/static/gujarati_letters' # Relative to script location
IMAGE_SIZE = (300, 300) # Width, Height in pixels
FONT_SIZE = 200 # Adjust as needed to fit the letter nicely
BACKGROUND_COLOR = (255, 255, 255, 0) # Transparent background (RGBA)
TEXT_COLOR = (0, 0, 0, 255) # Black text (RGBA)

# List of Gujarati Characters (Consonants and Vowels) - Add more if needed
GUJARATI_CHARS = [
    # Vowels (Svar)
    'અ', 'આ', 'ઇ', 'ઈ', 'ઉ', 'ઊ', 'ઋ', 'એ', 'ઐ', 'ઓ', 'ઔ',
    # Consonants (Vyanjan)
    'ક', 'ખ', 'ગ', 'ઘ', 'ઙ',
    'ચ', 'છ', 'જ', 'ઝ', 'ઞ',
    'ટ', 'ઠ', 'ડ', 'ઢ', 'ણ',
    'ત', 'થ', 'દ', 'ધ', 'ન',
    'પ', 'ફ', 'બ', 'ભ', 'મ',
    'ય', 'ર', 'લ', 'વ',
    'શ', 'ષ', 'સ', 'હ',
    'ળ', 'ક્ષ', 'જ્ઞ'
]
# --- End Configuration ---

def generate_images():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load the font
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except IOError:
        print(f"Error: Font file not found at '{FONT_PATH}'.")
        print("Please download a Gujarati .ttf font (e.g., Noto Sans Gujarati)")
        print("and update the FONT_PATH variable in this script.")
        return

    print(f"Generating {len(GUJARATI_CHARS)} images in '{OUTPUT_DIR}'...")

    for char in GUJARATI_CHARS:
        # Create a new transparent image
        img = Image.new('RGBA', IMAGE_SIZE, BACKGROUND_COLOR)
        draw = ImageDraw.Draw(img)

        # Get text bounding box
        # Use textbbox which accounts for font metrics better
        try:
            # Pillow versions 9.x.x and later use textbbox
            bbox = draw.textbbox((0, 0), char, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            # Adjust y-position based on bbox's top value for better vertical centering
            text_y_offset = bbox[1]
        except AttributeError:
            # Older Pillow versions use textsize
            text_width, text_height = draw.textsize(char, font=font)
            text_y_offset = 0 # Approximation for older versions


        # Calculate position to center the text
        x = (IMAGE_SIZE[0] - text_width) / 2
        # Adjust y based on text_height and the font's bounding box top offset
        y = (IMAGE_SIZE[1] - text_height) / 2 - text_y_offset


        # Draw the character onto the image
        draw.text((x, y), char, font=font, fill=TEXT_COLOR)

        # Save the image
        file_name = f"{char}.png"
        file_path = os.path.join(OUTPUT_DIR, file_name)
        img.save(file_path)

    print("Image generation complete.")

if __name__ == "__main__":
    # Basic check if font path was updated
    if FONT_PATH == '/path/to/your/font/NotoSansGujarati-Regular.ttf':
         print("Warning: FONT_PATH has not been updated in the script.")
         print("Please edit 'scripts/generate_letter_images.py' and set the correct path to your font file.")
    else:
        generate_images() 