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
    unsigned long long max_height_for_all = 0;

    if (argc > 1)
    {
        start = strtoull(argv[1], NULL, 10);
    }

    printf("\nnumber max_height steps cpu_time wall_time\n");

    // start the clock
    clock_t t = clock(); // CPU time
    struct timespec t_start, t_now;
    clock_gettime(CLOCK_MONOTONIC, &t_start);

    for (num = start; num <= end; num = num + 1)
    {
        unsigned long long steps = 0;
        unsigned long long curr_height = num;
        unsigned long long max_height_for_num = curr_height;

        // output only every 1000th num to improve performance
        if (num % 1000000 == 0)
        {
            printf("\r%llu", num);
            fflush(stdout);
        }

        // Run 3xplus1 algorithm for current number
        do
        {

            if (curr_height > max_height_for_num)
                max_height_for_num = curr_height;

            if (curr_height % 2 == 0)
                curr_height = curr_height / 2;
            else
            {
                // check for potential overflow before calculation
                if (curr_height > (ULLONG_MAX - 1) / 3)
                {
                    printf("\nOverflow at %llu", curr_height);
                    return 0;
                }
                curr_height = (3 * curr_height) + 1;
            }

            steps++;

        } while (curr_height > 1);

        // if this number got to a new max height, save and output it
        if (max_height_for_num > max_height_for_all)
        {
            max_height_for_all = max_height_for_num;
            clock_t t2 = clock();
            clock_gettime(CLOCK_MONOTONIC, &t_now);
            // num, height, steps, time taken (s)
            printf("\r%llu %llu %llu %.1f %.f\n", num, max_height_for_num, steps, (double)(t2 - t) / CLOCKS_PER_SEC, (t_now.tv_sec - t_start.tv_sec) + 1e-9 * (t_now.tv_nsec - t_start.tv_nsec));
            fflush(stdout);
        }
        // if (num == 10)
        //     break;

        // prevent infinite  loop (wrap back to 0)
        if (num == ULLONG_MAX)
            break;
    }

    // t = clock() - t;
    // double time_taken = ((double)t)/CLOCKS_PER_SEC; // in seconds
    // printf("\n\nTook %fs second(s)\n\n", time_taken);

    return 0;
}