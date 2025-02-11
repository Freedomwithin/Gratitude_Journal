from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import webbrowser
from threading import Timer

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///journal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    journal_entries = db.relationship('JournalEntry', backref='author', lazy=True)

# Journal Entry model
class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    mood = db.Column(db.String(100), nullable=True)
    date = db.Column(db.String(100), default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home route
@app.route('/')
@login_required
def index():
    entries = JournalEntry.query.filter_by(user_id=current_user.id).order_by(JournalEntry.date.desc()).all()
    return render_template('index.html', entries=entries)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))

        return 'Invalid username or password. Please try again.'

    return render_template('login.html')

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        user = User.query.filter_by(username=username).first()
        if user:
            return 'Username already exists! Please choose another.'

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/add', methods=['POST'])
@login_required
def add_entry():
    content = request.form['content']
    mood = request.form.get('mood', None)

    new_entry = JournalEntry(content=content, mood=mood, user_id=current_user.id)
    db.session.add(new_entry)
    db.session.commit()

    return redirect(url_for('index'))
@app.route('/edit/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def edit_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    if request.method == 'POST':
        if entry.user_id != current_user.id:
            abort(403)  # Prevent unauthorized edits
        entry.content = request.form['content']
        entry.mood = request.form['mood']
        db.session.commit()
        flash('Entry updated successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('edit.html', entry=entry)

@app.route('/delete/<int:entry_id>', methods=['POST'])
@login_required
def delete_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        abort(403)  # Prevent unauthorized deletion
    db.session.delete(entry)
    db.session.commit()
    flash('Entry deleted successfully!', 'success')
    return redirect(url_for('index'))

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Function to open the app in a browser
def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

# Run the app
if __name__ == '__main__':
    Timer(1, open_browser).start()  # Open browser with a slight delay
    app.run(debug=True)
