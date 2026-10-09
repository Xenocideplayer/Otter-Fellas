using System.Collections.Generic;
using System.Linq;
using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.BlueprintSystem;
using Timberborn.Common;
using Timberborn.Localization;
using Timberborn.WaterSystem;

namespace Otters
{
  /// <summary>Marks a building that has to be placed with at least part of its footprint standing in water.</summary>
  public record RiverHoltSpec : ComponentSpec
  {
    /// <summary>Minimum number of footprint tiles that must be underwater.</summary>
    [Serialize]
    public int MinimumWaterTiles { get; init; }

    [Serialize]
    public string WarningLocKey { get; init; }
  }

  public class RiverHoltPlacement : BaseComponent, IAwakableComponent, IPreviewValidator
  {
    private static readonly ReadOnlyHashSet<BaseComponent> None = new HashSet<BaseComponent>().AsReadOnlyHashSet();
    private readonly IThreadSafeWaterMap _waterMap;
    private readonly ILoc _loc;
    private BlockObject _blockObject;
    private RiverHoltSpec _spec;

    public RiverHoltPlacement(IThreadSafeWaterMap waterMap, ILoc loc)
    {
      _waterMap = waterMap;
      _loc = loc;
    }

    public void Awake()
    {
      _blockObject = GetComponent<BlockObject>();
      _spec = GetComponent<RiverHoltSpec>();
    }

    public bool IsValid(out string warningMessage)
    {
      int needed = _spec != null && _spec.MinimumWaterTiles > 0 ? _spec.MinimumWaterTiles : 1;
      int wet = _blockObject.PositionedBlocks.GetFoundationCoordinates().Count(c => _waterMap.CellIsUnderwater(c));
      if (wet >= needed)
      {
        warningMessage = string.Empty;
        return true;
      }
      warningMessage = _loc.T(string.IsNullOrEmpty(_spec?.WarningLocKey) ? "Building.RiverHolt.NeedsWater" : _spec.WarningLocKey);
      return false;
    }

    public ReadOnlyHashSet<BaseComponent> InvalidatedObjects(out string warningMessage)
    {
      warningMessage = string.Empty;
      return None;
    }
  }
}
