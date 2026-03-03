from flask import Flask
from .models import db # Importation de la db

# Initialisation de l'application Flask
app = Flask(__name__)

@app.before_request
def before_request():
    """Ouvre la connexion à la base de données avant chaque requête HTTP."""
    if db.is_closed():
        db.connect()

@app.teardown_request
def teardown_request(exc):
    """Ferme la connexion à la base de données après chaque requête HTTP."""
    if not db.is_closed():
        db.close()

# L'importation des routes et des commandes doit se faire après l'initialisation de l'application et de la base de données pour éviter les problèmes d'importation circulaire.
from . import routes
from . import commands

# Ajout des commandes personnalisées
app.cli.command("init-db")(commands.init_db)