"""Professional resume PDF generation with multiple templates.

Templates optimized for Canadian employers and ATS systems:
- No graphics, no images (ATS-safe)
- Clean typography, high contrast
- Proper section hierarchy for scanability
- No fancy fonts or colors that break parsing
"""

from io import BytesIO
from datetime import datetime
from models import ResumeDraft


def _format_date_range(start: str, end: str = None) -> str:
    """Convert YYYY-MM dates to readable format. 'May 2023 – Present' or 'May 2023 – Aug 2024'."""
    def parse_date(date_str):
        if not date_str:
            return None
        parts = date_str.split("-")
        if len(parts) == 2:
            month_map = {
                "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun",
                "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
            }
            return f"{month_map.get(parts[1], 'Unknown')} {parts[0]}"
        return date_str

    start_label = parse_date(start) or "Unknown"
    if end:
        end_label = parse_date(end) or "Unknown"
        return f"{start_label} – {end_label}"
    return f"{start_label} – Present"


def _format_date_year(date_str: str = None) -> str:
    """Just YYYY from YYYY-MM."""
    if not date_str or len(date_str) < 4:
        return ""
    return date_str[:4]


def _format_location_line(location: str, city: str, province: str) -> str:
    """Clean location: 'Toronto, ON' or 'Remote, Vancouver, BC'."""
    parts = [p.strip() for p in [location, city, province] if p and p.strip()]
    return " | ".join(parts) if parts else "Canada"


def _classic_template(resume: ResumeDraft, add_watermark: bool = False) -> str:
    """Traditional single-column resume (most ATS-friendly).
    
    Classic design:
    - Header: name, contact info
    - Summary
    - Experience (most recent first)
    - Education
    - Skills
    - Languages
    - Footer watermark (if free tier)
    """
    contact_info = f"{resume.email} • {resume.phone}"
    if resume.city:
        contact_info += f" • {resume.city}, {resume.province}"

    experience_html = ""
    for exp in resume.experience:
        date_range = _format_date_range(exp.start_date, exp.end_date)
        bullets_html = ""
        for bullet in exp.bullets:
            bullets_html += f"<li>{bullet.text}</li>"

        experience_html += f"""
        <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                <div style="font-weight: 600; font-size: 11pt;">{exp.title}</div>
                <div style="font-size: 10pt; color: #666;">{date_range}</div>
            </div>
            <div style="font-size: 10pt; color: #555; margin-bottom: 4px;">{exp.employer} • {_format_location_line(exp.location, '', '')}</div>
            <ul style="margin: 4px 0; padding-left: 20px; font-size: 10pt;">
                {bullets_html}
            </ul>
        </div>
        """

    education_html = ""
    for edu in resume.education:
        year_label = _format_date_year(edu.graduation_year)
        if year_label:
            year_label = f" ({year_label})"
        equiv_text = f" – {edu.canadian_equivalent}" if edu.canadian_equivalent else ""

        education_html += f"""
        <div style="margin-bottom: 8px;">
            <div style="font-weight: 600; font-size: 11pt;">{edu.credential}{equiv_text}</div>
            <div style="font-size: 10pt; color: #555;">{edu.institution}, {edu.country}{year_label}</div>
        </div>
        """

    skills_html = ""
    if resume.skills:
        skills_text = " • ".join(resume.skills[:15])  # Limit to 15 to avoid wrapping issues
        skills_html = f"""
        <div style="margin-bottom: 8px;">
            <div style="font-weight: 600; font-size: 10pt; text-transform: uppercase; letter-spacing: 0.5px;">Skills</div>
            <p style="font-size: 10pt; margin: 4px 0; line-height: 1.4;">{skills_text}</p>
        </div>
        """

    languages_html = ""
    if resume.languages:
        langs = []
        for lang in resume.languages:
            label = lang.language
            if lang.clb_level:
                label += f" ({lang.clb_level})"
            langs.append(label)
        languages_text = " • ".join(langs)
        languages_html = f"""
        <div style="margin-bottom: 8px;">
            <div style="font-weight: 600; font-size: 10pt; text-transform: uppercase; letter-spacing: 0.5px;">Languages</div>
            <p style="font-size: 10pt; margin: 4px 0;">{languages_text}</p>
        </div>
        """

    watermark_html = ""
    if add_watermark:
        watermark_html = """
        <div style="position: fixed; bottom: 10px; left: 10px; right: 10px; font-size: 8pt; color: #ccc; text-align: center;">
            Made with MapleJourney • Upgrade to remove watermark
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 11pt;
                line-height: 1.3;
                color: #333;
                margin: 0;
                padding: 36pt;
                background: white;
            }}
            @page {{
                size: letter;
                margin: 0.5in;
            }}
            h1 {{
                margin: 0 0 4pt 0;
                font-size: 16pt;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .contact {{
                margin-bottom: 12pt;
                font-size: 9pt;
                color: #666;
            }}
            .summary {{
                margin-bottom: 12pt;
                line-height: 1.5;
                font-size: 10pt;
            }}
            .section-title {{
                font-size: 10pt;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-top: 10pt;
                margin-bottom: 8pt;
                border-bottom: 1px solid #ddd;
                padding-bottom: 4px;
            }}
            .section-content {{
                margin-bottom: 12pt;
            }}
        </style>
    </head>
    <body>
        <h1>{resume.full_name}</h1>
        <div class="contact">{contact_info}</div>

        {f'''<div class="summary">
            <div class="section-title">Professional Summary</div>
            <p style="margin: 0; font-size: 10pt; line-height: 1.5;">{resume.summary}</p>
        </div>''' if resume.summary else ''}

        <div class="section-content">
            <div class="section-title">Experience</div>
            {experience_html if experience_html else '<p style="font-size: 10pt; color: #999;">No experience added yet.</p>'}
        </div>

        <div class="section-content">
            <div class="section-title">Education</div>
            {education_html if education_html else '<p style="font-size: 10pt; color: #999;">No education added yet.</p>'}
        </div>

        {skills_html}
        {languages_html}

        {watermark_html}
    </body>
    </html>
    """
    return html


def _modern_template(resume: ResumeDraft, add_watermark: bool = False) -> str:
    """Modern design with sidebar and subtle accent color.
    
    Modern touches:
    - Two-column: main content + sidebar
    - Sidebar: Skills, Languages (scannable)
    - Subtle color accent (brand blue) on headers
    - Still ATS-safe: no images, proper text hierarchy
    """
    contact_info = f"{resume.email} • {resume.phone}"
    if resume.city:
        contact_info += f" • {resume.city}, {resume.province}"

    experience_html = ""
    for exp in resume.experience:
        date_range = _format_date_range(exp.start_date, exp.end_date)
        bullets_html = ""
        for bullet in exp.bullets:
            bullets_html += f"<li>{bullet.text}</li>"

        experience_html += f"""
        <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                <div style="font-weight: 600; font-size: 11pt; color: #1a5f4a;">{exp.title}</div>
                <div style="font-size: 10pt; color: #888;">{date_range}</div>
            </div>
            <div style="font-size: 10pt; color: #666; margin-bottom: 4px; font-weight: 500;">{exp.employer} • {_format_location_line(exp.location, '', '')}</div>
            <ul style="margin: 4px 0; padding-left: 18px; font-size: 10pt; line-height: 1.4;">
                {bullets_html}
            </ul>
        </div>
        """

    education_html = ""
    for edu in resume.education:
        year_label = _format_date_year(edu.graduation_year)
        if year_label:
            year_label = f" ({year_label})"
        equiv_text = f" – {edu.canadian_equivalent}" if edu.canadian_equivalent else ""

        education_html += f"""
        <div style="margin-bottom: 8px;">
            <div style="font-weight: 600; font-size: 11pt; color: #1a5f4a;">{edu.credential}{equiv_text}</div>
            <div style="font-size: 10pt; color: #666;">{edu.institution}, {edu.country}{year_label}</div>
        </div>
        """

    skills_list = ""
    if resume.skills:
        for skill in resume.skills[:12]:
            skills_list += f"<div style='margin: 4px 0; font-size: 9pt;'>• {skill}</div>"

    languages_list = ""
    if resume.languages:
        for lang in resume.languages:
            label = lang.language
            if lang.clb_level:
                label += f" ({lang.clb_level})"
            languages_list += f"<div style='margin: 4px 0; font-size: 9pt;'>• {label}</div>"

    watermark_html = ""
    if add_watermark:
        watermark_html = """
        <div style="position: fixed; bottom: 8px; left: 8px; right: 8px; font-size: 7pt; color: #e0e0e0; text-align: center; z-index: -1;">
            Made with MapleJourney
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 11pt;
                line-height: 1.3;
                color: #333;
                margin: 0;
                padding: 0;
                background: white;
            }}
            @page {{
                size: letter;
                margin: 0.5in;
            }}
            .container {{
                display: flex;
                gap: 20pt;
            }}
            .main {{
                flex: 1;
            }}
            .sidebar {{
                width: 100pt;
                padding-left: 16pt;
                border-left: 2pt solid #1a5f4a;
                font-size: 9pt;
            }}
            h1 {{
                margin: 0 0 4pt 0;
                font-size: 16pt;
                font-weight: 700;
                color: #1a5f4a;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .contact {{
                margin-bottom: 12pt;
                font-size: 8pt;
                color: #888;
            }}
            .summary {{
                margin-bottom: 10pt;
                line-height: 1.5;
                font-size: 10pt;
            }}
            .section-title {{
                font-size: 9pt;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-top: 8pt;
                margin-bottom: 6pt;
                color: #1a5f4a;
            }}
            .section-content {{
                margin-bottom: 10pt;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="main">
                <h1>{resume.full_name}</h1>
                <div class="contact">{contact_info}</div>

                {f'''<div class="summary">
                    <div class="section-title">Professional Summary</div>
                    <p style="margin: 0; font-size: 9pt; line-height: 1.5;">{resume.summary}</p>
                </div>''' if resume.summary else ''}

                <div class="section-content">
                    <div class="section-title">Experience</div>
                    {experience_html if experience_html else '<p style="font-size: 9pt; color: #bbb;">No experience added.</p>'}
                </div>

                <div class="section-content">
                    <div class="section-title">Education</div>
                    {education_html if education_html else '<p style="font-size: 9pt; color: #bbb;">No education added.</p>'}
                </div>
            </div>

            <div class="sidebar">
                <div class="section-title">Skills</div>
                {skills_list if skills_list else '<p style="font-size: 8pt; color: #ccc;">No skills added.</p>'}

                <div style="margin-top: 12pt;">
                    <div class="section-title">Languages</div>
                    {languages_list if languages_list else '<p style="font-size: 8pt; color: #ccc;">No languages added.</p>'}
                </div>
            </div>
        </div>

        {watermark_html}
    </body>
    </html>
    """
    return html


def _compact_template(resume: ResumeDraft, add_watermark: bool = False) -> str:
    """Dense single-page format for experienced professionals.
    
    Compact design:
    - Reduced spacing, smaller fonts
    - Fits more content on one page
    - Still readable and professional
    - Perfect for 10+ years experience
    """
    contact_info = f"{resume.email} • {resume.phone}"
    if resume.city:
        contact_info += f" • {resume.city}, {resume.province}"

    experience_html = ""
    for exp in resume.experience:
        date_range = _format_date_range(exp.start_date, exp.end_date)
        bullets_html = ""
        for bullet in exp.bullets[:3]:  # Only 3 bullets in compact mode
            bullets_html += f"<li style='margin: 1px 0;'>{bullet.text}</li>"

        experience_html += f"""
        <div style="margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between;">
                <span style="font-weight: 600; font-size: 10pt;">{exp.title}</span>
                <span style="font-size: 9pt; color: #777;">{date_range}</span>
            </div>
            <div style="font-size: 9pt; color: #555;">{exp.employer} • {_format_location_line(exp.location, '', '')}</div>
            <ul style="margin: 2px 0; padding-left: 16px; font-size: 9pt;">
                {bullets_html}
            </ul>
        </div>
        """

    education_html = ""
    for edu in resume.education:
        year_label = _format_date_year(edu.graduation_year)
        if year_label:
            year_label = f" ({year_label})"
        equiv_text = f" – {edu.canadian_equivalent}" if edu.canadian_equivalent else ""

        education_html += f"""
        <div style="margin-bottom: 6px;">
            <span style="font-weight: 600; font-size: 10pt;">{edu.credential}{equiv_text}</span>
            <span style="font-size: 9pt; color: #666;"> • {edu.institution}, {edu.country}{year_label}</span>
        </div>
        """

    skills_text = " • ".join(resume.skills[:10]) if resume.skills else ""
    languages_text = " • ".join([f"{l.language}{f' ({l.clb_level})' if l.clb_level else ''}" for l in resume.languages]) if resume.languages else ""

    watermark_html = ""
    if add_watermark:
        watermark_html = """
        <div style="position: fixed; bottom: 6px; left: 6px; right: 6px; font-size: 7pt; color: #e8e8e8; text-align: center;">
            MapleJourney
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 10pt;
                line-height: 1.2;
                color: #222;
                margin: 0;
                padding: 24pt;
                background: white;
            }}
            @page {{
                size: letter;
                margin: 0.4in;
            }}
            h1 {{
                margin: 0 0 2pt 0;
                font-size: 14pt;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.3px;
            }}
            .contact {{
                margin-bottom: 8pt;
                font-size: 8pt;
                color: #777;
            }}
            .summary {{
                margin-bottom: 8pt;
                line-height: 1.4;
                font-size: 9pt;
            }}
            .section {{
                margin-bottom: 8pt;
            }}
            .section-title {{
                font-size: 9pt;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.3px;
                margin-bottom: 4pt;
                border-bottom: 1px solid #ddd;
                padding-bottom: 2px;
            }}
        </style>
    </head>
    <body>
        <h1>{resume.full_name}</h1>
        <div class="contact">{contact_info}</div>

        {f'''<div class="summary">
            <div class="section-title">Summary</div>
            <p style="margin: 0; font-size: 9pt; line-height: 1.4;">{resume.summary}</p>
        </div>''' if resume.summary else ''}

        <div class="section">
            <div class="section-title">Experience</div>
            {experience_html if experience_html else '<p style="font-size: 9pt; color: #aaa; margin: 0;">No experience added.</p>'}
        </div>

        <div class="section">
            <div class="section-title">Education</div>
            {education_html if education_html else '<p style="font-size: 9pt; color: #aaa; margin: 0;">No education added.</p>'}
        </div>

        {f'''<div class="section">
            <div class="section-title">Skills</div>
            <p style="font-size: 9pt; margin: 0;">{skills_text}</p>
        </div>''' if skills_text else ''}

        {f'''<div class="section">
            <div class="section-title">Languages</div>
            <p style="font-size: 9pt; margin: 0;">{languages_text}</p>
        </div>''' if languages_text else ''}

        {watermark_html}
    </body>
    </html>
    """
    return html


async def render_resume_to_pdf(resume: ResumeDraft, template: str = "classic", add_watermark: bool = False) -> BytesIO:
    """Render resume to PDF bytes.
    
    Args:
        resume: ResumeDraft model with all data
        template: 'classic', 'modern', or 'compact'
        add_watermark: If True, adds free-tier watermark footer
    
    Returns:
        BytesIO with PDF data ready for download
    """
    template = template.lower() or "classic"

    if template == "modern":
        html_string = _modern_template(resume, add_watermark)
    elif template == "compact":
        html_string = _compact_template(resume, add_watermark)
    else:  # classic
        html_string = _classic_template(resume, add_watermark)

    try:
        # Lazy import so missing native libs for WeasyPrint don't break API startup.
        from weasyprint import HTML
    except Exception as exc:
        raise RuntimeError("PDF rendering dependencies are not available on this server") from exc

    html_obj = HTML(string=html_string)
    pdf_bytes = html_obj.write_pdf()

    pdf_io = BytesIO(pdf_bytes)
    pdf_io.seek(0)
    return pdf_io


def get_template_list() -> list:
    """Return available templates."""
    return [
        {
            "id": "classic",
            "name": "Classic",
            "description": "Traditional single-column format. Most ATS-friendly.",
            "preview_class": "bg-white border-2 border-gray-300",
        },
        {
            "id": "modern",
            "name": "Modern",
            "description": "Two-column with skills sidebar. Contemporary and scannable.",
            "preview_class": "bg-white border-l-4 border-emerald-600",
        },
        {
            "id": "compact",
            "name": "Compact",
            "description": "Dense single-page for experienced professionals.",
            "preview_class": "bg-white border-2 border-gray-200 text-sm",
        },
    ]
