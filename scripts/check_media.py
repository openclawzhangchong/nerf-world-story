#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nerf-world-story 媒体文案机检（/test）

用法：python scripts/check_media.py
检查 文生视频文案/ 与 文生图片文案/ 下全部 20 卷：
- 视频每卷 10 条、每条 3 镜、每镜有画面提示词+台词字幕
- 图片每卷 10 条、每条 5 图
- 每个提示词都带主角固定描述词（37岁/180cm/9:16）
- 标志台词与篇号覆盖 1-100
"""
import re
import sys
import glob
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
HERO_TOKENS = ["37岁中国男性教师", "180cm", "9:16"]
END_LINE = "我们教育局有救了！世界需要你这样的天才！"
TITLE_RE = re.compile(r"^###\s*第(\d+)条")


def parse_entries(path):
    text = open(path, encoding="utf-8").read()
    parts = re.split(r"^###\s*", text, flags=re.M)[1:]
    entries = []
    for p in parts:
        num = int(TITLE_RE.match("### " + p.splitlines()[0]).group(1))
        entries.append((num, p))
    return entries


def check_video():
    files = sorted(glob.glob(os.path.join(BASE, "文生视频文案", "*.md")))
    nums, problems = [], 0
    print(f"== 文生视频文案: {len(files)} 卷 ==")
    for path in files:
        name = os.path.basename(path)
        entries = parse_entries(path)
        print(f"  {name}: {len(entries)} 条")
        if len(entries) != 10:
            print(f"    [FAIL] 条数应为10，实为{len(entries)}")
            problems += 1
        for num, body in entries:
            nums.append(num)
            shots = re.findall(r"\*\*镜头(\d)｜约10秒\*\*", body)
            if len(shots) != 3 or shots != ["1", "2", "3"]:
                print(f"    [FAIL] 第{num}条 镜头结构异常: {shots}")
                problems += 1
                continue
            for s in ("1", "2", "3"):
                seg = re.search(r"\*\*镜头" + s + r"｜约10秒\*\*\n(.*?)(?=\n\n|\Z)", body, re.S)
                seg = seg.group(1) if seg else ""
                has_prompt = "画面提示词" in seg
                has_line = "台词字幕" in seg
                hero = all(t in seg for t in HERO_TOKENS)
                if not (has_prompt and has_line and hero):
                    miss = [n for n, ok in [("画面提示词", has_prompt), ("台词字幕", has_line), ("主角描述词", hero)] if not ok]
                    print(f"    [FAIL] 第{num}条 镜头{s} 缺: {miss}")
                    problems += 1
            if "3" in shots and END_LINE not in body:
                print(f"    [FAIL] 第{num}条 缺标志结尾台词")
                problems += 1
    return nums, problems


def check_image():
    files = sorted(glob.glob(os.path.join(BASE, "文生图片文案", "*.md")))
    nums, problems = [], 0
    print(f"== 文生图片文案: {len(files)} 卷 ==")
    for path in files:
        name = os.path.basename(path)
        entries = parse_entries(path)
        print(f"  {name}: {len(entries)} 条")
        if len(entries) != 10:
            print(f"    [FAIL] 条数应为10，实为{len(entries)}")
            problems += 1
        for num, body in entries:
            nums.append(num)
            figs = re.findall(r"\*\*图(\d)/5", body)
            if figs != ["1", "2", "3", "4", "5"]:
                print(f"    [FAIL] 第{num}条 图片结构异常: {figs}")
                problems += 1
                continue
            for seg in re.split(r"\*\*图\d/5", body)[1:]:
                hero = all(t in seg for t in HERO_TOKENS)
                has_prompt = "提示词" in seg
                if not (hero and has_prompt):
                    miss = [n for n, ok in [("提示词", has_prompt), ("主角描述词", hero)] if not ok]
                    print(f"    [FAIL] 第{num}条 某张图 缺: {miss}")
                    problems += 1
    return nums, problems


def main():
    vn, vp = check_video()
    iv, ip = check_image()
    for label, nums in (("视频", vn), ("图片", iv)):
        dup = sorted({n for n in nums if nums.count(n) > 1})
        missing = sorted(set(range(1, 101)) - set(nums))
        if dup:
            print(f"[FAIL] {label}条号重复: {dup}")
            vp += 1
        if missing:
            print(f"[FAIL] {label}条号缺失: {missing}")
            ip += 1
    total = vp + ip
    print(f"\n汇总：视频 {len(vn)} 条 / 图片 {len(iv)} 条，问题 {total} 项")
    if total == 0 and len(vn) == 100 and len(iv) == 100:
        print("✅ 媒体文案机检全部通过")
        sys.exit(0)
    print("❌ 机检未通过，请逐项修正后重跑")
    sys.exit(1)


if __name__ == "__main__":
    main()
