# On part d'une image existante : nginx (serveur web) sur Alpine (Linux minuscule)
FROM nginx:1.27-alpine

# On copie notre site dans le dossier que nginx sert par défaut
COPY site/ /usr/share/nginx/html/

# Documentation : le conteneur écoute sur le port 80
EXPOSE 80

# Pas de CMD : on hérite de celle de l'image nginx (lance le serveur)
