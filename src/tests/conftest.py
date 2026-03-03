import pytest
from inf349 import app
from inf349.models import db, Product

@pytest.fixture
def client():
    """Configure un client de test Flask."""
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client