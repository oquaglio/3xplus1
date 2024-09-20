#!/bin/bash

# Sieve of Eratosthenes in Bash
# by Otto Quaglio 20/09/2024

DEFAULT_LIMIT=1000
DEFAULT_SECONDS=5

print_primes=0
quiet=0
oneshot=0
limit=$DEFAULT_LIMIT
seconds=$DEFAULT_SECONDS

print_usage() {
    echo "Usage: $0 [-l limit] [-s seconds] [-1] [-p] [-q] [-h]"
    echo "  -l limit    Specify the upper limit for prime calculation (default: 1000)"
    echo "  -s seconds  Specify the duration to run the sieve (default: 5 seconds)"
    echo "  -1          Run the sieve only once (oneshot mode)"
    echo "  -p          Print the primes as they are found"
    echo "  -q          Suppress banners and extraneous output"
    echo "  -h          Print this help message and exit"
}

while getopts ":l:s:1pqh" opt; do
    case $opt in
        l) limit=$OPTARG;;
        s) seconds=$OPTARG;;
        1) oneshot=1;;
        p) print_primes=1;;
        q) quiet=1;;
        h) print_usage; exit 0;;
        \?) print_usage; exit 1;;
    esac
done

if [[ $quiet -eq 0 ]]; then
    echo "------------------------------------"
    echo "Sieve of Eratosthenes by Otto Q 2024"
    echo "v1.00"
    echo "------------------------------------"
    echo "Solving primes up to $limit"
    echo "------------------------------------"
fi

sieve() {
    local limit=$1
    declare -a sieve
    local count=1  # Start count considering 2 is a prime

    # Initialize sieve array
    for ((i = 3; i <= limit; i += 2)); do
        sieve[$i]=0
    done

    # Apply sieve algorithm
    for ((i = 3; i*i <= limit; i += 2)); do
        if [[ ${sieve[$i]} -eq 0 ]]; then
            for ((j = i*i; j <= limit; j += 2*i)); do
                sieve[$j]=1
            done
        fi
    done

    # Output and count primes
    if [[ $print_primes -eq 1 ]]; then
        echo -n "2 "
    fi
    for ((i = 3; i <= limit; i += 2)); do
        if [[ ${sieve[$i]} -eq 0 ]]; then
            count=$((count + 1))
            if [[ $print_primes -eq 1 ]]; then
                echo -n "$i "
            fi
        fi
    done
    if [[ $print_primes -eq 1 ]]; then
        echo
    fi

    echo "Count of primes found: $count"
}

start_time=$(date +%s.%N)
sieve $limit
end_time=$(date +%s.%N)
elapsed_time=$(echo "$end_time - $start_time" | bc)

if [[ $quiet -eq 0 ]]; then
    echo "Total time taken: $elapsed_time seconds"
fi
