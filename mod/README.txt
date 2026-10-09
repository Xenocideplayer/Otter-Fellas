OTTERS - a water faction for Timberborn (built for game version 1.1.2.x)
=========================================================================

INSTALL
  Put this "Otters" folder in:  Documents\Timberborn\Mods\
  so you end up with:          Documents\Timberborn\Mods\Otters\version-1.1\manifest.json
  Start Timberborn, open Mods on the main menu, tick "Otters", then start a New Game
  and pick the Otters faction.

  To confirm the code half loaded, look in Player.log
  (%USERPROFILE%\AppData\LocalLow\Mechanistry\Timberborn\Player.log) for:
      [Otters] Code loaded from ...

WHAT OTTERS DO
  Water experts   Levee, Floodgate, Aquatic Farmhouse and Shower need no science;
                  bigger floodgates, valves, Large Water Pump and Lido are cheaper.
  Water crops     Cattail and Spadderdock grow about 40% faster. Two new aquatic crops
                  for the Aquatic Farmhouse: Wild Rice and Water Taro, cooked at the
                  Grill into Cooked Wild Rice and Roasted Taro (new foods).
  Mangroves       Otters can plant Mangrove trees in water (logs + mangrove fruit).
  River Holts     Otter dens built out in the water (River Holt for 3, Big River Holt
                  for 6). They must stand in water; residents' fur stays wet overnight.
  Dig Site        Available from the start, free, no explosives. Builders slowly dig
                  out one block by paw (12 builder-hours) and leave 1 dirt behind.
  Terrain Block   Available without science; costs 4 dirt, so digging returns 1/4.
  Reed Filter     Available from the start (20 logs). A Folktails water pump with a
                  bed of reeds at its feet; turns badwater at its intake into clean
                  water right there.
  On land         Walk about 15% slower than beavers. Swim noticeably faster.
  Moisture        A new need. It drains over ~3 days; when it runs out the otter has
                  "Dry fur" and works 15% slower. It refills while swimming (standing in
                  water), at a Shower, Lido or Domed Garden.
  Rinse Pod       550 science. Uses clean water to wash badwater contamination out of
                  otters. Otters have no Herbalist / Antidote.

LOOKS
  Otters have their own 3D body (adult and kit): slim build, long tapering tail,
  cream face and chest, whisker pads, small ears, webbed feet, and a woven reed sash
  with a shell clasp on adults. Fur detail, shading and normal maps are baked from the
  game's own beaver fur so they match the art style. Four fur colours for adults,
  three for kits. They reuse every beaver animation (walking, swimming,
  chopping, sleeping...), so hats, tools and carried goods still line up.

KNOWN LIMITS
  - Otters are built on the Folktails economy and buildings.
  - Worker outfits and tail decals are mapped from the beaver body, so they may sit
    slightly differently on the otter.
  - This mod was checked against the game's own files and code but has not been
    playtested; please report anything odd.

TUNING
  All numbers live at the top of build_mod.py in the source zip. Change them and run:
      python3 build_mod.py <vanilla blueprints folder> dist/Otters build/Otters.dll model_out
  To go back to beaver bodies, delete the "OtterMaterialSpec" and "Children" blocks
  from the two files in version-1.1\OttersModifiers\Characters\ and the "Textures"
  and "ChildTextures" lines from version-1.1\Factions\Faction.Otters.blueprint.json.

EDITING THE MODELS IN BLENDER
  Otters-blender.zip has OtterAdult.blend and OtterChild.blend (fur texture packed in).
  Edit the mesh named "Otter" (keep it triangulated, roughly where it stands now, one
  UV map), then from the source zip's model folder run:
      python3 from_blend.py OtterAdult.blend otter_adult.npz
      python3 export_otter.py BeaverAdult.timbermesh otter_adult.npz OtterAdult.Model.timbermesh 0.03
  (use 0.02 for the kit). BeaverAdult.timbermesh is pulled from your own game files by
  the extraction steps in model/README.txt. Fur textures are plain PNGs in
  version-1.1\Characters\Otters\Textures\ and can be repainted in any editor.
