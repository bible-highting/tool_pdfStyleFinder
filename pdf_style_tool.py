#!/usr/bin/env python3
"""
PDF 텍스트 스팬의 시각적 속성(폰트, 크기, 색)으로 요약·검색하는 CLI.
IDML 없이 PDF만 사용합니다.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from typing import Any, Iterator

import fitz


def normalize_font_name(name: str) -> str:
    """서브셋 접두사(예: ABCDEF+MyFont)를 제거해 같은 패밀리로 묶기."""
    if not name:
        return ""
    return re.sub(r"^[A-Z]{6}\+", "", name)


def color_to_rgb(color: int) -> tuple[int, int, int]:
    if color < 0:
        return (0, 0, 0)
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    return (r, g, b)


def rgb_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


@dataclass(frozen=True)
class StyleKey:
    font: str
    size: float
    rgb: tuple[int, int, int]
    flags: int

    @classmethod
    def from_span(cls, span: dict[str, Any]) -> StyleKey:
        font = normalize_font_name(span.get("font") or "")
        size = round(float(span.get("size", 0)), 2)
        rgb = color_to_rgb(int(span.get("color", 0)))
        flags = int(span.get("flags", 0))
        return cls(font=font, size=size, rgb=rgb, flags=flags)

    def signature(self) -> str:
        return f"{self.font}|{self.size}|{rgb_hex(self.rgb)}|f{self.flags}"


def style_keys_match(
    ref: StyleKey,
    other: StyleKey,
    *,
    size_tolerance_pt: float = 0.0,
) -> bool:
    """
    ref와 other가 같은 서식으로 볼지 판별.
    - 글꼴·색(RGB)·flags 는 항상 일치해야 함.
    - size_tolerance_pt > 0 이면 글자 크기는 ±이 값 이내 허용, 0 이면 완전 일치.
    """
    if ref.font != other.font or ref.rgb != other.rgb or ref.flags != other.flags:
        return False
    if size_tolerance_pt <= 0.0:
        return ref.size == other.size
    return abs(ref.size - other.size) <= size_tolerance_pt + 1e-9


@dataclass
class SpanRecord:
    page: int
    bbox: tuple[float, float, float, float]
    text: str
    key: StyleKey


def iter_page_spans(doc: fitz.Document, pno_0based: int) -> Iterator[SpanRecord]:
    page = doc[pno_0based]
    td = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
    for block in td.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text") or ""
                if not text.strip():
                    continue
                bbox = tuple(span.get("bbox", (0, 0, 0, 0)))
                yield SpanRecord(
                    page=pno_0based + 1,
                    bbox=bbox,
                    text=text,
                    key=StyleKey.from_span(span),
                )


def page_spans(doc: fitz.Document, page_1based: int) -> list[SpanRecord]:
    p = page_1based - 1
    if p < 0 or p >= len(doc):
        return []
    return list(iter_page_spans(doc, p))


def iter_text_spans(doc: fitz.Document) -> Iterator[SpanRecord]:
    for pno in range(len(doc)):
        yield from iter_page_spans(doc, pno)


def cmd_dump(args: argparse.Namespace) -> int:
    doc = fitz.open(args.pdf)
    try:
        pno = args.page - 1
        if pno < 0 or pno >= len(doc):
            print(f"페이지 범위: 1–{len(doc)}", file=sys.stderr)
            return 1
        rows: list[dict[str, Any]] = []
        for rec in page_spans(doc, args.page):
            t = rec.text
            k = rec.key
            rows.append(
                {
                    "text": t[:200] + ("…" if len(t) > 200 else ""),
                    "font": k.font,
                    "size": k.size,
                    "color_hex": rgb_hex(k.rgb),
                    "flags": k.flags,
                    "bbox": list(rec.bbox),
                }
            )
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
        else:
            for i, r in enumerate(rows, 1):
                print(
                    f"{i:4d}  {r['size']:5.2f}pt  {r['color_hex']}  {r['font']!r}  "
                    f"{r['text']!r}"
                )
        return 0
    finally:
        doc.close()


def cmd_styles(args: argparse.Namespace) -> int:
    doc = fitz.open(args.pdf)
    try:
        from collections import Counter

        counts: Counter[str] = Counter()
        samples: dict[str, str] = {}
        for rec in iter_text_spans(doc):
            sig = rec.key.signature()
            counts[sig] += 1
            if sig not in samples:
                samples[sig] = rec.text.strip()[:80]
        items = sorted(counts.items(), key=lambda x: -x[1])
        if args.limit:
            items = items[: args.limit]
        for sig, n in items:
            k = sig.split("|")
            font, size_s, hexpart, fl = k[0], k[1], k[2], k[3]
            print(f"{n:6d}  {size_s}pt  {hexpart}  {font!r}  {fl}  ex:{samples[sig]!r}")
        return 0
    finally:
        doc.close()


def cmd_match(args: argparse.Namespace) -> int:
    doc = fitz.open(args.pdf)
    try:
        ref_key: StyleKey | None = None
        ref_sample = ""
        for rec in iter_text_spans(doc):
            if rec.page != args.page:
                continue
            if args.contains not in rec.text:
                continue
            ref_key = rec.key
            ref_sample = rec.text.strip()[:120]
            break
        if ref_key is None:
            print(
                f"페이지 {args.page}에서 --contains {args.contains!r} 를 포함한 스팬이 없습니다.",
                file=sys.stderr,
            )
            return 1
        print(
            f"기준: {ref_key.font!r} {ref_key.size}pt {rgb_hex(ref_key.rgb)} flags={ref_key.flags}"
        )
        print(f"예시 텍스트: {ref_sample!r}")
        tol = float(args.size_tol or 0.0)
        if tol > 0:
            print(f"모드: 크기 ±{tol}pt 허용, 글꼴·색·flags 동일")
        else:
            print("모드: 속성 완전 일치")
        print("---")
        total = 0
        for rec in iter_text_spans(doc):
            if not style_keys_match(ref_key, rec.key, size_tolerance_pt=tol):
                continue
            if args.max and total >= args.max:
                break
            total += 1
            snippet = rec.text.strip().replace("\n", " ")[:100]
            print(f"p.{rec.page}  {snippet!r}")
        print(f"---\n총 {total}개 스팬")
        return 0
    finally:
        doc.close()


def main() -> int:
    p = argparse.ArgumentParser(description="PDF 시각 속성(폰트·크기·색) CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("dump", help="한 페이지의 텍스트 스팬 속성 덤프")
    d.add_argument("pdf")
    d.add_argument("-p", "--page", type=int, default=1)
    d.add_argument("--json", action="store_true")
    d.set_defaults(func=cmd_dump)

    s = sub.add_parser("styles", help="문서 전체에서 속성 조합별 개수 요약")
    s.add_argument("pdf")
    s.add_argument("-n", "--limit", type=int, default=0, help="상위 N개만 (0=전부)")
    s.set_defaults(func=cmd_styles)

    m = sub.add_parser(
        "match",
        help="특정 페이지·문구가 속한 스팬과 동일한 속성의 스팬 모두 나열",
    )
    m.add_argument("pdf")
    m.add_argument("-p", "--page", type=int, required=True, help="기준 문구가 있는 페이지(1-based)")
    m.add_argument(
        "-c",
        "--contains",
        type=str,
        required=True,
        help="그 페이지에서 찾을 부분 문자열",
    )
    m.add_argument("--max", type=int, default=0, help="출력 상한 (0=제한 없음)")
    m.add_argument(
        "--size-tol",
        type=float,
        default=0.0,
        metavar="PT",
        help="글자 크기 허용 오차(pt). 0이면 완전 일치. 예: 0.2",
    )
    m.set_defaults(func=cmd_match)

    args = p.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
