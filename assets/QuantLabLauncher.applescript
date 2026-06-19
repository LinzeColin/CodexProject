on run
  set launchCommand to "PROJECT_DIR='$EVA_OS_HOME'; LOG_DIR=\"$PROJECT_DIR/data/cache\"; LOG_FILE=\"$LOG_DIR/quantlab_macos_app.log\"; /bin/mkdir -p \"$LOG_DIR\"; /bin/echo \"==== $(/bin/date '+%Y-%m-%d %H:%M:%S') EVA_OS macOS app launch ====\" >> \"$LOG_FILE\"; if [ -f /tmp/quantlab_app_smoke_test ]; then /bin/echo \"SMOKE_OK $(/bin/date '+%Y-%m-%d %H:%M:%S')\" >> \"$LOG_FILE\"; exit 0; fi; cd \"$PROJECT_DIR\"; export QUANTLAB_LAUNCH_MODE='macos_app'; /usr/bin/nohup /bin/zsh \"$PROJECT_DIR/StartQuantLab.command\" >> \"$LOG_FILE\" 2>&1 &"
  do shell script "/bin/zsh -lc " & quoted form of launchCommand
end run
