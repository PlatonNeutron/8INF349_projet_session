# Projet de Session - 8INF349

Projet de session dans le cadre du cours 8INF349 à l'UQAC !

## Installation

### 1. Préparation de l'environnement

Créez l'environnement virtuel:

```bash
cd src
python -m venv venv
```

### 2. Activation de l'environnement

* **Windows :**
```bash
venv\Scripts\activate
```

* **macOS / Linux :**
```bash
source venv/bin/activate
```

### 3. Installation des dépendances
```bash
pip install -r requirements.txt
```

---

## Utilisation de l'application

### Initialisation de la base de données

* **Linux / macOS :**
```bash
FLASK_DEBUG=True FLASK_APP=inf349 flask init-db
```

* **Windows :**
Vous pouvez utiliser le script fourni pour configurer les variables d'environnement :
```bash
setvars
flask init-db
```

> `setvars` est un petit script qui set les variables d'environnments `FLASK_DEBUG` et `FLASK_APP` pour windows, c'est plus simple.

### Démarrage du serveur
* **Linux / macOS :**
```bash
FLASK_DEBUG=True FLASK_APP=inf349 flask run
```

* **Windows :**
```bash
setvars
flask run
```

---

## Tests
```bash
python -m pytest
```