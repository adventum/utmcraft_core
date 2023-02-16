set -o allexport &&
source .env &&
set +o allexport &&
chmod +x postgres/entrypoint.sh &&
docker-compose up -d --build;