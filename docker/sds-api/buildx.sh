set -e
DOCKER_BUILDKIT=1 docker build \
-t local/spine-directory-service:${BUILD_TAG} \
-f spine-directory-service/sds/Dockerfile_local .