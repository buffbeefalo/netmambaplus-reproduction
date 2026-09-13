"""Instructional diagrams and timed emphasis for the narrated course."""

import math
import re

DIAGRAMS = {'packet-flow', 'byte-layout', 'token-assembly', 'training-loop'}


def draw_diagram(scene, draw, put):
    kind = scene['kind']
    if kind not in DIAGRAMS:
        return False
    ink, teal, blue, coral = '#172c3a', '#126e68', '#d9e9ed', '#b14c36'
    def card(box, title, detail, accent=teal):
        x,y,right,bottom=box
        draw.rounded_rectangle(box,radius=20,fill='#ffffff',outline=blue,width=3)
        draw.rectangle((x+20,y+20,x+27,bottom-20),fill=accent)
        put(title,x+48,y+22,right-x-70,32,accent,True)
        put(detail,x+48,y+78,right-x-70,27,ink)
    if kind == 'packet-flow':
        for i,label in enumerate(['Conversation A','Conversation B']):
            y=370+i*200
            put(label,95,y+20,340,31,teal if i==0 else coral,True)
            draw.line((455,y+70,1405,y+70),fill=blue,width=8)
            for j in range(3):
                x=520+j*275
                draw.rounded_rectangle((x,y+32,x+110,y+109),radius=12,fill=teal if i==0 else coral)
                put(('A' if i==0 else 'B')+str(j+1),x+26,y+48,80,30,'#ffffff',True)
            card((1470,y,1820,y+142),'Flow '+('A' if i==0 else 'B'),'Related packets',teal if i==0 else coral)
        put('Illustration: preserve membership and order; proximity in a CSV is insufficient.',95,792,1720,27,ink)
    elif kind == 'byte-layout':
        for i in range(5):
            x=95+i*346
            card((x,338,x+312,594),f'Packet {i+1}','320 stored\nbyte positions')
            for j in range(8):
                draw.rectangle((x+32+j*30,545,x+55+j*30,564),fill=teal if j%2==0 else blue)
        draw.line((250,650,1640,650),fill=teal,width=6)
        put('5 × 320 = 1,600 stored byte positions',200,686,1530,45,teal,True)
        put('Paper: 80 header + 240 payload allocation. Released extraction history is unverified.',95,794,1720,25,coral)
    elif kind == 'token-assembly':
        for i,(title,detail) in enumerate([('Bytes','1,600 ÷ 4 = 400 tokens'),('Sizes','20 tokens'),('Intervals','20 tokens')]):
            y=310+i*153
            card((95,y,725,y+135),title,detail)
            draw.line((740,y+67,1000,547),fill='#6d979f',width=6)
        card((1040,354,1810,733),'443 tokens × 256 coordinates','400 + 20 + 20 + 3 summaries\n\nInput to all four Mamba blocks')
        put('Tokens are numerical input units; they are not language-model words.',95,790,1720,27,ink)
    else:
        boxes=[(130,310,830,503),(1080,310,1780,503),(1080,585,1780,778),(130,585,830,778)]
        items=[('1  Forward','Compute six category logits'),('2  Loss','Compare with supplied labels'),('3  Backward','Compute parameter gradients'),('4  Update','Optimizer changes model weights')]
        for box,item in zip(boxes,items):card(box,*item)
        for text,x,y in [('→',890,367),('↓',1390,508),('←',890,639),('↑',433,508)]:put(text,x,y,130,55,teal)
        put('Conceptual training cycle · repeated across batches and epochs',95,790,1720,26,ink)
    return True


def ass_time(seconds):
    value=round(seconds*100)
    hours,rest=divmod(value,360000)
    minutes,rest=divmod(rest,6000)
    secs,cs=divmod(rest,100)
    return f'{hours}:{minutes:02}:{secs:02}.{cs:02}'


def phrase_time(scene, phrase):
    normal=lambda text:re.sub(r'[^a-z0-9]','',text.lower())
    wanted=normal(phrase)
    cues=scene['audio']['cues']
    joined=''.join(normal(c['text']) for c in cues)
    if not wanted or joined.count(wanted)!=1:
        raise ValueError('Animation phrase must identify one narration passage: '+scene['id'])
    start=joined.index(wanted)
    cursor=0
    for cue in cues:
        cursor+=len(normal(cue['text']))
        if cursor>start:
            return scene['start']+cue['start']/scene['tempo']
    raise ValueError('Animation phrase has no measured audio boundary')


def animation_events(scenes, chapters, enabled):
    if not enabled:
        return [], []
    lines, records=[],[]
    def event(scene,start,end,tags,shape,meaning):
        if not (math.isfinite(start) and math.isfinite(end) and scene['start']<=start<end<=scene['end']):
            raise ValueError('Animation extends outside its scene')
        lines.append(f'Dialogue: 2,{ass_time(start)},{ass_time(end)},Motion,,0,0,0,,{{{tags}}}{shape}')
        records.append({'scene':scene['id'],'start':start,'end':end,'meaning':meaning})
    for scene in scenes:
        if scene['kind']=='pause':continue
        start,end=scene['start'],scene['end']
        duration=end-start
        # A thin line indicates progress through the current teaching scene.
        ms=round(duration*1000)
        event(scene,start,end,r'\an7\pos(90,840)\p1\c&H686E12&\bord0\fscx0'+f'\\t(0,{ms},\\fscx100)',
              'm 0 0 l 1730 0 l 1730 4 l 0 4','Teaching-scene progress, not live inference')
        kind=scene['kind']
        if kind=='packet-flow':
            for lane in range(2):
                for packet in range(3):
                    begin=start+1.0+packet*2.0+lane*0.7
                    stop=min(end,begin+3.8)
                    y=488+lane*200
                    color='686E12' if lane==0 else '364CB1'
                    event(scene,begin,stop,f'\\an7\\move(455,{y},1405,{y})\\p1\\c&H{color}&\\bord0\\fad(180,180)',
                          'm 0 0 l 22 0 l 22 16 l 0 16','Illustrative packet moving within its declared flow lane')
        if kind=='token-assembly':
            for modality in range(3):
                for token in range(4):
                    begin=start+1+token*1.2+modality*0.35
                    stop=min(end,begin+2.2)
                    y=377+153*modality
                    event(scene,begin,stop,f'\\an7\\move(755,{y},1000,547)\\p1\\c&H686E12&\\bord0\\fad(140,140)',
                          'm 0 0 l 16 0 l 16 16 l 0 16','Illustrative feature tokens entering the sequence')
        boxes=[]
        if kind=='byte-layout':boxes=[(95+i*346,338,407+i*346,594) for i in range(5)]
        elif kind=='training-loop':boxes=[(130,310,830,503),(1080,310,1780,503),(1080,585,1780,778),(130,585,830,778)]
        elif kind in ('flow','views') and len(scene['bullets'])==3:boxes=[(90+i*590,360,620+i*590,675) for i in range(3)]
        elif kind in ('cards','title','question','answer'):
            height=min(122,460//len(scene['bullets']))
            boxes=[(90,330+i*height,1820,330+(i+1)*height-17) for i in range(len(scene['bullets']))]
        elif kind=='code' and scene.get('code'):
            boxes=[(116,329+i*38,1250,367+i*38) for i,line in enumerate(scene['code'].splitlines()) if line.strip()]
        elif kind=='code':boxes=[(90,310,1820,795)]
        elif kind=='table':boxes=[(90,310,1820,785)]
        elif kind=='results':boxes=[(90,315+i*105,1820,405+i*105) for i in range(4)]
        elif kind=='comparison':boxes=[(90,325,920,690),(990,325,1820,690)]
        anchors=scene.get('focus_phrases',[])
        if anchors and len(anchors)!=len(boxes):raise ValueError('Animation focus count does not match its diagram')
        for i,(x,y,right,bottom) in enumerate(boxes):
            begin=phrase_time(scene,anchors[i]) if anchors else start+duration*(0.06+i*0.80/max(1,len(boxes)))
            stop=min(end,begin+max(2.0,min(7.0,duration/max(2,len(boxes)+1))))
            w,h=right-x,bottom-y
            shape=f'm 0 0 l {w} 0 l {w} {h} l 0 {h} l 0 0 m 5 5 l 5 {h-5} l {w-5} {h-5} l {w-5} 5 l 5 5'
            event(scene,begin,stop,f'\\an7\\pos({x},{y})\\p1\\c&H686E12&\\bord0\\fad(250,350)',shape,
                  'Narration-aligned emphasis' if anchors else 'Progressive emphasis of the teaching sequence')
        if kind=='results':
            for i in range(4):
                reveal=phrase_time(scene,anchors[i]) if anchors else start+1+i*2.2
                stop=min(end,reveal+1.8)
                delay=max(0,round((reveal-start)*1000))
                finish=round((stop-start)*1000)
                event(scene,start,stop,
                      f'\\an9\\pos(1550,{325+i*105})\\p1\\c&HEDE9D9&\\bord0\\fscx100\\t({delay},{finish},\\fscx0)',
                      'm 0 0 l 1180 0 l 1180 66 l 0 66',
                      'Reveal of an already measured accuracy bar; not a running training metric')
    return lines,records
