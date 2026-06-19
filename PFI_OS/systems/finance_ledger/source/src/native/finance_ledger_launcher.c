#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(void) {
    const char *home = getenv("FINANCE_LEDGER_HOME");
    if (home == NULL || home[0] == '\0') {
        home = ".";
    }
    char script[PATH_MAX];
    snprintf(script, sizeof(script), "%s/scripts/launch_finance_ledger_app.sh", home);
    execl("/bin/zsh", "zsh", script, (char *)NULL);
    return 1;
}
