import json

def test_get_products(client):
    """
    Test fonctionnel pour la route GET /
    Vérifie le code de statut, le Content-Type et la structure de la réponse.
    """

    response = client.get('/')
    
    # Vérification du code HTTP
    assert response.status_code == 200
    
    # Vérification du Content-Type
    assert response.headers['Content-Type'] == 'application/json'
    
    # Vérification du contenu JSON
    data = json.loads(response.data)

    assert "products" in data
    assert isinstance(data["products"], list)