import hashlib
import bcrypt
from flask import Flask, render_template, request, session, redirect, url_for, render_template_string
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, current_user, login_required, UserMixin
import dotenv
import os

dotenv.load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    imp = db.Column(db.String(300), nullable=False)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.id_attribute = 'username'

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(username):
    user = User.query.filter_by(username=username).first()
    if user and user.is_active:
        return user
    else:
        return None

def hash_password(password):
    """Hash the password using sha256."""
    return hashlib.sha256(password.encode()).hexdigest()

#def encrypt_data(data, desired_key_bytes=16, rounds=12):
#    """Encrypt data using bcrypt."""
#    salt = bcrypt.gensalt()
#    key = bcrypt.kdf(salt, data.encode(), desired_key_bytes, rounds)
#    return key

#def decrypt_data(encrypted_data, original_data):
#    """Decrypt data using bcrypt."""
#    salt = bcrypt.gensalt()
#    key = bcrypt.kdf(salt, encrypted_data, desired_key_bytes=16, rounds=12)
#    return key.decode() if bcrypt.kdf(salt, key, bcrypt, rounds=12).decode() == original_data else "Invalid key"

@app.route('/', methods=['GET'])
def home():
    if 'user_id' in session:
        user_id = session.get('user_id')
        user = db.session.query(User).filter_by(id=user_id).first()
        if user and user.is_active:
            return render_template('landing.html')
        else:
            return render_template('landing.html', user=user)
    else:
        return render_template('landing.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    return render_template('register.html')
@app.route('/process/register', methods=['POST'])
def processinfo():
    usernm = request.form['username']
    passwrd = request.form['password']
    impinfo = request.form['impinfo']
    hashed_pswd = hash_password(passwrd)
    user = db.session.query(User)
    new_user = User(username=usernm, password=hashed_pswd, imp=impinfo)
    new_user.is_active = True
    db.session.add(new_user)
    db.session.commit()
    session['user_id'] = new_user.id
    session['username'] = usernm
    session['imp'] = impinfo
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session and 'username' in session:
        users = db.session.query(User)
        imp = session.get('imp')
        return render_template('dashboard.html', user=users, username=session['username'], imp=imp)
    else:
        return redirect(url_for('home'))

@app.route('/login')
def loginpg():
    return render_template('login.html')

@app.route('/process/login', methods=['POST', 'GET'])
def login():
    usernm = request.form['username']
    passwrd = request.form['password']
    userst = None
    user = load_user(usernm)
    if user and hash_password(passwrd) == user.password and user.is_active:
        session['user_id'] = user.id
        session['username'] = user.username
        session['imp'] = user.imp
        userst = True
        return redirect(url_for('dashboard', user=user))
    else:
        userst = False
        return render_template('login.html', error_message="Invalid username or password.", userst=userst)


@app.route('/logout')
def logout():
    return render_template('logout.html')

@app.route('/logout/now')
def logoutnow():
    session.pop('user_id', None)
    session.pop('username', None)
    session.clear()
    return redirect(url_for('home'))

@app.route('/add-imp', methods=['POST'])
def addimp():
    impinfo = request.form['impin']
    return redirect(url_for('dashboard'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(host='localhost', port=3000)

