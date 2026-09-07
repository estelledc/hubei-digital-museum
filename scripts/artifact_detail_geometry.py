"""Focused 0.9 refinements, derived from saved source meshes and their existing photographs.
No source .blend is overwritten. Internal wall and paper thickness remain approximations.
"""
import bpy, bmesh, math
from mathutils import Vector
from artifact_geometry import Builder, interpolate

def refine(slug):
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    collection=objects[0].users_collection[0];b=Builder(collection)
    if slug=='zun':
        refined=0
        for o in objects:
            me=o.data
            if len(me.polygons)<3:continue
            sides=len(me.polygons[-1].vertices)
            if sides not in [6,7,8] or len(me.vertices)%sides or len(me.polygons)!=(len(me.vertices)//sides-1)*sides+2:continue
            # Increase radial sampling of the existing tube sections without
            # inventing more motifs or changing their paths and attachments.
            rings=len(me.vertices)//sides;verts=[];faces=[];count=16
            for j in range(rings):
                ring=[me.vertices[j*sides+k].co.copy() for k in range(sides)];center=sum(ring,Vector())/sides
                u=ring[0]-center;w=(ring[1]-center-u*math.cos(math.tau/sides))/math.sin(math.tau/sides)
                verts.extend([tuple(center+u*math.cos(k*math.tau/count)+w*math.sin(k*math.tau/count)) for k in range(count)])
            faces=[(j*count+k,j*count+(k+1)%count,(j+1)*count+(k+1)%count,(j+1)*count+k) for j in range(rings-1) for k in range(count)]
            faces += [tuple(reversed(range(count))),tuple((rings-1)*count+k for k in range(count))]
            mesh=bpy.data.meshes.new(me.name+'_细化');mesh.from_pydata(verts,[],faces);mesh.update()
            for m in me.materials:mesh.materials.append(m)
            for face in mesh.polygons:face.use_smooth=True
            o.data=mesh;b.uv(o,lambda v:(v.x*12,v.z*12+v.y*7));refined+=1
        return f'{refined} existing ornamental tubes resampled to 16 radial sides; motif count and paths retained'
    if slug=='drum-chongyang':
        bronze=bpy.data.materials['崇阳鼓灰褐青铜'];photo=bpy.data.materials['崇阳铜鼓馆方实拍纹饰']
        for o in objects:bpy.data.objects.remove(o,do_unlink=True)
        # Smooth axial silhouette. Observed right end gets its own registered photo,
        # rather than stretching the photographed side around an untextured disc.
        knots=[(-.24,.181),(-.21,.191),(-.12,.219),(0,.23),(.12,.219),(.21,.191),(.24,.181)]
        profile=interpolate(knots,10);segments=192
        vertices=[(x,r*math.sin(i*math.tau/segments),.39+r*math.cos(i*math.tau/segments)) for x,r in profile for i in range(segments)]
        faces=[(j*segments+i,(j+1)*segments+i,(j+1)*segments+(i+1)%segments,j*segments+(i+1)%segments) for j in range(len(profile)-1) for i in range(segments)]
        body=b.mesh('横置铜鼓鼓身_连续弧面',vertices,faces,bronze)
        body.data.materials.append(photo)
        for face in body.data.polygons:
            if face.center.y<-.035:
                face.material_index=1
                for li in face.loop_indices:
                    v=body.data.vertices[body.data.loops[li].vertex_index].co
                    px=204+(v.x+.24)/.48*244;py=424-(v.z-.16)/.46*259
                    body.data.uv_layers.active.data[li].uv=(px/700,1-py/600)
        for side in [-1,1]:
            vs=[(side*.24,0,.39)]+[(side*.24,.181*math.sin(a),.39+.181*math.cos(a)) for a in [i*math.tau/segments for i in range(segments)]]
            fs=[(0,1+i,1+(i+1)%segments) if side<0 else (0,1+(i+1)%segments,1+i) for i in range(segments)]
            cap=b.mesh('铜鼓右侧可见鼓面' if side>0 else '铜鼓左侧鼓面近似',vs,fs,photo if side>0 else bronze,False)
            if side>0:b.uv(cap,lambda v:((495+v.y/.181*30+(v.z-.39)/.181*15)/700,1-(310-(v.z-.39)/.181*118)/600))
        outline=[(-.13,0),(-.13,.20),(.13,.20),(.13,0),(.059,0),(.057,.056),(.040,.077),(.020,.083),(0,.087),(-.028,.082),(-.052,.062),(-.059,0)]
        base=b.polygon('铜鼓方座_拱形缺口',outline,.19,bronze,.004)
        crown=[(-.103,.620),(-.11,.73),(-.095,.755),(-.075,.748),(-.067,.703),(-.043,.686),(.043,.686),(.067,.703),(.075,.748),(.095,.755),(.11,.73),(.103,.620)]
        top=b.polygon('弧凹冠_可见穿孔',crown,.042,bronze,.003)
        # Round perforation visible in the catalogue photograph.
        bpy.context.view_layer.objects.active=top;top.select_set(True)
        for mod in list(top.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.011,depth=.08,location=(0,0,.651),rotation=(math.pi/2,0,0))
        cutter=bpy.context.object;mod=top.modifiers.new('冠部圆孔','BOOLEAN');mod.object=cutter;mod.operation='DIFFERENCE'
        bpy.context.view_layer.objects.active=top;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
        for o in [base,top]:
            o.data.materials.append(photo)
            photo_index=len(o.data.materials)-1
            for face in o.data.polygons:
                if o.data.materials[face.material_index] is None:face.material_index=0
                if face.normal.y<-.5:
                    face.material_index=photo_index
                    for li in face.loop_indices:
                        v=o.data.vertices[o.data.loops[li].vertex_index].co
                        px,py=(291+(v.x+.11)/.22*126,151-(v.z-.62)/.135*101) if o==top else (272+(v.x+.13)/.26*164,533-v.z/.20*104)
                        o.data.uv_layers.active.data[li].uv=(px/700,1-py/600)
        for o in b.objects:o['accuracy']='Photo-guided visible barrel/end/crest/base; hidden end and depth approximate; no recovered acoustic or relief scan'
        return 'Continuous barrel profile, observed right-end photo, perforated crest and arched base opening'
    if slug=='vase':
        body=objects[0];glaze=body.data.materials[0]
        bm=bmesh.new();bm.from_mesh(body.data)
        bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index==0],context='FACES');bm.to_mesh(body.data);bm.free();body.data.update()
        profile=[(.027,.387),(.024,.379),(.023,.369),(.022,.362),(.047,.354),(.068,.344),(.083,.332),(.092,.316),(.096,.296),(.095,.28),(.088,.23),(.075,.16),(.065,.10),(.060,.06),(.059,.025),(.058,.012),(.040,.009),(0,.009)]
        inside=b.lathe('梅瓶连续内壁_厚度近似',interpolate(profile,5),glaze,192)
        foot=b.lathe('梅瓶圈足底面_近似',[(.065,0),(.055,0),(.055,.004),(0,.004)],glaze,192)
        for face in foot.data.polygons:face.flip()
        for o in [inside,foot]:o['accuracy']='Estimated 3-5 mm wall and approximate foot underside; not CT or measured internal geometry'
        return 'Continuous estimated inner wall and ring-foot underside; original exterior photo atlas retained'
    if slug=='manuscript-xiong':
        leaf=next(o for o in objects if o.name.startswith('稿本微曲'))
        material=leaf.data.materials[0];bpy.data.objects.remove(leaf,do_unlink=True)
        cols,rows=48,64;vs=[];fs=[]
        for j in range(rows+1):
            z=.29*j/rows
            for i in range(cols+1):
                u=i/cols;x=-.105+.21*u
                y=-.001-.0025*math.sin(math.pi*u)**2-.0008*u**5*math.cos(z/.29*math.pi)
                vs.append((x,y,z))
        for j in range(rows):
            for i in range(cols):
                a=j*(cols+1)+i;fs.append((a,a+1,a+cols+2,a+cols+1))
        leaf=b.mesh('稿本微曲纸面_实际照片页',vs,fs,material)
        b.uv(leaf,lambda v:(.028+(v.x+.105)/.21*.819,.024+v.z/.29*.956))
        solid=leaf.modifiers.new('纸页薄边近似','SOLIDIFY');solid.thickness=.00014;solid.offset=0
        leaf['accuracy']='Existing photographed leaf; gentle curvature and 0.14 mm thickness are display estimates, no new page content'
        return 'Curved photographed leaf with a thin edge; no invented pages or text'
    return None

# Details are anchored to existing objects before they are joined into display groups.
# (label, source-name prefixes, view direction in glTF coordinates)
DETAILS={
 'sword':[
  ('剑身菱形纹与中脊',('剑身',),(0,0,1)),('剑格蓝绿嵌饰',('剑格嵌饰',),(.15,.15,1)),
  ('剑格曲线与细槽',('剑格细嵌槽','剑格_'),(0,.15,1)),('剑茎环箍',('剑茎环箍',),(.45,.1,1)),
  ('剑首十一道同心圆',('剑首十一道',),(0,1,.25))],
 'zun':[
  ('盘足兽首',('盘足兽首','兽首双目'),(.45,.25,1)),('兽形片状盘足',('盘足_',),(.4,.15,1)),
  ('盘口透空细节',('多层蟠虺','口沿外层'),(.3,.9,1)),('抠手盘蛇',('抠手镂空','盘四抠手'),(.3,.6,1)),
  ('尊颈攀附附件',('尊颈','反首豹','豹'),(.3,.3,1)),('卷曲浮雕',('蟠螭',),(.25,.2,1))],
 'drum':[
  ('卧虎头部与卷尾',('卧虎上卷','卧虎_','虎尾'),(.15,.2,1)),('凤鸟冠首',('凤鸟_张喙','凤冠'),(0,.1,1)),
  ('凤翼羽线',('凤翼','鸟翼'),(0,.15,1)),('承鼓小兽',('承鼓小兽','小兽承托'),(.2,.1,1)),
  ('鼓框断口',('缺损鼓腔',),(.2,.25,1))],
 'bamboo':[('照片文字与边缘',('秦简_',),(0,0,1))],
 'ding-jian':[
  ('鼎腹内腔',('铜方鼎_',),(.25,1,.8)),('双耳轮廓',('竖向环耳',),(.35,.35,1)),
  ('柱足凸弦纹',('柱足凸弦纹',),(.3,.15,1)),('扉棱凸齿',('扉棱凸齿',),(.4,.2,1))],
 'carving-wudang':[
  ('照片中的山门与人物',('武当朝圣图',),(0,0,1)),('玉石托座轮廓',('独山玉',),(.3,.5,1)),
  ('木托卷足',('木托卷足',),(.3,.2,1))],
 'manuscript-xiong':[
  ('实拍页文字与纸边',('稿本微曲',),(0,0,1)),('纸册边缘层次',('纸页叠层',),(.3,-.3,1)),
  ('封底厚度近似',('稿本封底',),(.4,.15,-1))],
 'office-dong':[
  ('窗格与护墙',('木窗','窗下'),(0,.2,1)),('抽屉拉手外观',('抽屉金属','书桌抽屉面'),(.2,.25,1)),
  ('绿色台灯',('台灯','绿色台灯'),(.35,.5,1)),('木椅靠背',('木椅靠背','木椅上横'),(.3,.3,1)),
  ('书架层板与书册',('木书架','书架陈列'),(.3,.3,1)),('茶杯与茶几',('茶杯','圆茶几'),(.4,.7,1))]
}

def detail_anchors(slug, group, bounds):
    points=[]
    for label,prefixes,direction in DETAILS.get(slug,[]):
        matches=[o for o in group if o.name.startswith(prefixes)]
        if not matches:continue
        # Repeated ornament: show a real visible example, not an oversized bounding box of all repetitions.
        if len(matches)>4:
            matches=sorted(matches,key=lambda o:sum(v.y for v in bounds([o]))/2)[:1]
        lo,hi=bounds(matches);center=(lo+hi)/2;span=max(hi-lo)
        if slug=='bamboo':center.z=.14;span=.085
        if slug=='sword' and prefixes==('剑身',):center.z=.33;span=.16
        if slug=='carving-wudang' and prefixes==('武当朝圣图',):center.z=.36;span=.20
        if slug=='manuscript-xiong' and prefixes==('稿本微曲',):center.z=.20;span=.12
        if slug=='drum' and prefixes==('缺损鼓腔',):span=max(span,.10)
        if slug=='zun':span=max(span,.09)
        points.append((label,center,max(span,.012),direction))
    return points
