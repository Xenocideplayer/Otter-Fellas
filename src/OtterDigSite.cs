using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.BlueprintSystem;
using Timberborn.Characters;
using Timberborn.Common;
using Timberborn.DeconstructionSystem;
using Timberborn.EntitySystem;
using Timberborn.Navigation;
using Timberborn.TerrainSystem;
using Timberborn.TickSystem;
using UnityEngine;

namespace Otters
{
  public record OtterDigSiteSpec : ComponentSpec
  {
    /// <summary>How many blocks of terrain one dig site removes.</summary>
    [Serialize]
    public int Depth { get; init; }
  }

  /// <summary>
  /// A dig site is "built" by builders like any construction site. Once finished it removes the terrain
  /// underneath it, the same way vanilla dynamite does, but quietly: no explosion, no chain reaction, and it
  /// waits until nobody is standing on the tile.
  /// </summary>
  public class OtterDigSite : TickableComponent, IAwakableComponent, IInitializableEntity, IFinishedStateListener,
                              ITerrainRemovingEntity
  {
    private readonly ITerrainService _terrainService;
    private readonly IBlockService _blockService;
    private readonly EntityService _entityService;
    private readonly CharacterPopulation _characterPopulation;

    private BlockObject _blockObject;
    private OtterDigSiteSpec _spec;

    public OtterDigSite(ITerrainService terrainService, IBlockService blockService, EntityService entityService,
                        CharacterPopulation characterPopulation)
    {
      _terrainService = terrainService;
      _blockService = blockService;
      _entityService = entityService;
      _characterPopulation = characterPopulation;
    }

    private int Depth => _spec != null && _spec.Depth > 0 ? _spec.Depth : 1;

    public void Awake()
    {
      _blockObject = GetComponent<BlockObject>();
      _spec = GetComponent<OtterDigSiteSpec>();
      DisableComponent();
    }

    public void InitializeEntity()
    {
      // A save made between finishing and digging resumes the dig.
      if (_blockObject.IsFinished)
      {
        EnableComponent();
      }
    }

    public void OnEnterFinishedState()
    {
      EnableComponent();
    }

    public void OnExitFinishedState()
    {
      DisableComponent();
    }

    public override void Tick()
    {
      if (!_blockObject.IsFinished || SomeoneIsStandingHere())
      {
        return;
      }
      Dig();
    }

    public bool RemovesTerrainAt(Vector3Int coordinates)
    {
      var current = _blockObject.Coordinates.Below();
      int depth = CalculateEffectiveDepth(current);
      for (int i = 0; i < depth; i++)
      {
        if (current == coordinates)
        {
          return true;
        }
        current.z--;
      }
      return false;
    }

    private void Dig()
    {
      DisableComponent();
      RemovePathOnTop();
      var below = _blockObject.Coordinates.Below();
      int depth = CalculateEffectiveDepth(below);
      if (depth > 0)
      {
        _terrainService.UnsetTerrain(below, depth);
      }
      GetComponent<Deconstructible>()?.DisableDeconstruction();
      _entityService.Delete(this);
    }

    private void RemovePathOnTop()
    {
      var path = _blockService.GetPathObjectAt(_blockObject.Coordinates);
      if (path != null)
      {
        path.GetComponent<Deconstructible>()?.DisableDeconstruction();
        _entityService.Delete(path);
      }
    }

    // Same rule as vanilla dynamite: stop digging at the first layer that has something built in it.
    private int CalculateEffectiveDepth(Vector3Int start)
    {
      var column = start.XY();
      for (int i = 0; i < Depth; i++)
      {
        if (_blockService.AnyObjectAt(column.ToVector3Int(start.z - i)))
        {
          return i;
        }
      }
      return Depth;
    }

    private bool SomeoneIsStandingHere()
    {
      var site = _blockObject.Coordinates;
      var characters = _characterPopulation.Characters;
      for (int i = 0; i < characters.Count; i++)
      {
        var character = characters[i];
        if (character && NavigationCoordinateSystem.WorldToGridInt(character.Transform.position) == site)
        {
          return true;
        }
      }
      return false;
    }
  }
}
