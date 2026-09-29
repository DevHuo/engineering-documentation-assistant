import unittest
from pathlib import Path

from src.pdf_loader import extract_pdf_file


class PdfLoaderTests(unittest.TestCase):
    def test_demo_pdf_has_expected_pages(self):
        path = Path(__file__).parents[1] / "demo_docs" / "network_troubleshooting_guide.pdf"
        pages = extract_pdf_file(path)
        self.assertEqual(len(pages), 3)
        self.assertIn("Commissioning", pages[0].text)
        self.assertIn("Communication Timeout", pages[1].text)
        self.assertIn("Duplicate IP", pages[2].text)


if __name__ == "__main__":
    unittest.main()
