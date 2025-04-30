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
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)


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
    user = User.query.get(user_id)

    xp_needed = 100 + (user.level - 1) * 50
    progress_percent = int((user.xp / xp_needed) * 100) if xp_needed > 0 else 0
    progress_class = f"w-[{progress_percent}%]"

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

    return render_template('habit.html',
                           habits=habits_with_data,
                           username=username,
                           user=user,
                           xp_needed=xp_needed,
                           progress_class=progress_class)

@app.route('/stats')
def stats():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    today = date.today()

    total_habits = Habit.query.filter_by(user_id=user_id).count()
    completed_today = HabitCompletion.query.filter_by(user_id=user_id, date=today).count()

    # Prepare chart data
    chart_data = {
        'labels': ['Completed Today', 'Remaining'],
        'data': [completed_today, max(total_habits - completed_today, 0)]
    }

    stats = {
        'total_habits': total_habits,
        'completed_habits': completed_today,
        'completion_rate': round((completed_today / total_habits) * 100, 1) if total_habits else 0
    }

    return render_template('stats.html', stats=stats, chart_data=chart_data)



@app.route('/add_habit', methods=['GET', 'POST'])
def add_habit():
    if 'user_id' not in session:
        return redirect(url_for('login')) 

    if request.method == 'POST':
        habit_name = request.form['habit_name']
        user_id = session['user_id']

        new_habit = Habit(name=habit_name, user_id=user_id)
        db.session.add(new_habit)
        db.session.commit()

        flash('Habit added successfully!')
        return redirect(url_for('habits'))

    return render_template('add_habit.html')

@app.route('/complete_habit/<int:habit_id>', methods=['POST'])
def complete_habit(habit_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    today = date.today()

    existing_completion = HabitCompletion.query.filter_by(
        habit_id=habit_id,
        user_id=user_id,
        date=today
    ).first()

    if existing_completion:
        flash('✅ You already completed this habit today!')
    else:
        completion = HabitCompletion(habit_id=habit_id, user_id=user_id, date=today)
        db.session.add(completion)

        user = User.query.get(user_id)
        xp_earned = 30
        leveled_up = add_xp_and_check_level(user, xp_earned)

        db.session.commit()

        flash(f'🎉 Habit completed! +{xp_earned} XP earned.')
        if leveled_up:
            flash(f'🚀 You leveled up to Level {user.level}!')

    return redirect(url_for('habits'))

@app.route('/delete_habit/<int:habit_id>', methods=['POST'])
def delete_habit(habit_id):
    if 'user_id' not in session:
        return redirect(url_for('login')) 
    
    user_id = session['user_id']
    habit = Habit.query.filter_by(id=habit_id, user_id=user_id).first()
    
    if habit:
        db.session.delete(habit)  
        db.session.commit()  
        flash('Habit deleted successfully!')  
    else:
        flash('Habit not found or unauthorized action.')  
    
    return redirect(url_for('habits')) 

def xp_for_next_level(level):
    return 100 + (level - 1) * 50

def add_xp_and_check_level(user, amount):
    user.xp += amount
    leveled_up = False

    while user.xp >= xp_for_next_level(user.level):
        user.xp -= xp_for_next_level(user.level)
        user.level += 1
        leveled_up = True

    return leveled_up

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)