#!/usr/bin/env python3
"""
Generate md-to-pdf config with Tendo branded header/footer.

Usage:
    python gen_md2pdf_config.py [output_dir]

Output:
    - md2pdf-config.js  (Puppeteer PDF options + header/footer templates)

CSS (tendo-style.css) is shared from skill/references/ — no per-project copy needed.

Prerequisites:
    1. npm install -g md-to-pdf
    2. npx puppeteer browsers install chrome
    3. Unpack reference docx for icons:
       python scripts/office/unpack.py references/TendoCN-Test-Procedure.docx unpacked_ref
"""

import base64
import os
import sys

def img_to_base64(path):
    """Convert image file to base64 data URI string."""
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

def main():
    # Determine paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_dir = os.path.dirname(script_dir)
    assets_dir = os.path.join(skill_dir, 'assets')
    
    # Output directory (default: current directory)
    output_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    # Icon source (from unpacked TendoCN - Test Procedure.docx)
    # image2.jpg = location pin, image3.jpg = mail envelope
    unpacked_media = os.path.join(output_dir, 'unpacked_ref', 'word', 'media')
    
    # Check if icons exist (optional — header works without them)
    logo_path = os.path.join(assets_dir, 'Logo Transparent (Header).png')
    marker_path = os.path.join(unpacked_media, 'image2.jpg')
    mail_path = os.path.join(unpacked_media, 'image3.jpg')

    def safe_b64(path, placeholder=''):
        if os.path.exists(path):
            return img_to_base64(path)
        return placeholder

    logo_b64 = safe_b64(logo_path)
    marker_b64 = safe_b64(marker_path, 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')
    mail_b64 = safe_b64(mail_path, 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')
    
    # Header template — no footer, single-line company name
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height:32px;" />' if logo_b64 else '<span style="font-size:9pt;font-weight:bold;color:#578FD6;">TENDO</span>'
    marker_html = f'<img src="data:image/jpeg;base64,{marker_b64}" style="height:11px;vertical-align:middle;" />' if marker_b64 else ''
    mail_html = f'<img src="data:image/jpeg;base64,{mail_b64}" style="height:11px;vertical-align:middle;" />' if mail_b64 else ''

    header_html = f'''<div style="width:100%;box-sizing:border-box;padding-left:25mm;padding-right:25mm;font-family:Arial,sans-serif;color:#404040;">
<table style="width:100%;border-collapse:collapse;border:none;margin:0;padding:0;">
<tr>
<td style="width:18%;border:none;padding:0;vertical-align:middle;">
{logo_html}
</td>
<td style="width:28%;border:none;border-left:3px solid #C6D9F1;padding-left:10px;vertical-align:middle;white-space:nowrap;">
<div style="font-size:7.5pt;font-weight:bold;color:#404040;">Tendo Technology (Shanghai) Co., Ltd.</div>
<div style="font-size:6.5pt;color:#666;margin-top:1px;">VAT Reg. No: 91310000MAE6R8R250</div>
</td>
<td style="width:32%;border:none;border-left:3px solid #C6D9F1;padding-left:10px;vertical-align:middle;">
{marker_html}<span style="font-size:7pt;color:#666;vertical-align:middle;margin-left:3px;">Building B, Unit 206, No. 135 Yanping Road, Jingan District, Shanghai 200042</span>
</td>
<td style="width:22%;border:none;border-left:3px solid #C6D9F1;padding-left:10px;vertical-align:middle;">
{mail_html}<span style="font-size:7pt;color:#666;vertical-align:middle;margin-left:3px;">www.tendo.technology</span>
</td>
</tr>
</table>
<div style="height:4px;background:#578FD6;margin-top:8px;"></div>
</div>'''

    # No footer
    footer_html = '<div></div>'
    
    # CSS absolute path (so md-to-pdf finds it regardless of MD file location)
    css_abs_path = os.path.join(skill_dir, 'references', 'tendo-style.css').replace('\\', '/')

    # Config file content — large top margin for header image overlay
    config = f"""module.exports = {{
  pdf_options: {{
    format: 'A4',
    margin: {{ top: '32mm', bottom: '15mm', left: '25mm', right: '25mm' }},
    displayHeaderFooter: false
  }},
  stylesheet: ['{css_abs_path}']
}};"""
    
    # Write config file
    config_path = os.path.join(output_dir, 'md2pdf-config.js')
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config)

    print(f'Generated:')
    print(f'  - {config_path}')
    print(f'  - CSS: {css_abs_path} (shared, no copy needed)')
    print(f'\nUsage:')
    print(f'  md-to-pdf input.md --config-file md2pdf-config.js')

if __name__ == '__main__':
    main()
