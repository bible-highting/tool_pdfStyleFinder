# PDF 서식 찾기

인디자인 등에서보낸 PDF에서 **글꼴·글자 크기·색** 등 **화면에 보이는 텍스트 속성**이 같은 구간을 찾는 도구입니다. IDML이 없어도 **PDF 파일만** 있으면 됩니다.

---

## 목차

1. [이 도구로 할 수 있는 일](#features)
2. [준비물](#requirements)
3. [프로젝트 받기](#download)
4. [설치 (처음 한 번)](#install)
5. [GUI로 쓰는 방법](#gui)
6. [명령줄(CLI)로 쓰는 방법](#cli)
7. [「같은 서식」이 어떻게 정해지나요?](#how-matching-works)
8. [알아두면 좋은 점과 한계](#notes-and-limitations)
9. [자주 묻는 문제](#faq)
10. [테스트 실행 (개발·기여 시)](#running-tests)

---

<a id="features"></a>

## 이 도구로 할 수 있는 일
- PDF에서 글씨 크기, 색상, 폰트 서식별로 글자를 찾을 수 있습니다.
- 한 페이지에서 **한 줄을 골라** 그 줄과 **같은 시각 속성**을 가진 텍스트가 문서 **어느 페이지에 몇 군데** 있는지 찾습니다.
- 본문이 아니라 특정 서식만 검색하고 싶을 때 사용하면 좋습니다. 
- 이럴 때 쓰면 좋습니다 ➊ 단계 숫자, [미친 활용 00]만 뽑아서 숫자흐름이 맞는지 확인할 수 있습니다.
- 이럴 때 쓰면 좋습니다 ➋ 최종 목차 확인시 챕터 제목 서식, 중제목 서식만 뽑아서 페이지를 비교할 수 있습니다.

> **주의:** PDF에 들어 있는 “태그”나 접근성 구조가 아니라, **렌더링에 쓰인 텍스트 런(run)의 속성**을 기준으로 합니다. 그래서 인디자인에서 보이는 것과 거의 같게 맞추는 용도에 가깝습니다.

---

<a id="requirements"></a>

## 준비물

| 항목 | 설명 |
|------|------|
| **Python** | **3.10 이상** 권장. 터미널(또는 명령 프롬프트)에서 `python3 --version` 으로 확인하세요. |
| **인터넷** | 처음 설치할 때 `pip`로 패키지를 받습니다. |
| **tkinter** | GUI에 사용합니다. macOS·Windows의 공식 Python에는 보통 포함되어 있습니다. **Linux**에서는 배포판에 따라 `python3-tk` 패키지를 따로 설치해야 할 수 있습니다. (아래 [자주 묻는 문제](#faq) 참고) |

의존성 라이브러리는 `requirements.txt`에 적혀 있으며, 핵심은 **[PyMuPDF](https://pymupdf.readthedocs.io/)** 입니다.

---

<a id="download"></a>

## 프로젝트 받기

### 방법 A: Git이 있는 경우

원하는 폴더에서:

```bash
git clone <여기에-저장소-URL>
cd pdf_style
```

(`pdf_style` 대신 실제 클론한 폴더 이름을 쓰세요.)

### 방법 B: ZIP으로 받는 경우

GitHub 저장소 페이지에서 **Code → Download ZIP** 으로 내려받은 뒤, 압축을 풀고 그 폴더로 터미널을 연 다음, 아래 설치 단계를 **그 폴더 안에서** 진행하면 됩니다.

---

<a id="install"></a>

## 설치 (처음 한 번)

**항상 프로젝트 루트**( `pdf_style_gui.py` 와 `requirements.txt` 가 있는 폴더)에서 작업합니다.

### 1) 가상환경 만들기

가상환경을 쓰면 다른 Python 프로젝트와 패키지가 섞이지 않아서 안전합니다.

**macOS / Linux**

```bash
python3 -m venv .venv
```

**Windows (PowerShell 또는 CMD)**

```bash
python -m venv .venv
```

(`python` 이 안 되면 `py -3 -m venv .venv` 를 시도해 보세요.)

### 2) 가상환경 활성화

**macOS / Linux**

```bash
source .venv/bin/activate
```

프롬프트 앞에 `(.venv)` 가 보이면 성공입니다.

**Windows CMD**

```bash
.venv\Scripts\activate.bat
```

**Windows PowerShell**

```bash
.venv\Scripts\Activate.ps1
```

> PowerShell에서 스크립트 실행이 막혀 있으면, 관리자 권한이 아닌 경우 한 번만  
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`  
> 를 허용해야 할 수 있습니다.

### 3) 패키지 설치

가상환경이 **켜진 상태**에서:

```bash
pip install -r requirements.txt
```

끝입니다. 이후부터는 **같은 폴더에서** GUI나 CLI를 실행하면 됩니다.

### 설치 없이 매번 실행만 하고 싶을 때

가상환경을 매번 켜기 귀찮다면, 아래처럼 **풀 경로**로 Python을 지정해도 됩니다.

**macOS / Linux**

```bash
.venv/bin/python pdf_style_gui.py
.venv/bin/python pdf_style_tool.py --help
```

**Windows**

```bash
.venv\Scripts\python.exe pdf_style_gui.py
.venv\Scripts\python.exe pdf_style_tool.py --help
```

---

<a id="gui"></a>

## GUI로 쓰는 방법

### 실행

가상환경을 활성화한 뒤:

```bash
python pdf_style_gui.py
```

PDF 경로를 미리 알고 있다면:

```bash
python pdf_style_gui.py "/경로/문서.pdf"
```

**macOS**에서는 프로젝트에 포함된 **`PDF 서식 찾기 실행.command`** 를 더블클릭해도 됩니다. (터미널이 열리며 실행됩니다. 처음에는 보안 경고가 나오면 **우클릭 → 열기**로 한 번 허용하세요.)

### 화면 구성과 추천 순서

1. **「PDF 열기…」**  
   분석할 PDF를 고릅니다. 상단에 전체 페이지 수가 표시됩니다.

2. **페이지 번호**를 고른 뒤 **「이 페이지 스팬 보기」**  
   위쪽 표에 그 페이지의 텍스트가 **스팬** 단위로 나옵니다. 열은 **크기(pt), 색, 글꼴, 텍스트** 입니다.

3. 위 표에서 **찾고 싶은 서식을 대표하는 한 줄을 클릭**해 선택합니다.

4. **「선택한 줄과 동일 서식 찾기」**  
   문서 **전체**를 뒤져서, 선택한 줄과 같은 시각 속성인 구간을 아래 **검색 결과** 표에 모읍니다. (큰 파일은 잠시 “처리 중”이 보일 수 있습니다.)

5. **검색 결과**에서 **행을 더블클릭**하면 해당 **페이지로 이동**하고, 다시 **「이 페이지 스팬 보기」** 로 그 페이지 스팬을 볼 수 있습니다.

6. **「문서 서식 요약…」**  
   문서 안에 등장하는 **서식 조합마다 몇 번 쓰였는지**, 예시 텍스트와 함께 새 창으로 보여 줍니다. 전체 구조를 파악할 때 유용합니다.

### 「거의 같은 서식」 옵션

- **「거의 같은 서식」** 을 켜면 **글자 크기**만 **±지정 pt** 범위에서 달라도 같은 서식으로 봅니다. (기본값은 **0.2pt** 근처로 두는 경우가 많습니다.)
- **글꼴 이름·색(RGB)·굵기/기울임 등(flags)** 은 **반드시 같아야** 합니다. 크기만 살짝 다른 경우에 쓰기 좋습니다.
- 끄면 **크기까지 완전히 같은 경우만** 매칭합니다.

### 복사 기능

- 검색 결과에서 **⌘+C (macOS) / Ctrl+C (Windows·Linux)** : 선택한 행을 **탭으로 구분된 텍스트**로 클립보드에 복사합니다. (선택이 없으면 전체 결과 복사 동작이 될 수 있습니다.)
- **「전체 표 복사 (탭)」** : 검색 결과 전체를 한 번에 복사합니다. 스프레드시트에 붙여넣기 좋습니다.

---

<a id="cli"></a>

## 명령줄(CLI)로 쓰는 방법

실행 파일은 `pdf_style_tool.py` 입니다. 하위 명령이 **3가지** 있습니다.

```bash
python pdf_style_tool.py --help
python pdf_style_tool.py dump --help
python pdf_style_tool.py styles --help
python pdf_style_tool.py match --help
```

아래 예시는 가상환경을 켠 뒤 `python` 이 프로젝트 루트에서 실행된다고 가정합니다.

### `dump` — 한 페이지의 스팬 목록

지정한 **한 페이지**의 텍스트 스팬과 속성을 출력합니다.

```bash
python pdf_style_tool.py dump 문서.pdf -p 1
```

- `-p` / `--page` : 페이지 번호 (**1부터** 시작). 기본값 `1`.
- `--json` : 사람이 읽기 쉬운 텍스트 대신 **JSON**으로 출력 (다른 프로그램에서 파싱할 때 유용).

### `styles` — 문서 전체 서식 요약

문서 전체를 돌면서 **같은 속성 조합**이 몇 번 나왔는지 **많이 쓰인 순**으로 나열합니다.

```bash
python pdf_style_tool.py styles 문서.pdf
```

- `-n` / `--limit` : **상위 N개**만 출력. `0`(기본)이면 전부.

### `match` — 특정 문구가 속한 스팬과 “같은 서식” 전부

**어느 페이지**에서 **어떤 글자열**이 들어 있는 스팬을 하나 찾아 그 스팬의 속성을 기준으로, **문서 전체**에서 같은 속성인 스팬을 나열합니다.

```bash
python pdf_style_tool.py match 문서.pdf -p 3 -c "제목일부"
```

- `-p` / `--page` : 기준 문구를 찾을 **페이지 (필수, 1부터)**  
- `-c` / `--contains` : 그 페이지 안에서 찾을 **부분 문자열 (필수)**  
  - **첫 번째로 걸리는 스팬**이 기준이 됩니다. 문구가 여러 스팬에 나뉘어 있으면 원하는 줄이 안 나올 수 있으니, **짧고 특징 있는 덩어리**를 넣는 것이 좋습니다.
- `--size-tol PT` : 글자 크기 허용 오차(pt). `0`(기본)이면 완전 일치. 예: `0.2`
- `--max N` : 출력 **최대 개수**. `0`(기본)이면 제한 없음.

---


<a id="notes-and-limitations"></a>

## 알아두면 좋은 점과 한계

- PDF는 **어떻게 만들었는지**에 따라 같은 단락이 **여러 스팬으로 쪼개져** 보일 수 있습니다. 그럴 때는 GUI에서 줄을 잘 골라야 합니다.
- **이미지로 박힌 글자**는 텍스트 스팬이 아니라서 이 도구로는 잡히지 않습니다.
- **보안·암호**로 열기가 막힌 PDF는 먼저 열 수 있게 해야 합니다.
- 이 저장소의 `.gitignore`에는 **`*.pdf`가 제외**되어 있습니다. **원고·개인 문서를 실수로 GitHub에 올리지 않도록** 한 설정이니, 샘플 PDF를 넣고 싶다면 정책을 팀과 맞추세요.

---

<a id="faq"></a>

## 자주 묻는 문제

### `ModuleNotFoundError: No module named 'fitz'` (또는 `pymupdf`)

가상환경을 **활성화한 상태**에서 `pip install -r requirements.txt` 를 다시 실행했는지 확인하세요.  
또한 실행할 때 `python` 이 **그 가상환경의 Python**인지 확인하세요 (`which python` / `where python`).

### GUI 실행 시 `tkinter` 관련 오류 (특히 Linux)

Ubuntu 계열 예:

```bash
sudo apt update
sudo apt install python3-tk
```

배포판마다 패키지 이름이 다를 수 있습니다.

### macOS에서 “개발자를 확인할 수 없음” (`.command` 실행 시)

**우클릭 → 열기** 로 한 번 실행을 허용하거나, 시스템 설정에서 해당 파일 실행을 허용하세요.

### Windows에서 `python` 을 못 찾겠다고 나올 때

Microsoft Store 대신 [python.org](https://www.python.org/downloads/) 에서 설치했는지 확인하고, 설치 시 **“Add Python to PATH”** 를 켰는지 확인하세요. 또는 `py` 런처를 사용해 보세요.

---
