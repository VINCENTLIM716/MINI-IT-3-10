from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

app = Flask(__name__)
app.secret_key = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)

class HabitCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, default=date.today)

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed = generate_password_hash(password)

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists.")
            return redirect(url_for('register'))

        new_user = User(username=username, password=hashed)
        db.session.add(new_user)
        db.session.commit()
        
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/habits')
def habits():
    if 'user_id' not in session:
        return redirect(url_for('login')) 

    user_id = session['user_id']
    username = session.get('username')

    user_habits = Habit.query.filter_by(user_id=user_id).all()

    habits_with_data = []
    for habit in user_habits:
        completions = HabitCompletion.query.filter_by(habit_id=habit.id, user_id=user_id).count()
        habits_with_data.append({
            'id': habit.id,
            'name': habit.name,
            'streak': completions, 
            'frequency': "Daily"    
        })

    return render_template('habit.html', habits=habits_with_data, username=username)


@app.route('/stats')
def stats():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    total_habits = Habit.query.filter_by(user_id=user_id).count()
    completed = HabitCompletion.query.filter_by(user_id=user_id).count()
    completion_rate = round((completed / total_habits) * 100, 1) if total_habits > 0 else 0

    stats = {
        'total_habits': total_habits,
        'completed_habits': completed,
        'completion_rate': completion_rate
    }

    return render_template('stats.html', stats=stats)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)