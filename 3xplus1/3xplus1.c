#include <limits.h>
#include <stdio.h>
#include <time.h>
#include <math.h>
#include <stdlib.h>

/*
 * Function:  main
 * --------------------
 * Computes Collatz conjecture (3x + 1) for specified range of numbers
 *
 * Prints each time a new max is found
 *
 */
int main(int argc, char *argv[])
{

    unsigned long long num;
    unsigned long long start = 1;
    unsigned long long end = ULLONG_MAX;
    unsigned long long max_height = 0;

    if (argc > 1)
    {
        start = strtoull(argv[1], NULL, 10);
    }
    else
    {
        start = 1; // Default start if no argument is provided
    }

    clock_t t = clock(); // CPU time
    struct timespec t_start, t_now;
    clock_gettime(CLOCK_MONOTONIC, &t_start);

    printf("\nnumber height steps cpu_time wall_time\n");

    for (num = start; num <= end; num = num + 1)
    {
        unsigned long long steps = 0;
        unsigned long long height = 0;
        unsigned long long next_num = 0;
        unsigned long long curr_num = num;

        // output only every 1000th num to improve performance
        if (num % 1000000 == 0)
        {
            printf("\r%llu", num);
            fflush(stdout);
        }

        // iterate until we get back to 1 (assuming we ever will)
        do
        {

            if (curr_num > height)
                height = curr_num;

            if (curr_num % 2 == 0)
                curr_num = curr_num / 2;
            else
            {
                // check for potential overflow before calculation
                if (curr_num > (ULLONG_MAX - 1) / 3)
                {
                    printf("\nOverflow at %llu", curr_num);
                    return 0;
                }
                curr_num = 3 * curr_num + 1;
            }

            steps++;

        } while (curr_num > 1);

        if (height > max_height)
        {
            max_height = height;
            clock_t t2 = clock();
            clock_gettime(CLOCK_MONOTONIC, &t_now);
            // num, height, steps, time taken (s)
            printf("\r%llu %llu %llu %.1f %.f\n", num, height, steps, (double)(t2 - t) / CLOCKS_PER_SEC, (t_now.tv_sec - t_start.tv_sec) + 1e-9 * (t_now.tv_nsec - t_start.tv_nsec));
            fflush(stdout);
        }

        // prevent infinite  loop (wrap back to 0)
        if (num == ULLONG_MAX)
            break;
    }

    // t = clock() - t;
    // double time_taken = ((double)t)/CLOCKS_PER_SEC; // in seconds
    // printf("\n\nTook %fs second(s)\n\n", time_taken);

    return 0;
}