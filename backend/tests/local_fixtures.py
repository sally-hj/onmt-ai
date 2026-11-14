"""Fabrication de scans entièrement fictifs, avec rendu correct des caractères arabes."""
import html
import io

from PIL import Image
from playwright.sync_api import sync_playwright


def scanned_pdf(pages):
    images = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={'width': 1400, 'height': 900})
            page.route('**/*', lambda route: route.abort())
            for text, language in pages:
                direction = 'rtl' if language == 'ar' else 'ltr'
                page.set_content(f'<html lang="{language}" dir="{direction}"><meta charset="utf-8">'
                                 '<body style="font:38px Arial;line-height:1.8;padding:90px;background:white">'
                                 + html.escape(text) + '</body></html>')
                image = Image.open(io.BytesIO(page.screenshot())).convert('RGB')
                images.append(image)
        finally:
            browser.close()
    output = io.BytesIO()
    images[0].save(output, format='PDF', resolution=150, save_all=True, append_images=images[1:])
    for image in images:
        image.close()
    return output.getvalue()
