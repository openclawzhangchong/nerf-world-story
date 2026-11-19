#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nerf-world-story 媒体文案机检（/test）

视频文案新标准（用户 2026-11-19 定稿）：
- 每条 3 镜：镜头1约6秒 / 镜头2约7秒 / 镜头3约7秒
- 全局统一人设块置于每条开头
- 音画自洽：镜1=世界观反差、镜2=炸锅+第一次、镜3=传说技能+钻一层+标志结尾
- 画面提示词禁后期词/双景别/微动作（仅检查画面区，头部用法说明不算）
图片文案：每条 5 图，主角描述词齐全。
"""
import re
import sys
import glob
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
HERO = "37岁中国男性教师，国字脸，黑色短发，身材挺拔，身着白衬衫+深色西裤，面容成熟稳重"
HERO_SHORT = "37岁中国男教师（白衬衫深色西裤）"
SHOT_RE = re.compile(r"\*\*镜头(\d)（约(\d)秒 \| ([^）]+)）\*\*\n画面提示词：\n(.*?)\n\n台词字幕：\n(.*?)(?=\n\n---|\Z)", re.S)
ENTRY_RE = re.compile(r"^###\s*第(\d+)条[｜|]\s*(.+?)（对应梗文第(\d+)篇《(.+?)》）", re.M)
BAD_WORDS = ["叠化", "淡入", "淡出", "转场", "特写转", "中景转", "眼镜滑", "微颤", "手部特写转"]
END_MARKS = ["开什么玩笑！", "我们教育局有救了！世界需要你这样的天才！"]


def split_entries(text):
    ms = list(ENTRY_RE.finditer(text))
    out = []
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        out.append((int(m.group(1)), m.group(2).strip(), text[m.end():end]))
    return out


def check_video():
    files = sorted(glob.glob(os.path.join(BASE, "文生视频文案", "*.md")))
    nums, problems = [], 0
    print(f"== 文生视频文案: {len(files)} 卷 ==")
    for path in files:
        name = os.path.basename(path)
        text = open(path, encoding="utf-8").read()
        entries = split_entries(text)
        print(f"  {name}: {len(entries)} 条")
        if len(entries) != 10:
            print(f"    [FAIL] 条数应为10，实为{len(entries)}"); problems += 1
        for n, title, body in entries:
            nums.append(n)
            if HERO not in body:
                print(f"    [FAIL] 第{n}条 缺全局统一人设块"); problems += 1
            shots = SHOT_RE.findall(body)
            if [s[0] for s in shots] != ["1", "2", "3"]:
                print(f"    [FAIL] 第{n}条 镜头结构异常: {[s[0] for s in shots]}"); problems += 1
                continue
            for idx, (sn, secs, sub, prompt, line) in enumerate(shots, 1):
                want_sec = {1: "6", 2: "7", 3: "7"}[idx]
                if secs != want_sec:
                    print(f"    [FAIL] 第{n}条 镜头{idx}时长应为{want_sec}秒，实为{secs}秒"); problems += 1
                hero_ok = HERO_SHORT in prompt or (idx == 3 and "这位白衬衫男教师" in prompt)
                if not hero_ok:
                    print(f"    [FAIL] 第{n}条 镜头{idx}画面缺主角"); problems += 1
                # 画面区违规词（不含头部说明）
                for w in BAD_WORDS:
                    if w in prompt:
                        print(f"    [FAIL] 第{n}条 镜头{idx}画面含违规词『{w}』"); problems += 1
                if "9:16" not in prompt or "8K超清" not in prompt:
                    print(f"    [FAIL] 第{n}条 镜头{idx}画面缺 9:16/8K超清"); problems += 1
            # 台词关键点
            lines = [s[4] for s in shots]
            if "一觉醒来" not in lines[0] or "只有我还和从前一样" not in lines[0]:
                print(f"    [FAIL] 第{n}条 镜1台词缺世界观反差"); problems += 1
            if "炸开了锅" not in lines[1] or "第一次" not in lines[1]:
                print(f"    [FAIL] 第{n}条 镜2台词缺炸锅/第一次"); problems += 1
            for mark in END_MARKS:
                if mark not in lines[2]:
                    print(f"    [FAIL] 第{n}条 镜3台词缺『{mark}』"); problems += 1
    return nums, problems


def check_image():
    files = sorted(glob.glob(os.path.join(BASE, "文生图片文案", "*.md")))
    nums, problems = [], 0
    print(f"== 文生图片文案: {len(files)} 卷 ==")
    for path in files:
        name = os.path.basename(path)
        text = open(path, encoding="utf-8").read()
        entries = split_entries(re.sub(r"^###\s*", "### ", text, flags=re.M))
        # 图片文案标题格式同为 "### 第N条｜..."
        entries = split_entries(text)
        print(f"  {name}: {len(entries)} 条")
        if len(entries) != 10:
            print(f"    [FAIL] 条数应为10，实为{len(entries)}"); problems += 1
        for n, title, body in entries:
            nums.append(n)
            figs = re.findall(r"\*\*图(\d)/5", body)
            if figs != ["1", "2", "3", "4", "5"]:
                print(f"    [FAIL] 第{n}条 图片结构异常: {figs}"); problems += 1
                continue
            for seg in re.split(r"\*\*图\d/5", body)[1:]:
                if not all(t in seg for t in ["37岁中国男性教师", "180cm", "9:16"]):
                    print(f"    [FAIL] 第{n}条 某图缺主角描述词"); problems += 1
    return nums, problems


def main():
    vn, vp = check_video()
    iv, ip = check_image()
    for label, nums, base_p in (("视频", vn, vp), ("图片", iv, ip)):
        dup = sorted({n for n in nums if nums.count(n) > 1})
        missing = sorted(set(range(1, 101)) - set(nums))
        if dup:
            print(f"[FAIL] {label}条号重复: {dup}")
        if missing:
            print(f"[FAIL] {label}条号缺失: {missing}")
    total = vp + ip
    print(f"\n汇总：视频 {len(vn)} 条 / 图片 {len(iv)} 条，问题 {total} 项")
    if total == 0 and len(vn) == 100 and len(iv) == 100:
        print("✅ 媒体文案机检全部通过")
        sys.exit(0)
    print("❌ 机检未通过，请逐项修正后重跑")
    sys.exit(1)


if __name__ == "__main__":
    main()
