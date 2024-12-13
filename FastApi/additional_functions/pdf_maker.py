from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from datetime import datetime
from reportlab.platypus import XPreformatted
import os

from textwrap import wrap
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm, inch
import logging
logger = logging.getLogger(__name__)

import reportlab.rl_config
reportlab.rl_config.warnOnMissingFontGlyphs = 0
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont('Inter', 'fonts/Inter_18pt-Regular.ttf'))
pdfmetrics.registerFont(TTFont('InterL', 'fonts/Inter_18pt-Light.ttf'))
pdfmetrics.registerFont(TTFont('InterM', 'fonts/Inter_18pt-Medium.ttf'))
pdfmetrics.registerFont(TTFont('InterBd', 'fonts/Inter_18pt-Bold.ttf'))
pdfmetrics.registerFont(TTFont('InterIt', 'fonts/Inter_18pt-BlackItalic.ttf'))
pdfmetrics.registerFont(TTFont('InterBI', 'fonts/Inter_18pt-BoldItalic.ttf'))

class PDFReport:
    def __init__(self, start_page_num=1, pdf_file_name="File name", user_folder="temp", total_pages=8):
        self.start_page_num = start_page_num
        self.pdf_file_name = pdf_file_name
        self.user_folder = user_folder
        self.original_page_name = pdf_file_name
        self.page_size = (210 * mm, 297 * mm)
        self.styles = getSampleStyleSheet()
        
        self.start_page_num = start_page_num
        self.total_pages = total_pages

    def parse_markdown(self, markdown_text):
        """This func get text from file, and return list of lines from it"""
        text = []
        lines = []
        for char in markdown_text:
            if char == '\n':
                text.append(list(lines))
                lines =[]
                #print(1)
            else:
                lines.append(char)

        final_list_text = []
        for lst in text:
            joined_text = ''.join(lst).strip()
            final_list_text.append(joined_text)
        return final_list_text
    def add_improve_suggestions(self, c, file_path, plots_number):
        
        self.header(c)

        # Set fill and stroke colors
        fill_color = HexColor("#f5faf7")  # 5% opacity to color #409A65 /  https://www.diversifyindia.in/rgba-to-hex-converter/
        stroke_color = HexColor("#409A65")  # 100% opacity
        c.setFillColor(fill_color)
        c.setStrokeColor(stroke_color)

        # Draw the rectangle with adjusted stroke weight
        x, y= 20, 70  # X-coordinate of the lower-left corner
        width = 555  # Width of the rectangle
        height = 710  # Height of the rectangle
        corner_radius = 18  # Corner radius

        # Increase border thickness
        stroke_weight = 3  # Adjusted border thickness
        c.setLineWidth(stroke_weight)
        
        # Adjust the rectangle size to simulate outside stroke
        adjust = stroke_weight / 2
        c.roundRect(x + adjust, y + adjust, width - stroke_weight, height - stroke_weight, 
                    corner_radius, stroke=1, fill=1)

        #text block
        text = "<b>Achievements and Suggestions for Growth</b>"
        styles = getSampleStyleSheet()
        style = styles["Title"]
        style.fontSize = 14
        style.leading = 23
        #style.aligment = TA_CENTER
        xpreformatted = XPreformatted(text, style)
        xpreformatted.wrapOn(c, 400, 300)
        xpreformatted.drawOn(c, x=90, y=100)
        
        c.setFont('InterBd', 17)
        c.setFillColorRGB(0, 0, 0)  # Set text color to black
        
        # Read text from the file
        extracted_sections = self.extract_sections(file_path)
        markdown_text = extracted_sections
        markdown_text = markdown_text.get("Achievements_Suggestions_Growth")

        render_text = self.parse_markdown(markdown_text)

        page_height = 297*mm
        x, y = 35, 145  # Start position (from the top-left corner)
        line_height = 18  # Space between lines
        #max_line_width = 520  # Max width for wrapping text (e.g., 520 points)
        font_name = "Inter"
        font_size = 14

        text_object = c.beginText(x, y)
        text_object.setFont(font_name, font_size)


        # Function to wrap text at the maximum width
        from textwrap import wrap

        # Process each line of data
        temp =1250
        ll=[]
        #print(render_text)
        for line in render_text:
            text_object.setLeading(line_height)  # Line spacing
            if line.strip() == "":  # Handle empty lines (blank lines)
                #text_object.textLine("")  # Add a blank line
                temp -= line_height
                continue
            check_bold_line = False
            # Use a regex to find bold substrings (text between **)
            if ("**") in line:
                parts = re.split(r'(\*\*.*?\*\*)', line)
                ll.append(parts)

            #if line.startswith("**") and line.endswith("**"):  # Bold detection
            if line.startswith("**") and line.endswith("**"):  # Bold detection
                check_bold_line = True
                text_object.setFont("InterBd", font_size)  # Set bold font
                line = line.strip("**")  # Remove bold markers
            else:
                check_bold_line = False
                line = line.strip("**")  # Remove bold markers
                text_object.setFont(font_name, font_size)  # Regular font

            #test for capital letter check pasrsing
            ## Wrap text to fit within max line width
            #if sum(1 for char in line if char.isupper()) < 15:
            #    wrapped_lines = wrap(line, width=79)
            #elif sum(1 for char in line if char.isupper()) < 20:
            #    wrapped_lines = wrap(line, width=75)
            #elif sum(1 for char in line if char.isupper()) < 25:
            #    wrapped_lines = wrap(line, width=70)
            #elif sum(1 for char in line if char.isupper()) < 30:
            #    wrapped_lines = wrap(line, width=63)
            #else:
            #    wrapped_lines = wrap(line, width=58)
            
            #make letter small for reduce border overlapping

            cap_let = True
            line_low =""
            for i, v in enumerate(line):
                if v.isalpha() and cap_let:
                    cap_let = False
                    line_low += v
                else:
                    line_low += v.lower()

            wrapped_lines = wrap(line_low, width=76)
            
            for wrapped_line in wrapped_lines:
                #print(temp)
                wrapped_line_c = ''
                if "**" in wrapped_line:
                    for i in wrapped_line:
                        if i == "*":
                            pass
                        else:
                            wrapped_line_c +=i

                    wrapped_line = wrapped_line_c
                if temp - line_height < 30:  # If text exceeds the page height, create a new page
                    c.drawText(text_object)  # Draw current text before creating a new page

                    c.showPage()  # Start a new page
                    #y = page_height - 50  # Reset Y to top of the new page
                    y = 40
                    temp =750
                    text_object = c.beginText(x, y)  # Create a new text block on the new page
                    text_object.setFont(font_name, font_size) #TODO potential bug if line bold but begin next page can be common
                    text_object.setLeading(line_height)  # Reset line spacing

                # Add the wrapped line to the text object
                #text_object.textLine(f'\u2022 {wrapped_line}')  #TODO here can split line for **
                if wrapped_line.startswith('-'):
                    wrapped_line_c = ''
                    for i in wrapped_line:
                        if i == "-":
                            pass
                        else:
                            wrapped_line_c +=i

                    wrapped_line ='  ' + '\u2022 ' + wrapped_line_c
                if '\u2022 ' in wrapped_line:
                    text_object.textLine('\n')  
                    temp -= line_height  # Move to the next line
                    text_object.textLine(f'{wrapped_line}')  
                    temp -= line_height  # Move to the next line
                else:
                    if check_bold_line:
                        text_object.textLine('\n')  
                        temp -= line_height
                        text_object.textLine(f'{wrapped_line}')  
                        temp -= line_height  # Move to the next line
                    else:
                        text_object.textLine(f'{wrapped_line}')  
                        temp -= line_height

        # Draw the text on the canvas
        c.drawText(text_object)
        
        self.footer(c, plots_number+2)
        c.showPage()

    def add_data_analytic(self, c, file_path, plots_number):
        self.header(c)
        #from markdown import markdown
        x, y = 20, 90  # Start from the top of the page
        textobject = c.beginText(x, y)
        textobject.setFont('Inter', 12)
        line_height = 18  # Adjust this value for desired line spacing
        textobject.setLeading(line_height)

        extracted_sections = self.extract_sections(file_path)
        markdown_text = extracted_sections
        markdown_text = markdown_text.get("Detailed Analysis")
        #print(markdown_text)
        render_text = self.parse_markdown(markdown_text)

        page_height = 297*mm
        x, y = 30, 80  # Start position (from the top-left corner)
        line_height = 18  # Space between lines
        #max_line_width = 520  # Max width for wrapping text (e.g., 520 points)
        font_name = "Inter"
        font_size = 12

        text_object = c.beginText(x, y)
        text_object.setFont(font_name, font_size)


        # Function to wrap text at the maximum width
        from textwrap import wrap

        # Process each line of data
        temp =820 #one more exist if new page
        ll=[]
        #print(render_text)
        for line in render_text:
            text_object.setLeading(line_height)  # Line spacing
            if line.strip() == "":  # Handle empty lines (blank lines)
                text_object.textLine("")  # Add a blank line
                temp -= line_height
                continue
            
            # Use a regex to find bold substrings (text between **)
            if ("**") in line:
                parts = re.split(r'(\*\*.*?\*\*)', line)
                ll.append(parts)

            #if line.startswith("**") and line.endswith("**"):  # Bold detection
            if line.startswith("**") and line.endswith("**"):  # Bold detection
                text_object.setFont("InterBd", font_size)  # Set bold font
                line = line.strip("**")  # Remove bold markers
            else:
                line = line.strip("**")  # Remove bold markers
                text_object.setFont(font_name, font_size)  # Regular font

            # Wrap text to fit within max line width
            wrapped_lines = wrap(line, width=86)  # Wrap text to 90 characters, or adjust as necessary

            for wrapped_line in wrapped_lines:
                #print(temp)
                wrapped_line_c = ''
                if "**" in wrapped_line:
                    for i in wrapped_line:
                        if i == "*":
                            pass
                        else:
                            wrapped_line_c +=i

                    wrapped_line = wrapped_line_c
                if temp - line_height < 30:  # If text exceeds the page height, create a new page
                    c.drawText(text_object)  # Draw current text before creating a new page

                    c.showPage()  # Start a new page
                    #y = page_height - 50  # Reset Y to top of the new page
                    y = 40
                    temp =820
                    text_object = c.beginText(x, y)  # Create a new text block on the new page
                    text_object.setFont(font_name, font_size) #TODO potential bug if line bold but begin next page can be common
                    text_object.setLeading(line_height)  # Reset line spacing

                # Add the wrapped line to the text object
                #text_object.textLine(f'\u2022 {wrapped_line}')  #TODO here can split line for **
                
                if wrapped_line.startswith('-'):
                    wrapped_line_c = ''
                    for i in wrapped_line:
                        if i == "-":
                            pass
                        else:
                            wrapped_line_c +=i

                    wrapped_line = wrapped_line_c

                    wrapped_line ='  ' + '\u2022 ' + wrapped_line

                if wrapped_line.startswith('1.') or wrapped_line.startswith('2.') or wrapped_line.startswith('3.') or \
                            wrapped_line.startswith('4.') or wrapped_line.startswith('5.') or wrapped_line.startswith('6.') or wrapped_line.startswith('7.') \
                                or wrapped_line.startswith('8.') or wrapped_line.startswith('9.'):    
                    text_object.textLine(wrapped_line) #TODO here can split line for **
                    temp -= line_height  # Move to the next line
                    text_object.textLine('\n')
                    temp -= line_height  # Move to the next line
                else:
                    text_object.textLine(wrapped_line) #TODO here can split line for **
                    temp -= line_height    
                

        # Draw the text on the canvas
        c.drawText(text_object)
        
        self.footer(c, plots_number +1)
        c.showPage()
    
    def extract_sections(self, file_path):
        """Extracts specific sections from the text file based on headings."""
        sections = {
            "Detailed Analysis": [],
            "Achievements_Suggestions_Growth": []  #Achievements and Suggestions for Growth
        }

        # Start with the in_analysis flag set to True
        in_analysis = True
        in_suggestions = False


        with open(file_path, "r") as file:
            for line in file:
                #line = line.strip()

                # Check for "Business Improvement Suggestions" (case insensitive)
                if "achievements and suggestions for growth" in line.lower():
                    in_analysis = False
                    in_suggestions = True
                    continue
                

                # Collect lines for the respective sections
                if in_analysis:
                    sections["Detailed Analysis"].append(line)
                    #sections["Detailed Analysis"].append('\n')
                elif in_suggestions:
                    sections["Achievements_Suggestions_Growth"].append(line)
                    sections["Achievements_Suggestions_Growth"].append('\n')


        # Join the lines to form paragraphs
        for key in sections:
            sections[key] = " ".join(sections[key])

        return sections

    def add_section_to_page(self, c, section_title, extracted_sections):
        """Adds the content of each section to the page."""
        section_content = extracted_sections.get(section_title, [])
        
        y_position = 50  # Starting y position for content
        
        for line in section_content.split("\n"):
            paragraph = Paragraph(line, self.styles['Normal'])
            paragraph.wrap(500, y_position)
            paragraph.drawOn(c, 15, y_position)
            y_position -= paragraph.getHeight() + 5  # Move down for the next line

    def pdf_name(self, filename: str) -> str:
        """Format filename for pdf"""
        extensions = ['.csv', '.xlsx', '.xls']

        for ext in extensions:
            if filename.endswith(ext):
                # Remove the matching extension
                return filename[:-len(ext)]

        # If no matching extension is found, return the filename as is
        return filename

    def format_filename(self, filename: str) -> str:
        """Format filename based on extension."""
        extensions = ['.csv', '.xlsx', '.xls']
        for ext in extensions:
            if filename.endswith(ext):
                prefix_len, suffix_len = (7, 4) if ext == ".csv" else (6, 4)
                base_name = filename[:-len(ext)]
                if len(base_name) > 13:
                    return f"{base_name[:prefix_len]}...{base_name[-suffix_len:]}{ext}"
                else:
                    return filename.ljust(13)
            else:
                pass
        return filename.ljust(13)

    def header(self, c):
        """Add the header to each page."""
        c.saveState()
        
        image_path = "SD logo white.png"
        c.scale(1,-1)
        x_val = 20
        y_val = -41
        width = 632/5
        height = 92/5
        try:
            c.drawImage(ImageReader(image_path), x_val, y_val, width=width, height=height, mask='auto')
        except Exception as e:
            logging.warning(f'Error add logo: {e}')
        c.restoreState()

        #file name block
        formated_file_name = self.format_filename(self.original_page_name)
        
        
        fill_color = HexColor("#ececec")  # 5% opacity to color #409A65 /  https://www.diversifyindia.in/rgba-to-hex-converter/
        stroke_color = HexColor("#ececec")  # 100% opacity
        c.setFillColor(fill_color)
        c.setStrokeColor(stroke_color)

        # Draw the rectangle with adjusted stroke weight
        x = 361  # X-coordinate of the lower-left corner
        y = 18.6  # Y-coordinate of the lower-left corner
        width = 848/4 # Width of the rectangle
        height = 122/4  # Height of the rectangle
        corner_radius = 5  # Corner radius


        # Increase border thickness
        stroke_weight = 3  # Adjusted border thickness
        c.setLineWidth(stroke_weight)
        
        # Adjust the rectangle size to simulate outside stroke
        adjust = stroke_weight / 2
        c.roundRect(x + adjust, y + adjust, width - stroke_weight, height - stroke_weight, 
                    corner_radius, stroke=1, fill=1)
        
        
        
        c.setFont('InterBd',11)
        c.setFillColorRGB(0,0,0)
        c.drawString(368,37, f"Analyzed report:")
        
        c.setFont('Inter',11)
        c.setFillColorRGB(0,0,0)
        c.drawString(462,37, f"{formated_file_name}")

    def footer(self, c, current_page):
        """Add footer to each page."""
        try:
            # Date report created
            date_rep = datetime.now().strftime('%m/%d/%Y')

            # Font setup for the footer
            c.setFont("InterL", 13)
            c.setFillColorRGB(0, 0, 0)  # Text color: black

            # Date at bottom-left corner
            c.drawString(20, 815, "Date Exported:")  # x=5, y=15 from bottom-left
            c.setFont("InterM", 13)
            c.drawString(110, 815, date_rep)

            # Page numbering at bottom-right corner
            c.setFont("InterL", 13)
            c.drawRightString(573, 815, f"Page {current_page}")

        except Exception as e:
            print(f"in footer error: {e}")

    def add_viz_and_summary(self, c,user_folder, num_pages=5):
        """Add visualization and summary pages."""
        UPLOAD_FOLDER = f'FastApi/src/uploads/{user_folder}'
        PDF_FOLDER = f'FastApi/src/pdfs/{user_folder}'
        PLOTS_FOLDER = f'FastApi/src/plots/{user_folder}'
        SUMMARY_FOLDER = f'FastApi/src/summary/{user_folder}'
        
        extra_plot_path = os.path.join('FastApi/src/extra_plots.png')
        extra_text_path = os.path.join('FastApi/src/extra_sum.txt')
        
        for folder in [UPLOAD_FOLDER, PDF_FOLDER, PLOTS_FOLDER, SUMMARY_FOLDER]:
            if not os.path.exists(folder):
                os.makedirs(folder)
        
        
        current_iteration = 1
        photo_counter = 1
        page_nu = 1
        while current_iteration <= 10:        
            plot_image_path = os.path.join(PLOTS_FOLDER, f"chart_{photo_counter}.png")
            
            if os.path.exists(plot_image_path):
                self.header(c)
                c.saveState()

                c.scale(1,-1)
                x_val = 18.5
                y_val = -387
                #width = 196 * mm
                #height = 110*mm            
                width = 16*35.55
                height = 9*36.55
                try:
                    plot_image_path = os.path.join(PLOTS_FOLDER, f"chart_{photo_counter}.png")
                    c.drawImage(ImageReader(plot_image_path), x_val, y_val, width=width, height=height, mask='auto')
                except Exception as e:
                    logger.warning(f"Error adding plot {plot_image_path}: {e}. Using fallback image.")    
                    #c.drawImage(ImageReader(extra_plot_path), x_val, y_val, width=width, height=height, mask='auto')


                c.restoreState()

                stroke_color = HexColor("#FFFFFF")  # 100% opacity 
                c.setStrokeColor(stroke_color)

                # Draw the rectangle with adjusted stroke weight
                x, y= 8, 50

                width = 17*34
                height = 10*34.55
                corner_radius = 12
                # Increase border thickness
                stroke_weight = 13  # Adjusted border thickness
                c.setLineWidth(stroke_weight)

                # Adjust the rectangle size to simulate outside stroke
                adjust = stroke_weight / 2
                c.roundRect(x + adjust, y + adjust, width - stroke_weight, height - stroke_weight, 
                corner_radius, stroke=1, fill=0)

                x = 6.3
                y = 54
                width = 17*35
                height = 10*35.55
                c.rect(x, y, width - stroke_weight, height - stroke_weight,  stroke=1, fill=0)

                #text sum block
                try:
                    text_file_path = os.path.join(SUMMARY_FOLDER, f"sum_{photo_counter}.txt")
                    with open(text_file_path, "r") as file:
                        text = file.read()

                    x, y = 30, 410  # Start position (from the top-left corner)
                    line_height = 23  # Space between lines #TODO not working
                    #max_line_width = 520  # Max width for wrapping text (e.g., 520 points)
                    font_name = "Inter"
                    font_size = 12

                    text_object = c.beginText(x, y)
                    text_object.setFont(font_name, font_size)

                    # Process each line of data
                    temp =750
                    ll=[]

                    render_text = self.parse_markdown(text)

                    for line in render_text:
                        text_object.setLeading(line_height)  # Line spacing
                        if line.strip() == "":  # Handle empty lines (blank lines)
                            text_object.textLine("")  # Add a blank line
                            temp -= line_height
                            continue
                        
                        # Use a regex to find bold substrings (text between **)
                        if ("**") in line:
                            parts = re.split(r'(\*\*.*?\*\*)', line)
                            ll.append(parts)

                        #if line.startswith("**") and line.endswith("**"):  # Bold detection
                        if line.startswith("**") and line.endswith("**"):  # Bold detection
                            text_object.setFont("InterBd", font_size)  # Set bold font
                            line = line.strip("**")  # Remove bold markers
                        else:
                            line = line.strip("**")  # Remove bold markers
                            text_object.setFont(font_name, font_size)  # Regular font

                        # Wrap text to fit within max line width
                        wrapped_lines = wrap(line, width=93)  # Wrap text to 90 characters, or adjust as necessary

                        for wrapped_line in wrapped_lines:
                            #print(temp)
                            wrapped_line_c = ''
                            if "**" in wrapped_line:
                                for c in wrapped_line:
                                    if c == "*":
                                        pass
                                    else:
                                        wrapped_line_c +=c

                                wrapped_line = wrapped_line_c
                            if temp - line_height < 30:  # If text exceeds the page height, create a new page
                                c.drawText(text_object)  # Draw current text before creating a new page

                                c.showPage()  # Start a new page
                                #y = page_height - 50  # Reset Y to top of the new page
                                y = 40
                                temp =750
                                text_object = c.beginText(x, y)  # Create a new text block on the new page
                                text_object.setFont(font_name, font_size) #TODO potential bug if line bold but begin next page can be common
                                text_object.setLeading(line_height)  # Reset line spacing

                            # Add the wrapped line to the text object
                            #text_object.textLine(f'\u2022 {wrapped_line}')  #TODO here can split line for **

                            if wrapped_line.startswith('-') or wrapped_line.startswith('1.') or wrapped_line.startswith('2.') or wrapped_line.startswith('3.') or \
                                wrapped_line.startswith('4.') or wrapped_line.startswith('5.') or wrapped_line.startswith('6.') or wrapped_line.startswith('7.') \
                                    or wrapped_line.startswith('8.') or wrapped_line.startswith('9.'):

                                skip = False
                                for v, char in enumerate(wrapped_line):
                                    # Check if the current character and the next one form a pattern like "8."
                                    if char.isdigit() and v + 1 < len(wrapped_line) and wrapped_line[v + 1] == '.':
                                        skip = True
                                        continue
                                    elif skip:
                                        # Skip the dot following the number
                                        skip = False
                                        continue
                                    elif char == '-':
                                        pass
                                    else:
                                        wrapped_line_c += char

                                text_object.textLine('\n')
                                wrapped_line ='  ' + '\u2022 ' + wrapped_line_c

                            else:
                                for v, char in enumerate(wrapped_line):
                                    # Check if the current character and the next one form a pattern like "8."
                                        wrapped_line_c += char


                                wrapped_line = wrapped_line_c
                            text_object.textLine(f'{wrapped_line}')  
                            #text_object.textLine('\n')  
                            temp -= line_height  # Move to the next line

                    # Draw the text on the canvas
                    c.drawText(text_object)

                    self.footer(c,page_nu)
                    page_nu += 1
                    c.showPage()
                except Exception as e:
                    logger.warning(f"Error adding text from {text_file_path}: {e}. Using fallback text.")
                    #with open(extra_text_path, "r") as file:
                    #    text = file.read()
                    #x, y = 30, 410  # Start position (from the top-left corner)
                    #line_height = 23  # Space between lines #TODO not working
                    ##max_line_width = 520  # Max width for wrapping text (e.g., 520 points)
                    #font_name = "Inter"
                    #font_size = 12
#   
                    #text_object = c.beginText(x, y)
                    #text_object.setFont(font_name, font_size)
                    #wrapped_lines = wrap(text, width=93)
                    #for wrapped_line in wrapped_lines:
                    #    text_object.textLine(f'{wrapped_line}') 
                    #c.drawText(text_object)
#   
                    #self.footer(c,photo_counter)
                    #c.showPage()
            else:
                pass
                #print(f"{plot_image_path} does not exist, skipping.")
            current_iteration+=1
            photo_counter += 1

    def create_pdf(self):
        """Generate the PDF."""
        pdf_folder = f"FastApi/src/pdfs/{self.user_folder}"
        file_path = f"FastApi/src/uploads/{self.user_folder}/final_gen.txt"
        extra_file_path = f"FastApi/src/extra_final.txt"
        user_folder = 'temp'
        os.makedirs(pdf_folder, exist_ok=True)

        pdf_name = self.pdf_name(self.pdf_file_name)

        pdf_path = os.path.join(pdf_folder, f"{pdf_name}.pdf")
        c = canvas.Canvas(pdf_path, pagesize=self.page_size, bottomup=0)
        #c.translate(0, c._pagesize[1])

        import fnmatch
        dirpath = f"FastApi/src/plots/{self.user_folder}"
        plots_number = len(fnmatch.filter(os.listdir(dirpath), '*.png'))
        # Add content
        self.add_viz_and_summary(c, user_folder=self.user_folder, num_pages=plots_number)
        try:
            self.add_data_analytic(c,file_path, plots_number)
            self.add_improve_suggestions(c,file_path, plots_number)
        except Exception as e:
            self.add_data_analytic(c,extra_file_path)
            self.add_improve_suggestions(c,extra_file_path)
        
        # Save the PDF
        c.save()
        return pdf_path

# Usage Example
#pdf = PDFReport(start_page_num=1, pdf_file_name="GNGR_20240511  (2).csv", user_folder='1d01165b-1102-4609-b876-db31a6c15dbf')
#pdf.create_pdf()
#
