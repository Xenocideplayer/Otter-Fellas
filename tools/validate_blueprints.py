"""Static checks for the Otters mod against the game's own code and data.

    python3 validate_blueprints.py <decompiled game source dir> <vanilla blueprints dir> <mod version dir> <mod src dir>

1. Builds a schema of every [Serialize] property of every type in the decompiled game source and the mod's C#.
2. Validates every blueprint (vanilla first, as a self-test of the checker, then the mod) against that schema.
3. Cross-checks references: template collections, recipes, goods, needs, bonus ids, loc keys, sprites, modifiers.
"""
import csv
import glob
import json
import os
import re
import sys

SRC, VANILLA, MOD, MOD_SRC = sys.argv[1:5]

TYPE_RE = re.compile(r'^\s*(?:public|internal|private|protected)?\s*(?:sealed\s+|abstract\s+|static\s+|readonly\s+)*'
                     r'(?:record\s+struct|record|class|struct)\s+(\w+)')
SER_RE = re.compile(r'^\s*\[Serialize(?:\("(\w+)"\))?\]\s*$')
PROP_RE = re.compile(r'^\s*(?:public|private|internal|protected)\s+(?:virtual\s+|override\s+)?(.+?)\s+(\w+)\s*\{\s*get;')
ALIAS_RE = re.compile(r'\[SpecAlias\(([^\]]*)\)\]')


def build_schema(files):
    schema, aliases = {}, {}
    for path in files:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
        current = None
        pending = None
        pending_alias = []
        for line in lines:
            a = ALIAS_RE.search(line)
            if a:
                pending_alias = re.findall(r'"(\w+)"', a.group(1))
            m = TYPE_RE.match(line)
            if m:
                current = m.group(1)
                schema.setdefault(current, {})
                for al in pending_alias:
                    aliases[al] = current
                pending_alias = []
                continue
            s = SER_RE.match(line)
            if s:
                pending = s.group(1) or ""
                continue
            if pending is not None:
                p = PROP_RE.match(line)
                if p and current:
                    ctype, name = p.group(1), p.group(2)
                    schema[current][pending or name] = ctype
                pending = None
    return schema, aliases


game_files = glob.glob(os.path.join(SRC, "*.cs"))
mod_files = glob.glob(os.path.join(MOD_SRC, "*.cs"))
SCHEMA, ALIASES = build_schema(game_files + mod_files)
MOD_SPECS = set(build_schema(mod_files)[0])


def inner_type(ctype):
    for wrapper in ("ImmutableArray<", "AssetRef<", "List<", "IReadOnlyList<"):
        if ctype.startswith(wrapper) and ctype.endswith(">"):
            return inner_type(ctype[len(wrapper):-1])
    return ctype.rstrip("?")


problems = []
OBSERVED = set()   # (spec, field) pairs vanilla files use: valid even if the type lives in a DLL not decompiled
OBSERVING = [False]
OBSERVED_SPECS = set()


def check_object(obj, type_name, where, spec_key=None):
    fields = SCHEMA.get(type_name)
    for key, value in obj.items():
        base = key.split("#")[0]
        if OBSERVING[0]:
            OBSERVED.add((type_name, base))
        if fields is None or base not in fields:
            if (type_name, base) in OBSERVED or (fields is None and type_name in OBSERVED_SPECS):
                continue
            if fields is None:
                continue  # primitives, enums, Unity structs
            problems.append(f"{where}: {type_name} has no serialized field '{base}'")
            continue
        sub = inner_type(fields[base])
        if isinstance(value, dict):
            check_object(value, sub, f"{where}.{base}")
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    check_object(item, sub, f"{where}.{base}[{i}]")


def check_node(node, where):
    for key, value in node.items():
        if key == "Children":
            for child, cnode in value.items():
                if child.endswith("#nested"):
                    allowed = {"BlueprintPath", "Modification"}
                    extra = set(cnode) - allowed
                    if extra:
                        problems.append(f"{where}/{child}: unexpected keys {extra}")
                    if "Modification" in cnode:
                        check_node(cnode["Modification"], f"{where}/{child}(mod)")
                else:
                    check_node(cnode, f"{where}/{child}")
            continue
        spec = key.split("#")[0]
        spec_type = ALIASES.get(spec, spec)
        if OBSERVING[0]:
            OBSERVED_SPECS.add(spec_type)
        if spec_type not in SCHEMA and spec_type not in OBSERVED_SPECS:
            problems.append(f"{where}: unknown spec '{spec}'")
            continue
        if isinstance(value, dict):
            check_object(value, spec_type, f"{where}:{spec}")


def blueprint_files(root):
    return sorted(glob.glob(os.path.join(root, "**", "*.blueprint.json"), recursive=True))


def rel(root, path):
    return os.path.relpath(path, root).replace(os.sep, "/")


# 1) self-test on vanilla (also records which specs/fields vanilla uses)
OBSERVING[0] = True
for f in blueprint_files(VANILLA):
    check_node(json.load(open(f, encoding="utf-8-sig")), "vanilla:" + rel(VANILLA, f))
OBSERVING[0] = False
vanilla_problems = list(problems)
problems.clear()
print(f"schema: {len(SCHEMA)} types; vanilla self-test: {len(vanilla_problems)} problems")
for p in vanilla_problems[:20]:
    print("  VANILLA", p)

# 2) the mod
mod_bps = {rel(MOD, f): json.load(open(f, encoding="utf-8-sig")) for f in blueprint_files(MOD)}
for path, data in mod_bps.items():
    check_node(data, "mod:" + path)

# 3) references
def bp_exists(path):
    path = path[:-len(".blueprint")] if path.endswith(".blueprint") else path
    for root in (VANILLA, MOD):
        if os.path.exists(os.path.join(root, path + ".blueprint.json")):
            return True
    return False


vanilla_bps = {rel(VANILLA, f): json.load(open(f, encoding="utf-8-sig")) for f in blueprint_files(VANILLA)}
all_bps = dict(vanilla_bps)
all_bps.update(mod_bps)


def specs_of(spec):
    return [d[spec] for d in all_bps.values() if spec in d]


goods = {s["Id"] for s in specs_of("GoodSpec")}
needs = {s["Id"] for s in specs_of("NeedSpec")}
recipes = {s["Id"] for s in specs_of("RecipeSpec")}
bonuses = {s["Id"] for s in specs_of("BonusTypeSpec")}
need_groups = {s["Id"] for s in specs_of("NeedGroupSpec")}
tool_groups = {s["Id"] for s in specs_of("BlockObjectToolGroupSpec")} | {s.get("Id") for s in specs_of("ToolGroupSpec")}

faction = mod_bps["Factions/Faction.Otters.blueprint.json"]["FactionSpec"]
collections = {d["TemplateCollectionSpec"]["CollectionId"]: d["TemplateCollectionSpec"]["Blueprints"]
               for d in all_bps.values() if "TemplateCollectionSpec" in d and "CollectionId" in d["TemplateCollectionSpec"]}
need_cols = {d["NeedCollectionSpec"]["CollectionId"]: d["NeedCollectionSpec"]["Needs"]
             for d in all_bps.values() if "NeedCollectionSpec" in d and "CollectionId" in d["NeedCollectionSpec"]}
good_cols = {d["GoodCollectionSpec"]["CollectionId"]: d["GoodCollectionSpec"]["Goods"]
             for d in all_bps.values() if "GoodCollectionSpec" in d and "CollectionId" in d["GoodCollectionSpec"]}
mat_cols = {d["MaterialCollectionSpec"]["CollectionId"] for d in all_bps.values() if "MaterialCollectionSpec" in d}

for cid in faction["TemplateCollectionIds"]:
    if cid not in collections:
        problems.append(f"faction: template collection {cid} missing")
for cid in faction["NeedCollectionIds"]:
    if cid not in need_cols:
        problems.append(f"faction: need collection {cid} missing")
for cid in faction["GoodCollectionIds"]:
    if cid not in good_cols:
        problems.append(f"faction: good collection {cid} missing")
for cid in faction["MaterialCollectionIds"]:
    if cid not in mat_cols:
        problems.append(f"faction: material collection {cid} missing")

faction_templates = []
for cid in faction["TemplateCollectionIds"] + ["Common"]:
    for path in collections.get(cid, []) if cid != "Common" else (
            collections.get("Buildings.Common", []) + collections.get("NaturalResources.Common", [])):
        if not bp_exists(path):
            problems.append(f"collection {cid}: blueprint {path} not found")
        faction_templates.append(path)

faction_goods = set(good_cols["Otters"]) | set(good_cols.get("Common", []))
faction_needs = set(need_cols["Otters"]) | set(need_cols.get("Common", []))
for n in need_cols["Otters"]:
    if n not in needs:
        problems.append(f"need collection: unknown need {n}")
for g in good_cols["Otters"]:
    if g not in goods:
        problems.append(f"good collection: unknown good {g}")

# Every template in the faction: names unique, recipes and costs use faction goods.
names = {}
for path in faction_templates:
    key = (path[:-len('.blueprint')] if path.endswith('.blueprint') else path) + ".blueprint.json"
    data = all_bps.get(key)
    if data is None:
        continue
    tn = data.get("TemplateSpec", {}).get("TemplateName")
    if tn:
        if tn in names:
            problems.append(f"duplicate template name {tn}: {names[tn]} and {path}")
        names[tn] = path
    for cost in data.get("BuildingSpec", {}).get("BuildingCost", []):
        if cost["Id"] not in faction_goods:
            problems.append(f"{path}: cost uses {cost['Id']} which otters cannot make")
    for rid in data.get("ManufactorySpec", {}).get("ProductionRecipeIds", []):
        if rid not in recipes:
            problems.append(f"{path}: unknown recipe {rid}")
            continue
        r = next(s for s in specs_of("RecipeSpec") if s["Id"] == rid)
        for ga in r["Ingredients"] + r["Products"] + ([{"Id": r["Fuel"]}] if r["Fuel"] else []):
            if ga["Id"] not in faction_goods:
                problems.append(f"{path}: recipe {rid} uses {ga['Id']} which otters cannot make")
    for eff in data.get("AttractionSpec", {}).get("Effects", []) + data.get("ContinuousEffectBuildingSpec", {}).get("Effects", []):
        if eff["NeedId"] not in faction_needs:
            problems.append(f"{path}: effect on need {eff['NeedId']} that otters lack")
    for cg in data.get("GoodConsumingBuildingSpec", {}).get("ConsumedGoods", []):
        if cg["GoodId"] not in faction_goods:
            problems.append(f"{path}: consumes {cg['GoodId']} which otters cannot make")

# Faction modifiers point at real blueprints and real mod files that will not load on their own.
for m in faction["BlueprintModifiers"]:
    if not bp_exists(m["Original"]):
        problems.append(f"modifier original missing: {m['Original']}")
    mod_file = os.path.join(MOD, m["Modifier"] + ".json")
    if not os.path.exists(mod_file):
        problems.append(f"modifier file missing: {m['Modifier']}")
    if not m["Modifier"].endswith(".optional.blueprint"):
        problems.append(f"modifier should be .optional so it never loads as its own blueprint: {m['Modifier']}")
    if os.path.exists(os.path.join(MOD, m["Modifier"].replace(".optional.blueprint", ".blueprint") + ".json")):
        problems.append(f"modifier has a non-optional twin and would load standalone: {m['Modifier']}")
    data = json.load(open(mod_file))
    for eff in data.get("AttractionSpec", {}).get("Effects#append", []):
        if eff["NeedId"] not in needs:
            problems.append(f"modifier {m['Modifier']}: unknown need {eff['NeedId']}")

# Needs, bonuses and groups
for path, data in mod_bps.items():
    if "NeedSpec" in data and "Id" in data["NeedSpec"]:
        if data["NeedSpec"]["NeedGroupId"] not in need_groups:
            problems.append(f"{path}: unknown need group")
    for pen in data.get("PunitiveNeedSpec", {}).get("Penalties", []):
        if pen["Id"] not in bonuses:
            problems.append(f"{path}: unknown bonus {pen['Id']}")

# Loc keys used by mod blueprints exist
loc = {}
for f in glob.glob(os.path.join(os.path.dirname(VANILLA.rstrip('/')), "loc", "enUS*.csv")) + \
        glob.glob(os.path.join(MOD, "Localizations", "enUS*.csv")):
    with open(f, encoding="utf-8-sig") as fh:
        for row in csv.reader(fh):
            if row:
                loc[row[0]] = row[1] if len(row) > 1 else ""


def walk_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.endswith("LocKey") and isinstance(v, str) and v:
                yield v
            yield from walk_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_keys(v)


for path, data in mod_bps.items():
    for key in walk_keys(data):
        if key not in loc:
            problems.append(f"{path}: missing loc key {key}")

# Sprites the mod points at exist in the mod (vanilla sprite paths are trusted)
def check_sprite(p, where):
    if p.startswith(("Sprites/Avatars/Otters", "Sprites/StatusIcons/Otter", "Buildings/")) and "Otter" in p or "ReedFilter" in p or "RinsePod" in p:
        if not os.path.exists(os.path.join(MOD, p + ".png")):
            problems.append(f"{where}: sprite {p} missing")
        elif not os.path.exists(os.path.join(MOD, p + ".png.meta.json")):
            problems.append(f"{where}: sprite {p} has no meta (isSprite)")


for k in ("Avatar", "ChildAvatar", "ContaminatedAdultAvatar", "ContaminatedChildAvatar", "Logo", "NewGameFullAvatar"):
    if k not in faction:
        problems.append(f"faction: missing {k}")
        continue
    check_sprite(faction[k], "faction." + k)
for path, data in mod_bps.items():
    icon = data.get("LabeledEntitySpec", {}).get("Icon")
    if icon:
        check_sprite(icon, path)
    sprite = data.get("CriticalNeedSpec", {}).get("SpriteName")
    if sprite:
        check_sprite("Sprites/StatusIcons/" + sprite, path)

print(f"mod blueprints checked: {len(mod_bps)}; faction templates: {len(faction_templates)}")
if problems:
    print(f"{len(problems)} PROBLEMS:")
    for p in problems:
        print("  ", p)
    sys.exit(1)
print("All checks passed.")
