"""Correct only the identified legacy generated Albedo images; leave photos/bakes intact."""
import bpy
import numpy as np
import re


def repair(materials):
    corrected=set();records=[]
    for m in materials:
        if not m or not m.use_nodes or not str(m.get('surface_accuracy','')).startswith('procedural micro-surface'):
            continue
        if m.get('albedo_encoding')=='srgb-byte-v1':continue
        p=m.node_tree.nodes.get('Principled BSDF')
        if not p or not p.inputs['Base Color'].is_linked:continue
        node=p.inputs['Base Color'].links[0].from_node
        if node.type!='TEX_IMAGE' or not node.image or not re.sub(r'\.\d+$','',node.image.name).endswith('_Albedo'):continue
        im=node.image
        if im.name not in corrected:
            pixels=np.empty(len(im.pixels),dtype=np.float32);im.pixels.foreach_get(pixels)
            pixels=pixels.reshape((-1,4));c=pixels[:,:3]
            before=c.mean(axis=0).tolist()
            pixels[:,:3]=np.where(c<=.0031308,c*12.92,1.055*c**(1/2.4)-.055)
            im.pixels.foreach_set(pixels.ravel());im.pack()
            records.append({'material':m.name,'image':im.name,'encoded_mean_before':before,'encoded_mean_after':pixels[:,:3].mean(axis=0).tolist()})
            corrected.add(im.name)
        m['albedo_encoding']='srgb-byte-v1'
    return records
