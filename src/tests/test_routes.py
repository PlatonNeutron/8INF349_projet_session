import json
import pytest
from unittest.mock import patch
from inf349.models import Product, Order

class TestProductsRoutes:
    def test_get_products_success(self, client):
        """Test la récupération de la liste des produits (GET /)"""
        response = client.get('/')
        assert response.status_code == 200
        data = response.get_json()
        assert "products" in data
        assert isinstance(data["products"], list)

class TestOrderCreationRoutes:
    def test_post_order_success(self, client):
        """Test la création d'une commande valide"""
        payload = {"product": {"id": 1, "quantity": 2}}
        response = client.post('/order', json=payload)
        assert response.status_code == 302
        assert "Location" in response.headers
        assert "/order/" in response.headers["Location"]

    def test_post_order_missing_product(self, client):
        """Test la création avec un objet product manquant"""
        response = client.post('/order', json={})
        assert response.status_code == 422
        data = response.get_json()
        assert data["errors"]["product"]["code"] == "missing-fields"

    def test_post_order_invalid_quantity(self, client):
        """Test la création avec une quantité inférieure à 1"""
        payload = {"product": {"id": 1, "quantity": 0}}
        response = client.post('/order', json=payload)
        assert response.status_code == 422
        data = response.get_json()
        assert data["errors"]["product"]["code"] == "missing-fields"

    def test_post_order_out_of_stock(self, client):
        """Test la création avec un produit qui n'est pas en inventaire"""
        payload = {"product": {"id": 2, "quantity": 1}} # Assumant que l'id 2 a in_stock=False
        response = client.post('/order', json=payload)
        assert response.status_code == 422
        data = response.get_json()
        assert data["errors"]["product"]["code"] == "out-of-inventory"

class TestOrderRetrievalRoutes:
    def test_get_order_success(self, client):
        """Test la récupération d'une commande existante"""
        # Création d'une commande au préalable
        post_resp = client.post('/order', json={"product": {"id": 1, "quantity": 1}})
        location = post_resp.headers["Location"]
        
        get_resp = client.get(location)
        assert get_resp.status_code == 200
        data = get_resp.get_json()
        assert "order" in data
        assert data["order"]["product"]["id"] == 1

    def test_get_order_not_found(self, client):
        """Test la récupération d'une commande inexistante"""
        response = client.get('/order/9999')
        assert response.status_code == 404

class TestOrderUpdateShippingRoutes:
    def test_put_order_shipping_success(self, client):
        """Test l'ajout des informations d'expédition"""
        post_resp = client.post('/order', json={"product": {"id": 1, "quantity": 1}})
        location = post_resp.headers["Location"]

        payload = {
            "order": {
                "email": "test@uqac.ca",
                "shipping_information": {
                    "country": "Canada",
                    "address": "201, rue Président-Kennedy",
                    "postal_code": "G7X 3Y7",
                    "city": "Chicoutimi",
                    "province": "QC"
                }
            }
        }
        put_resp = client.put(location, json=payload)
        assert put_resp.status_code == 200
        data = put_resp.get_json()
        assert data["order"]["email"] == "test@uqac.ca"

    def test_put_order_shipping_missing_fields(self, client):
        """Test l'ajout d'informations d'expédition incomplètes"""
        post_resp = client.post('/order', json={"product": {"id": 1, "quantity": 1}})
        location = post_resp.headers["Location"]

        payload = {
            "order": {
                "shipping_information": {
                    "country": "Canada",
                    "province": "QC"
                }
            }
        }
        put_resp = client.put(location, json=payload)
        assert put_resp.status_code == 422
        assert put_resp.get_json()["errors"]["order"]["code"] == "missing-fields"

class TestOrderPaymentRoutes:
    def test_put_order_payment_without_shipping(self, client):
        """Test le paiement avant d'avoir mis les informations de livraison"""
        post_resp = client.post('/order', json={"product": {"id": 1, "quantity": 1}})
        location = post_resp.headers["Location"]

        payload = {
            "credit_card": {
                "name": "John Doe", "number": "4242 4242 4242 4242",
                "expiration_year": 2026, "cvv": "123", "expiration_month": 9
            }
        }
        resp = client.put(location, json=payload)
        assert resp.status_code == 422
        assert resp.get_json()["errors"]["order"]["code"] == "missing-fields"

    @patch('urllib.request.urlopen')
    def test_put_order_payment_success(self, mock_urlopen, client):
        """Test d'un paiement valide avec mock de l'API distante"""
        # 1. Créer la commande
        post_resp = client.post('/order', json={"product": {"id": 1, "quantity": 1}})
        location = post_resp.headers["Location"]

        # 2. Ajouter les infos de livraison
        client.put(location, json={
            "order": {
                "email": "test@uqac.ca",
                "shipping_information": {
                    "country": "Canada", "address": "123 Rue",
                    "postal_code": "G1G1G1", "city": "Ville", "province": "QC"
                }
            }
        })

        # Mock de la réponse HTTP de l'API externe
        mock_response = mock_urlopen.return_value.__enter__.return_value
        mock_response.read.return_value = json.dumps({
            "credit_card": {
                "name": "John Doe", "first_digits": "4242", "last_digits": "4242",
                "expiration_year": 2026, "expiration_month": 9
            },
            "transaction": {
                "id": "mocked_transaction_id", "success": True, "amount_charged": 1000
            }
        }).encode('utf-8')
        mock_response.getcode.return_value = 200

        # 3. Payer
        payload = {
            "credit_card": {
                "name": "John Doe", "number": "4242 4242 4242 4242",
                "expiration_year": 2026, "cvv": "123", "expiration_month": 9
            }
        }
        resp = client.put(location, json=payload)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["order"]["paid"] == True
        assert data["order"]["transaction"]["id"] == "mocked_transaction_id"