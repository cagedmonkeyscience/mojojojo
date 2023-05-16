from flask import Flask, jsonify

fapp = Flask(__name__)
@fapp.route('/health', methods=['GET'])
def health_check():
    return jsonify(status='ok')
