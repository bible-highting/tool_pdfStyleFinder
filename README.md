# PDF 서식 찾기 (tool_pdfStyleFinder)

인디자인 등에서보낸 PDF에서 **글꼴·크기·색** 등 시각 속성이 같은 텍스트 구간을 찾는 도구입니다. IDML 없이 PDF만 사용합니다.

## 요구 사항

- Python 3.10+
- [PyMuPDF](https://pymupdf.readthedocs.io/) (`requirements.txt` 참고)

## 설치

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 실행

**GUI**

```bash
.venv/bin/python pdf_style_gui.py
.venv/bin/python pdf_style_gui.py /path/to/document.pdf
```

**CLI**

```bash
.venv/bin/python pdf_style_tool.py dump document.pdf -p 1
.venv/bin/python pdf_style_tool.py match document.pdf -p 1 -c "문자열" --size-tol 0.2
```

## 테스트

로컬에 임의의 `.pdf`를 프로젝트 폴더에 두면 스모크 테스트가 실행됩니다. **저장소에는 PDF를 올리지 마세요** (`.gitignore`에 `*.pdf` 포함).

```bash
.venv/bin/python -m unittest tests.test_smoke -v
```

## 라이선스

필요 시 저장소에 `LICENSE`를 추가하세요.
