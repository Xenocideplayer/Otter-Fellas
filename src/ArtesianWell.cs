using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.BlueprintSystem;
using Timberborn.Common;
using Timberborn.EntitySystem;
using Timberborn.HazardousWeatherSystem;
using Timberborn.Localization;
using Timberborn.Persistence;
using Timberborn.StatusSystem;
using Timberborn.TickSystem;
using Timberborn.WaterBuildings;
using Timberborn.WeatherSystem;
using Timberborn.Workshops;
using Timberborn.WorldPersistence;
using UnityEngine;

namespace Otters
{
  public record ArtesianWellSpec : ComponentSpec
  {
    /// <summary>Clean water (cubic blocks) brought up per hour of full-speed work.</summary>
    [Serialize]
    public float WaterPerHour { get; init; }

    /// <summary>Pumping speed during a drought, as a share of normal (0.5 = half speed).</summary>
    [Serialize]
    public float DroughtSpeed { get; init; }

    /// <summary>Average breakdowns per hour of running (1/50 = once every 50 running hours on average).</summary>
    [Serialize]
    public float BreakdownChancePerHour { get; init; }

    /// <summary>Work-hours the operator spends fixing a broken well.</summary>
    [Serialize]
    public float RepairHours { get; init; }

    /// <summary>Tiles next to the well's walls (relative to the well) where a water tube can plug in.</summary>
    [Serialize]
    public ImmutableArray<Vector3Int> TubePorts { get; init; }

    [Serialize]
    public string BrokenStatusIcon { get; init; }

    [Serialize]
    public string BrokenStatusLocKey { get; init; }

    [Serialize]
    public string BrokenAlertLocKey { get; init; }
  }

  /// <summary>
  /// A powered well that brings clean water up from deep underground, needing no aquifer and working through
  /// droughts at half speed. It runs as a one-worker workshop: production only advances with an operator and
  /// power (the game's manufactory already scales progress by power efficiency), and every bit of progress pours
  /// water out. With water tubes plugged into its walls the water goes to the tube outlets, shared between them;
  /// otherwise it spills over the edge behind the well. Now and then the pump seizes up; the operator then spends
  /// their work time on repairs instead and no water comes out until it is fixed.
  ///
  /// Co-op safe: breakdowns are drawn from the game's own random number generator inside the simulation tick
  /// (which Timber Together / BeaverBuddies keeps identical on every computer), and the time to the next
  /// breakdown is saved.
  /// </summary>
  public class ArtesianWell : TickableComponent, IAwakableComponent, IInitializableEntity, IManufactoryLimiter,
                              IPersistentEntity, IPostInitializableEntity, IWaterTubeEndpoint
  {
    private static readonly ComponentKey WellKey = new ComponentKey("OttersArtesianWell");
    private static readonly PropertyKey<bool> BrokenKey = new PropertyKey<bool>("Broken");
    private static readonly PropertyKey<float> RepairProgressKey = new PropertyKey<float>("RepairProgress");
    private static readonly PropertyKey<float> HoursUntilBreakdownKey = new PropertyKey<float>("HoursUntilBreakdown");
    private static readonly float SpaceHysteresis = 0.01f;

    private readonly ILoc _loc;
    private readonly IRandomNumberGenerator _random;
    private readonly HazardousWeatherService _hazardousWeatherService;
    private readonly WeatherService _weatherService;
    private readonly WaterTubeRegistry _tubes;

    private ArtesianWellSpec _spec;
    private BlockObject _blockObject;
    private Manufactory _manufactory;
    private Workshop _workshop;
    private WaterOutput _waterOutput;
    private StatusToggle _brokenStatus;
    private StatusToggle _noRoomStatus;
    private StatusToggle _closedStatus;
    private List<WaterTubeOutlet> _outlets = new List<WaterTubeOutlet>();
    private bool _networkBlocked;
    private int _outletsVersion = -1;
    private readonly List<WaterTubeOutlet> _eligible = new List<WaterTubeOutlet>();

    public bool IsBroken { get; private set; }

    /// <summary>Repair work done so far, 0..1.</summary>
    public float RepairProgress { get; private set; }

    /// <summary>Running hours left before the next breakdown; negative until first drawn.</summary>
    public float HoursUntilBreakdown { get; private set; } = -1f;

    public ArtesianWell(ILoc loc, IRandomNumberGenerator random, HazardousWeatherService hazardousWeatherService,
                        WeatherService weatherService, WaterTubeRegistry tubes)
    {
      _loc = loc;
      _random = random;
      _hazardousWeatherService = hazardousWeatherService;
      _weatherService = weatherService;
      _tubes = tubes;
    }

    public void Awake()
    {
      _spec = GetComponent<ArtesianWellSpec>();
      _blockObject = GetComponent<BlockObject>();
      _manufactory = GetComponent<Manufactory>();
      _workshop = GetComponent<Workshop>();
      _waterOutput = GetComponent<WaterOutput>();
      _brokenStatus = StatusToggle.CreatePriorityStatusWithAlertAndFloatingIcon(
        string.IsNullOrEmpty(_spec.BrokenStatusIcon) ? "OtterWellBroken" : _spec.BrokenStatusIcon,
        _loc.T(_spec.BrokenStatusLocKey), _loc.T(_spec.BrokenAlertLocKey));
      _noRoomStatus = StatusToggle.CreateNormalStatusWithAlert("OtterWellNoRoom",
        _loc.T("Status.ArtesianWell.NoRoom"), _loc.T("Status.ArtesianWell.NoRoom.Short"), 1f);
      _closedStatus = StatusToggle.CreateNormalStatusWithAlert("OtterWellNoRoom",
        _loc.T("Status.ArtesianWell.Closed"), _loc.T("Status.ArtesianWell.Closed.Short"), 1f);
    }

    /// <summary>Tells the player when the water has nowhere to go (level ground behind, full outlets).</summary>
    public override void Tick()
    {
      RefreshOutlets();
      bool stuck = !IsBroken && _blockObject.IsFinished && !HasRoom(0f);
      bool closed = stuck && _outlets.Count == 0 && _networkBlocked;
      _closedStatus.Toggle(closed);
      _noRoomStatus.Toggle(stuck && !closed);
    }

    private bool HasRoom(float offset)
    {
      IReadOnlyList<WaterTubeOutlet> outlets = ConnectedOutlets;
      if (outlets.Count == 0 && _networkBlocked)
      {
        return false;  // every outlet is closed off by a valve or paused: the water waits in the well
      }
      if (outlets.Count > 0)
      {
        foreach (WaterTubeOutlet outlet in outlets)
        {
          if (!outlet.IsDeleted && outlet.AvailableSpace + offset > 0f)
          {
            return true;
          }
        }
        return false;
      }
      return _waterOutput != null && _waterOutput.AvailableSpace + offset > 0f;
    }

    public void InitializeEntity()
    {
      GetComponent<StatusSubject>().RegisterStatus(_brokenStatus);
      GetComponent<StatusSubject>().RegisterStatus(_noRoomStatus);
      GetComponent<StatusSubject>().RegisterStatus(_closedStatus);
      _manufactory.ProductionProgressed += OnProductionProgressed;
      UpdateStatus();
    }

    public void PostInitializeEntity()
    {
      UpdateStatus();  // after a load
      if (!_blockObject.IsPreview)
      {
        _tubes.MarkDirty();  // tubes next to the walls turn to face the well
      }
    }

    public bool IsDrought => _weatherService.IsHazardousWeather
                             && _hazardousWeatherService.CurrentCycleHazardousWeather is DroughtWeather;

    private float SpeedFactor => IsDrought ? Mathf.Clamp(_spec.DroughtSpeed, 0f, 1f) : 1f;

    public bool AcceptsTubeAt(Vector3Int tubeCoordinates)
    {
      if (_spec == null || _spec.TubePorts.IsDefault)
      {
        return false;
      }
      foreach (Vector3Int port in _spec.TubePorts)
      {
        if (_blockObject.TransformCoordinates(port) == tubeCoordinates)
        {
          return true;
        }
      }
      return false;
    }

    /// <summary>The outlets currently plugged into this well through finished tubes and open valves, as of
    /// this well's last simulation tick.</summary>
    public IReadOnlyList<WaterTubeOutlet> ConnectedOutlets => _outlets;

    /// <summary>
    /// Re-traces the tube network when it changed. Only called from the simulation tick, so the outlets (and
    /// the valve and pause states they depend on) are read at the same moment on every computer in co-op.
    /// </summary>
    private void RefreshOutlets()
    {
      if (_outletsVersion == _tubes.Version)
      {
        return;
      }
      _outletsVersion = _tubes.Version;
      var ports = new List<Vector3Int>();
      if (!_spec.TubePorts.IsDefault)
      {
        foreach (Vector3Int port in _spec.TubePorts)
        {
          ports.Add(_blockObject.TransformCoordinates(port));
        }
      }
      _outlets = _tubes.FindOutlets(ports, out _networkBlocked);
    }

    public float ProductionEfficiency()
    {
      if (IsBroken)
      {
        return 1f;  // repairs don't depend on the weather or on where the water can go
      }
      bool working = _workshop != null && _workshop.CurrentlyWorking;
      // Same rule as the game's own water outputs: stop once the water at the spout is almost up to it, with a
      // little hysteresis so the well doesn't flicker on and off.
      return HasRoom(working ? SpaceHysteresis : -SpaceHysteresis) ? SpeedFactor : 0f;
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
      RefreshOutlets();  // production only moves on in the simulation
      float hours = e.ProductionProgressChange * _manufactory.CurrentRecipe.CycleDurationInHours;
      if (IsBroken)
      {
        Repair(hours);
        return;
      }
      PourWater(_spec.WaterPerHour * hours);
      Wear(hours);
    }

    private void PourWater(float water)
    {
      IReadOnlyList<WaterTubeOutlet> outlets = ConnectedOutlets;
      if (outlets.Count == 0)
      {
        if (!_networkBlocked)
        {
          _waterOutput.AddCleanWater(water);
        }
        return;
      }
      _eligible.Clear();
      WaterTubeOutlet roomiest = null;
      foreach (WaterTubeOutlet outlet in outlets)
      {
        if (outlet.IsDeleted)
        {
          continue;
        }
        if (outlet.AvailableSpace > 0f)
        {
          _eligible.Add(outlet);
        }
        if (roomiest == null || outlet.AvailableSpace > roomiest.AvailableSpace)
        {
          roomiest = outlet;
        }
      }
      if (_eligible.Count == 0)
      {
        roomiest?.AddCleanWater(water);  // nearly full everywhere: top up the roomiest, like the game's own spouts
        return;
      }
      float share = water / _eligible.Count;
      foreach (WaterTubeOutlet outlet in _eligible)
      {
        outlet.AddCleanWater(share);
      }
    }

    private void Wear(float hours)
    {
      if (_spec.BreakdownChancePerHour <= 0f)
      {
        return;
      }
      if (HoursUntilBreakdown < 0f)
      {
        DrawNextBreakdown();
      }
      HoursUntilBreakdown -= hours;
      if (HoursUntilBreakdown <= 0f)
      {
        IsBroken = true;
        RepairProgress = 0f;
        HoursUntilBreakdown = -1f;
        UpdateStatus();
      }
    }

    /// <summary>Running time to the next breakdown is exponential with the given average rate.</summary>
    private void DrawNextBreakdown()
    {
      float u = Mathf.Clamp(_random.Range(0f, 1f), 0f, 0.9999f);
      HoursUntilBreakdown = (float)(-Math.Log(1.0 - u) / _spec.BreakdownChancePerHour);
    }

    private void Repair(float hours)
    {
      float needed = Math.Max(_spec.RepairHours, 0.1f);
      RepairProgress = Math.Min(1f, RepairProgress + hours / needed);
      if (RepairProgress >= 1f)
      {
        IsBroken = false;
        RepairProgress = 0f;
        DrawNextBreakdown();
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
      saver.Set(HoursUntilBreakdownKey, HoursUntilBreakdown);
    }

    public void Load(IEntityLoader entityLoader)
    {
      if (entityLoader.TryGetComponent(WellKey, out IObjectLoader loader))
      {
        IsBroken = loader.Get(BrokenKey);
        RepairProgress = loader.Get(RepairProgressKey);
        if (loader.Has(HoursUntilBreakdownKey))
        {
          HoursUntilBreakdown = loader.Get(HoursUntilBreakdownKey);
        }
      }
    }
  }
}
