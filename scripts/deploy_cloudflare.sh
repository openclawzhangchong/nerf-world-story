#!/usr/bin/env bash
# Cloudflare Pages 一键部署脚本（nerf-world-story 展示站）
#
# 前置：
#   1. 在 https://dash.cloudflare.com/profile/api-tokens 创建 API Token（模板 "Cloudflare Pages — Edit"）
#   2. 拿到 Account ID（控制台首页右侧 / Workers & Pages 概览页）
#
# 用法（Git Bash / Linux / macOS）：
#   CLOUDFLARE_API_TOKEN=<token> CLOUDFLARE_ACCOUNT_ID=<account_id> bash scripts/deploy_cloudflare.sh
#
# 部署成功后地址：https://nerf-world-story.pages.dev
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

: "${CLOUDFLARE_API_TOKEN:?请先设置 CLOUDFLARE_API_TOKEN（见文件头说明）}"
: "${CLOUDFLARE_ACCOUNT_ID:?请先设置 CLOUDFLARE_ACCOUNT_ID（见文件头说明）}"

# 1. 构建展示站（若 dist 不存在或想刷新内容）
python scripts/build_site.py

# 2. 部署 dist 到 Cloudflare Pages
#    wrangler 优先取全局；否则用本机工作目录 cf-deploy 里预装的版本
if command -v wrangler >/dev/null 2>&1; then
  exec wrangler pages deploy .zcode-site/stage/dist --project-name nerf-world-story --commit-dirty=true
elif [ -x ../cf-deploy/node_modules/.bin/wrangler ] || [ -d ../cf-deploy/node_modules/wrangler ]; then
  cd ../cf-deploy && exec npx wrangler pages deploy ../nerf-world-story/.zcode-site/stage/dist --project-name nerf-world-story --commit-dirty=true
else
  echo "未找到 wrangler，先用 npx 下载（需要 npm 网络）……"
  exec npx -y wrangler pages deploy .zcode-site/stage/dist --project-name nerf-world-story --commit-dirty=true
fi
