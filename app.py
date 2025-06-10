# app.py - Main Flask Application
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import sqlite3
import os
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///poultry_farm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    farm_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Livestock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    livestock_id = db.Column(db.String(50), unique=True, nullable=False)
    breed = db.Column(db.String(100), nullable=False)
    age_weeks = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, sold, deceased
    health_status = db.Column(db.String(20), default='healthy')
    weight = db.Column(db.Float, default=0.0)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class HealthRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    livestock_id = db.Column(db.Integer, db.ForeignKey('livestock.id'), nullable=False)
    treatment_type = db.Column(db.String(100), nullable=False)
    medication = db.Column(db.String(100))
    dosage = db.Column(db.String(50))
    vet_notes = db.Column(db.Text)
    treatment_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class FeedRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feed_type = db.Column(db.String(100), nullable=False)
    quantity_kg = db.Column(db.Float, nullable=False)
    cost_per_kg = db.Column(db.Float, nullable=False)
    date_purchased = db.Column(db.DateTime, default=datetime.utcnow)
    stock_remaining = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class ProductionRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    eggs_collected = db.Column(db.Integer, default=0)
    eggs_sold = db.Column(db.Integer, default=0)
    revenue = db.Column(db.Float, default=0.0)
    mortality_count = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class FinancialRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # income, expense
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['farm_name'] = user.farm_name
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        farm_name = request.form['farm_name']
        email = request.form['email']
        password = request.form['password']
        location = request.form['location']
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        user = User(
            full_name=full_name,
            farm_name=farm_name,
            email=email,
            password_hash=generate_password_hash(password),
            location=location
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    
    # Get summary statistics
    total_livestock = Livestock.query.filter_by(user_id=user_id, status='active').count()
    
    # Get recent production data
    recent_production = ProductionRecord.query.filter_by(user_id=user_id).order_by(ProductionRecord.date.desc()).limit(7).all()
    
    # Calculate weekly revenue
    week_ago = datetime.now() - timedelta(days=7)
    weekly_revenue = db.session.query(db.func.sum(ProductionRecord.revenue)).filter(
        ProductionRecord.user_id == user_id,
        ProductionRecord.date >= week_ago.date()
    ).scalar() or 0
    
    # Get pending health alerts (vaccinations due)
    pending_alerts = 5  # Placeholder
    
    # Get mortality rate
    mortality_records = ProductionRecord.query.filter_by(user_id=user_id).all()
    total_mortality = sum(record.mortality_count for record in mortality_records)
    
    return render_template('dashboard.html', 
                         total_livestock=total_livestock,
                         weekly_revenue=weekly_revenue,
                         pending_alerts=pending_alerts,
                         total_mortality=total_mortality,
                         recent_production=recent_production)

@app.route('/livestock')
@login_required
def livestock():
    user_id = session['user_id']
    search = request.args.get('search', '')
    status_filter = request.args.get('status', 'all')
    
    query = Livestock.query.filter_by(user_id=user_id)
    
    if search:
        query = query.filter(Livestock.livestock_id.contains(search))
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    livestock_list = query.order_by(Livestock.livestock_id).all()
    
    return render_template('livestock.html', livestock_list=livestock_list)

@app.route('/livestock/add', methods=['GET', 'POST'])
@login_required
def add_livestock():
    if request.method == 'POST':
        livestock = Livestock(
            livestock_id=request.form['livestock_id'],
            breed=request.form['breed'],
            age_weeks=int(request.form['age_weeks']),
            weight=float(request.form['weight']) if request.form['weight'] else 0.0,
            user_id=session['user_id']
        )
        
        db.session.add(livestock)
        db.session.commit()
        
        flash('Livestock added successfully!', 'success')
        return redirect(url_for('livestock'))
    
    return render_template('add_livestock.html')

@app.route('/health')
@login_required
def health():
    user_id = session['user_id']
    health_records = db.session.query(HealthRecord, Livestock).join(Livestock).filter(
        HealthRecord.user_id == user_id
    ).order_by(HealthRecord.treatment_date.desc()).all()
    
    return render_template('health.html', health_records=health_records)

@app.route('/health/add', methods=['GET', 'POST'])
@login_required
def add_health_record():
    if request.method == 'POST':
        livestock_id = request.form['livestock_id']
        
        health_record = HealthRecord(
            livestock_id=livestock_id,
            treatment_type=request.form['treatment_type'],
            medication=request.form['medication'],
            dosage=request.form['dosage'],
            vet_notes=request.form['vet_notes'],
            user_id=session['user_id']
        )
        
        db.session.add(health_record)
        db.session.commit()
        
        flash('Health record added successfully!', 'success')
        return redirect(url_for('health'))
    
    user_id = session['user_id']
    livestock_list = Livestock.query.filter_by(user_id=user_id, status='active').all()
    return render_template('add_health_record.html', livestock_list=livestock_list)

@app.route('/feed')
@login_required
def feed():
    user_id = session['user_id']
    feed_records = FeedRecord.query.filter_by(user_id=user_id).order_by(FeedRecord.date_purchased.desc()).all()
    
    # Calculate total stock value
    total_stock_value = sum(record.stock_remaining * record.cost_per_kg for record in feed_records)
    
    return render_template('feed.html', feed_records=feed_records, total_stock_value=total_stock_value)

@app.route('/feed/add', methods=['GET', 'POST'])
@login_required
def add_feed_record():
    if request.method == 'POST':
        quantity = float(request.form['quantity_kg'])
        
        feed_record = FeedRecord(
            feed_type=request.form['feed_type'],
            quantity_kg=quantity,
            cost_per_kg=float(request.form['cost_per_kg']),
            stock_remaining=quantity,
            user_id=session['user_id']
        )
        
        db.session.add(feed_record)
        db.session.commit()
        
        flash('Feed record added successfully!', 'success')
        return redirect(url_for('feed'))
    
    return render_template('add_feed_record.html')

@app.route('/production')
@login_required
def production():
    user_id = session['user_id']
    production_records = ProductionRecord.query.filter_by(user_id=user_id).order_by(ProductionRecord.date.desc()).all()
    
    return render_template('production.html', production_records=production_records)

@app.route('/production/add', methods=['GET', 'POST'])
@login_required
def add_production_record():
    if request.method == 'POST':
        production_record = ProductionRecord(
            date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
            eggs_collected=int(request.form['eggs_collected']),
            eggs_sold=int(request.form['eggs_sold']),
            revenue=float(request.form['revenue']),
            mortality_count=int(request.form['mortality_count']),
            user_id=session['user_id']
        )
        
        db.session.add(production_record)
        db.session.commit()
        
        flash('Production record added successfully!', 'success')
        return redirect(url_for('production'))
    
    return render_template('add_production_record.html')

@app.route('/financial')
@login_required
def financial():
    user_id = session['user_id']
    financial_records = FinancialRecord.query.filter_by(user_id=user_id).order_by(FinancialRecord.date.desc()).all()
    
    # Calculate totals
    total_income = sum(record.amount for record in financial_records if record.type == 'income')
    total_expenses = sum(record.amount for record in financial_records if record.type == 'expense')
    net_profit = total_income - total_expenses
    
    return render_template('financial.html', 
                         financial_records=financial_records,
                         total_income=total_income,
                         total_expenses=total_expenses,
                         net_profit=net_profit)

@app.route('/financial/add', methods=['GET', 'POST'])
@login_required
def add_financial_record():
    if request.method == 'POST':
        financial_record = FinancialRecord(
            type=request.form['type'],
            category=request.form['category'],
            amount=float(request.form['amount']),
            description=request.form['description'],
            user_id=session['user_id']
        )
        
        db.session.add(financial_record)
        db.session.commit()
        
        flash('Financial record added successfully!', 'success')
        return redirect(url_for('financial'))
    
    return render_template('add_financial_record.html')

@app.route('/notifications')
@login_required
def notifications():
    # Mock notifications for demo
    notifications = [
        {'type': 'vaccination', 'message': 'Vaccination due for batch PL-001', 'date': datetime.now() - timedelta(days=1)},
        {'type': 'feed', 'message': 'Feed stock running low - 5kg remaining', 'date': datetime.now() - timedelta(hours=6)},
        {'type': 'health', 'message': 'Health check recommended for flock B', 'date': datetime.now() - timedelta(days=3)},
    ]
    
    return render_template('notifications.html', notifications=notifications)

@app.route('/settings')
@login_required
def settings():
    user_id = session['user_id']
    user = User.query.get(user_id)
    return render_template('settings.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# API endpoints for charts
@app.route('/api/production-chart')
@login_required
def production_chart_data():
    user_id = session['user_id']
    records = ProductionRecord.query.filter_by(user_id=user_id).order_by(ProductionRecord.date.desc()).limit(30).all()
    
    data = {
        'dates': [record.date.strftime('%Y-%m-%d') for record in reversed(records)],
        'eggs_collected': [record.eggs_collected for record in reversed(records)],
        'revenue': [float(record.revenue) for record in reversed(records)]
    }
    
    return jsonify(data)

@app.route('/api/mortality-chart')
@login_required
def mortality_chart_data():
    user_id = session['user_id']
    records = ProductionRecord.query.filter_by(user_id=user_id).order_by(ProductionRecord.date.desc()).limit(30).all()
    
    data = {
        'dates': [record.date.strftime('%Y-%m-%d') for record in reversed(records)],
        'mortality': [record.mortality_count for record in reversed(records)]
    }
    
    return jsonify(data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

# Create templates directory structure and files
# templates/base.html
# templates/login.html
# templates/register.html
# templates/dashboard.html
# templates/livestock.html
# templates/add_livestock.html
# templates/health.html
# templates/add_health_record.html
# templates/feed.html
# templates/add_feed_record.html
# templates/production.html
# templates/add_production_record.html
# templates/financial.html
# templates/add_financial_record.html
# templates/notifications.html
# templates/settings.html

# static/css/style.css
# static/js/main.js

# requirements.txt
"""
Flask==2.3.2
Flask-SQLAlchemy==3.0.5
Werkzeug==2.3.6
"""