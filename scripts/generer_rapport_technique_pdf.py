"""Generate the technical report PDF from its HTML source using Playwright."""

from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "rapport-technique.html"
OUTPUT = ROOT / "docs" / "rapport-technique-stage-unifunl.pdf"


def main():
    html = SOURCE.read_text(encoding="utf-8")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="load")
        page.pdf(
            path=str(OUTPUT),
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
            display_header_footer=True,
            header_template="<div></div>",
            footer_template=(
                '<div style="font-size:8px;color:#68768d;width:100%;'
                'text-align:center">Projet Stage Unifunl · Rapport technique '
                '<span class="pageNumber"></span> / '
                '<span class="totalPages"></span></div>'
            ),
        )
        browser.close()
    print(f"PDF genere : {OUTPUT}")


if __name__ == "__main__":
    main()
