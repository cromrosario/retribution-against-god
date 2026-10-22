#!/usr/bin/env python3
"""LB(リミットブレイク)を3段階にする + 侍のガードを「いなし」にする。
 LB: ゲージ 33% / 67% / 100% で Lv1 / Lv2 / Lv3 が使える。段階ごとに威力が増す(Lv1=約4割、Lv2=約7割、Lv3=従来のLB)。
     どの段階で使っても、溜まっているゲージは全て消費する。技名は職業×段階で用意(Lv3は従来の名前)。
 侍: 「身を守る」の代わりに「いなし」を出す(効果は同じ)。
使い方: python3 tools/apply_lb3.py game/index.html [--remove]
 FIT-JS の後ろに LB3-JS、UI3-CSS の後ろに LB3-CSS を足し、元のコード5か所を書き換える。--remove で元にバイト一致。"""
import sys
path = sys.argv[1]; remove = "--remove" in sys.argv
s = open(path, encoding="utf-8", newline="").read()
CB, CE = "/* ==== LB3-CSS:BEGIN", "/* ==== LB3-CSS:END ==== */\n"
JB, JE = "/* ==== LB3-JS:BEGIN", "/* ==== LB3-JS:END ==== */\n"
PAIRS = [
 # 戦闘のLBボタン: 段階に応じた技を出す
 ('    if (G.lb >= 100) {\n      list.push({ label: G.job.lb.n, note: "リミットブレイク / " + G.job.lb.desc, cls: "lb", icon: "lb", cd: true, disabled: !ready, fn: useLB });\n',
  '    if (lbLevel() > 0) { /* LB3 */\n      const lbLv = lbLevel(), lbSk = lbSkill(lbLv); list.push({ label: lbSk.n, note: "リミットブレイク Lv" + lbLv + " / " + lbSk.desc, cls: "lb", icon: "lb", cd: true, disabled: !ready, fn: useLB });\n'),
 # ゲージの表示(段階の色・Lv表示・段階が上がったときの音)
 ('    $("#lbWrap").className = "bar lb" + (G.lb >= 100 ? " full" : "");\n    $("#lbNum").textContent = G.lb >= 100 ? "発動可" : Math.floor(G.lb) + "%";\n',
  '    $("#lbWrap").className = "bar lb lv" + lbLevel() + (G.lb >= 100 ? " full" : ""); /* LB3 */\n    $("#lbNum").textContent = lbLevel() ? "Lv" + lbLevel() + (lbLevel() === 3 ? " MAX" : "") : Math.floor(G.lb) + "%"; lbWatch();\n'),
 # ステータス画面
 ('      b.appendChild(kv(G.job.lb.n, Math.floor(G.lb) + "%"));\n',
  '      b.appendChild(kv("LB(" + G.job.lb.n + ")", "Lv" + lbLevel() + " / " + Math.floor(G.lb) + "%")); /* LB3 */\n'),
 # 侍: いなし。元の「身を守る」の2行は一字も変えず、直後に1行足して、侍のときだけ差し替える(自動テストが label: "身を守る" の文字列を探すため)
 ('    list.push({ label: "身を守る", note: "次の行動まで被ダメージ軽減", icon: "shield", cd: true, alt: true, disabled: !ready,\n      fn: () => { G.guard = true; log("身を低くして、構えを固める。(次の行動を選ぶまで続く)"); endPlayerAction(); } });\n',
  '    list.push({ label: "身を守る", note: "次の行動まで被ダメージ軽減", icon: "shield", cd: true, alt: true, disabled: !ready,\n      fn: () => { G.guard = true; log("身を低くして、構えを固める。(次の行動を選ぶまで続く)"); endPlayerAction(); } });\n    /* LB3 */ if (typeof guardTune === "function") guardTune(list[list.length - 1]);\n'),
 ('    if (G.guard) { G.guard = false; log("防御を解いた。", "dice"); }\n',
  '    if (G.guard) { G.guard = false; log(G.job.id === "samurai" ? "いなしの構えを解いた。" : "防御を解いた。", "dice"); } /* LB3 */\n'),
]
def strip(s):
    for b, e in ((CB, CE), (JB, JE)):
        i = s.find(b)
        if i >= 0:
            j = s.index(e, i) + len(e); s = s[:i] + s[j:]
    for old, new in PAIRS:
        s = s.replace(new, old)
    return s
s = strip(s)
if remove:
    open(path, "w", encoding="utf-8", newline="").write(s); print("removed"); sys.exit()

CSS = CB + " (自動挿入。apply_lb3.py を直して再実行する) ==== */\n" + r"""/* LBゲージ: 3段階の区切りと、段階ごとの色 */
.bar.lb { position: relative; }
.bar.lb::after { content: ""; position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, transparent calc(33.33% - 1px), rgba(0, 0, 0, 0.85) calc(33.33% - 1px), rgba(0, 0, 0, 0.85) calc(33.33% + 1px), transparent calc(33.33% + 1px), transparent calc(66.66% - 1px), rgba(0, 0, 0, 0.85) calc(66.66% - 1px), rgba(0, 0, 0, 0.85) calc(66.66% + 1px), transparent calc(66.66% + 1px)); }
.bar.lb.lv1 > i { background: linear-gradient(#fff3b8, #ffd24a 60%, #c99a0c); }
.bar.lb.lv2 > i { background: linear-gradient(#ffe0a0, #ff9a2e 60%, #c4600a); }
.bar.lb.lv3 > i { background: linear-gradient(#ffd0c0, #ff5a3a 60%, #b01c0c); }
""" + CE
JS = JB + " (自動挿入。apply_lb3.py を直して再実行する) ==== */\n" + r"""/* ---- LB 3段階: ゲージ 33% / 67% / 100% で Lv1 / Lv2 / Lv3。使うと、どの段階でも溜まっているゲージは全て消費する ---- */
const LB_F = [0, 0.4, 0.7, 1];   /* 段階ごとの威力の倍率(Lv3 が従来のLB) */
const LB_NAMES = {               /* [Lv1, Lv2]。Lv3 は職業データの従来の名前 */
  paladin: ["守りの誓い", "聖盾の誓約"], warrior: ["戦士の雄叫び", "不屈の咆哮"], darkknight: ["闇の目覚め", "冥府の胎動"],
  gunbreaker: ["火花の一撃", "烈火の砲撃"], monk: ["十烈拳", "五十烈拳"], samurai: ["一閃・初の型", "一閃・中の型"],
  dragoon: ["竜槍の一突き", "竜牙の穿ち"], reaper: ["魂の刈り取り", "死神の一薙ぎ"], ninja: ["影十本", "影百本"],
  viper: ["蛇の一噛み", "百蛇の顎"], bard: ["流星の矢", "星屑の矢雨"], machinist: ["小口径砲撃", "中口径砲撃"],
  dancer: ["序の舞", "破の舞"], redmage: ["紅の剣閃", "紅蓮の閃光"], pictomancer: ["小さな絵筆", "天を描く画"],
  blackmage: ["流星の詠唱", "彗星の詠唱"], summoner: ["幼竜の咆哮", "竜王の咆哮"], scholar: ["命の鼓動", "生命の脈動"],
  whitemage: ["祈りの聖歌", "聖なる合唱"], astrologian: ["星の囁き", "星々の祝福"], sage: ["小結界", "叡智の結界"]
};
const lbLevel = () => (G ? Math.min(3, Math.floor(G.lb * 3 / 100 + 1e-9)) : 0);
let lbSeen = 0;
function lbSyncSeen() { lbSeen = lbLevel(); }          /* 戦闘開始時: 持ち越したゲージでは音を鳴らさない */
function lbWatch() { const lv = lbLevel(); if (lv > lbSeen && typeof SFX !== "undefined") SFX.play("lbup"); lbSeen = lv; }
const lbStatName = { str: "筋力", dex: "敏捷", wis: "知識", skl: "器用さ" };
function lbScaleBuff(b, f) {
  const o = Object.assign({}, b);
  o.sec = Math.max(4, Math.round(b.sec * f));
  ["shield", "regen", "dot"].forEach((k) => { if (b[k]) o[k] = Math.max(1, Math.round(b[k] * f)); });
  ["dmgUp", "mit", "vuln", "haste", "steal"].forEach((k) => { if (b[k]) o[k] = Math.round(b[k] * f * 100) / 100; });
  if (b.dmgUp) o.n = "攻撃↑" + Math.round(o.dmgUp * 100) + "%";
  if (b.mit) o.n = "被ダメ↓" + Math.round(o.mit * 100) + "%";
  if (b.vuln) o.n = "被ダメ↑" + Math.round(o.vuln * 100) + "%";
  return o;
}
function lbDesc(sk) {
  const p = [], spec = (a) => a[0] + "d" + a[1] + (a[2] ? "+" + a[2] : "") + (a[3] ? "+" + lbStatName[a[3]] + "修正" : "");
  if (sk.dmg) p.push("必中の" + spec(sk.dmg));
  if (sk.strikes) p.push("命中+" + (sk.hit || 0) + "の通常攻撃を" + sk.strikes + "回");
  if (sk.heal && sk.healPct) p.push("HPを最大の" + Math.round(sk.healPct * 100) + "%回復");
  else if (sk.heal) p.push("HPを " + spec(sk.heal) + " 回復");
  if (sk.leech) p.push("与えた分の" + Math.round(sk.leech * 100) + "%を回復");
  if (sk.crits) p.push("確定でクリティカルヒット");
  if (sk.cure) p.push("毒を消す");
  if (sk.shadow) p.push("次の敵の攻撃をかわす");
  if (sk.haste) p.push("次のATBが" + sk.haste + "%から始まる");
  (sk.buffs || []).forEach((b) => p.push(b.n + " " + b.sec + "秒"));
  (sk.debuffs || []).forEach((b) => p.push("敵に" + b.n + " " + b.sec + "秒"));
  return p.join("。");
}
/* 段階 lv(1〜3)の技。Lv3 は従来のLBそのもの */
function lbSkill(lv) {
  const base = G.job.lb;
  if (lv >= 3) return base;
  const f = LB_F[lv];
  const sp = (a) => [Math.max(1, Math.round(a[0] * f)), a[1], Math.round((a[2] || 0) * f), a[3]];
  const sk = { n: (LB_NAMES[G.job.id] || [])[lv - 1] || (base.n + "(Lv" + lv + ")"), lvl: lv };
  if (base.dmg) sk.dmg = sp(base.dmg);
  if (base.heal) sk.heal = sp(base.heal);
  if (base.fullHeal) { sk.heal = [1, 6, 0]; sk.healPct = lv === 1 ? 0.4 : 0.7; }   /* 全回復は Lv3 だけ。Lv1=4割、Lv2=7割 */
  if (base.strikes) { sk.strikes = Math.max(1, Math.round(base.strikes * f)); sk.hit = base.hit; }
  if (base.leech) sk.leech = base.leech;
  if (base.haste) sk.haste = Math.round(base.haste * f);
  if (base.crits && lv >= 2) sk.crits = 1;
  if (base.cure && lv >= 2) sk.cure = 1;
  if (base.shadow && lv >= 2) sk.shadow = 1;
  if (base.buffs) sk.buffs = base.buffs.map((b) => lbScaleBuff(b, f));
  if (base.debuffs) sk.debuffs = base.debuffs.map((b) => lbScaleBuff(b, f));
  sk.desc = lbDesc(sk);
  return sk;
}
/* 元の useLB を置き換える(後ろの宣言が優先される)。溜まっているゲージは全て消費する */
function useLB() {
  const lv = lbLevel(); if (!lv) return;
  const sk = lbSkill(lv);
  G.lb = 0; lbSeen = 0;
  runSkill(sk, "lb", true, false);
}
/* 身を守る(ガード)のボタンの調整: 全職業で防御の音を足し、侍は「いなし」に差し替える */
function guardTune(g) {
  const base = g.fn;
  g.fn = () => { if (typeof SFX !== "undefined") SFX.play("guard"); base(); };
  if (G.job.id === "samurai") {
    g.label = "いなし"; g.note = "刃で受け流す。次の行動まで被ダメージ軽減";
    g.fn = () => { G.guard = true; if (typeof SFX !== "undefined") SFX.play("guard"); log("刃を寝かせ、攻撃をいなす構えをとる。(次の行動を選ぶまで続く)"); endPlayerAction(); };
  }
}
""" + JE
a1 = "/* ==== UI3-CSS:END ==== */\n"; a2 = "/* ==== FIT-JS:END ==== */\n"
assert s.count(a1) == 1 and s.count(a2) == 1, "UI3-CSS / FIT-JS が見つからない(先に適用)"
for old, new in PAIRS:
    assert s.count(old) == 1, "接続箇所の件数が想定と違う: " + old[:50]
for old, new in PAIRS:
    s = s.replace(old, new)
s = s.replace(a1, a1 + CSS).replace(a2, a2 + JS)
open(path, "w", encoding="utf-8", newline="").write(s); print("applied")
