from flask import Flask
from flask_cors import CORS
from routes.slr_routes import slr_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(slr_bp, url_prefix='/api')

@app.route('/')
def root():
    return {'info': "SLR Parser"}

@app.route('/api/health', methods=['GET'])
def health():
    return {'status': 'ok'}

# IMPORTANT: keep this, but Railway will NOT use it
if __name__ == '__main__':
    app.run()


