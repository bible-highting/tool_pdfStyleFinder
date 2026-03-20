"""스모크·단위 테스트."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import fitz  # noqa: E402

from pdf_style_tool import (  # noqa: E402
    StyleKey,
    iter_text_spans,
    page_spans,
    style_keys_match,
)


def _any_project_pdf() -> Path | None:
    pdfs = sorted(ROOT.glob("*.pdf"))
    return pdfs[0] if pdfs else None


class TestStyleKeysMatch(unittest.TestCase):
    def test_exact_size(self) -> None:
        a = StyleKey("KoPub", 9.8, (35, 31, 32), 0)
        b = StyleKey("KoPub", 9.8, (35, 31, 32), 0)
        self.assertTrue(style_keys_match(a, b, size_tolerance_pt=0.0))
        self.assertTrue(style_keys_match(a, b, size_tolerance_pt=0.2))

    def test_fuzzy_size(self) -> None:
        ref = StyleKey("KoPub", 9.8, (35, 31, 32), 0)
        near = StyleKey("KoPub", 9.7, (35, 31, 32), 0)
        self.assertFalse(style_keys_match(ref, near, size_tolerance_pt=0.0))
        self.assertTrue(style_keys_match(ref, near, size_tolerance_pt=0.2))

    def test_color_must_match(self) -> None:
        a = StyleKey("KoPub", 9.8, (35, 31, 32), 0)
        b = StyleKey("KoPub", 9.79, (0, 0, 0), 0)
        self.assertFalse(style_keys_match(a, b, size_tolerance_pt=1.0))

    def test_font_must_match(self) -> None:
        a = StyleKey("A", 10.0, (0, 0, 0), 0)
        b = StyleKey("B", 10.0, (0, 0, 0), 0)
        self.assertFalse(style_keys_match(a, b, size_tolerance_pt=0.5))


class TestPdfSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pdf = _any_project_pdf()

    def test_any_pdf_exists(self) -> None:
        if self.pdf is None:
            self.skipTest(f"프로젝트 폴더에 *.pdf 없음: {ROOT}")

    def test_open_and_iter_spans(self) -> None:
        if self.pdf is None:
            self.skipTest("PDF 없음")
        doc = fitz.open(self.pdf)
        try:
            self.assertGreater(len(doc), 0, "페이지가 0입니다.")
            n = sum(1 for _ in iter_text_spans(doc))
            self.assertGreater(n, 0, "추출된 텍스트 스팬이 없습니다.")
        finally:
            doc.close()

    def test_first_page_has_spans(self) -> None:
        if self.pdf is None:
            self.skipTest("PDF 없음")
        doc = fitz.open(self.pdf)
        try:
            recs = page_spans(doc, 1)
            self.assertGreater(len(recs), 0, "1페이지에 스팬이 없습니다.")
        finally:
            doc.close()


if __name__ == "__main__":
    unittest.main()
