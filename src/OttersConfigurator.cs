using Bindito.Core;
using Timberborn.ModManagerScene;
using Timberborn.TemplateInstantiation;
using UnityEngine;

namespace Otters
{
  [Context("Game")]
  public class OttersConfigurator : Configurator
  {
    protected override void Configure()
    {
      Bind<OtterSwimmer>().AsTransient();
      Bind<OtterDigSite>().AsTransient();
      Bind<ReedFilter>().AsTransient();
      Bind<OtterMaterial>().AsTransient();
      MultiBind<TemplateModule>().ToProvider(ProvideTemplateModule).AsSingleton();
    }

    private static TemplateModule ProvideTemplateModule()
    {
      var builder = new TemplateModule.Builder();
      builder.AddDecorator<OtterSwimmerSpec, OtterSwimmer>();
      builder.AddDecorator<OtterDigSiteSpec, OtterDigSite>();
      builder.AddDecorator<ReedFilterSpec, ReedFilter>();
      builder.AddDecorator<OtterMaterialSpec, OtterMaterial>();
      return builder.Build();
    }
  }

  /// <summary>Writes one line to Player.log so it is easy to confirm the code half of the mod loaded.</summary>
  public class OttersModStarter : IModStarter
  {
    public void StartMod(IModEnvironment modEnvironment)
    {
      Debug.Log("[Otters] Code loaded from " + modEnvironment.ModPath);
    }
  }
}
