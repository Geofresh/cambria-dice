from flask import Flask, render_template, jsonify, request, url_for, send_file
from random_generator import generate_random_numbers, verify_proof
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import logging
import json
from datetime import datetime
import io
import csv
import hashlib

app = Flask(__name__, static_url_path='/static')
logging.basicConfig(level=logging.DEBUG)

# Store roll history in memory (consider using a database for production)
roll_history = []

# Add rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri="memory://",
    default_limits=["200 per day", "50 per hour"]
)

# Add security headers but allow necessary content
Talisman(app, 
    content_security_policy={
        'default-src': ["'self'"],
        'style-src': ["'self'", "'unsafe-inline'", "fonts.googleapis.com"],
        'font-src': ["'self'", "fonts.gstatic.com"],
        'img-src': ["'self'", "data:"],
        'script-src': ["'self'", "'unsafe-inline'"],
        'connect-src': ["'self'"]
    },
    force_https=False  # Disable HTTPS requirement for local development
)

@app.route('/')
def index():
    return render_template('index.html', roll_history=roll_history)

@app.route('/generate', methods=['POST'])
@limiter.limit("10 per minute")
def generate():
    try:
        app.logger.debug(f"Received request: {request.get_data(as_text=True)}")
        data = request.get_json()
        app.logger.debug(f"Parsed JSON data: {data}")
        
        if not data:
            raise ValueError("No JSON data received")
            
        max_range = int(data.get('maxRange', 1))
        count = int(data.get('count', 1))
        
        app.logger.debug(f"Generating numbers with max_range={max_range}, count={count}")
        
        numbers, proofs = generate_random_numbers(max_range, count)
        app.logger.debug(f"Generated numbers: {numbers}")
        
        # Create roll history entry
        timestamp = datetime.fromtimestamp(proofs[0]['timestamp'])
        roll_id = len(roll_history) + 1
        history_entry = {
            'id': roll_id,
            'timestamp': timestamp,
            'numbers': numbers,
            'max_range': max_range,
            'count': count,
            'proofs': proofs
        }
        roll_history.append(history_entry)
        
        response_data = {
            'numbers': numbers,
            'success': True,
            'count': count,
            'maxRange': max_range,
            'rollId': roll_id,
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        app.logger.debug(f"Sending response: {response_data}")
        return jsonify(response_data)
    except Exception as e:
        app.logger.error(f"Error generating numbers: {str(e)}", exc_info=True)
        return jsonify({
            'error': str(e),
            'success': False
        }), 400

@app.route('/download/<int:roll_id>')
def download_proof(roll_id):
    try:
        roll = next((r for r in roll_history if r['id'] == roll_id), None)
        if not roll:
            return "Roll not found", 404

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Roll Information'])
        writer.writerow(['Timestamp', roll['timestamp'].strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow(['Maximum Range', roll['max_range']])
        writer.writerow(['Number of Rolls', roll['count']])
        writer.writerow([])
        writer.writerow(['Number', 'Timestamp', 'Nonce', 'Hash'])
        
        # Write each number and its proof
        for number, proof in zip(roll['numbers'], roll['proofs']):
            writer.writerow([
                number,
                proof['timestamp'],
                proof['nonce'],
                proof['hash']
            ])

        # Prepare the response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'roll_{roll_id}_proof.csv'
        )
    except Exception as e:
        app.logger.error(f"Error generating CSV: {str(e)}", exc_info=True)
        return str(e), 400

@app.route('/verify/<int:roll_id>')
def verify_roll(roll_id):
    try:
        roll = next((r for r in roll_history if r['id'] == roll_id), None)
        if not roll:
            return jsonify({
                'error': 'Roll not found',
                'success': False
            }), 404

        verifications = []
        for number, proof in zip(roll['numbers'], roll['proofs']):
            # Verify each number
            is_valid = verify_proof(proof)
            verification = {
                'number': number,
                'timestamp': proof['timestamp'],
                'nonce': proof['nonce'],
                'expected_hash': proof['hash'],
                'computed_hash': hashlib.sha256(f"{number}:{proof['timestamp']}:{proof['nonce']}".encode()).hexdigest(),
                'valid': is_valid
            }
            verifications.append(verification)

        return jsonify({
            'success': True,
            'verifications': verifications,
            'all_valid': all(v['valid'] for v in verifications)
        })
    except Exception as e:
        app.logger.error(f"Error verifying roll: {str(e)}", exc_info=True)
        return jsonify({
            'error': str(e),
            'success': False
        }), 400

if __name__ == '__main__':
    # debugging
    app.run(debug=True)
else:
    # change before deployment
    app.run(host='0.0.0.0', port=8080) 