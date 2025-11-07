# All flask start with an application instance

from flask import Flask
app = Flask(__name__) # Flask(capital F) is the class and the app is the application instance

if __name__ == '__main__':
    app.run(debug=True)