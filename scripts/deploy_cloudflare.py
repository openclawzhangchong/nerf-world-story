# -*- coding: utf-8 -*-
"""Cloudflare Pages 部署脚本（nerf-world-story 展示站）

从环境变量读取 CLOUDFLARE_API_TOKEN / CLOUDFLARE_ACCOUNT_ID：
1. 用 REST API 确保 Pages 项目存在（wrangler 的 project create 在部分账号上报 8000000，改用 API）
2. 用 wrangler pages deploy 上传 .zcode-site/stage/dist

用法：
    CLOUDFLARE_API_TOKEN=xxx CLOUDFLARE_ACCOUNT_ID=yyy python scripts/deploy_cloudflare.py

Token 权限：Cloudflare Pages 编辑（Account → Pages:Edit）。凭据绝不入库。
"""
import json, os, subprocess, sys, urllib.request, urllib.error

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(BASE, ".zcode-site", "stage", "dist")
PROJECT = "nerf-world-story"

token = os.environ.get("CLOUDFLARE_API_TOKEN")
acct = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
assert token and acct, "请设置 CLOUDFLARE_API_TOKEN 与 CLOUDFLARE_ACCOUNT_ID"

HDR = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
API = f"https://api.cloudflare.com/client/v4/accounts/{acct}/pages/projects"

# 1) 确保项目存在
def api_get(url):
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

existing = api_get(API)
names = [p["name"] for p in existing.get("result", [])]
if PROJECT not in names:
    body = json.dumps({"name": PROJECT, "production_branch": "main"}).encode()
    req = urllib.request.Request(API, data=body, headers=HDR, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read())
    assert d.get("success"), f"创建项目失败: {d.get('errors')}"
    print("已创建项目:", PROJECT)
else:
    print("项目已存在:", PROJECT)

# 2) wrangler 部署（优先本地预装，否则 npx）
local = os.path.join(BASE, "..", "cf-deploy", "node_modules", ".bin", "wrangler.cmd")
wrangler = local if os.path.exists(local) else "wrangler"
env = os.environ.copy()
env["WRANGLER_SEND_METRICS"] = "false"
cmd = [wrangler, "pages", "deploy", DIST, "--project-name", PROJECT,
       "--branch", "main", "--commit-dirty", "true"]
print("部署中:", " ".join(cmd[:4]))
r = subprocess.run(cmd, env=env, cwd=os.path.dirname(local) if os.path.exists(local) else None,
                   capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
print((r.stdout or "")[-1200:])
print((r.stderr or "")[-600:])
sys.exit(r.returncode)
