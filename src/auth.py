# src/auth.py
from flask_login import UserMixin, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from src.database import db

login_manager = LoginManager()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # nurse, doctor, admin
    full_name = db.Column(db.String(100), nullable=False)
    facility = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_auth(app):
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Create default users if they don't exist
    with app.app_context():
        if not User.query.filter_by(username='nurse1').first():
            default_nurse = User(
                username='nurse1',
                role='nurse',
                full_name='Jane Mwende',
                facility="Murang'a County Hospital"
            )
            default_nurse.set_password('nurse123')
            db.session.add(default_nurse)
            
        if not User.query.filter_by(username='doctor1').first():
            default_doctor = User(
                username='doctor1', 
                role='doctor',
                full_name='Dr. Kamau Waweru',
                facility="Murang'a County Hospital"
            )
            default_doctor.set_password('doctor123')
            db.session.add(default_doctor)
            
        db.session.commit()