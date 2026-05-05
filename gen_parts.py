#!/usr/bin/env python3
"""Generate _journal_parts files with all journal content."""
import os

PARTS_DIR = "B:/python/advanced-nlp/_journal_parts"
os.makedirs(PARTS_DIR, exist_ok=True)

def w(name, text):
    path = os.path.join(PARTS_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Wrote {name}")


def header():
    w("header.txt", """# Hybrid Search and Topic Modeling: A Comprehensive Technical Journal

**Author:** Abdul Saboor Hamedi, NIM: 241012050123, Class: Regular B

**Course:** Advanced Natural Language Processing

**Date:** April 2026

## Abstract

This journal documents the design, implementation, and evaluation of a production-grade hybrid search engine that combines semantic vector search using pgvector cosine similarity with lexical BM25 keyword search using PostgreSQL full-text search capabilities. The system is augmented by unsupervised LDA topic modeling via Gensim, providing an additional discovery layer over the document corpus. Sentence Transformers are employed for multilingual embedding generation, supporting over 50 languages through the paraphrase-multilingual-MiniLM-L12-v2 model. The application exposes dual interfaces: a feature-rich Command-Line Interface built with the Rich library and a Flask web application styled with Tailwind CSS. A complete PDF ingestion pipeline handles document parsing, text cleaning, intelligent chunking, language detection, embedding generation, and database storage. The journal covers theoretical foundations, system architecture, database schema design, embedding pipelines, hybrid scoring fusion techniques, LDA topic modeling, PDF ingestion workflows, user interface design, utility modules, and a thorough evaluation of search quality, latency, and throughput. Practical challenges such as score normalization, thread safety, multilingual text handling, and batch processing are discussed in detail.

## Table of Contents

- 1.  Introduction and Motivation
- 2.  Theoretical Foundations
- 3.  System Architecture
- 4.  Database Design and Schema
- 5.  The Embedding Pipeline
- 6.  The Hybrid Search Engine
- 7.  LDA Topic Modeling
- 8.  PDF Ingestion Pipeline
- 9.  User Interfaces
- 10. Utility Modules
- 11. Evaluation and Analysis
- 12. Future Work
- 13. Conclusion
- 14. References

""")

def s01():
    w("s01.txt", """## 1. Introduction and Motivation

### 1.1 The Information Retrieval Challenge

The exponential growth of digital text over the past two decades has created an acute need for systems that can efficiently locate relevant information within vast document collections. From academic researchers sifting through thousands of papers to legal professionals navigating case law databases, the ability to surface the right document at the right time is critical across nearly every domain of knowledge work. Yet the gap between how humans express information needs and how machines index documents remains one of the most persistent challenges in natural language processing and information retrieval.
""")
