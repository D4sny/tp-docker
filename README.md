# TP d'introduction à Docker

L'objectif du TP est de découvrir et d'apprendre à utiliser Docker, tout en évitant le "C'est de la magie noire".

0. [Connexion et prérequis](#0-connexion-et-prérequis)
1. [Hello world](#1-hello-world)
2. [Lancer une image existante](#2-lancer-une-image-existante)
3. [Écrire un Dockerfile](#3-écrire-un-dockerfile)
4. [Entrer dans un conteneur](#4-entrer-dans-un-conteneur)
5. [Docker Compose](#5-docker-compose)
6. [Bonus : reverse proxy avec Traefik](#6-bonus--reverse-proxy-avec-traefik)
7. [Nettoyage](#7-nettoyage)

Une [antisèche](#antisèche) et une liste des [erreurs fréquentes](#erreurs-fréquentes) sont en fin de document.


## 0. Connexion et prérequis

La première étape est d'installer docker dans votre VM. Pour cela vous pouvez lancer :
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Les services délivrant un service http tourneront sur la VM. Pour ouvrir les pages web dans le navigateur de votre ordinateur, on ouvre un tunnels SSH : `-L 8080:localhost:8080` signifie que le port 8080 de votre ordinateur est redirigé vers le port 8080 de la VM.

Depuis le terminal de votre ordinateur :

```bash
ssh -L 8080:localhost:8080 -L 3001:localhost:3001 -L 8081:localhost:8081 \
    -L 8000:localhost:8000 -L 8090:localhost:8090 \
    -L 8880:localhost:80   -L 8088:localhost:8088 \
    <user>@<adresse_de_la_vm>
```

Cette commande couvre tous les ports du TP. Dans la suite, les adresses `http://localhost:...` sont à ouvrir dans votre navigateur.

Une fois connecté, vous pouver récupérer le tp sur votre VM :

```bash
git clone <URL_DU_REPO> tp-docker
cd tp-docker
docker version
```

La sortie doit contenir deux parties, `Client` et `Server`. Le client est la commande `docker` que vous tapez ; le serveur (le démon `dockerd`) télécharge les images et lance les conteneurs.

Si vous obtenez `permission denied ... docker.sock`, votre utilisateur n'est pas dans le groupe `docker` : `sudo usermod -aG docker $USER`, puis déconnectez-vous et reconnectez-vous.


## 1. Hello world

```bash
docker run hello-world
```

Docker cherche l'image `hello-world` en local. Comme elle n'y est pas, il la télécharge depuis le Docker Hub, crée un conteneur à partir de cette image et le lance. Le programme affiche un message puis se termine, et le conteneur s'arrête avec lui.

```bash
docker images     # l'image est maintenant présente en local
docker ps         # conteneurs en cours d'exécution : aucun
docker ps -a      # tous les conteneurs : hello-world apparaît avec le statut Exited
```

Une **image** est un modèle en lecture seule. Un **conteneur** est une instance créée à partir de ce modèle.

Relancez `docker run hello-world` : l'image n'est pas retéléchargée, mais un second conteneur apparaît dans `docker ps -a`.

### Un shell dans un autre Linux

```bash
docker run -it --rm alpine sh
```

`-it` ouvre une session interactive, `--rm` supprime le conteneur à la sortie. Dans le conteneur :

```sh
cat /etc/os-release   # Alpine Linux
uname -r              # version du noyau
ps aux                # un seul processus : votre shell
exit
```

Lancez `uname -r` sur la VM : la version est la même. Un conteneur n'est pas une machine virtuelle. Il utilise le noyau de la machine hôte et dispose seulement de ses propres fichiers et de ses propres processus, ce qui explique qu'il démarre presque instantanément.


## 2. Lancer une image existante

On lance un serveur web nginx sans rien installer sur la VM :

```bash
docker run -d --name web -p 8080:80 nginx
```

- `-d` lance le conteneur en arrière-plan ;
- `--name web` lui donne un nom (sinon Docker en génère un) ;
- `-p 8080:80` redirige le port 8080 de la VM vers le port 80 du conteneur.

Ouvrez http://localhost:8080 : la page « Welcome to nginx! » s'affiche.

```bash
docker ps              # le conteneur tourne
docker logs -f web     # rechargez la page pour voir les requêtes (Ctrl+C pour quitter)
docker stop web        # la page ne répond plus
docker start web       # elle revient
docker rm -f web       # arrête et supprime le conteneur
```

Sans l'option `-p`, le port 80 du conteneur n'est pas accessible depuis l'extérieur.

**Bonus.** Une application plus complète, toujours en une commande :

```bash
docker run -d --name kuma -p 3001:3001 louislam/uptime-kuma:1
```

http://localhost:3001 affiche Uptime Kuma, un outil de supervision de sites. Supprimez-le ensuite avec `docker rm -f kuma`.


## 3. Écrire un Dockerfile

Un Dockerfile décrit comment construire une image. Celui de [`03-dockerfile`](03-dockerfile/Dockerfile) tient en deux instructions :

```dockerfile
FROM nginx:1.27-alpine
COPY site/ /usr/share/nginx/html/
```

On part de l'image nginx et on y copie notre propre page.

```bash
cd 03-dockerfile
docker build -t mon-site .
docker images
docker run -d --name mon-site -p 8081:80 mon-site
```

`docker build -t mon-site .` construit une image nommée `mon-site` à partir du dossier courant. La page est visible sur http://localhost:8081.

### Exercice

1. Modifiez [`site/index.html`](03-dockerfile/site/index.html), puis rechargez la page. Que se passe-t-il ?
2. Reconstruisez l'image et recréez le conteneur :
   ```bash
   docker build -t mon-site .
   docker rm -f mon-site
   docker run -d --name mon-site -p 8081:80 mon-site
   ```
3. Dans la sortie du build, l'étape `FROM` est marquée `CACHED`. Une image est composée de couches, et Docker ne reconstruit que celles qui ont changé. `docker history mon-site` les affiche.

L'image est figée au moment du build : modifier les fichiers sources ne la change pas.

Laissez `mon-site` tourner pour l'étape suivante.


## 4. Entrer dans un conteneur

`docker exec` lance une commande dans un conteneur déjà démarré. Ici, on ouvre un shell :

```bash
docker exec -it mon-site sh
```

Puis, dans le conteneur :

```sh
cd /usr/share/nginx/html
sed -i 's/Bonjour/Coucou/' index.html
exit
```

Rechargez http://localhost:8081 : le titre a changé. `docker diff mon-site` liste les fichiers modifiés par rapport à l'image.

### Que devient la modification ?

Avant chaque commande, essayez de prévoir le résultat.

```bash
docker restart mon-site
```

Rechargez la page.

```bash
docker rm -f mon-site
docker run -d --name mon-site -p 8081:80 mon-site
```

Rechargez la page.

<details>
<summary>Réponse</summary>

Après `restart`, c'est le même conteneur : la modification est conservée.
Après `rm` puis `run`, c'est un nouveau conteneur créé à partir de l'image : la modification est perdue.

Un conteneur, c'est l'image (en lecture seule) plus une couche modifiable, qui disparaît quand on supprime le conteneur. Comme les conteneurs sont régulièrement supprimés et recréés (mises à jour, redéploiements), on ne modifie jamais un conteneur à la main : on modifie le Dockerfile, ou on utilise un volume.
</details>

### Monter un dossier dans le conteneur

On rend le dossier `site/` de la VM visible dans le conteneur (*bind mount*) :

```bash
docker rm -f mon-site
docker run -d --name mon-site -p 8081:80 \
  -v "$(pwd)/site:/usr/share/nginx/html:ro" \
  mon-site
```

`-v <chemin sur la VM>:<chemin dans le conteneur>` partage le dossier ; `:ro` le rend accessible en lecture seule dans le conteneur.

Modifiez `site/index.html` sur la VM (`nano site/index.html`) et rechargez : le changement est immédiat, sans rebuild. Les fichiers restent sur la VM même si le conteneur est supprimé.

C'est pratique pendant le développement. En production, on reconstruit plutôt l'image.

```bash
docker rm -f mon-site
cd ..
```


## 5. Docker Compose

Une application réelle se compose de plusieurs services : un site, une base de données, un outil d'administration. Docker Compose permet de les décrire dans un seul fichier, [`05-compose/docker-compose.yml`](05-compose/docker-compose.yml), et de les lancer ensemble.

L'application est un livre d'or :

| Service   | Image                                          | Rôle                            |
|-----------|------------------------------------------------|---------------------------------|
| `app`     | construite depuis [`app/`](05-compose/app/)    | le site (Python / Flask)        |
| `db`      | `postgres:17-alpine`                           | la base de données              |
| `adminer` | `adminer`                                      | interface web pour la base      |

```
port 8000 ──> app ─────┐
                       ├──> db ──> volume db-data
port 8090 ──> adminer ─┘
```

`app` et `db` partagent le réseau `backend`, `adminer` et `db` partagent le réseau `admin`. La base n'a aucun port publié.

### Lancer

```bash
cd 05-compose
docker compose up -d --build
docker compose ps
docker compose logs -f app
```

- http://localhost:8000 : le livre d'or ;
- http://localhost:8090 : Adminer. Système `PostgreSQL`, serveur `db`, identifiants dans [`.env`](05-compose/.env).

### Réseaux

Sur un même réseau Docker, les services se joignent par leur nom. C'est pour cela que l'application se connecte à `db:5432` plutôt qu'à une adresse IP.

```bash
docker compose exec app python -c "import socket; print(socket.gethostbyname('db'))"
docker compose exec app python -c "import socket; print(socket.gethostbyname('adminer'))"
```

La première commande renvoie une adresse IP, la seconde échoue : `app` et `adminer` ne sont pas sur le même réseau. Et comme la base n'a pas de port publié, elle n'est pas joignable depuis l'extérieur de la VM.

On peut aussi interroger la base directement :

```bash
docker compose exec db psql -U livredor -c "SELECT * FROM messages;"
```

### Persistance des données

Ajoutez quelques messages, puis, en prévoyant à chaque fois le résultat :

```bash
docker compose down
docker compose up -d
```

Rechargez la page.

```bash
docker compose down -v
docker compose up -d
```

Rechargez la page.

<details>
<summary>Réponse</summary>

`down` supprime les conteneurs et les réseaux, mais les données sont stockées dans le volume `db-data`, qui est conservé.

`down -v` supprime aussi le volume. Au redémarrage, la base est vide, donc Postgres exécute [`db/init.sql`](05-compose/db/init.sql) : seuls les deux messages initiaux réapparaissent.

`docker volume ls` liste les volumes.
</details>

### Modifier l'application

Changez le titre dans [`app/templates/index.html`](05-compose/app/templates/index.html) et rechargez : rien ne change, comme à l'étape 3. Lancez `docker compose up -d --build` : seul le service `app` est reconstruit et recréé.

### Bonnes pratiques présentes dans ce projet

- les mots de passe sont dans `.env` et non dans le code (en temps normal, ce fichier n'est pas versionné) ;
- l'application tourne avec un utilisateur non root (`USER appuser` dans le Dockerfile) ;
- les ressources CPU et mémoire de l'application sont limitées ;
- `depends_on` et `healthcheck` font attendre l'application jusqu'à ce que la base soit prête ;
- `restart: unless-stopped` relance les services après un crash ou un redémarrage de la VM.

```bash
docker compose down
cd ..
```


## 6. Bonus : reverse proxy avec Traefik

Un serveur peut héberger des dizaines de sites. On ne demande pas aux visiteurs d'utiliser un port différent pour chacun : tout le monde arrive sur le port 80, et un **reverse proxy** transmet chaque requête au bon conteneur selon le nom de domaine demandé.

[Traefik](https://traefik.io) découvre les conteneurs en lisant le socket Docker et se configure à partir de leurs labels. Dans [`06-traefik/docker-compose.yml`](06-traefik/docker-compose.yml), les services `site` et `whoami` n'ont aucun port publié, seulement des labels :

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.site.rule=Host(`site.${DOMAIN}`)"
```

```
                          ┌──> site    (image de l'étape 3)
port 80 ──> traefik ──────┤
                          └──> whoami
```

En production, de vrais noms de domaine pointeraient vers le serveur. Ici, on utilise le fait que les navigateurs redirigent tous les noms en `*.localhost` vers votre propre ordinateur, donc dans le tunnel SSH (port 8880 de votre ordinateur vers le port 80 de la VM). Le fichier [`.env`](06-traefik/.env) contient déjà `DOMAIN=localhost`.

```bash
cd 06-traefik
docker compose up -d --build
```

- http://site.localhost:8880 : le site de l'étape 3 ;
- http://whoami.localhost:8880 : le détail de la requête et du conteneur qui a répondu ;
- http://localhost:8880 : erreur 404, aucun service ne correspond à ce nom ;
- http://localhost:8088 : le tableau de bord de Traefik, avec les routes détectées (onglet *HTTP*).

Si `site.localhost` ne fonctionne pas dans votre navigateur (c'est le cas de certaines versions de Safari), utilisez Firefox ou Chrome, ou testez depuis la VM avec `curl -H "Host: whoami.localhost" http://localhost`.

### Répartition de charge

```bash
docker compose up -d --scale whoami=3
```

Rechargez http://whoami.localhost:8880 plusieurs fois : la ligne `Hostname` change. Traefik a détecté les nouveaux conteneurs et répartit les requêtes entre eux. Avec `ports:`, ce serait impossible, car trois conteneurs ne peuvent pas publier le même port de la VM.

### Exercice

Ajoutez un service accessible sur http://hello.localhost:8880, basé sur l'image `nginx`.

<details>
<summary>Solution</summary>

```yaml
  hello:
    image: nginx
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.hello.rule=Host(`hello.${DOMAIN}`)"
      - "traefik.http.routers.hello.entrypoints=web"
```

Puis `docker compose up -d`. Traefik prend en compte le nouveau conteneur sans redémarrer.
</details>

### Sécurité

Donner accès à `/var/run/docker.sock` à un conteneur revient à lui donner le contrôle de Docker, et donc pratiquement les droits root sur la machine. On le monte en lecture seule et on le réserve à des images de confiance. De même, le tableau de bord est ici exposé sans authentification (`--api.insecure=true`), ce qu'on ne fait pas en production. En production, Traefik gère aussi le HTTPS, avec des certificats Let's Encrypt.

```bash
docker compose down
cd ..
```


## 7. Nettoyage

```bash
docker rm -f $(docker ps -aq)       # supprime tous les conteneurs
docker system prune -a --volumes    # supprime les images, réseaux et volumes inutilisés
docker system df                    # affiche l'espace disque utilisé par Docker
```


## Antisèche

| Commande                                                          | Effet                                                    |
| ----------------------------------------------------------------- | -------------------------------------------------------- |
| `docker run [-d] [-it] [--rm] [--name N] [-p H:C] [-v H:C] IMAGE` | crée et lance un conteneur                               |
| `docker ps [-a]`                                                  | liste les conteneurs actifs (ou tous)                    |
| `docker logs [-f] NAME`                                           | affiche la sortie d'un conteneur                         |
| `docker exec -it NAME sh`                                         | ouvre un shell dans un conteneur actif                   |
| `docker stop` / `start` / `restart NAME`                          | arrête, démarre, redémarre                               |
| `docker rm [-f] NAME`                                             | supprime un conteneur                                    |
| `docker images`                                                   | liste les images locales                                 |
| `docker build -t NOM .`                                           | construit une image à partir du Dockerfile du dossier    |
| `docker compose up [-d] [--build]`                                | lance les services (en arrière plan) (en reconstruisant) |
| `docker compose down [-v]`                                        | supprime les services (et les volumes)                   |
| `docker compose logs -f [service]`                                | affiche les logs                                         |

`H:C` : Hôte (votre VM) puis Conteneur.


## Erreurs fréquentes

| Erreur                                       | Solution                                                                                                                                           |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `port is already allocated`                  | un autre conteneur utilise ce port : `docker ps`, puis supprimez-le ou changez le port de gauche dans `-p`                                         |
| `The container name "xxx" is already in use` | un conteneur portant ce nom existe déjà, même arrêté : `docker rm -f xxx`                                                                          |
| La page ne s'affiche pas                     | vérifiez que le conteneur tourne (`docker ps`), ses logs (`docker logs N`), le port, et que la connexion SSH avec les tunnels est toujours ouverte |
| Une modification n'apparaît pas              | l'image a-t-elle été reconstruite (`--build`) ?                                                                                                    |
| `permission denied ... docker.sock`          | voir l'étape 0                                                                                                                                     |
