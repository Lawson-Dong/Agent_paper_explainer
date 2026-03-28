import base64
from typing import Optional, List, Tuple
import urllib.parse
import logging

logger = logging.getLogger(__name__)

class OverleafManager:
    """
    Integration with Overleaf for LaTeX document creation and editing.
    """
    
    OVERLEAF_URL = "https://www.overleaf.com/docs"
    
    def __init__(self):
        pass
    
    def generate_open_in_overleaf_link(
        self,
        latex_code: str,
        filename: str = "document.tex",
        engine: str = "pdflatex"
    ) -> str:
        """
        Generate a link to open LaTeX code in Overleaf.
        
        Args:
            latex_code: LaTeX source code
            filename: Name of the main file
            engine: TeX engine ('pdflatex', 'xelatex', 'lualatex', 'latex_dvipdf')
        
        Returns:
            URL to open in Overleaf
        """
        try:
            # URL encode the LaTeX code
            encoded_snip = urllib.parse.quote(latex_code)
            
            url = f"{self.OVERLEAF_URL}?encoded_snip={encoded_snip}"
            if engine != "pdflatex":
                url += f"&engine={engine}"
            
            return url
        
        except Exception as e:
            logger.error(f"Error generating Overleaf link: {e}")
            return ""
    
    def generate_base64_link(
        self,
        latex_code: str,
        engine: str = "pdflatex"
    ) -> str:
        """
        Generate Overleaf link using base64 encoding.
        
        Better for complex LaTeX with special characters.
        """
        try:
            # Encode as base64
            b64_code = base64.b64encode(latex_code.encode('utf-8')).decode('utf-8')
            
            url = f"{self.OVERLEAF_URL}?snip_uri=data:application/x-tex;base64,{b64_code}"
            if engine != "pdflatex":
                url += f"&engine={engine}"
            
            return url
        
        except Exception as e:
            logger.error(f"Error generating base64 Overleaf link: {e}")
            return ""
    
    def create_paper_template(
        self,
        title: str,
        authors: List[str],
        abstract: str,
        content: str = ""
    ) -> str:
        """
        Create an academic paper LaTeX template.
        
        Returns:
            Complete LaTeX document
        """
        authors_str = " \\and ".join(authors)
        
        latex_template = f"""\\documentclass{{article}}
\\usepackage{{amsmath}}
\\usepackage{{amssymb}}
\\usepackage{{graphicx}}
\\usepackage{{hyperref}}
\\usepackage{{cite}}
\\usepackage{{geometry}}
\\geometry{{margin=1in}}

\\title{{{title}}}
\\author{{{authors_str}}}
\\date{{\\today}}

\\begin{{document}}

\\maketitle

\\begin{{abstract}}
{abstract}
\\end{{abstract}}

\\section{{Introduction}}
% Add introduction here

{content}

\\section{{Conclusion}}
% Add conclusion here

\\begin{{thebibliography}}{{99}}
% Add references here
\\end{{thebibliography}}

\\end{{document}}
"""
        return latex_template
    
    def create_presentation_template(
        self,
        title: str,
        author: str,
        content_slides: List[Tuple[str, str]]
    ) -> str:
        """
        Create a Beamer presentation template.
        
        Args:
            title: Presentation title
            author: Author name
            content_slides: List of (slide_title, slide_content) tuples
        """
        slides = ""
        for slide_title, slide_content in content_slides:
            slides += f"""
\\begin{{frame}}
\\frametitle{{{slide_title}}}
{slide_content}
\\end{{frame}}
"""
        
        latex_template = f"""\\documentclass{{beamer}}
\\usepackage{{amsmath}}
\\usepackage{{amssymb}}
\\usetheme{{Madrid}}
\\usecolortheme{{default}}

\\title{{{title}}}
\\author{{{author}}}
\\date{{\\today}}

\\begin{{document}}

\\frame{{\\titlepage}}

{slides}

\\end{{document}}
"""
        return latex_template
    
    def create_research_proposal_template(
        self,
        title: str,
        researcher: str,
        background: str,
        objectives: str,
        methodology: str,
        expected_outcomes: str
    ) -> str:
        """Create a research proposal template."""
        
        latex_template = f"""\\documentclass{{article}}
\\usepackage{{amsmath}}
\\usepackage{{amssymb}}
\\usepackage{{graphicx}}
\\usepackage{{cite}}
\\usepackage{{geometry}}
\\geometry{{margin=1in}}

\\title{{{title}}}
\\author{{{researcher}}}
\\date{{\\today}}

\\begin{{document}}

\\maketitle

\\section{{Background and Significance}}
{background}

\\section{{Research Objectives}}
{objectives}

\\section{{Methodology}}
{methodology}

\\section{{Expected Outcomes}}
{expected_outcomes}

\\section{{Timeline}}
% Add timeline here

\\section{{Budget}}
% Add budget information here

\\begin{{thebibliography}}{{99}}
% Add references here
\\end{{thebibliography}}

\\end{{document}}
"""
        return latex_template
