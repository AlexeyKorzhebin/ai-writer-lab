from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import inch
import tempfile
import os

class PDFExporter:
    def export_project(self, project, chapters):
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

        doc = SimpleDocTemplate(tmp_file.name)
        elements = []

        # Register a Unicode font (DejaVuSans supports Cyrillic)
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
            style = ParagraphStyle(
                name="NormalUnicode",
                fontName="DejaVuSans",
                fontSize=12,
                leading=14,
            )
        else:
            style = getSampleStyleSheet()["Normal"]

        elements.append(Paragraph(project.title, style))
        elements.append(Spacer(1, 0.3 * inch))

        for chapter in chapters:
            elements.append(Paragraph(chapter.title, style))
            elements.append(Spacer(1, 0.2 * inch))
            content = chapter.content or ""
            elements.append(Paragraph(content.replace("\n", "<br/>"), style))
            elements.append(Spacer(1, 0.5 * inch))

        doc.build(elements)
        return tmp_file.name
