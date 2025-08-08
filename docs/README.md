# README.md
# Application Auto Discoverer

## Overview
The Application Auto Discoverer is a FastAPI-based system that analyzes logs from network monitoring tools (ExtraHop, Splunk, DynaTrace) to automatically discover and document network topology and application dependencies.

## Features
- **Log Analysis**: Process CSV/XLSX files from multiple data sources
- **Topology Discovery**: Automatically map network connections and dependencies
- **Documentation Generation**: Create comprehensive documentation in multiple formats
- **Diagram Generation**: Generate visual network and application diagrams
- **Multi-format Export**: Export results to Excel, Visio, Word, PDF, and Lucid formats

## Installation

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Setup
1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate virtual environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy environment template: `cp .env.example .env`
6. Configure environment variables in `.env`

### Running the Application
```bash
python main.py
```

The application will be available at `http://localhost:8000`

## Directory Structure
```
application_auto_discoverer/
├── data_staging/           # Input files staging area
│   ├── processed/         # Successfully processed files
│   └── failed/           # Failed processing files
├── results/              # Output artifacts
│   ├── excel/           # Excel exports
│   ├── visio/           # Visio diagrams
│   ├── word/            # Word documents
│   ├── pdf/             # PDF reports
│   └── lucid/           # Lucid charts
├── routers/             # API route handlers
├── services/            # Business logic
├── models/              # Data models
├── utils/               # Utility functions
└── config/              # Configuration files
```

## Usage
1. Upload log files via the API or web interface
2. Files are automatically processed from the `data_staging` directory
3. Successfully processed files move to `data_staging/processed`
4. Failed files move to `data_staging/failed` with error logs
5. Generated artifacts are saved in `results/` subdirectories with app name tags

## API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Configuration
See `.env.example` for all available configuration options.

## Contributing
[To be documented]

## License
[To be documented]
