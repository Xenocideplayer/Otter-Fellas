// Lets records with init-only properties compile for netstandard2.1, which predates IsExternalInit.
namespace System.Runtime.CompilerServices
{
  internal static class IsExternalInit
  {
  }
}
