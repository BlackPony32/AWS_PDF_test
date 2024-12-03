import os
from fpdf import FPDF
from datetime import datetime
from fpdf.enums import XPos, YPos, Align
import logging
# Path to your logo file
LOGO_PATH = 'FastApi/src/icon.ico'
logger = logging.getLogger(__name__)
class PDF(FPDF):
    def __init__(self, start_page_num=1, formated_file_name='File name', user_folder='temp1'):
        super().__init__()
        self.formated_file_name = formated_file_name
        self.start_page_num = start_page_num
        self.user_folder = user_folder
        
    def format_filename(self, filename: str) -> str:
        # Define limits and structure based on file type
        if filename.endswith('.csv'):
            prefix_len = 7  # First 7 characters
            suffix_len = 4  # Last 4 characters before ".csv"
            extension = '.csv'
        elif filename.endswith('.xlsx'):
            prefix_len = 6  # First 6 characters
            suffix_len = 4  # Last 4 characters before ".xlsx"
            extension = '.xlsx'
        elif filename.endswith('.xls'):
            prefix_len = 7  # First 7 characters
            suffix_len = 3  # Last 3 characters before ".xls"
            extension = '.xls'
        else:
            # For files without these extensions, return filename padded to 17
            return filename.ljust(17)

        # Check if filename (excluding extension) is longer than 17
        base_name = filename[: -len(extension)]
        if len(filename) > 17:
            # Construct the shortened filename with specified prefix, suffix, and extension
            return base_name[:prefix_len] + '...' + base_name[-suffix_len:] + extension
        else:
            # If filename is 17 or shorter, pad it to exactly 17 characters
            return filename.ljust(17)

    def header(self):
        try:
            # Background rectangle for the logo and text area
            self.set_fill_color(217, 217, 217)
            self.rect(149, 7.0, 55, 7, round_corners=True, style="F")

            # Add company logo if it exists
            if os.path.exists(LOGO_PATH):
                self.image(LOGO_PATH, x=9.2, y=8.2, w=5)  # Adjusted width for smaller logo

            # Company name
            self.set_xy(14, 3.3)
            self.set_font("helvetica", 'B', 16)
            self.set_text_color(55, 55, 55)
            self.cell(100, 15, text="simply", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')

            self.set_xy(32, 3.3)
            self.set_font("helvetica")
            self.cell(100, 15, text="depo", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')

            # Main title
            self.set_xy(114, 3.3)
            self.set_font("helvetica", 'B', 8)
            self.set_text_color(0, 0, 0)
            self.cell(100, 15, text="Analyzed report: ", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

            # Report filename
            self.set_xy(139, 3.3)
            self.set_font("helvetica")
            formated_file_name = self.format_filename(self.formated_file_name)
            self.cell(100, 15, text=formated_file_name, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
            
            # Line break after header
            self.ln(4)
        except Exception as e:
            print(f"in header error: {e}")
    
    def add_plain_text_to_pdf(self, text_file_path):
        """Helper function to add plain text to the PDF from a file."""
        self.set_text_color(0, 0, 0)
        with open(text_file_path, 'r') as file:
            text = file.read()
        self.set_font('helvetica', size=11)
        self.multi_cell(0, 6, text)

    
    def add_viz_and_sum_pages(self, num_pages=5):
        self.set_font("helvetica")
        
        #self.add_page()
        UPLOAD_FOLDER = f'FastApi/src/uploads/{self.user_folder}'
        PDF_FOLDER = f'FastApi/src/pdfs/{self.user_folder}'
        PLOTS_FOLDER = f'FastApi/src/plots/{self.user_folder}'
        SUMMARY_FOLDER = f'FastApi/src/summary/{self.user_folder}'
        page_width = 210
        for i in range(1, num_pages+1):
            self.add_page()
            plot_image_path = os.path.join(PLOTS_FOLDER, f"chart_{i}.png")
            text_file_path = os.path.join(SUMMARY_FOLDER, f"sum_{i}.txt")
            extra_plot_path = os.path.join('FastApi/src/extra_plots.png')
            extra_text_path = os.path.join('FastApi/src/extra_sum.txt')

            try:
                image_width = 180
                x_position = (page_width - image_width) / 2
                self.image(plot_image_path, x=x_position, y=30, w=image_width)
            except Exception as e:
                logger.warning(f"Error adding plot {plot_image_path}: {e}. Using fallback image.")
                image_width = 180
                x_position = (page_width - image_width) / 2

                self.image(extra_plot_path, x=x_position, y=30, w=image_width, h=120)

            self.ln(140)

            try:
                self.add_plain_text_to_pdf(text_file_path)
            except Exception as e:
                logger.warning(f"Error adding text from {text_file_path}: {e}. Using fallback text.")
                self.add_plain_text_to_pdf(extra_text_path)
            
    def extract_sections(self, file_path):
        """Extracts specific sections from the text file based on headings.

        Args:
            file_path (str): Path to the text file.

        Returns:
            dict: A dictionary containing the extracted sections.
        """
        sections = {
            "Detailed Analysis": [],
            "Business Improvement Suggestions": [],
            "Negative Aspects": []
        }

        # Start with the in_analysis flag set to True
        in_analysis = True
        in_suggestions = False
        in_negatives = False

        with open(file_path, "r") as file:
            for line in file:
                line = line.strip()

                # Check for "Business Improvement Suggestions" (case insensitive)
                if "business improvement suggestions" in line.lower():
                    in_analysis = False
                    in_suggestions = True
                    in_negatives = False
                    continue
                
                # Check for "Negative Aspects" (case insensitive)
                if "negative aspects" in line.lower():
                    in_analysis = False
                    in_suggestions = False
                    in_negatives = True
                    continue

                # Collect lines for the respective sections
                if in_analysis:
                    sections["Detailed Analysis"].append(line)
                    sections["Detailed Analysis"].append('\n')
                elif in_suggestions:
                    sections["Business Improvement Suggestions"].append(line)
                    sections["Business Improvement Suggestions"].append('\n')
                elif in_negatives:
                    sections["Negative Aspects"].append(line)
                    sections["Negative Aspects"].append('\n')

        # Join the lines to form paragraphs
        for key in sections:
            sections[key] = " ".join(sections[key])

        return sections
    
    def footer(self):
        try:
            # Date report created
            date_rep = datetime.now().strftime('%m/%d/%Y')
            self.set_font("helvetica")
            self.set_text_color(0, 0, 0)

            # Date at bottom-left corner
            self.set_xy(5, -15)
            self.cell(w=0, h=10, text="Date Exported", align=Align.L)
            self.set_font("helvetica", 'B', 10)
            self.set_xy(34, -15)
            self.cell(w=0, h=10, text=date_rep, align=Align.L)

            # Page numbering at bottom-right corner
            self.set_font("helvetica")
            self.set_xy(188, -15)
            self.cell(w=0, h=10, text="Page", align=Align.L)
            page_num = self.page_no() + self.start_page_num - 1
            self.set_font("helvetica", 'B', 10)
            self.set_xy(197, -15)
            self.cell(w=0, h=10, text=f"{int(page_num)}/{8}", align=Align.L)
        except Exception as e:
            print(f"in footer error: {e}")

    def add_text(self, final_sum_path):
        self.add_page()
        self.set_auto_page_break(auto=True, margin=15)
        with open(final_sum_path, 'r') as file:
            text = file.read()
        self.set_font('helvetica', size=12)  # Set bold font
        lines  = text.split('\n')
        try:
            extracted_sections = self.extract_sections(final_sum_path)

            for line in extracted_sections.get("Detailed Analysis").split('\n'):
                if False:
                    pass
                else:
                    self.multi_cell(0, 10, line, markdown=True,new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            self.add_page()
            self.set_fill_color(231,242,236)
            self.rect(8, 20, 194, 250, round_corners=True, style="DF")
            self.set_font('helvetica', size=17, style='B')  # Set bold font
            self.set_xy(15, 30)
            self.cell(0,8, "Business Improvement Suggestions",center=True, markdown=True,align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            self.set_font('helvetica', size=12)  # Set bold font
            self.set_xy(15, 50)
            for line in extracted_sections.get("Business Improvement Suggestions").split('\n'):
                if False:
                    pass
                else:
                    self.multi_cell(0,8, line, markdown=True,new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            for line in extracted_sections.get("Negative Aspects").split('\n'):
                if False:
                    pass
                else:
                    self.multi_cell(0, 8, line, markdown=True,new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        except Exception as e:
            logger.error("Error add final summary: ", e)
                
    def create_pdf(self):
        primary_file_path = "FastApi/src/final_gen.txt"
        fallback_file_path = "FastApi/src/extra_final.txt"
        PDF_FOLDER = f'FastApi/src/pdfs/{self.user_folder}'
        if not os.path.exists(PDF_FOLDER):
            os.makedirs(PDF_FOLDER)
        path = 'FastApi/src/final_gen.txt'
        self.add_viz_and_sum_pages()
        self.add_text(path)
        
        pdf_filename = f"{os.path.splitext(self.formated_file_name)[0]}.pdf"
        pdf_path = os.path.join(PDF_FOLDER, pdf_filename)
        self.output(pdf_path)
        return pdf_path
# Usage example
#pdf = PDF(start_page_num=1, formated_file_name="GNGR_20240504 .xlsx", user_folder='0597d292-a72a-11ef-896f-70665514def7')
#pdf.create_pdf()
