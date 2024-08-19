# Use an Ubuntu base image
FROM ubuntu:latest

# Install build-essential and any necessary libraries for networking
RUN apt-get update && apt-get install -y \
    build-essential \
    net-tools \
    iputils-ping

# Copy the server source code to the container
COPY server.c /usr/src/myapp/server.c

# Set the working directory
WORKDIR /usr/src/myapp

# Compile the server program
RUN gcc -o server server.c

# Specify the command to run the server program
CMD ["./server"]
