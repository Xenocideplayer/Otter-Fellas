using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.BlueprintSystem;
using Timberborn.EntitySystem;
using Timberborn.Persistence;
using Timberborn.WorldPersistence;
using Timberborn.Growing;
using Timberborn.SoilContaminationSystem;
using Timberborn.SoilMoistureSystem;
using Timberborn.TickSystem;
using Timberborn.TimeSystem;
using Timberborn.WaterSystem;

namespace Otters
{
  public record CleanWaterGrowthSpec : ComponentSpec
  {
    /// <summary>Growth speed while the crop's water is perfectly clean (1.5 = 50% faster).</summary>
    [Serialize]
    public float GrowthMultiplier { get; init; }

    /// <summary>Water at or below this contamination counts as 100% clean (the UI shows it as 0%).</summary>
    [Serialize]
    public float CleanThreshold { get; init; }
  }

  /// <summary>
  /// Otter-planted crops grow faster while their water is perfectly clean: for an aquatic crop, the water it
  /// stands in has no badwater in it; for a land crop, its soil is irrigated and not contaminated at all.
  /// The bonus is added on top of normal growth from the simulation tick, in small batches.
  /// </summary>
  public class CleanWaterGrowth : TickableComponent, IAwakableComponent, IInitializableEntity, IPersistentEntity
  {
    private static readonly float BatchProgress = 0.01f;
    private static readonly ComponentKey Key = new ComponentKey("OttersCleanWaterGrowth");
    private static readonly PropertyKey<float> PendingKey = new PropertyKey<float>("Pending");

    private readonly IThreadSafeWaterMap _waterMap;
    private readonly ISoilMoistureService _soilMoisture;
    private readonly ISoilContaminationService _soilContamination;
    private readonly IDayNightCycle _dayNightCycle;

    private Growable _growable;
    private BlockObject _blockObject;
    private CleanWaterGrowthSpec _spec;
    private float _pending;

    public CleanWaterGrowth(IThreadSafeWaterMap waterMap, ISoilMoistureService soilMoisture,
                            ISoilContaminationService soilContamination, IDayNightCycle dayNightCycle)
    {
      _waterMap = waterMap;
      _soilMoisture = soilMoisture;
      _soilContamination = soilContamination;
      _dayNightCycle = dayNightCycle;
    }

    public void Awake()
    {
      _growable = GetComponent<Growable>();
      _blockObject = GetComponent<BlockObject>();
      _spec = GetComponent<CleanWaterGrowthSpec>();
    }

    public void InitializeEntity()
    {
      if (_growable == null)
      {
        return;
      }
      if (_growable.IsGrown)
      {
        DisableComponent();
      }
      _growable.HasGrown += (sender, args) => DisableComponent();  // nothing left to speed up
    }

    public void Save(IEntitySaver entitySaver)
    {
      if (_pending > 0f)
      {
        entitySaver.GetComponent(Key).Set(PendingKey, _pending);
      }
    }

    public void Load(IEntityLoader entityLoader)
    {
      if (entityLoader.TryGetComponent(Key, out IObjectLoader loader))
      {
        _pending = loader.Get(PendingKey);
      }
    }

    /// <summary>True while the bonus applies (handy for tooltips and tests).</summary>
    public bool InCleanWater
    {
      get
      {
        var cell = _blockObject.Coordinates;
        if (_waterMap.CellIsUnderwater(cell))
        {
          return _waterMap.ColumnContamination(cell) <= _spec.CleanThreshold;
        }
        return _soilMoisture.SoilIsMoist(cell) && !_soilContamination.SoilIsContaminated(cell);
      }
    }

    public override void Tick()
    {
      if (_growable == null || _spec == null || _spec.GrowthMultiplier <= 1f || !_blockObject.IsFinished
          || !_growable.GrowthInProgress || _growable.GrowthTimeInDays <= 0f)
      {
        return;
      }
      if (!InCleanWater)
      {
        return;
      }
      _pending += (_spec.GrowthMultiplier - 1f) * _dayNightCycle.FixedDeltaTimeInHours / 24f / _growable.GrowthTimeInDays;
      if (_pending >= BatchProgress)
      {
        _growable.IncreaseGrowthProgress(_pending);
        _pending = 0f;
      }
    }
  }
}
