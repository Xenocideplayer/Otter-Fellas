using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.BlueprintSystem;
using Timberborn.Rendering;
using UnityEngine;

namespace Otters
{
  public record ReedPipeSpec : ComponentSpec
  {
    /// <summary>Name of the node in the building model that holds one block of reed bundle.</summary>
    [Serialize]
    public string TemplateName { get; init; }

    /// <summary>The model child the game puts the pipe segments under (WaterInputPipeSpec.PipeParentName).</summary>
    [Serialize]
    public string PipeParentName { get; init; }
  }

  /// <summary>
  /// Dresses the game's water-intake pipe in reeds: every pipe segment the pump creates gets its wooden pipe meshes
  /// emptied and a copy of the model's reed-bundle node put in their place. The game keeps positioning, showing
  /// and hiding the segments as the water level changes, so the reeds always reach as deep as the pipe would.
  /// Purely visual: nothing here touches the simulation (safe in co-op).
  /// </summary>
  public class ReedPipe : BaseComponent, IAwakableComponent, IUpdatableComponent
  {
    private static readonly string SegmentName = "PipeSegment";
    private static readonly string ReedsName = "OtterReeds";
    private static readonly int CheckEveryFrames = 2;
    private static Mesh _emptyMesh;

    private readonly MaterialColorer _materialColorer;
    private ReedPipeSpec _spec;
    private BlockObject _blockObject;
    private EntityMaterials _entityMaterials;
    private Transform _template;
    private Transform _pipeParent;
    private int _frame;

    public ReedPipe(MaterialColorer materialColorer)
    {
      _materialColorer = materialColorer;
    }

    public void Awake()
    {
      _spec = GetComponent<ReedPipeSpec>();
      _blockObject = GetComponent<BlockObject>();
      _entityMaterials = GetComponent<EntityMaterials>();
    }

    public void Update()
    {
      if (++_frame < CheckEveryFrames)
      {
        return;
      }
      _frame = 0;
      if (_template == null || _pipeParent == null)
      {
        // The model's nodes are looked up lazily: they may not be in place yet while the entity wakes up. The
        // template is shrunk to nothing in the model itself, so it never shows even before this runs.
        _template = Find(GameObject.transform, _spec.TemplateName);
        _pipeParent = Find(GameObject.transform, _spec.PipeParentName);
        if (_template == null || _pipeParent == null)
        {
          return;
        }
        _template.gameObject.SetActive(false);
      }
      for (int i = 0; i < _pipeParent.childCount; i++)
      {
        Transform segment = _pipeParent.GetChild(i);
        if (segment.name == SegmentName && segment.Find(ReedsName) == null)
        {
          Dress(segment);
        }
      }
    }

    private void Dress(Transform segment)
    {
      foreach (MeshFilter filter in segment.GetComponentsInChildren<MeshFilter>(true))
      {
        // the wooden pipe: an empty mesh rather than null, which debug tools (mesh metrics on selection) can't read
        filter.sharedMesh = EmptyMesh;
      }
      GameObject reeds = Object.Instantiate(_template.gameObject, segment, false);
      reeds.name = ReedsName;
      reeds.transform.localPosition = Vector3.zero;
      reeds.transform.localRotation = Quaternion.identity;
      reeds.transform.localScale = Vector3.one;
      reeds.SetActive(true);
      if (_entityMaterials != null)
      {
        _entityMaterials.AddMaterials(reeds);
      }
      if (_blockObject != null && !_blockObject.IsFinished)
      {
        _materialColorer.EnableGrayscale(reeds);
      }
    }

    private static Mesh EmptyMesh
    {
      get
      {
        if (_emptyMesh == null)
        {
          _emptyMesh = new Mesh { name = "OtterEmptyPipe" };
        }
        return _emptyMesh;
      }
    }

    private static Transform Find(Transform root, string name)
    {
      if (string.IsNullOrEmpty(name))
      {
        return null;
      }
      for (int i = 0; i < root.childCount; i++)
      {
        Transform child = root.GetChild(i);
        if (child.name == name)
        {
          return child;
        }
        Transform found = Find(child, name);
        if (found != null)
        {
          return found;
        }
      }
      return null;
    }
  }
}
