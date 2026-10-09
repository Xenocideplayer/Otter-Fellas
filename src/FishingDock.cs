using System;
using Timberborn.BaseComponentSystem;
using Timberborn.BlueprintSystem;
using Timberborn.WaterBuildings;
using Timberborn.Workshops;

namespace Otters
{
  public record FishingDockSpec : ComponentSpec
  {
    /// <summary>At or above this badwater share (0..1) at the line, nothing bites at all.</summary>
    [Serialize]
    public float MaxContamination { get; init; }
  }

  /// <summary>
  /// The catch depends on the water at the end of the line: none when it's dry, full in clean water, and
  /// falling off as badwater mixes in. Fishing doesn't take any water out of the river.
  /// </summary>
  public class FishingDock : BaseComponent, IAwakableComponent, IManufactoryLimiter
  {
    private WaterInput _waterInput;
    private FishingDockSpec _spec;

    public void Awake()
    {
      _waterInput = GetComponent<WaterInput>();
      _spec = GetComponent<FishingDockSpec>();
    }

    public float ProductionEfficiency()
    {
      if (_waterInput == null || !_waterInput.IsUnderwater)
      {
        return 0f;
      }
      float max = _spec != null && _spec.MaxContamination > 0f ? _spec.MaxContamination : 0.5f;
      return Math.Max(0f, 1f - _waterInput.ContaminationPercentage / max);
    }

    public float MaxProductionProgressChange(float expectedProductionProgressChange)
    {
      return 1f;
    }
  }
}
