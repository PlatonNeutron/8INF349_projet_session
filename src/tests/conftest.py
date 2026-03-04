import os
import pytest
from inf349 import app
from inf349.models import db, Product, Order, ShippingInformation, CreditCard, Transaction

TEST_DB = 'test_data.db'

@pytest.fixture(autouse=True)
def setup_db():
    """Configure une base de données isolée et déterministe pour les tests."""
    # Redirige Peewee vers une base de données de test
    db.init(TEST_DB)
    
    # S'assure que la connexion est fermée avant de la rouvrir
    if not db.is_closed():
        db.close()
    
    db.connect()
    
    # Création des tables de zéro
    tables = [Product, Order, ShippingInformation, CreditCard, Transaction]
    db.drop_tables(tables, safe=True)
    db.create_tables(tables)
    
    # --- Insertion des données mock pour les tests ---
    Product.create(
        id=1, name="Produit en stock", description="Super produit", 
        price=10.0, weight=100, in_stock=True, image="1.jpg"
    )
    Product.create(
        id=2, name="Produit hors stock", description="C'est non", 
        price=15.0, weight=200, in_stock=False, image="2.jpg"
    )
    
    # Fermeture de la connexion
    db.close()
    
    yield
    
    # Suppresion de la db après les tests
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

@pytest.fixture
def client():
    """Configure un client de test Flask."""
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client