# Django Backend API avec Docker et Kubernetes

Ce projet met en œuvre une API backend basée sur Django et Django REST framework, conteneurisée avec Docker et déployable sur Kubernetes. L'application fournit des endpoints pour lire et écrire des données dans une base de données SQLite.

## Table des matières
- [Structure du projet](#structure-du-projet)
- [Prérequis](#prérequis)
- [Exécution locale avec Docker](#exécution-locale-avec-docker)
- [Exécution locale avec Docker Compose](#exécution-locale-avec-docker-compose)
- [Déploiement sur Kubernetes](#déploiement-sur-kubernetes)
- [Utilisation de l'API](#utilisation-de-lapi)
- [Résolution des problèmes](#résolution-des-problèmes)

## Structure du projet

```
django-backend-api/
├── Dockerfile               # Instructions pour construire l'image Docker
├── .dockerignore            # Fichiers à ignorer lors de la construction de l'image
├── docker-compose.yaml      # Configuration Docker Compose
├── requirements.txt         # Dépendances Python
├── manage.py                # Script de gestion Django
├── README.md                # Ce fichier
├── backend/                 # Projet Django principal
│   ├── __init__.py
│   ├── settings.py          # Configuration Django
│   ├── urls.py              # URLs du projet
│   ├── asgi.py
│   └── wsgi.py
├── api/                     # Application API
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py            # Modèle Item
│   ├── serializers.py       # Sérialiseurs REST
│   ├── tests.py
│   ├── urls.py              # URLs de l'API
│   └── views.py             # Endpoints read/write
└── kubernetes/              # Manifestes Kubernetes
    ├── backend-configmap.yaml
    ├── backend-deployment.yaml
    ├── backend-service.yaml
    └── sqlite-pvc.yaml
```

## Prérequis

- Docker & Docker Compose
- Kubernetes (minikube pour le développement local)
- kubectl

## Exécution locale avec Docker

### Option 1: Récupérer l'image depuis Docker Hub

L'image est déjà disponible sur Docker Hub et peut être utilisée directement:

```bash
# Récupérer l'image depuis Docker Hub
docker pull dastou/backend:v1.0.0

# Exécuter le conteneur
docker run -p 8000:8000 dastou/backend:v1.0.0
```

### Option 2: Construction locale de l'image Docker

Si vous préférez construire l'image vous-même:

```bash
# Construction de l'image
docker build -t dastou/backend:v1.0.0 .

# Exécution du conteneur
docker run -p 8000:8000 dastou/backend:v1.0.0
```

### Publication de votre propre image sur Docker Hub

Si vous souhaitez publier votre propre version de l'image:

```bash
# Construire avec votre identifiant Docker Hub
docker build -t votre-id/backend:v1.0.0 .

# Se connecter à Docker Hub
docker login

# Publier l'image
docker push votre-id/backend:v1.0.0
```

L'API sera accessible à l'adresse http://localhost:8000/api/items/

## Exécution locale avec Docker Compose

Docker Compose simplifie la gestion des conteneurs et des volumes.

### 1. Démarrage des services

```bash
docker-compose up -d
```

### 2. Accès aux logs

```bash
docker-compose logs -f
```

### 3. Arrêt des services

```bash
docker-compose down
```

L'API sera accessible à l'adresse http://localhost:8000/api/items/

## Déploiement sur Kubernetes

### Architecture Kubernetes

Le déploiement sur Kubernetes comprend plusieurs composants:

1. **ConfigMap** - Stocke les variables d'environnement et configurations
2. **PersistentVolumeClaim (PVC)** - Assure la persistance des données
3. **Deployment** - Gère les pods Django et assure leur disponibilité
4. **Service** - Expose l'application à l'extérieur du cluster

### Détail des fichiers manifestes

#### backend-configmap.yaml
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: backend-config
data:
  DEBUG: "True"
```
Ce fichier définit les variables d'environnement pour l'application Django.

#### sqlite-pvc.yaml
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: sqlite-data-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```
Ce manifeste demande un volume persistant de 1Go pour stocker la base de données SQLite.

#### backend-deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: django-backend
  labels:
    app: django-backend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: django-backend
  template:
    metadata:
      labels:
        app: django-backend
    spec:
      containers:
      - name: backend
        image: dastou/backend:v1.0.0
        ports:
        - containerPort: 8000
        command: ["sh", "-c"]
        args:
        - |
          python manage.py migrate
          python manage.py runserver 0.0.0.0:8000
        env:
        - name: DEBUG
          valueFrom:
            configMapKeyRef:
              name: backend-config
              key: DEBUG
        - name: ALLOWED_HOSTS
          value: "*"
        volumeMounts:
        - name: sqlite-data
          mountPath: /app/data
      volumes:
      - name: sqlite-data
        persistentVolumeClaim:
          claimName: sqlite-data-pvc
```
Ce fichier définit le déploiement du backend Django, configurant:
- L'image Docker à utiliser
- Les commandes à exécuter au démarrage (migrations et lancement du serveur)
- Les variables d'environnement (depuis le ConfigMap)
- Le montage du volume persistant

#### backend-service.yaml
```yaml
apiVersion: v1
kind: Service
metadata:
  name: django-backend
spec:
  selector:
    app: django-backend
  ports:
  - port: 80
    targetPort: 8000
  type: NodePort
```
Ce fichier expose le service sur un port dynamique (NodePort) pour y accéder depuis l'extérieur du cluster.

### Instructions de déploiement

**Note importante**: L'image `dastou/backend:v1.0.0` est référencée dans les fichiers manifestes Kubernetes. Cette image est disponible publiquement sur Docker Hub, mais si vous souhaitez utiliser votre propre image:

1. Construisez et publiez votre image avec votre identifiant Docker Hub:
   ```bash
   docker build -t votre-id/backend:v1.0.0 .
   docker push votre-id/backend:v1.0.0
   ```

2. Modifiez les fichiers de déploiement Kubernetes pour référencer votre image:
   ```bash
   # Modifiez l'image dans backend-deployment.yaml puis appliquez
   sed -i 's|dastou/backend:v1.0.0|votre-id/backend:v1.0.0|g' kubernetes/backend-deployment.yaml
   kubectl apply -f kubernetes/backend-deployment.yaml
   ```

#### 1. Démarrage du cluster Kubernetes local

```bash
# Démarrage avec le pilote Docker (recommandé pour Windows)
minikube start --driver=docker

# Alternative avec plus de ressources si nécessaire
minikube start --driver=docker --memory=4096 --cpus=2
```

#### 2. Vérifier que le cluster est opérationnel

```bash
kubectl cluster-info
minikube status
```

#### 3. Application des manifestes Kubernetes

```bash
# Créer le volume persistant en premier
kubectl apply -f kubernetes/sqlite-pvc.yaml

# Créer le ConfigMap
kubectl apply -f kubernetes/backend-configmap.yaml

# Déployer l'application
kubectl apply -f kubernetes/backend-deployment.yaml

# Créer le service
kubectl apply -f kubernetes/backend-service.yaml

# Ou appliquer tous les fichiers d'un coup
kubectl apply -f kubernetes/
```

#### 4. Vérification du déploiement

```bash
# Vérifier que le PVC est créé et attaché
kubectl get pvc

# Vérifier que les pods sont en cours d'exécution
kubectl get pods

# Vérifier l'état du déploiement
kubectl get deployment

# Vérifier que le service est disponible
kubectl get services

# Vérifier les logs du pod
kubectl logs deployment/django-backend
```

#### 5. Accès au service

```bash
# Obtenir l'URL du service et l'ouvrir automatiquement dans un navigateur
minikube service django-backend

# Obtenir uniquement l'URL sans ouvrir le navigateur
minikube service django-backend --url
```

**Important pour les utilisateurs Windows avec Docker**: Gardez le terminal ouvert lorsque vous utilisez `minikube service`, car la redirection de port s'arrête si vous fermez le terminal.

#### 6. Alternative avec port-forwarding

```bash
# Rediriger le port local 8000 vers le port 80 du service
kubectl port-forward service/django-backend 8000:80
```

Vous pourrez alors accéder à l'application sur http://localhost:8000.

#### 7. Nettoyage des ressources

```bash
# Supprimer toutes les ressources créées
kubectl delete -f kubernetes/

# Ou supprimer les ressources individuellement
kubectl delete service django-backend
kubectl delete deployment django-backend
kubectl delete configmap backend-config
kubectl delete pvc sqlite-data-pvc

# Arrêter minikube si vous avez terminé
minikube stop
```

## Utilisation de l'API

L'API fournit deux endpoints principaux:

### Endpoint de lecture (GET)

```
GET /api/items/
```

Renvoie la liste de tous les items stockés dans la base de données.

### Endpoint d'écriture (POST)

```
POST /api/items/
```

Ajoute un nouvel item dans la base de données.

Exemple de requête POST:
```bash
curl -X POST http://localhost:8000/api/items/ \
     -H "Content-Type: application/json" \
     -d '{"name": "Mon Item", "description": "Description de mon item"}'
```

## Structure des données

Le modèle `Item` possède les champs suivants:
- `name`: Nom de l'item (chaîne de caractères)
- `description`: Description de l'item (texte)
- `created_at`: Date et heure de création (automatique)

## Résolution des problèmes

### Problèmes de migrations

Si vous rencontrez des erreurs concernant les migrations ou les tables manquantes:

```bash
# Vérifier les logs du pod
kubectl logs <nom-du-pod>

# Exécuter les migrations manuellement
kubectl exec -it <nom-du-pod> -- python manage.py migrate
```

### Problèmes d'accès au service

Si vous ne pouvez pas accéder à l'API via minikube:

```bash
# Vérifier l'URL du service
minikube service django-backend --url

# Utiliser le port-forwarding comme alternative
kubectl port-forward service/django-backend 8000:80
```

### Problèmes de volume persistant

Si le volume persistant n'est pas correctement attaché:

```bash
# Vérifier l'état du PVC
kubectl get pvc

# Décrire le PVC pour plus de détails
kubectl describe pvc sqlite-data-pvc
```

### Erreur "OperationalError at /api/"

Cette erreur peut survenir si les migrations n'ont pas été correctement appliquées ou si la base de données n'est pas accessible. Solution:

```bash
# Redéployer l'application
kubectl delete deployment django-backend
kubectl apply -f kubernetes/backend-deployment.yaml
```

### Problèmes avec Docker Hub

Si vous avez des problèmes pour récupérer l'image depuis Docker Hub:

```bash
# Vérifier si l'image est accessible
docker pull dastou/backend:v1.0.0

# Si l'image n'est pas disponible, construisez-la localement
docker build -t dastou/backend:v1.0.0 .
```

## Technologies utilisées

- Django 4.2
- Django REST Framework
- SQLite
- Docker & Docker Compose
- Kubernetes (minikube)