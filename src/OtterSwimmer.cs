using Timberborn.BaseComponentSystem;
using Timberborn.BlueprintSystem;
using Timberborn.WalkingSystem;

namespace Otters
{
  /// <summary>
  /// Added to the beaver body only in Otter games, through the faction's blueprint modifiers.
  /// </summary>
  public record OtterSwimmerSpec : ComponentSpec
  {
    /// <summary>Multiplies the speed a character has while in water (1 = vanilla swimming).</summary>
    [Serialize]
    public float SwimSpeedMultiplier { get; init; }
  }

  /// <summary>
  /// The game's WalkerSpeedManager multiplies in-water speed by every IWaterPenaltyModifier on the character,
  /// so this one component is all it takes to make otters faster in water.
  /// </summary>
  public class OtterSwimmer : BaseComponent, IAwakableComponent, IWaterPenaltyModifier
  {
    private float _multiplier = 1f;

    public float WaterPenaltyModifier => _multiplier;

    public void Awake()
    {
      var spec = GetComponent<OtterSwimmerSpec>();
      if (spec != null && spec.SwimSpeedMultiplier > 0f)
      {
        _multiplier = spec.SwimSpeedMultiplier;
      }
    }
  }
}
