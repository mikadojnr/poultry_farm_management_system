# app.py - Main Flask Application
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import sqlite3
import os
from functools import wraps
from flask_moment import Moment
from sqlalchemy import func
import shutil
import io
import csv



app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///poultry_farm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
moment = Moment(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    farm_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class UserPreferences(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    weight_unit = db.Column(db.String(10), default='kg')
    currency = db.Column(db.String(10), default='NGN')
    email_notifications = db.Column(db.Boolean, default=True)
    sms_notifications = db.Column(db.Boolean, default=False)
    dashboard_alerts = db.Column(db.Boolean, default=True)

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
    administered_by = db.Column(db.String(100))  # New field
    cost = db.Column(db.Float, default=0.0)     # New field
    symptoms = db.Column(db.Text)               # New field
    next_checkup = db.Column(db.DateTime)       # New field
    status = db.Column(db.String(20), default='completed')  # New field
    treatment_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
class FeedRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feed_type = db.Column(db.String(100), nullable=False)
    quantity_kg = db.Column(db.Float, nullable=False)
    cost_per_kg = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    date_purchased = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expiry_date = db.Column(db.DateTime)
    batch_number = db.Column(db.String(50))
    storage_location = db.Column(db.String(100))
    quality_grade = db.Column(db.String(50))
    stock_remaining = db.Column(db.Float, nullable=False)
    supplier = db.Column(db.String(100))
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'feed_type': self.feed_type,
            'quantity_kg': self.quantity_kg,
            'cost_per_kg': self.cost_per_kg,
            'total_cost': self.total_cost,
            'date_purchased': self.date_purchased.strftime('%Y-%m-%d') if self.date_purchased else None,
            'expiry_date': self.expiry_date.strftime('%Y-%m-%d') if self.expiry_date else None,
            'batch_number': self.batch_number,
            'storage_location': self.storage_location,
            'quality_grade': self.quality_grade,
            'stock_remaining': self.stock_remaining,
            'supplier': self.supplier,
            'notes': self.notes,
            'user_id': self.user_id
        }

class FeedUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feed_id = db.Column(db.Integer, db.ForeignKey('feed_record.id'), nullable=False)
    amount_used = db.Column(db.Float, nullable=False)
    usage_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    notes = db.Column(db.Text)
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
    
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # vaccination, feed, health, production, general
    message = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='unread')  # unread, read
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    related_id = db.Column(db.Integer, nullable=True)  # Optional: ID of related record (e.g., feed_id, health_record_id)

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Helper function to generate notifications
def generate_notifications(user_id):
    """Generate real-time notifications based on farm events."""
    today = datetime.utcnow().date()
    one_week_from_now = today + timedelta(days=7)

    # Clear old notifications (optional: keep only last 30 days or unread)
    Notification.query.filter_by(user_id=user_id).filter(
        db.and_(Notification.date < (datetime.utcnow() - timedelta(days=30)), Notification.status == 'read')
    ).delete()
    db.session.commit()

    # Check for low feed stock
    feed_records = FeedRecord.query.filter_by(user_id=user_id).all()
    for record in feed_records:
        if record.stock_remaining <= 0.1 * record.quantity_kg:  # Less than 10% remaining
            existing = Notification.query.filter_by(
                user_id=user_id,
                type='feed',
                related_id=record.id,
                status='unread'
            ).first()
            if not existing:
                notification = Notification(
                    type='feed',
                    message=f'Feed stock low: {record.feed_type} has {record.stock_remaining:.2f} kg remaining',
                    user_id=user_id,
                    related_id=record.id
                )
                db.session.add(notification)

    # Check for upcoming health checkups/vaccinations
    health_records = HealthRecord.query.filter_by(user_id=user_id).filter(
        HealthRecord.next_checkup != None,
        HealthRecord.next_checkup >= today,
        HealthRecord.next_checkup <= one_week_from_now
    ).all()
    for record in health_records:
        livestock = Livestock.query.get(record.livestock_id)
        existing = Notification.query.filter_by(
            user_id=user_id,
            type='vaccination',
            related_id=record.id,
            status='unread'
        ).first()
        if not existing and livestock:
            notification = Notification(
                type='vaccination',
                message=f'Vaccination/checkup due for {livestock.livestock_id} on {record.next_checkup.strftime("%Y-%m-%d")}',
                user_id=user_id,
                related_id=record.id
            )
            db.session.add(notification)

    # Check for low production
    recent_production = ProductionRecord.query.filter_by(user_id=user_id).order_by(ProductionRecord.date.desc()).limit(7).all()
    avg_eggs = sum(record.eggs_collected for record in recent_production) / len(recent_production) if recent_production else 0
    for record in recent_production:
        if record.eggs_collected < 0.5 * avg_eggs and avg_eggs > 0:  # Less than 50% of average
            existing = Notification.query.filter_by(
                user_id=user_id,
                type='production',
                related_id=record.id,
                status='unread'
            ).first()
            if not existing:
                notification = Notification(
                    type='production',
                    message=f'Low production detected: {record.eggs_collected} eggs collected on {record.date.strftime("%Y-%m-%d")}',
                    user_id=user_id,
                    related_id=record.id
                )
                db.session.add(notification)

    # Check for high mortality
    for record in recent_production:
        if record.mortality_count > 5:  # Arbitrary threshold
            existing = Notification.query.filter_by(
                user_id=user_id,
                type='health',
                related_id=record.id,
                status='unread'
            ).first()
            if not existing:
                notification = Notification(
                    type='health',
                    message=f'High mortality detected: {record.mortality_count} deaths on {record.date.strftime("%Y-%m-%d")}',
                    user_id=user_id,
                    related_id=record.id
                )
                db.session.add(notification)

    db.session.commit()

def calculate_storage_usage(user_id):
    """
    Estimate storage usage based on the database file size, proportional to the user's data.
    """
    try:
        db_size_bytes = os.path.getsize('poultry_farm.db')
        total_users = db.session.query(func.count(User.id)).scalar()
        if total_users == 0:
            return 0.0
        
        # Estimate user's share of the database (simplified)
        user_records = sum(
            db.session.query(func.count(model.id)).filter(model.user_id == user_id).scalar()
            for model in [Livestock, HealthRecord, FeedRecord, FeedUsage, ProductionRecord, FinancialRecord, Notification]
        )
        total_records = sum(
            db.session.query(func.count(model.id)).scalar()
            for model in [Livestock, HealthRecord, FeedRecord, FeedUsage, ProductionRecord, FinancialRecord, Notification]
        )
        
        # Proportion of user's records to total records
        user_proportion = user_records / total_records if total_records > 0 else 0
        user_size_bytes = db_size_bytes * user_proportion
        user_size_mb = user_size_bytes / (1024 * 1024)  # Convert to MB
        return round(user_size_mb, 2)
    except Exception as e:
        print(f"Error calculating storage: {e}")
        return 0.0
    
    
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
        purchase_date_str = request.form.get('purchase_date')

        # Parse purchase_date string into a date object or None
        purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date() if purchase_date_str else None

        livestock = Livestock(
            livestock_id=request.form['livestock_id'],
            breed=request.form['breed'],
            age_weeks=int(request.form['age_weeks']),
            weight=float(request.form['weight']) if request.form['weight'] else 0.0,
            user_id=session['user_id'],
            purchase_date=purchase_date
        )

        db.session.add(livestock)
        db.session.commit()

        flash('Livestock added successfully!', 'success')
        return redirect(url_for('livestock'))

    return render_template('add_livestock.html', editing=False, datetime=datetime)

@app.route('/livestock/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_livestock(id):
    livestock = Livestock.query.get_or_404(id)
    
    purchase_date_str = request.form.get('purchase_date')

    if request.method == 'POST':
        livestock.livestock_id = request.form['livestock_id']
        livestock.breed = request.form['breed']
        livestock.age_weeks = int(request.form['age_weeks'])
        livestock.weight = float(request.form['weight']) if request.form['weight'] else 0.0
        livestock.health_status = request.form.get('health_status', 'healthy')
        
        if purchase_date_str:
            livestock.purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()
        else:
            livestock.purchase_date = None
    
        livestock.notes = request.form.get('notes', '')

        db.session.commit()
        flash('Livestock updated successfully!', 'success')
        return redirect(url_for('livestock'))

    return render_template(
        'add_livestock.html',
        livestock=livestock,
        purchase_date=livestock.purchase_date.strftime('%Y-%m-%d') if livestock.purchase_date else '',
        editing=True,
         datetime=datetime  # still needed for fallback date
    )

@app.route('/livestock/view/<string:id>')
@login_required
def view_livestock(id):
    livestock = Livestock.query.get_or_404(id)
    health_records = HealthRecord.query\
    .filter_by(livestock_id=livestock.id)\
    .order_by(HealthRecord.treatment_date.desc())\
        .all()
    return render_template('view_livestock.html', 
                           livestock=livestock, 
                           health_records=health_records,
                           datetime=datetime)

@app.route('/livestock/delete/<int:livestock_id>', methods=['POST'])
@login_required
def delete_livestock(livestock_id):
    livestock = Livestock.query.get_or_404(livestock_id)

    # Optional: delete associated health records
    HealthRecord.query.filter_by(livestock_id=livestock.id).delete()

    db.session.delete(livestock)
    db.session.commit()
    flash('Livestock and its associated health records were deleted successfully.', 'success')
    return redirect(url_for('livestock'))

@app.route('/health')
@login_required
def health():
    user_id = session['user_id']
    
    # Fetch health records with associated livestock
    health_records = db.session.query(HealthRecord, Livestock).join(Livestock).filter(
        HealthRecord.user_id == user_id
    ).order_by(HealthRecord.treatment_date.desc()).all()
    
    # Calculate health alerts
    today = datetime.utcnow().date()
    one_week_from_now = today + timedelta(days=7)
    
    # Critical alerts: Ongoing treatments or recent symptoms
    critical_records = HealthRecord.query.filter_by(user_id=user_id).filter(
        db.or_(
            HealthRecord.status == 'ongoing',
            HealthRecord.symptoms != None
        )
    ).count()
    
    # Due soon: Vaccinations or checkups due within a week
    due_soon_records = HealthRecord.query.filter_by(user_id=user_id).filter(
        HealthRecord.next_checkup != None,
        HealthRecord.next_checkup >= today,
        HealthRecord.next_checkup <= one_week_from_now
    ).count()
    
    # Healthy percentage: Based on livestock health status
    total_livestock = Livestock.query.filter_by(user_id=user_id, status='active').count()
    healthy_livestock = Livestock.query.filter_by(user_id=user_id, status='active', health_status='healthy').count()
    healthy_percentage = (healthy_livestock / total_livestock * 100) if total_livestock > 0 else 0
    
    # Upcoming vaccinations (for vaccination schedule section)
    upcoming_vaccinations = HealthRecord.query.filter_by(user_id=user_id).filter(
        HealthRecord.next_checkup != None,
        HealthRecord.next_checkup >= today,
        HealthRecord.next_checkup <= one_week_from_now
    ).order_by(HealthRecord.next_checkup).limit(5).all()
    
    return render_template('health.html', 
                         health_records=health_records,
                         critical_count=critical_records,
                         due_soon_count=due_soon_records,
                         healthy_percentage=round(healthy_percentage, 1),
                         upcoming_vaccinations=upcoming_vaccinations)
    
@app.route('/health/add', methods=['GET', 'POST'])
@login_required
def add_health_record():
    if request.method == 'POST':
        treatment_date_str = request.form.get('treatment_date')
        next_checkup_str = request.form.get('next_checkup')
        cost = request.form.get('cost', '')
        
        health_record = HealthRecord(
            livestock_id=int(request.form['livestock_id']),
            treatment_type=request.form['treatment_type'],
            medication=request.form.get('medication'),
            dosage=request.form.get('dosage'),
            vet_notes=request.form.get('vet_notes'),
            administered_by=request.form.get('administered_by'),
            cost=float(cost) if cost else 0.0,
            symptoms=request.form.get('symptoms'),
            next_checkup=datetime.strptime(next_checkup_str, '%Y-%m-%d').date() if next_checkup_str else None,
            status=request.form.get('status', 'completed'),
            treatment_date=datetime.strptime(treatment_date_str, '%Y-%m-%d').date() if treatment_date_str else datetime.utcnow(),
            user_id=session['user_id']
        )
        
        db.session.add(health_record)
        db.session.commit()
        
        flash('Health record added successfully!', 'success')
        return redirect(url_for('health'))
    
    user_id = session['user_id']
    livestock_list = Livestock.query.filter_by(user_id=user_id, status='active').all()
    return render_template('add_health_record.html', livestock_list=livestock_list, datetime=datetime)

@app.route('/health_records/<int:health_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_health_record(health_id):
    health_record = HealthRecord.query.get_or_404(health_id)
    if health_record.user_id != session['user_id']:
        flash('Unauthorized access', 'error')
        return redirect(url_for('health'))
    
    if request.method == 'POST':
        treatment_date_str = request.form.get('treatment_date')
        next_checkup_str = request.form.get('next_checkup')
        cost = request.form.get('cost', '')
        
        health_record.livestock_id = int(request.form['livestock_id'])
        health_record.treatment_type = request.form['treatment_type']
        health_record.medication = request.form.get('medication')
        health_record.dosage = request.form.get('dosage')
        health_record.vet_notes = request.form.get('vet_notes')
        health_record.administered_by = request.form.get('administered_by')
        cost=float(cost) if cost else 0.0,
        health_record.symptoms = request.form.get('symptoms')
        health_record.next_checkup = datetime.strptime(next_checkup_str, '%Y-%m-%d').date() if next_checkup_str else None
        health_record.status = request.form.get('status', 'completed')
        health_record.treatment_date = datetime.strptime(treatment_date_str, '%Y-%m-%d').date() if treatment_date_str else datetime.utcnow()
        
        db.session.commit()
        flash('Health record updated successfully!', 'success')
        return redirect(url_for('health'))
    
    user_id = session['user_id']
    livestock_list = Livestock.query.filter_by(user_id=user_id, status='active').all()
    return render_template(
        'add_health_record.html',
        livestock_list=livestock_list,
        health_record=health_record,
        editing=True,
        treatment_date=health_record.treatment_date.strftime('%Y-%m-%d') if health_record.treatment_date else '',
        next_checkup=health_record.next_checkup.strftime('%Y-%m-%d') if health_record.next_checkup else '',
        datetime=datetime
    )
    
@app.route('/health_records/<int:health_id>/delete', methods=['POST'])
@login_required
def delete_health_record(health_id):
    health_record = HealthRecord.query.get_or_404(health_id)
    if health_record.user_id != session['user_id']:
        flash('Unauthorized access', 'error')
        return redirect(url_for('health'))
    
    db.session.delete(health_record)
    db.session.commit()
    flash('Health record deleted successfully!', 'success')
    return redirect(url_for('health'))

@app.route('/feed')
@login_required
def feed():
    user_id = session['user_id']
    feed_records = FeedRecord.query.filter_by(user_id=user_id).order_by(FeedRecord.date_purchased.desc()).all()
    
    total_stock_value = sum(record.stock_remaining * record.cost_per_kg for record in feed_records)
    
    # Fetch usage history for each feed record (limited to 10 per record)
    feed_usage = {}
    for record in feed_records:
        try:
            usage_records = FeedUsage.query.filter_by(feed_id=record.id).order_by(FeedUsage.usage_date.desc()).limit(10).all()
            feed_usage[record.id] = [{
                'id': usage.id,
                'amount_used': float(usage.amount_used) if usage.amount_used is not None else 0.0,
                'usage_date': usage.usage_date.strftime('%Y-%m-%d') if usage.usage_date else '',
                'notes': str(usage.notes) if usage.notes is not None else 'N/A'
            } for usage in usage_records]
            
        except Exception as e:
            
            feed_usage[record.id] = []
    
    
    return render_template('feed.html', 
                         feed_records=feed_records, 
                         total_stock_value=total_stock_value,
                         feed_usage=feed_usage)

@app.route('/feed/add', methods=['GET', 'POST'])
@login_required
def add_feed_record():
    if request.method == 'POST':
        quantity = request.form.get('quantity_kg', '')
        cost_per_kg = request.form.get('cost_per_kg', '')
        date_purchased_str = request.form.get('date_purchased')
        expiry_date_str = request.form.get('expiry_date')
        
        # Validate required fields
        if not quantity or not cost_per_kg or not date_purchased_str or not request.form['feed_type']:
            flash('Feed type, quantity, cost per kg, and purchase date are required.', 'error')
            return render_template('add_feed_record.html', editing=False, datetime=datetime)
        
        try:
            quantity = float(quantity)
            cost_per_kg = float(cost_per_kg)
            if quantity <= 0 or cost_per_kg <= 0:
                raise ValueError("Quantity and cost per kg must be positive.")
        except ValueError:
            flash('Invalid quantity or cost per kg. Please enter valid positive numbers.', 'error')
            return render_template('add_feed_record.html', editing=False, datetime=datetime)
        
        feed_record = FeedRecord(
            feed_type=request.form['feed_type'],
            quantity_kg=quantity,
            cost_per_kg=cost_per_kg,
            total_cost=quantity * cost_per_kg,
            date_purchased=datetime.strptime(date_purchased_str, '%Y-%m-%d').date(),
            expiry_date=datetime.strptime(expiry_date_str, '%Y-%m-%d').date() if expiry_date_str else None,
            batch_number=request.form.get('batch_number'),
            storage_location=request.form.get('storage_location'),
            quality_grade=request.form.get('quality_grade'),
            stock_remaining=quantity,
            supplier=request.form.get('supplier'),
            notes=request.form.get('notes'),
            user_id=session['user_id']
        )
        
        db.session.add(feed_record)
        db.session.commit()
        
        flash('Feed record added successfully!', 'success')
        return redirect(url_for('feed'))
    
    return render_template('add_feed_record.html', editing=False, datetime=datetime)

@app.route('/feed/<int:feed_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_feed_record(feed_id):
    feed_record = FeedRecord.query.get_or_404(feed_id)
    if feed_record.user_id != session['user_id']:
        flash('Unauthorized access', 'error')
        return redirect(url_for('feed'))
    
    if request.method == 'POST':
        quantity = request.form.get('quantity_kg', '')
        cost_per_kg = request.form.get('cost_per_kg', '')
        date_purchased_str = request.form.get('date_purchased')
        expiry_date_str = request.form.get('expiry_date')
        
        # Validate required fields
        if not quantity or not cost_per_kg or not date_purchased_str or not request.form['feed_type']:
            flash('Feed type, quantity, cost per kg, and purchase date are required.', 'error')
            return render_template('add_feed_record.html', editing=True, feed_record=feed_record, datetime=datetime)
        
        try:
            quantity = float(quantity)
            cost_per_kg = float(cost_per_kg)
            if quantity <= 0 or cost_per_kg <= 0:
                raise ValueError("Quantity and cost per kg must be positive.")
        except ValueError:
            flash('Invalid quantity or cost per kg. Please enter valid positive numbers.', 'error')
            return render_template('add_feed_record.html', editing=True, feed_record=feed_record, datetime=datetime)
        
        feed_record.feed_type = request.form['feed_type']
        feed_record.quantity_kg = quantity
        feed_record.cost_per_kg = cost_per_kg
        feed_record.total_cost = quantity * cost_per_kg
        feed_record.date_purchased = datetime.strptime(date_purchased_str, '%Y-%m-%d').date()
        feed_record.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date() if expiry_date_str else None
        feed_record.batch_number = request.form.get('batch_number')
        feed_record.storage_location = request.form.get('storage_location')
        feed_record.quality_grade = request.form.get('quality_grade')
        feed_record.stock_remaining = quantity  # Assuming edit resets stock_remaining to quantity
        feed_record.supplier = request.form.get('supplier')
        feed_record.notes = request.form.get('notes')
        
        db.session.commit()
        flash('Feed record updated successfully!', 'success')
        return redirect(url_for('feed'))
    
    return render_template(
        'add_feed_record.html',
        editing=True,
        feed_record=feed_record,
        date_purchased=feed_record.date_purchased.strftime('%Y-%m-%d') if feed_record.date_purchased else '',
        expiry_date=feed_record.expiry_date.strftime('%Y-%m-%d') if feed_record.expiry_date else '',
        datetime=datetime
    )

@app.route('/feed/<int:feed_id>/delete', methods=['POST'])
@login_required
def delete_feed_record(feed_id):
    feed_record = FeedRecord.query.get_or_404(feed_id)
    if feed_record.user_id != session['user_id']:
        flash('Unauthorized access', 'error')
        return redirect(url_for('feed'))
    
    db.session.delete(feed_record)
    db.session.commit()
    flash('Feed record deleted successfully!', 'success')
    return redirect(url_for('feed'))

@app.route('/feed/<int:feed_id>/use', methods=['POST'])
@login_required
def record_feed_usage(feed_id):
    feed_record = FeedRecord.query.get_or_404(feed_id)
    if feed_record.user_id != session['user_id']:
        flash('Unauthorized access', 'error')
        return redirect(url_for('feed'))
    
    amount_used = request.form.get('amount_used')
    usage_date_str = request.form.get('usage_date')
    notes = request.form.get('notes')
    
    # Validate inputs
    if not amount_used or not usage_date_str:
        flash('Amount used and usage date are required', 'error')
        return redirect(url_for('feed'))
    
    try:
        amount_used = float(amount_used)
        if amount_used <= 0:
            flash('Amount used must be positive', 'error')
            return redirect(url_for('feed'))
        if amount_used > feed_record.stock_remaining:
            flash(f'Amount used ({amount_used:.2f} kg) exceeds stock remaining ({feed_record.stock_remaining:.2f} kg)', 'error')
            return redirect(url_for('feed'))
        usage_date = datetime.strptime(usage_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid amount or date format', 'error')
        return redirect(url_for('feed'))
    
    # Update stock_remaining
    feed_record.stock_remaining -= amount_used
    
    # Create FeedUsage record
    feed_usage = FeedUsage(
        feed_id=feed_id,
        amount_used=amount_used,
        usage_date=usage_date,
        notes=notes,
        user_id=session['user_id']
    )
    
    db.session.add(feed_usage)
    db.session.commit()
    
    flash('Feed usage recorded successfully', 'success')
    return redirect(url_for('feed'))


@app.route('/production')
@login_required
def production():
    user_id = session['user_id']
    production_records = ProductionRecord.query.filter_by(user_id=user_id).order_by(ProductionRecord.date.desc()).all()
    
    return render_template('production.html', production_records=production_records, datetime=datetime)

@app.route('/production/add', methods=['GET', 'POST'])
@login_required
def add_production_record():
    if request.method == 'POST':
        try:
            date_str = request.form['date']
            eggs_collected = request.form['eggs_collected']
            eggs_sold = request.form['eggs_sold']
            revenue = request.form['revenue']
            mortality_count = request.form['mortality_count']
            
            if not all([date_str, eggs_collected, eggs_sold, revenue]):
                flash('All required fields must be filled.', 'error')
                return render_template('add_production_record.html', datetime=datetime)
                
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            eggs_collected = int(eggs_collected)
            eggs_sold = int(eggs_sold)
            revenue = float(revenue)
            mortality_count = int(mortality_count)
            
            if eggs_sold > eggs_collected:
                flash('Eggs sold cannot exceed eggs collected.', 'error')
                return render_template('add_production_record.html', datetime=datetime)
            
            if eggs_collected < 0 or eggs_sold < 0 or revenue < 0 or mortality_count < 0:
                flash('Values cannot be negative.', 'error')
                return render_template('add_production_record.html', datetime=datetime)
                
            production_record = ProductionRecord(
                date=date,
                eggs_collected=eggs_collected,
                eggs_sold=eggs_sold,
                revenue=revenue,
                mortality_count=mortality_count,
                user_id=session['user_id']
            )
            
            db.session.add(production_record)
            db.session.commit()
            flash('Production record added successfully!', 'success')
            return redirect(url_for('production'))
        except ValueError:
            flash('Invalid input format. Please check your entries.', 'error')
            return render_template('add_production_record.html', datetime=datetime)
    
    return render_template('add_production_record.html', datetime=datetime)

@app.route('/production/edit/<int:production_id>', methods=['GET', 'POST'])
@login_required
def edit_production_record(production_id):
    production_record = ProductionRecord.query.get_or_404(production_id)
    
    if production_record.user_id != session['user_id']:
        flash('Unauthorized access', 'error')
        return redirect(url_for('production'))
    
    if request.method == 'POST':
        try:
            date_str = request.form['date']
            eggs_collected = request.form['eggs_collected']
            eggs_sold = request.form['eggs_sold']
            revenue = request.form['revenue']
            mortality_count = request.form['mortality_count']
            
            if not all([date_str, eggs_collected, eggs_sold, revenue]):
                flash('All required fields must be filled.', 'error')
                return render_template('add_production_record.html', 
                                     production=production_record,
                                     editing=True,
                                     datetime=datetime)
                
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            eggs_collected = int(eggs_collected)
            eggs_sold = int(eggs_sold)
            revenue = float(revenue)
            mortality_count = int(mortality_count)
            
            if eggs_sold > eggs_collected:
                flash('Eggs sold cannot exceed eggs collected.', 'error')
                return render_template('add_production_record.html', 
                                     production=production_record,
                                     editing=True,
                                     datetime=datetime)
            
            if eggs_collected < 0 or eggs_sold < 0 or revenue < 0 or mortality_count < 0:
                flash('Values cannot be negative.', 'error')
                return render_template('add_production_record.html', 
                                     production=production_record,
                                     editing=True,
                                     datetime=datetime)
                
            production_record.date = date
            production_record.eggs_collected = eggs_collected
            production_record.eggs_sold = eggs_sold
            production_record.revenue = revenue
            production_record.mortality_count = mortality_count
            
            db.session.commit()
            flash('Production record updated successfully!', 'success')
            return redirect(url_for('production'))
        except ValueError:
            flash('Invalid input format. Please check your entries.', 'error')
            return render_template('add_production_record.html', 
                                 production=production_record,
                                 editing=True,
                                 datetime=datetime)
    
    return render_template(
        'add_production_record.html',
        production=production_record,
        editing=True,
        datetime=datetime
    )

@app.route('/production/delete/<int:production_id>', methods=['POST'])
@login_required
def delete_production_record(production_id):
    production_record = ProductionRecord.query.get_or_404(production_id)
    
    if production_record.user_id != session['user_id']:
        flash('Unauthorized access', 'error')
        return redirect(url_for('production'))
    
    db.session.delete(production_record)
    db.session.commit()
    flash('Production record deleted successfully!', 'success')
    return redirect(url_for('production'))

@app.route('/financial')
@login_required
def financial():
    user_id = session['user_id']
    financial_records = FinancialRecord.query.filter_by(user_id=user_id).order_by(FinancialRecord.date.desc()).all()
    
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
        try:
            type = request.form['type']
            category = request.form['category']
            amount = request.form['amount']
            description = request.form.get('description')
            date_str = request.form.get('date')

            if not all([type, category, amount]):
                flash('Type, category, and amount are required.', 'error')
                return render_template('add_financial_record.html', datetime=datetime)
            
            amount = float(amount)
            if amount <= 0:
                flash('Amount must be positive.', 'error')
                return render_template('add_financial_record.html', datetime=datetime)
            
            date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
            
            financial_record = FinancialRecord(
                type=type,
                category=category,
                amount=amount,
                description=description,
                date=date,
                user_id=session['user_id']
            )
            
            db.session.add(financial_record)
            db.session.commit()
            flash('Financial record added successfully!', 'success')
            return redirect(url_for('financial'))
        except ValueError:
            flash('Invalid input format. Please check your entries.', 'error')
            return render_template('add_financial_record.html', datetime=datetime)
    
    return render_template('add_financial_record.html', datetime=datetime)

@app.route('/financial/edit/<int:financial_id>', methods=['GET', 'POST'])
@login_required
def edit_financial_record(financial_id):
    financial_record = FinancialRecord.query.get_or_404(financial_id)
    
    if financial_record.user_id != session['user_id']:
        flash('Unauthorized access', 'error')
        return redirect(url_for('financial'))
    
    if request.method == 'POST':
        try:
            type = request.form['type']
            category = request.form['category']
            amount = request.form['amount']
            description = request.form.get('description')
            date_str = request.form.get('date')
            
            if not all([type, category, amount]):
                flash('Type, category, and amount are required.', 'error')
                return render_template('add_financial_record.html', 
                                     financial=financial_record,
                                     editing=True,
                                     datetime=datetime)
            
            amount = float(amount)
            if amount <= 0:
                flash('Amount must be positive.', 'error')
                return render_template('add_financial_record.html', 
                                     financial=financial_record,
                                     editing=True,
                                     datetime=datetime)
            
            date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
            
            financial_record.type = type
            financial_record.category = category
            financial_record.amount = amount
            financial_record.description = description
            financial_record.date = date
            
            db.session.commit()
            flash('Financial record updated successfully!', 'success')
            return redirect(url_for('financial'))
        except ValueError:
            flash('Invalid input format. Please check your entries.', 'error')
            return render_template('add_financial_record.html', 
                                 financial=financial_record,
                                 editing=True,
                                 datetime=datetime)
    
    return render_template(
        'add_financial_record.html',
        financial=financial_record,
        editing=True,
        datetime=datetime
    )

@app.route('/financial/delete/<int:financial_id>', methods=['POST'])
@login_required
def delete_financial_record(financial_id):
    financial_record = FinancialRecord.query.get_or_404(financial_id)
    
    if financial_record.user_id != session['user_id']:
        flash('Unauthorized access', 'error')
        return redirect(url_for('financial'))
    
    db.session.delete(financial_record)
    db.session.commit()
    flash('Financial record deleted successfully!', 'success')
    return redirect(url_for('financial'))

@app.route('/notifications')
@login_required
def notifications():
    user_id = session['user_id']
    generate_notifications(user_id)  # Generate notifications before rendering
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.date.desc()).all()
    
    # Calculate notification counts for categories
    health_count = Notification.query.filter_by(user_id=user_id, type='health', status='unread').count() + \
                   Notification.query.filter_by(user_id=user_id, type='vaccination', status='unread').count()
    feed_count = Notification.query.filter_by(user_id=user_id, type='feed', status='unread').count()
    production_count = Notification.query.filter_by(user_id=user_id, type='production', status='unread').count()
    general_count = Notification.query.filter_by(user_id=user_id, type='general', status='unread').count()
    
    return render_template('notifications.html', 
                         notifications=notifications,
                         health_count=health_count,
                         feed_count=feed_count,
                         production_count=production_count,
                         general_count=general_count)

@app.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != session['user_id']:
        flash('Unauthorized access', 'error')
        return redirect(url_for('notifications'))
    
    notification.status = 'read'
    db.session.commit()
    flash('Notification marked as read', 'success')
    return redirect(url_for('notifications'))

@app.route('/notifications/mark_all_read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    user_id = session['user_id']
    Notification.query.filter_by(user_id=user_id, status='unread').update({'status': 'read'})
    db.session.commit()
    flash('All notifications marked as read', 'success')
    return redirect(url_for('notifications'))

@app.route('/notifications/clear_all', methods=['POST'])
@login_required
def clear_all_notifications():
    user_id = session['user_id']
    Notification.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    flash('All notifications cleared', 'success')
    return redirect(url_for('notifications'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        flash('User not found.', 'error')
        session.clear()
        return redirect(url_for('login'))
    
    preferences = UserPreferences.query.filter_by(user_id=user_id).first()
    if not preferences:
        preferences = UserPreferences(user_id=user_id)
        db.session.add(preferences)
        db.session.commit()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            full_name = request.form.get('full_name')
            farm_name = request.form.get('farm_name')
            email = request.form.get('email')
            location = request.form.get('location')
            
            if not all([full_name, farm_name, email, location]):
                flash('All profile fields are required.', 'error')
                return render_template('settings.html', user=user, preferences=preferences)
            
            if email != user.email and User.query.filter_by(email=email).first():
                flash('Email already registered.', 'error')
                return render_template('settings.html', user=user, preferences=preferences)
            
            user.full_name = full_name
            user.farm_name = farm_name
            user.email = email
            user.location = location
            session['farm_name'] = farm_name
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        
        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not all([current_password, new_password, confirm_password]):
                flash('All password fields are required.', 'error')
                return render_template('settings.html', user=user, preferences=preferences)
            
            if not check_password_hash(user.password_hash, current_password):
                flash('Current password is incorrect.', 'error')
                return render_template('settings.html', user=user, preferences=preferences)
            
            if new_password != confirm_password:
                flash('New passwords do not match.', 'error')
                return render_template('settings.html', user=user, preferences=preferences)
            
            if len(new_password) < 8:
                flash('New password must be at least 8 characters long.', 'error')
                return render_template('settings.html', user=user, preferences=preferences)
            
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash('Password changed successfully!', 'success')
        
        elif action == 'save_preferences':
            weight_unit = request.form.get('weight_unit')
            currency = request.form.get('currency')
            email_notifications = request.form.get('email_notifications') == 'on'
            sms_notifications = request.form.get('sms_notifications') == 'on'
            dashboard_alerts = request.form.get('dashboard_alerts') == 'on'
            
            preferences.weight_unit = weight_unit
            preferences.currency = currency
            preferences.email_notifications = email_notifications
            preferences.sms_notifications = sms_notifications
            preferences.dashboard_alerts = dashboard_alerts
            db.session.commit()
            flash('Preferences saved successfully!', 'success')
        
        return redirect(url_for('settings'))
    
    storage_usage = calculate_storage_usage(user_id)
    return render_template('settings.html', user=user, preferences=preferences, storage_usage=storage_usage)

@app.route('/settings/export_data', methods=['POST'])
@login_required
def export_data():
    user_id = session['user_id']
    output = io.StringIO()
    writer = csv.writer(output)
    
    models = [
        (Livestock, ['livestock_id', 'breed', 'age_weeks', 'status', 'health_status', 'weight', 'purchase_date']),
        (HealthRecord, ['livestock_id', 'treatment_type', 'medication', 'dosage', 'vet_notes', 'administered_by', 'cost', 'symptoms', 'next_checkup', 'status', 'treatment_date']),
        (FeedRecord, ['feed_type', 'quantity_kg', 'cost_per_kg', 'total_cost', 'date_purchased', 'expiry_date', 'batch_number', 'storage_location', 'quality_grade', 'stock_remaining', 'supplier', 'notes']),
        (FeedUsage, ['feed_id', 'amount_used', 'usage_date', 'notes']),
        (ProductionRecord, ['date', 'eggs_collected', 'eggs_sold', 'revenue', 'mortality_count']),
        (FinancialRecord, ['type', 'category', 'amount', 'description', 'date']),
        (Notification, ['type', 'message', 'date', 'status'])
    ]
    
    for model, fields in models:
        writer.writerow([f'-- {model.__name__} --'])
        writer.writerow(fields)
        records = model.query.filter_by(user_id=user_id).all()
        for record in records:
            row = []
            for field in fields:
                value = getattr(record, field)
                if isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S') if value else ''
                row.append(str(value))
            writer.writerow(row)
        writer.writerow([])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'farm_data_{datetime.utcnow().strftime("%Y%m%d")}.csv'
    )

@app.route('/settings/create_backup', methods=['POST'])
@login_required
def create_backup():
    user_id = session['user_id']
    backup_dir = 'backups'
    os.makedirs(backup_dir, exist_ok=True)
    backup_file = os.path.join(backup_dir, f'backup_user_{user_id}_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}.db')
    
    shutil.copyfile('instance/poultry_farm.db', backup_file)
    
    flash('Backup created successfully!', 'success')
    return redirect(url_for('settings'))

@app.route('/settings/delete_account', methods=['POST'])
@login_required
def delete_account():
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        flash('User not found.', 'error')
        session.clear()
        return redirect(url_for('login'))
    
    confirm = request.form.get('confirm')
    if confirm != 'DELETE':
        flash('Please type "DELETE" to confirm account deletion.', 'error')
        return redirect(url_for('settings'))
    
    # Delete all user-related data
    for model in [Notification, FinancialRecord, ProductionRecord, FeedUsage, FeedRecord, HealthRecord, Livestock, UserPreferences, User]:
        model.query.filter_by(user_id=user_id).delete()
    
    db.session.commit()
    session.clear()
    flash('Your account and all associated data have been deleted.', 'success')
    return redirect(url_for('login'))

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
