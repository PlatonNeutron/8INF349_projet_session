from flask import jsonify
from . import app
from .models import Product

@app.route('/', methods=['GET'])
def get_products():
    """
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