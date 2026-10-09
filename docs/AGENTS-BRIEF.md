# Brief for agents working on the Otters mod / Timber Together

## Environment (cloud container, no game runtime — nothing can be playtested; correctness comes from reading the
## game's real code and from the checkers below)
- Game: Timberborn 1.1.2.x. Game assemblies: `/mnt/user-data/uploads/Timberborn_Data/Managed` (259 DLLs; a few,
  e.g. Timberborn.MechanicalSystem, Timberborn.Tubes, Timberborn.SlotSystem, are NOT there).
- Decompiled game source, one .cs per assembly: `/root/gamesrc` (decompiler: `/root/decomp/App/bin/Release/net8.0/App <managed> /root/gamesrc <dlls>`).
- Vanilla blueprints (from the game's Blueprints.zip): `/root/vanilla/bp` (`*.blueprint.json`).
- The user's PC is NOT linked right now; can't extract more game assets (models/textures) from it.
- Network: package registries (nuget, pip, npm) and GitHub work; other sites don't.

## Otters mod
- Source of truth: `/home/claude/otters`
  - `build_mod.py` generates every blueprint from vanilla ones. Run:
    `cd /home/claude/otters && rm -rf dist/Otters/version-1.1 && python3 build_mod.py /root/vanilla/bp dist/Otters build/Otters.dll model_out && python3 art/make_art.py dist/Otters/version-1.1 dist/Otters model_out/portraits && cp model_out/thumbnail.png dist/Otters/thumbnail.png`
  - C# (`Otters.dll`, netstandard2.1) in `src/`. Build:
    `cd /home/claude/otters && dotnet build src/Otters.csproj -c Release -nologo -v q -p:GameManaged=/mnt/user-data/uploads/Timberborn_Data/Managed -o build`
  - Models: `model/` (procedural props: `procmesh.py`, `make_props.py`, `make_fishing_dock.py`, `make_splash_pool.py`;
    timbermesh read/write: `timbermesh.py`; flat preview render: `building_preview.py model.timbermesh out.png`).
    Built models go to `model_out/buildings/`. Game model space = Unity: x right, y up, z = grid +Y (back);
    1 unit = 1 block. Folktails materials: `BaseWood_LightBrown.Folktails`, `BaseWood_Brown.Folktails`,
    `BaseWood_White.Folktails` (tint with vertex colour), `IrregularPlanks_Brown.Folktails`, `ThatchedRoof.Folktails`,
    `PlasteredWood_White.Folktails`, `WindowsAtlas.Folktails`. Slots are empty nodes named `#Slot#<Keyword>.001`.
  - Icons: `art/icons.py` (tan line-art in the game's UI style), wired up in `art/make_art.py`.
- Checkers (all must pass):
  - `python3 tools/validate_blueprints.py /root/gamesrc /root/vanilla/bp dist/Otters/version-1.1 src`
  - `cd /root/harness && dotnet build -c Release -nologo -v q && dotnet bin/Release/net8.0/Harness.dll /root/vanilla/bp /home/claude/otters/dist/Otters/version-1.1`
    (merges faction blueprint modifiers with the game's JsonMerger and deserializes every spec with the game's
    deserializer; rebuild the harness after rebuilding Otters.dll — it copies the DLL).
  - `dotnet /root/tmcheck/bin/Release/net8.0/tmcheck.dll <file.timbermesh>` (reads models with the game's reader).
- Git repo for publishing: `/home/claude/timberborn-otters` (copy of src/art/model/tools/build_mod.py + built mod
  in `mod/` minus the two big otter body .timbermesh files). Commit trailer lines:
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and
  `Claude-Session: https://claude.ai/code/session_01XRxHSVGEuDFb3HZy6CznfD`.

## Co-op rules (Timber Together / BeaverBuddies lockstep)
- Simulation code: only the game's `IRandomNumberGenerator` (inside ticks), never System.Random / UnityEngine.Random
  directly / Guid.NewGuid / Time.deltaTime / DateTime. Change simulation state only from ticks or replayed events,
  never from UI or Update. Save everything the simulation reads. Iterate collections in a fixed order.
- UI actions that change simulation state need a BeaverBuddies `ReplayEvent`. Prefer reusing actions TT already
  syncs (pausing a building, recipes, priorities, workers).
