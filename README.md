
# JobsonTwo

JobsonTwo is a web-based job processing system that provides a flexible framework for executing various types of computational tasks through a clean and intuitive interface.

## Features

- Web-based interface for job management
- Support for multiple job types:
  - Text Analyzer (word count, language detection, sentiment analysis)
  - Image Processor (resize, format conversion)
  - Calculator
  - Echo Test
- File upload and download capabilities
- Job status tracking
- Clean, responsive user interface

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -e .
   ```

## Usage

1. Start the server:
   ```bash
   python run.py
   ```
2. Open your browser and navigate to `http://localhost:3001`
3. Create and manage jobs through the web interface

## Development

For development, you can run the server in debug mode:
```bash
python run.py --debug
```

## Production Deployment

For production deployment:
1. Set up a production-grade WSGI server (e.g., Gunicorn)
2. Configure a reverse proxy (e.g., Nginx)
3. Set appropriate environment variables
4. Ensure proper file permissions for uploads and jobs directories

## Job Types

### Text Analyzer
- Input: Text file
- Output: Analysis report including:
  - Word and character counts
  - Language detection
  - Readability scores
  - Sentiment analysis
  - Word frequency analysis

### Image Processor
- Input: Image file
- Features:
  - Resize
  - Format conversion
  - Filter application

### Calculator
- Input: Mathematical expression
- Output: Calculation result

### Echo Test
- Input: Any text
- Output: Echoed input (for testing)

## Project Structure

- `web/`: Flask web application
- `specs/`: Job specifications
- `jobs/`: Job execution directory
- `uploads/`: File upload storage
- `storage/`: Job storage
- `execution/`: Job execution utilities
- `tests/`: Test files

## Dependencies

- Flask
- PyYAML
- TextBlob
- langdetect
- NLTK
- Pillow

## License

MIT License 
