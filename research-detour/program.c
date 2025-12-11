// cc -o program program.c

#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>

static void invoke_message(void) {
    printf("invoke\n");
    fflush(stdout);
}

static void log_message(int count) {
    printf("heartbeat %d\n", count);
    fflush(stdout);
}

int main(void) {
    printf("pid %d\n", getpid());
    int count = 0;
    for (;;) {
        log_message(count);
        count++;
        sleep(1);
    }
    return 0;
}
