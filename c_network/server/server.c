#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include <unistd.h>

#define PORT 8082

int main()
{
    int server_fd, new_socket;
    struct sockaddr_in address;
    int opt = 1;
    int addrlen = sizeof(address);
    char buffer[1024] = {0};
    const char *hello = "Hello from server";

    // Debug: Start of the program
    printf("Debug: Starting the server program...\n");

    // Create socket file descriptor
    printf("Debug: Creating socket...\n");
    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0)
    {
        perror("Socket failed");
        exit(EXIT_FAILURE);
    }
    printf("Debug: Socket created successfully.\n");

    // Forcefully attach socket to the port
    printf("Debug: Setting socket options (SO_REUSEADDR | SO_REUSEPORT)...\n");
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &opt, sizeof(opt)))
    {
        perror("Setsockopt failed");
        close(server_fd);
        exit(EXIT_FAILURE);
    }
    printf("Debug: Socket options set successfully.\n");

    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);

    // Bind the socket to the network address
    printf("Debug: Binding socket to port %d...\n", PORT);
    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0)
    {
        perror("Bind failed");
        close(server_fd);
        exit(EXIT_FAILURE);
    }
    printf("Debug: Socket successfully bound to port %d.\n", PORT);

    // Listen for connections
    printf("Debug: Listening for incoming connections...\n");
    if (listen(server_fd, 3) < 0)
    {
        perror("Listen failed");
        close(server_fd);
        exit(EXIT_FAILURE);
    }
    printf("Debug: Server is listening for incoming connections on port %d.\n", PORT);

    // Accept incoming connection
    printf("Debug: Waiting to accept a connection...\n");
    if ((new_socket = accept(server_fd, (struct sockaddr *)&address, (socklen_t *)&addrlen)) < 0)
    {
        perror("Accept failed");
        close(server_fd);
        exit(EXIT_FAILURE);
    }
    printf("Debug: Connection accepted successfully.\n");

    // Read message from client
    printf("Debug: Reading message from client...\n");
    read(new_socket, buffer, 1024);
    printf("Message from client: %s\n", buffer);

    // Send response to client
    printf("Debug: Sending response to client: %s\n", hello);
    send(new_socket, hello, strlen(hello), 0);
    printf("Debug: Response sent to client.\n");

    // Close the connection
    printf("Debug: Closing the connection...\n");
    close(new_socket);
    close(server_fd);
    printf("Debug: Connection closed. Server program terminated.\n");

    return 0;
}
