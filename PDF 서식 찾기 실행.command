#!/bin/bash
# 더블클릭으로 PDF 서식 찾기 GUI 실행 (macOS Terminal)
# README대로 만든 .venv가 있으면 그 Python을 씁니다.

DIR="$(cd "$(dirname "$0")" && pwd)" || exit 1
cd "$DIR" || exit 1

PYTHON=""
if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
elif command -v python3 &>/dev/null; then
  PYTHON="python3"
else
  echo "python3를 찾을 수 없습니다. Xcode Command Line Tools 또는 Python을 설치하세요."
  read -r -p "Enter를 누르면 창이 닫힙니다..."
  exit 1
fi

"$PYTHON" pdf_style_gui.py
status=$?
if [ "$status" -ne 0 ]; then
  echo
  echo "실행 중 오류가 발생했습니다 (종료 코드: $status)"
  if [ ! -x ".venv/bin/python" ]; then
    echo "힌트: README의 「설치」대로 이 폴더에서 .venv를 만들고 pip install -r requirements.txt 를 실행해 보세요."
  fi
  read -r -p "Enter를 누르면 창이 닫힙니다..."
fi
exit "$status"
