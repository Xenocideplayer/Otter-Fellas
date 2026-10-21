Otter model pipeline (Python + Blender's bpy module)

1. Extract the beaver bodies from your game (needs UnityPy):
     resources.assets -> GameObjects "BeaverAdult.Model" / "BeaverChild.Model" -> their BinaryData
     MonoBehaviour. The raw object is a 32-byte header, an int32 length, then the zlib .timbermesh bytes.
2. python3 build_models.py <folder with BeaverAdult.timbermesh, BeaverChild.timbermesh> <out folder>
   builds the shapes (otter_shape.py), cleans them up in Blender (finish_mesh.py), paints fur (paint.py),
   transfers all 61/39 beaver animations (transfer.py) and writes OtterAdult/OtterChild.Model.timbermesh,
   textures, portraits and .blend files.
   It finishes with add_axe.py, which gives the adult a hatchet (hidden except while cutting trees) and
   rebuilds the four tree-cutting animations as an overhead chop; run it on its own with
   python3 add_axe.py <out folder> to redo just that.
3. python3 ../build_mod.py <vanilla blueprints> ../dist/Otters ../build/Otters.dll <out folder>

timbermesh.py reads/writes the game's model format; the layout is documented at the top of the file.
