#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""/test 一键总入口：依次跑全部机检 + 网站构建验证。

用法：
    python scripts/run_tests.py            # 全部测试
    python scripts/run_tests.py --no-build # 跳过网站构建，只跑机检

通过标准：梗文 100 篇 0 问题；媒体（视频/分镜/图片/15秒分镜）各 100 全 0 问题；网站构建成功。
"""
import os
import sys
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TESTS = [
    ("梗文机检 check.py", [sys.executable, "-I", os.path.join(BASE, "scripts", "check.py")]),
    ("媒体机检 check_media.py", [sys.executable, "-I", os.path.join(BASE, "scripts", "check_media.py")]),
]

def run(label, cmd, show_tail=2):
    print(f"\n===== {label} =====")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    out = (r.stdout or "") + (r.stderr or "")
    tail = [l for l in out.splitlines() if l.strip()][-show_tail:]
    for l in tail:
        print("  " + l)
    return r.returncode == 0

def main():
    no_build = "--no-build" in sys.argv
    results = []
    for label, cmd in TESTS:
        results.append((label, run(label, cmd)))

    if not no_build:
        results.append(("网站构建 build_site.py", run(
            "网站构建 build_site.py",
            [sys.executable, "-I", os.path.join(BASE, "scripts", "build_site.py")], show_tail=3)))

    print("\n========== 汇总 ==========")
    all_ok = True
    for label, ok in results:
        print(("✅" if ok else "❌"), label)
        all_ok = all_ok and ok

    dist = os.path.join(BASE, ".zcode-site", "stage", "dist", "index.html")
    if os.path.exists(dist):
        print(f"✅ 站点产物存在: {round(os.path.getsize(dist)/1024)} KB")
    else:
        print("❌ 站点产物缺失（先跑 build_site.py）")
        all_ok = False

    if all_ok:
        print("\n✅ /test 全部通过——可放心 commit / push / 部署")
        sys.exit(0)
    print("\n❌ /test 未通过——按上方 FAIL 逐项修复后重跑")
    sys.exit(1)

if __name__ == "__main__":
    main()
