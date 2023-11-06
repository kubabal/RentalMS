import logging
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

# set up logging for SQLAlchemy
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///properties.db'
db = SQLAlchemy(app)


# Database models
class Property(db.Model):
    property_id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(150), nullable=False)
    rental_price = db.Column(db.Float, nullable=False)
    tenants = db.relationship('Lease', back_populates='property', cascade="all, delete-orphan")

class Tenant(db.Model):
    tenant_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    leases = db.relationship('Lease', back_populates='tenant', cascade="all, delete-orphan")

class Lease(db.Model):
    lease_id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.property_id'))
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.tenant_id'))
    property = db.relationship('Property', back_populates='tenants')
    tenant = db.relationship('Tenant', back_populates='leases')

# route for root URL
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_property', methods=['GET', 'POST'])
def add_property():
    if request.method == 'POST':
        address = request.form.get('address')
        rental_price = request.form.get('rental_price')
        
        new_property = Property(address=address, rental_price=rental_price)
        
        try:
          db.session.add(new_property)
          db.session.commit()
        except Exception as e:
            print("Failed to add property:", e)
            db.session.rollback()

        return redirect(url_for('index'))
    
    return render_template('add_property.html')

@app.route('/add_tenant', methods=['GET', 'POST'])
def add_tenant():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        
        new_tenant = Tenant(name=name, phone=phone, email=email)

        try:
          db.session.add(new_tenant)
          db.session.commit()
        except Exception as e:
            print("Failed to add tenant:", e)
            db.session.rollback()
        
        return redirect(url_for('index'))
    
    return render_template('add_tenant.html')



 



if __name__ == "__main__":
    with app.app_context():
      db.create_all() # create sqlite db
    app.run(debug=True)