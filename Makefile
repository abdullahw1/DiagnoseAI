DOCKER_REGISTRY := "defendaitech.azurecr.io"
DOCKER_REPO := "defendai"
DOCKER_IMAGE := "diagnoseai"
IMAGE_TAG := "0.08"

docker:
	docker build . -t diagnoseai:dev

publish:
	docker tag diagnoseai:dev ${DOCKER_REGISTRY}/${DOCKER_REPO}:${DOCKER_IMAGE}.${IMAGE_TAG}
	docker push ${DOCKER_REGISTRY}/${DOCKER_REPO}:${DOCKER_IMAGE}.${IMAGE_TAG}