import logging
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from datetime import datetime

# set up logging for SQLAlchemy
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///properties.db'
db = SQLAlchemy(app)


# Database models
class Property(db.Model):
    property_id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(150), nullable=False, index=True)
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
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False, index=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.property_id'), index=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.tenant_id'), index=True)
    property = db.relationship('Property', back_populates='tenants')
    tenant = db.relationship('Tenant', back_populates='leases')
    rent = db.Column(db.Float, nullable=False)

    __table_args__ = (db.Index('idx_leases_dates_property', 'start_date', 'end_date', 'property_id'),)

# route for root URL
@app.route('/')
def index():
    leases = Lease.query.all()
    return render_template('index.html', leases=leases)

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

@app.route('/add_lease', methods=['GET', 'POST'])
def add_lease():
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        property_id = request.form['property_id']
        tenant_id = request.form['tenant_id']
        rent = request.form['rent']

        new_lease = Lease(
            start_date=datetime.strptime(start_date, '%Y-%m-%d'),
            end_date=datetime.strptime(end_date, '%Y-%m-%d'),
            property_id=property_id,
            tenant_id=tenant_id,
            rent=rent
        )
        
        db.session.add(new_lease)
        db.session.commit()

        return redirect(url_for('index'))

    properties = Property.query.all()
    tenants = Tenant.query.all()
    return render_template('add_lease.html', properties=properties, tenants=tenants)

@app.route('/edit_lease/<int:lease_id>', methods=['GET', 'POST'])
def edit_lease(lease_id):
    lease = Lease.query.get_or_404(lease_id)
    if request.method == 'POST':
        lease.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        lease.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        lease.property_id = request.form['property_id']
        lease.tenant_id = request.form['tenant_id']
        lease.rent = request.form['rent']
        db.session.commit()
        return redirect(url_for('index'))
    
    lease = Lease.query.get_or_404(lease_id)
    properties = Property.query.all()
    tenants = Tenant.query.all()
    return render_template('edit_lease.html', lease=lease, properties=properties, tenants=tenants)

@app.route('/delete_lease/<int:lease_id>')
def delete_lease(lease_id):
    lease = Lease.query.get_or_404(lease_id)
    db.session.delete(lease)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/generate_report', methods=['GET', 'POST'])
def generate_report():
    report_data = None
    filtered_leases = None
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        property_id = request.form.get('property_id')

        stmt = text("SELECT Lease.*, Property.address AS property_address, Tenant.name AS tenant_name FROM Lease "
                    "JOIN Property ON Lease.property_id = Property.property_id "
                    "JOIN Tenant ON Lease.tenant_id = Tenant.tenant_id "
                    "WHERE start_date >= :start_date AND end_date <= :end_date")
        params = {'start_date': start_date, 'end_date': end_date}

        if property_id:
            stmt = text("SELECT Lease.*, Property.address AS property_address, Tenant.name AS tenant_name FROM Lease "
                        "JOIN Property ON Lease.property_id = Property.property_id "
                        "JOIN Tenant ON Lease.tenant_id = Tenant.tenant_id "
                        "WHERE start_date >= :start_date AND end_date <= :end_date AND Lease.property_id = :property_id")
            params['property_id'] = property_id

        result = db.session.execute(stmt, params)
        filtered_leases = result.fetchall()

        # STATISTICS
        if filtered_leases:
            average_rent = sum(lease.rent for lease in filtered_leases) / len(filtered_leases)
            max_rent_lease = max(filtered_leases, key=lambda x: x.rent)
            min_rent_lease = min(filtered_leases, key=lambda x: x.rent)
            total_lease_duration = sum((datetime.strptime(lease.end_date, '%Y-%m-%d') - datetime.strptime(lease.start_date, '%Y-%m-%d')).days for lease in filtered_leases)
            average_lease_duration = total_lease_duration / len(filtered_leases)
        else:
            average_rent = 0
            max_rent_lease = None
            min_rent_lease = None
            average_lease_duration = 0

        report_data = {
            "average_rent": average_rent,
            "total_leases": len(filtered_leases),
            "max_rent_lease": max_rent_lease,
            "min_rent_lease": min_rent_lease,
            "average_lease_duration": average_lease_duration
        }

    properties = Property.query.all()
    tenants = Tenant.query.all()
    return render_template('generate_report.html', properties=properties, tenants=tenants, report_data=report_data, filtered_leases=filtered_leases)

 



if __name__ == "__main__":
    with app.app_context():
      db.create_all() # create sqlite db
    app.run(debug=True)