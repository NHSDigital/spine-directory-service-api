set -e
docker build -t local/spine-directory-service:${BUILD_TAG} -f spine-directory-service/spine-directory-service/Dockerfile .