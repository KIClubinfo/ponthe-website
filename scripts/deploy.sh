#!/usr/bin/env bash
#
# Met la production à jour depuis origin/master et remplace ce qui a changé.
#
#   scripts/deploy.sh              récupère master, sauvegarde la base, reconstruit
#   GIT=non scripts/deploy.sh      reconstruit le code déjà en place
#
# Les images et le frontend sont construits pendant que le site tourne : la
# coupure se réduit au redémarrage de back.
#
set -euo pipefail
cd "$(dirname "$0")/.."

COMPOSE=(docker compose -f docker-compose-prod.yaml)
BRANCH=${BRANCH:-master}

dire() { printf '\n=== %s\n' "$*"; }

attendre_le_site() {
    # gunicorn n'accepte que le nom de domaine configuré : on le lui donne.
    local essai
    for essai in $(seq 1 90); do
        if "${COMPOSE[@]}" exec -T back python -c "
import os, urllib.request
r = urllib.request.Request('http://localhost:8000/api/years/', headers={'Host': os.environ['DOMAIN_NAME']})
urllib.request.urlopen(r, timeout=5)" < /dev/null 2> /dev/null; then
            return 0
        fi
        sleep 2
    done
    return 1
}

if [ "${GIT:-oui}" = oui ]; then
    dire "Récupération de $BRANCH"
    git pull --ff-only origin "$BRANCH"
fi

projet=$("${COMPOSE[@]}" config | awk '/^name:/ {print $2; exit}')

dire "Construction des images (le site continue de tourner)"
"${COMPOSE[@]}" build

# Un simple docker run, sur le pont de Docker : le webinstaller n'a besoin
# d'aucun réseau du projet, seulement d'atteindre le registre npm.
dire "Compilation du frontend (le site continue de tourner)"
docker run --rm -v "${projet}_bundles:/react" "${projet}-webinstaller"

# back applique les migrations à son démarrage : garder la base d'avant.
dire "Sauvegarde de la base"
sauvegarde="avant-deploiement-$(date +%Y%m%d-%H%M%S).sql.gz"
"${COMPOSE[@]}" exec -T db sh -c \
    'pg_dump -U "$POSTGRES_USER" -Z 6 -f "/backups/'"$sauvegarde"'" "$POSTGRES_DB"' < /dev/null
echo "backups/$sauvegarde"

dire "Remplacement des conteneurs (coupure de quelques dizaines de secondes)"
"${COMPOSE[@]}" up -d --no-deps --remove-orphans back celery-worker nginx

dire "Attente du site"
if ! attendre_le_site; then
    echo "Le backend ne répond pas. Journaux : ${COMPOSE[*]} logs --tail 80 back"
    exit 1
fi
# nginx garde l'adresse de l'ancien conteneur back et répond 502 sans cela.
"${COMPOSE[@]}" exec -T nginx nginx -s reload < /dev/null

# nginx sert la copie que collectstatic fait des bundles, et back ne le lance
# qu'à son démarrage. Or compose ne recrée pas back quand son image n'a pas
# changé : un déploiement qui ne touche que le frontend compilait les bundles
# sans jamais les publier.
dire "Publication des fichiers statiques"
"${COMPOSE[@]}" exec -T back python manage.py collectstatic --noinput < /dev/null

dire "État"
"${COMPOSE[@]}" ps
