import urllib.request
import json
from .models import db, Product, Order, ShippingInformation, CreditCard, Transaction

def init_db():
    db.connect()

    # Suppression et création des tables
    db.drop_tables([Product, Order, ShippingInformation, CreditCard, Transaction], safe=True)
    db.create_tables([Product, Order, ShippingInformation, CreditCard, Transaction])

    # Récupération des produits
    url = "https://dimensweb.uqac.ca/~jgnault/shops/products/"
    
    try:
        # Requête HTTP
        with urllib.request.urlopen(url) as response:
            content = response.read().decode('utf-8')
            
            content = content.replace('\\u0000', '') # Nettoyage sinon postgre veut pas
            data = json.loads(content)

        # Insertion des données
        for p in data.get('products', []):
            Product.create(
                id = p['id'],
                name = p['name'],
                description = p['description'],
                price = p['price'],
                weight = p['weight'],
                in_stock = p['in_stock'],
                image = p['image']
            )
        
    except Exception as e:
        print(f"Erreur lors de l'initialisation : {e}")
    
    finally:
        db.close()