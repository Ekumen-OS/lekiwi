#!/bin/bash

export UID=$(id -u)
export GID=$(id -g)

docker build -t lekiwi-dora-dev-container -f .devcontainer/lekiwi-dev/Dockerfile \
    --build-arg UID=$UID \
    --build-arg GID=$GID \
    .
