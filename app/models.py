from app import db, bcrypt


class User(db.Model):  
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')  # 'admin' or 'user'
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Port(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    air_quality = db.Column(db.Float, nullable=False)
    water_quality = db.Column(db.Float, nullable=False)
    co2_emissions = db.Column(db.Float, nullable=False)
    incidents = db.Column(db.Integer, nullable=False, default=0)
    subscribers = db.Column(db.Text, default='')  # Emails через запятую
    
    @property
    def green_score(self):
        # Нормализация: 0-100, где 100 - идеально
        score = (
            (1 - min(self.air_quality / 50, 1)) * 25 +
            (1 - min(self.water_quality / 30, 1)) * 25 +
            (1 - min(self.co2_emissions / 1000, 1)) * 25 +
            (1 - min(self.incidents / 5, 1)) * 25
        )
        return round(score, 2)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    port_id = db.Column(db.Integer, db.ForeignKey('port.id'), nullable=False)
    user_email = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())