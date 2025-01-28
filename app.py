from flask import Flask, render_template, jsonify, request, url_for, send_file
from random_generator import generate_random_numbers, verify_proof
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_login import LoginManager, login_required, current_user
from models import db, User, Roll
from auth import auth, init_admin
import logging
import json
from datetime import datetime
import io
import csv
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///cambria.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(auth)

logging.basicConfig(level=logging.DEBUG)

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
    # Get rolls in descending order by timestamp
    roll_history = Roll.query.order_by(Roll.timestamp.desc()).limit(50).all()
    return render_template('index.html', 
                         roll_history=roll_history, 
                         is_admin=current_user.is_authenticated and current_user.is_admin)

@app.route('/generate', methods=['POST'])
@login_required
def generate():
    if not current_user.is_admin:
        return jsonify({
            'error': 'Unauthorized. Only administrators can generate rolls.',
            'success': False
        }), 403

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
        
        # Create new roll in database
        roll = Roll(
            max_range=max_range,
            count=count,
            user_id=current_user.id,
            timestamp=datetime.fromtimestamp(proofs[0]['timestamp'])
        )
        roll.set_numbers(numbers)
        roll.set_proofs(proofs)
        
        db.session.add(roll)
        db.session.commit()
        
        response_data = {
            'numbers': numbers,
            'success': True,
            'count': count,
            'maxRange': max_range,
            'rollId': roll.id,
            'timestamp': roll.timestamp.strftime('%Y-%m-%d %H:%M:%S')
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
        roll = Roll.query.get_or_404(roll_id)

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Roll Information'])
        writer.writerow(['Timestamp', roll.timestamp.strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow(['Maximum Range', roll.max_range])
        writer.writerow(['Number of Rolls', roll.count])
        writer.writerow([])
        writer.writerow(['Number', 'Timestamp', 'Nonce', 'Hash'])
        
        # Write each number and its proof
        numbers = roll.get_numbers()
        proofs = roll.get_proofs()
        for number, proof in zip(numbers, proofs):
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
        roll = Roll.query.get_or_404(roll_id)
        numbers = roll.get_numbers()
        proofs = roll.get_proofs()

        verifications = []
        for number, proof in zip(numbers, proofs):
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

def create_tables():
    with app.app_context():
        app.logger.info("Creating database tables...")
        db.create_all()
        app.logger.info("Tables created successfully")
        
        # Initialize admin user
        app.logger.info("Initializing admin user...")
        try:
            init_admin()
            app.logger.info("Admin user initialized successfully")
        except Exception as e:
            app.logger.error(f"Error initializing admin user: {str(e)}")
            raise

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    create_tables()
    app.run(debug=True)
else:
    # Create tables when running with gunicorn
    logging.basicConfig(level=logging.INFO)
    create_tables()
    app.run(host='0.0.0.0', port=8080) 