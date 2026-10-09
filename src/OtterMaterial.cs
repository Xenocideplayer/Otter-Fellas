using Timberborn.AssetSystem;
using Timberborn.BaseComponentSystem;
using Timberborn.BlueprintSystem;
using Timberborn.Characters;
using Timberborn.EntitySystem;
using UnityEngine;

namespace Otters
{
  /// <summary>
  /// Texture paths that replace the beaver material's normal, occlusion and metallic maps on otters. Those maps are
  /// painted for the beaver body's UV layout, so on the otter body they would show up as smudges.
  /// </summary>
  public record OtterMaterialSpec : ComponentSpec
  {
    [Serialize]
    public string NormalMap { get; init; }

    [Serialize]
    public string OcclusionMap { get; init; }

    [Serialize]
    public string MetallicMap { get; init; }
  }

  public class OtterMaterial : BaseComponent, IAwakableComponent, IInitializableEntity
  {
    private static readonly int NormalMapId = Shader.PropertyToID("_BumpMap");
    private static readonly int OcclusionMapId = Shader.PropertyToID("_OcclusionMap");
    private static readonly int MetallicMapId = Shader.PropertyToID("_MetallicGlossMap");

    private readonly IAssetLoader _assetLoader;
    private CharacterMaterialModifier _materialModifier;
    private OtterMaterialSpec _spec;

    public OtterMaterial(IAssetLoader assetLoader)
    {
      _assetLoader = assetLoader;
    }

    public void Awake()
    {
      _materialModifier = GetComponent<CharacterMaterialModifier>();
      _spec = GetComponent<OtterMaterialSpec>();
    }

    public void InitializeEntity()
    {
      if (_materialModifier == null || _spec == null)
      {
        return;
      }
      Set(NormalMapId, _spec.NormalMap);
      Set(OcclusionMapId, _spec.OcclusionMap);
      Set(MetallicMapId, _spec.MetallicMap);
    }

    private void Set(int propertyId, string path)
    {
      if (string.IsNullOrEmpty(path))
      {
        return;
      }
      var texture = _assetLoader.LoadSafe<Texture2D>(path);
      if (texture != null)
      {
        _materialModifier.SetTexture(propertyId, texture);
      }
      else
      {
        Debug.LogWarning("[Otters] Missing texture " + path);
      }
    }
  }
}
