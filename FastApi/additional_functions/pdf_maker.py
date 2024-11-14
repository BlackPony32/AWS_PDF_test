from fpdf import FPDF
import logging
import os
import markdown2

logger = logging.getLogger(__name__)



#_____start of trash functions_ probably deleet________________________________
def process_markdown_to_pdf(pdf, markdown_text):
    """Convert Markdown to PDF with basic formatting."""
    lines = markdown_text.split('\n')
    for line in lines:
        if line.startswith('#'):
            pdf.set_font("Arial", style='B', size=16)  # Larger font for headers
            pdf.cell(200, 10, txt=line.replace('#', '').strip(), ln=1)
            pdf.set_font("Arial", size=12)

        elif '**' in line:
            bold_text = line.replace('**', '')  # Strip the markdown bold markers
            pdf.set_font("Arial", style='B', size=12)
            pdf.cell(200, 10, txt=bold_text, ln=1)
            pdf.set_font("Arial", size=12)
        else:

            max_line_length = 100
            words = line.split()  # Split line into words
            current_line = ""

            for word in words:
                if len(current_line) + len(word) + 1 <= max_line_length:  # +1 for space
                    current_line += (word + " ")  # Add the word with a space
                else:
                    # Output the current line and reset for the next line
                    pdf.cell(200, 10, txt=current_line.strip(), ln=1)
                    current_line = word + " "  # Start a new line with the current word

            if current_line:
                pdf.cell(200, 10, txt=current_line.strip(), ln=1)

def add_plain_text_to_pdf(pdf, file_path, font_size=11):
    """Helper function to add plain text to the PDF from a file."""
    try:
        pdf.set_text_color(0, 0, 0)
        with open(file_path, 'r') as file:
            text = file.read()
        pdf.set_font("Arial", size=font_size)
        pdf.multi_cell(0, 6, text)
    except Exception as e:
        logger.info(f"Error reading {file_path}: {e}")

def add_markdown_to_pdf(pdf, file_path):
    """Helper function to read Markdown and convert it to PDF."""
    try:
        pdf.set_text_color(0, 0, 0)
        with open(file_path, 'r') as file:
            markdown_text = file.read()

        pdf.multi_cell(0, 10, markdown_text)
        #process_markdown_to_pdf(pdf, markdown_text)
    except Exception as e:
        logger.info(f"Error reading {file_path}: {e}")

#_____end of trash functions_ probably deleet________________________________
from fpdf.enums import XPos, YPos
def find_bold(pdf, file_path):
    with open(file_path, 'r') as file:
        text = file.read()

    # Use regex to find text between ** symbols
    #matches = re.findall(r'\*\*(.*?)\*\*', line)
    pdf.set_font('helvetica', size=12)  # Set bold font
    lines  = text.split('\n')
    for line in lines:

            pdf.multi_cell(0, 10, line, markdown=True,new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
def generate_pdf(original_filename, user_folder):
    # Define folder paths
    UPLOAD_FOLDER = f'FastApi/src/uploads/{user_folder}'
    PDF_FOLDER = f'FastApi/src/pdfs/{user_folder}'
    PLOTS_FOLDER = f'FastApi/src/plots/{user_folder}'
    SUMMARY_FOLDER = f'FastApi/src/summary/{user_folder}'
    LOGO_PATH = 'FastApi/src/icon.ico'

    for folder in [UPLOAD_FOLDER, PDF_FOLDER, PLOTS_FOLDER, SUMMARY_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)
    pdf_filename = f"{os.path.splitext(original_filename)[0]}.pdf"
    pdf_path = os.path.join(PDF_FOLDER, pdf_filename)

    pdf = FPDF()
    pdf.add_page()

    # Add company logo and title on the first page and background rectangle for the logo and text area
    pdf.set_fill_color(31, 100, 109)
    pdf.rect(0, 0, 210, 40, 'F')  
    if os.path.exists(LOGO_PATH):
        pdf.image(LOGO_PATH, x=9.5, y=20, w=5)  # Smaller logo size (adjusted width)

    pdf.set_xy(15, 15)
    pdf.set_font("helvetica", 'B', 16)
    pdf.set_text_color(255, 255, 255)  # White text color for contrast
    pdf.cell(100, 15, txt="SimplyDepo", ln=False, align='L')

    pdf.ln(20)

    # Add main title
    pdf.set_xy(100, 15)
    pdf.set_font("helvetica", 'B', 16)
    pdf.set_text_color(71, 160, 109)  # Reset to black text
    pdf.cell(100, 15, txt=f"User Data Report: {original_filename}", ln=True, align='C')

    # Loop through and add charts and summaries
    page_width = 210
    for i in range(1, 6):
        plot_image_path = os.path.join(PLOTS_FOLDER, f"chart_{i}.png")
        text_file_path = os.path.join(SUMMARY_FOLDER, f"sum_{i}.txt")
        extra_plot_path = os.path.join('FastApi/src/extra_plots.png')
        extra_text_path = os.path.join('FastApi/src/extra_sum.txt')

        try:
            image_width = 180
            x_position = (page_width - image_width) / 2
            pdf.image(plot_image_path, x=x_position, y=30, w=image_width)
        except Exception as e:
            image_width = 180
            x_position = (page_width - image_width) / 2
            logger.warning(f"Error adding plot {plot_image_path}: {e}. Using fallback image.")
            pdf.image(extra_plot_path, x=x_position, y=30, w=image_width)

        pdf.ln(140)

        try:
            add_plain_text_to_pdf(pdf, text_file_path)
        except Exception as e:
            logger.warning(f"Error adding text from {text_file_path}: {e}. Using fallback text.")
            add_plain_text_to_pdf(pdf, extra_text_path)

        if i < 5:
            pdf.add_page()
            pdf.set_fill_color(31, 100, 109)
            pdf.rect(0, 0, 210, 40, 'F')  

            pdf.image(LOGO_PATH, x=9.5, y=20, w=5)
            pdf.set_xy(15, 15)  # Position next to the logo
            pdf.set_font("helvetica", 'B', 16)
            pdf.set_text_color(255, 255, 255)  # White text color for contrast
            pdf.cell(100, 15, txt="SimplyDepo", ln=False, align='L')

            pdf.ln(25)  # Add line break

    pdf.add_page()  # Ensure there's a new page for the final section
    primary_file_path = "FastApi/src/final_gen.txt"
    fallback_file_path = "FastApi/src/extra_final.txt"
    if os.path.exists(primary_file_path):
        find_bold(pdf, primary_file_path)
    else:
        find_bold(pdf, fallback_file_path)

    pdf.output(pdf_path)
    logger.info(f"PDF generated: {pdf_path}")

    return pdf_path
