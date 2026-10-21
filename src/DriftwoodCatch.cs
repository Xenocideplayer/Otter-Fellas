using System;
using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.BlueprintSystem;
using Timberborn.EntitySystem;
using Timberborn.Localization;
using Timberborn.StatusSystem;
using Timberborn.TickSystem;
using Timberborn.WaterSystem;
using Timberborn.Workshops;
using UnityEngine;

namespace Otters
{
  public record DriftwoodCatchSpec : ComponentSpec
  {
    /// <summary>The tile (relative to the building) whose current brings the driftwood.</summary>
    [Serialize]
    public Vector3Int WaterCoordinates { get; init; }

    /// <summary>Water needed over the riverbed there, in blocks.</summary>
    [Serialize]
    public float MinWaterDepth { get; init; }

    /// <summary>Current (as the Flow Sensor reads it) at which the catch works at full speed.</summary>
    [Serialize]
    public float FullSpeedCurrent { get; init; }

    /// <summary>Below this current the water counts as still: nothing drifts in.</summary>
    [Serialize]
    public float MinimumCurrent { get; init; }

    [Serialize]
    public string StatusIcon { get; init; }

    [Serialize]
    public string StatusLocKey { get; init; }

    [Serialize]
    public string StatusShortLocKey { get; init; }
  }

  /// <summary>
  /// A log boom that catches driftwood: works only in moving water, faster the stronger the current (full speed
  /// at the spec's current, like a Flow Sensor reading). Takes nothing out of the river.
  ///
  /// Co-op safe: reads the game's water map (kept identical by the lockstep) and only changes its status in the
  /// simulation tick.
  /// </summary>
  public class DriftwoodCatch : TickableComponent, IAwakableComponent, IInitializableEntity, IManufactoryLimiter
  {
    private readonly IThreadSafeWaterMap _waterMap;
    private readonly ILoc _loc;
    private DriftwoodCatchSpec _spec;
    private BlockObject _blockObject;
    private StatusToggle _noCurrentStatus;

    public DriftwoodCatch(IThreadSafeWaterMap waterMap, ILoc loc)
    {
      _waterMap = waterMap;
      _loc = loc;
    }

    public void Awake()
    {
      _spec = GetComponent<DriftwoodCatchSpec>();
      _blockObject = GetComponent<BlockObject>();
      _noCurrentStatus = StatusToggle.CreateNormalStatusWithAlert(
        string.IsNullOrEmpty(_spec.StatusIcon) ? "OtterDriftwoodNoCurrent" : _spec.StatusIcon,
        _loc.T(_spec.StatusLocKey), _loc.T(_spec.StatusShortLocKey), 1f);
    }

    public void InitializeEntity()
    {
      GetComponent<StatusSubject>().RegisterStatus(_noCurrentStatus);
    }

    private Vector3Int WaterCell => _blockObject.TransformCoordinates(_spec.WaterCoordinates);

    /// <summary>The current at the boom's mouth, or 0 when there isn't enough water there.</summary>
    public float Current
    {
      get
      {
        Vector3Int cell = WaterCell;
        if (!_waterMap.TryGetColumnFloor(cell, out int floor))
        {
          return 0f;
        }
        if (_waterMap.WaterHeightOrFloor(cell) - floor < _spec.MinWaterDepth)
        {
          return 0f;
        }
        return _waterMap.WaterFlowDirection(new Vector3Int(cell.x, cell.y, floor)).magnitude;
      }
    }

    public override void Tick()
    {
      _noCurrentStatus.Toggle(_blockObject.IsFinished && ProductionEfficiency() <= 0f);
    }

    public float ProductionEfficiency()
    {
      float current = Current;
      if (current < _spec.MinimumCurrent)
      {
        return 0f;
      }
      float full = _spec.FullSpeedCurrent > 0f ? _spec.FullSpeedCurrent : 1f;
      return Math.Min(1f, current / full);
    }

    public float MaxProductionProgressChange(float expectedProductionProgressChange)
    {
      return 1f;
    }
  }
}
