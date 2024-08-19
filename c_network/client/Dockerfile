# Use an Ubuntu base image
FROM ubuntu:latest

# Install build-essential and any necessary libraries for networking
RUN apt-get update && apt-get install -y \
    build-essential \
    net-tools \
    iputils-ping

# Copy the client source code to the container
COPY client.c /usr/src/myapp/client.c

# Set the working directory
WORKDIR /usr/src/myapp

# Compile the client program
RUN gcc -o client client.c

# Specify the command to run the client program
CMD ["./client"]
