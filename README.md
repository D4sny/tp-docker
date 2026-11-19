# TP d'introduction à Docker

L'objectif du TP est de découvrir et d'apprendre à utiliser Docker, tout en évitant le "C'est de la magie noire".

0. [Connexion et prérequis](#0-connexion-et-prérequis)
1. [Hello world](#1-hello-world)
2. [Lancer une image existante](#2-lancer-une-image-existante)
3. [Écrire un Dockerfile](#3-écrire-un-dockerfile)
4. [Docker Compose](#4-docker-compose)
5. [Bonus : réparer un compose cassé](#5-bonus--réparer-un-compose-cassé)
6. [Nettoyage](#6-nettoyage)

Une [antisèche](#antisèche) et une liste des [erreurs fréquentes](#erreurs-fréquentes) sont en fin de document. Les réponses aux questions sont dans [`SOLUTIONS.md`](SOLUTIONS.md) : ne l'ouvrez qu'après avoir cherché.

Les questions en *italique* n'attendent pas une commande mais une explication. Prenez le temps d'être certain de comprendre ce qui se passe avant de passer à la suite : c'est là que se trouve l'essentiel du TP.

À tout moment, `docker ps` liste les conteneurs qui tournent et `docker stop NAME` en arrête un.


## 0. Connexion et prérequis

La première étape est d'installer Docker sur votre VM :

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Déconnectez-vous puis reconnectez-vous pour que l'ajout au groupe `docker` soit pris en compte.

Les services web tourneront sur la VM, mais vous voudrez les ouvrir dans le navigateur de votre ordinateur. Pour cela, on ouvre un tunnel SSH : `-L 8080:localhost:8080` redirige le port 8080 de votre ordinateur vers le port 8080 de la VM (`-L` pour *local forwarding*).

Depuis le terminal de votre ordinateur :

```bash
ssh -L 8080:localhost:8080 <user>@<adresse_de_la_vm>
```

Ce tunnel suffit pour les étapes 1 à 3. Les adresses `http://localhost:...` sont à ouvrir dans le navigateur de votre ordinateur.

Une fois connecté, récupérez le TP sur la VM :

```bash
git clone <URL_DU_REPO> tp-docker
cd tp-docker
docker version
```

La sortie contient deux parties, `Client` et `Server`. Le client est la commande `docker` que vous tapez ; le serveur (le démon `dockerd`) télécharge les images et lance les conteneurs.

*Le client et le serveur sont deux programmes distincts. Qu'est-ce que cela permet, à votre avis ?*


## 1. Hello world

```bash
docker run hello-world
```

Docker cherche l'image `hello-world` en local. Comme elle n'y est pas, il la télécharge depuis le Docker Hub, crée un conteneur à partir de cette image et le lance. Le programme affiche un message puis se termine, et le conteneur s'arrête avec lui.

Regardez maintenant ce qu'il reste sur la machine avec `docker images`, `docker ps` et `docker ps -a`. Relancez `docker run hello-world`, puis regardez à nouveau.

*Combien d'images avez-vous ? Combien de conteneurs ? Qu'en déduisez-vous sur la différence entre une image et un conteneur ?*

### Un shell dans un autre Linux

```bash
docker run -it --rm alpine sh
```

`-it` ouvre une session interactive, `--rm` supprime le conteneur à la sortie. Vous êtes maintenant dans le conteneur. Comparez ce que renvoient `cat /etc/os-release`, `uname -r` et `ps aux` dans le conteneur et sur la VM.

*Le conteneur tourne sous Alpine, mais quel noyau utilise-t-il ? Pourquoi ne voit-il qu'un seul processus ?*

*En vous appuyant sur ces observations : pourquoi un conteneur démarre-t-il en une fraction de seconde, alors qu'une machine virtuelle met de longues secondes ? Pourrait-on lancer un conteneur Windows sur cette VM Linux ?*


## 2. Lancer une image existante

On lance un serveur web nginx :

```bash
docker run -d --name web -p 8080:80 nginx
```

- `-d` lance le conteneur en arrière-plan ;
- `--name web` lui donne un nom (sinon Docker en génère un) ;
- `-p 8080:80` redirige le port 8080 de la VM vers le port 80 du conteneur.

Ouvrez http://localhost:8080. La requête de votre navigateur traverse le tunnel SSH jusqu'au port 8080 de la VM, puis Docker la transmet au port 80 du conteneur.

Utilisez `docker logs`, `stop`, `start` et `rm` pour observer et manipuler ce conteneur.

*Essayez de lancer un second nginx avec exactement la même commande, en changeant seulement le nom. Que se passe-t-il, et pourquoi ? Que faut-il changer pour que deux nginx tournent en même temps ? Pourquoi n'y a-t-il aucun conflit sur le port 80 des conteneurs ?*

*Que se passe-t-il si on oublie `-d` ? Et si on oublie `-p` ?*

Supprimez ces conteneurs avant de passer à la suite.


## 3. Écrire un Dockerfile

Le dossier [`03-dockerfile`](03-dockerfile/Dockerfile) contient un Dockerfile de deux instructions :

```dockerfile
FROM nginx:1.27-alpine
COPY site/ /usr/share/nginx/html/
```

On part de l'image nginx et on y copie notre propre page.

```bash
cd 03-dockerfile
docker build -t mon-site .
docker run -d --name mon-site -p 8080:80 mon-site
```

`docker build -t mon-site .` construit une image nommée `mon-site` à partir du dossier courant. La page est visible sur http://localhost:8080.

*Ce Dockerfile ne dit nulle part comment lancer nginx. Comment le conteneur sait-il quoi exécuter ?*

### Modifier l'image

Modifiez [`site/index.html`](03-dockerfile/site/index.html) et rechargez la page (changez un mot ou autre si vous le souhaitez). Faites ensuite le nécessaire pour que votre modification apparaisse.

*Pourquoi la modification n'apparaissait-elle pas tout de suite ? Qu'avez-vous dû refaire, et pourquoi chacune de ces opérations était-elle nécessaire ?*

Lors du second build, l'étape `FROM` est marquée `CACHED` : une image est un empilement de couches, et Docker ne reconstruit que celles qui ont changé. `docker history mon-site` les affiche.

### Entrer dans un conteneur

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

Rechargez la page : le titre a changé. `docker diff mon-site` liste les fichiers modifiés par rapport à l'image.

Avant de taper chacune des commandes suivantes, essayez de prévoir si la modification survivra :

```bash
docker restart mon-site
```

```bash
docker rm -f mon-site
docker run -d --name mon-site -p 8080:80 mon-site
```

*Expliquez les deux résultats. Sachant qu'en production, les conteneurs sont régulièrement supprimés et recréés (mise à jour, redéploiement, panne), que pensez-vous de la modification d'un conteneur à la main ?*

## 4. Docker Compose

Une application réelle se compose de plusieurs services : un site, une base de données, un outil d'administration. Docker Compose permet de les décrire dans un seul fichier et évite de lancer des dizaines de commandes avec des options précises pour les relier. [`04-compose/docker-compose.yml`](04-compose/docker-compose.yml) en contient un exemple : un livre d'or.

| Service   | Image                                          | Rôle                            |
|-----------|------------------------------------------------|---------------------------------|
| `app`     | construite depuis [`app/`](04-compose/app/)    | le site (Python / Flask)        |
| `db`      | `postgres:17-alpine`                           | la base de données              |
| `adminer` | `adminer`                                      | interface web pour la base      |

```
port 8000 ──> app ─────┐
                       ├──> db ──> volume db-data
port 8090 ──> adminer ─┘
```

Lisez le fichier `docker-compose.yml` en entier avant de lancer quoi que ce soit, et faites le parallèle avec les options de `docker run` vues plus haut.

### Lancer

```bash
cd 04-compose
docker compose up -d --build
docker compose ps
docker compose logs -f app
```

L'application écoute sur le port 8000 de la VM, Adminer sur le port 8090. Votre tunnel SSH actuel ne couvre que le port 8080 : ouvrez une nouvelle connexion SSH avec les tunnels nécessaires, puis consultez le livre d'or et Adminer (système `PostgreSQL`, serveur `db`, identifiants dans [`.env`](04-compose/.env)).

### Réseaux

L'application se connecte à la base avec l'adresse `db:5432` (voir `DATABASE_URL` dans le compose), sans jamais connaître son adresse IP.

```bash
docker compose exec app python -c "import socket; print(socket.gethostbyname('db'))"
docker compose exec app python -c "import socket; print(socket.gethostbyname('adminer'))"
```

*Pourquoi la première commande fonctionne-t-elle et pas la seconde ? Regardez la section `networks` du compose.*

*Le service `db` n'a aucune section `ports`. Comment Adminer et l'application y accèdent-ils quand même ? Pourquoi est-ce un choix délibéré ?*

### Persistance des données

Ajoutez quelques messages. Avant chaque commande, essayez de prévoir ce que vous verrez en rechargeant la page :

```bash
docker compose down
docker compose up -d
```

```bash
docker compose down -v
docker compose up -d
```

*Où sont stockés les messages ? Pourquoi survivent-ils au premier `down` mais pas au second ?*

### Modifier l'application

Changez le titre dans [`app/templates/index.html`](04-compose/app/templates/index.html) et faites en sorte qu'il apparaisse sur le site.

*Lors du rebuild, quels services Compose a-t-il recréés ? Pourquoi pas les autres ?*

### Bonnes pratiques présentes dans le projet

- les mots de passe sont dans `.env` et non dans le code (en temps normal, ce fichier n'est pas dans le repo) ;
- l'application tourne avec un utilisateur non root (`USER appuser` dans le Dockerfile) ;
- `depends_on` et `healthcheck` font attendre l'application jusqu'à ce que la base soit prête ;
- `restart: unless-stopped` relance les services après un crash ou un redémarrage de la VM.

*Pour chacune de ces pratiques, quel problème concret évite-t-elle ?*

Arrêtez les conteneurs du compose et revenez à la racine du TP.


## 5. Bonus : réparer un compose cassé

Cette partie n'est pas guidée : aucune commande n'est donnée, et tout ce dont vous avez besoin a été vu plus haut.

Le dossier [`05-compose-casse`](05-compose-casse/) contient un compteur de visites : une application Flask qui stocke son compteur dans Redis, une base de données clé-valeur en mémoire. Celui qui l'a écrit est parti sans la tester, et elle ne fonctionne pas.

Le code Python ([`app/app.py`](05-compose-casse/app/app.py)) est correct. Les problèmes se trouvent dans le Dockerfile, le `docker-compose.yml` et la façon dont ils s'articulent. Vous ne savez pas combien il y en a.

### Objectif

La stack est réparée quand :

- http://localhost:8080 affiche un compteur qui augmente à chaque rechargement ;
- le compteur conserve sa valeur après un `docker compose down` suivi d'un `docker compose up` ;
- Redis n'est pas accessible depuis l'extérieur de la VM.

Pensez à arrêter ce qui occupe déjà le port 8080.

### Méthode

Corrigez une erreur à la fois, et pour chacune, notez le symptôme observé, la façon dont vous l'avez localisée et la cause. Ne modifiez rien au hasard : chaque correction doit s'expliquer.

Les logs, `docker compose ps`, `docker compose exec` et les avertissements affichés par `docker compose` lui-même sont vos meilleurs outils. Quand quelque chose ne répond pas, demandez-vous à quel endroit de la chaîne la requête s'arrête : navigateur, tunnel, VM, conteneur, processus.

<details>
<summary>Indice si vous êtes bloqué sur la page qui ne répond pas</summary>

Depuis l'intérieur du conteneur `app`, l'application répond-elle ? Essayez :
`docker compose exec app python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5000').read())"`
Si elle répond de l'intérieur mais pas de l'extérieur, relisez attentivement les premières lignes des logs.
</details>

<details>
<summary>Indice si tout fonctionne sauf la persistance</summary>

Où Redis écrit-il réellement ses données ? Cherchez la documentation de l'image `redis` sur le Docker Hub, et comparez avec `docker volume ls`.
</details>



## 6. Nettoyage

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
| `docker compose exec SERVICE CMD`                                 | exécute une commande dans un service                     |

`H:C` : Hôte (votre VM) puis Conteneur. Pour `-v`, le chemin côté hôte doit être absolu (`"$(pwd)/dossier"`).


## Erreurs fréquentes

| Erreur                                       | Solution                                                                                                                                           |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `port is already allocated`                  | un autre conteneur utilise ce port : `docker ps`, puis supprimez-le ou changez le port de gauche dans `-p`                                         |
| `The container name "xxx" is already in use` | un conteneur portant ce nom existe déjà, même arrêté : `docker rm -f xxx`                                                                          |
| La page ne s'affiche pas                     | vérifiez que le conteneur tourne (`docker ps`), ses logs (`docker logs NAME`), le port, et que le tunnel SSH vers ce port est ouvert               |
| Une modification n'apparaît pas              | l'image a-t-elle été reconstruite (`--build`) ?                                                                                                    |
| `permission denied ... docker.sock`          | votre utilisateur n'est pas dans le groupe `docker`, ou vous ne vous êtes pas reconnecté depuis (voir l'étape 0)                                    |
