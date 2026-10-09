# Otters — a water faction for Timberborn

![Otters](docs/images/thumbnail.png)

A third playable faction for **Timberborn 1.1.2+**: sleek river otters who would rather swim than walk.
They manage water from day one, farm aquatic crops faster, dig out terrain without explosives and filter
badwater clean — but they're slow on land and work slower once their fur dries out.

## Features

| | |
|---|---|
| **Water experts** | Levee, Floodgate, Aquatic Farmhouse and Shower need no science; bigger floodgates, valves, the Large Water Pump and the Lido are cheaper. |
| **Water crops** | Cattail and Spadderdock grow about 25% faster. |
| **Dig Site** | Available from the start, free, no explosives. Removes one block of terrain once built. |
| **Reed Filter** | Available from the start (20 logs). Turns badwater into clean water where it stands. |
| **On land / in water** | Walk ~15% slower than beavers, swim much faster. |
| **Moisture** | A new need. When it runs dry the otter gets *Dry fur* and works 15% slower. Swimming, the Shower, the Lido and the Domed Garden refill it. |
| **Rinse Pod** | 550 science. Uses clean water to wash badwater contamination out of otters (no Herbalist/Antidote). |
| **Their own bodies** | Custom 3D adult and kit models with otter faces, long tails and webbed feet, 4 adult and 3 kit fur colours, and every beaver animation carried over. |

![Adult otter](docs/images/otter-adult.png)

## Install

1. Download **Otters.zip** from the [latest release](../../releases/latest).
2. Unzip it into `Documents\Timberborn\Mods\` so you have `Mods\Otters\version-1.1\manifest.json`.
3. Start Timberborn, enable **Otters** under *Mods*, and pick the Otters faction in a new game.

The `mod/Otters` folder in this repository is the same mod **without the two 3D model files**
(`*.timbermesh`, 100+ MB, over GitHub's file limit) — use the release zip to play.

## Repository layout

| Path | What it is |
|---|---|
| `src/` | C# code (`Otters.dll`): Dig Site, Reed Filter, faster swimming, otter material maps. |
| `build_mod.py` | Generates every blueprint from the game's own vanilla blueprints; all balance numbers are at the top. |
| `art/make_art.py` | Vector art for icons, logo and fallback portraits. |
| `model/` | The otter model pipeline (Python + Blender's `bpy`): shape, UVs, fur painting, animation transfer, `.timbermesh` export. See `model/README.txt`. |
| `tools/validate_blueprints.py` | Checks every blueprint against the game's spec schema. |
| `mod/Otters/` | Built mod (minus model files). |

## Building

```
# code
dotnet build src/Otters.csproj -c Release -p:GameManaged="<Timberborn>/Timberborn_Data/Managed" -o build

# blueprints (vanilla blueprints come from the game's StreamingAssets/Modding/Blueprints.zip)
python3 build_mod.py <vanilla blueprints> mod/Otters build/Otters.dll <model output folder>
python3 art/make_art.py mod/Otters/version-1.1 mod/Otters <model output folder>/portraits
```

The model pipeline needs the beaver bodies from your own copy of the game; see `model/README.txt`.
No game files are included in this repository.

## Status

Checked against the game's own blueprint merger, deserializer and model reader, but not yet widely
playtested. Issues and screenshots welcome.

*Fan-made mod; not affiliated with or endorsed by Mechanistry.*
