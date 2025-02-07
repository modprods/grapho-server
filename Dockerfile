# Use an official Node runtime as a parent image
FROM debian:bullseye

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the rest of the application code
COPY . .

# Install the dependencies
RUN apt-get update -y \
    && apt-get upgrade -y \
    && apt-get -y install build-essential \
        zlib1g-dev \
        libncurses5-dev \
        libgdbm-dev \ 
        libnss3-dev \
        libssl-dev \
        libreadline-dev \
        libffi-dev \
        libsqlite3-dev \
        libbz2-dev \
        wget \
        curl \
        git \
        procps \
        vim \
        ncurses-term \
        # openjdk-11-jdk \
        htop \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get purge -y imagemagick imagemagick-6-common

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

SHELL ["/bin/bash", "-c"]

# Setup environment
RUN uv sync

# this could be cleaned up but resolving pipenv lockfile conflicts became a bottleneck
# TODO create pipenv.lock from stable env install when
#RUN pipenv run pip install -r requirements.txt

# Expose the port the app runs on
EXPOSE 5042

EXPOSE 80

# Define the command to run the app
# CMD ["pipenv", "run", "python", "api.py"]
# CMD ["uv","run","api.py"]
CMD ["bash"]