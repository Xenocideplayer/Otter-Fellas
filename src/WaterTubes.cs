using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.BlueprintSystem;
using Timberborn.Buildings;
using Timberborn.EntitySystem;
using Timberborn.SingletonSystem;
using Timberborn.TickSystem;
using Timberborn.WaterBuildings;
using UnityEngine;

namespace Otters
{
  /// <summary>Something a water tube can plug into from a given neighbouring tile (a well's wall, an outlet).</summary>
  public interface IWaterTubeEndpoint
  {
    bool AcceptsTubeAt(Vector3Int tubeCoordinates);
  }

  /// <summary>
  /// Keeps track of when the tube network changes. The network version moves on in the simulation tick (so wells
  /// re-trace their network at the same moment on every computer in co-op), while tube models refresh every frame,
  /// even when the game is paused.
  /// </summary>
  public class WaterTubeRegistry : ITickableSingleton, IUpdatableSingleton
  {
    private static readonly Vector3Int[] Neighbours =
      { new Vector3Int(0, -1, 0), new Vector3Int(-1, 0, 0), new Vector3Int(0, 1, 0), new Vector3Int(1, 0, 0) };

    private readonly IBlockService _blockService;
    private bool _dirty = true;
    private bool _visualsDirty = true;

    /// <summary>Goes up by one each time anything in a tube network was built, finished or removed.</summary>
    public int Version { get; private set; }

    /// <summary>Raised on the frame after anything in a tube network was built, finished or removed.</summary>
    public event EventHandler VisualsChanged;

    public WaterTubeRegistry(IBlockService blockService)
    {
      _blockService = blockService;
    }

    public void MarkDirty()
    {
      _dirty = true;
      _visualsDirty = true;
    }

    public void Tick()
    {
      if (_dirty)
      {
        _dirty = false;
        Version++;
      }
    }

    public void UpdateSingleton()
    {
      if (_visualsDirty)
      {
        _visualsDirty = false;
        VisualsChanged?.Invoke(this, EventArgs.Empty);
      }
    }

    public WaterTube TubeAt(Vector3Int coordinates)
    {
      foreach (WaterTube tube in _blockService.GetObjectsWithComponentAt<WaterTube>(coordinates))
      {
        return tube;
      }
      return null;
    }

    /// <summary>Whether a tube at <paramref name="from"/> visually and hydraulically joins whatever is at
    /// <paramref name="neighbour"/>.</summary>
    public bool Joins(Vector3Int from, Vector3Int neighbour)
    {
      if (TubeAt(neighbour) != null)
      {
        return true;
      }
      foreach (IWaterTubeEndpoint endpoint in _blockService.GetObjectsWithComponentAt<IWaterTubeEndpoint>(neighbour))
      {
        if (endpoint.AcceptsTubeAt(from))
        {
          return true;
        }
      }
      return false;
    }

    /// <summary>
    /// Follows finished tubes from the given start tiles and returns every finished outlet plugged into them, in
    /// a fixed order (breadth first, neighbours down/left/up/right) so every computer in a co-op game agrees.
    /// </summary>
    public List<WaterTubeOutlet> FindOutlets(IEnumerable<Vector3Int> startTiles)
    {
      var outlets = new List<WaterTubeOutlet>();
      var seen = new HashSet<Vector3Int>();
      var queue = new Queue<Vector3Int>();
      foreach (Vector3Int start in startTiles)
      {
        WaterTube tube = TubeAt(start);
        if (tube != null && tube.IsFinished && !tube.IsDeleted && seen.Add(start))
        {
          queue.Enqueue(start);
        }
      }
      while (queue.Count > 0)
      {
        Vector3Int tile = queue.Dequeue();
        foreach (Vector3Int offset in Neighbours)
        {
          Vector3Int next = tile + offset;
          foreach (WaterTubeOutlet outlet in _blockService.GetObjectsWithComponentAt<WaterTubeOutlet>(next))
          {
            if (outlet.IsFinished && !outlet.IsDeleted && outlet.AcceptsTubeAt(tile) && !outlets.Contains(outlet))
            {
              outlets.Add(outlet);
            }
          }
          WaterTube tube = TubeAt(next);
          if (tube != null && tube.IsFinished && !tube.IsDeleted && seen.Add(next))
          {
            queue.Enqueue(next);
          }
        }
      }
      return outlets;
    }
  }

  public record WaterTubeSpec : ComponentSpec
  {
    /// <summary>Name prefix of the model variants under the finished model ("Variant_" for the game's tubes).</summary>
    [Serialize]
    public string ModelPrefix { get; init; }
  }

  /// <summary>
  /// A length of tube that carries well water. Uses the game's own tube models: the variants are named by which
  /// sides connect (down, left, up, right, then two vertical flags) in one canonical orientation, and the right
  /// one is picked and turned to match the neighbours.
  /// </summary>
  public class WaterTube : BaseComponent, IAwakableComponent, IPostInitializableEntity, IDeletableEntity,
                           IFinishedStateListener, IPrePreviewShownListener
  {
    private static readonly Vector3Int[] LocalNeighbours =
      { new Vector3Int(0, -1, 0), new Vector3Int(-1, 0, 0), new Vector3Int(0, 1, 0), new Vector3Int(1, 0, 0) };
    private static readonly Vector3 Pivot = new Vector3(0.5f, 0f, 0.5f);

    private readonly WaterTubeRegistry _registry;
    private readonly PreviewBlockService _previewBlocks;
    private BlockObject _blockObject;
    private WaterTubeSpec _spec;
    private readonly Dictionary<string, Transform> _variants = new Dictionary<string, Transform>();
    private bool _listening;

    public WaterTube(WaterTubeRegistry registry, PreviewBlockService previewBlocks)
    {
      _registry = registry;
      _previewBlocks = previewBlocks;
    }

    public bool IsFinished => _blockObject.IsFinished;

    public bool IsDeleted { get; private set; }

    public Vector3Int Coordinates => _blockObject.Coordinates;

    public void Awake()
    {
      _blockObject = GetComponent<BlockObject>();
      _spec = GetComponent<WaterTubeSpec>();
    }

    public void OnPrePreviewShown()
    {
      UpdateModel();  // previews are reused, so refresh every time one is shown
    }

    public void PostInitializeEntity()
    {
      if (_blockObject.IsPreview)
      {
        return;
      }
      _registry.VisualsChanged += OnNetworkChanged;
      _listening = true;
      _registry.MarkDirty();
      UpdateModel();
    }

    public void DeleteEntity()
    {
      IsDeleted = true;
      if (_listening)
      {
        _registry.VisualsChanged -= OnNetworkChanged;
        _listening = false;
      }
      _registry.MarkDirty();
    }

    public void OnEnterFinishedState()
    {
      _registry.MarkDirty();
    }

    public void OnExitFinishedState()
    {
      _registry.MarkDirty();
    }

    private void OnNetworkChanged(object sender, EventArgs e)
    {
      UpdateModel();
    }

    private void UpdateModel()
    {
      GameObject model = GetComponent<BuildingModel>()?.FinishedModel;
      if (model == null)
      {
        return;
      }
      string prefix = string.IsNullOrEmpty(_spec?.ModelPrefix) ? "Variant_" : _spec.ModelPrefix;
      if (_variants.Count == 0)
      {
        foreach (Transform child in model.transform)
        {
          if (child.name.StartsWith(prefix, StringComparison.Ordinal))
          {
            _variants[child.name.Substring(prefix.Length)] = child;
          }
        }
      }
      if (_variants.Count == 0)
      {
        return;
      }
      int mask = 0;
      Vector3Int here = _blockObject.Coordinates;
      for (int i = 0; i < 4; i++)
      {
        Vector3Int neighbour = _blockObject.TransformCoordinates(LocalNeighbours[i]);
        if (_registry.Joins(here, neighbour)
            || (_blockObject.IsPreview && _previewBlocks.GetFirstObjectWithComponentAt<WaterTube>(neighbour) != null))
        {
          mask |= 1 << i;
        }
      }
      Pick(mask, out string chosen, out int turns);
      foreach (KeyValuePair<string, Transform> variant in _variants)
      {
        bool active = variant.Key == chosen;
        variant.Value.gameObject.SetActive(active);
        if (active)
        {
          Quaternion rotation = Quaternion.Euler(0f, 90f * turns, 0f);
          variant.Value.localRotation = rotation;
          variant.Value.localPosition = Pivot - rotation * Pivot;
        }
      }
    }

    /// <summary>
    /// Finds the canonical variant for this set of connections and how many quarter turns (clockwise seen from
    /// above, i.e. down to left to up to right) carry it onto the actual connections.
    /// </summary>
    private void Pick(int mask, out string chosen, out int turns)
    {
      for (int k = 0; k < 4; k++)
      {
        int canonical = 0;
        for (int i = 0; i < 4; i++)
        {
          if ((mask & (1 << i)) != 0)
          {
            canonical |= 1 << ((i - k + 4) % 4);
          }
        }
        string key = Key(canonical);
        if (_variants.ContainsKey(key))
        {
          chosen = key;
          turns = k;
          return;
        }
      }
      chosen = _variants.ContainsKey("000000") ? "000000" : FirstKey();  // not reached with the game's variants
      turns = 0;
    }

    private string FirstKey()
    {
      foreach (string key in _variants.Keys)
      {
        return key;
      }
      return "";
    }

    private static string Key(int canonical)
    {
      var chars = new char[6];
      for (int i = 0; i < 4; i++)
      {
        chars[i] = (canonical & (1 << i)) != 0 ? '1' : '0';
      }
      chars[4] = '0';
      chars[5] = '0';
      return new string(chars);
    }
  }

  public record WaterTubeOutletSpec : ComponentSpec
  {
    /// <summary>The tile (relative to the outlet) where the incoming tube has to sit.</summary>
    [Serialize]
    public Vector3Int InputCoordinates { get; init; }
  }

  /// <summary>The open end of a tube line: pours whatever the network carries out of its spout.</summary>
  public class WaterTubeOutlet : BaseComponent, IAwakableComponent, IWaterTubeEndpoint, IPostInitializableEntity,
                                 IDeletableEntity, IFinishedStateListener
  {
    private readonly WaterTubeRegistry _registry;
    private BlockObject _blockObject;
    private WaterOutput _waterOutput;
    private WaterTubeOutletSpec _spec;

    public WaterTubeOutlet(WaterTubeRegistry registry)
    {
      _registry = registry;
    }

    public bool IsFinished => _blockObject.IsFinished;

    public bool IsDeleted { get; private set; }

    /// <summary>How much more water the spout can pour before the water below it is almost up to it.</summary>
    public float AvailableSpace => _waterOutput != null ? _waterOutput.AvailableSpace : 0f;

    public void Awake()
    {
      _blockObject = GetComponent<BlockObject>();
      _waterOutput = GetComponent<WaterOutput>();
      _spec = GetComponent<WaterTubeOutletSpec>();
    }

    public bool AcceptsTubeAt(Vector3Int tubeCoordinates)
    {
      return _spec != null && _blockObject.TransformCoordinates(_spec.InputCoordinates) == tubeCoordinates;
    }

    public void AddCleanWater(float amount)
    {
      if (amount > 0f)
      {
        _waterOutput?.AddCleanWater(amount);
      }
    }

    public void PostInitializeEntity()
    {
      if (!_blockObject.IsPreview)
      {
        _registry.MarkDirty();
      }
    }

    public void DeleteEntity()
    {
      IsDeleted = true;
      _registry.MarkDirty();
    }

    public void OnEnterFinishedState()
    {
      _registry.MarkDirty();
    }

    public void OnExitFinishedState()
    {
      _registry.MarkDirty();
    }
  }
}
