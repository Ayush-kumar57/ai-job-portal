import os
from flask import Flask, render_template
import config
from db import db

# HTML aur CSS frontend/ folder mein hain, isliye Flask ko unka rasta batate hain
FRONTEND_DIR = os.path.join(config.BASE_DIR, 'frontend')

app = Flask(__name__,
            template_folder=os.path.join(FRONTEND_DIR, 'templates'),
            static_folder=os.path.join(FRONTEND_DIR, 'static'))
app.config.from_object(config)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/db-test')
def db_test():
    db['test'].insert_one({'msg': 'hello from flask'})
    count = db['test'].count_documents({})
    return f'MongoDB connected. Test records: {count}'


if __name__ == '__main__':
    app.run(debug=True)
