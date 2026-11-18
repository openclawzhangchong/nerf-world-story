# -*- coding: utf-8 -*-
"""nerf-world-story 展示站生成器

从仓库 md 内容生成单文件静态站到 .zcode-site/stage/dist/index.html
（梗文库 100 篇 + 视频文案 100 条 + 图片文案 100 条，全部内嵌可搜索）。

用法（仓库根目录）：
    python scripts/build_site.py

部署：配合 ZCode Sites（.zcode-site/stage/ 下 start.sh + static-server.mjs + dist/），
详见 handoff/HANDOFF.md。
"""
import glob
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, ".zcode-site", "stage", "dist")
os.makedirs(OUT, exist_ok=True)

RE_STORY = re.compile(r"^##\s*第(\d+)篇[:：]\s*(.+)$", re.M)
RE_ENTRY = re.compile(r"^###\s*第(\d+)条[｜|]\s*(.+?)（对应梗文第(\d+)篇《(.+?)》）", re.M)
RE_SHOT = re.compile(r"\*\*镜头(\d)｜约10秒\*\*\s*\n画面提示词：(.*?)\n台词字幕：(.*?)(?=\n\n\*\*镜头|\n---|\Z)", re.S)
RE_FIG = re.compile(r"\*\*图(\d)/5[｜|]\s*(.+?)\*\*\s*\n提示词：(.*?)(?=\n\n\*\*图|\n---|\Z)", re.S)


def read(rel):
    with open(os.path.join(BASE, rel), encoding="utf-8") as f:
        return f.read()


def parse_stories():
    stories = []
    for path in sorted(glob.glob(os.path.join(BASE, "stories", "batch-*.md"))):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        matches = list(RE_STORY.finditer(text))
        for i, m in enumerate(matches):
            num = int(m.group(1))
            title = m.group(2).strip()
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end]
            body = re.sub(r"\n---\s*$", "", body).strip()
            paras = [p.strip() for p in body.split("\n\n") if p.strip() and not p.strip().startswith("#")]
            stories.append({"n": num, "t": title, "ps": paras})
    stories.sort(key=lambda s: s["n"])
    return stories


def parse_media(folder, kind):
    items = []
    for path in sorted(glob.glob(os.path.join(BASE, folder, "*.md"))):
        vol = int(re.sub(r"^.*?第(\d+)卷.*$", r"\1", os.path.basename(path)))
        with open(path, encoding="utf-8") as f:
            text = f.read()
        for m in RE_ENTRY.finditer(text):
            num, title, story_n, story_t = int(m.group(1)), m.group(2).strip(), int(m.group(3)), m.group(4)
            start = m.end()
            nxt = RE_ENTRY.search(text, start)
            end = nxt.start() if nxt else len(text)
            seg = text[start:end]
            if kind == "video":
                shots = [{"i": int(s[0]), "p": s[1].strip(), "l": s[2].strip()} for s in RE_SHOT.findall(seg)]
                items.append({"n": num, "t": title, "sn": story_n, "st": story_t, "vol": vol, "shots": shots})
            else:
                figs = [{"i": int(f[0]), "t": f[1].strip(), "p": f[2].strip()} for f in RE_FIG.findall(seg)]
                items.append({"n": num, "t": title, "sn": story_n, "st": story_t, "vol": vol, "figs": figs})
    items.sort(key=lambda x: x["n"])
    return items


data = {
    "stories": parse_stories(),
    "videos": parse_media("文生视频文案", "video"),
    "images": parse_media("文生图片文案", "image"),
}

assert len(data["stories"]) == 100, f"梗文 {len(data['stories'])}"
assert len(data["videos"]) == 100, f"视频 {len(data['videos'])}"
assert len(data["images"]) == 100, f"图片 {len(data['images'])}"
bad_shots = [v["n"] for v in data["videos"] if len(v["shots"]) != 3]
bad_figs = [i["n"] for i in data["images"] if len(i["figs"]) != 5]
assert not bad_shots, f"镜头异常: {bad_shots}"
assert not bad_figs, f"图片异常: {bad_figs}"
print("数据解析 OK:", {k: len(v) for k, v in data.items()})

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>nerf-world-story｜一觉醒来，全国老师降智一万倍</title>
<style>
:root{
  --board:#152b1e; --chalk:#f3eee0; --chalk-dim:#c9c3b0;
  --yellow:#f7d774; --pink:#f2a2a2; --line:rgba(243,238,224,.14);
  --card:#1c3526; --maxw:1080px;
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  background:
    radial-gradient(1200px 500px at 80% -100px, rgba(247,215,116,.07), transparent),
    radial-gradient(900px 400px at 10% 20%, rgba(168,200,232,.05), transparent),
    var(--board);
  color:var(--chalk);
  font-family:"PingFang SC","Microsoft YaHei","Source Han Sans SC",system-ui,sans-serif;
  line-height:1.75;
}
.wrap{max-width:var(--maxw);margin:0 auto;padding:0 20px}
a{color:var(--yellow);text-decoration:none}
a:hover{text-decoration:underline}
nav{position:sticky;top:0;z-index:50;background:rgba(21,43,30,.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
nav .wrap{display:flex;align-items:center;gap:18px;height:56px}
nav .logo{font-weight:800;letter-spacing:.5px;color:var(--chalk)}
nav .logo b{color:var(--yellow)}
nav a.item{color:var(--chalk-dim);font-size:14px}
nav a.item:hover{color:var(--yellow);text-decoration:none}
nav .gh{margin-left:auto;font-size:13px;border:1px solid var(--line);padding:5px 12px;border-radius:99px;color:var(--chalk)}
nav .gh:hover{border-color:var(--yellow);color:var(--yellow);text-decoration:none}
header.hero{padding:88px 0 64px;text-align:center;border-bottom:1px dashed var(--line)}
.hero .kicker{display:inline-block;font-size:13px;letter-spacing:2px;color:var(--yellow);border:1px dashed rgba(247,215,116,.5);padding:4px 14px;border-radius:99px;margin-bottom:22px}
.hero h1{font-size:clamp(28px,5vw,46px);font-weight:900;letter-spacing:1px;line-height:1.3}
.hero h1 .hl{color:var(--yellow)}
.hero p.sub{margin:18px auto 0;max-width:720px;color:var(--chalk-dim);font-size:16px}
.hero .stats{display:flex;gap:0;justify-content:center;margin-top:36px;flex-wrap:wrap}
.hero .stat{padding:0 30px;border-right:1px solid var(--line);text-align:center}
.hero .stat:last-child{border-right:none}
.hero .stat b{display:block;font-size:30px;font-weight:900;color:var(--yellow)}
.hero .stat span{font-size:13px;color:var(--chalk-dim)}
.hero .cta{margin-top:34px;display:flex;gap:14px;justify-content:center;flex-wrap:wrap}
.btn{display:inline-block;padding:11px 26px;border-radius:12px;font-weight:700;font-size:15px;border:1px solid var(--line);color:var(--chalk)}
.btn:hover{text-decoration:none;border-color:var(--yellow);color:var(--yellow)}
.btn.solid{background:var(--yellow);color:#233024;border-color:var(--yellow)}
.btn.solid:hover{filter:brightness(1.05);color:#233024}
section{padding:64px 0;border-bottom:1px dashed var(--line)}
h2.sec{font-size:26px;font-weight:900;letter-spacing:1px;margin-bottom:8px}
h2.sec .no{color:var(--yellow);margin-right:10px;font-family:Georgia,serif}
p.secdesc{color:var(--chalk-dim);font-size:15px;margin-bottom:30px;max-width:760px}
.steps{display:grid}
.step{display:flex;gap:16px;padding:16px 0;border-top:1px dashed var(--line)}
.step:first-child{border-top:none}
.step .sn{flex:0 0 44px;height:44px;border-radius:12px;background:rgba(247,215,116,.12);color:var(--yellow);display:flex;align-items:center;justify-content:center;font-weight:900;font-size:18px}
.step h3{font-size:16px;margin-bottom:4px}
.step p{font-size:14px;color:var(--chalk-dim)}
.grid{display:grid;gap:14px}
.g3{grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 22px}
.card h3{font-size:16px;margin-bottom:8px;color:var(--yellow)}
.card p{font-size:14px;color:var(--chalk-dim)}
.qilian li{list-style:none;display:flex;gap:14px;padding:12px 0;border-top:1px dashed var(--line);font-size:15px}
.qilian li:first-child{border-top:none}
.qilian .qn{flex:0 0 30px;height:30px;border-radius:8px;background:rgba(242,162,162,.14);color:var(--pink);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:14px}
.qilian p{color:var(--chalk-dim);font-size:14px;margin-top:2px}
.golden{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:26px 28px}
.golden .tag{display:inline-block;font-size:12px;color:var(--pink);border:1px solid rgba(242,162,162,.4);padding:3px 12px;border-radius:99px;margin-bottom:14px}
.golden h3{font-size:18px;margin-bottom:12px}
.golden p{font-size:15px;color:var(--chalk);margin-bottom:12px;text-align:justify}
.golden p.dim{color:var(--chalk-dim)}
.tabs{display:flex;gap:10px;margin-bottom:18px;flex-wrap:wrap}
.tab{padding:9px 20px;border-radius:99px;border:1px solid var(--line);cursor:pointer;font-size:14px;color:var(--chalk-dim);user-select:none}
.tab.on{background:var(--yellow);color:#233024;border-color:var(--yellow);font-weight:800}
.search{width:100%;padding:12px 18px;border-radius:12px;border:1px solid var(--line);background:rgba(0,0,0,.18);color:var(--chalk);font-size:15px;outline:none;margin-bottom:16px}
.search:focus{border-color:var(--yellow)}
.count{font-size:13px;color:var(--chalk-dim);margin-bottom:14px}
.list details{background:var(--card);border:1px solid var(--line);border-radius:12px;margin-bottom:10px;overflow:hidden}
.list summary{cursor:pointer;padding:14px 18px;display:flex;align-items:center;gap:12px;list-style:none}
.list summary::-webkit-details-marker{display:none}
.list summary:hover{background:rgba(247,215,116,.05)}
.list .no{flex:0 0 auto;font-family:Georgia,serif;color:var(--yellow);font-weight:800;font-size:15px;min-width:52px}
.list .tt{font-size:15px;font-weight:600}
.list .meta{margin-left:auto;font-size:12px;color:var(--chalk-dim);flex:0 0 auto}
.list .body{padding:4px 18px 18px;border-top:1px dashed var(--line)}
.list .body p{font-size:14px;color:var(--chalk);margin:12px 0;text-align:justify}
.list .body .lab{display:inline-block;font-size:12px;color:var(--yellow);border:1px dashed rgba(247,215,116,.4);border-radius:6px;padding:1px 8px;margin:14px 0 4px}
.list .body .pv{background:rgba(0,0,0,.16);border-left:3px solid var(--yellow);border-radius:0 8px 8px 0;padding:10px 14px;margin:8px 0;font-size:13px;color:var(--chalk);text-align:justify}
.list .body .lc{background:rgba(242,162,162,.08);border-left:3px solid var(--pink);border-radius:0 8px 8px 0;padding:10px 14px;margin:8px 0;font-size:13px;color:var(--chalk);text-align:justify}
.list .body .dim{color:var(--chalk-dim);font-size:13px}
footer{padding:44px 0 60px;text-align:center;color:var(--chalk-dim);font-size:13px}
footer .big{font-size:16px;color:var(--chalk);margin-bottom:10px}
.chalk-line{height:3px;background:repeating-linear-gradient(90deg,var(--yellow) 0 14px,transparent 14px 26px);border-radius:2px;opacity:.35;margin-top:10px}
@media(max-width:640px){.hero .stat{padding:0 14px}.hero .stat b{font-size:22px}}
</style>
</head>
<body>
<nav><div class="wrap">
  <span class="logo">nerf-<b>world</b>-story</span>
  <a class="item" href="#formula">写法</a>
  <a class="item" href="#golden">黄金标准</a>
  <a class="item" href="#library">内容库</a>
  <a class="gh" href="https://github.com/openclawzhangchong/nerf-world-story" target="_blank" rel="noopener">GitHub ↗</a>
</div></nav>

<header class="hero"><div class="wrap">
  <div class="kicker">AI 技能 · 100 篇梗文 · 200 条即梦文案</div>
  <h1>一觉醒来，全国老师<span class="hl">降智一万倍</span><br>而我却保持不变</h1>
  <p class="sub">一个可安装的 AI 技能包：让任何 AI 都能稳定写出「降智爽文梗」——技能普通到废、领导层层发癫、结尾惊动教育局。附带 100 篇成文、100 条文生视频文案、100 条文生图片文案，全部开源。</p>
  <div class="stats">
    <div class="stat"><b>100</b><span>篇梗文成文</span></div>
    <div class="stat"><b>300</b><span>镜视频提示词</span></div>
    <div class="stat"><b>500</b><span>张图提示词</span></div>
    <div class="stat"><b>100%</b><span>机检通过</span></div>
  </div>
  <div class="cta">
    <a class="btn solid" href="#library">📖 马上阅读</a>
    <a class="btn" href="https://github.com/openclawzhangchong/nerf-world-story" target="_blank" rel="noopener">⭐ GitHub 仓库</a>
  </div>
</div></header>

<section id="formula"><div class="wrap">
  <h2 class="sec"><span class="no">01</span>五段公式</h2>
  <p class="secdesc">任何一篇都严格按这个顺序写，段段有固定动作。爽点内核只有一句话：主角只会干最普通的事，全世界却把他当神。</p>
  <div class="steps">
    <div class="step"><div class="sn">1</div><div><h3>开头反差钩子</h3><p>「把【核心技能】改成【最废仪式】。。。一觉醒来，全国XX下降一万倍。而我却保持不变。」——保留三个句号的 low 味，读者比主角先爽。</p></div></div>
    <div class="step"><div class="sn">2</div><div><h3>主角铺垫</h3><p>底层新人自认平平无奇——资历越浅，后面反差越大。</p></div></div>
    <div class="step"><div class="sn">3</div><div><h3>引爆现场</h3><p>随手做出废动作，围观者炸锅。标配句式：「干了这么多年，第一次有人对我做这件普通事。」</p></div></div>
    <div class="step"><div class="sn">4</div><div><h3>领导发癫（爽点核心）</h3><p>七连拳按顺序打完，一拳比一拳荒诞，见下节。</p></div></div>
    <div class="step"><div class="sn">5</div><div><h3>传播升级收尾</h3><p>录制 → 播放量 → 部门惊动 → 「我们教育局有救了！世界需要你这样的天才！」三连一字不改。</p></div></div>
  </div>

  <h2 class="sec" style="margin-top:56px"><span class="no">02</span>写前铁律</h2>
  <p class="secdesc">违反任何一条都不合格——这是用户逐句验收换来的规矩。</p>
  <div class="grid g3">
    <div class="card"><h3>① 技能普通到废</h3><p>问一句"听懂了没有"、把翻到的页讲出来——任何正常人都会干的事。绝不能是专业绝活。</p></div>
    <div class="card"><h3>② 全程大白话</h3><p>禁用"启发式教学""因材施教"等一切术语，领导台词小学生都能看懂。</p></div>
    <div class="card"><h3>③ 震惊围绕废动作本身</h3><p>震惊的不是"做得多好"，而是"他居然会做这件事"这个事实。</p></div>
    <div class="card"><h3>④ 荒诞再钻一层</h3><p>"他是不是还会等学生回答？开什么玩笑啊！"——把废动作的基本延伸当更高神迹。</p></div>
    <div class="card"><h3>⑤ 不用正常智力写</h3><p>全世界降智到底，逻辑漏洞就是笑点，不要修复。</p></div>
    <div class="card"><h3>⑥ 成文加标点断句</h3><p>保留"。。。"的 low 味，但段落完整、引号配对、读得通。</p></div>
  </div>

  <h2 class="sec" style="margin-top:56px"><span class="no">03</span>领导发癫七连</h2>
  <p class="secdesc">第4段按顺序连打七拳，第 5 拳是全段灵魂：荒诞必须钻到第二层。</p>
  <ul class="qilian">
    <li><span class="qn">1</span><div>被震惊到目瞪口呆<b>（固定开场）</b></div></li>
    <li><span class="qn">2</span><div>"这难道是传说中的XXX！"<b>（把废动作封神：提问教学/翻书教学）</b></div></li>
    <li><span class="qn">3</span><div>"这可是全国老师都不会的方法！"<b>（铺世界观）</b></div></li>
    <li><span class="qn">4</span><div>"一个小小的年轻教师，居然会XXX。"<b>（把废动作原样复述）</b></div></li>
    <li><span class="qn">5</span><div>"他是不是还会XXX？开什么玩笑啊！"<b>（荒诞钻第二层，句式每篇必换）</b></div></li>
    <li><span class="qn">6</span><div>"恐怕只有全国最厉害的老师，进修1000年才能够想出来！"<b>（固定量级）</b></div></li>
    <li><span class="qn">7</span><div>"他是怎么做到的？是抄袭名师的课吧。"<b>（降智世界唯一的理性解释是作弊）</b></div></li>
  </ul>
</div></section>

<section id="golden"><div class="wrap">
  <h2 class="sec"><span class="no">04</span>黄金标准（用户逐句验收）</h2>
  <p class="secdesc">教师·提问版——技能废到"问一句听懂了没有"，主任发癫一层比一层荒诞。新写的文都要达到它的水平。</p>
  <div class="golden">
    <span class="tag">案例三 · 用户验收 ✅</span>
    <h3>提问教学：把讲课改成划重点</h3>
    <p class="dim">把讲课改成划重点。。。一觉醒来，全国老师教学水平下降一万倍。而我却保持不变。此时我还没发现任何异常。</p>
    <p>直到那天，我跟往常一样走进教室，本以为又是一节平平无奇的课堂，因为我只是一个刚开始工作的年轻教师。没想到我只是随口问了句"听懂了没有"，全班学生立刻炸开了锅——读了这么多年书，第一次有老师问他们听懂没有。</p>
    <p>教室的骚动很快引来了教导主任。听到我竟然会向学生提问，主任被震惊到目瞪口呆："这难道是传说中的提问教学？这可是全国老师都不会的方法！一个小小的年轻教师，居然会问学生听懂了没有。他是不是还会等学生回答？开什么玩笑啊。这种事，恐怕只有全国最厉害的老师进修1000年才能够想出来。他是怎么做到的？是抄袭名师的课吧。"</p>
    <p>校领导决定把整节课录制下来。随着录像播放量的增加，各级教育部门终于注意到原本籍籍无名的我，兴冲冲地到学校找我："想不到我们县居然有你这样的一位天才，真是太好了！我们教育局有救了！世界需要你这样的天才！"</p>
    <div class="chalk-line"></div>
  </div>
</div></section>

<section id="library"><div class="wrap">
  <h2 class="sec"><span class="no">05</span>内容库 · 全部开源</h2>
  <p class="secdesc">三套内容一一对应：每篇梗文 → 一条 3 镜视频文案 → 一条 5 图图片文案。点开条目读全文，提示词可直接复制进即梦生成。</p>
  <div class="tabs">
    <div class="tab on" data-tab="stories">📖 梗文库 · 100 篇</div>
    <div class="tab" data-tab="videos">🎬 视频文案 · 100 条</div>
    <div class="tab" data-tab="images">🖼️ 图片文案 · 100 条</div>
  </div>
  <input class="search" id="search" type="search" placeholder="搜索：标题 / 关键词（如 提问、粉笔、家长会、听懂了没有）…">
  <div class="count" id="count"></div>
  <div class="list" id="list"></div>
</div></section>

<footer><div class="wrap">
  <p class="big">我们教育局有救了！世界需要你这样的天才！</p>
  <p>nerf-world-story · MIT License · 由 AI 技能包自动产出 · <a href="https://github.com/openclawzhangchong/nerf-world-story" target="_blank" rel="noopener">github.com/openclawzhangchong/nerf-world-story</a></p>
  <p style="margin-top:8px">安装：git clone 到 ~/.agents/skills/nerf-world-story 即可让任何 AI 学会这个写法</p>
</div></footer>

<script id="data" type="application/json">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById("data").textContent);
const esc = s => s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
let cur = "stories", q = "";
const VOLS = {1:"课堂基本功",2:"课堂互动",3:"提问与作业",4:"批改与备课",5:"教学与关心学生",6:"暖心小动作",7:"尊重学生与考试",8:"讲评与课堂管理",9:"放学与职业日常",10:"校园点滴"};
function storyBody(s){ return s.ps.map(p=>`<p>${esc(p)}</p>`).join(""); }
function videoBody(v){
  const shot = v.shots.map(s=>`<span class="lab">镜头${s.i}｜约10秒 · 画面提示词</span><div class="pv">${esc(s.p)}</div><span class="lab">台词字幕</span><div class="lc">${esc(s.l)}</div>`).join("");
  return `<p class="dim">对应梗文第${v.sn}篇《${esc(v.st)}》 · 提示词可直接粘贴进即梦"视频生成"，比例 9:16</p>${shot}`;
}
function imageBody(m){
  const fig = m.figs.map(f=>`<span class="lab">图${f.i}/5｜${esc(f.t)}</span><div class="pv">${esc(f.p)}</div>`).join("");
  return `<p class="dim">对应梗文第${m.sn}篇《${esc(m.st)}》 · 五图对应五段公式，每张可直接粘贴进即梦"图片生成"，比例 9:16</p>${fig}`;
}
function render(){
  const src = DATA[cur];
  const kw = q.trim().toLowerCase();
  const items = src.filter(it=>{
    if(!kw) return true;
    const hay = (it.t + JSON.stringify(it.ps||it.shots||it.figs)).toLowerCase();
    return hay.includes(kw);
  });
  document.getElementById("count").textContent = `共 ${items.length} 条（库内总量 100 条）`;
  document.getElementById("list").innerHTML = items.map(it=>{
    let body, meta;
    if(cur==="stories"){ body=storyBody(it); meta=`卷${Math.ceil(it.n/10)} · ${VOLS[Math.ceil(it.n/10)]}`; }
    else if(cur==="videos"){ body=videoBody(it); meta=`第${it.vol}卷 ${VOLS[it.vol]} · 3镜`; }
    else { body=imageBody(it); meta=`第${it.vol}卷 ${VOLS[it.vol]} · 5图`; }
    return `<details><summary><span class="no">#${String(it.n).padStart(3,"0")}</span><span class="tt">${esc(it.t)}</span><span class="meta">${meta}</span></summary><div class="body">${body}</div></details>`;
  }).join("") || `<p class="dim" style="padding:20px">没有匹配的内容，换个关键词试试～</p>`;
}
document.querySelectorAll(".tab").forEach(t=>{
  t.addEventListener("click",()=>{
    document.querySelectorAll(".tab").forEach(x=>x.classList.remove("on"));
    t.classList.add("on");
    cur = t.dataset.tab;
    render();
  });
});
document.getElementById("search").addEventListener("input",e=>{ q=e.target.value; render(); });
render();
</script>
</body>
</html>
"""

data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
html = HTML.replace("__DATA__", data_json)
with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8", newline="\n") as f:
    f.write(html)
print("index.html 生成:", round(os.path.getsize(os.path.join(OUT, "index.html")) / 1024), "KB")
