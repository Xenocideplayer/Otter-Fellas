using System;
using System.Collections.Generic;
using System.Reflection;
using Bindito.Core;
using Timberborn.Goods;
using UnityEngine;

namespace Otters
{
  /// <summary>
  /// Drops goods on the ground as a recovered good stack (the pile builders haul away after a demolition).
  /// The game's spawner is internal, so it is looked up once through the DI container and called by reflection.
  /// </summary>
  public class OtterDirtDropper
  {
    private const string SpawnerType = "Timberborn.RecoveredGoodSystem.RecoveredGoodStackSpawner, Timberborn.RecoveredGoodSystem";
    private readonly IContainer _container;
    private object _spawner;
    private MethodInfo _addAwaitingGoods;
    private bool _failed;

    public OtterDirtDropper(IContainer container)
    {
      _container = container;
    }

    public void Drop(Vector3Int coordinates, string goodId, int amount)
    {
      if (amount <= 0 || !Resolve())
      {
        return;
      }
      try
      {
        _addAwaitingGoods.Invoke(_spawner, new object[] { coordinates, new List<GoodAmount> { new GoodAmount(goodId, amount) } });
      }
      catch (Exception e)
      {
        Debug.LogWarning("[Otters] Could not drop " + goodId + ": " + e.Message);
      }
    }

    private bool Resolve()
    {
      if (_spawner != null)
      {
        return true;
      }
      if (_failed)
      {
        return false;
      }
      try
      {
        var type = Type.GetType(SpawnerType, true);
        _spawner = _container.GetInstance(type);
        _addAwaitingGoods = type.GetMethod("AddAwaitingGoods", BindingFlags.Public | BindingFlags.Instance);
        if (_spawner == null || _addAwaitingGoods == null)
        {
          throw new InvalidOperationException("spawner not found");
        }
        return true;
      }
      catch (Exception e)
      {
        _failed = true;
        _spawner = null;
        Debug.LogWarning("[Otters] Dug dirt cannot be dropped in this game version: " + e.Message);
        return false;
      }
    }
  }
}
