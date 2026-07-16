#include <errno.h>
#include <limits.h>
#include <mach-o/dyld.h>
#include <spawn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>

extern char **environ;

static int executable_exists(const char *path) {
  return path != NULL && path[0] != '\0' && access(path, X_OK) == 0;
}

static void dirname_in_place(char *path) {
  char *slash = strrchr(path, '/');
  if (slash == NULL) {
    strcpy(path, ".");
  } else if (slash == path) {
    slash[1] = '\0';
  } else {
    *slash = '\0';
  }
}

static const char *basename_ptr(const char *path) {
  const char *slash = strrchr(path, '/');
  return slash == NULL ? path : slash + 1;
}

static int join_path(char *out, size_t out_size, const char *left, const char *right) {
  return snprintf(out, out_size, "%s/%s", left, right) > 0 && strlen(out) < out_size;
}

static int read_first_line(const char *path, char *out, size_t out_size) {
  FILE *fp = fopen(path, "r");
  if (fp == NULL) {
    return 0;
  }
  if (fgets(out, (int)out_size, fp) == NULL) {
    fclose(fp);
    return 0;
  }
  fclose(fp);
  out[strcspn(out, "\r\n")] = '\0';
  return out[0] != '\0';
}

static int spawn_detached(const char *path, char *const argv[]) {
  pid_t pid = 0;
  int rc = 0;
#ifdef PFI_STAGE1_ISOLATED_PROCESS_GROUP
  posix_spawnattr_t attributes;
  rc = posix_spawnattr_init(&attributes);
  if (rc != 0) {
    return rc;
  }
  rc = posix_spawnattr_setflags(&attributes, POSIX_SPAWN_SETPGROUP);
  if (rc == 0) {
    rc = posix_spawnattr_setpgroup(&attributes, 0);
  }
  if (rc == 0) {
    rc = posix_spawn(&pid, path, NULL, &attributes, argv, environ);
  }
  posix_spawnattr_destroy(&attributes);
#else
  rc = posix_spawn(&pid, path, NULL, NULL, argv, environ);
#endif
  if (rc != 0) {
    return rc;
  }
  return 0;
}

static int spawn_command_direct(const char *target) {
  char *const argv[] = {"/bin/zsh", "-f", (char *)target, NULL};
  return spawn_detached("/bin/zsh", argv) == 0;
}

static void show_error(const char *message) {
  char *const argv[] = {
      "osascript",
      "-e",
      (char *)message,
      NULL,
  };
  spawn_detached("/usr/bin/osascript", argv);
}

static void show_release_error(void) {
  show_error("display dialog \"PFI 版本冲突或本地发布身份缺失。请重新启动 PFI；仍不一致时从受信任的本地 checkout 重新安装 PFI.app，并清除缓存后重试。\" buttons {\"好\"} default button \"好\" with icon caution");
}

static void add_candidate(char candidates[][PATH_MAX], int *count, const char *candidate) {
  if (candidate == NULL || candidate[0] == '\0' || *count >= 8) {
    return;
  }
  for (int i = 0; i < *count; i++) {
    if (strcmp(candidates[i], candidate) == 0) {
      return;
    }
  }
  snprintf(candidates[*count], PATH_MAX, "%s", candidate);
  (*count)++;
}

int main(void) {
  char executable[PATH_MAX];
  uint32_t executable_size = sizeof(executable);
  if (_NSGetExecutablePath(executable, &executable_size) != 0) {
    return 1;
  }

  char macos_dir[PATH_MAX];
  snprintf(macos_dir, sizeof(macos_dir), "%s", executable);
  dirname_in_place(macos_dir);

  char contents_dir[PATH_MAX];
  snprintf(contents_dir, sizeof(contents_dir), "%s", macos_dir);
  dirname_in_place(contents_dir);

  char app_dir[PATH_MAX];
  snprintf(app_dir, sizeof(app_dir), "%s", contents_dir);
  dirname_in_place(app_dir);

  char app_parent_dir[PATH_MAX];
  snprintf(app_parent_dir, sizeof(app_parent_dir), "%s", app_dir);
  dirname_in_place(app_parent_dir);

  char root_file[PATH_MAX];
  join_path(root_file, sizeof(root_file), contents_dir, "Resources/PFI_PROJECT_ROOT");

  char candidates[8][PATH_MAX];
  int candidate_count = 0;
  add_candidate(candidates, &candidate_count, getenv("PFI_HOME"));

  char project_from_file[PATH_MAX];
  if (read_first_line(root_file, project_from_file, sizeof(project_from_file))) {
    add_candidate(candidates, &candidate_count, project_from_file);
  }

  if (strcmp(basename_ptr(app_parent_dir), "macos") == 0) {
    char source_project[PATH_MAX];
    snprintf(source_project, sizeof(source_project), "%s", app_parent_dir);
    dirname_in_place(source_project);
    add_candidate(candidates, &candidate_count, source_project);
  }

  const char *home = getenv("HOME");
  if (home != NULL && home[0] != '\0') {
    char workspace_candidate[PATH_MAX];
    const char *workspace_root = getenv("PFI_WORKSPACE_ROOT");
    if (workspace_root != NULL && workspace_root[0] != '\0') {
      snprintf(workspace_candidate, sizeof(workspace_candidate), "%s/systems/pfi", workspace_root);
    } else {
      snprintf(workspace_candidate, sizeof(workspace_candidate), "%s/Documents/PFI_Workspace/systems/pfi", home);
    }
    add_candidate(candidates, &candidate_count, workspace_candidate);

    char codex_candidate[PATH_MAX];
    snprintf(codex_candidate, sizeof(codex_candidate), "%s/Documents/Codex/PFI", home);
    add_candidate(candidates, &candidate_count, codex_candidate);
  }

  int dry_run = getenv("PFI_APP_LAUNCH_DRY_RUN") != NULL && strcmp(getenv("PFI_APP_LAUNCH_DRY_RUN"), "1") == 0;
  int identity_dry_run = getenv("PFI_APP_LAUNCH_IDENTITY_DRY_RUN") != NULL &&
                         strcmp(getenv("PFI_APP_LAUNCH_IDENTITY_DRY_RUN"), "1") == 0;

  for (int i = 0; i < candidate_count; i++) {
    char command_path[PATH_MAX];
    if (!join_path(command_path, sizeof(command_path), candidates[i], "StartPFI.command")) {
      continue;
    }
    if (!executable_exists(command_path)) {
      continue;
    }
    if (dry_run) {
      printf(
          "PFI_APP_LAUNCH: project=%s command=./StartPFI.command command_path=%s mode=spawn-command\n",
          candidates[i],
          command_path);
      return 0;
    }
    if (identity_dry_run) {
      printf(
          "PFI_APP_LAUNCH_IDENTITY: app_path=%s project=%s command_path=%s mode=spawn-command\n",
          app_dir,
          candidates[i],
          command_path);
      return 0;
    }
    if (setenv("PFI_LAUNCHER_APP_PATH", app_dir, 1) != 0) {
      show_release_error();
      return 1;
    }
    if (!spawn_command_direct(command_path)) {
      show_release_error();
      return 1;
    }
    return 0;
  }

  if (dry_run) {
    printf("PFI_APP_LAUNCH: missing_project\n");
    return 1;
  }
  if (identity_dry_run) {
    printf("PFI_APP_LAUNCH_IDENTITY: missing_project app_path=%s\n", app_dir);
    return 1;
  }

  show_release_error();
  return 1;
}
