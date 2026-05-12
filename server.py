import json
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # allow cross-origin requests (useful during development)

DATA_FILE = 'data.json'

# ---------------------------
#  Helper: load/save data
# ---------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        # Initial structure
        return {
            "master_hash": None,
            "master_salt": None,
            "vaults": {
                "student": {"data": None},
                "faculty": {"data": None},
                "staff": {"data": None}
            },
            "auth_codes": {
                "faculty": "faculty123",   # default demo codes – change them!
                "staff": "staff123"
            }
        }
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ---------------------------
#  API endpoints
# ---------------------------
@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

@app.route('/api/master', methods=['GET'])
def get_master():
    data = load_data()
    if data['master_hash'] is None:
        return jsonify({"exists": False})
    return jsonify({
        "exists": True,
        "hash": data['master_hash'],
        "salt": data['master_salt']
    })

@app.route('/api/master', methods=['POST'])
def set_master():
    req = request.get_json()
    hash_val = req.get('hash')
    salt = req.get('salt')
    if not hash_val or not salt:
        return jsonify({"error": "Missing hash or salt"}), 400

    data = load_data()
    # Only allow creation if master doesn't exist yet
    if data['master_hash'] is not None:
        return jsonify({"error": "Master already exists"}), 409

    data['master_hash'] = hash_val
    data['master_salt'] = salt
    save_data(data)
    return jsonify({"success": True})

@app.route('/api/vault/<role>', methods=['GET'])
def get_vault(role):
    if role not in ('student', 'faculty', 'staff'):
        return jsonify({"error": "Invalid role"}), 400
    data = load_data()
    vault_data = data['vaults'].get(role, {}).get('data')
    return jsonify({"data": vault_data})

@app.route('/api/vault/<role>', methods=['PUT'])
def put_vault(role):
    if role not in ('student', 'faculty', 'staff'):
        return jsonify({"error": "Invalid role"}), 400
    req = request.get_json()
    encrypted_data = req.get('data')
    if encrypted_data is None:
        return jsonify({"error": "Missing data"}), 400

    data = load_data()
    if role not in data['vaults']:
        data['vaults'][role] = {}
    data['vaults'][role]['data'] = encrypted_data
    save_data(data)
    return jsonify({"success": True})

@app.route('/api/auth/<role>', methods=['GET'])
def verify_auth_code(role):
    if role not in ('faculty', 'staff'):
        return jsonify({"valid": False}), 400

    code = request.args.get('code', '')
    data = load_data()
    valid_codes = data.get('auth_codes', {})
    expected = valid_codes.get(role)
    return jsonify({"valid": code == expected})

# ---------------------------
#  Run the server
# ---------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)