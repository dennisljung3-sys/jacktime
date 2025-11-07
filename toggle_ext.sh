#!/bin/bash

# Växla mellan .py och .txt
if ls *.py &>/dev/null; then
  for file in *.py; do
    mv "$file" "${file%.py}.txt"
  done
  echo "Alla .py-filer har döpts om till .txt"
elif ls *.txt &>/dev/null; then
  for file in *.txt; do
    mv "$file" "${file%.txt}.py"
  done
  echo "Alla .txt-filer har döpts om till .py"
else
  echo "Inga .py eller .txt-filer hittades"
fi

