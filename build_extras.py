"""Extra Otter content: the Tube Valve, the Clam Bed (with clams and grilled clams) and the otters' own wonder, the
Wellspring. Called from build_mod.py:

    import build_extras
    extras = build_extras.build_all(sys.modules[__name__])

build_all writes the blueprints through build_mod's helpers and returns what build_mod still has to wire up:
    buildings      blueprint paths (no .json) for TemplateCollection.Buildings.Otters
    goods, needs   ids for the otter good / need collections
    grill_recipes  recipe ids the otter Grill should offer
    text           loc key -> English text for every key used here
    models         (mod folder, file name) pairs to copy from <model dir>/buildings (built by model/make_extras.py)
    icons          (function in art/icons_extras.py, size, path relative to the version folder);
                   size 112 = building icon, 80 = good icon, 512 = status icon -- icons_extras.render(name, size)
    wonder         FactionWonderSpec for the otter faction
    omit_folktails Folktails blueprints otters get no copy of (the Folktails wonder: they get their own)
"""
import os

TUBE_VALVE = "Buildings/Water/TubeValve/TubeValve.Otters.blueprint"
CLAM_BED = "Buildings/Food/ClamBed/ClamBed.Otters.blueprint"
WELLSPRING = "Buildings/Monuments/Wellspring/Wellspring.Otters.blueprint"
FOLKTAILS_WONDER = "Buildings/Monuments/EarthRecultivator/EarthRecultivator.Folktails.blueprint"

# Tuning
VALVE_COST = [{"Id": "Plank", "Amount": 3}, {"Id": "Gear", "Amount": 1}, {"Id": "MetalBlock", "Amount": 1}]
CLAM_BED_COST = [{"Id": "Log", "Amount": 30}, {"Id": "Plank", "Amount": 8}]
CLAM_BED_SCIENCE = 80
CLAM_HOURS = 3.0                     # one gathering cycle (work-hours at full speed)...
CLAMS_PER_CYCLE = 2                  # ...brings up two clams (fish: one per 2.5 h, but clams are pickier)
CLAM_MIN_DEPTH = 0.5                 # blocks of water over the riverbed
CLAM_MAX_CONTAMINATION = 0.2         # clean water only: full speed at 0 %, nothing at 20 % badwater or more
GRILLED_CLAMS = (2, 3)               # 2 clams -> 3 grilled clams
WONDER_COST = [{"Id": "Gear", "Amount": 1600}, {"Id": "TreatedPlank", "Amount": 2400},
               {"Id": "MetalBlock", "Amount": 1500}]          # Folktails: 2000 / 2000 / 1500
WONDER_GOODS = [{"Id": "Extract", "Amount": 500}, {"Id": "SmokedFish", "Amount": 500}]  # Folktails: Extract + Paper
WONDER_MOISTURE = 1.0                # moisture points per hour for otters in range while the wonder runs

TEXT = {
    "Building.TubeValve.DisplayName": "Tube Valve",
    "Building.TubeValve.Description": "A length of Water Tube with a hand wheel. Pause it to close it: no water gets "
                                      "past it, so outlets beyond it go dry and the rest of the line shares the well's "
                                      "water. If every outlet on a well's line is closed off, the well stops pumping "
                                      "instead of spilling behind it. Paused Tube Outlets get no water either.",
    "Building.TubeValve.FlavorDescription": "Righty-tighty, lefty-loosey.",
    "Status.ArtesianWell.Closed": "Every Tube Outlet on this well's line is paused or closed off by a Tube Valve, "
                                  "so the water stays in the well.",
    "Status.ArtesianWell.Closed.Short": "Well's tube line is closed",
    "Building.ClamBed.DisplayName": "Clam Bed",
    "Building.ClamBed.Description": "A staked net over the riverbed where a gatherer raises clams. Build it with its "
                                    "deck on the bank and its bed over water one block down. Needs at least half a "
                                    "block of water over the bed, and clean water: the more badwater, the fewer clams, "
                                    "and none at all at 20% badwater. Takes no water from the river.",
    "Building.ClamBed.FlavorDescription": "Happy as a clam, as long as the water's clean.",
    "Recipe.OtterClamming": "Gathering clams",
    "Status.ClamBed.NoWater": "No clams: the bed needs at least half a block of clean water (under 20% badwater) over it.",
    "Status.ClamBed.NoWater.Short": "Clam bed needs clean water",
    "Good.Clams.DisplayName": "Clams",
    "Good.Clams.PluralDisplayName": "Clams",
    "Good.GrilledClams.DisplayName": "Grilled clams",
    "Good.GrilledClams.PluralDisplayName": "Grilled clams",
    "Building.Wellspring.DisplayName": "The Wellspring",
    "Building.Wellspring.Description": "The Otters' wonder: a great log fountain that lifts the river into a bowl high "
                                       "above the town and pours it back in four streams, with a holt on top. Once "
                                       "finished and stocked with extract and smoked fish it can be activated, filling "
                                       "every otter nearby with awe and keeping their fur wet.",
    "Building.Wellspring.FlavorDescription": "Every river starts somewhere. This one starts here.",
}


def _clean(spec_list):
    return [dict(x) for x in spec_list]


def _box(cx, cy, cz, sx, sy, sz):
    return {"Center": {"X": cx, "Y": cy, "Z": cz}, "Size": {"X": sx, "Y": sy, "Z": sz}}


def _colliders(boxes, spheres=()):
    return {"BoxColliders": [_box(*b) for b in boxes],
            "SphereColliders": [{"Center": {"X": x, "Y": y, "Z": z}, "Radius": r} for x, y, z, r in spheres],
            "CapsuleColliders": []}


def _block(occ, below="Any"):
    return {"MatterBelow": below, "Occupations": occ, "Stackable": "None", "OccupyAllBelow": False, "Underground": False}


# ---------------------------------------------------------------------------------------------------- valve
def build_tube_valve(bm):
    bp = bm.copy.deepcopy(bm.load("Buildings/Paths/Tubeway/Tubeway.IronTeeth.blueprint"))
    bp["TemplateSpec"].update({"TemplateName": "TubeValve.Otters", "BackwardCompatibleTemplateNames": []})
    bp["BuildingSpec"].update({"BuildingCost": _clean(VALVE_COST), "ScienceCost": 0,
                               "FinishableWithBeaversOnSite": False})
    for spec in ("BlockObjectNavMeshSettingsSpec", "BlockObjectWithPathRangeSpec", "PathSpec", "TubeModelSpec",
                 "TubeSpec", "MovementSpeedBoostingBuildingSpec"):
        del bp[spec]
    bp["BlockObjectSpec"]["Blocks"][0]["Occupations"] = "Bottom, Middle"
    bp["WaterTubeSpec"] = {"ModelPrefix": "Variant_"}       # same tube models and joining as the Water Tube
    bp["WaterTubeValveSpec"] = {"OpenMarkerName": "ValveOpenTag", "ClosedMarkerName": "ValveClosedTag"}
    if bm.MODEL_DIR:
        bp["Children"]["#Finished"].setdefault("Children", {})["OtterValveWheel"] = {
            "TimbermeshSpec": {"Model": "Buildings/Water/TubeValve/TubeValveWheel.Otters.Model"}}
    bp["PlaceableBlockObjectSpec"].update({"ToolGroupId": "Water", "ToolOrder": 104, "Layout": "Single"})
    bm.labeled(bp["LabeledEntitySpec"], "TubeValve", "Buildings/Water/TubeValve/TubeValveIcon")
    bm.write(TUBE_VALVE + ".json", bm.order_specs(bp))


# ---------------------------------------------------------------------------------------------------- clam bed
def build_clam_bed(bm):
    pump = bm.load("Buildings/Water/WaterPump/WaterPump.Folktails.blueprint")
    pool = bm.load("Buildings/Wellbeing/SwimmingPool/SwimmingPool.IronTeeth.blueprint")
    bp = bm.copy.deepcopy(pump)
    bp["TemplateSpec"].update({"TemplateName": "ClamBed.Otters", "BackwardCompatibleTemplateNames": []})
    bp["BuildingSpec"].update({"BuildingCost": _clean(CLAM_BED_COST), "ScienceCost": CLAM_BED_SCIENCE,
                               "LoopingSoundName": ""})
    bp["ManufactorySpec"]["ProductionRecipeIds"] = ["OtterClamming"]
    for spec in ("ManufactoryWaterConsumerSpec", "WorkshopAnimationControllerSpec", "WaterInputSpec",
                 "WaterInputPipeSpec", "WorkshopWorkerHiderSpec"):
        bp.pop(spec, None)
    # The gatherer stays in view at the end of the walkway, digging for clams.
    bp["TransformSlotInitializerSpec"]["Slots"] = [
        {"SlotKeyword": "Entrance", "Animation": "Planting", "Inanimate": False, "RandomizeYRotation": False,
         "WaterSlot": False}]
    # Laid out like the Swimming Pool: a deck row on the bank, two rows of bed one block down in the water.
    full = "Bottom, Top, Corners, Path, Middle"
    layers = [[["None"] * 3, [full] * 3, [full] * 3],                 # z0: the bed, in the water
              [[full] * 3, ["Bottom"] * 3, ["Bottom"] * 3]]          # z1: ground level (deck on the bank)
    blocks = []
    for z, layer in enumerate(layers):
        for y, row in enumerate(layer):
            for occ in row:
                blocks.append(_block(occ, "GroundOrStackable" if (z, y) == (1, 0) else "Any"))
    bp["BlockObjectSpec"] = bm.copy.deepcopy(pool["BlockObjectSpec"])
    bp["BlockObjectSpec"].update({"Size": {"X": 3, "Y": 3, "Z": 2}, "Blocks": blocks,
                                  "Entrance": {"HasEntrance": True, "Coordinates": {"X": 1, "Y": -1, "Z": 1}},
                                  "BaseZ": 1})
    bp["BlockObjectNavMeshSettingsSpec"] = bm.copy.deepcopy(pool["BlockObjectNavMeshSettingsSpec"])
    bp["BuildingAccessibleSpec"] = bm.copy.deepcopy(pool["BuildingAccessibleSpec"])
    bp["PlaceableBlockObjectSpec"] = bm.copy.deepcopy(pool["PlaceableBlockObjectSpec"])
    bp["PlaceableBlockObjectSpec"].update({"ToolGroupId": "Food", "ToolOrder": 13})
    bp["ClamBedSpec"] = {"WaterCoordinates": {"X": 1, "Y": 2, "Z": 0}, "MinWaterDepth": CLAM_MIN_DEPTH,
                         "MaxContamination": CLAM_MAX_CONTAMINATION, "StatusIcon": "OtterClamBedNoWater",
                         "StatusLocKey": "Status.ClamBed.NoWater", "StatusShortLocKey": "Status.ClamBed.NoWater.Short"}
    walls = [(0.07, -0.35, 2.0, 0.14, 1.3, 2.0), (2.93, -0.35, 2.0, 0.14, 1.3, 2.0), (1.5, -0.35, 2.94, 3.0, 1.3, 0.14)]
    bp["Children"] = {
        "#Finished": {"TimbermeshSpec": {"Model": "Buildings/Food/ClamBed/ClamBed.Otters.Model"},
                      "CollidersSpec": _colliders([(1.5, 0.1, 0.5, 3.0, 0.2, 1.0), (1.5, 0.06, 1.8, 0.6, 0.14, 1.6)]
                                                  + walls)},
        "#Unfinished": {"Children": {
            "ConstructionBase3x1#nested": {"BlueprintPath": "ConstructionBases/ConstructionBase3x1/ConstructionBase3x1.blueprint"},
            "ConstructionStage0": {"TimbermeshSpec": {"Model": "Buildings/Food/ClamBed/ClamBed.Otters.ConstructionStage0.Model"},
                                   "CollidersSpec": _colliders([(1.5, 0.1, 0.5, 3.0, 0.2, 1.0)])}}}}
    bp["ConstructionSiteProgressVisualizerSpec"] = {"ProgressThresholds": [0.0]}
    bm.labeled(bp["LabeledEntitySpec"], "ClamBed", "Buildings/Food/ClamBed/ClamBedIcon")
    bm.write(CLAM_BED + ".json", bm.order_specs(bp))

    water = bm.load("Recipes/Recipe.Water.blueprint")["RecipeSpec"]
    bm.write("Recipes/Recipe.OtterClamming.blueprint.json", {"RecipeSpec": {
        **bm.copy.deepcopy(water), "Id": "OtterClamming", "BackwardCompatibleIds": [],
        "DisplayLocKey": "Recipe.OtterClamming", "CycleDurationInHours": CLAM_HOURS, "Ingredients": [],
        "Products": [{"Id": "Clams", "Amount": CLAMS_PER_CYCLE}], "CyclesCapacity": 10,
        "Icon": "Sprites/Goods/ClamsIcon"}})

    clams = bm.copy.deepcopy(bm.load("Goods/Good.Carrot.blueprint"))
    clams["GoodSpec"].update({"Id": "Clams", "Icon": "Sprites/Goods/ClamsIcon", "GoodOrder": 9016,
                              "ContainerColor": {"r": 0.58, "g": 0.56, "b": 0.54, "a": 1.0},
                              "ConsumptionEffects": [{"NeedId": "Hunger", "Points": 0.3}, {"NeedId": "Clams", "Points": 0.2}],
                              "DisplayNameLocKey": "Good.Clams.DisplayName",
                              "PluralDisplayNameLocKey": "Good.Clams.PluralDisplayName"})
    bm.write("Goods/Good.Clams.blueprint.json", clams)
    need = bm.copy.deepcopy(bm.load("Needs/Need.Beaver.Carrots.blueprint"))
    need["NeedSpec"].update({"Id": "Clams", "Order": 12, "DisplayNameLocKey": "Good.Clams.PluralDisplayName"})
    bm.write("Needs/Need.Beaver.Clams.blueprint.json", need)

    grilled = bm.copy.deepcopy(bm.load("Goods/Good.GrilledSpadderdock.blueprint"))
    grilled["GoodSpec"].update({"Id": "GrilledClams", "Icon": "Sprites/Goods/GrilledClamsIcon", "GoodOrder": 9048,
                                "ConsumptionEffects": [{"NeedId": "Hunger", "Points": 0.3},
                                                       {"NeedId": "GrilledClams", "Points": 0.2}],
                                "DisplayNameLocKey": "Good.GrilledClams.DisplayName",
                                "PluralDisplayNameLocKey": "Good.GrilledClams.PluralDisplayName"})
    bm.write("Goods/Good.GrilledClams.blueprint.json", grilled)
    need = bm.copy.deepcopy(bm.load("Needs/Need.Beaver.GrilledSpadderdock.blueprint"))
    need["NeedSpec"].update({"Id": "GrilledClams", "Order": 57, "DisplayNameLocKey": "Good.GrilledClams.PluralDisplayName"})
    bm.write("Needs/Need.Beaver.GrilledClams.blueprint.json", need)
    recipe = bm.copy.deepcopy(bm.load("Recipes/Recipe.GrilledSpadderdock.blueprint"))
    recipe["RecipeSpec"].update({"Id": "GrilledClams", "BackwardCompatibleIds": [],
                                 "DisplayLocKey": "Good.GrilledClams.PluralDisplayName", "CycleDurationInHours": 0.5,
                                 "Ingredients": [{"Id": "Clams", "Amount": GRILLED_CLAMS[0]}],
                                 "Products": [{"Id": "GrilledClams", "Amount": GRILLED_CLAMS[1]}],
                                 "Icon": "Sprites/Goods/GrilledClamsIcon"})
    bm.write("Recipes/Recipe.GrilledClams.blueprint.json", recipe)


# ---------------------------------------------------------------------------------------------------- wonder
def build_wellspring(bm):
    folk = bm.load(FOLKTAILS_WONDER)
    bp = bm.copy.deepcopy(folk)
    bp["TemplateSpec"].update({"TemplateName": "Wellspring.Otters", "BackwardCompatibleTemplateNames": []})
    bp["BuildingSpec"]["BuildingCost"] = _clean(WONDER_COST)
    bp.pop("BuildingModelGroundCutoffSpec")          # targets a node of the Folktails model ("#Screw_Animated")
    bp["WonderInventorySpec"]["RequiredGoods"] = _clean(WONDER_GOODS)
    bp["WonderEffectControllerSpec"]["Effects"] = [
        {"NeedId": "Wellspring", "PointsPerHour": 10.0, "SatisfyToMaxValue": False},
        {"NeedId": "OtterMoisture", "PointsPerHour": WONDER_MOISTURE, "SatisfyToMaxValue": False}]
    # The Folktails sky lanterns rise from the top of the holt when the wonder is activated.
    for att in bp["TemplateAttachmentsSpec"]["Attachments"]:
        att["Position"] = {"X": 3.5, "Y": 6.0, "Z": 3.5}
    bm.labeled(bp["LabeledEntitySpec"], "Wellspring", "Buildings/Monuments/Wellspring/WellspringIcon")
    model = "Buildings/Monuments/Wellspring/Wellspring.Otters"
    plinth = [(3.5, 0.5, 3.5, 6.8, 1.0, 4.8), (3.5, 0.5, 3.5, 4.8, 1.0, 6.8), (3.5, 0.5, 3.5, 6.0, 1.0, 6.0)]
    low = [(x, 0.05, z, sx, 0.1, sz) for x, _, z, sx, _, sz in plinth]
    half = [(x, 0.3, z, sx, 0.6, sz) for x, _, z, sx, _, sz in plinth]
    pool = (3.5, 1.3, 3.5, 5.4, 0.6, 5.4)
    stages = {
        0: _colliders(low),
        1: _colliders(half + [(3.5, 0.7, 3.5, 1.3, 1.4, 1.3)]),
        2: _colliders(plinth + [(3.5, 2.0, 3.5, 1.3, 2.0, 1.3)]),
        3: _colliders(plinth + [pool, (3.5, 2.4, 3.5, 1.3, 2.8, 1.3), (3.5, 4.0, 3.5, 4.4, 0.9, 4.4)]),
    }
    bp["Children"] = {
        "#Finished": {"TimbermeshSpec": {"Model": model + ".Model"},
                      "CollidersSpec": _colliders(plinth + [pool, (3.5, 2.4, 3.5, 1.3, 2.8, 1.3),
                                                            (3.5, 4.1, 3.5, 4.4, 1.1, 4.4), (3.5, 6.0, 3.5, 0.1, 2.4, 0.1)],
                                                  [(3.5, 5.0, 3.5, 1.1)])},
        "#Unfinished": {"Children": {
            f"ConstructionStage{k}": {"TimbermeshSpec": {"Model": f"{model}.ConstructionStage{k}.Model"},
                                      "CollidersSpec": c} for k, c in stages.items()}}}
    # the first child counts as the construction base: one threshold fewer than stages, like the Folktails wonder
    assert len(bp["ConstructionSiteProgressVisualizerSpec"]["ProgressThresholds"]) == len(stages) - 1
    bm.write(WELLSPRING + ".json", bm.order_specs(bp))

    need = bm.copy.deepcopy(bm.load("Needs/Need.Beaver.EarthRecultivator.blueprint"))
    need["NeedSpec"].update({"Id": "Wellspring", "BackwardCompatibleIds": [],
                             "DisplayNameLocKey": "Building.Wellspring.DisplayName"})
    bm.write("Needs/Need.Beaver.Wellspring.blueprint.json", need)


def build_all(bm):
    build_tube_valve(bm)
    build_clam_bed(bm)
    build_wellspring(bm)
    folk_wonder = bm.load("Factions/Faction.Folktails.blueprint")["FactionWonderSpec"]
    models = [("Buildings/Water/TubeValve", "TubeValveWheel.Otters.Model.timbermesh"),
              ("Buildings/Food/ClamBed", "ClamBed.Otters.Model.timbermesh"),
              ("Buildings/Food/ClamBed", "ClamBed.Otters.ConstructionStage0.Model.timbermesh"),
              ("Buildings/Monuments/Wellspring", "Wellspring.Otters.Model.timbermesh")]
    models += [("Buildings/Monuments/Wellspring", f"Wellspring.Otters.ConstructionStage{k}.Model.timbermesh")
               for k in range(4)]
    if bm.MODEL_DIR:
        missing = [n for _, n in models if not os.path.exists(os.path.join(bm.MODEL_DIR, "buildings", n))]
        assert not missing, f"run model/make_extras.py first, missing {missing}"
    return {
        "buildings": [TUBE_VALVE, CLAM_BED, WELLSPRING],
        "goods": ["Clams", "GrilledClams"],
        "needs": ["Clams", "GrilledClams", "Wellspring"],
        "grill_recipes": ["GrilledClams"],
        "text": dict(TEXT),
        "models": models,
        "icons": [("tube_valve", 112, "Buildings/Water/TubeValve/TubeValveIcon.png"),
                  ("clam_bed", 112, "Buildings/Food/ClamBed/ClamBedIcon.png"),
                  ("wellspring", 112, "Buildings/Monuments/Wellspring/WellspringIcon.png"),
                  ("clams_good", 80, "Sprites/Goods/ClamsIcon.png"),
                  ("grilled_clams_good", 80, "Sprites/Goods/GrilledClamsIcon.png"),
                  ("clam_bed_no_water_symbol", 512, "Sprites/StatusIcons/OtterClamBedNoWater.png")],
        "wonder": {"WonderCompletionImage": folk_wonder["WonderCompletionImage"],
                   "WonderLaunchSound": folk_wonder["WonderLaunchSound"],
                   "WonderCompletionFlavorLocKey": "Faction.Otters.WonderCompletionFlavor",
                   "WonderCompletionMessageLocKey": "Faction.Otters.WonderCompletionMessage"},
        "omit_folktails": [FOLKTAILS_WONDER],
    }
