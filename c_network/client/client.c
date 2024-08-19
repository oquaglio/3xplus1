#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <netdb.h> // For getaddrinfo()

#define PORT 8081

int main()
{
    int sock = 0;
    struct sockaddr_in serv_addr;
    struct addrinfo hints, *res;
    const char *hello = "Hello from client";
    char buffer[1024] = {0};

    // Debug: Start of the program
    printf("Debug: Starting the client program...\n");

    // Create socket
    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
        printf("Socket creation error\n");
        return -1;
    }
    printf("Debug: Socket created successfully.\n");

    // Initialize hints
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET; // IPv4
    hints.ai_socktype = SOCK_STREAM;

    // Resolve the hostname to an IP address
    printf("Debug: Resolving hostname 'server'...\n");
    if (getaddrinfo("server", NULL, &hints, &res) != 0)
    {
        printf("Failed to resolve hostname\n");
        return -1;
    }
    printf("Debug: Hostname 'server' resolved successfully.\n");

    // Set up the sockaddr_in structure using the resolved IP
    struct sockaddr_in *addr = (struct sockaddr_in *)res->ai_addr;
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);
    serv_addr.sin_addr = addr->sin_addr; // Copy the resolved IP address

    // Debug: Print the resolved IP address
    char ip_str[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &serv_addr.sin_addr, ip_str, sizeof(ip_str));
    printf("Debug: Resolved IP address of 'server' is: %s\n", ip_str);

    freeaddrinfo(res); // Free the address info structure

    // Connect to the server
    printf("Debug: Attempting to connect to the server at %s on port %d...\n", ip_str, PORT);
    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0)
    {
        printf("Connection failed\n");
        return -1;
    }
    printf("Debug: Connected to the server successfully.\n");

    // Send message to server
    printf("Debug: Sending message to the server: %s\n", hello);
    send(sock, hello, strlen(hello), 0);
    printf("Debug: Message sent to the server.\n");

    // Read server response
    printf("Debug: Waiting for response from server...\n");
    read(sock, buffer, 1024);
    printf("Debug: Received message from server: %s\n", buffer);

    // Close the socket
    printf("Debug: Closing the socket.\n");
    close(sock);
    printf("Debug: Socket closed.\n");

    return 0;
}
