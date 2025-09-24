from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# In-memory data storage (will reset on server restart)
customers = {}
interactions = {}
tags = ['潛在客戶', '已成交', '跟進中', '已流失', 'VIP客戶']

# Customer model functions
def create_customer(name, phone, email, address, notes, customer_tags):
    customer_id = str(uuid.uuid4())
    customers[customer_id] = {
        'id': customer_id,
        'name': name,
        'phone': phone,
        'email': email,
        'address': address,
        'notes': notes,
        'tags': customer_tags,
        'created_at': datetime.now()
    }
    return customer_id

def update_customer(customer_id, name, phone, email, address, notes, customer_tags):
    if customer_id in customers:
        customers[customer_id].update({
            'name': name,
            'phone': phone,
            'email': email,
            'address': address,
            'notes': notes,
            'tags': customer_tags
        })
        return True
    return False

def delete_customer(customer_id):
    if customer_id in customers:
        # Also delete related interactions
        interactions_to_delete = [i_id for i_id, interaction in interactions.items()
                                if interaction['customer_id'] == customer_id]
        for i_id in interactions_to_delete:
            del interactions[i_id]
        del customers[customer_id]
        return True
    return False

def add_interaction(customer_id, interaction_type, description, date):
    interaction_id = str(uuid.uuid4())
    interactions[interaction_id] = {
        'id': interaction_id,
        'customer_id': customer_id,
        'type': interaction_type,
        'description': description,
        'date': date,
        'created_at': datetime.now()
    }
    return interaction_id

# Routes
@app.route('/')
def index():
    return render_template('index.html', customers=customers.values(), tags=tags)

@app.route('/customers')
def customer_list():
    # Filter customers based on search and tag filters
    search_query = request.args.get('search', '').lower()
    tag_filter = request.args.get('tag', '')

    filtered_customers = customers.values()

    if search_query:
        filtered_customers = [c for c in filtered_customers
                            if search_query in c['name'].lower()
                            or search_query in c['phone'].lower()
                            or search_query in c['email'].lower()]

    if tag_filter:
        filtered_customers = [c for c in filtered_customers
                            if tag_filter in c.get('tags', [])]

    return render_template('customers.html',
                         customers=filtered_customers,
                         tags=tags,
                         search_query=search_query,
                         tag_filter=tag_filter)

@app.route('/customer/new', methods=['GET', 'POST'])
def new_customer():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        notes = request.form.get('notes')
        customer_tags = request.form.getlist('tags')

        if not name or not phone or not email:
            flash('請填寫所有必填欄位（姓名、電話、Email）', 'error')
            return render_template('customer_form.html',
                                 customer=None,
                                 tags=tags,
                                 action='new')

        customer_id = create_customer(name, phone, email, address, notes, customer_tags)
        flash('客戶新增成功！', 'success')
        return redirect(url_for('customer_detail', customer_id=customer_id))

    return render_template('customer_form.html', customer=None, tags=tags, action='new')

@app.route('/customer/<customer_id>')
def customer_detail(customer_id):
    if customer_id not in customers:
        flash('客戶不存在', 'error')
        return redirect(url_for('customer_list'))

    customer = customers[customer_id]
    customer_interactions = [i for i in interactions.values()
                           if i['customer_id'] == customer_id]

    return render_template('customer_detail.html',
                         customer=customer,
                         interactions=customer_interactions)

@app.route('/customer/<customer_id>/edit', methods=['GET', 'POST'])
def edit_customer(customer_id):
    if customer_id not in customers:
        flash('客戶不存在', 'error')
        return redirect(url_for('customer_list'))

    customer = customers[customer_id]

    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        notes = request.form.get('notes')
        customer_tags = request.form.getlist('tags')

        if not name or not phone or not email:
            flash('請填寫所有必填欄位（姓名、電話、Email）', 'error')
            return render_template('customer_form.html',
                                 customer=customer,
                                 tags=tags,
                                 action='edit')

        if update_customer(customer_id, name, phone, email, address, notes, customer_tags):
            flash('客戶資料更新成功！', 'success')
            return redirect(url_for('customer_detail', customer_id=customer_id))
        else:
            flash('更新失敗', 'error')

    return render_template('customer_form.html',
                         customer=customer,
                         tags=tags,
                         action='edit')

@app.route('/customer/<customer_id>/delete', methods=['POST'])
def delete_customer_route(customer_id):
    if delete_customer(customer_id):
        flash('客戶已刪除', 'success')
    else:
        flash('刪除失敗', 'error')
    return redirect(url_for('customer_list'))

@app.route('/customer/<customer_id>/interaction/new', methods=['GET', 'POST'])
def new_interaction(customer_id):
    if customer_id not in customers:
        flash('客戶不存在', 'error')
        return redirect(url_for('customer_list'))

    if request.method == 'POST':
        interaction_type = request.form.get('type')
        description = request.form.get('description')
        date = request.form.get('date')

        if not interaction_type or not description or not date:
            flash('請填寫所有欄位', 'error')
            return render_template('interaction_form.html',
                                 customer_id=customer_id,
                                 interaction=None)

        add_interaction(customer_id, interaction_type, description, date)
        flash('互動記錄新增成功！', 'success')
        return redirect(url_for('customer_detail', customer_id=customer_id))

    return render_template('interaction_form.html',
                         customer_id=customer_id,
                         interaction=None)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
