"""Side-effect-free Cloudflare delivery contract shared by audits and deploys."""

from __future__ import annotations


PROJECT_NAME = "openai-memory-atlas"
PUBLISH_DIR_ARG = "apps/memory-atlas/dist"
DEPLOYMENT_MODE = "pages_direct_upload_with_workers_migration_ready_config"
PAGES_DEPLOY_COMMAND = [
    "npx",
    "wrangler",
    "pages",
    "deploy",
    PUBLISH_DIR_ARG,
    "--project-name",
    PROJECT_NAME,
]
