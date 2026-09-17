# Company Enrichment & ICP Qualification CLI

Python-based GTM engineering workflow that enriches company domains, normalizes third-party API data, scores ICP fit, and processes prospect lists for sales qualification.

Business Problem

Sales and GTM teams often receive account lists that require enrichment, validation, deduplication, qualification, and prioritization before outreach.

This project automates that workflow while handling invalid inputs, API failures, and partial batch failures.

# Features

**V1 — Single Account Enrichment**

* Company enrichment through an external API
* JSON response parsing
* Pydantic data normalization
* Deterministic ICP scoring
* JSON and CSV persistence
* API and network error handling
* Retry/backoff for temporary failures
* Unit and mocked API tests
* Malformed-response validation

**V2 — Batch Account Qualification**

Status: In Development

* CSV prospect-list ingestion
* Domain validation
* Duplicate detection
* Previously processed account detection
* Prospect source preservation
* Per-account failure isolation
* ICP qualification
* ICP ranking
* Batch result persistence
* Batch processing summary
* Batch-specific automated tests

# Data Flow

Single Account

Domain
  ↓
API Client
  ↓
Raw JSON
  ↓
Pydantic Model
  ↓
ICP Scoring
  ↓
JSON / CSV Output

Batch Processing

Prospect CSV
     ↓
Validation
     ↓
Deduplication
     ↓
Company Enrichment
     ↓
Pydantic Normalization
     ↓
ICP Scoring
     ↓
Qualification + Ranking
     ↓
Batch Results + Summary

The batch workflow is designed so that failure of an individual account does not terminate processing of the remaining prospect list.

# Tech Stack

* Python
* Requests
* Pydantic
* python-dotenv
* pytest
* AbstractAPI Company Enrichment API
* Pandas (batch-processing extension)

# Project Structure

CompanyEnrichmentCLI-Codespace/
│
├── clients/
│   └── abstract_api.py
│
├── models/
│   ├── company.py
│   └── icp.py
│
├── services/
│   ├── company_enrichment.py
│   ├── persistence.py
│   └── scoring_icp.py
│
├── tests/
├── output/
├── config.py
├── main.py
├── requirements.txt
└── README.md

Responsibilities

* clients/ — External API communication and API-specific error handling
* models/ — Application-owned Pydantic data models
* services/ — Enrichment, ICP scoring, and persistence logic
* tests/ — Automated tests
* main.py — CLI entry point and orchestration

# Setup

Clone the repository:

git clone <repository-url>
cd CompanyEnrichmentCLI-Codespace

Create and activate a virtual environment:

python -m venv .venv
source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Create a .env file:

ABSTRACT_API_KEY=your_api_key

# Usage

**Single Account**

python main.py example.com

The application:

1. Accepts a company domain
2. Calls the enrichment API
3. Normalizes the response
4. Calculates ICP fit
5. Prints the structured result
6. Saves JSON and CSV output

**Batch Processing**

Planned / In Development

python main.py --csv prospects.csv

Example input:

domain,source
openai.com,outbound
stripe.com,event
example.com,linkedin

# Failure Handling

Account-level failures are recorded without terminating the entire batch.

Examples include:

* Invalid domains
* Duplicate accounts
* Previously processed accounts
* API failures
* Malformed API responses
* Pydantic validation failures

Batch-level failures, such as an unreadable input CSV, terminate the batch with an appropriate error.

# Testing

Run the test suite:

python -m pytest

Current tests cover:

* ICP scoring
* Persistence
* API behavior
* Mocked API responses
* Retry behavior
* API error handling
* JSON decoding failures
* Malformed responses
* Pydantic validation

Planned batch tests include:

* Normal batch processing
* Duplicate detection
* Source preservation
* Qualified and unqualified outcomes
* Invalid domains
* API failures
* Partial-failure continuation
* Batch result persistence
* ICP ranking
* Batch summary accuracy

# Current Status

V1 — Single Account Enrichment

Complete

* [x]	CLI domain input
* [x]	External API integration
* [x]	JSON parsing
* [x]	Pydantic normalization
* [x]	ICP scoring
* [x]	JSON / CSV persistence
* [x]	Error handling
* [x]	Retry / backoff
* [x]	Unit tests
* [x]	Mock API tests

V2 — Batch Account Qualification

In Development

* [ ]	CSV ingestion
* [ ]	Input validation
* [ ]	Deduplication
* [ ]	Source preservation
* [ ]	Account-level failure isolation
* [ ]	ICP qualification
* [ ]	ICP ranking
* [ ]	Batch persistence
* [ ]	Batch summary
* [ ]	Batch-specific tests

# Portfolio Context

This project is part of an AI GTM Engineering development path focused on translating GTM business requirements into reliable software systems.

The project demonstrates the progression from a basic API integration into a more realistic GTM workflow with validation, error handling, testing, batch processing, and reusable application architecture.