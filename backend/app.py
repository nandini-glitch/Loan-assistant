from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
from agents.master_agent import MasterAgent

app = Flask(__name__)
CORS(app)

# Store active sessions (in production, use Redis or similar)
active_sessions = {}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'BFSI Loan Chatbot API is running'})

@app.route('/api/chat/start', methods=['POST'])
def start_chat():
    """Initialize a new chat session"""
    session_id = request.json.get('session_id', 'default_session')
    
    # Create new master agent for this session
    master = MasterAgent()
    active_sessions[session_id] = master
    
    # Get initial greeting
    response = master.process_message('start', None)
    
    return jsonify({
        'session_id': session_id,
        'response': response['response'],
        'stage': response['stage'],
        'action': response.get('action')
    })

@app.route('/api/chat/message', methods=['POST'])
def send_message():
    """Process user message"""
    data = request.json
    session_id = data.get('session_id', 'default_session')
    user_message = data.get('message', '')
    context = data.get('context', {})
    
    # Get or create master agent for session
    if session_id not in active_sessions:
        active_sessions[session_id] = MasterAgent()
    
    master = active_sessions[session_id]
    
    # Process message
    response = master.process_message(user_message, context)
    
    # Extract sanction result if available
    sanction_data = None
    pdf_filename = None
    
    if response.get('sanction_result'):
        sanction_data = response['sanction_result']
        pdf_filename = sanction_data.get('pdf_filename')
        print(f"[API] Sanction result found, PDF filename: {pdf_filename}")
    
    return jsonify({
        'session_id': session_id,
        'response': response['response'],
        'stage': response['stage'],
        'action': response.get('action'),
        'data': {
            'customer_data': response.get('customer_data'),
            'loan_terms': response.get('loan_terms'),
            'suggestions': response.get('suggestions'),
            'credit_info': response.get('credit_info'),
            'sanction_result': sanction_data,
            'pdf_available': response.get('pdf_available', False),
            'pdf_path': pdf_filename or response.get('pdf_path')
        }
    })

@app.route('/api/chat/upload', methods=['POST'])
def upload_document():
    """Handle document upload (salary slip)"""
    session_id = request.form.get('session_id', 'default_session')
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    # Save file
    upload_folder = 'uploads'
    os.makedirs(upload_folder, exist_ok=True)
    
    filename = f"{session_id}_{file.filename}"
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    print(f"[API] File uploaded: {filepath}")
    
    # Get master agent and process
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    master = active_sessions[session_id]
    
    # Process with context
    context = {
        'file_uploaded': True,
        'file_name': filename,
        'file_path': filepath
    }
    
    response = master.process_message('', context)
    
    return jsonify({
        'session_id': session_id,
        'file_uploaded': True,
        'filename': filename,
        'response': response['response'],
        'stage': response['stage'],
        'action': response.get('action'),
        'next_step': response.get('next_step')
    })

@app.route('/api/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """Download generated sanction letter"""
    try:
        print(f"\n[API] Download request received for: {filename}")
        
        # Construct file path
        if filename.startswith('generated_letters'):
            filepath = filename
        else:
            filepath = os.path.join('generated_letters', filename)
        
        # Get absolute path
        abs_filepath = os.path.abspath(filepath)
        print(f"[API] Looking for file at: {abs_filepath}")
        
        # Check if file exists
        if not os.path.exists(abs_filepath):
            print(f"[API] ❌ File not found!")
            
            # List available files for debugging
            if os.path.exists('generated_letters'):
                available = os.listdir('generated_letters')
                print(f"[API] Available files: {available}")
            
            return jsonify({
                'error': 'File not found',
                'requested': filename,
                'path': abs_filepath
            }), 404
        
        print(f"[API] ✅ File found! Sending...")
        
        return send_file(
            abs_filepath,
            as_attachment=True,
            download_name=os.path.basename(filename),
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"[API] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/reset', methods=['POST'])
def reset_chat():
    """Reset conversation for a session"""
    session_id = request.json.get('session_id', 'default_session')
    
    if session_id in active_sessions:
        active_sessions[session_id].reset_conversation()
    
    return jsonify({
        'session_id': session_id,
        'message': 'Conversation reset successfully'
    })

@app.route('/api/customers', methods=['GET'])
def get_test_customers():
    """Get list of test customer phone numbers (for demo purposes)"""
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

@app.route('/api/debug/pdf-status', methods=['GET'])
def pdf_status():
    """Debug: Check PDF generation status"""
    import os
    
    pdf_dir = 'generated_letters'
    
    if not os.path.exists(pdf_dir):
        return jsonify({
            'exists': False,
            'path': os.path.abspath(pdf_dir),
            'message': 'Directory does not exist'
        })
    
    files = os.listdir(pdf_dir)
    
    file_details = []
    for f in files:
        fpath = os.path.join(pdf_dir, f)
        file_details.append({
            'name': f,
            'size': os.path.getsize(fpath),
            'path': os.path.abspath(fpath)
        })
    
    return jsonify({
        'exists': True,
        'directory': os.path.abspath(pdf_dir),
        'count': len(files),
        'files': file_details
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 BFSI Loan Chatbot Backend Starting...")
    print("="*60)
    print("📡 Server running on: http://localhost:5002")
    print("📋 API endpoints available:")
    print("   - POST /api/chat/start")
    print("   - POST /api/chat/message")
    print("   - POST /api/chat/upload")
    print("   - GET  /api/download/<filename>")
    print("   - GET  /api/customers")
    print("   - GET  /api/debug/pdf-status")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5002)