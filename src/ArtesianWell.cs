using System;
using Timberborn.BaseComponentSystem;
using Timberborn.BlueprintSystem;
using Timberborn.EntitySystem;
using Timberborn.Localization;
using Timberborn.Persistence;
using Timberborn.StatusSystem;
using Timberborn.WaterBuildings;
using Timberborn.Workshops;
using Timberborn.WorldPersistence;

namespace Otters
{
  public record ArtesianWellSpec : ComponentSpec
  {
    /// <summary>Clean water (cubic blocks) brought up per hour of full-speed work.</summary>
    [Serialize]
    public float WaterPerHour { get; init; }

    /// <summary>Chance per hour of running that the well breaks down (0..1).</summary>
    [Serialize]
    public float BreakdownChancePerHour { get; init; }

    /// <summary>Work-hours the operator spends fixing a broken well.</summary>
    [Serialize]
    public float RepairHours { get; init; }

    [Serialize]
    public string BrokenStatusIcon { get; init; }

    [Serialize]
    public string BrokenStatusLocKey { get; init; }

    [Serialize]
    public string BrokenAlertLocKey { get; init; }
  }

  /// <summary>
  /// A powered well that brings clean water up from deep underground, needing no aquifer and working through
  /// droughts. It runs as a one-worker workshop: production only advances with an operator and power (the game's
  /// manufactory already scales progress by power efficiency), and every bit of progress pours water out of the
  /// spout. Now and then the pump seizes up; the operator then spends their work time on repairs instead and no
  /// water comes out until it is fixed.
  /// </summary>
  public class ArtesianWell : BaseComponent, IAwakableComponent, IInitializableEntity, IManufactoryLimiter,
                              IPersistentEntity, IPostInitializableEntity
  {
    private static readonly ComponentKey WellKey = new ComponentKey("OttersArtesianWell");
    private static readonly PropertyKey<bool> BrokenKey = new PropertyKey<bool>("Broken");
    private static readonly PropertyKey<float> RepairProgressKey = new PropertyKey<float>("RepairProgress");
    private static readonly float SpaceHysteresis = 0.01f;

    private readonly ILoc _loc;
    private readonly Random _random = new Random();

    private ArtesianWellSpec _spec;
    private Manufactory _manufactory;
    private Workshop _workshop;
    private WaterOutput _waterOutput;
    private StatusToggle _brokenStatus;

    public bool IsBroken { get; private set; }

    /// <summary>Repair work done so far, 0..1.</summary>
    public float RepairProgress { get; private set; }

    public ArtesianWell(ILoc loc)
    {
      _loc = loc;
    }

    public void Awake()
    {
      _spec = GetComponent<ArtesianWellSpec>();
      _manufactory = GetComponent<Manufactory>();
      _workshop = GetComponent<Workshop>();
      _waterOutput = GetComponent<WaterOutput>();
      _brokenStatus = StatusToggle.CreatePriorityStatusWithAlertAndFloatingIcon(
        string.IsNullOrEmpty(_spec.BrokenStatusIcon) ? "OtterWellBroken" : _spec.BrokenStatusIcon,
        _loc.T(_spec.BrokenStatusLocKey), _loc.T(_spec.BrokenAlertLocKey));
    }

    public void InitializeEntity()
    {
      GetComponent<StatusSubject>().RegisterStatus(_brokenStatus);
      _manufactory.ProductionProgressed += OnProductionProgressed;
      UpdateStatus();
    }

    public void PostInitializeEntity()
    {
      UpdateStatus();  // after a load
    }

    public float ProductionEfficiency()
    {
      if (IsBroken)
      {
        return 1f;  // repairs don't depend on where the water can go
      }
      if (_waterOutput == null)
      {
        return 0f;
      }
      // Same rule as the game's own water outputs: stop once water around the spout is almost up to it, with a
      // little hysteresis so the well doesn't flicker on and off.
      bool working = _workshop != null && _workshop.CurrentlyWorking;
      float offset = working ? SpaceHysteresis : -SpaceHysteresis;
      return _waterOutput.AvailableSpace + offset > 0f ? 1f : 0f;
    }

    public float MaxProductionProgressChange(float expectedProductionProgressChange)
    {
      return 1f;
    }

    private void OnProductionProgressed(object sender, ProductionProgressedEventArgs e)
    {
      if (e.ProductionProgressChange <= 0f || _manufactory.CurrentRecipe == null)
      {
        return;
      }
      float hours = e.ProductionProgressChange * _manufactory.CurrentRecipe.CycleDurationInHours;
      if (IsBroken)
      {
        Repair(hours);
        return;
      }
      _waterOutput.AddCleanWater(_spec.WaterPerHour * hours);
      RollForBreakdown(hours);
    }

    private void RollForBreakdown(float hours)
    {
      float chancePerHour = Math.Max(0f, Math.Min(_spec.BreakdownChancePerHour, 1f));
      if (chancePerHour <= 0f)
      {
        return;
      }
      double chance = 1.0 - Math.Pow(1.0 - chancePerHour, hours);
      if (_random.NextDouble() < chance)
      {
        IsBroken = true;
        RepairProgress = 0f;
        UpdateStatus();
      }
    }

    private void Repair(float hours)
    {
      float needed = Math.Max(_spec.RepairHours, 0.1f);
      RepairProgress = Math.Min(1f, RepairProgress + hours / needed);
      if (RepairProgress >= 1f)
      {
        IsBroken = false;
        RepairProgress = 0f;
        UpdateStatus();
      }
    }

    private void UpdateStatus()
    {
      if (_brokenStatus == null)
      {
        return;
      }
      if (IsBroken)
      {
        _brokenStatus.Activate();
      }
      else
      {
        _brokenStatus.Deactivate();
      }
    }

    public void Save(IEntitySaver entitySaver)
    {
      IObjectSaver saver = entitySaver.GetComponent(WellKey);
      saver.Set(BrokenKey, IsBroken);
      saver.Set(RepairProgressKey, RepairProgress);
    }

    public void Load(IEntityLoader entityLoader)
    {
      if (entityLoader.TryGetComponent(WellKey, out IObjectLoader loader))
      {
        IsBroken = loader.Get(BrokenKey);
        RepairProgress = loader.Get(RepairProgressKey);
      }
    }
  }
}
