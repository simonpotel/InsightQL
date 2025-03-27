# InsightQL

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Ollama](https://img.shields.io/badge/Ollama-0.4.0%2B-orange)](https://ollama.ai/)

A simple tool to search and chat with your local documents using LLMs running through Ollama.

## Overview

InsightQL lets you ask questions about your documents using a local LLM. It indexes your files in a SQLite database and retrieves relevant information based on your queries.

## Requirements

- Python 3.8+
- [Ollama](https://ollama.ai/)

## Quick Start

```bash
# get the code
git clone https://github.com/yourusername/InsightQL.git
cd InsightQL

# install dependencies
pip install -r requirements.txt

# make sure Ollama is running
ollama serve

# run the app
python main.py
```


## Memory Consumption Tracking

| Component | Model | RAM Usage (GB) | VRAM Usage (GB) | Notes |
|-----------|-------|----------------|-----------------|-------|
| Ollama    | llama3.2 | 5.5 - 8.0 | 7.0 - 9.0 | |
| Ollama    | phi-3-mini | 2.5 - 4.0 | 3.0 - 4.5 | |
| Ollama    | mistral-7b-instruct | 4.0 - 6.0 | 5.0 - 7.0 | |
| InsightQL | | 0.2 - 0.5 | | |


## Tested Usage

### Example Configuration

```
Model: llama3.2 (default)
Documents: 5 files (.llm format)
Total content: ~972 segments from educational materials
Database size: 2.6 MB
Indexed terms: 16,427
Document count: 1,032 chunks
Average query time: 0.8 seconds
Memory usage: 5.8GB RAM (Ollama) + 0.2GB (InsightQL)
```

This configuration was tested on a Windows system for full-text search capabilities. The indexed content consists of educational materials on operating systems, with good response times even for complex queries. The system can handle much larger document collections while maintaining reasonable performance.

## License

MIT License - see [LICENSE](LICENSE) file for details.