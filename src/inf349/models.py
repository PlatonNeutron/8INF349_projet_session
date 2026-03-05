from peewee import *

db = SqliteDatabase('data.db')

class BaseModel(Model):
    class Meta:
        database = db

class Product(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField()
    description = TextField()
    price = FloatField()
    weight = IntegerField() 
    in_stock = BooleanField()
    image = CharField()

class Order(BaseModel):
    product = ForeignKeyField(Product, backref='orders')
    quantity = IntegerField()
    email = CharField(null=True)
    
    # Champs calculés
    # TODO: les calculer dynamiquement ???
    shipping_price = IntegerField(null=True) # Prix d'expédition calculé selon le poids
    total_price = FloatField(null=True) # Prix produit * quantité
    total_price_tax = FloatField(null=True) # total_price * taxe de la province
    paid = BooleanField(default=False)

class ShippingInformation(BaseModel):
    order = ForeignKeyField(Order, backref='shipping_information', unique=True)
    country = CharField()
    address = CharField()
    postal_code = CharField()
    city = CharField()
    province = CharField() # QC, ON, AB, BC ou NS

class CreditCard(BaseModel):
    order = ForeignKeyField(Order, backref='credit_card', unique=True)
    name = CharField()
    first_digits = CharField()
    last_digits = CharField()
    expiration_year = IntegerField() 
    expiration_month = IntegerField()

class Transaction(BaseModel):
    order = ForeignKeyField(Order, backref='transaction', unique=True)
    transaction_id = CharField()
    success = BooleanField()
    amount_charged = FloatField()