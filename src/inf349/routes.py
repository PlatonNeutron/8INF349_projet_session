import urllib.request
import urllib.error
import json
from datetime import datetime
from flask import jsonify, request, make_response
from . import app
from .models import Product, Order, ShippingInformation, CreditCard, Transaction

@app.route('/', methods=['GET'])
def get_products():
    """
    GET /
    Récupère la liste complète des produits disponibles.
    """

    # Récupérer tous les produits depuis la db
    produits_db = Product.select()
    
    # Formater les données
    liste_produits = []
    for p in produits_db:
        liste_produits.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "weight": p.weight,
            "in_stock": p.in_stock,
            "image": p.image
        })

    # Retourner le resultat    
    return jsonify({"products": liste_produits}), 200

@app.route('/order', methods=['POST'])
def create_order():
    """
    POST /order
    Crée une nouvelle commande.
    """
    data = request.get_json()

    # Validation de la structure initiale
    if not data or 'product' not in data:
        return jsonify({
            "errors": {
                "product": {
                    "code": "missing-fields",
                    "name": "La création d'une commande nécessite un produit"
                }
            }
        }), 422

    product_data = data['product']
    product_id = product_data.get('id')
    quantity = product_data.get('quantity')

    # Validation des champs id et quantity
    if product_id is None or quantity is None or not isinstance(quantity, int) or quantity < 1:
        return jsonify({
            "errors": {
                "product": {
                    "code": "missing-fields",
                    "name": "La création d'une commande nécessite un produit"
                }
            }
        }), 422

    # Vérification de l'existence et de l'inventaire du produit
    product = Product.get_or_none(Product.id == product_id)
    if not product:
        return jsonify({
            "errors": {
                "product": {
                    "code": "out-of-inventory",
                    "name": "Le produit demandé n'est pas en inventaire"
                }
            }
        }), 422

    if not product.in_stock:
        return jsonify({
            "errors": {
                "product": {
                    "code": "out-of-inventory",
                    "name": "Le produit demandé n'est pas en inventaire"
                }
            }
        }), 422

    # Création de la commande
    total_price = product.price * quantity
    
    new_order = Order.create(
        product=product,
        quantity=quantity,
        total_price=total_price,
        paid=False
    )

    # Retourner 302
    response = make_response("", 302)
    response.headers['Location'] = f"/order/{new_order.id}"
    return response

@app.route('/order/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """
    GET /order/<order_id>
    Récupère les détails d'une commande spécifique.
    """

    # Récupérer la commande
    order = Order.get_or_none(Order.id == order_id)
    if not order:
        return jsonify({"error": "Commande non trouvée"}), 404

    # Récupérer le produit associé
    product = order.product

    # Calcul du poids total
    total_weight = product.weight * order.quantity

    # Calcul du prix d'expédition
    if total_weight <= 500:
        shipping_price = 500
    elif total_weight < 2000:
        shipping_price = 1000
    else:
        shipping_price = 2500

    # Le prix total
    total_price = product.price * order.quantity

    total_price_tax = order.total_price_tax if order.total_price_tax else total_price

    # Récupération des relations (si elles existent, sinon null)
    shipping_info = order.shipping_information.first()
    credit_card = order.credit_card.first()
    transaction = order.transaction.first()

    # S'il existe ont ajoute les différentes infos
    shipping_dict = {}
    if shipping_info:
        shipping_dict = {
            "country": shipping_info.country,
            "address": shipping_info.address,
            "postal_code": shipping_info.postal_code,
            "city": shipping_info.city,
            "province": shipping_info.province
        }

    credit_card_dict = {}
    if credit_card:
        credit_card_dict = {
            "name": credit_card.name,
            "first_digits": credit_card.first_digits,
            "last_digits": credit_card.last_digits,
            "expiration_year": credit_card.expiration_year,
            "expiration_month": credit_card.expiration_month
        }

    transaction_dict = {}
    if transaction:
        transaction_dict = {
            "id": transaction.transaction_id,
            "success": transaction.success,
            "amount_charged": transaction.amount_charged
        }

    # Construction de la réponse finale
    response_data = {
        "order": {
            "id": order.id,
            "total_price": total_price,
            "total_price_tax": total_price_tax,
            "email": order.email,
            "credit_card": credit_card_dict,
            "shipping_information": shipping_dict,
            "paid": order.paid,
            "transaction": transaction_dict,
            "product": {
                "id": product.id,
                "quantity": order.quantity
            },
            "shipping_price": shipping_price
        }
    }

    return jsonify(response_data), 200

@app.route('/order/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    """
    PUT /order/<order_id>
    Redirige vers la mise à jour des infos OU le paiement.
    """
    order = Order.get_or_none(Order.id == order_id)
    if not order:
        return jsonify({"error": "Commande non trouvée"}), 404
        
    data = request.get_json()
    if not data:
        return jsonify({"errors": {"order": {"code": "missing-fields", "name": "Payload manquant"}}}), 422
        
    # Logique de paiement
    if "credit_card" in data:
        if "order" in data:
            return jsonify({"errors": {"order": {"code": "invalid-request", "name": "Le paiement et la mise à jour des informations doivent être faits séparément."}}}), 422
        return handle_payment(order, data["credit_card"], order_id)
        
    # Logique de mise à jour des informations de livraison
    elif "order" in data:
        return handle_shipping_update(order, data["order"], order_id)
        
    # Cas invalide
    return jsonify({"errors": {"order": {"code": "invalid-request", "name": "Requête invalide"}}}), 400

def handle_payment(order, cc_data, order_id):
    """
    Gère la logique de paiement d'une commande.
    Parent: update_order
    """
    if not order.email or order.shipping_information.count() == 0:
        return jsonify({"errors": {"order": {"code": "missing-fields", "name": "Les informations du client sont nécessaire avant d'appliquer une carte de crédit"}}}), 422
        
    if order.paid:
        return jsonify({"errors": {"order": {"code": "already-paid", "name": "La commande a déjà été payée."}}}), 422
        
    cvv = cc_data.get("cvv")
    if not isinstance(cvv, str) or len(cvv) != 3 or not cvv.isdigit():
        return jsonify({"errors": {"credit_card": {"code": "invalid-cvv", "name": "Le CVV doit être une chaîne de 3 chiffres"}}}), 422
        
    exp_year = cc_data.get("expiration_year")
    exp_month = cc_data.get("expiration_month")
    
    if not isinstance(exp_year, int) or not isinstance(exp_month, int):
        return jsonify({"errors": {"credit_card": {"code": "invalid-expiration", "name": "Les dates d'expiration doivent être des entiers"}}}), 422
        
    now = datetime.now()
    if exp_year < now.year or (exp_year == now.year and exp_month < now.month):
        return jsonify({"errors": {"credit_card": {"code": "card-expired", "name": "La carte de crédit est expirée."}}}), 422
        
    amount_charged = int(order.total_price + order.shipping_price)
    
    pay_url = "https://dimensweb.uqac.ca/~jgnault/shops/pay/"
    payload = {"credit_card": cc_data, "amount_charged": amount_charged}
    
    req = urllib.request.Request(
        pay_url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            CreditCard.create(
                order=order,
                name=result["credit_card"]["name"],
                first_digits=result["credit_card"]["first_digits"],
                last_digits=result["credit_card"]["last_digits"],
                expiration_year=result["credit_card"]["expiration_year"],
                expiration_month=result["credit_card"]["expiration_month"]
            )
            
            Transaction.create(
                order=order,
                transaction_id=result["transaction"]["id"],
                success=result["transaction"]["success"],
                amount_charged=result["transaction"]["amount_charged"]
            )
            
            order.paid = True
            order.save()
            
            return get_order(order_id)
            
    except urllib.error.HTTPError as e:
        if e.code == 422:
            return jsonify(json.loads(e.read().decode('utf-8'))), 422
        return jsonify({"error": "Erreur inattendue du service de paiement"}), e.code

def handle_shipping_update(order, order_data, order_id):
    """
    Gère la mise à jour des informations de livraison.
    Parent: update_order
    """
    email = order_data.get("email")
    shipping_info_data = order_data.get("shipping_information")
    
    if not email or not shipping_info_data:
        return jsonify({"errors": {"order": {"code": "missing-fields", "name": "Il manque un ou plusieurs champs qui sont obligatoires"}}}), 422
        
    required_fields = ["country", "address", "postal_code", "city", "province"]
    for field in required_fields:
        if field not in shipping_info_data or not shipping_info_data.get(field):
            return jsonify({"errors": {"order": {"code": "missing-fields", "name": "Il manque un ou plusieurs champs qui sont obligatoires"}}}), 422

    taxes = {"QC": 0.15, "ON": 0.13, "AB": 0.05, "BC": 0.12, "NS": 0.14}
    tax_rate = taxes.get(shipping_info_data["province"], 0.0) 
    
    order.email = email
    order.total_price_tax = order.total_price * (1 + tax_rate)
    
    total_weight = order.product.weight * order.quantity
    if total_weight <= 500:
        order.shipping_price = 500
    elif total_weight < 2000:
        order.shipping_price = 1000
    else:
        order.shipping_price = 2500
        
    order.save()
    
    shipping_info = order.shipping_information.first()
    if not shipping_info:
        ShippingInformation.create(
            order=order,
            country=shipping_info_data["country"],
            address=shipping_info_data["address"],
            postal_code=shipping_info_data["postal_code"],
            city=shipping_info_data["city"],
            province=shipping_info_data["province"]
        )
    else:
        shipping_info.country = shipping_info_data["country"]
        shipping_info.address = shipping_info_data["address"]
        shipping_info.postal_code = shipping_info_data["postal_code"]
        shipping_info.city = shipping_info_data["city"]
        shipping_info.province = shipping_info_data["province"]
        shipping_info.save()
        
    return get_order(order_id)