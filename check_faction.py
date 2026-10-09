"""Checks that the built Otters mod is a self-contained faction, separated from Folktails and Iron Teeth the way those
two are from each other (what Timber Together's mixed-faction games rely on).

    python3 check_faction.py /root/vanilla/bp dist/Otters/version-1.1

1. No Otters template collection lists a blueprint that a Folktails or Iron Teeth collection lists, except natural
   resources (trees and bushes maps place) and blueprints the two vanilla factions share themselves; the shared ones
   are printed.
2. Every TemplateName (and backward-compatible name) in the mod is unique across mod + vanilla, and no mod file
   replaces a vanilla one.
3. No blueprint modifiers: no .optional.blueprint.json files, no FactionSpec.BlueprintModifiers.
4. Every Icon, *LocKey and Model the mod's blueprints reference exists (in the mod, or used by vanilla blueprints /
   vanilla localization), and so do the faction's avatars, fur textures and otter material maps.
5. The faction has exactly one adult, child, bot and power-shaft parts template of its own, its starting building is
   its own, its workplaces' worker outfits exist for Otters, its planters can plant every crop it lists, and spec
   fields naming templates point at templates the faction has.
"""
import csv
import glob
import json
import os
import sys

VANILLA, MOD = sys.argv[1], sys.argv[2]
LOC_DIR = os.path.join(os.path.dirname(VANILLA.rstrip("/")), "loc")
problems = []


def load_tree(root):
    out = {}
    for f in glob.glob(os.path.join(root, "**", "*.json"), recursive=True):
        rel = os.path.relpath(f, root).replace(os.sep, "/")
        if not rel.endswith(".blueprint.json"):
            continue
        with open(f, encoding="utf-8-sig") as fh:
            out[rel[:-len(".json")]] = json.load(fh)
    return out


vanilla = load_tree(VANILLA)
mod = load_tree(MOD)
everything = dict(vanilla)
everything.update(mod)


def collections(tree):
    out = {}
    for data in tree.values():
        spec = data.get("TemplateCollectionSpec")
        if spec:
            out.setdefault(spec["CollectionId"], []).extend(spec["Blueprints"])
    return out


all_collections = collections(everything)
factions = {d["FactionSpec"]["Id"]: d["FactionSpec"] for d in everything.values() if "FactionSpec" in d}
otters = factions["Otters"]


def listed(faction):
    return [b for cid in faction["TemplateCollectionIds"] for b in all_collections.get(cid, [])]


# 1) nothing listed by Otters and a vanilla faction, bar natural resources and what vanilla shares itself ----------
otter_bps = listed(otters)
folk_bps, iron_bps = set(listed(factions["Folktails"])), set(listed(factions["IronTeeth"]))
vanilla_shared = folk_bps & iron_bps
shared = []
for bp in otter_bps:
    owners = [f for f, s in (("Folktails", folk_bps), ("IronTeeth", iron_bps)) if bp in s]
    if not owners:
        continue
    if bp.startswith("NaturalResources/") or bp in vanilla_shared:
        shared.append((bp, owners))
    else:
        problems.append(f"Otters list {bp}, which {'/'.join(owners)} list too")
if len(otter_bps) != len(set(otter_bps)):
    problems.append("an Otters collection lists a blueprint twice")
for cid in otters["TemplateCollectionIds"]:
    if cid in factions["Folktails"]["TemplateCollectionIds"] or cid in factions["IronTeeth"]["TemplateCollectionIds"]:
        problems.append(f"Otters use the vanilla collection {cid}")
print("Shared with vanilla factions (allowed):")
for bp, owners in shared:
    print(f"   {bp}  (also {', '.join(owners)})")

# 2) template names unique -----------------------------------------------------------------------------------------
for path in mod:
    if path in vanilla:
        problems.append(f"mod file replaces the vanilla blueprint {path}")
names = {}
for path, data in everything.items():
    spec = data.get("TemplateSpec")
    if not spec:
        continue
    for name in [spec["TemplateName"]] + list(spec.get("BackwardCompatibleTemplateNames") or []):
        names.setdefault(name, []).append(path)
dupes = {n: p for n, p in names.items() if len(p) > 1 and any(x in mod for x in p)}
for n, p in sorted(dupes.items()):
    problems.append(f"template name {n} used by {p}")

# 3) no modifiers ----------------------------------------------------------------------------------------------------
optional = glob.glob(os.path.join(MOD, "**", "*.optional.blueprint.json"), recursive=True)
for f in optional:
    problems.append(f"modifier file left: {os.path.relpath(f, MOD)}")
if otters.get("BlueprintModifiers"):
    problems.append("FactionSpec.BlueprintModifiers is not empty")

# 4) references exist ------------------------------------------------------------------------------------------------
loc = set()
for f in glob.glob(os.path.join(LOC_DIR, "enUS*.csv")) + glob.glob(os.path.join(MOD, "Localizations", "enUS*.csv")):
    with open(f, encoding="utf-8-sig") as fh:
        loc.update(row[0] for row in csv.reader(fh) if row)


def strings(node, key=None):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from strings(v, k)
    elif isinstance(node, list):
        for v in node:
            yield from strings(v, key)
    elif isinstance(node, str):
        yield key, node


vanilla_strings = {v for data in vanilla.values() for _, v in strings(data)}


def asset_exists(path, extensions):
    return path in vanilla_strings or any(os.path.exists(os.path.join(MOD, path + e)) for e in extensions)


checked = {"Icon": 0, "LocKey": 0, "Model": 0, "other assets": 0}
for path, data in mod.items():
    for key, value in strings(data):
        if not value or key is None:
            continue
        if key.endswith("LocKey"):
            checked["LocKey"] += 1
            if value not in loc:
                problems.append(f"{path}: loc key {value} missing")
        elif key == "Icon":
            checked["Icon"] += 1
            if not asset_exists(value, (".png",)):
                problems.append(f"{path}: icon {value} missing")
        elif key == "Model":
            checked["Model"] += 1
            if not asset_exists(value, (".timbermesh",)):
                problems.append(f"{path}: model {value} missing")
        elif key in ("NormalMap", "OcclusionMap", "MetallicMap"):
            checked["other assets"] += 1
            if not asset_exists(value, (".png",)):
                problems.append(f"{path}: texture {value} missing")
for key in ("Avatar", "ChildAvatar", "BotAvatar", "ContaminatedAdultAvatar", "ContaminatedChildAvatar", "Logo",
            "NewGameFullAvatar"):
    checked["other assets"] += 1
    if not asset_exists(otters[key], (".png",)):
        problems.append(f"faction {key} {otters[key]} missing")
for tex in otters.get("Textures", []) + otters.get("ChildTextures", []):
    checked["other assets"] += 1
    if not asset_exists(tex, (".png",)):
        problems.append(f"faction texture {tex} missing")

# 5) the faction's own pieces ----------------------------------------------------------------------------------------
common = all_collections.get("Common", [])
own = [everything.get(b) for b in otter_bps]
missing = [b for b, d in zip(otter_bps, own) if d is None]
for b in missing:
    problems.append(f"collection blueprint {b} not found")
templates = [d for d in own if d is not None] + [everything[b] for b in common if b in everything]
for spec in ("AdultSpec", "ChildSpec", "BotSpec", "ModularShaftPartsSpec"):
    holders = [b for b, d in zip(otter_bps, own) if d and spec in d]
    common_holders = [b for b in common if spec in everything.get(b, {})]
    if len(holders) + len(common_holders) != 1:
        problems.append(f"{spec}: {len(holders) + len(common_holders)} templates ({holders + common_holders})")
    elif not holders:
        problems.append(f"{spec}: only a common template")
    elif holders[0] in folk_bps | iron_bps:
        problems.append(f"{spec}: {holders[0]} is shared with a vanilla faction")
own_names = {d["TemplateSpec"]["TemplateName"] for d in own if d and "TemplateSpec" in d}
common_names = {everything[b]["TemplateSpec"]["TemplateName"] for b in common
                if b in everything and "TemplateSpec" in everything[b]}
if otters["StartingBuildingId"] not in own_names:
    problems.append(f"starting building {otters['StartingBuildingId']} is not an Otters template")

outfits = {(d["WorkerOutfitSpec"]["Id"], d["WorkerOutfitSpec"]["WorkerType"]): d["WorkerOutfitSpec"]["FactionId"]
           for d in everything.values() if "WorkerOutfitSpec" in d and d["WorkerOutfitSpec"]["FactionId"] == "Otters"}
folk_outfits = {(d["WorkerOutfitSpec"]["Id"], d["WorkerOutfitSpec"]["WorkerType"])
                for d in vanilla.values() if d.get("WorkerOutfitSpec", {}).get("FactionId") == "Folktails"}
if set(outfits) != folk_outfits:
    problems.append(f"Otters outfits {sorted(outfits)} differ from Folktails' {sorted(folk_outfits)}")
used = {d["WorkplaceWorkerOutfitSpec"]["WorkerOutfit"] for d in own if d and "WorkplaceWorkerOutfitSpec" in d}
for outfit in sorted(u for u in used if u):
    if (outfit, "Beaver") not in outfits:
        problems.append(f"no Otters beaver outfit {outfit}")

groups = {d["PlanterBuildingSpec"]["PlantableResourceGroup"] for d in templates if "PlanterBuildingSpec" in d}
for b, d in zip(otter_bps, own):
    if d and "PlantableSpec" in d and d["PlantableSpec"]["ResourceGroup"] not in groups:
        problems.append(f"{b}: no Otters building plants resource group {d['PlantableSpec']['ResourceGroup']}")

faction_names = own_names | common_names
map_editor = {everything[b]["TemplateSpec"]["TemplateName"] for cid, bps in all_collections.items()
              for b in bps if b in everything and "TemplateSpec" in everything[b] and b.startswith("MapEditor/")}
folk_names = {everything[b]["TemplateSpec"]["TemplateName"] for b in folk_bps - iron_bps
              if b in everything and "TemplateSpec" in everything[b]} - faction_names
ref_count = 0
for b, d in zip(otter_bps, own):
    if not d:
        continue
    for key, value in strings(d):
        if key and "TemplateName" in key and key != "TemplateName":
            ref_count += 1
            if value not in faction_names | map_editor:
                problems.append(f"{b}: {key} names {value}, which otters don't have")
        # goods, sounds and recipes may share a name with a template (Wheat, Detailer.Folktails, Bot.Folktails)
        if value in folk_names and key not in ("Id", "GoodId", "SelectionSoundName", "ProductionRecipeIds"):
            problems.append(f"{b}: {key} = {value} names a Folktails-only template")

print(f"Otters: {len(otter_bps)} templates in {otters['TemplateCollectionIds']}; {len(shared)} shared; "
      f"{len(outfits)} outfits; planter groups {sorted(groups)}; {ref_count} template references; "
      f"checked refs {checked}")
if problems:
    print(f"{len(problems)} PROBLEMS:")
    for p in problems:
        print("  ", p)
    sys.exit(1)
print("Faction checks passed.")
