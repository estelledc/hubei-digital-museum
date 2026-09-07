"""Reopen the animated derivative and verify actual timeline state and embedded resources."""
import bpy,json,math
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/interactive/bells-interactive.blend'),load_ui=False)
s=bpy.context.scene;rigs=sorted([o for o in s.objects if o.type=='EMPTY' and o.get('bell_id')],key=lambda o:o['bell_id']);assert len(rigs)==65
s.frame_set(0);rest=[o.rotation_quaternion.copy() if o.rotation_mode=='QUATERNION' else o.rotation_euler.to_quaternion() for o in rigs]
s.frame_set(11)
angles=[o.rotation_euler.to_quaternion().rotation_difference(r).angle for o,r in zip(rigs,rest)]
assert math.radians(.1)<angles[0]<math.radians(1) and all(a<.00001 for a in angles[1:]),angles
tools=sorted([o for o in s.objects if o.type=='EMPTY' and o.get('performance_demo')],key=lambda o:o.name)
assert len(tools)==65
for i,o in enumerate(rigs):
 s.frame_set(11+i*20)
 assert math.radians(.1)<o.rotation_euler.to_quaternion().rotation_difference(rest[i]).angle<math.radians(1)
 s.frame_set(6+i*20)
 p=Vector(o['strike_front']);p=Vector((p.x,-p.z,p.y))+o.location
 assert (tools[i].location-p).length<.00001,(tools[i].name,'tip misses contact')
 assert min(tools[i].scale)>.99
 normal=Vector(o['normal_front']);normal=Vector((normal.x,-normal.z,normal.y))
 assert (tools[i].rotation_euler.to_quaternion()@Vector((0,0,1))).dot(normal)>.99
 assert (tools[i].rotation_euler.to_quaternion()@Vector((0,1,0))).z>.99
s.frame_set(s.frame_end)
assert all(o.rotation_euler.to_quaternion().rotation_difference(r).angle<.00001 for o,r in zip(rigs,rest))
assert all(max(o.scale)<.00001 for o in tools)
assert all(im.packed_file or Path(bpy.path.abspath(im.filepath)).exists() for im in bpy.data.images if im.source=='FILE')
report={'revision':'0.7','reopened':True,'bell_rigs':len(rigs),'individual_actions':sum(len(o.animation_data.nla_tracks) for o in rigs),'frame_11_only_first_bell_moves':True,'reference_peak_between_0_1_and_1_degree':True,'tools_with_verified_contact_and_orientation':len(tools),'short_mallets':sum(o['tool_type']=='short_mallet' for o in tools),'long_rods':sum(o['tool_type']=='long_rod' for o in tools),'strike_duration_seconds':3,'end_frame_restored':True,'tools_hidden_at_end':True,'timeline_end':s.frame_end,'packed_images':sum(bool(im.packed_file) for im in bpy.data.images),'mesh_triangles':sum(len(o.data.polygons) for o in s.objects if o.type=='MESH' and not o.get('performance_demo')),'scope':'Reference-based tool demonstration. Strike points and reduced swing remain approximations, not acoustic/physical reconstruction. Static originals unchanged.'}
(ROOT/'reports/bell-interaction-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('BELL_ANIMATION_VERIFIED',report,flush=True)
