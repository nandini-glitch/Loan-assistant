from flask import Flask, request, jsonify, send_file, make_response
import os
import traceback
from functools import wraps
from agents.master_agent import MasterAgent

app = Flask(__name__)

# Store active sessions
active_sessions = {}

# ✅ Manual CORS decorator (no flask-cors needed)
def add_cors_headers(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Handle OPTIONS preflight
        if request.method == 'OPTIONS':
            response = make_response('', 204)
        else:
            response = make_response(f(*args, **kwargs))
        
        # Add CORS headers to every response
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Max-Age'] = '3600'
        
        return response
    return decorated_function

@app.route('/api/health', methods=['GET', 'OPTIONS'])
@add_cors_headers
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'BFSI Loan Chatbot API is running'})

@app.route('/api/chat/start', methods=['POST', 'OPTIONS'])
@add_cors_headers
def start_chat():
    """Initialize a new chat session"""
    try:
        session_id = request.json.get('session_id', 'default_session')
        
        master = MasterAgent()
        active_sessions[session_id] = master
        
        response = master.process_message('start', None)
        
        return jsonify({
            'session_id': session_id,
            'response': response['response'],
            'stage': response['stage'],
            'action': response.get('action')
        })
    except Exception as e:
        print(f"[API /chat/start] ERROR: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/message', methods=['POST', 'OPTIONS'])
@add_cors_headers
def send_message():
    """Process user message"""
    try:
        data = request.json
        session_id = data.get('session_id', 'default_session')
        user_message = data.get('message', '')
        context = data.get('context', {})
        
        print(f"\n[API /chat/message] Session: {session_id}")
        print(f"[API /chat/message] Message: {user_message}")
        
        if session_id not in active_sessions:
            active_sessions[session_id] = MasterAgent()
        
        master = active_sessions[session_id]
        response = master.process_message(user_message, context)
        
        api_response = {
            'session_id': session_id,
            'response': response['response'],
            'stage': response['stage'],
            'action': response.get('action'),
            'pdf_available': response.get('pdf_available', False),
            'pdf_path': response.get('pdf_path'),
            'sanction_result': response.get('sanction_result'),
            'data': {
                'customer_data': response.get('customer_data'),
                'loan_terms': response.get('loan_terms'),
                'suggestions': response.get('suggestions'),
                'credit_info': response.get('credit_info'),
                'pdf_available': response.get('pdf_available', False),
                'pdf_path': response.get('pdf_path'),
                'sanction_result': response.get('sanction_result'),
                'loan_amount': response.get('loan_amount'),
                'rejection_reason': response.get('rejection_reason'),
            }
        }
        
        print(f"[API /chat/message] Response action: {api_response['action']}")
        print(f"[API /chat/message] Response stage: {api_response['stage']}")
        
        return jsonify(api_response)
        
    except Exception as e:
        print(f"[API /chat/message] ERROR: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/upload', methods=['POST', 'OPTIONS'])
@add_cors_headers
def upload_document():
    """Handle document upload (salary slip)"""
    try:
        print("\n" + "="*60)
        print("[API /chat/upload] ===== UPLOAD REQUEST RECEIVED =====")
        print("="*60)
        
        # Print request info
        print(f"[API /chat/upload] Request method: {request.method}")
        print(f"[API /chat/upload] Content type: {request.content_type}")
        print(f"[API /chat/upload] Form keys: {list(request.form.keys())}")
        print(f"[API /chat/upload] Files keys: {list(request.files.keys())}")
        
        session_id = request.form.get('session_id')
        print(f"[API /chat/upload] Session ID: {session_id}")
        
        if not session_id:
            print("[API /chat/upload] ERROR: No session_id provided")
            return jsonify({'error': 'No session_id provided'}), 400
        
        if 'file' not in request.files:
            print("[API /chat/upload] ERROR: No file in request")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        print(f"[API /chat/upload] File: {file.filename}")
        
        if file.filename == '':
            print("[API /chat/upload] ERROR: Empty filename")
            return jsonify({'error': 'Empty filename'}), 400
        
        # Validate file type
        allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            print(f"[API /chat/upload] ERROR: Invalid file type: {file_ext}")
            return jsonify({'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'}), 400
        
        # Save file
        upload_folder = 'uploads'
        os.makedirs(upload_folder, exist_ok=True)
        
        filename = f"{session_id}_{file.filename}"
        filepath = os.path.join(upload_folder, filename)
        
        print(f"[API /chat/upload] Saving to: {filepath}")
        file.save(filepath)
        
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"[API /chat/upload] ✅ Saved! Size: {file_size} bytes")
        else:
            print(f"[API /chat/upload] ❌ File NOT saved!")
            return jsonify({'error': 'Failed to save file'}), 500
        
        # Get master agent
        if session_id not in active_sessions:
            print(f"[API /chat/upload] ERROR: Session not found")
            return jsonify({'error': 'Session not found. Please start a new chat.'}), 404
        
        master = active_sessions[session_id]
        
        # Process with context
        context = {
            'file_uploaded': True,
            'file_name': filename,
            'file_path': filepath
        }
        
        print(f"[API /chat/upload] Processing...")
        response = master.process_message('', context)
        
        print(f"\n[API /chat/upload] ===== MASTER RESPONSE =====")
        print(f"[API /chat/upload] Action: {response.get('action')}")
        print(f"[API /chat/upload] Stage: {response.get('stage')}")
        print(f"[API /chat/upload] PDF Available: {response.get('pdf_available')}")
        print(f"[API /chat/upload] PDF Path: {response.get('pdf_path')}")
        print(f"[API /chat/upload] ===========================\n")
        
        api_response = {
            'session_id': session_id,
            'file_uploaded': True,
            'filename': filename,
            'response': response['response'],
            'stage': response['stage'],
            'action': response.get('action'),
            'pdf_available': response.get('pdf_available', False),
            'pdf_path': response.get('pdf_path'),
            'sanction_result': response.get('sanction_result'),
            'data': {
                'customer_data': response.get('customer_data'),
                'loan_terms': response.get('loan_terms'),
                'credit_info': response.get('credit_info'),
                'pdf_available': response.get('pdf_available', False),
                'pdf_path': response.get('pdf_path'),
                'sanction_result': response.get('sanction_result'),
            }
        }
        
        print(f"[API /chat/upload] Returning response with action: {api_response['action']}")
        
        return jsonify(api_response)
        
    except Exception as e:
        print(f"\n[API /chat/upload] ❌ ERROR: {e}")
        print(f"[API /chat/upload] Type: {type(e).__name__}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'type': type(e).__name__}), 500

@app.route('/api/download/<path:filename>', methods=['GET', 'OPTIONS'])
@add_cors_headers
def download_file(filename):
    """Download generated sanction letter"""
    try:
        print(f"\n[API /download] Requested: {filename}")
        
        if filename.startswith('generated_letters'):
            filepath = filename
        else:
            filepath = os.path.join('generated_letters', filename)
        
        abs_filepath = os.path.abspath(filepath)
        print(f"[API /download] Looking for: {abs_filepath}")
        
        if not os.path.exists(abs_filepath):
            print(f"[API /download] ❌ File not found!")
            return jsonify({'error': 'File not found'}), 404
        
        print(f"[API /download] ✅ Sending file")
        
        return send_file(
            abs_filepath,
            as_attachment=True,
            download_name=os.path.basename(filename),
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"[API /download] ❌ Error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/reset', methods=['POST', 'OPTIONS'])
@add_cors_headers
def reset_chat():
    """Reset conversation"""
    try:
        session_id = request.json.get('session_id', 'default_session')
        
        if session_id in active_sessions:
            active_sessions[session_id].reset_conversation()
        
        return jsonify({
            'session_id': session_id,
            'message': 'Conversation reset successfully'
        })
    except Exception as e:
        print(f"[API /chat/reset] ERROR: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/customers', methods=['GET', 'OPTIONS'])
@add_cors_headers
def get_test_customers():
    """Get list of test customer phone numbers"""
    try:
        from data.customers import CUSTOMER_DATABASE
        
        test_customers = []
        for phone, data in CUSTOMER_DATABASE.items():
            test_customers.append({
                'phone': phone,
                'name': data['name'],
                'city': data['city'],
                'pre_approved_limit': data['pre_approved_limit']
            })
        
        return jsonify({'customers': test_customers})
    except Exception as e:
        print(f"[API /customers] ERROR: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/pdf-status', methods=['GET', 'OPTIONS'])
@add_cors_headers
def pdf_status():
    """Debug: Check PDF generation status"""
    try:
        pdf_dir = 'generated_letters'
        
        if not os.path.exists(pdf_dir):
            return jsonify({
                'exists': False,
                'message': 'Directory does not exist'
            })
        
        files = os.listdir(pdf_dir)
        
        file_details = []
        for f in files:
            fpath = os.path.join(pdf_dir, f)
            file_details.append({
                'name': f,
                'size': os.path.getsize(fpath)
            })
        
        return jsonify({
            'exists': True,
            'count': len(files),
            'files': file_details
        })
    except Exception as e:
        print(f"[API /debug/pdf-status] ERROR: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    response = jsonify({'error': 'Not found'})
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 404

@app.errorhandler(500)
def internal_error(error):
    print(f"[API] Internal Server Error: {error}")
    traceback.print_exc()
    response = jsonify({'error': 'Internal server error'})
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 BFSI Loan Chatbot Backend Starting...")
    print("="*60)
    
    # Get port from environment variable (Render requirement)
    port = int(os.environ.get('PORT', 5002))
    
    # Get host - use 0.0.0.0 for production
    host = os.environ.get('HOST', '0.0.0.0')
    
    # Check if running in production
    is_production = os.environ.get('RENDER', False)
    
    if is_production:
        print("🌐 Running in PRODUCTION mode on Render")
    else:
        print("🔧 Running in DEVELOPMENT mode")
    
    print(f"📡 Server: http://{host}:{port}")
    print("✅ Manual CORS enabled")
    print("="*60 + "\n")
    
    # Disable debug in production
    app.run(debug=not is_production, port=port, threaded=True, host=host)