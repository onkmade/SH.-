# All flask start with an application instance

from flask import Flask
app = Flask(__name__) # Flask(capital F) is the class and the app is the application instance

@app.route('/main')
def main():
    return '<h1>THIS IS MAIN PAGE</h1>'