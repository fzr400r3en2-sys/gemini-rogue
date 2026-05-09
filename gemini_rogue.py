import os
import sys
import random
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text
from rich.align import Align

os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

console = Console()

FINAL_FLOOR = 20
BOSS_FLOORS = {5, 10, 15, 20}

# =====================================================================
# アイテム定義
# =====================================================================
ITEMS: Dict[str, dict] = {
    # 消費アイテム
    "ポーション":       {"category": "consumable", "effect": "heal",     "power": 25, "price": 30,  "desc": "HPを25回復"},
    "ハイポーション":    {"category": "consumable", "effect": "heal",     "power": 60, "price": 80,  "desc": "HPを60回復"},
    "エリクサー":       {"category": "consumable", "effect": "full_heal", "power": 0,  "price": 200, "desc": "HPを全回復"},
    "毒消し草":         {"category": "consumable", "effect": "cure_poison","power": 0, "price": 25,  "desc": "毒を治す"},
    "力の薬":           {"category": "consumable", "effect": "buff_atk", "power": 5,  "price": 60,  "desc": "5ターン攻撃力+5"},
    "鉄壁の薬":         {"category": "consumable", "effect": "buff_def", "power": 5,  "price": 60,  "desc": "5ターン防御力+5"},
    "煙玉":             {"category": "consumable", "effect": "escape",   "power": 0,  "price": 40,  "desc": "戦闘から確実に逃走"},
    "魔法の巻物":       {"category": "consumable", "effect": "magic",    "power": 30, "price": 70,  "desc": "敵に30の固定ダメージ"},
    "賢者の石":         {"category": "consumable", "effect": "level_up", "power": 0,  "price": 500, "desc": "即座にレベルアップ"},
    # 武器
    "木の棒":           {"category": "weapon", "atk": 2,  "price": 20,  "desc": "攻撃力+2"},
    "鉄の剣":           {"category": "weapon", "atk": 6,  "price": 120, "desc": "攻撃力+6"},
    "鋼の剣":           {"category": "weapon", "atk": 12, "price": 300, "desc": "攻撃力+12"},
    "炎の剣":           {"category": "weapon", "atk": 18, "price": 600, "desc": "攻撃力+18・たまに炎ダメージ"},
    "竜殺しの槍":       {"category": "weapon", "atk": 25, "price": 1200,"desc": "攻撃力+25・竜種に倍ダメージ"},
    # 防具
    "革の鎧":           {"category": "armor", "defense": 3,  "price": 80,  "desc": "防御力+3"},
    "鎖帷子":           {"category": "armor", "defense": 7,  "price": 220, "desc": "防御力+7"},
    "鋼の鎧":           {"category": "armor", "defense": 12, "price": 500, "desc": "防御力+12"},
    "聖なる鎧":         {"category": "armor", "defense": 18, "price": 1000,"desc": "防御力+18・毒無効"},
}

# =====================================================================
# モンスター定義
# =====================================================================
class MonsterTpl(BaseModel):
    name: str
    hp: int
    atk: int
    defense: int
    exp: int
    gold: int
    drops: List[Tuple[str, float]] = []
    flavor: str = ""
    tags: List[str] = []  # "dragon", "undead" 等

MONSTERS: Dict[str, MonsterTpl] = {
    "スライム":     MonsterTpl(name="スライム",     hp=12, atk=4,  defense=1, exp=6,  gold=5,  drops=[("ポーション",0.15)],                       flavor="ぷるぷる震える青い塊。"),
    "コウモリ":     MonsterTpl(name="コウモリ",     hp=8,  atk=5,  defense=0, exp=5,  gold=4,  drops=[("毒消し草",0.10)],                         flavor="鋭い爪で襲いかかってくる。"),
    "ゴブリン":     MonsterTpl(name="ゴブリン",     hp=18, atk=7,  defense=2, exp=10, gold=12, drops=[("木の棒",0.08),("ポーション",0.10)],        flavor="緑色の小鬼。下卑た笑みを浮かべる。"),
    "オーク":       MonsterTpl(name="オーク",       hp=30, atk=10, defense=4, exp=18, gold=22, drops=[("鉄の剣",0.05),("ポーション",0.20)],        flavor="筋骨隆々の獣人戦士。"),
    "スケルトン":   MonsterTpl(name="スケルトン",   hp=24, atk=11, defense=3, exp=16, gold=18, drops=[("革の鎧",0.07)],                            flavor="カタカタと骨を鳴らす死霊。", tags=["undead"]),
    "ダイアウルフ": MonsterTpl(name="ダイアウルフ", hp=28, atk=13, defense=2, exp=20, gold=20, drops=[("毒消し草",0.15)],                          flavor="赤い目を輝かせた巨狼。"),
    "トロル":       MonsterTpl(name="トロル",       hp=55, atk=16, defense=6, exp=35, gold=45, drops=[("ハイポーション",0.20),("鎖帷子",0.05)],   flavor="再生する皮膚を持つ巨人。"),
    "ゾンビ":       MonsterTpl(name="ゾンビ",       hp=40, atk=14, defense=4, exp=30, gold=30, drops=[("毒消し草",0.30)],                          flavor="腐臭を放つ死者。毒を持つ。", tags=["undead","poison"]),
    "ダークエルフ": MonsterTpl(name="ダークエルフ", hp=45, atk=20, defense=5, exp=38, gold=55, drops=[("魔法の巻物",0.15),("鋼の剣",0.04)],        flavor="影に紛れる弓使い。"),
    "ミノタウロス": MonsterTpl(name="ミノタウロス", hp=80, atk=24, defense=8, exp=55, gold=80, drops=[("鋼の剣",0.10),("鋼の鎧",0.06)],            flavor="迷宮の主の眷属。"),
    "リッチ":       MonsterTpl(name="リッチ",       hp=70, atk=28, defense=7, exp=60, gold=100,drops=[("魔法の巻物",0.30),("エリクサー",0.05)],   flavor="不死の魔術師。", tags=["undead"]),
    "ワイバーン":   MonsterTpl(name="ワイバーン",   hp=90, atk=26, defense=10,exp=65, gold=110,drops=[("竜殺しの槍",0.03),("ハイポーション",0.20)],flavor="鋭い爪と尾を持つ亜竜。", tags=["dragon"]),
    # ボス
    "スライム王":   MonsterTpl(name="スライム王",   hp=80, atk=12, defense=5, exp=60, gold=120,drops=[("ハイポーション",1.0)],                    flavor="巨大な王冠を被った金色のスライム。"),
    "ゴブリン将軍": MonsterTpl(name="ゴブリン将軍", hp=160,atk=22, defense=10,exp=140,gold=300,drops=[("鋼の剣",1.0),("力の薬",1.0)],             flavor="赤い甲冑の歴戦の戦士。"),
    "古龍":         MonsterTpl(name="古龍",         hp=300,atk=34, defense=14,exp=280,gold=600,drops=[("聖なる鎧",1.0),("エリクサー",1.0)],       flavor="千年を生きた翠の竜。", tags=["dragon"]),
    "魔王ザロス":   MonsterTpl(name="魔王ザロス",   hp=520,atk=44, defense=18,exp=500,gold=1500,drops=[("賢者の石",1.0)],                          flavor="この迷宮の主。漆黒の闇を纏う。"),
}

FLOOR_POOL: Dict[int, List[str]] = {
    1: ["スライム","コウモリ","ゴブリン"],
    2: ["コウモリ","ゴブリン","オーク"],
    3: ["オーク","スケルトン","ダイアウルフ"],
    4: ["トロル","ゾンビ","ダークエルフ"],
    5: ["ミノタウロス","リッチ","ワイバーン"],
}

def floor_tier(floor: int) -> int:
    if floor <= 3:   return 1
    if floor <= 6:   return 2
    if floor <= 9:   return 3
    if floor <= 14:  return 4
    return 5

def boss_for_floor(floor: int) -> str:
    return {5:"スライム王", 10:"ゴブリン将軍", 15:"古龍", 20:"魔王ザロス"}[floor]

def make_monster(name: str) -> MonsterTpl:
    return MONSTERS[name].model_copy(deep=True)

# =====================================================================
# プレイヤー
# =====================================================================
CLASSES = {
    "戦士":   {"hp": 40, "atk": 12, "defense": 6, "gold": 30, "start": ["鉄の剣","ポーション"]},
    "盗賊":   {"hp": 28, "atk": 11, "defense": 4, "gold": 80, "start": ["木の棒","煙玉","煙玉"]},
    "魔導士": {"hp": 24, "atk": 8,  "defense": 3, "gold": 50, "start": ["木の棒","魔法の巻物","魔法の巻物"]},
}

class StatusEffect(BaseModel):
    name: str
    turns: int
    power: int = 0

class PlayerState(BaseModel):
    name: str = "冒険者"
    cls: str = "戦士"
    level: int = 1
    hp: int = 40
    max_hp: int = 40
    base_atk: int = 12
    base_def: int = 6
    exp: int = 0
    gold: int = 30
    floor: int = 1
    inventory: List[str] = Field(default_factory=list)
    weapon: Optional[str] = None
    armor: Optional[str] = None
    effects: List[StatusEffect] = Field(default_factory=list)

    @property
    def atk(self) -> int:
        bonus = ITEMS[self.weapon]["atk"] if self.weapon else 0
        for e in self.effects:
            if e.name == "buff_atk":
                bonus += e.power
        return self.base_atk + bonus

    @property
    def defense(self) -> int:
        bonus = ITEMS[self.armor]["defense"] if self.armor else 0
        for e in self.effects:
            if e.name == "buff_def":
                bonus += e.power
        return self.base_def + bonus

    def has_effect(self, name: str) -> bool:
        return any(e.name == name for e in self.effects)

    def add_effect(self, name: str, turns: int, power: int = 0):
        for e in self.effects:
            if e.name == name:
                e.turns = max(e.turns, turns)
                e.power = max(e.power, power)
                return
        self.effects.append(StatusEffect(name=name, turns=turns, power=power))

    def tick_effects(self) -> List[str]:
        msgs = []
        survivors = []
        for e in self.effects:
            if e.name == "poison":
                if self.armor == "聖なる鎧":
                    msgs.append("聖なる鎧が毒を浄化した。")
                    continue
                self.hp -= 2
                msgs.append("毒で2のダメージ。")
            e.turns -= 1
            if e.turns > 0:
                survivors.append(e)
            else:
                msgs.append(f"[{e.name}]の効果が切れた。")
        self.effects = survivors
        if self.hp < 0:
            self.hp = 0
        return msgs

    def need_exp(self) -> int:
        return self.level * 20 + (self.level - 1) * 5

    def gain_exp(self, exp: int) -> List[str]:
        msgs = []
        self.exp += exp
        while self.exp >= self.need_exp():
            self.exp -= self.need_exp()
            self.level += 1
            self.max_hp += 8
            self.hp = self.max_hp
            self.base_atk += 2
            self.base_def += 1
            msgs.append(f"★ レベルアップ！ Lv{self.level} (HP+8 / 攻+2 / 防+1)")
        return msgs

    def heal(self, amount: int) -> int:
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

# =====================================================================
# 描画ヘルパ
# =====================================================================
def render_status(p: PlayerState):
    t = Table(show_header=False, box=None, padding=(0,1))
    t.add_column(style="cyan", justify="right")
    t.add_column(style="white")
    t.add_row("冒険者", f"{p.name} ({p.cls}) Lv{p.level}")
    hp_color = "green" if p.hp > p.max_hp*0.5 else "yellow" if p.hp > p.max_hp*0.25 else "red"
    t.add_row("HP",  f"[{hp_color}]{p.hp}/{p.max_hp}[/{hp_color}]")
    t.add_row("攻撃/防御", f"{p.atk} / {p.defense}")
    t.add_row("EXP", f"{p.exp}/{p.need_exp()}")
    t.add_row("所持金", f"{p.gold} G")
    t.add_row("武器", p.weapon or "なし")
    t.add_row("防具", p.armor or "なし")
    inv = ", ".join(p.inventory) if p.inventory else "空"
    t.add_row("所持品", inv)
    if p.effects:
        t.add_row("状態", ", ".join(f"{e.name}({e.turns})" for e in p.effects))
    return Panel(t, title=f"[bold]B{p.floor}F[/bold]  Gemini-Rogue", border_style="blue")

def show_options(opts: List[str]):
    lines = [f"[bold cyan]{i+1}[/bold cyan]: {o}" for i, o in enumerate(opts)]
    console.print(Panel("\n".join(lines), title="行動", border_style="yellow"))

def ask_choice(opts: List[str], prompt: str = "選択") -> int:
    show_options(opts)
    choices = [str(i+1) for i in range(len(opts))]
    return int(Prompt.ask(prompt, choices=choices)) - 1

def narrate(text: str, title: str = "", style: str = "white"):
    console.print(Panel(Text.from_markup(text), title=title, border_style="green"))

# =====================================================================
# アイテム使用
# =====================================================================
def use_item(p: PlayerState, item: str, in_combat: bool = False, target: Optional[MonsterTpl] = None) -> Tuple[bool, str]:
    info = ITEMS[item]
    cat = info["category"]

    if cat == "weapon":
        old = p.weapon
        p.weapon = item
        p.inventory.remove(item)
        if old:
            p.inventory.append(old)
        return True, f"{item} を装備した。" + (f"（{old} を外した）" if old else "")

    if cat == "armor":
        old = p.armor
        p.armor = item
        p.inventory.remove(item)
        if old:
            p.inventory.append(old)
        return True, f"{item} を装備した。" + (f"（{old} を外した）" if old else "")

    eff = info["effect"]
    if eff == "heal":
        gained = p.heal(info["power"])
        p.inventory.remove(item)
        return True, f"{item} を使った。HPが {gained} 回復した。"
    if eff == "full_heal":
        gained = p.heal(p.max_hp)
        p.inventory.remove(item)
        return True, f"エリクサーの輝き！ HPが {gained} 回復した。"
    if eff == "cure_poison":
        if p.has_effect("poison"):
            p.effects = [e for e in p.effects if e.name != "poison"]
            p.inventory.remove(item)
            return True, "毒消し草を噛んだ。毒が消えた。"
        return False, "今は毒に侵されていない。"
    if eff == "buff_atk":
        p.add_effect("buff_atk", 5, info["power"])
        p.inventory.remove(item)
        return True, "力の薬！ 5ターン攻撃力が上昇した。"
    if eff == "buff_def":
        p.add_effect("buff_def", 5, info["power"])
        p.inventory.remove(item)
        return True, "鉄壁の薬！ 5ターン防御力が上昇した。"
    if eff == "escape":
        if not in_combat:
            return False, "戦闘中にしか使えない。"
        p.inventory.remove(item)
        return True, "煙玉を投げつけた！ 視界が遮られる。"
    if eff == "magic":
        if not in_combat or target is None:
            return False, "戦闘中にしか使えない。"
        target.hp -= info["power"]
        p.inventory.remove(item)
        return True, f"魔法の巻物が炸裂！ {target.name} に {info['power']} のダメージ！"
    if eff == "level_up":
        p.exp = p.need_exp()
        msgs = p.gain_exp(0)
        p.inventory.remove(item)
        return True, "賢者の石が砕けた！ " + " ".join(msgs)
    return False, "何も起こらなかった。"

def open_inventory(p: PlayerState, in_combat: bool = False, target: Optional[MonsterTpl] = None) -> Optional[str]:
    if not p.inventory:
        narrate("所持品は空だ。", style="dim")
        return None
    items = list(dict.fromkeys(p.inventory))
    labels = []
    for it in items:
        count = p.inventory.count(it)
        info = ITEMS[it]
        suffix = f" x{count}" if count > 1 else ""
        labels.append(f"{it}{suffix} — {info.get('desc', '')}")
    labels.append("やめる")
    idx = ask_choice(labels, "使うアイテム")
    if idx == len(labels) - 1:
        return None
    item = items[idx]
    consumed, msg = use_item(p, item, in_combat=in_combat, target=target)
    narrate(msg, style="cyan" if consumed else "yellow")
    return item if consumed else None

# =====================================================================
# 戦闘
# =====================================================================
def calc_damage(atk: int, defense: int, variance: float = 0.25) -> int:
    base = max(1, atk - defense // 2)
    spread = max(1, int(base * variance))
    return max(1, base + random.randint(-spread, spread))

def combat(p: PlayerState, m: MonsterTpl, can_flee: bool = True) -> bool:
    console.print(Panel(
        f"[bold red]{m.name}[/bold red] が現れた！\n[italic]{m.flavor}[/italic]\nHP {m.hp}  攻撃 {m.atk}  防御 {m.defense}",
        title="戦闘開始", border_style="red"))

    turn = 0
    while m.hp > 0 and p.hp > 0:
        turn += 1
        hp_color = "green" if p.hp > p.max_hp*0.5 else "yellow" if p.hp > p.max_hp*0.25 else "red"
        console.print(f"\n[bold]── ターン {turn} ──[/bold]   "
                      f"敵HP [red]{m.hp}[/red]   自HP [{hp_color}]{p.hp}/{p.max_hp}[/{hp_color}]")

        opts = ["攻撃", "防御（次のダメージ半減）", "アイテム"]
        if can_flee:
            opts.append("逃げる")
        idx = ask_choice(opts, "戦術")

        defending = False
        skip_enemy = False

        if idx == 0:
            crit = random.random() < 0.10
            dmg = calc_damage(p.atk, m.defense)
            if "dragon" in m.tags and p.weapon == "竜殺しの槍":
                dmg *= 2
                console.print("[bold yellow]竜殺しの槍が輝く！[/bold yellow]")
            if p.weapon == "炎の剣" and random.random() < 0.30:
                dmg += 6
                console.print("[bold red]炎の刃が燃え上がる！[/bold red]")
            if crit:
                dmg = int(dmg * 1.8)
                console.print("[bold magenta]会心の一撃！[/bold magenta]")
            m.hp -= dmg
            console.print(f"あなたの攻撃 → {m.name} に [bold]{dmg}[/bold] ダメージ。")

        elif idx == 1:
            defending = True
            console.print("[cyan]構えを取った。[/cyan]")

        elif idx == 2:
            consumed = open_inventory(p, in_combat=True, target=m)
            if consumed is None:
                skip_enemy = True
            else:
                if consumed == "煙玉":
                    narrate(f"{m.name} を撒いて逃げ切った！")
                    return False
                if m.hp <= 0:
                    break

        elif idx == 3:
            chance = 0.4 + p.level * 0.03
            if random.random() < chance:
                narrate(f"{m.name} を撒いて逃げ切った！")
                return False
            console.print("[red]逃げられなかった！[/red]")

        if skip_enemy:
            continue
        if m.hp <= 0:
            break

        # 敵ターン
        if random.random() < 0.10:
            console.print(f"{m.name} の攻撃は外れた！")
        else:
            edmg = calc_damage(m.atk, p.defense)
            if defending:
                edmg = max(1, edmg // 2)
            p.hp -= edmg
            console.print(f"{m.name} の攻撃 → あなたに [red]{edmg}[/red] ダメージ。")
            if "poison" in m.tags and not p.has_effect("poison") and random.random() < 0.35:
                if p.armor != "聖なる鎧":
                    p.add_effect("poison", 4)
                    console.print("[green]あなたは毒に侵された！[/green]")

        for msg in p.tick_effects():
            console.print(f"[dim]{msg}[/dim]")

    if p.hp <= 0:
        return False

    msgs = [f"[bold green]{m.name} を倒した！[/bold green]",
            f"経験値 {m.exp} と {m.gold}G を得た。"]
    p.gold += m.gold
    for msg in p.gain_exp(m.exp):
        msgs.append(msg)
    for item, prob in m.drops:
        if random.random() < prob:
            p.inventory.append(item)
            msgs.append(f"{m.name} は [cyan]{item}[/cyan] を落とした！")
    console.print(Panel("\n".join(msgs), title="勝利", border_style="green"))
    return True

# =====================================================================
# イベント
# =====================================================================
TREASURE_POOL = [
    ("ポーション", 0.30), ("ハイポーション", 0.10),
    ("毒消し草", 0.15), ("力の薬", 0.06), ("鉄壁の薬", 0.06),
    ("煙玉", 0.10), ("魔法の巻物", 0.08),
    ("鉄の剣", 0.05), ("革の鎧", 0.05),
    ("鋼の剣", 0.02), ("鎖帷子", 0.02),
    ("エリクサー", 0.01),
]

TRAP_TYPES = [
    ("矢の罠",     "壁から無数の矢が飛び出した！", "phys",   12),
    ("毒霧",       "緑の霧が立ち込める。",         "poison", 0),
    ("落とし穴",   "床が抜け、深く転落した！",     "phys",   15),
    ("呪いの石板", "禍々しい紋様が光る。",         "curse",  0),
    ("爆発の罠",   "床のスイッチが弾ける！",       "phys",   20),
]

EVENT_FLAVOR = {
    "monster": ["奥から唸り声が聞こえる。", "血の匂いが漂っている。", "壁に爪痕が刻まれている。"],
    "treasure": ["金属の輝きが見える。", "古い宝箱が安置されている。", "祭壇の上に何かが置かれている。"],
    "empty": ["静寂に包まれた部屋だ。", "苔むした石壁が広がる。", "湿った空気が流れている。"],
    "trap": ["床に違和感がある。", "壁の小穴が並んでいる。", "嫌な予感がする。"],
}

def event_monster(p: PlayerState):
    pool = FLOOR_POOL[floor_tier(p.floor)]
    if random.random() < 0.12 and floor_tier(p.floor) + 1 in FLOOR_POOL:
        pool = FLOOR_POOL[floor_tier(p.floor) + 1]
        console.print("[red]…なにか強い気配がする。[/red]")
    m = make_monster(random.choice(pool))
    flavor = random.choice(EVENT_FLAVOR["monster"])
    narrate(f"{flavor}\n[bold red]{m.name}[/bold red] と遭遇した！", title="モンスター")
    idx = ask_choice(["戦う", "様子を見て逃げる（成功率: 階層が深いほど低下）"])
    if idx == 1:
        chance = max(0.25, 0.7 - p.floor * 0.02)
        if random.random() < chance:
            narrate("そっと後退し、気付かれずに通り抜けた。")
            return
        console.print("[red]気付かれた！[/red]")
    combat(p, m)

def event_treasure(p: PlayerState):
    flavor = random.choice(EVENT_FLAVOR["treasure"])
    narrate(f"{flavor}\n古びた宝箱が部屋の中央に置かれている。", title="宝箱")
    idx = ask_choice(["開ける", "罠を疑って蹴り倒す（罠回避だが破損リスク）", "立ち去る"])
    if idx == 2:
        return
    trapped = random.random() < 0.20 + p.floor * 0.01
    if idx == 1:
        if trapped:
            narrate("蹴り倒した宝箱から針が飛び出すが、当たらなかった！", style="green")
            trapped = False
        else:
            if random.random() < 0.4:
                narrate("中身が壊れてしまった…", style="dim")
                return
    if trapped:
        dmg = random.randint(5, 12)
        p.hp -= dmg
        narrate(f"宝箱は罠だった！ {dmg} のダメージ。", style="red")
        if p.hp <= 0:
            return
    rolls = 1 + (1 if random.random() < 0.3 else 0)
    gained = []
    for _ in range(rolls):
        items, weights = zip(*TREASURE_POOL)
        item = random.choices(items, weights=weights)[0]
        p.inventory.append(item)
        gained.append(item)
    gold = random.randint(5, 15) * p.floor
    p.gold += gold
    narrate(f"{gold}G と {', '.join(gained)} を手に入れた！", style="cyan")

def event_trap(p: PlayerState):
    flavor = random.choice(EVENT_FLAVOR["trap"])
    name, desc, kind, dmg = random.choice(TRAP_TYPES)
    narrate(f"{flavor}\n[yellow]これは…{name}か？[/yellow]", title="罠")
    idx = ask_choice(["慎重に避ける（成功率: 防御依存）",
                      "走って駆け抜ける（半ダメージ）",
                      f"アイテムで対処する（所持品: {len(p.inventory)}）"])
    if idx == 2:
        open_inventory(p)
        idx = ask_choice(["慎重に避ける", "駆け抜ける"])
    success_rate = min(0.85, 0.45 + p.defense * 0.02)
    if idx == 0:
        if random.random() < success_rate:
            narrate(f"{desc} だがあなたは見切って避けた！", style="green")
            p.gain_exp(3)
            return
        narrate(desc, style="red")
        actual = dmg
    else:
        narrate(f"{desc} 駆け抜けた！", style="yellow")
        actual = dmg // 2

    if kind == "phys":
        p.hp -= actual
        console.print(f"[red]{actual} のダメージ。[/red]")
    elif kind == "poison":
        if p.armor == "聖なる鎧":
            console.print("[green]聖なる鎧が霧を弾いた。[/green]")
        else:
            p.add_effect("poison", 5)
            console.print("[green]毒に侵された！[/green]")
    elif kind == "curse":
        loss = min(p.gold, random.randint(10, 30))
        p.gold -= loss
        console.print(f"[magenta]呪いで {loss}G が消失した！[/magenta]")

def event_empty(p: PlayerState):
    flavor = random.choice(EVENT_FLAVOR["empty"])
    narrate(flavor, title="静寂の部屋")
    idx = ask_choice(["休憩する（HP最大値の30%回復）", "探索する", "瞑想する（経験値+5）"])
    if idx == 0:
        gained = p.heal(p.max_hp * 30 // 100)
        narrate(f"少し休んだ。HPが {gained} 回復した。", style="green")
    elif idx == 1:
        if random.random() < 0.5:
            gold = random.randint(3, 10) * p.floor
            p.gold += gold
            narrate(f"床の隙間に{gold}Gを見つけた。", style="cyan")
        else:
            narrate("特に何もなかった。", style="dim")
    else:
        msgs = p.gain_exp(5)
        narrate("精神を研ぎ澄ました。 " + " ".join(msgs), style="cyan")

def event_merchant(p: PlayerState):
    narrate("フードを被った行商人が荷物を広げている。\n「ふむ、生きて帰れる客は久しぶりだ。何を見ていく？」",
            title="行商人", style="cyan")
    pool = ["ポーション", "ハイポーション", "毒消し草", "力の薬",
            "煙玉", "魔法の巻物", "鉄の剣", "鋼の剣", "革の鎧", "鎖帷子"]
    if p.floor >= 8:
        pool += ["炎の剣", "鋼の鎧", "エリクサー"]
    if p.floor >= 14:
        pool += ["竜殺しの槍", "聖なる鎧"]
    stock = [random.choice(pool) for _ in range(5)]
    while True:
        labels = [f"{it}  {ITEMS[it]['price']}G  — {ITEMS[it].get('desc','')}" for it in stock]
        labels.append(f"売る（所持品 {len(p.inventory)}個）")
        labels.append("立ち去る")
        console.print(f"\n[bold]所持金: {p.gold}G[/bold]")
        idx = ask_choice(labels, "商品")
        if idx == len(labels) - 1:
            narrate("「またのご来店を。生きてればな。」")
            return
        if idx == len(labels) - 2:
            if not p.inventory:
                narrate("売れる物が無い。", style="dim")
                continue
            items = list(dict.fromkeys(p.inventory))
            sell_labels = [f"{it} → {ITEMS[it]['price']//2}G" for it in items]
            sell_labels.append("やめる")
            j = ask_choice(sell_labels, "売却")
            if j == len(sell_labels) - 1:
                continue
            sold = items[j]
            p.inventory.remove(sold)
            p.gold += ITEMS[sold]["price"] // 2
            narrate(f"{sold} を {ITEMS[sold]['price']//2}G で売却した。", style="cyan")
            continue
        item = stock[idx]
        price = ITEMS[item]["price"]
        if p.gold < price:
            narrate("「金が足りないようだな。」", style="red")
            continue
        p.gold -= price
        p.inventory.append(item)
        stock.pop(idx)
        narrate(f"{item} を {price}G で購入した。", style="cyan")
        if not stock:
            narrate("「これで打ち止めだ。気をつけてな。」")
            return

def event_shrine(p: PlayerState):
    narrate("古い祭壇から淡い光が漏れている。", title="祭壇", style="magenta")
    idx = ask_choice(["祈る（HP・状態異常完全回復）",
                      "捧げ物をする（所持金の10%で最大HP+5）",
                      "破壊して持ち去る（呪われる可能性）"])
    if idx == 0:
        p.hp = p.max_hp
        p.effects.clear()
        narrate("温かい光に包まれ、心身ともに癒された。", style="green")
    elif idx == 1:
        cost = max(20, p.gold // 10)
        if p.gold < cost:
            narrate("捧げ物が足りなかった…", style="dim")
            return
        p.gold -= cost
        p.max_hp += 5
        p.hp += 5
        narrate(f"{cost}Gを捧げた。最大HPが5上昇した。", style="cyan")
    else:
        if random.random() < 0.4:
            p.gold += 100
            narrate("祭壇から100Gが転がり出た。だが背筋が冷える…", style="yellow")
            if random.random() < 0.5:
                p.add_effect("poison", 8)
                narrate("呪いで毒に侵された！", style="red")
        else:
            narrate("天罰！ 雷が落ちた！", style="red")
            p.hp = max(1, p.hp - 20)
            p.add_effect("poison", 6)

def event_fountain(p: PlayerState):
    narrate("七色に光る泉がある。", title="不思議な泉", style="blue")
    idx = ask_choice(["飲む（ランダム効果）", "見つめる（経験値+10）", "立ち去る"])
    if idx == 2:
        return
    if idx == 1:
        msgs = p.gain_exp(10)
        narrate("古の知恵が流れ込んできた。 " + " ".join(msgs), style="cyan")
        return
    roll = random.random()
    if roll < 0.30:
        p.max_hp += 10
        p.hp = p.max_hp
        narrate("最大HPが10上昇した！", style="green")
    elif roll < 0.55:
        p.base_atk += 2
        narrate("攻撃力が永続的に2上昇した！", style="green")
    elif roll < 0.75:
        p.base_def += 2
        narrate("防御力が永続的に2上昇した！", style="green")
    elif roll < 0.90:
        loss = random.randint(5, 15)
        p.hp = max(1, p.hp - loss)
        narrate(f"水は腐っていた！ {loss}のダメージ。", style="red")
    else:
        p.max_hp = max(10, p.max_hp - 5)
        p.hp = min(p.hp, p.max_hp)
        narrate("最大HPが5下がった…", style="red")

def event_riddle(p: PlayerState):
    riddles = [
        ("「私は食べれば食べるほど大きくなるが、飲めば死ぬ。何だ？」（火/水/影 で答えよ）", "火"),
        ("「重ければ前へ、軽ければ後ろへ。私は何？」（年齢/秘密/影 で答えよ）", "秘密"),
        ("「2の10乗はいくつ？」（数字で）", "1024"),
        ("「黒くして光、白くして闇を成すもの。何？」（墨/影/雲 で答えよ）", "墨"),
        ("「持ち上げれば軽く、長く持つほど重くなる。何？」（息/言葉/羽 で答えよ）", "息"),
    ]
    q, ans = random.choice(riddles)
    narrate(f"スフィンクスが立ち塞がる。\n「謎を解けば富を授け、間違えば命を頂く。」\n\n{q}",
            title="謎かけ", style="magenta")
    answer = Prompt.ask("答え")
    if answer.strip() == ans:
        gold = 50 * p.floor
        p.gold += gold
        msgs = p.gain_exp(20)
        narrate(f"正解！ {gold}Gと深い経験を得た。 " + " ".join(msgs), style="green")
    else:
        narrate(f"不正解！ 答えは「{ans}」だった。スフィンクスが襲いかかる！", style="red")
        m = make_monster("ダークエルフ" if p.floor < 10 else "リッチ")
        m.name = "スフィンクス"
        combat(p, m, can_flee=False)

def event_gamble(p: PlayerState):
    narrate("怪しい二人組がサイコロを転がしている。\n「賭けてみないか？ 倍か無か。」",
            title="賭場", style="yellow")
    if p.gold < 10:
        narrate("（所持金が足りず誘いを断った）", style="dim")
        return
    while p.gold >= 10:
        opts = [f"10G賭ける（勝率45%・倍）"]
        opts.append(f"50G賭ける（勝率40%・倍）" if p.gold >= 50 else "（50Gが足りない）")
        opts.append(f"全額（{p.gold}G）賭ける（勝率30%・倍）")
        opts.append("立ち去る")
        idx = ask_choice(opts)
        if idx == 3:
            return
        if idx == 1 and p.gold < 50:
            continue
        bet, rate = [(10, 0.45), (50, 0.40), (p.gold, 0.30)][idx]
        if random.random() < rate:
            p.gold += bet
            narrate(f"勝った！ {bet}Gを得た。 (現在 {p.gold}G)", style="green")
        else:
            p.gold -= bet
            narrate(f"負けた… {bet}Gを失った。 (現在 {p.gold}G)", style="red")
            if p.gold < 10:
                narrate("「すっからかんか。また来な。」", style="dim")
                return

EVENTS_NORMAL = [
    (event_monster,  35),
    (event_treasure, 14),
    (event_trap,     12),
    (event_empty,    10),
    (event_merchant, 9),
    (event_shrine,   7),
    (event_fountain, 5),
    (event_riddle,   4),
    (event_gamble,   4),
]

def pick_event():
    fns, weights = zip(*EVENTS_NORMAL)
    return random.choices(fns, weights=weights)[0]

def event_boss(p: PlayerState):
    name = boss_for_floor(p.floor)
    m = make_monster(name)
    console.print(Panel(
        f"[bold red]{m.name}[/bold red]\n[italic]{m.flavor}[/italic]\n\n"
        "──── これより先、逃げる事は叶わない。",
        title=f"B{p.floor}F ボス", border_style="red"))
    Prompt.ask("[bold]Enter で戦闘開始[/bold]", default="")
    won = combat(p, m, can_flee=False)
    if won and p.floor == FINAL_FLOOR:
        ending(p)
        sys.exit(0)

# =====================================================================
# タイトル/エンディング
# =====================================================================
TITLE = r"""
   ____            _       _ ____
  / ___| ___ _ __ (_)_ __ (_)  _ \ ___   __ _ _   _  ___
 | |  _ / _ \ '_ \| | '_ \| | |_) / _ \ / _` | | | |/ _ \
 | |_| |  __/ | | | | | | | |  _ < (_) | (_| | |_| |  __/
  \____|\___|_| |_|_|_| |_|_|_| \_\___/ \__, |\__,_|\___|
                                        |___/
"""

def title_screen() -> PlayerState:
    console.clear()
    console.print(Align.center(Text(TITLE, style="bold magenta")))
    console.print(Align.center(Text(
        f"〜 全{FINAL_FLOOR}階の迷宮で魔王ザロスを討て 〜", style="dim")))
    console.print()
    name = Prompt.ask("[bold]主人公の名前[/bold]", default="冒険者")
    cls_options = []
    for k, v in CLASSES.items():
        cls_options.append(f"{k}（HP{v['hp']} / 攻{v['atk']} / 防{v['defense']} / 金{v['gold']}G / 装備:{', '.join(v['start'])}）")
    idx = ask_choice(cls_options, "クラス選択")
    cls = list(CLASSES.keys())[idx]
    cfg = CLASSES[cls]
    p = PlayerState(
        name=name, cls=cls,
        hp=cfg["hp"], max_hp=cfg["hp"],
        base_atk=cfg["atk"], base_def=cfg["defense"],
        gold=cfg["gold"], inventory=list(cfg["start"]),
    )
    for it in list(p.inventory):
        info = ITEMS[it]
        if info["category"] == "weapon" and not p.weapon:
            p.weapon = it
            p.inventory.remove(it)
        elif info["category"] == "armor" and not p.armor:
            p.armor = it
            p.inventory.remove(it)
    return p

def ending(p: PlayerState):
    console.clear()
    console.print(Align.center(Text("✦ ✦ ✦  GAME CLEAR  ✦ ✦ ✦", style="bold yellow")))
    console.print()
    score = p.gold + p.level * 100 + p.max_hp * 5
    t = Table(title="冒険の記録", border_style="green")
    t.add_column("項目", style="cyan")
    t.add_column("値",   style="magenta")
    t.add_row("勇者", f"{p.name} ({p.cls})")
    t.add_row("最終レベル", str(p.level))
    t.add_row("最大HP", str(p.max_hp))
    t.add_row("攻/防", f"{p.atk} / {p.defense}")
    t.add_row("装備", f"{p.weapon or '—'} / {p.armor or '—'}")
    t.add_row("所持金", f"{p.gold} G")
    t.add_row("到達階", f"{p.floor}F")
    t.add_row("総合スコア", f"[bold yellow]{score}[/bold yellow]")
    console.print(t)
    console.print("\n[italic]魔王ザロスは塵となって消えた。\n地上に光が戻り、勇者の伝説が始まる──[/italic]\n")

def game_over(p: PlayerState):
    console.print()
    console.print(Align.center(Text("☠  YOU DIED  ☠", style="bold red")))
    console.print()
    score = p.gold + p.level * 50 + p.floor * 30
    console.print(Panel(
        f"到達 {p.floor}F   Lv{p.level}   {p.gold}G   スコア [bold yellow]{score}[/bold yellow]",
        title="冒険の記録", border_style="red"))

# =====================================================================
# メインループ
# =====================================================================
def main():
    try:
        p = title_screen()
        while p.hp > 0:
            console.clear()
            console.print(render_status(p))

            if p.floor in BOSS_FLOORS:
                event_boss(p)
            else:
                with console.status("[green]次の部屋を探索中…[/green]"):
                    fn = pick_event()
                fn(p)

            if p.hp > 0 and p.effects:
                msgs = p.tick_effects()
                for msg in msgs:
                    console.print(f"[dim]{msg}[/dim]")

            if p.hp <= 0:
                game_over(p)
                return

            console.print()
            choices = ["次の階へ進む", "アイテムを使う", "ステータス確認"]
            while True:
                idx = ask_choice(choices)
                if idx == 0:
                    break
                if idx == 1:
                    open_inventory(p)
                else:
                    console.print(render_status(p))
            p.floor += 1
    except KeyboardInterrupt:
        console.print("\n[dim]冒険を中断した。[/dim]")

if __name__ == "__main__":
    main()
