using System;
using Timberborn.BaseComponentSystem;
using Timberborn.BlueprintSystem;
using Timberborn.EntitySystem;
using Timberborn.WaterBuildings;
using Timberborn.WaterSystem;
using Timberborn.Workshops;

namespace Otters
{
  public record ReedFilterSpec : ComponentSpec
  {
    /// <summary>
    /// Water converted from badwater to clean water per finished production cycle, when the water at the
    /// intake is fully contaminated. At lower contamination the filter cleans proportionally less.
    /// </summary>
    [Serialize]
    public float WaterPerCycle { get; init; }

    /// <summary>Below this contamination (0..1) at the intake, the filter has nothing to do and idles.</summary>
    [Serialize]
    public float MinimumContamination { get; init; }
  }

  /// <summary>
  /// Works like a pump with a worker, but instead of taking water out it swaps contaminated water for clean
  /// water at its intake, so the river stays the same height and simply gets cleaner.
  /// </summary>
  public class ReedFilter : BaseComponent, IAwakableComponent, IInitializableEntity, IManufactoryLimiter
  {
    private readonly IWaterService _waterService;
    private readonly IThreadSafeWaterMap _waterMap;

    private Manufactory _manufactory;
    private WaterInput _waterInput;
    private ReedFilterSpec _spec;

    public ReedFilter(IWaterService waterService, IThreadSafeWaterMap waterMap)
    {
      _waterService = waterService;
      _waterMap = waterMap;
    }

    public void Awake()
    {
      _manufactory = GetComponent<Manufactory>();
      _waterInput = GetComponent<WaterInput>();
      _spec = GetComponent<ReedFilterSpec>();
    }

    public void InitializeEntity()
    {
      _manufactory.ProductionProgressed += OnProductionProgressed;
    }

    public float ProductionEfficiency()
    {
      if (_waterInput == null || !_waterInput.IsUnderwater)
      {
        return 0f;
      }
      return _waterInput.ContaminationPercentage >= MinimumContamination ? 1f : 0f;
    }

    public float MaxProductionProgressChange(float expectedProductionProgressChange)
    {
      return 1f;
    }

    private float MinimumContamination => _spec != null ? Math.Max(_spec.MinimumContamination, 0.0001f) : 0.01f;

    private void OnProductionProgressed(object sender, ProductionProgressedEventArgs e)
    {
      if (_waterInput == null || _spec == null || e.ProductionProgressChange <= 0f)
      {
        return;
      }
      var intake = _waterInput.Coordinates;
      float contamination = _waterMap.ColumnContamination(intake);
      if (contamination <= 0f)
      {
        return;
      }
      float wanted = _spec.WaterPerCycle * e.ProductionProgressChange * contamination;
      float available = _waterMap.WaterDepth(intake) * contamination;
      float amount = Math.Min(wanted, available);
      if (amount <= 0f)
      {
        return;
      }
      _waterService.RemoveContaminatedWater(intake, amount);
      _waterService.AddCleanWater(intake, amount);
    }
  }
}
