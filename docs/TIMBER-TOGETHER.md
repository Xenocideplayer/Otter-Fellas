# Otters and Timber Together

[Timber Together](https://github.com/timbermods/TimberTogether) is the BeaverBuddies-based co-op mod. Every
computer runs the same simulation from the same save, and only player actions go over the network. So a mod
works in co-op as long as its simulation is deterministic and every player has the same version.

## Status (Otters 2.0.1)

Otters 2.0 is a self-contained faction: collections `Buildings.Otters`, `Characters.Otters` (`OtterAdult`,
`OtterChild`, `Bot.Otters`), `ModularShaftParts.Otters`, `NaturalResources.Otters`, worker outfits with
`FactionId: "Otters"`, starting building `DistrictCenter.Otters`, and no faction blueprint modifiers. The only
templates shared with other factions are the map plants (Dandelion, Chestnut Tree, Maple with Folktails;
Mangrove with Iron Teeth) and the two dev-mode objects every faction lists. `check_faction.py` checks all of this.

| Mode | Timber Together rc32 (released) | Timber Together rc33 (branch `otters-mixed-factions`) |
|---|---|---|
| Shared colony, Otters | Works | Works |
| Separate colonies, all Otters | Works, no Trading Post for otters | Works, with an Otters Trading Post and Power Export |
| Mixed factions (any, Otters installed) | Crashes at load | Fixed (see that branch's docs/MIXED-FACTIONS-FIX.md); untested in game |

The rest of this page is the 1.2 analysis, kept for reference.

## What works now (Otters 1.2.0)

| Mode | Status |
|---|---|
| Shared colony ("Separate colonies" off), Otters | Works. Ordinary co-op. |
| Separate colonies, everyone plays Otters | Works. The Trading Post and Power Export Facility show up for otters, because Otters now builds from the `Buildings.Folktails` list and Timber Together appends its buildings there. |
| Mixed factions including Otters | Not supported. See below. |
| Mixed Folktails + Iron Teeth with Otters installed | Timber Together greys out Mixed factions when there are more than two factions. Don't load old mixed saves with Otters enabled. |

## What the mod does to stay in sync

- **Artesian Well breakdowns** use the game's `IRandomNumberGenerator`, drawn only inside the simulation tick.
  Timber Together keeps that generator identical on every computer and checks it every heartbeat. The well draws
  the running time to its next breakdown once, after each repair, and saves it.
- **Water** goes through `IWaterService` and `WaterOutput` from the tick, the same path as the game's own pumps.
- **Tube networks**: the network version only changes in the tick, and outlets are traced in a fixed order. Tube
  *models* refresh every frame, which is fine because they are only visuals.
- **Clean-water crop growth** runs from the tick, reads the thread-safe water and soil maps, and saves the
  unapplied bonus.
- **No UI actions change the simulation**, so no custom `ReplayEvent`s are needed. Recipes, pausing, priorities
  and workers are already synced by Timber Together.

Mismatched versions get only a warning from Timber Together, then drift apart. The manifest version goes up with
every release, so treat that warning as fatal.

## Mixed factions: plan for the fork

Both sides need changes.

**Timber Together**
1. Lift the exactly-two-factions gate: `Factions/NewGameFactionCapture.cs` (`MixedPossible`),
   `Lobby/NewGameColonyOptions.cs`, `Lobby/LobbyHostPanel.cs`, `Factions/MixedFactions.cs`.
2. Load only the factions being played (`MixedFactions.cs`, around the collection merge).
3. Fix strings that assume two factions (e.g. `Connect/LoadGameBoxColonies.cs`).

**Otters**
1. Stop using faction blueprint modifiers on shared blueprints. A mixed game merges every faction's modifiers,
   so the otter body, speeds, science discounts and crop changes would hit every faction.
   - Give Otters their own character templates (OtterAdult/OtterChild).
   - Give them their own copies of the Folktails buildings they change.
2. Give Otters their own `Characters`, `ModularShaftParts` and `NaturalResources` collections. Timber Together
   treats a template as one faction's only if exactly one faction lists it.
3. Give Otters their own Trading Post and Power Export copies.
4. Give Otters their own housing templates, because babies take the faction of the house they're born in.

We'll compare the two approaches once the fork exists.
