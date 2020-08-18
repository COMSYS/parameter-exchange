#!/usr/bin/env bash

# Colors
ncolors=$(tput colors)
big="$(tput bold)"
normal="$(tput sgr0)"

CONTAINER_NAME="pppe_full"
IMAGE_NAME="erikb/pppe_full"
CURRENT_DIR=$(python3 -c "import os; print(os.path.realpath('$1'))")
REPO_BASE_DIR="$(dirname "$CURRENT_DIR")"
HOSTPATH=$REPO_BASE_DIR
echo -e "Using host path: ${big}${REPO_BASE_DIR}${normal}"
DOCKERPATH="/master"

if [[ "$(docker images -q $IMAGE_NAME 2> /dev/null)" == "" ]]; then
	# Check if Image exists and build it if not
    echo "Building image..."
    # Builder image from Dockerfile
    docker build -t $IMAGE_NAME .
fi
echo "Starting container..."
# Start container based on Dockerfile
# Expose internal ports 80, 443, 5000 and 5001 and mount root directory of repo at /master
docker run --name $CONTAINER_NAME -e HOST_IP="$(ifconfig en0 | awk '/ *inet /{print $2}')" -p 80:8080 -p 443:40443 -p 5000:5000 -p 5001:5001 -v $HOSTPATH:$DOCKERPATH -ti $IMAGE_NAME
