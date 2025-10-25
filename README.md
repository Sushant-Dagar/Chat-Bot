# 🧠 Local Command-Line Chatbot (Factual + Hugging Face)

## Overview
This chatbot can answer factual and general questions locally using Hugging Face's `google/flan-t5-small` model.
It includes predefined factual data for accurate responses and uses AI for other queries.

## Features
- Answers factual questions (e.g., presidents, capitals)
- Uses Hugging Face model for reasoning
- Works on CPU (no GPU required)
- Maintains short-term conversation memory

## Installation
```bash
pip install transformers torch sentencepiece
```

## Run
```bash
python interface.py
```

## Example
```
🤖 Local CLI Chatbot (Factual + FLAN-T5)
Type '/exit' to quit.

User: what is the capital of italy
Bot: Rome
User: who is the president of india
Bot: Droupadi Murmu
User: tell me a joke
Bot: Why did the computer get cold? Because it left its Windows open.
```
