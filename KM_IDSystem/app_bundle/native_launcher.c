#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

static const char *PROJECT_DIR = "/Users/linzezhang/Documents/Codex/2026-06-04/files-mentioned-by-the-user-wuhan";
static const char *RUN_SCRIPT = "/Users/linzezhang/Documents/Codex/2026-06-04/files-mentioned-by-the-user-wuhan/scripts/run_local_services.sh";
static const char *LOG_FILE = "/Users/linzezhang/Documents/Codex/2026-06-04/files-mentioned-by-the-user-wuhan/data/app_entry.log";

static void write_log(const char *message) {
  FILE *file = fopen(LOG_FILE, "a");
  if (!file) {
    return;
  }
  time_t now = time(NULL);
  struct tm local_time;
  localtime_r(&now, &local_time);
  char stamp[32];
  strftime(stamp, sizeof(stamp), "%Y-%m-%d %H:%M:%S", &local_time);
  fprintf(file, "[%s] %s\n", stamp, message);
  fclose(file);
}

int main(void) {
  char data_dir[1024];
  snprintf(data_dir, sizeof(data_dir), "%s/data", PROJECT_DIR);
  mkdir(data_dir, 0755);
  write_log("Native app launcher invoked");

  pid_t pid = fork();
  if (pid < 0) {
    write_log(strerror(errno));
    return 1;
  }
  if (pid > 0) {
    return 0;
  }

  if (setsid() < 0) {
    write_log("setsid failed");
  }

  chdir(PROJECT_DIR);
  int null_fd = open("/dev/null", O_RDWR);
  if (null_fd >= 0) {
    dup2(null_fd, STDIN_FILENO);
    close(null_fd);
  }
  int log_fd = open(LOG_FILE, O_CREAT | O_WRONLY | O_APPEND, 0644);
  if (log_fd >= 0) {
    dup2(log_fd, STDOUT_FILENO);
    dup2(log_fd, STDERR_FILENO);
    close(log_fd);
  }

  setenv("PATH", "/Library/Frameworks/Python.framework/Versions/3.13/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin", 1);
  execl("/bin/bash", "bash", RUN_SCRIPT, (char *)NULL);

  write_log("exec failed");
  return 127;
}

