from flask import Flask, Blueprint

import api_v1

app = Flask(__name__)

app.register_blueprint(api_v1.api)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
