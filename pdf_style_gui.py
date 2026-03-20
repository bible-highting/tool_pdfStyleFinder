#!/usr/bin/env python3
"""PDF 시각 서식 탐색 GUI (tkinter + PyMuPDF)."""

from __future__ import annotations

import argparse
import sys
import threading
import tkinter as tk
from collections import Counter
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import fitz

from pdf_style_tool import (
    StyleKey,
    iter_text_spans,
    page_spans,
    rgb_hex,
    style_keys_match,
)


class PdfStyleApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("PDF 서식 찾기")
        self.minsize(880, 520)
        self.geometry("960x640")

        self._doc: fitz.Document | None = None
        self._pdf_path: str = ""
        self._page_records: list = []

        self._build_ui()

    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=8)
        top.pack(fill=tk.X)

        ttk.Button(top, text="PDF 열기…", command=self._open_pdf).pack(side=tk.LEFT)
        self._path_var = tk.StringVar(value="파일을 선택하세요")
        ttk.Label(top, textvariable=self._path_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(12, 0)
        )
        self._pages_var = tk.StringVar(value="")
        ttk.Label(top, textvariable=self._pages_var).pack(side=tk.RIGHT)

        row2 = ttk.Frame(self, padding=(8, 0, 8, 8))
        row2.pack(fill=tk.X)

        ttk.Label(row2, text="페이지").pack(side=tk.LEFT)
        self._page_var = tk.StringVar(value="1")
        self._page_spin = ttk.Spinbox(
            row2,
            from_=1,
            to=1,
            width=6,
            textvariable=self._page_var,
        )
        self._page_spin.pack(side=tk.LEFT, padx=(4, 12))

        ttk.Button(row2, text="이 페이지 스팬 보기", command=self._load_page_spans).pack(
            side=tk.LEFT
        )
        ttk.Button(
            row2,
            text="선택한 줄과 동일 서식 찾기",
            command=self._find_same_style,
        ).pack(side=tk.LEFT, padx=(12, 0))
        ttk.Button(row2, text="문서 서식 요약…", command=self._style_summary).pack(
            side=tk.LEFT, padx=(12, 0)
        )

        row_tol = ttk.Frame(self, padding=(8, 0, 8, 4))
        row_tol.pack(fill=tk.X)
        self._fuzzy_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            row_tol,
            text="거의 같은 서식",
            variable=self._fuzzy_var,
            command=self._toggle_tol_widgets,
        ).pack(side=tk.LEFT)
        ttk.Label(row_tol, text="크기 ±(pt)").pack(side=tk.LEFT, padx=(8, 4))
        self._size_tol_var = tk.StringVar(value="0.2")
        self._tol_spin = ttk.Spinbox(
            row_tol,
            from_=0.0,
            to=5.0,
            increment=0.05,
            width=6,
            textvariable=self._size_tol_var,
        )
        self._tol_spin.pack(side=tk.LEFT)
        ttk.Label(
            row_tol,
            text="(글꼴·색·굵기/기울임 플래그는 동일해야 함)",
            foreground="gray",
        ).pack(side=tk.LEFT, padx=(12, 0))

        paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        upper = ttk.Frame(paned, padding=0)
        paned.add(upper, weight=2)
        ttk.Label(
            upper,
            text="이 페이지의 텍스트 스팬 (한 줄을 선택한 뒤 「동일 서식 찾기」)",
        ).pack(anchor=tk.W)
        u_wrap = ttk.Frame(upper)
        u_wrap.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        cols = ("size", "color", "font", "text")
        self._span_tree = ttk.Treeview(
            u_wrap,
            columns=cols,
            show="headings",
            selectmode="browse",
            height=12,
        )
        self._span_tree.heading("size", text="크기(pt)")
        self._span_tree.heading("color", text="색")
        self._span_tree.heading("font", text="글꼴")
        self._span_tree.heading("text", text="텍스트")
        self._span_tree.column("size", width=72, anchor=tk.CENTER)
        self._span_tree.column("color", width=88, anchor=tk.CENTER)
        self._span_tree.column("font", width=200, anchor=tk.W)
        self._span_tree.column("text", width=480, anchor=tk.W)
        sy = ttk.Scrollbar(u_wrap, orient=tk.VERTICAL, command=self._span_tree.yview)
        self._span_tree.configure(yscrollcommand=sy.set)
        self._span_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sy.pack(side=tk.RIGHT, fill=tk.Y)

        lower = ttk.Frame(paned, padding=0)
        paned.add(lower, weight=1)
        lower_head = ttk.Frame(lower)
        lower_head.pack(fill=tk.X)
        ttk.Label(
            lower_head,
            text="검색 결과 (더블클릭: 페이지 이동 · ⌘/Ctrl+C: 선택 행 복사)",
        ).pack(side=tk.LEFT, anchor=tk.W)
        ttk.Button(
            lower_head,
            text="전체 표 복사 (탭)",
            command=self._copy_all_hits_tsv,
        ).pack(side=tk.RIGHT, padx=(8, 0))
        l_wrap = ttk.Frame(lower)
        l_wrap.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        rcols = ("page", "text")
        self._hit_tree = ttk.Treeview(
            l_wrap,
            columns=rcols,
            show="headings",
            selectmode="extended",
            height=8,
        )
        self._hit_tree.heading("page", text="페이지")
        self._hit_tree.heading("text", text="텍스트")
        self._hit_tree.column("page", width=64, anchor=tk.CENTER)
        self._hit_tree.column("text", width=820, anchor=tk.W)
        ry = ttk.Scrollbar(l_wrap, orient=tk.VERTICAL, command=self._hit_tree.yview)
        self._hit_tree.configure(yscrollcommand=ry.set)
        self._hit_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ry.pack(side=tk.RIGHT, fill=tk.Y)
        self._hit_tree.bind("<Double-1>", self._on_hit_double)
        self._hit_tree.bind("<Control-c>", self._on_hit_tree_copy_shortcut)
        if sys.platform == "darwin":
            self._hit_tree.bind("<Command-c>", self._on_hit_tree_copy_shortcut)

        self._status = tk.StringVar(value="준비됨")
        ttk.Label(self, textvariable=self._status, padding=(8, 0, 8, 8)).pack(
            fill=tk.X, anchor=tk.W
        )

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._toggle_tol_widgets()

    @staticmethod
    def _tsv_cell(value: object) -> str:
        s = "" if value is None else str(value)
        s = s.replace("\r\n", "\n").replace("\r", "\n")
        return s.replace("\t", " ").replace("\n", " ")

    def _hits_to_tsv(self, item_ids: tuple[str, ...] | list[str]) -> str:
        lines = ["페이지\t텍스트"]
        for iid in item_ids:
            vals = self._hit_tree.item(iid, "values")
            if len(vals) < 2:
                page, text = (vals[0] if vals else ""), ""
            else:
                page, text = vals[0], vals[1]
            lines.append(f"{self._tsv_cell(page)}\t{self._tsv_cell(text)}")
        return "\n".join(lines) + "\n"

    def _clipboard_set_text(self, text: str, status_msg: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update_idletasks()
        self._status.set(status_msg)

    def _copy_all_hits_tsv(self) -> None:
        items = self._hit_tree.get_children()
        if not items:
            messagebox.showinfo("안내", "복사할 검색 결과가 없습니다.")
            return
        tsv = self._hits_to_tsv(items)
        self._clipboard_set_text(tsv, f"클립보드: 검색 결과 {len(items)}행 (탭 구분)")

    def _on_hit_tree_copy_shortcut(self, _evt: tk.Event) -> str:
        sel = self._hit_tree.selection()
        if sel:
            tsv = self._hits_to_tsv(sel)
            self._clipboard_set_text(tsv, f"클립보드: 선택 {len(sel)}행 (탭 구분)")
        else:
            self._copy_all_hits_tsv()
        return "break"

    def _toggle_tol_widgets(self) -> None:
        state = tk.NORMAL if self._fuzzy_var.get() else tk.DISABLED
        self._tol_spin.configure(state=state)

    def _get_size_tolerance(self) -> float:
        if not self._fuzzy_var.get():
            return 0.0
        try:
            v = float(self._size_tol_var.get().replace(",", "."))
        except ValueError:
            return 0.2
        return max(0.0, v)

    def _set_busy(self, busy: bool, msg: str = "") -> None:
        if busy:
            self._status.set(msg or "처리 중…")
            self.config(cursor="watch")
        else:
            self._status.set("준비됨")
            self.config(cursor="")

    def _load_pdf_path(self, path: str) -> bool:
        p = Path(path)
        if not p.is_file():
            messagebox.showerror("오류", f"파일이 없습니다.\n{path}")
            return False
        try:
            if self._doc:
                self._doc.close()
            self._doc = fitz.open(str(p))
        except Exception as e:
            messagebox.showerror("오류", f"PDF를 열 수 없습니다.\n{e}")
            return False
        self._pdf_path = str(p)
        self._path_var.set(self._pdf_path)
        n = len(self._doc)
        self._pages_var.set(f"총 {n}페이지")
        self._page_spin.config(to=max(1, n))
        self._page_var.set("1")
        self._clear_trees()
        self._status.set("PDF 로드됨 — 페이지를 고르고 「스팬 보기」를 누르세요.")
        return True

    def _open_pdf(self) -> None:
        path = filedialog.askopenfilename(
            title="PDF 선택",
            filetypes=[("PDF", "*.pdf"), ("모든 파일", "*.*")],
        )
        if not path:
            return
        self._load_pdf_path(path)

    def _clear_trees(self) -> None:
        self._page_records.clear()
        for iid in self._span_tree.get_children():
            self._span_tree.delete(iid)
        for iid in self._hit_tree.get_children():
            self._hit_tree.delete(iid)

    def _load_page_spans(self) -> None:
        if not self._doc:
            messagebox.showinfo("안내", "먼저 PDF를 여세요.")
            return
        try:
            p = int(self._page_var.get().strip())
        except ValueError:
            messagebox.showwarning("안내", "페이지 번호는 숫자여야 합니다.")
            return
        recs = page_spans(self._doc, p)
        for iid in self._span_tree.get_children():
            self._span_tree.delete(iid)
        self._page_records = recs
        for i, rec in enumerate(recs):
            k = rec.key
            preview = rec.text.replace("\n", " ").strip()
            if len(preview) > 120:
                preview = preview[:117] + "…"
            self._span_tree.insert(
                "",
                tk.END,
                iid=str(i),
                values=(f"{k.size:g}", rgb_hex(k.rgb), k.font, preview),
            )
        self._status.set(f"페이지 {p} — 스팬 {len(recs)}개")

    def _find_same_style(self) -> None:
        if not self._doc:
            messagebox.showinfo("안내", "먼저 PDF를 여세요.")
            return
        sel = self._span_tree.selection()
        if not sel:
            messagebox.showinfo("안내", "위 목록에서 한 줄을 선택하세요.")
            return
        idx = int(sel[0])
        if idx < 0 or idx >= len(self._page_records):
            return
        key = self._page_records[idx].key
        tol = self._get_size_tolerance()
        for iid in self._hit_tree.get_children():
            self._hit_tree.delete(iid)

        doc = self._doc

        def work() -> None:
            hits: list[tuple[int, str]] = []
            try:
                for rec in iter_text_spans(doc):
                    if not style_keys_match(key, rec.key, size_tolerance_pt=tol):
                        continue
                    t = rec.text.replace("\n", " ").strip()
                    if len(t) > 200:
                        t = t[:197] + "…"
                    hits.append((rec.page, t))
            except Exception as e:

                def err() -> None:
                    self._set_busy(False)
                    messagebox.showerror("오류", str(e))

                self.after(0, err)
                return

            def done() -> None:
                for i, (pg, t) in enumerate(hits):
                    self._hit_tree.insert("", tk.END, iid=str(i), values=(pg, t))
                self._set_busy(False)
                mode = f"크기 ±{tol}pt" if tol > 0 else "완전 일치"
                self._status.set(
                    f"{len(hits)}곳 ({mode}) — {key.font} ~{key.size}pt {rgb_hex(key.rgb)}"
                )

            self.after(0, done)

        self._set_busy(True, "문서 전체 검색 중…")
        threading.Thread(target=work, daemon=True).start()

    def _style_summary(self) -> None:
        if not self._doc:
            messagebox.showinfo("안내", "먼저 PDF를 여세요.")
            return
        doc = self._doc
        self._set_busy(True, "서식 요약 수집 중…")

        def work() -> None:
            counts: Counter[str] = Counter()
            samples: dict[str, str] = {}
            keys: dict[str, StyleKey] = {}
            try:
                for rec in iter_text_spans(doc):
                    sig = rec.key.signature()
                    counts[sig] += 1
                    if sig not in keys:
                        keys[sig] = rec.key
                        samples[sig] = rec.text.replace("\n", " ").strip()[:72]
            except Exception as e:

                def err() -> None:
                    self._set_busy(False)
                    messagebox.showerror("오류", str(e))

                self.after(0, err)
                return

            rows = sorted(counts.items(), key=lambda x: -x[1])

            def done() -> None:
                self._set_busy(False)
                win = tk.Toplevel(self)
                win.title("문서 서식 요약")
                win.minsize(720, 400)
                win.geometry("800x480")
                cols = ("cnt", "size", "color", "font", "flags", "sample")
                tree = ttk.Treeview(win, columns=cols, show="headings", height=20)
                tree.heading("cnt", text="개수")
                tree.heading("size", text="pt")
                tree.heading("color", text="색")
                tree.heading("font", text="글꼴")
                tree.heading("flags", text="flags")
                tree.heading("sample", text="예시")
                tree.column("cnt", width=56, anchor=tk.CENTER)
                tree.column("size", width=56, anchor=tk.CENTER)
                tree.column("color", width=80, anchor=tk.CENTER)
                tree.column("font", width=180, anchor=tk.W)
                tree.column("flags", width=52, anchor=tk.CENTER)
                tree.column("sample", width=360, anchor=tk.W)
                sy = ttk.Scrollbar(win, orient=tk.VERTICAL, command=tree.yview)
                tree.configure(yscrollcommand=sy.set)
                tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=8)
                sy.pack(side=tk.LEFT, fill=tk.Y, pady=8)
                for i, (sig, c) in enumerate(rows):
                    k = keys[sig]
                    tree.insert(
                        "",
                        tk.END,
                        iid=str(i),
                        values=(
                            c,
                            f"{k.size:g}",
                            rgb_hex(k.rgb),
                            k.font,
                            k.flags,
                            samples.get(sig, ""),
                        ),
                    )
                ttk.Label(
                    win,
                    text="이 창은 참고용입니다. 특정 서식을 찾으려면 해당 페이지에서 스팬을 선택하세요.",
                ).pack(fill=tk.X, padx=8, pady=(0, 8))

            self.after(0, done)

        threading.Thread(target=work, daemon=True).start()

    def _on_hit_double(self, _evt: tk.Event) -> None:
        sel = self._hit_tree.selection()
        if not sel:
            return
        vals = self._hit_tree.item(sel[0], "values")
        if not vals:
            return
        try:
            pg = int(vals[0])
        except (ValueError, TypeError):
            return
        self._page_var.set(str(pg))
        self._load_page_spans()

    def _on_close(self) -> None:
        if self._doc:
            self._doc.close()
            self._doc = None
        self.destroy()


def main() -> None:
    ap = argparse.ArgumentParser(description="PDF 서식 찾기")
    ap.add_argument("pdf", nargs="?", help="시작 시 열 PDF 경로")
    ns = ap.parse_args()

    app = PdfStyleApp()
    if ns.pdf:
        p = ns.pdf
        app.after(80, lambda: app._load_pdf_path(p))

    app.mainloop()


if __name__ == "__main__":
    main()
