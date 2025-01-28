# Cambria Random Number Generator

A Cambria-themed web application that generates cryptographically secure random numbers using Python's `secrets` module. Features a responsive, pixel-art style interface inspired by the Cambria aesthetic.

## Features

- Cryptographically secure random number generation
- Cambria-themed UI with pixel art styling
- Configurable number range and roll count
- Responsive design that works on all devices
- Rate limiting

## Requirements

- Python 3.x
- Flask 3.0.0
- Additional dependencies listed in `requirements.txt`

## Quick Start

1. Clone the repository
2. Set up the virtual environment:
```bash
.\setup.bat
```

3. Activate the virtual environment:
```bash
venv\Scripts\activate.bat
```

4. Start the application:
```bash
python app.py
```

5. Open your browser and navigate to: `http://127.0.0.1:5000`

## Usage

1. Enter your desired maximum number (1 or greater)
2. Choose how many numbers you want to generate (1-100)
3. Click "Roll the Dice"
4. View your randomly generated numbers

## Security Features

- Cryptographically secure random generation using `secrets` module
- Rate limiting (10 rolls per minute, 50 per hour, 200 per day)
- Input validation and sanitization
- Error handling and logging

## Development

The application is built with:
- Flask for the backend
- JavaScript for frontend interactions
- CSS for Cambria styling
- Google Fonts (MedievalSharp)

## API Endpoints

### Generate Numbers
- **URL**: `/generate`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "maxRange": 365,  // Maximum number (inclusive)
    "count": 24      // How many numbers to generate
  }
  ```
- **Response**:
  ```json
  {
    "numbers": [1, 2, 3],  // Generated numbers
    "success": true,
    "count": 3,
    "maxRange": 365
  }
  ```

## Deployment

1. **Development**:
```bash
python app.py
```

2. **Production** (using Gunicorn):
```bash
gunicorn wsgi:app
```

## Rate Limits

- 10 rolls per minute
- 50 rolls per hour
- 200 rolls per day

## Project Structure

```
.
├── app.py              # Main Flask application
├── random_generator.py # Random number generation logic
├── requirements.txt    # Project dependencies
├── setup.bat          # Setup script for Windows
├── wsgi.py            # WSGI entry point
├── static/            # Static files
│   └── images/        # Images including logo
└── templates/         # HTML templates
    └── index.html     # Main page template
```
