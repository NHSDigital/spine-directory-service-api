set -e
docker build -t local/cache-service:${BUILD_TAG} -f spine-directory-service/Dockerfile .
