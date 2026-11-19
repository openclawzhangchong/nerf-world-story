#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nerf-world-story 媒体文案机检（/test）

视频文案 v2（用户定稿）：每条 3 镜 0-5s/5-10s/10-15s，字幕【心声】主角 OS，
镜3 含"失传绝技...大法了！哈哈哈哈！"，结尾参数 "，9:16，15s，720p"；
画面含人设、"带着一群领导冷汗直流"、"教育局领导弯腰陪笑"。
图片文案：每条 5 图，主角描述词齐全。
"""
import re, sys, glob, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
HERO = "37岁中国男性教师，国字脸，黑色短发，身材挺拔，身着白衬衫+深色西裤，面容成熟稳重"
HERO_SHORT = "37岁中国男教师（白衬衫深色西裤）"
ENT = re.compile(r"^###\s*第(\d+)条[｜|]\s*(.+?)（对应梗文第(\d+)篇《(.+?)》）", re.M)
BAD_WORDS = ["叠化", "淡入", "淡出", "转场", "特写转", "中景转", "眼镜滑", "微颤"]


def entries(text):
    ms = list(ENT.finditer(text))
    return [(int(m.group(1)), m.group(2), text[m.end(): ms[i+1].start() if i+1 < len(ms) else len(text)])
            for i, m in enumerate(ms)]


def check_video():
    files = sorted(glob.glob(os.path.join(BASE, "文生视频文案", "*.md")))
    nums, bad = [], 0
    print(f"== 文生视频文案: {len(files)} 卷 ==")
    for path in files:
        name = os.path.basename(path)
        es = entries(open(path, encoding="utf-8").read())
        print(f"  {name}: {len(es)} 条")
        if len(es) != 10:
            print(f"    [FAIL] 条数{len(es)}"); bad += 1
        for n, title, body in es:
            nums.append(n)
            if HERO not in body:
                print(f"    [FAIL] {n} 人设块"); bad += 1
            for t in ["镜头 1｜0-5s", "镜头 2｜5-10s", "镜头 3｜10-15s"]:
                if t not in body:
                    print(f"    [FAIL] {n} 缺 {t}"); bad += 1
            if body.count("字幕【心声】：") != 3:
                print(f"    [FAIL] {n} 心声数"); bad += 1
            if "带着一群领导冷汗直流" not in body:
                print(f"    [FAIL] {n} 冷汗直流"); bad += 1
            if "教育局领导弯腰陪笑" not in body:
                print(f"    [FAIL] {n} 弯腰陪笑"); bad += 1
            if "失传绝技" not in body or "大法了！哈哈哈哈！，9:16，15s，720p" not in body:
                print(f"    [FAIL] {n} 心声结尾/参数"); bad += 1
            if HERO_SHORT not in body:
                print(f"    [FAIL] {n} 画面缺主角"); bad += 1
            # 违规词只查画面行（以"画面："开头的行）
            for line in body.splitlines():
                if line.strip().startswith("画面：") or line.strip().startswith("前半段：") or line.strip().startswith("后半段："):
                    for w in BAD_WORDS:
                        if w in line:
                            print(f"    [FAIL] {n} 画面违规词 {w}"); bad += 1
    return nums, bad


def check_image():
    files = sorted(glob.glob(os.path.join(BASE, "文生图片文案", "*.md")))
    nums, bad = [], 0
    print(f"== 文生图片文案: {len(files)} 卷 ==")
    for path in files:
        es = entries(open(path, encoding="utf-8").read())
        print(f"  {os.path.basename(path)}: {len(es)} 条")
        if len(es) != 10:
            print(f"    [FAIL] 条数{len(es)}"); bad += 1
        for n, title, body in es:
            nums.append(n)
            if re.findall(r"\*\*图(\d)/5", body) != ["1","2","3","4","5"]:
                print(f"    [FAIL] {n} 图片结构"); bad += 1
                continue
            for seg in re.split(r"\*\*图\d/5", body)[1:]:
                if not all(t in seg for t in ["37岁中国男性教师", "180cm", "9:16"]):
                    print(f"    [FAIL] {n} 某图缺主角描述"); bad += 1
    return nums, bad


def main():
    vn, vp = check_video()
    iv, ip = check_image()
    for label, nums in (("视频", vn), ("图片", iv)):
        dup = sorted({n for n in nums if nums.count(n) > 1})
        miss = sorted(set(range(1, 101)) - set(nums))
        if dup: print(f"[FAIL] {label}重复 {dup}")
        if miss: print(f"[FAIL] {label}缺失 {miss}")
    total = vp + ip
    print(f"\n汇总：视频 {len(vn)} / 图片 {len(iv)}，问题 {total}")
    if total == 0 and len(vn) == 100 and len(iv) == 100:
        print("✅ 媒体文案机检全部通过"); sys.exit(0)
    print("❌ 机检未通过"); sys.exit(1)


if __name__ == "__main__":
    main()
