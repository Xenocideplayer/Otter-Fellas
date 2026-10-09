"""Generates the Otters mod data from Timberborn's own blueprints.

    python3 build_mod.py <vanilla blueprints dir> <output mod dir> <Otters.dll> [otter model dir]

The optional model dir is the output of model/build_models.py (otter bodies, fur textures). Without it the
otters keep the beaver body.

New buildings start as copies of vanilla ones (so models, colliders and nav meshes are the game's own), and
otter-only tweaks to vanilla content are written as faction blueprint modifiers, which the game applies only in
Otter colonies.
"""
import copy
import csv
import io
import json
import os
import shutil
import sys

VANILLA = sys.argv[1]
OUT_ROOT = sys.argv[2]
DLL = sys.argv[3]
MODEL_DIR = sys.argv[4] if len(sys.argv) > 4 else None
GAME_VERSION_DIR = "version-1.1"
OUT = os.path.join(OUT_ROOT, GAME_VERSION_DIR)

MOD_VERSION = "1.0.0"
MOD_ID = "Otters.WaterFaction"
MODIFIERS = "OttersModifiers"

written = []


def load(path):
    with open(os.path.join(VANILLA, path + ".json"), encoding="utf-8-sig") as f:
        return json.load(f)


def write(rel, data):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    written.append(rel)


# ---------------------------------------------------------------------------------------------------------
# Tuning, all in one place
# ---------------------------------------------------------------------------------------------------------
LAND_SPEED = {"BeaverAdult": (2.3, 1.15), "BeaverChild": (1.15, 0.55)}  # vanilla 2.7/1.35 and 1.35/0.65
SWIM_SPEED_MULTIPLIER = 1.8          # in water: 2.3 * (1 - 0.3 swim penalty) * 1.8 = 2.9, faster than on land
OTTER_MODELS = {"BeaverAdult": "Characters/Otters/OtterAdult.Model", "BeaverChild": "Characters/Otters/OtterChild.Model"}
ADULT_TEXTURES = [f"Characters/Otters/Textures/OtterAdult{i}" for i in range(1, 5)]
CHILD_TEXTURES = [f"Characters/Otters/Textures/OtterChild{i}" for i in range(1, 4)]
# The beaver material's normal/AO/metal maps are painted for the beaver's UV layout; otters swap in neutral ones
# (their painted fur already carries the shading).
OTTER_MATERIAL = {"NormalMap": "Characters/Otters/Textures/OtterFlatNormal",
                  "OcclusionMap": "Characters/Otters/Textures/OtterNoOcclusion",
                  "MetallicMap": "Characters/Otters/Textures/OtterNoMetal"}

MOISTURE_DAILY_DELTA = -0.3          # full to bone dry in about 3.3 days without water
MOISTURE_SOAK_PER_HOUR = 1.0         # an hour in the water refills it
DRY_WORK_PENALTY = -0.15             # working speed while bone dry

SCIENCE_DISCOUNTS = {                # Folktails blueprint -> science cost for otters
    "Buildings/Landscaping/Levee/Levee.Folktails.blueprint": 0,
    "Buildings/Landscaping/Floodgate/Floodgate.Folktails.blueprint": 0,
    "Buildings/Landscaping/DoubleFloodgate/DoubleFloodgate.Folktails.blueprint": 100,
    "Buildings/Landscaping/TripleFloodgate/TripleFloodgate.Folktails.blueprint": 250,
    "Buildings/Landscaping/FillValve/FillValve.Folktails.blueprint": 150,
    "Buildings/Landscaping/ThrottlingValve/ThrottlingValve.Folktails.blueprint": 250,
    "Buildings/Food/AquaticFarmhouse/AquaticFarmhouse.Folktails.blueprint": 0,
    "Buildings/Water/LargeWaterPump/LargeWaterPump.Folktails.blueprint": 200,
    "Buildings/Wellbeing/Shower/Shower.Folktails.blueprint": 0,
    "Buildings/Wellbeing/Lido/Lido.Folktails.blueprint": 150,
}
MOISTURE_SOURCES = {                 # attractions that also refill otter moisture (points per hour)
    "Buildings/Wellbeing/Shower/Shower.Folktails.blueprint": 1.5,
    "Buildings/Wellbeing/Lido/Lido.Folktails.blueprint": 0.8,
    "Buildings/Wellbeing/DomedGarden/DomedGarden.Folktails.blueprint": 0.6,
}
CROP_GROWTH_DAYS = {                 # aquatic crops grow ~25% faster for otters
    "NaturalResources/Crops/Cattail/Cattail.blueprint": 6.0,      # vanilla 8
    "NaturalResources/Crops/Spadderdock/Spadderdock.blueprint": 9.0,  # vanilla 12
}
REMOVED_FOLKTAILS_BUILDINGS = ["Buildings/Wellbeing/Herbalist/Herbalist.Folktails.blueprint"]
REMOVED_GOODS = ["Antidote"]
REMOVED_NEEDS = ["Antidote"]

DIG_SITE = "Buildings/Landscaping/OtterDigSite/OtterDigSite.Otters.blueprint"
REED_FILTER = "Buildings/Water/ReedFilter/ReedFilter.Otters.blueprint"
RINSE_POD = "Buildings/Wellbeing/RinsePod/RinsePod.Otters.blueprint"

TEXT = {
    "Faction.Otters.DisplayName": "Otters",
    "Faction.Otters.Description": "Sleek river folk who would rather swim than walk. Otters dig, filter and farm the "
                                  "water from day one, but they are slow on land and work slower once their fur "
                                  "dries out.",
    "Faction.Otters.GameOver.Message": "The rivers ran dry, and your Otters with them. This is the end.",
    "Faction.Otters.GameOver.Flavor": "No current runs forever.",
    "Faction.Otters.WonderCompletionMessage": "Congratulations! You mastered the Otters' water-bound ways and used "
                                              "this map's rivers to build the faction's wonder.",
    "Faction.Otters.WonderCompletionFlavor": "The rivers run clean again, and every one of them leads home.",
    "Need.OtterMoisture.DisplayName": "Moisture",
    "Status.Need.OtterMoisture": "Dry fur: works slower until wet again.",
    "Building.OtterDigSite.DisplayName": "Dig Site",
    "Building.OtterDigSite.Description": "Builders dig out the block of terrain underneath. No explosives, and the "
                                         "digging waits until nobody is standing on the spot.",
    "Building.OtterDigSite.FlavorDescription": "\"Why blow it up when you can just dig?\"",
    "Building.ReedFilter.DisplayName": "Reed Filter",
    "Building.ReedFilter.Description": "Turns badwater at its intake into clean water without lowering the river. "
                                       "Cleans faster the dirtier the water is.",
    "Building.ReedFilter.FlavorDescription": "The reeds don't mind the taste.",
    "Building.RinsePod.DisplayName": "Rinse Pod",
    "Building.RinsePod.Description": "A long soak in clean water that washes badwater contamination out of an "
                                     "otter's fur. Uses water.",
    "Building.RinsePod.FlavorDescription": "In through the badwater, out through the rinse.",
    "Recipe.OtterWaterFiltering": "Filtering water",
}


# ---------------------------------------------------------------------------------------------------------
# Faction
# ---------------------------------------------------------------------------------------------------------
def modifier_path(original, name):
    return f"{MODIFIERS}/{name}.Otters.optional.blueprint"


def build_faction(modifiers):
    folk = load("Factions/Faction.Folktails.blueprint")
    f = copy.deepcopy(folk["FactionSpec"])
    f.update({
        "Id": "Otters",
        "Order": 2,
        "Avatar": "Sprites/Avatars/OttersAdult",
        "ChildAvatar": "Sprites/Avatars/OttersChild",
        "BotAvatar": "Sprites/Avatars/FolktailsBot",
        "ContaminatedAdultAvatar": "Sprites/Avatars/OttersContaminatedAdult",
        "ContaminatedChildAvatar": "Sprites/Avatars/OttersContaminatedChild",
        "Logo": "Sprites/Avatars/OttersLogo",
        "NewGameFullAvatar": "Sprites/Avatars/OttersFullNewGame",
        # The pod model is the Iron Teeth one, so their materials are needed too.
        "MaterialCollectionIds": ["Folktails", "IronTeeth"],
        "TemplateCollectionIds": ["Buildings.Otters", "Characters.Folktails", "ModularShaftParts.Folktails",
                                  "NaturalResources.Folktails"],
        "NeedCollectionIds": ["Otters"],
        "GoodCollectionIds": ["Otters"],
        "BlueprintModifiers": [{"Original": o, "Modifier": m} for o, m in modifiers],
        **({"Textures": ADULT_TEXTURES, "ChildTextures": CHILD_TEXTURES} if MODEL_DIR else {}),
        "DisplayNameLocKey": "Faction.Otters.DisplayName",
        "DescriptionLocKey": "Faction.Otters.Description",
        "GameOverMessageLocKey": "Faction.Otters.GameOver.Message",
        "GameOverFlavorLocKey": "Faction.Otters.GameOver.Flavor",
    })
    wonder = copy.deepcopy(folk["FactionWonderSpec"])
    wonder["WonderCompletionFlavorLocKey"] = "Faction.Otters.WonderCompletionFlavor"
    wonder["WonderCompletionMessageLocKey"] = "Faction.Otters.WonderCompletionMessage"
    write("Factions/Faction.Otters.blueprint.json",
          {"FactionSpec": f, "StartingFactionSpec": {}, "FactionWonderSpec": wonder})


def build_collections():
    buildings = load("TemplateCollections/TemplateCollection.Buildings.Folktails.blueprint")["TemplateCollectionSpec"]
    blueprints = [b for b in buildings["Blueprints"] if b not in REMOVED_FOLKTAILS_BUILDINGS]
    blueprints += [DIG_SITE, REED_FILTER, RINSE_POD]
    write("TemplateCollections/TemplateCollection.Buildings.Otters.blueprint.json",
          {"TemplateCollectionSpec": {"CollectionId": "Buildings.Otters", "Blueprints": blueprints}})

    goods = load("GoodCollections/GoodCollection.Folktails.blueprint")["GoodCollectionSpec"]["Goods"]
    write("GoodCollections/GoodCollection.Otters.blueprint.json",
          {"GoodCollectionSpec": {"CollectionId": "Otters", "Goods": [g for g in goods if g not in REMOVED_GOODS]}})

    needs = load("NeedCollections/NeedCollection.Folktails.blueprint")["NeedCollectionSpec"]["Needs"]
    needs = [n for n in needs if n not in REMOVED_NEEDS] + ["OtterMoisture"]
    write("NeedCollections/NeedCollection.Otters.blueprint.json",
          {"NeedCollectionSpec": {"CollectionId": "Otters", "Needs": sorted(needs)}})


# ---------------------------------------------------------------------------------------------------------
# Moisture need: dries out over time, refilled by swimming and by showers/lido/domed garden
# ---------------------------------------------------------------------------------------------------------
def build_moisture_need():
    wet = load("Needs/Need.Beaver.WetFur.blueprint")["NeedSpec"]
    need = copy.deepcopy(wet)
    need.update({
        "Id": "OtterMoisture",
        "BackwardCompatibleIds": [],
        "Order": 55,
        "StartingValue": 1.0,
        "MinimumValue": 0.0,
        "MaximumValue": 1.0,
        "DailyDelta": MOISTURE_DAILY_DELTA,
        "Wastable": True,
        "DisplayNameLocKey": "Need.OtterMoisture.DisplayName",
        "FavorableWellbeing": 0,
        "UnfavorableWellbeing": 0,
    })
    write("Needs/Need.Beaver.OtterMoisture.blueprint.json", {
        "NeedSpec": need,
        "NeedAffectedBySoakednessSpec": {"PointsPerHour": MOISTURE_SOAK_PER_HOUR},
        "CriticalNeedSpec": {
            "CriticalNeedType": "State",
            "SpriteName": "OtterDryFur",
            "DescriptionLocKey": "Status.Need.OtterMoisture",
            "DescriptionShortLocKey": "",
        },
        "PunitiveNeedSpec": {"Penalties": [{"Id": "WorkingSpeed", "MultiplierDelta": DRY_WORK_PENALTY}]},
    })


# ---------------------------------------------------------------------------------------------------------
# New buildings
# ---------------------------------------------------------------------------------------------------------
def labeled(spec, key, icon):
    spec["DisplayNameLocKey"] = f"Building.{key}.DisplayName"
    spec["DescriptionLocKey"] = f"Building.{key}.Description"
    spec["FlavorDescriptionLocKey"] = f"Building.{key}.FlavorDescription"
    spec["Icon"] = icon


def build_dig_site():
    bp = copy.deepcopy(load("Buildings/Landscaping/Dynamite/Dynamite.Folktails.blueprint"))
    bp["BuildingSpec"].update({"SelectionSoundName": "Default", "BuildingCost": [], "ScienceCost": 0,
                               "FinishableWithBeaversOnSite": True})
    bp["TemplateSpec"]["TemplateName"] = "OtterDigSite.Otters"
    bp["TemplateSpec"]["BackwardCompatibleTemplateNames"] = []
    del bp["DynamiteSpec"]
    bp["OtterDigSiteSpec"] = {"Depth": 1}
    bp["ConstructionSiteBuildTimeSpec"] = {"ConstructionTimeInHours": 4.0}
    bp["PlaceableBlockObjectSpec"]["ToolOrder"] = 79
    labeled(bp["LabeledEntitySpec"], "OtterDigSite", "Buildings/Landscaping/OtterDigSite/OtterDigSiteIcon")
    # Look: a marked plot of ground instead of a stick of dynamite. The finished state lasts a moment.
    base = "ConstructionBases/ConstructionBase1x1Dynamite/ConstructionBase1x1Dynamite.blueprint"
    base_bp = load(base)
    unfinished = bp["Children"]["#Unfinished"]["Children"]
    unfinished.pop("ConstructionStage0", None)
    assert list(unfinished) == ["ConstructionBase1x1Dynamite#nested"], unfinished.keys()
    bp["ConstructionSiteProgressVisualizerSpec"] = {"ProgressThresholds": []}
    bp["Children"]["#Finished"] = {"TimbermeshSpec": base_bp["TimbermeshSpec"],
                                   "CollidersSpec": base_bp["CollidersSpec"]}
    write(DIG_SITE + ".json", order_specs(bp))


def build_reed_filter():
    bp = copy.deepcopy(load("Buildings/Water/BadwaterPump/BadwaterPump.Folktails.blueprint"))
    bp["BuildingSpec"].update({"BuildingCost": [{"Id": "Log", "Amount": 20}], "ScienceCost": 0})
    bp["ManufactorySpec"]["ProductionRecipeIds"] = ["OtterWaterFiltering"]
    del bp["ManufactoryWaterContaminationConsumerSpec"]
    bp["ReedFilterSpec"] = {"WaterPerCycle": 1.0, "MinimumContamination": 0.01}
    bp["TemplateSpec"]["TemplateName"] = "ReedFilter.Otters"
    bp["TemplateSpec"]["BackwardCompatibleTemplateNames"] = []
    bp["PlaceableBlockObjectSpec"]["ToolOrder"] = 11
    labeled(bp["LabeledEntitySpec"], "ReedFilter", "Buildings/Water/ReedFilter/ReedFilterIcon")
    write(REED_FILTER + ".json", order_specs(bp))

    write("Recipes/Recipe.OtterWaterFiltering.blueprint.json", {"RecipeSpec": {
        "Id": "OtterWaterFiltering",
        "BackwardCompatibleIds": [],
        "DisplayLocKey": "Recipe.OtterWaterFiltering",
        "CycleDurationInHours": 1.0,
        "Ingredients": [],
        "Products": [],
        "ProducedSciencePoints": 0,
        "Fuel": "",
        "CyclesFuelLasts": 0,
        "FuelCapacity": 0,
        "CyclesCapacity": 1,
        "Icon": "Sprites/Goods/WaterIcon",
    }})


def build_rinse_pod():
    bp = copy.deepcopy(load("Buildings/Wellbeing/DecontaminationPod/DecontaminationPod.IronTeeth.blueprint"))
    bp["BuildingSpec"].update({"BuildingCost": [{"Id": "Plank", "Amount": 20}, {"Id": "Gear", "Amount": 5}],
                               "ScienceCost": 550})
    bp["AttractionSpec"]["Effects"] = [
        {"NeedId": "BadwaterContamination", "PointsPerHour": 0.1, "SatisfyToMaxValue": False}]
    bp["GoodConsumingBuildingSpec"] = {"FullInventoryWorkHours": 50,
                                       "ConsumedGoods": [{"GoodId": "Water", "GoodPerHour": 0.5}]}
    # Runs on water alone: no power connection.
    for spec in ("PoweredGoodConsumingBuildingSpec", "MechanicalBuildingSpec", "MechanicalNodeSpec",
                 "MechanicalConnectorTargetSpec", "TransputProviderSpec"):
        bp.pop(spec)
    bp["TemplateSpec"]["TemplateName"] = "RinsePod.Otters"
    bp["TemplateSpec"]["BackwardCompatibleTemplateNames"] = []
    labeled(bp["LabeledEntitySpec"], "RinsePod", "Buildings/Wellbeing/RinsePod/RinsePodIcon")
    write(RINSE_POD + ".json", order_specs(bp))


def order_specs(bp):
    # Keep Children last, as the game's own files do.
    children = bp.pop("Children", None)
    if children is not None:
        bp["Children"] = children
    return bp


# ---------------------------------------------------------------------------------------------------------
# Otter-only tweaks to vanilla content (faction blueprint modifiers)
# ---------------------------------------------------------------------------------------------------------
def build_modifiers():
    mods = []

    def add(original, name, content):
        path = modifier_path(original, name)
        load(original)  # fail loudly if the vanilla blueprint moved
        write(path + ".json", content)
        mods.append((original, path))

    for character, (walk, slowed) in LAND_SPEED.items():
        content = {
            "WalkerSpeedManagerSpec": {"BaseWalkingSpeed": walk, "BaseSlowedSpeed": slowed},
            "OtterSwimmerSpec": {"SwimSpeedMultiplier": SWIM_SPEED_MULTIPLIER},
        }
        if MODEL_DIR:
            content["OtterMaterialSpec"] = OTTER_MATERIAL
            content["Children"] = {"Model_Preserved": {"TimbermeshSpec": {"Model": OTTER_MODELS[character]}}}
        add(f"Characters/Beaver/{character}.blueprint", f"Characters/{character}", content)

    buildings = sorted(set(SCIENCE_DISCOUNTS) | set(MOISTURE_SOURCES))
    for original in buildings:
        content = {}
        if original in SCIENCE_DISCOUNTS:
            content["BuildingSpec"] = {"ScienceCost": SCIENCE_DISCOUNTS[original]}
        if original in MOISTURE_SOURCES:
            vanilla_effects = load(original)["AttractionSpec"]["Effects"]
            assert vanilla_effects, original
            content["AttractionSpec"] = {"Effects#append": [
                {"NeedId": "OtterMoisture", "PointsPerHour": MOISTURE_SOURCES[original], "SatisfyToMaxValue": False}]}
        name = original.split("/")[-1].replace(".blueprint", "")
        add(original, f"Buildings/{name}", content)

    for original, days in CROP_GROWTH_DAYS.items():
        name = original.split("/")[-1].replace(".blueprint", "")
        add(original, f"NaturalResources/{name}", {"GrowableSpec": {"GrowthTimeInDays": days}})
    return mods


# ---------------------------------------------------------------------------------------------------------
# Text, manifest, code
# ---------------------------------------------------------------------------------------------------------
def build_localization():
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["ID", "Text", "Comment"])
    for key, text in TEXT.items():
        w.writerow([key, text, ""])
    path = os.path.join(OUT, "Localizations", "enUS_Otters.csv")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(buf.getvalue())
    written.append("Localizations/enUS_Otters.csv")


def build_manifest():
    write("manifest.json", {
        "Name": "Otters",
        "Version": MOD_VERSION,
        "Id": MOD_ID,
        "MinimumGameVersion": "1.1.2.0",
        "Description": "A third faction of otters: water specialists who dig, filter badwater and farm aquatic "
                       "crops from day one. They swim faster than they walk, work slower when their fur dries "
                       "out, and cure contamination in a clean-water Rinse Pod.",
        "RequiredMods": [],
        "OptionalMods": [],
    })


def copy_models():
    """Otter bodies (.timbermesh), fur textures and the neutral material maps."""
    from PIL import Image
    dst = os.path.join(OUT, "Characters", "Otters")
    os.makedirs(os.path.join(dst, "Textures"), exist_ok=True)
    for name in ("OtterAdult.Model.timbermesh", "OtterChild.Model.timbermesh"):
        shutil.copy(os.path.join(MODEL_DIR, name), os.path.join(dst, name))
        written.append(f"Characters/Otters/{name}")
    for tex in ADULT_TEXTURES + CHILD_TEXTURES:
        name = tex.split("/")[-1] + ".png"
        shutil.copy(os.path.join(MODEL_DIR, "textures", name), os.path.join(dst, "Textures", name))
        written.append(f"{tex}.png")
    maps = {"OtterFlatNormal": ((128, 128, 255, 255), {"isNormalMap": True}),
            "OtterNoOcclusion": ((255, 255, 255, 255), {"linear": True}),
            "OtterNoMetal": ((0, 0, 0, 0), {"linear": True})}
    for name, (rgba, meta) in maps.items():
        path = os.path.join(dst, "Textures", name + ".png")
        Image.new("RGBA", (4, 4), rgba).save(path)
        with open(path + ".meta.json", "w") as f:
            json.dump(meta, f, indent=2)
        written.append(f"Characters/Otters/Textures/{name}.png")


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    modifiers = build_modifiers()
    build_faction(modifiers)
    build_collections()
    build_moisture_need()
    build_dig_site()
    build_reed_filter()
    build_rinse_pod()
    build_localization()
    build_manifest()
    if MODEL_DIR:
        copy_models()
    shutil.copy(DLL, os.path.join(OUT, "Otters.dll"))
    written.append("Otters.dll")
    print("\n".join(sorted(written)))


if __name__ == "__main__":
    main()
