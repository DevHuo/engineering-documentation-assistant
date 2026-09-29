import unittest

from src.chunking import chunk_pages
from src.models import PageText


class ChunkingTests(unittest.TestCase):
    def test_chunking_preserves_page_metadata(self):
        page = PageText(document="manual.pdf", page=7, text=("alpha beta gamma. " * 120))
        chunks = chunk_pages([page], chunk_size=220, overlap=40, min_chunk_chars=20)
        self.assertGreater(len(chunks), 2)
        self.assertTrue(all(chunk.document == "manual.pdf" for chunk in chunks))
        self.assertTrue(all(chunk.page == 7 for chunk in chunks))
        self.assertEqual(len({chunk.id for chunk in chunks}), len(chunks))

    def test_invalid_overlap_is_rejected(self):
        page = PageText(document="x.pdf", page=1, text="some text")
        with self.assertRaises(ValueError):
            chunk_pages([page], chunk_size=100, overlap=100)


if __name__ == "__main__":
    unittest.main()
