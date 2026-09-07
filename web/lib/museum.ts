import type { Object3D } from 'three';

export function setSpaceCutaway(root: Object3D, hidden: boolean) {
  root.traverse((object) => {
    const part = String(object.userData.part || '');
    // glTF may represent a multi-material roof as a Group containing meshes.
    if (
      object.userData.roof ||
      part.startsWith('05_') ||
      part.startsWith('02_')
    )
      object.visible = !hidden;
  });
}

export const publicViews: Record<
  string,
  { label: string; camera: number[]; target: number[]; fov: number }[]
> = {
  campus: [
    {
      label: '园区总览',
      camera: [190, 148, 247],
      target: [0, 2, -53],
      fov: 31.186,
    },
    {
      label: '南广场',
      camera: [54, 3, 102],
      target: [0, 10, 8],
      fov: 41.112,
    },
    {
      label: '北馆庭院',
      camera: [69, 15, -197],
      target: [0, 13, -112],
      fov: 38.88,
    },
  ],
  arrival: [
    {
      label: '入口全景',
      camera: [10, 1.7, 24],
      target: [0, 2.3, 1],
      fov: 53.13,
    },
    {
      label: '服务台近看',
      camera: [19, 1.65, 24],
      target: [12, 1.25, 15],
      fov: 49.55,
    },
    {
      label: '下层大厅',
      camera: [8, -5.12, 24],
      target: [0, -3.4, 0],
      fov: 53.13,
    },
  ],
  atrium: [
    {
      label: '树形中庭',
      camera: [9, 9.4, 21],
      target: [-8, 15.2, -10],
      fov: 57.221,
    },
    {
      label: '旋梯近看',
      camera: [-9, 10, 22],
      target: [-20, 11.8, 8],
      fov: 53.13,
    },
    {
      label: '临窗环廊',
      camera: [-27, 15.25, 24],
      target: [17, 15.5, 15],
      fov: 51.282,
    },
  ],
  connection: [
    {
      label: '通道全景',
      camera: [2, 1.65, 21],
      target: [0, 1.8, -12],
      fov: 47.925,
    },
    {
      label: '北馆端',
      camera: [-2, 1.65, -16],
      target: [0, 2, -24],
      fov: 49.55,
    },
    {
      label: '南馆端',
      camera: [2, 1.65, -17],
      target: [0, 1.9, 22],
      fov: 47.925,
    },
  ],
};

export const artifacts = [
  {
    id: 'bells',
    title: '曾侯乙编钟',
    era: '战国早期',
    floor: '南馆 · 曾侯乙',
    provenance: '存档模型',
    dimension: '65 件 · 钟架长 7.48 m、高 2.65 m',
    description:
      '三层八组、曲尺形钟架。复用你提供的考据校正版，保留钟体与现代展台；浏览版已提高网格和贴图精度，完整细节保留在 Blender 工程中。',
    limit: '存档建模资产，未经扫描精度认证；包围盒包含现代展台。',
    url: 'https://www.hbww.org.cn/zgzb/p/4695.html',
  },
  {
    id: 'chimes',
    title: '曾侯乙编磬',
    era: '战国早期',
    floor: '南馆 · 曾侯乙',
    provenance: '存档模型',
    dimension: '32 枚石磬 · 两层、每层 16 枚',
    description:
      '与编钟共同组成曾侯乙墓的礼乐器群。复用考据校正版编磬，保留悬挂结构、磬石和展台。',
    limit: '复用用户存档，陈列位置为数字场景近似安排。',
    url: 'https://www.hbww.org.cn/cszl/p/4676.html',
  },
  {
    id: 'sword',
    title: '越王勾践剑',
    era: '春秋晚期',
    floor: '南馆二层',
    provenance: '照片依据补建',
    dimension: '长 55.6 cm · 宽 5 cm',
    description:
      '按馆方尺寸重建薄刃、中脊、曲线剑格及外翻剑首，以实拍照片呈现剑身菱形纹和鸟篆铭文。',
    limit: '剑身正面为实拍投影；背面、精细截面及镶嵌槽仍近似，铭文未另行雕刻。',
    url: 'https://www.hbww.org.cn/zgzb/p/4694.html',
  },
  {
    id: 'zun',
    title: '曾侯乙尊盘',
    era: '战国早期',
    floor: '南馆 · 曾侯乙',
    provenance: '照片依据补建',
    dimension: '尊高 30.1 cm · 盘口径 58 cm',
    description:
      '按多角度实拍重建浅腹盘、圈足尊、分层透空口沿、四处抠手、兽形盘足与颈部攀附附件。',
    limit:
      '装饰结构比首版细化，但龙蛇数量、连接拓扑和嵌合深度仍近似；未取得馆方 CT 网格。',
    url: 'https://www.hbww.org.cn/zgzb/p/6911.html',
  },
  {
    id: 'drum',
    title: '虎座鸟架鼓',
    era: '战国',
    floor: '南馆三层 · 楚文化主题',
    provenance: '照片依据补建',
    dimension: '原器高 135.9 cm · 宽 134 cm',
    description:
      '对照九连墩二号墓器物照片重建伏虎卷尾、凤鸟弧颈、羽翼、承鼓小兽与缺损鼓框，公开版表面使用近似漆色，不包含馆方目录照片。',
    limit:
      '高与宽按馆方尺寸校准，厚度和背面近似。鼓框沿用馆方目录的缺损状态；2021 展柜照片中的鼓面性质未核实。',
    url: 'https://www.hbww.org.cn/zgzb/p/6913.html',
  },
  {
    id: 'vase',
    title: '元青花四爱图梅瓶',
    era: '元代',
    floor: '北馆三层 · 陶瓷主题',
    provenance: '照片依据补建',
    dimension: '高 38.7 cm · 口径 6.4 cm',
    description:
      '2006 年出土于钟祥郢靖王墓。按尺寸与照片重建短颈、丰肩、圈足，并用四面实拍补齐四爱故事纹饰。',
    limit:
      '四面照片的环向位置与拼接近似，照片仍有展柜反光；内壁厚度与圈足底面为近似，未经内部测绘。',
    url: 'https://www.hbww.org.cn/zgzb/p/4696.html',
  },
  {
    id: 'bamboo',
    title: '云梦睡虎地秦简',
    era: '秦',
    floor: '南馆三层 · 楚文化主题',
    provenance: '照片依据补建',
    dimension: '五枚照片依据补建 · 不代表完整简数',
    description:
      '1975 年出土于云梦睡虎地秦墓。改为馆方照片中实际展示的五枚竹简，保留窄条形态和断痕；公开版未收录文字照片。',
    limit:
      '公开版仅展示近似竹材，不展示或补写文字；25 cm 展示尺度与厚度为近似，当前展位未核实。',
    url: 'https://www.hbww.org.cn/zgzb/p/6912.html',
  },
  {
    id: 'ding-jian',
    title: '曾侯谏铜方鼎',
    era: '西周',
    floor: '曾世家',
    dimension: '近似高 57.8 cm；原器尺寸未取得',
    description:
      '依照实拍建立中空折壁鼎腹、四足、双耳与角部扉棱，正面纹带采用实拍投影。',
    limit: '比例及背面纹饰近似；不得用模型尺寸反推原器尺寸。',
    url: 'https://www.hbww.org.cn/xwdt/p/7400.html',
    provenance: '照片依据补建',
  },
  {
    id: 'gold-liang',
    title: '梁庄王金锭',
    era: '明代',
    floor: '梁庄王珍藏',
    dimension: '原器重 1937 g；展示高度 14 cm 为近似',
    description:
      '依据馆方照片建立束腰锭形与闭合器身；公开版使用近似金色，不展示照片铭文。',
    limit: '背面和厚度未测绘；当前具体展柜未核实，按梁庄王墓主题陈列。',
    url: 'https://www.hbww.org.cn/xwdt/p/6897.html',
    provenance: '照片依据补建',
  },
  {
    id: 'pottery-bell',
    title: '石家河陶铃',
    era: '新石器时代',
    floor: '天籁',
    dimension: '高 5.4 cm · 口径 9.8 × 7.0 cm',
    description:
      '依据馆方公开 VR 的两视角照片与尺寸，重建椭圆口、中空器身和顶部双孔。',
    limit: '依据 2026 年公开 VR 版本；背面刻纹与壁厚近似，未核对线下当日撤换。',
    url: 'https://3dvr4.marslanding.com.cn/',
    provenance: '照片依据补建',
  },
  {
    id: 'drum-chongyang',
    title: '崇阳铜鼓',
    era: '商代',
    floor: '古代文明',
    dimension: '原器高 75.5 cm',
    description:
      '按馆方照片细化连续弧面鼓身、可见侧鼓面、冠部圆孔及拱形座口，公开版使用近似青铜材质。',
    limit: '横截面、进深与隐藏纹饰近似；以较新的北馆展览资料安排主题归属。',
    url: 'https://www.hbww.org.cn/zgzb/p/6916.html',
    provenance: '照片依据补建',
  },
  {
    id: 'jade-shijiahe',
    title: '石家河玉人',
    era: '新石器时代',
    floor: '古代文明',
    dimension: '展示高 7 cm；原器尺寸未取得',
    description:
      '依馆方照片描出器形，制作闭合浅浮雕轮廓；公开版未收录面部与冠部照片纹饰。',
    limit:
      '公开版为近似色浅浮雕轮廓，深度、背面和尺度近似，不能替代完整立体雕刻或扫描。',
    url: 'https://www.hbww.org.cn/zgzb/p/6915.html',
    provenance: '照片依据补建',
  },
  {
    id: 'carving-wudang',
    title: '武当朝圣图',
    era: '当代 · 袁嘉骐',
    floor: '巧夺天工',
    dimension: '雕件高 44 cm；底座另计',
    description:
      '沿绿松石雕的照片轮廓建立闭合浮雕体，公开版使用近似颜色，另建玉石与木底座。',
    limit:
      '人物、建筑的纵深未从照片恢复；公开版仅保留浅浮雕轮廓，底座形态近似。',
    url: 'https://www.hbww.org.cn/p/9380.html',
    provenance: '照片依据补建',
  },
  {
    id: 'medal-lizuodong',
    title: '李作栋勋四位章',
    era: '民国',
    floor: '近代风云',
    dimension: '展示直径约 8 cm；原器尺寸未取得',
    description:
      '依据馆方照片建立多瓣轮廓与闭合金属厚度；公开版未收录照片章面与珐琅细节。',
    limit: '背面、边缘起伏和尺度近似；公开版采用近似金属色。',
    url: 'https://www.hbww.org.cn/xwdt/p/9632.html',
    provenance: '照片依据补建',
  },
  {
    id: 'manuscript-xiong',
    title: '熊秉坤稿本',
    era: '近代',
    floor: '近代风云',
    dimension: '展示页高 29 cm；原册尺寸未取得',
    description:
      '《前清工程八营革命实录》稿本。保留微曲纸面、薄纸边、纸册厚度和封底；公开版采用空白近似纸材。',
    limit:
      '公开版未收录文字页面；曲度、纸厚和封底为近似，不补写未见页或缺失文字。',
    url: 'https://www.hbww.org.cn/xwdt/p/9632.html',
    provenance: '照片依据补建',
  },
  {
    id: 'office-dong',
    title: '董必武办公室展陈',
    era: '历史场景复原',
    floor: '现当代英杰',
    dimension: '展陈空间尺寸为近似',
    description:
      '参照馆方展厅照片建立写字台、木窗、书柜、茶桌和椅子，可从多角度查看。',
    limit:
      '这是展陈场景近似；未确认每件家具是否为历史原件，窗景与陈设细节未复原。',
    url: 'https://www.hbww.org.cn/cszl/p/10713.html',
    provenance: '展陈场景近似',
  },
];
export const spaces = [
  {
    id: 'campus',
    title: '园区全景',
    floor: '南馆 · 北馆 · 西馆',
    position: [0, 35, 0],
    camera: [190, 148, 247],
    target: [0, 2, -53],
    model: 'museum-architecture',
    artifacts: [],
    description:
      '按建筑照片与总平面深化旧馆窗带与挑檐、南馆浅浮雕、基座庭院、南广场台阶和湖岸步道；可切换三个观察位置。地形、纹样、树位与细部尺寸仍近似。',
    url: 'https://design.citic/portal/article/index/id/3220.html',
  },
  {
    id: 'arrival',
    title: '南入口与服务区',
    floor: '南馆入口大厅 · 上下层公共空间',
    position: [0, -20, 0],
    camera: [10, 1.7, 24],
    target: [0, 2.3, 1],
    model: 'public/arrival',
    artifacts: [],
    description:
      '圆形挑空、玻璃栏杆、光纤灯幕与服务台近看；补门厅纵深、柱墙拼缝和设备细节。台位、灯幕光点仍近似，背景墙图案未复原。',
    url: 'https://design.citic/portal/article/index/id/3220.html',
  },
  {
    id: 'atrium',
    title: '南馆中庭',
    floor: '南馆 · 公共空间',
    position: [0, 0, 0],
    camera: [9, 9.4, 21],
    target: [-8, 15.2, -10],
    model: 'public/atrium',
    artifacts: [],
    description:
      '通透玻璃环廊、连续树形分叉、夹胶天窗、旋梯接层与防滑嵌条；可切换树形中庭、旋梯及临窗视角。构件尺寸与窗外景观为近似。',
    url: 'https://design.citic/portal/article/index/id/3220.html',
  },
  {
    id: 'connection',
    title: '新旧馆连接空间',
    floor: '南馆至北馆 · 公共空间',
    position: [0, 56, 13.6],
    camera: [2, 1.65, 21],
    target: [0, 1.8, -12],
    model: 'public/connection',
    artifacts: [],
    description:
      '依据建筑衔接关系和三层通道实拍，深化玻璃段、两端石材门厅、门框、扶手与窗外庭院；可分别查看南北两端。长度、分格与家具位置近似。',
    url: 'https://design.citic/portal/article/index/id/3220.html',
  },
  {
    id: 'theatre',
    title: '编钟演奏厅',
    floor: '南馆负一层 · 公共空间',
    position: [-48, 0, -6.8],
    camera: [2, 2.65, 9],
    target: [0, 2.8, -8],
    model: 'public/theatre',
    artifacts: [],
    description:
      '按建筑资料的红黑色调补建舞台与观众席，并设置明确标注的演奏场景编钟副本。座席数量、舞台布置与乐器位置近似。',
    url: 'https://design.citic/portal/article/index/id/3220.html',
  },
  {
    id: 'terrace',
    title: '四层观景平台',
    floor: '南馆四层 · 公共空间',
    position: [0, 0, 20.4],
    camera: [20, 22.1, -36],
    target: [0, 18, -95],
    model: 'museum-architecture',
    artifacts: [],
    description:
      '从高层平台观看新旧馆关系。平台与护栏依据建筑照片补建；标高及观景路线未测绘。',
    url: 'https://design.citic/portal/article/index/id/3220.html',
  },
  {
    id: 'zeng',
    title: '曾侯乙',
    floor: '南馆一、二层',
    position: [-48, 0, 0],
    camera: [8, 2.6, 12],
    target: [0, 1.25, 0],
    model: 'galleries/zeng',
    artifacts: ['bells', 'chimes', 'zun'],
    description:
      '礼乐重器 · 数字展陈近似。已建立独立展厅与代表展品；展墙、展柜坐标及未见细节近似，未复现全部在展藏品。',
    url: 'https://www.hbww.org.cn/cszl/p/4676.html',
  },
  {
    id: 'sword-hall',
    title: '越王勾践剑特展',
    floor: '南馆二层',
    position: [48, -13, 6.8],
    camera: [2.2, 1.75, 4.7],
    target: [0, 1.25, 0],
    model: 'galleries/sword-hall',
    artifacts: ['sword'],
    description:
      '春秋晚期 · 馆方尺寸与实拍依据。已建立独立展厅与代表展品；展墙、展柜坐标及未见细节近似，未复现全部在展藏品。',
    url: 'https://www.hbww.org.cn/cszl/p/7387.html',
  },
  {
    id: 'family',
    title: '曾世家',
    floor: '南馆二层',
    position: [48, 17, 6.8],
    camera: [2.2, 1.75, 4.7],
    target: [0, 1.25, 0],
    model: 'galleries/family',
    artifacts: ['ding-jian'],
    description:
      '考古揭秘的曾国 · 陈列位置近似。已建立独立展厅与代表展品；展墙、展柜坐标及未见细节近似，未复现全部在展藏品。',
    url: 'https://www.hbww.org.cn/cszl/p/7386.html',
  },
  {
    id: 'chu',
    title: '楚国八百年',
    floor: '南馆三层',
    position: [-48, 0, 13.6],
    camera: [4, 2.0, 7],
    target: [0, 1.25, 0],
    model: 'galleries/chu',
    artifacts: ['drum', 'bamboo'],
    description:
      '漆木与文字 · 照片依据补建。已建立独立展厅与代表展品；展墙、展柜坐标及未见细节近似，未复现全部在展藏品。',
    url: 'https://www.hbww.org.cn/cszl/p/7385.html',
  },
  {
    id: 'liang',
    title: '梁庄王珍藏',
    floor: '南馆三层',
    position: [48, 0, 13.6],
    camera: [2.2, 1.75, 4.7],
    target: [0, 1.25, 0],
    model: 'galleries/liang',
    artifacts: ['gold-liang'],
    description:
      '明代藩王 · 海上交流。已建立独立展厅与代表展品；展墙、展柜坐标及未见细节近似，未复现全部在展藏品。',
    url: 'https://www.hbww.org.cn/cszl/p/4698.html',
  },
  {
    id: 'music',
    title: '天籁',
    floor: '南馆负一层',
    position: [48, 0, -6.8],
    camera: [2.2, 1.75, 4.7],
    target: [0, 1.25, 0],
    model: 'galleries/music',
    artifacts: ['pottery-bell'],
    description:
      '湖北早期乐器 · 陶铃据官方 VR 2026 版本。已建立独立展厅与代表展品；展墙、展柜坐标及未见细节近似，未复现全部在展藏品。',
    url: 'https://www.hbww.org.cn/cszl/p/12832.html',
  },
  {
    id: 'craft',
    title: '巧夺天工',
    floor: '西馆二层',
    position: [-95, 82, 6.8],
    camera: [2.2, 1.75, 4.7],
    target: [0, 1.25, 0],
    model: 'galleries/craft',
    artifacts: ['carving-wudang'],
    description:
      '湖北工艺美术作品。已建立独立展厅与代表展品；展墙、展柜坐标及未见细节近似，未复现全部在展藏品。',
    url: 'https://www.hbww.org.cn/cszl/p/10718.html',
  },
  {
    id: 'ancient',
    title: '极目楚天 · 古代文明',
    floor: '北馆二层',
    position: [0, 98, 6.8],
    camera: [4, 1.9, 7],
    target: [0, 1.25, 0],
    model: 'galleries/ancient',
    artifacts: ['drum-chongyang', 'jade-shijiahe'],
    description:
      '史前至明清 · 代表藏品。已建立独立展厅与代表展品；展墙、展柜坐标及未见细节近似，未复现全部在展藏品。',
    url: 'https://www.hbww.org.cn/cszl/p/10715.html',
  },
  {
    id: 'ceramics',
    title: '荆楚陶雅 瓷韵江夏',
    floor: '北馆三层',
    position: [-17, 112, 13.6],
    camera: [2.2, 1.75, 4.7],
    target: [0, 1.25, 0],
    model: 'galleries/ceramics',
    artifacts: ['vase'],
    description:
      '馆藏历代陶瓷。已建立独立展厅与代表展品；展墙、展柜坐标及未见细节近似，未复现全部在展藏品。',
    url: 'https://www.hbww.org.cn/cszl/p/10716.html',
  },
  {
    id: 'modern',
    title: '极目楚天 · 近代风云',
    floor: '北馆三层',
    position: [17, 112, 13.6],
    camera: [2.2, 1.75, 4.7],
    target: [0, 1.25, 0],
    model: 'galleries/modern',
    artifacts: ['medal-lizuodong', 'manuscript-xiong'],
    description:
      '1840—1919 · 馆藏文献与器物。已建立独立展厅与代表展品；展墙、展柜坐标及未见细节近似，未复现全部在展藏品。',
    url: 'https://www.hbww.org.cn/cszl/p/10714.html',
  },
  {
    id: 'people',
    title: '极目楚天 · 现当代英杰',
    floor: '北馆四层',
    position: [0, 112, 20.4],
    camera: [1, 1.9, 6],
    target: [0, 1.25, 0],
    model: 'galleries/people',
    artifacts: ['office-dong'],
    description:
      '董必武办公室展陈 · 照片依据近似。已建立独立展厅与代表展品；展墙、展柜坐标及未见细节近似，未复现全部在展藏品。',
    url: 'https://www.hbww.org.cn/cszl/p/10713.html',
  },
];
export const sources = [
  {
    title: '馆方 · 当前常设展览目录',
    url: 'https://www.hbww.org.cn/cszl/index.html',
    note: '展览名称与楼层归属',
  },
  {
    title: '中信设计 · 三期扩建竣工资料',
    url: 'https://design.citic/portal/article/index/id/3220.html',
    note: '新旧馆关系、外形与中庭结构',
  },
  {
    title: '建筑学院 · 总平面与四层建筑图',
    url: 'https://www.archcollege.com/50808.html',
    note: '图纸署名中信设计；比例尺估计不等于测绘',
  },
  {
    title: '馆方 · 虚拟展览',
    url: 'https://www.hbww.org.cn/xnzl/index.html',
    note: '可跳转官方全景，与近似模型对照',
  },
  {
    title: '馆方 · 曾侯乙三维全景',
    url: 'https://3dvr3.marslanding.com.cn/',
    note: '已查看实际展厅；未下载其扫描资产',
  },
  {
    title: '文物高清照片与纹理署名',
    url: '/research/fidelity-credits.md',
    note: 'Siyuwj、三十三画生、Liuxingy · CC BY-SA 4.0；照片投影与接缝处理说明',
  },
];
