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
  public record ClamBedSpec : ComponentSpec
  {
    /// <summary>The tile (relative to the building) whose water the clams live in.</summary>
    [Serialize]
    public Vector3Int WaterCoordinates { get; init; }

    /// <summary>Clams need at least this much water over the riverbed (in blocks).</summary>
    [Serialize]
    public float MinWaterDepth { get; init; }

    /// <summary>At or above this badwater share (0..1) the clams close up and none are gathered.</summary>
    [Serialize]
    public float MaxContamination { get; init; }

    [Serialize]
    public string StatusIcon { get; init; }

    [Serialize]
    public string StatusLocKey { get; init; }

    [Serialize]
    public string StatusShortLocKey { get; init; }
  }

  /// <summary>
  /// A staked bed of clams on the riverbed. The gatherer only finds clams while the water over the bed is deep
  /// enough and clean: full speed in clean water, falling off as badwater mixes in, nothing at all once it reaches
  /// the spec's limit. Takes no water from the river.
  ///
  /// Co-op safe: reads the game's water map (which the lockstep keeps identical) and only changes its status in
  /// the simulation tick.
  /// </summary>
  public class ClamBed : TickableComponent, IAwakableComponent, IInitializableEntity, IManufactoryLimiter
  {
    private readonly IThreadSafeWaterMap _waterMap;
    private readonly ILoc _loc;
    private ClamBedSpec _spec;
    private BlockObject _blockObject;
    private StatusToggle _noWaterStatus;

    public ClamBed(IThreadSafeWaterMap waterMap, ILoc loc)
    {
      _waterMap = waterMap;
      _loc = loc;
    }

    public void Awake()
    {
      _spec = GetComponent<ClamBedSpec>();
      _blockObject = GetComponent<BlockObject>();
      _noWaterStatus = StatusToggle.CreateNormalStatusWithAlert(
        string.IsNullOrEmpty(_spec.StatusIcon) ? "OtterClamBedNoWater" : _spec.StatusIcon,
        _loc.T(_spec.StatusLocKey), _loc.T(_spec.StatusShortLocKey), 1f);
    }

    public void InitializeEntity()
    {
      GetComponent<StatusSubject>().RegisterStatus(_noWaterStatus);
    }

    private Vector3Int WaterCell => _blockObject.TransformCoordinates(_spec.WaterCoordinates);

    /// <summary>Water over the riverbed at the bed, in blocks.</summary>
    public float WaterDepth
    {
      get
      {
        Vector3Int cell = WaterCell;
        if (!_waterMap.TryGetColumnFloor(cell, out int floor))
        {
          return 0f;
        }
        return Math.Max(0f, _waterMap.WaterHeightOrFloor(cell) - floor);
      }
    }

    public float Contamination => _waterMap.ColumnContamination(WaterCell);

    public override void Tick()
    {
      _noWaterStatus.Toggle(_blockObject.IsFinished && ProductionEfficiency() <= 0f);
    }

    public float ProductionEfficiency()
    {
      if (WaterDepth < _spec.MinWaterDepth)
      {
        return 0f;
      }
      float max = _spec.MaxContamination > 0f ? _spec.MaxContamination : 0.2f;
      return Math.Max(0f, 1f - Contamination / max);
    }

    public float MaxProductionProgressChange(float expectedProductionProgressChange)
    {
      return 1f;
    }
  }
}
