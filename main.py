from flask import Flask, render_template, request, redirect, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask import url_for
from sqlalchemy import inspect
import base64
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///menu.db'
app.config['SECRET_KEY'] = os.urandom(24)  # Добавляем секретный ключ для сессии
db = SQLAlchemy(app)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

# Создание таблиц
with app.app_context():
    db.create_all()


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String, nullable=True)  # Тип поля image - строка для хранения base64

@app.route('/')
def index():
    cards = Card.query.all()
    return render_template('index.html', cards=cards)

@app.route('/cart')
def cart():
    # Извлечение всех товаров из БД
    cart_items = CartItem.query.all()
    # Ваш код для отображения корзины
    return render_template('cart.html', items=cart_items)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    item_id = request.form['item_id']
    quantity = int(request.form['quantity'])
    try:
        # Проверка наличия товара в БД и обновление количества
        existing_item = CartItem.query.filter_by(item_id=item_id).first()
        if existing_item:
            existing_item.quantity += quantity
        else:
            new_item = CartItem(item_id=item_id, quantity=quantity)
            db.session.add(new_item)
        db.session.commit()
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        db.session.rollback()  # Откат транзакции в случае ошибки
    return redirect(url_for('cart'))

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    card_id = request.form.get('card_id')
    cart_items = session.get('cart_items', [])
    
    # Удаляем товар из сессии
    session['cart_items'] = [item for item in cart_items if item['id'] != int(card_id)]
    session.modified = True
    
    return jsonify({'status': 'success'})

@app.route('/additem', methods=['GET','POST'])
def additem():
    # Получаем данные из формы
    category = request.form.get('category')
    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price')
    image_data = request.form.get('image')

    # Создаем картинку из base64-данных
    image_data = image_data.split(',')[1]
    image_data = base64.b64decode(image_data)
    image_path = f'static/images/{name}.jpg'
    with open(image_path, 'wb') as f:
        f.write(image_data)

    # Добавляем карточку в базу данных
    new_card = Card(category=category, name=name, description=description, price=price, image=image_path)
    db.session.add(new_card)
    db.session.commit()

    # Получаем список карточек
    cards = Card.query.all()

    # Возвращаем список карточек в формате JSON
    response = {'cards': [card.to_dict() for card in cards]}
    return jsonify(response)




@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    session['cart_items'] = []
    session.modified = True
    return jsonify({'status': 'success'})


if __name__ == '__main__':
    app.run(debug=True)
