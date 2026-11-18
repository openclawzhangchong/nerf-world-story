#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nerf-world-story 机械检查脚本（/test）

用法：
    python scripts/check.py            # 检查 ../stories（相对本脚本）
    python scripts/check.py <目录>     # 检查指定目录

逐篇检查降智爽文梗是否符合六条铁律与五段公式。全部通过退出码 0，否则 1。
人工检查要求见 docs/checklist.md（机检通过后仍需人工过一遍）。
"""
import re
import sys
import glob
import os
from collections import Counter

# Windows 控制台默认 GBK，强制 UTF-8 输出避免 emoji 报错
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------- 每篇必须包含的固定短语（原梗指纹，一字不许动） ----------
REQUIRED_PHRASES = [
    "一觉醒来，全国老师教学水平下降一万倍",
    "而我却保持不变",
    "此时我还没发现任何异常",
    # "本以为又是一节平平无奇的课堂"：场景适配时允许"课堂/上午/下午/办公室日常"等变体，用前缀正则查
    "因为我只是一个刚开始工作的年轻教师",
    "第一次",                       # 第2段标配：第一次有人对我做这件普通事
    "这难道是传说中的",
    "这可是全国老师都不会的方法",
    "一个小小的年轻教师",
    "他是不是还会",                 # 荒诞钻一层
    "开什么玩笑啊",
    "进修1000年",
    "各级教育部门终于注意到原本籍籍无名的我",
    "兴冲冲地",
    "想不到我们县居然有你这样的一位天才",
    "真是太好了",
    "我们教育局有救了",
    "世界需要你这样的天才",
]

# ---------- 黑名单：专业术语与书面语（铁律2，出现即 FAIL） ----------
BLACKLIST = [
    "启发式", "因材施教", "循序渐进", "层层递进", "举一反三", "因势利导",
    "寓教于乐", "循循善诱", "深入浅出", "春风化雨", "言传身教", "探究式",
    "翻转课堂", "核心素养", "差异化", "情境教学", "教学目标", "教学设计",
    "教育理念", "引导式", "互动式", "分层教学", "个性化", "自主探究",
    "元认知", "触类旁通", "融会贯通", "潜移默化", "谆谆教导", "诲人不倦",
    "教学体系", "教学法", "课程设计", "学情分析", "教学评估", "教学反思",
    "教育心理学", "建构", "迁移", "内化于心", "外化于行",
]

# ---------- 雷同检测的采集正则 ----------
RE_QIANCENG = re.compile(r"他是不是还会[^？!！。;；\"”]*")   # 钻一层句式
RE_CHUANSHUO = re.compile(r"传说中的[^！？。;；\"”]*")         # 传说技能名
RE_CHAOXI = re.compile(r"是(?:抄袭|偷学|偷师)[^。;；\"”]{0,20}吧")  # 自我怀疑句（原梗两种变体都认）

TITLE_RE = re.compile(r"^##\s*第(\d+)篇[:：]")
RE_PINGPING = re.compile(r"本以为又是(?:一[节个次顿段趟场回])?平平无奇的")  # 场景句指纹，量词与结尾按场景变体


def split_stories(md_text: str):
    """按 '## 第N篇' 标题切分，返回 [(篇号, 标题行, 正文)]"""
    lines = md_text.splitlines()
    stories, cur_num, cur_title, cur_body = [], None, None, []
    for line in lines:
        m = TITLE_RE.match(line.strip())
        if m:
            if cur_num is not None:
                stories.append((cur_num, cur_title, "\n".join(cur_body).strip()))
            cur_num, cur_title, cur_body = int(m.group(1)), line.strip(), []
        elif cur_num is not None:
            cur_body.append(line)
    if cur_num is not None:
        stories.append((cur_num, cur_title, "\n".join(cur_body).strip()))
    return stories


def check_story(num, title, body):
    """返回该篇的问题列表（空列表 = 通过）"""
    problems = []
    plain = body.replace(" ", "")

    # 铁律6 + 公式第1段：。。。必须在第一段
    paras = [p for p in body.split("\n\n") if p.strip()]
    if len(paras) != 4:
        problems.append(f"段落结构错误：应为4段，实为{len(paras)}段")
    if not paras or "。。。" not in paras[0]:
        problems.append("第一段缺少『。。。』三连句号")

    # 固定短语
    for ph in REQUIRED_PHRASES:
        if ph.replace(" ", "") not in plain:
            problems.append(f"缺少固定短语『{ph}』")

    # "平平无奇"场景句（前缀固定，结尾可按场景变体）
    if not RE_PINGPING.search(plain):
        problems.append("缺少『本以为又是一节平平无奇的……』场景句")

    # 自我怀疑句：是抄袭...吧
    if not RE_CHAOXI.search(body):
        problems.append("缺少『是抄袭……吧』自我怀疑句")

    # 黑名单专业词
    for w in BLACKLIST:
        if w in plain:
            problems.append(f"出现黑名单专业词『{w}』（铁律2）")

    # 字数（正文，去空白）
    n_chars = len(re.sub(r"\s", "", body))
    if not (250 <= n_chars <= 700):
        problems.append(f"字数超出弹性区间：{n_chars}字（要求250-700，目标350-450）")

    # 引号配对
    if plain.count("“") != plain.count("”"):
        problems.append("中文引号不配对")
    return problems


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "stories")
    files = sorted(glob.glob(os.path.join(base, "batch-*.md")))
    if not files:
        print(f"未找到 batch-*.md：{base}")
        sys.exit(1)

    all_nums, total_problems = [], 0
    qianceng_counter, chuanshuo_counter = Counter(), Counter()
    story_locations = {}  # 句式 -> [(篇号, 文件名)]

    for path in files:
        fname = os.path.basename(path)
        with open(path, encoding="utf-8") as f:
            md = f.read()
        stories = split_stories(md)
        print(f"== {fname}: {len(stories)} 篇 ==")
        if len(stories) != 10:
            print(f"  [FAIL] 文件篇数应为10，实为{len(stories)}")
            total_problems += 1

        for num, title, body in stories:
            all_nums.append(num)
            problems = check_story(num, title, body)
            # 雷同采集
            for m in RE_QIANCENG.findall(body):
                key = m.strip()
                qianceng_counter[key] += 1
                story_locations.setdefault(("钻", key), []).append((num, fname))
            for m in RE_CHUANSHUO.findall(body):
                key = m.strip()
                chuanshuo_counter[key] += 1
                story_locations.setdefault(("传", key), []).append((num, fname))

            if problems:
                total_problems += len(problems)
                print(f"  [FAIL] {title}")
                for p in problems:
                    print(f"         - {p}")

    # 编号连续性：全局 1..100 无缺无重
    dup = [n for n, c in Counter(all_nums).items() if c > 1]
    missing = sorted(set(range(1, 101)) - set(all_nums))
    extra = [n for n in all_nums if not (1 <= n <= 100)]
    if dup:
        print(f"[FAIL] 篇号重复：{sorted(set(dup))}")
        total_problems += 1
    if missing:
        print(f"[FAIL] 篇号缺失：{missing}")
        total_problems += 1
    if extra:
        print(f"[FAIL] 越界篇号：{extra}")
        total_problems += 1

    # 防雷同：钻一层句式 / 传说技能名全局不可重复
    for counter, tag in ((qianceng_counter, "钻一层"), (chuanshuo_counter, "传说技能名")):
        for key, cnt in counter.items():
            if cnt > 1:
                locs = story_locations[(tag[0], key)]
                print(f"[FAIL] {tag}雷同（出现{cnt}次）『{key}』→ 篇号 {[n for n, _ in locs]}（文件 {[f for _, f in locs]}）")
                total_problems += 1

    n_stories = len(all_nums)
    print(f"\n汇总：共 {n_stories} 篇，问题 {total_problems} 项")
    if total_problems == 0 and n_stories == 100:
        print("✅ 机检全部通过（人工检查要求见 docs/checklist.md）")
        sys.exit(0)
    print("❌ 机检未通过，请逐项修正后重跑")
    sys.exit(1)


if __name__ == "__main__":
    main()
