"""Bake actual Blender base-colour graphs before exporting glTF.

The supplied archive contains Hue/Saturation, Multiply and Noise/ColorRamp
chains which glTF cannot represent directly. Bake the colour graph on a UV
quad; keep the source normal maps and PBR controls. No lighting is baked in.
"""
import bpy

def bake_base_colors(materials, size=1024):
    scene=bpy.context.scene
    previous_engine=scene.render.engine
    previous_samples=scene.cycles.samples
    previous_margin=scene.render.bake.margin
    scene.render.engine='CYCLES';scene.cycles.samples=1
    scene.render.bake.margin=0
    previous_active=bpy.context.view_layer.objects.active
    previous_selected=list(bpy.context.selected_objects)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0,0,10000))
    quad=bpy.context.object
    records=[]
    for material in materials:
        if not material.use_nodes:continue
        bsdf=next((n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
        if bsdf is None or not bsdf.inputs['Base Color'].is_linked:continue
        # Direct textures are already representable. Baking is needed only for a graph.
        if bsdf.inputs['Base Color'].links[0].from_node.type=='TEX_IMAGE':continue
        scratch=material.copy();quad.data.materials.clear();quad.data.materials.append(scratch)
        nodes=scratch.node_tree.nodes;links=scratch.node_tree.links
        p=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
        output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
        emit=nodes.new('ShaderNodeEmission');emit.inputs['Strength'].default_value=1
        source=p.inputs['Base Color'].links[0].from_socket
        links.new(source,emit.inputs['Color']);links.new(emit.outputs[0],output.inputs['Surface'])
        image=bpy.data.images.new('Baked_Albedo_'+material.name,width=size,height=size,alpha=False)
        image.colorspace_settings.name='sRGB'
        target=nodes.new('ShaderNodeTexImage');target.image=image;nodes.active=target
        bpy.context.view_layer.objects.active=quad;quad.select_set(True)
        bpy.ops.object.bake(type='EMIT',use_clear=True)
        image.pack()
        original_nodes=material.node_tree.nodes
        direct=original_nodes.new('ShaderNodeTexImage');direct.name='glTF baked base colour';direct.image=image
        material.node_tree.links.new(direct.outputs['Color'],bsdf.inputs['Base Color'])
        material['base_color_export']='EMIT bake of source graph, no lighting'
        records.append({'material':material.name,'texture':image.name,'size':size,'source_node':source.node.type})
        quad.data.materials.clear();bpy.data.materials.remove(scratch)
    bpy.data.objects.remove(quad,do_unlink=True)
    for o in previous_selected:
        if o.name in bpy.data.objects:o.select_set(True)
    bpy.context.view_layer.objects.active=previous_active
    scene.render.engine=previous_engine
    scene.cycles.samples=previous_samples
    scene.render.bake.margin=previous_margin
    return records
