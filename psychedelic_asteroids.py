#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
  ★ PSYCHEDELIC ASTEROIDS ★  v4.0 — LASER ARSENAL EDITION
  Retro Asteroids clone with trippy colors, 8-bit sounds & BGM
  Controls: ←→/AD Rotate | ↑/W Thrust | SPACE Shoot | H Hyperspace
            B Bomb | LSHIFT Dash | P Pause | M Music | C CRT | ESC Quit
═══════════════════════════════════════════════════════════════════════════
"""

import pygame, math, random, numpy as np, sys, os, json

pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
pygame.init()

WIDTH, HEIGHT = 1000, 750
FPS = 60
CX, CY = WIDTH // 2, HEIGHT // 2
try:
    HS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".psyche_hs.json")
except NameError:
    HS_FILE = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), ".psyche_hs.json")

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("★ PSYCHEDELIC ASTEROIDS ★ v4.0 LASER ARSENAL")
clock = pygame.time.Clock()
SR = 44100

# ──────────────────────────────────────
#  SOUND ENGINE
# ──────────────────────────────────────
def gen_snd(freq, dur, wt="square", vol=0.3, fend=None, vib=0, nmix=0.0):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    fe = fend if fend else freq
    fs = np.linspace(freq, fe, len(t))
    if vib: fs += vib * np.sin(2 * np.pi * 6 * t)
    ph = 2 * np.pi * np.cumsum(fs) / SR
    w = {"square": np.sign(np.sin(ph)), "sawtooth": 2*(fs*t%1)-1,
         "triangle": 2*np.abs(2*(fs*t%1)-1)-1, "sine": np.sin(ph),
         "noise": np.random.uniform(-1,1,len(t))}.get(wt, np.sign(np.sin(ph)))
    if nmix > 0: w = (1-nmix)*w + nmix*np.random.uniform(-1,1,len(t))
    att, dec = int(.01*SR), int(.05*SR)
    rel = int(min(.15, dur*.5)*SR)
    sus = max(0, len(w)-att-dec-rel)
    env = np.ones(len(w))
    if att: env[:att] = np.linspace(0,1,att)
    if dec and att+dec<=len(w): env[att:att+dec] = np.linspace(1,.7,dec)
    if sus: env[att+dec:att+dec+sus] = .7
    if rel and att+dec+sus+rel<=len(w): env[att+dec+sus:] = np.linspace(.7,0,rel)
    w = np.clip(w*env*vol*32767,-32767,32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack((w,w)))

def gen_bgm(bpm=138, bars=4, npb=8):
    bps=bpm/60; sd=bps/2; ts=bars*npb; td=ts*sd; n=int(SR*td); w=np.zeros(n)
    bp=[55,55,65.4,73.4,55,82.4,73.4,65.4,55,55,65.4,73.4,82.4,73.4,65.4,55,
        61.7,61.7,73.4,82.4,61.7,87.3,82.4,73.4,55,55,82.4,73.4,65.4,55,73.4,65.4]
    ap=[220,261.6,329.6,392,440,392,329.6,261.6,246.9,293.7,349.2,415.3,493.9,415.3,349.2,293.7,
        261.6,329.6,392,523.3,523.3,440,392,329.6,220,261.6,329.6,392,440,523.3,493.9,440]
    for i in range(ts):
        s,e=int(i*sd*SR),min(int((i+1)*sd*SR),n); l=e-s
        if l<=0: continue
        tl=np.linspace(0,sd,l,False)
        bf=bp[i%len(bp)]; be=np.ones(l); fd=min(int(.005*SR),l)
        if fd: be[:fd]=np.linspace(0,1,fd); be[-fd:]=np.linspace(1,.3,fd)
        w[s:e]+=np.sign(np.sin(2*np.pi*bf*tl))*.08*be
        af=ap[i%len(ap)]; w[s:e]+=(2*np.abs(2*(af*tl%1)-1)-1)*.04*np.exp(-3*tl/sd)
        if i%2==0: w[s:e]+=np.random.uniform(-1,1,l)*.03*np.exp(-20*tl/sd)
        if i%4==0: kf=150*np.exp(-15*tl/sd)+40; w[s:e]+=np.sign(np.sin(2*np.pi*np.cumsum(kf)/SR*np.ones(l)))*.12*np.exp(-8*tl/sd)
        if i%4==2: w[s:e]+=np.random.uniform(-1,1,l)*.06*np.exp(-12*tl/sd)+np.sin(2*np.pi*200*tl)*.04*np.exp(-15*tl/sd)
    return pygame.sndarray.make_sound(np.clip(w*32767,-32767,32767).astype(np.int16).repeat(2,axis=1))

def make_sounds():
    S={}
    S["shoot"]=gen_snd(880,.08,"square",.2,fend=1760,nmix=.1)
    S["shoot_spread"]=gen_snd(660,.12,"square",.18,fend=1320,nmix=.15)
    S["shoot_multi"]=gen_snd(440,.15,"square",.15,fend=880)
    S["shoot_homing"]=gen_snd(600,.1,"triangle",.15,fend=1200)
    S["shoot_explosive"]=gen_snd(200,.15,"sawtooth",.2,fend=100,nmix=.3)
    S["shoot_chain"]=gen_snd(1000,.12,"square",.15,fend=500)
    S["shoot_freeze"]=gen_snd(1800,.1,"sine",.15,fend=2400)
    S["shoot_pierce"]=gen_snd(1200,.15,"sawtooth",.15,fend=2400,nmix=.05)
    S["thrust"]=gen_snd(55,.12,"sawtooth",.15,fend=40,nmix=.6)
    S["explode_small"]=gen_snd(400,.25,"noise",.3,fend=80,nmix=.9)
    S["explode_big"]=gen_snd(200,.5,"noise",.35,fend=30,nmix=.85)
    S["player_death"]=gen_snd(600,.8,"square",.3,fend=40,vib=30,nmix=.3)
    S["extra_life"]=gen_snd(440,.5,"triangle",.25,fend=1320)
    S["level_up"]=gen_snd(330,.6,"square",.2,fend=990,vib=10)
    S["hyperspace"]=gen_snd(1500,.3,"sawtooth",.2,fend=50,nmix=.4)
    S["select"]=gen_snd(660,.1,"square",.2,fend=880)
    S["powerup"]=gen_snd(523,.35,"triangle",.25,fend=1047,vib=5)
    S["combo"]=gen_snd(700,.15,"square",.15,fend=1400)
    S["shield_hit"]=gen_snd(300,.2,"sine",.25,fend=600)
    S["boss_hit"]=gen_snd(100,.15,"noise",.3,fend=200,nmix=.5)
    S["boss_die"]=gen_snd(80,1.2,"noise",.4,fend=20,nmix=.7)
    S["wave_announce"]=gen_snd(440,.8,"triangle",.2,fend=880)
    S["pause"]=gen_snd(330,.15,"square",.15,fend=220)
    S["bomb"]=gen_snd(60,1.0,"noise",.4,fend=20,nmix=.8)
    S["dash"]=gen_snd(900,.12,"sine",.2,fend=1800)
    S["ufo_shoot"]=gen_snd(1200,.06,"square",.12,fend=600,nmix=.3)
    S["ufo_die"]=gen_snd(300,.4,"sawtooth",.25,fend=50,nmix=.5)
    S["streak"]=gen_snd(880,.5,"triangle",.2,fend=1760,vib=20)
    S["blackhole"]=gen_snd(40,2.0,"sine",.15,fend=20,vib=5)
    S["ice_hit"]=gen_snd(1500,.1,"triangle",.2,fend=3000)
    S["fire_hit"]=gen_snd(200,.2,"sawtooth",.25,fend=100,nmix=.4)
    S["chain_jump"]=gen_snd(1400,.08,"square",.12,fend=700)
    S["explosive_aoe"]=gen_snd(100,.3,"noise",.25,fend=30,nmix=.7)
    S["freeze_hit"]=gen_snd(2000,.15,"triangle",.15,fend=800)
    S["ghost_phase"]=gen_snd(500,.2,"sine",.1,fend=1500)
    S["magnet_pickup"]=gen_snd(660,.2,"triangle",.15,fend=1320)
    return S

# ──────────────────────────────────────
#  COLORS
# ──────────────────────────────────────
def hsv(h,s,v):
    h%=360; c=v*s; x=c*(1-abs((h/60)%2-1)); m=v-c
    if h<60: r,g,b=c,x,0
    elif h<120: r,g,b=x,c,0
    elif h<180: r,g,b=0,c,x
    elif h<240: r,g,b=0,x,c
    elif h<300: r,g,b=x,0,c
    else: r,g,b=c,0,x
    return (int((r+m)*255),int((g+m)*255),int((b+m)*255))

class Palette:
    def __init__(self):
        self.t=0; self.spd=0.5; self.pi=0; self.pc=(255,255,255)
    def update(self,dt):
        self.t+=dt*self.spd
        if self.pi>0:
            self.pi-=dt*3
            if self.pi<0: self.pi=0
    def pulse(self,c=(255,255,255),i=1.0): self.pc=c; self.pi=i
    def bg(self):
        b=hsv(self.t*15%360,.6,.04)
        if self.pi>0:
            p=self.pi*.15
            return (min(255,int(b[0]+self.pc[0]*p)),min(255,int(b[1]+self.pc[1]*p)),min(255,int(b[2]+self.pc[2]*p)))
        return b
    def ship_c(self): return hsv(self.t*60%360,1,1)
    def bullet_c(self): return hsv(self.t*120+90%360,.8,1)
    def ast_c(self,s=0): return hsv(self.t*30+s*47%360,.7,.9)
    def txt_c(self): return hsv(self.t*45%360,.9,1)
    def part_c(self,s=0): return hsv(self.t*90+s*31%360,1,1)
    def trail_c(self,i=0): return hsv(self.t*80+i*25%360,.9,.8)
    def pu_c(self,pt):
        m={"shield":180,"rapid":60,"spread":300,"speed":120,"life":0,
           "laser_pierce":270,"laser_homing":120,"laser_explosive":30,
           "laser_chain":180,"laser_freeze":200,"magnet":330,"ghost":280,"multi":60}
        return hsv(self.t*50+m.get(pt,0)%360,1,1)
    def laser_c(self,lt):
        m={"pierce":270,"homing":120,"explosive":30,"chain":180,"freeze":200}
        return hsv((self.t*80+m.get(lt,0))%360,1,1)
    def glow(self,r,c,i=0.5):
        s=r*2
        if s<=0: return pygame.Surface((1,1),pygame.SRCALPHA)
        sf=pygame.Surface((s,s),pygame.SRCALPHA)
        for ri in range(r,0,-2):
            a=max(0,min(255,int(i*255*(1-ri/r)**2)))
            pygame.draw.circle(sf,(*c[:3],a),(r,r),ri)
        return sf

# ──────────────────────────────────────
#  VECTOR HELPERS
# ──────────────────────────────────────
def vadd(a,b): return(a[0]+b[0],a[1]+b[1])
def vsub(a,b): return(a[0]-b[0],a[1]-b[1])
def vscl(v,s): return(v[0]*s,v[1]*s)
def vlen(v): return math.sqrt(v[0]**2+v[1]**2)
def vnorm(v):
    l=vlen(v)
    return(v[0]/l,v[1]/l) if l>0 else(0,0)
def wrap(p):
    x,y=p; m=30
    if x<-m: x=WIDTH+m
    elif x>WIDTH+m: x=-m
    if y<-m: y=HEIGHT+m
    elif y>HEIGHT+m: y=-m
    return(x,y)

def load_hs():
    try:
        with open(HS_FILE,'r') as f: return json.load(f).get("hs",0)
    except: return 0
def save_hs(s):
    try:
        with open(HS_FILE,'w') as f: json.dump({"hs":s},f)
    except: pass

# ──────────────────────────────────────
#  EFFECTS
# ──────────────────────────────────────
class Shockwave:
    def __init__(self,pos,mr=80,dur=0.4):
        self.pos=list(pos);self.mr=mr;self.dur=dur;self.time=0;self.alive=True
    def update(self,dt):
        self.time+=dt
        if self.time>=self.dur: self.alive=False
    def draw(self,sf,pal):
        p=self.time/self.dur; r=int(self.mr*p); a=int(255*(1-p)**1.5)
        if r<2 or a<5: return
        c=hsv((pal.t*60+p*180)%360,1,1)
        rs=pygame.Surface((r*2+4,r*2+4),pygame.SRCALPHA)
        pygame.draw.circle(rs,(*c,a),(r+2,r+2),r,max(1,int(3*(1-p))))
        sf.blit(rs,(int(self.pos[0])-r-2,int(self.pos[1])-r-2))

class Popup:
    def __init__(self,pos,text):
        self.pos=list(pos);self.text=text;self.lt=1.2;self.time=0;self.alive=True
    def update(self,dt):
        self.time+=dt;self.pos[1]-=40*dt
        if self.time>=self.lt: self.alive=False
    def draw(self,sf,pal,font):
        p=self.time/self.lt; a=int(255*(1-p)**1.5)
        if a<5: return
        c=hsv((pal.t*80)%360,.8,1); ts=font.render(self.text,True,c); ts.set_alpha(a)
        sc=1+.3*(1-min(1,self.time*5)); w=max(1,int(ts.get_width()*sc)); h=max(1,int(ts.get_height()*sc))
        sf.blit(pygame.transform.scale(ts,(w,h)),(int(self.pos[0])-w//2,int(self.pos[1])-h//2))

class StreakAnnounce:
    def __init__(self,text):
        self.text=text;self.lt=1.5;self.time=0;self.alive=True
    def update(self,dt):
        self.time+=dt
        if self.time>=self.lt: self.alive=False
    def draw(self,sf,pal,font):
        p=self.time/self.lt
        if p<.1: sc,al=p/.1,int(255*sc)
        elif p>.7: sc,al=1.0,int(255*(1-(p-.7)/.3))
        else: sc,al=1.0,255
        c=hsv((pal.t*120)%360,1,1); ts=font.render(self.text,True,c); ts.set_alpha(max(0,al))
        w=max(1,int(ts.get_width()*sc)); h=max(1,int(ts.get_height()*sc))
        scaled=pygame.transform.scale(ts,(w,h))
        gs=pygame.Surface((w+40,h+20),pygame.SRCALPHA); gs.fill((*c,max(0,al//4)))
        sf.blit(gs,(CX-w//2-20,CY-40-h//2-10),special_flags=pygame.BLEND_ADD)
        sf.blit(scaled,(CX-w//2,CY-40-h//2))

class Debris:
    def __init__(self,pos,vel):
        self.pos=list(pos);self.vel=list(vel);self.lt=random.uniform(1.5,4)
        self.time=0;self.alive=True;self.sz=random.uniform(1,3)
        self.seed=random.randint(0,999)
    def update(self,dt):
        self.pos[0]+=self.vel[0]*dt;self.pos[1]+=self.vel[1]*dt
        self.vel[0]*=(1-.3*dt);self.vel[1]*=(1-.3*dt);self.time+=dt
        if self.time>=self.lt: self.alive=False
        self.pos=list(wrap(self.pos))
    def draw(self,sf,pal):
        a=max(0,1-self.time/self.lt); c=pal.ast_c(self.seed); s=max(1,int(self.sz*a))
        ds=pygame.Surface((s*2,s*2),pygame.SRCALPHA)
        pygame.draw.circle(ds,(*c,int(200*a)),(s,s),s)
        sf.blit(ds,(int(self.pos[0])-s,int(self.pos[1])-s))

# ──────────────────────────────────────
#  POWER-UP SYSTEM
# ──────────────────────────────────────
PU_TYPES=["shield","rapid","spread","speed","life",
           "laser_pierce","laser_homing","laser_explosive","laser_chain","laser_freeze",
           "magnet","ghost","multi"]
PU_SYMS={"shield":"S","rapid":"R","spread":"W","speed":"F","life":"+",
          "laser_pierce":"P","laser_homing":"H","laser_explosive":"E","laser_chain":"C","laser_freeze":"Z",
          "magnet":"M","ghost":"G","multi":"*"}
PU_DUR={"shield":6,"rapid":5,"spread":5,"speed":6,"life":0,
          "laser_pierce":6,"laser_homing":6,"laser_explosive":5,"laser_chain":6,"laser_freeze":6,
          "magnet":10,"ghost":7,"multi":5}
LASER_NAMES={"laser_pierce":"PIERCE","laser_homing":"HOMING","laser_explosive":"EXPLOSIVE",
              "laser_chain":"CHAIN","laser_freeze":"FREEZE"}

class PowerUp:
    def __init__(self,pos,pt=None):
        self.pos=list(pos)
        self.pt=pt or random.choice(PU_TYPES)
        self.lt=10.0;self.time=0;self.alive=True;self.bob=random.uniform(0,math.pi*2)
    def update(self,dt):
        self.time+=dt;self.lt-=dt
        if self.lt<=0: self.alive=False
    def draw(self,sf,pal):
        b=math.sin(self.time*3+self.bob)*4; y=self.pos[1]+b; c=pal.pu_c(self.pt)
        g=pal.glow(25,c,.3+.1*math.sin(self.time*5))
        sf.blit(g,(int(self.pos[0])-25,int(y)-25),special_flags=pygame.BLEND_ADD)
        rd=math.radians(self.time*90); sz=12
        pts=[(self.pos[0]+math.cos(rd+math.pi/2*i)*sz,y+math.sin(rd+math.pi/2*i)*sz) for i in range(4)]
        pygame.draw.polygon(sf,c,pts,2)
        f=pygame.font.Font(None,20); sym=f.render(PU_SYMS[self.pt],True,c)
        sf.blit(sym,(int(self.pos[0])-sym.get_width()//2,int(y)-sym.get_height()//2))
        if self.lt<3 and int(self.time*6)%2:
            pygame.draw.circle(sf,c,(int(self.pos[0]),int(y)),15,1)
        # Laser type label
        if self.pt.startswith("laser_"):
            ln=pygame.font.Font(None,16).render(LASER_NAMES[self.pt],True,c)
            sf.blit(ln,(int(self.pos[0])-ln.get_width()//2,int(y)+14))

# ──────────────────────────────────────
#  ENEMIES
# ──────────────────────────────────────
class UFO:
    def __init__(self,ut="small",lv=1):
        self.ut=ut;self.alive=True;self.time=0;self.flash=0
        if ut=="small":
            self.r=12;self.hp=1;self.pts=1000;self.spd=random.uniform(120,180)+lv*3
            self.si=random.uniform(1,2);self.acc=.4
        else:
            self.r=22;self.hp=3;self.pts=200;self.spd=random.uniform(50,90)+lv*2
            self.si=random.uniform(1.5,3);self.acc=.8
        self.st=self.si;side=random.randint(0,1)
        if side==0: self.pos=[-self.r-5,random.uniform(50,HEIGHT-50)];self.vel=[self.spd,random.uniform(-20,20)]
        else: self.pos=[WIDTH+self.r+5,random.uniform(50,HEIGHT-50)];self.vel=[-self.spd,random.uniform(-20,20)]
        self.ty=random.uniform(100,HEIGHT-100);self.wb=random.uniform(0,math.pi*2)
    def update(self,dt,sp):
        self.time+=dt
        if self.flash>0: self.flash-=dt
        dy=self.ty-self.pos[1];self.vel[1]+=dy*.5*dt;self.vel[1]*=(1-dt)
        self.pos[0]+=self.vel[0]*dt;self.pos[1]+=self.vel[1]*dt
        if self.pos[0]<-100 or self.pos[0]>WIDTH+100: self.alive=False
        self.pos[1]=max(10,min(HEIGHT-10,self.pos[1]))
    def try_shoot(self,dt,sp):
        self.st-=dt
        if self.st<=0:
            self.st=self.si
            dx,dy=sp[0]-self.pos[0],sp[1]-self.pos[1]; a=math.atan2(dy,dx)
            a+=random.uniform(-1,1)*(1-self.acc)*math.pi*.4; bs=250
            return(math.cos(a)*bs,math.sin(a)*bs)
        return None
    def draw(self,sf,pal):
        c=(255,100,100) if self.ut=="large" else (100,255,100)
        if self.flash>0: c=(255,255,255)
        x,y=int(self.pos[0]),int(self.pos[1]); r=self.r; wb=int(math.sin(self.time*8+self.wb)*2)
        g=pal.glow(r*2,c,.2); sf.blit(g,(x-r*2,y-r*2),special_flags=pygame.BLEND_ADD)
        pygame.draw.ellipse(sf,c,(x-r//2,y-r+wb,r,r))
        pygame.draw.ellipse(sf,c,(x-r,y-r//3+wb,r*2,r))
        for i in range(3 if self.ut=="large" else 2):
            lx=x-(r*2//3)+i*(r*2//(2 if self.ut=="small" else 3))
            lc=hsv((pal.t*120+i*120)%360,1,1)
            pygame.draw.circle(sf,lc,(lx,y+r//3+wb),2)

class UFOBullet:
    def __init__(self,pos,vel):
        self.pos=list(pos);self.vel=list(vel);self.lt=3;self.alive=True
    def update(self,dt):
        self.pos[0]+=self.vel[0]*dt;self.pos[1]+=self.vel[1]*dt;self.lt-=dt
        if self.lt<=0 or not(-60<self.pos[0]<WIDTH+60 and -60<self.pos[1]<HEIGHT+60):
            self.alive=False
    def draw(self,sf,pal):
        c=hsv((pal.t*200)%360,1,1)
        pygame.draw.circle(sf,c,(int(self.pos[0]),int(self.pos[1])),3)

class BlackHole:
    def __init__(self):
        self.pos=[random.uniform(100,WIDTH-100),random.uniform(100,HEIGHT-100)]
        self.r=30;self.pr=180;self.lt=12;self.time=0;self.alive=True;self.str=8000
    def update(self,dt):
        self.time+=dt;self.lt-=dt
        if self.lt<=0: self.alive=False
    def pull(self,p):
        dx,dy=self.pos[0]-p[0],self.pos[1]-p[1]; d=max(20,math.sqrt(dx*dx+dy*dy))
        if d>self.pr: return(0,0)
        f=self.str/(d*d); return(dx/d*f,dy/d*f)
    def draw(self,sf,pal):
        for i in range(3):
            rr=self.r+15+i*20+5*math.sin(self.time*3+i); h=(pal.t*40+i*40+self.time*60)%360
            c=hsv(h,.8,.7); a=int(100*(1-i/3))
            rs=pygame.Surface((int(rr*2+4),int(rr*2+4)),pygame.SRCALPHA)
            pygame.draw.circle(rs,(*c,a),(int(rr+2),int(rr+2)),int(rr),1)
            sf.blit(rs,(int(self.pos[0]-rr-2),int(self.pos[1]-rr-2)))
        pygame.draw.circle(sf,(0,0,0),(int(self.pos[0]),int(self.pos[1])),self.r)
        ec=hsv((self.t*80)%360,1,1)
        pygame.draw.circle(sf,ec,(int(self.pos[0]),int(self.pos[1])),self.r,2)
        for i in range(6):
            a=self.time*2+i*math.pi/3; rr=self.r+8+3*math.sin(self.time*4+i)
            pygame.draw.circle(sf,ec,(int(self.pos[0]+math.cos(a)*rr),int(self.pos[1]+math.sin(a)*rr)),1)
        if self.lt<4 and int(self.time*4)%2:
            lb=pygame.font.Font(None,20).render("BLACK HOLE",True,ec)
            sf.blit(lb,(int(self.pos[0])-lb.get_width()//2,int(self.pos[1])-self.r-20))

class BossAsteroid:
    def __init__(self,lv):
        self.r=55+min(lv*3,30);self.mhp=15+lv*5;self.hp=self.mhp
        self.pos=[float(CX),-self.r-10];self.vel=[random.uniform(-20,20),random.uniform(15,30)]
        self.ra=0;self.rs=random.uniform(-30,30);self.seed=random.randint(0,999)
        self.alive=True;self.flash=0;self.st=1.5;self.si=max(.6,2-lv*.1)
        self.entered=False;self.phase=0
        n=random.randint(12,18)
        self.verts=[(2*math.pi*i/n,self.r*random.uniform(.75,1.2)) for i in range(n)]
        self.slow_timer=0  # for freeze laser
    def update(self,dt):
        self.pos[0]+=self.vel[0]*dt;self.pos[1]+=self.vel[1]*dt
        if not self.entered:
            if self.pos[1]>HEIGHT*.25:
                self.entered=True;self.vel=[random.uniform(-40,40),random.uniform(-20,20)]
        else:
            if self.pos[1]>HEIGHT*.55: self.vel[1]=-abs(self.vel[1])
            if self.pos[1]<60: self.vel[1]=abs(self.vel[1])
            if self.pos[0]<30: self.vel[0]=abs(self.vel[0])
            elif self.pos[0]>WIDTH-30: self.vel[0]=-abs(self.vel[0])
        if self.slow_timer>0: self.slow_timer-=dt
        sm=0.3 if self.slow_timer>0 else 1.0
        self.ra+=self.rs*dt; if self.flash>0: self.flash-=dt; self.st-=dt
        if self.hp<=self.mhp*.3 and self.phase<2: self.phase=2; self.si*=.5
        elif self.entered and self.phase<1: self.phase=1
        # Apply slow to velocity
        self.vel[0]*=(1-(1-sm)*dt*0.5)  # don't fully stop, just dampen
        self.vel[1]*=(1-(1-sm)*dt*0.5)
    def try_shoot(self,dt,sp):
        if not self.entered: return []
        self.st-=dt
        if self.st<=0:
            self.st=self.si
            dx,dy=sp[0]-self.pos[0],sp[1]-self.pos[1]; a=math.atan2(dy,dx); spd=200
            if self.phase==2:
                return[([*self.pos],(math.cos(a+math.radians(o))*spd,math.sin(a+math.radians(o))*spd)) for o in[-20,-10,0,10,20]]
            return[([*self.pos],(math.cos(a)*spd,math.sin(a)*spd))]
        return []
    def get_pts(self):
        rot=math.radians(self.ra)
        return[(self.pos[0]+math.cos(a+rot)*r,self.pos[1]+math.sin(a+rot)*r) for a,r in self.verts]
    def draw(self,sf,pal):
        c=pal.ast_c(self.seed)
        if self.flash>0: c=(255,255,255)
        if self.phase==2: c=hsv((pal.t*10)%60,1,1)
        elif self.slow_timer>0: c=hsv(200,.6,.8)  # blue tint when frozen
        pts=self.get_pts()
        g=pal.glow(int(self.r*2),c,.08)
        sf.blit(g,(int(self.pos[0])-int(self.r*2),int(self.pos[1])-int(self.r*2)),special_flags=pygame.BLEND_ADD)
        ig=pal.glow(int(self.r),c,.1+.05*math.sin(pal.t*4))
        sf.blit(ig,(int(self.pos[0])-int(self.r),int(self.pos[1])-int(self.r)),special_flags=pygame.BLEND_ADD)
        pygame.draw.polygon(sf,c,pts,3)
        bw=self.r*2; bx=self.pos[0]-bw/2; by=self.pos[1]-self.r-15; hr=self.hp/self.mhp
        pygame.draw.rect(sf,(60,60,60),(bx,by,bw,6))
        pygame.draw.rect(sf,hsv(120*hr,1,1),(bx,by,bw*hr,6))
        pygame.draw.rect(sf,(200,200,200),(bx,by,bw,6),1)
        f=pygame.font.Font(None,20)
        lt="BOSS" if self.phase<2 else ("FROZEN!" if self.slow_timer>0 else "ENRAGED!")
        l=f.render(lt,True,c); sf.blit(l,(int(self.pos[0])-l.get_width()//2,int(by)-18))

# ──────────────────────────────────────
#  ASTEROID
# ──────────────────────────────────────
AST_TYPES=["normal","normal","normal","ice","fire","gold"]

class Asteroid:
    SIZES={3:40,2:25,1:15}
    def __init__(self,x=None,y=None,sz=3,vel=None,at=None,lv=1):
        self.size=sz;self.radius=self.SIZES[sz];self.seed=random.randint(0,999)
        self.at=at or (random.choice(AST_TYPES) if sz==3 and random.random()<.15+lv*.02 else "normal")
        if x is None:
            s=random.randint(0,3)
            if s==0: self.pos=[random.randint(0,WIDTH),-self.radius]
            elif s==1: self.pos=[WIDTH+self.radius,random.randint(0,HEIGHT)]
            elif s==2: self.pos=[random.randint(0,WIDTH),HEIGHT+self.radius]
            else: self.pos=[-self.radius,random.randint(0,HEIGHT)]
        else: self.pos=[float(x),float(y)]
        if vel is None:
            sp=random.uniform(30,80)+lv*2; a=random.uniform(0,2*math.pi)
            self.vel=[math.cos(a)*sp,math.sin(a)*sp]
        else: self.vel=list(vel)
        self.ra=random.uniform(0,360);self.rs=random.uniform(-60,60)
        self.verts=[(2*math.pi*i/n,self.radius*random.uniform(.7,1.3)) for i,n in enumerate([random.randint(8,14)])][0]
        self.slow_timer=0
    def update(self,dt,bhs=None):
        if bhs:
            for bh in bhs:
                p=bh.pull(self.pos); self.vel[0]+=p[0]*dt; self.vel[1]+=p[1]*dt
                if vlen(vsub(self.pos,bh.pos))<bh.r: return"absorbed"
        if self.slow_timer>0: self.slow_timer-=dt
        sm=.3 if self.slow_timer>0 else 1.0
        self.pos[0]+=self.vel[0]*dt*sm; self.pos[1]+=self.vel[1]*dt*sm
        self.pos=list(wrap(self.pos)); self.ra+=self.rs*dt*sm
        return None
    def get_pts(self):
        rot=math.radians(self.ra)
        return[(self.pos[0]+math.cos(a+rot)*r,self.pos[1]+math.sin(a+rot)*r) for a,r in self.verts]
    def draw(self,sf,pal):
        if self.at=="ice": c=hsv((pal.t*20+200)%360,.5,1)
        elif self.at=="fire": c=hsv((pal.t*40+10)%60,1,1)
        elif self.at=="gold": c=hsv((pal.t*10+45)%60,.8,1)
        else: c=pal.ast_c(self.seed)
        if self.slow_timer>0: c=hsv(200,.6,.9)  # blue tint when frozen
        pts=self.get_pts()
        g=pal.glow(int(self.radius*1.5),c,.1)
        sf.blit(g,(int(self.pos[0])-int(self.radius*1.5),int(self.pos[1])-int(self.radius*1.5)),special_flags=pygame.BLEND_ADD)
        th=3 if self.at!="normal" else 2
        pygame.draw.polygon(sf,c,pts,th)
        if self.at=="ice":
            for i in range(3):
                a=math.radians(self.ra*.5+i*120)
                pygame.draw.circle(sf,(200,230,255),(int(self.pos[0]+math.cos(a)*self.radius*.4),int(self.pos[1]+math.sin(a)*self.radius*.4)),2)
        elif self.at=="fire" and random.random()<.3:
            fs=pygame.Surface((6,6),pygame.SRCALPHA)
            pygame.draw.circle(fs,(*c,150),(3,3),3)
            sf.blit(fs,(int(self.pos[0]+random.uniform(-self.radius*.5,self.radius*.5))-3,int(self.pos[1]+random.uniform(-self.radius*.5,self.radius*.5))-3))
        elif self.at=="gold" and int(pal.t*6)%3==0:
            pygame.draw.polygon(sf,(255,255,200),pts,1)

# ──────────────────────────────────────
#  BULLET (multi-type laser system)
# ──────────────────────────────────────
class Bullet:
    def __init__(self,pos,vel,spread=False,laser_type=None,ufo=False,multi=False):
        self.pos=list(pos);self.vel=list(vel);self.alive=True;self.trail=[]
        self.spread=spread;self.ufo=ufo;self.multi=multi
        self.lt=.8 if spread else (2.0 if laser_type else (1.5 if multi else 1.2))
        # Laser properties
        self.laser_type=laser_type  # None, "pierce", "homing", "explosive", "chain", "freeze"
        self.pierce=5 if laser_type=="pierce" else (1 if laser_type in ("explosive","chain","freeze") else 0)
        self.homing_target=None  # set by game
        self.chain_hits=0
        self.max_chain=3
        self.aoe_radius=80 if laser_type=="explosive" else 0
        self.freeze_dur=3.0

    def update(self,dt):
        # Homing behavior
        if self.laser_type=="homing" and self.homing_target:
            tp=self.homing_target
            if hasattr(tp,'pos') and (hasattr(tp,'alive') and not tp.alive or not hasattr(tp,'alive')):
                pass  # target dead, go straight
            elif hasattr(tp,'pos'):
                dx,dy=tp.pos[0]-self.pos[0],tp.pos[1]-self.pos[1]
                d=math.sqrt(dx*dx+dy*dy)
                if d>0:
                    cur_a=math.atan2(self.vel[1],self.vel[0])
                    tgt_a=math.atan2(dy,dx)
                    diff=tgt_a-cur_a
                    # Normalize angle difference
                    while diff>math.pi: diff-=2*math.pi
                    while diff<-math.pi: diff+=2*math.pi
                    turn=max(-4, min(4, diff*8))*dt*60  # steering
                    spd=vlen(self.vel)
                    new_a=cur_a+turn
                    self.vel=[math.cos(new_a)*spd,math.sin(new_a)*spd]

        self.pos[0]+=self.vel[0]*dt; self.pos[1]+=self.vel[1]*dt
        self.lt-=dt
        if self.lt<=0: self.alive=False
        if not(-60<self.pos[0]<WIDTH+60 and -60<self.pos[1]<HEIGHT+60):
            self.alive=False
        self.trail.append(tuple(self.pos))
        if len(self.trail)>8: self.trail.pop(0)

    def draw(self,sf,pal):
        if self.ufo:
            c=hsv((pal.t*200)%360,1,1)
            pygame.draw.circle(sf,c,(int(self.pos[0]),int(self.pos[1])),3)
            return
        if self.multi:
            c=hsv((pal.t*100+60)%360,.8,1)
            for i,tp in enumerate(self.trail):
                a=int(200*(i/len(self.trail))*.4)
                ts=pygame.Surface((4,4),pygame.SRCALPHA); pygame.draw.circle(ts,(*c,a),(2,2),2)
                sf.blit(ts,(int(tp[0])-2,int(tp[1])-2))
            pygame.draw.circle(sf,(255,255,255),(int(self.pos[0]),int(self.pos[1])),2)
            return
        if self.laser_type:
            lt=self.laser_type; c=pal.laser_c(lt)
            # Distinct visual per laser type
            if lt=="homing":
                # Green with curved trail
                for i,tp in enumerate(self.trail):
                    a=int(200*(i/len(self.trail))*.7)
                    ts=pygame.Surface((8,8),pygame.SRCALPHA); pygame.draw.circle(ts,(*c,a),(4,4),4)
                    sf.blit(ts,(int(tp[0])-4,int(tp[1])-4))
                g=pal.glow(14,c,.6); sf.blit(g,(int(self.pos[0])-14,int(self.pos[1])-14),special_flags=pygame.BLEND_ADD)
                pygame.draw.circle(sf,c,(int(self.pos[0]),int(self.pos[1])),4)
                # Arrow tip
                a=math.atan2(self.vel[1],self.vel[0])
                for da in [2.8,-2.8]:
                    hx=int(self.pos[0]+math.cos(a+da)*6); hy=int(self.pos[1]+math.sin(a+da)*6)
                    pygame.draw.circle(sf,(255,255,255),(hx,hy),1)
            elif lt=="explosive":
                # Red-orange, larger glow
                for i,tp in enumerate(self.trail):
                    a=int(180*(i/len(self.trail))*.6)
                    ts=pygame.Surface((8,8),pygame.SRCALPHA); pygame.draw.circle(ts,(*c,a),(4,4),4)
                    sf.blit(ts,(int(tp[0])-4,int(tp[1])-4))
                g=pal.glow(20,c,.6); sf.blit(g,(int(self.pos[0])-20,int(self.pos[1])-20),special_flags=pygame.BLEND_ADD)
                pygame.draw.circle(sf,(255,200,100),(int(self.pos[0]),int(self.pos[1])),4)
            elif lt=="chain":
                # Cyan with electric effect
                for i,tp in enumerate(self.trail):
                    a=int(255*(i/len(self.trail))*.5)
                    ts=pygame.Surface((8,8),pygame.SRCALPHA); pygame.draw.circle(ts,(*c,a),(4,4),4)
                    sf.blit(ts,(int(tp[0])-4,int(tp[1])-4))
                g=pal.glow(18,c,.5); sf.blit(g,(int(self.pos[0])-18,int(self.pos[1])-18),special_flags=pygame.BLEND_ADD)
                pygame.draw.circle(sf,c,(int(self.pos[0]),int(self.pos[1])),3)
                # Electric sparks
                for _ in range(2):
                    ox=random.uniform(-6,6); oy=random.uniform(-6,6)
                    sf.set_at((max(0,min(WIDTH-1,int(self.pos[0]+ox))),max(0,min(HEIGHT-1,int(self.pos[1]+oy)))),c)
            elif lt=="freeze":
                # Light blue, icy look
                for i,tp in enumerate(self.trail):
                    a=int(200*(i/len(self.trail))*.6)
                    ts=pygame.Surface((6,6),pygame.SRCALPHA); pygame.draw.circle(ts,(200,230,255,a),(3,3),3)
                    sf.blit(ts,(int(tp[0])-3,int(tp[1])-3))
                g=pal.glow(14,(200,230,255),.5); sf.blit(g,(int(self.pos[0])-14,int(self.pos[1])-14),special_flags=pygame.BLEND_ADD)
                pygame.draw.circle(sf,(220,240,255),(int(self.pos[0]),int(self.pos[1])),3)
            else:  # pierce
                h=(pal.t*150+270)%360; c=hsv(h,.6,1)
                for i,tp in enumerate(self.trail):
                    a=int(200*(i/len(self.trail))*.7)
                    ts=pygame.Surface((6,6),pygame.SRCALPHA); pygame.draw.circle(ts,(*c,a),(3,3),3)
                    sf.blit(ts,(int(tp[0])-3,int(tp[1])-3))
                g=pal.glow(16,c,.5); sf.blit(g,(int(self.pos[0])-16,int(self.pos[1])-16),special_flags=pygame.BLEND_ADD)
                pygame.draw.circle(sf,(255,255,255),(int(self.pos[0]),int(self.pos[1])),3)
            return
        # Normal bullet
        c=pal.bullet_c()
        for i,tp in enumerate(self.trail):
            a=int(200*(i/len(self.trail))*.5)
            ts=pygame.Surface((4,4),pygame.SRCALPHA); pygame.draw.circle(ts,(*c,a),(2,2),2)
            sf.blit(ts,(int(tp[0])-2,int(tp[1])-2))
        g=pal.glow(12,c,.4); sf.blit(g,(int(self.pos[0])-12,int(self.pos[1])-12),special_flags=pygame.BLEND_ADD)
        pygame.draw.circle(sf,(255,255,255),(int(self.pos[0]),int(self.pos[1])),2 if not self.spread else 3)

class Particle:
    def __init__(self,pos,vel,c,lt=.8,sz=3):
        self.pos=list(pos);self.vel=list(vel);self.c=c;self.lt=lt;self.mlt=lt;self.sz=sz;self.alive=True
    def update(self,dt):
        self.pos[0]+=self.vel[0]*dt;self.pos[1]+=self.vel[1]*dt
        self.vel[0]*=(1-2*dt);self.vel[1]*=(1-2*dt);self.lt-=dt
        if self.lt<=0: self.alive=False
    def draw(self,sf,pal):
        a=max(0,self.lt/self.mlt); c=pal.part_c(hash(str(self.c))%100)
        s=max(1,int(self.sz*a))
        ps=pygame.Surface((s*2,s*2),pygame.SRCALPHA)
        pygame.draw.circle(ps,(*c,int(255*a)),(s,s),s)
        sf.blit(ps,(int(self.pos[0])-s,int(self.pos[1])-s))

class ShootingStar:
    def __init__(self):
        self.pos=[random.uniform(0,WIDTH),random.uniform(0,HEIGHT*.3)]
        a=random.uniform(math.pi*.15,math.pi*.45); sp=random.uniform(400,900)
        self.vel=[math.cos(a)*sp,math.sin(a)*sp];self.lt=random.uniform(.3,.8);self.time=0;self.alive=True;self.hue=random.uniform(0,360)
    def update(self,dt):
        self.pos[0]+=self.vel[0]*dt;self.pos[1]+=self.vel[1]*dt;self.time+=dt
        if self.time>=self.lt or self.pos[0]>WIDTH or self.pos[1]>HEIGHT: self.alive=False
    def draw(self,sf,pal):
        p=self.time/self.lt; a=int(255*(1-p)); c=hsv((pal.t*20+self.hue)%360,.6,1)
        n=vnorm(self.vel)
        ls=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
        pygame.draw.line(ls,(*c,a),(int(self.pos[0]),int(self.pos[1])),(int(self.pos[0]-n[0]*30),int(self.pos[1]-n[1]*30)),2)
        sf.blit(ls,(0,0)); pygame.draw.circle(sf,(255,255,255),(int(self.pos[0]),int(self.pos[1])),2)

class NebulaCloud:
    def __init__(self):
        self.x=random.uniform(0,WIDTH);self.y=random.uniform(0,HEIGHT)
        self.r=random.uniform(60,150);self.ho=random.uniform(0,360);self.a=random.uniform(3,10)
        self.d=[random.uniform(-3,3),random.uniform(-3,3)]
    def update(self,dt):
        self.x+=self.d[0]*dt;self.y+=self.d[1]*dt
        if self.x<-self.r: self.x=WIDTH+self.r
        if self.x>WIDTH+self.r: self.x=-self.r
        if self.y<-self.r: self.y=HEIGHT+self.r
        if self.y>HEIGHT+self.r: self.y=-self.r
    def draw(self,sf,pal):
        h=(pal.t*5+self.ho)%360; c=hsv(h,.8,.6)
        ns=pygame.Surface((int(self.r*2),int(self.r*2)),pygame.SRCALPHA)
        for r in range(int(self.r),0,-4):
            a=max(0,min(255,int(self.a*(1-(r/self.r)**.5))))
            pygame.draw.circle(ns,(*c,a),(int(self.r),int(self.r)),r)
        sf.blit(ns,(int(self.x-self.r),int(self.y-self.r)))

class StarField:
    def __init__(self,n=250):
        self.s=[{'x':random.randint(0,WIDTH),'y':random.randint(0,HEIGHT),'b':random.uniform(.2,1),'ho':random.uniform(0,360),'ts':random.uniform(1,4)} for _ in range(n)]
    def draw(self,sf,pal):
        for s in self.s:
            tw=.5+.5*math.sin(pal.t*s['ts']); b=s['b']*tw
            c=hsv((pal.t*10+s['ho'])%360,.5,b); x,y=int(s['x']),int(s['y'])
            if 0<=x<WIDTH and 0<=y<HEIGHT:
                sf.set_at((x,y),c)
                if b>.7: pygame.draw.circle(sf,c,(x,y),2)

def create_crt():
    sf=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
    for y in range(0,HEIGHT,3): pygame.draw.line(sf,(0,0,0,25),(0,y),(WIDTH,y))
    for i in range(40):
        a=int(80*(1-i/40)**2)
        pygame.draw.rect(sf,(0,0,0,a),(i,i,WIDTH-2*i,HEIGHT-2*i),1)
    return sf

# ──────────────────────────────────────
#  SHIP
# ──────────────────────────────────────
class Ship:
    def __init__(self): self.reset()
    def reset(self):
        self.pos=[float(CX),float(CY)];self.vel=[.0,.0];self.angle=-90
        self.thrusting=False;self.thrust_t=0;self.invuln=3.0;self.alive=True;self.death_t=0
        self.trail=[]
        self.shield=0;self.rapid=0;self.spread=0;self.speed=0
        self.laser=0;self.laser_type=None
        self.magnet=0;self.ghost=0;self.multi_shot=0
        self.dash_cd=0;self.dash_t=0;self.dash_max=.15;self.dash_cd_max=1.5;self.dashing=False;self.dash_dir=(0,0)
    @property
    def has_shield(self): return self.shield>0
    def update(self,dt,keys):
        if not self.alive: self.death_t-=dt; return
        for a in ['shield','rapid','spread','speed','laser','magnet','ghost','multi_shot']:
            v=getattr(self,a)
            if v>0: setattr(self,a,v-dt)
        if self.dash_cd>0: self.dash_cd-=dt
        if self.dashing:
            self.dash_t-=dt; self.vel[0]=self.dash_dir[0]*800; self.vel[1]=self.dash_dir[1]*800
            if self.dash_t<=0: self.dashing=False; self.vel=[self.vel[0]*.3,self.vel[1]*.3]
        else:
            rs=250
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.angle-=rs*dt
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.angle+=rs*dt
            self.thrusting=keys[pygame.K_UP] or keys[pygame.K_w]
            tm=1.6 if self.speed>0 else 1.0
            if self.thrusting:
                rad=math.radians(self.angle)
                self.vel[0]+=math.cos(rad)*280*tm*dt; self.vel[1]+=math.sin(rad)*280*tm*dt; self.thrust_t=.1
            self.vel[0]*=(1-.5*dt); self.vel[1]*=(1-.5*dt)
        sp=vlen(self.vel); ms=600 if self.dashing else (450*(1.6 if self.speed>0 else 1.0))
        if sp>ms: self.vel[0]=self.vel[0]/sp*ms; self.vel[1]=self.vel[1]/sp*ms
        self.pos[0]+=self.vel[0]*dt; self.pos[1]+=self.vel[1]*dt; self.pos=list(wrap(self.pos))
        if self.thrust_t>0: self.thrust_t-=dt
        if self.invuln>0: self.invuln-=dt
        self.trail.append(tuple(self.pos))
        if len(self.trail)>25: self.trail.pop(0)
    def start_dash(self):
        if self.dash_cd>0 or self.dashing: return False
        rad=math.radians(self.angle); self.dash_dir=(math.cos(rad),math.sin(rad))
        self.dashing=True; self.dash_t=self.dash_max; self.dash_cd=self.dash_cd_max
        self.invuln=max(self.invuln,self.dash_max+.05); return True
    def get_pts(self):
        rad=math.radians(self.angle)
        return[(self.pos[0]+math.cos(rad)*18,self.pos[1]+math.sin(rad)*18),
               (self.pos[0]+math.cos(rad+2.5)*14,self.pos[1]+math.sin(rad+2.5)*14),
               (self.pos[0]+math.cos(rad-2.5)*14,self.pos[1]+math.sin(rad-2.5)*14)]
    def get_flame(self):
        rad=math.radians(self.angle)
        return[(self.pos[0]+math.cos(rad+2.8)*10,self.pos[1]+math.sin(rad+2.8)*10),
               (self.pos[0]+math.cos(rad-2.8)*10,self.pos[1]+math.sin(rad-2.8)*10),
               (self.pos[0]+math.cos(rad+math.pi)*(18+random.random()*12),
                self.pos[1]+math.sin(rad+math.pi)*(18+random.random()*12)),
               (self.pos[0]+math.cos(rad+math.pi)*12,self.pos[1]+math.sin(rad+math.pi)*12)]
    def draw(self,sf,pal):
        if not self.alive: return
        if self.invuln>0 and int(self.invuln*10)%2==0: return
        c=pal.ship_c()
        if self.dashing:
            for i,tp in enumerate(self.trail[-8:]):
                a=int(180*(i/8)); ts=pygame.Surface((20,20),pygame.SRCALPHA)
                pygame.draw.circle(ts,(*c,a),(10,10),8); sf.blit(ts,(int(tp[0])-10,int(tp[1])-10))
        for i,tp in enumerate(self.trail):
            a=int(255*(i/len(self.trail))*.25); tc=pal.trail_c(i)
            ts=pygame.Surface((4,4),pygame.SRCALPHA); pygame.draw.circle(ts,(*tc,a),(2,2),2)
            sf.blit(ts,(int(tp[0])-2,int(tp[1])-2))
        if self.has_shield:
            sa=int(80+40*math.sin(pal.t*6)); sc=hsv((pal.t*90+180)%360,.7,1); sr=28
            ss=pygame.Surface((sr*2,sr*2),pygame.SRCALPHA)
            pygame.draw.circle(ss,(*sc,sa),(sr,sr),sr,2); pygame.draw.circle(ss,(*sc,sa//3),(sr,sr),sr)
            sf.blit(ss,(int(self.pos[0])-sr,int(self.pos[1])-sr))
        # Ghost visual (transparent + blue tint)
        if self.ghost>0:
            gs=pygame.Surface((60,60),pygame.SRCALPHA)
            pygame.draw.polygon(gs,(*hsv((pal.t*60+280)%360,.8,1),100),[(30,5),(10,55),(50,55)],0)
            pygame.draw.polygon(gs,(200,200,255,60),[(30,5),(10,55),(50,55)],1)
            sf.blit(gs,(int(self.pos[0])-30,int(self.pos[1])-30))
        # Laser type indicator
        if self.laser>0 and self.laser_type:
            lc=pal.laser_c(self.laser_type); rad=math.radians(self.angle)
            lx,ly=int(self.pos[0]+math.cos(rad)*22),int(self.pos[1]+math.sin(rad)*22)
            pygame.draw.circle(sf,lc,(lx,ly),5)
            ln=pygame.font.Font(None,16).render(self.laser_type.upper(),True,lc)
            sf.blit(ln,(lx-ln.get_width()//2,ly-16))
        # Magnet rings
        if self.magnet>0:
            mr=int(60+20*math.sin(pal.t*4))
            ms=pygame.Surface((mr*2,mr*2),pygame.SRCALPHA)
            mc=hsv((pal.t*60+330)%360,.7,1)
            pygame.draw.circle(ms,(*mc,int(40+20*math.sin(pal.t*4))),(mr,mr),1)
            sf.blit(ms,(int(self.pos[0])-mr,int(self.pos[1])-mr))
        if self.speed>0 and self.thrusting:
            for _ in range(3):
                tc=pal.trail_c(random.randint(0,20))
                ps=pygame.Surface((6,6),pygame.SRCALPHA); pygame.draw.circle(ps,(*tc,120),(3,3),3)
                sf.blit(ps,(int(self.pos[0]+random.uniform(-8,8))-3,int(self.pos[1]+random.uniform(-8,8))-3))
        g=pal.glow(30,c,.15); sf.blit(g,(int(self.pos[0])-30,int(self.pos[1])-30),special_flags=pygame.BLEND_ADD)
        if self.thrust_t>0:
            fc=hsv((pal.t*200)%360,1,1); pygame.draw.polygon(sf,fc,self.get_flame())
            rad=math.radians(self.angle)
            inn=[(self.pos[0]+math.cos(rad+math.pi)*14,self.pos[1]+math.sin(rad+math.pi)*14),
                 (self.pos[0]+math.cos(rad+2.9)*7,self.pos[1]+math.sin(rad+2.9)*7),
                 (self.pos[0]+math.cos(rad+math.pi)*(12+random.random()*8),self.pos[1]+math.sin(rad+math.pi)*(12+random.random()*8)),
                 (self.pos[0]+math.cos(rad-2.9)*7,self.pos[1]+math.sin(rad-2.9)*7)]
            pygame.draw.polygon(sf,(255,255,255),inn)
        pts=self.get_pts(); pygame.draw.polygon(sf,c,pts,2)
        sfill=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); pygame.draw.polygon(sfill,(*c,30),pts)
        sf.blit(sfill,(0,0))
        inds=[]
        if self.rapid>0: inds.append(hsv(60,1,1))
        if self.spread>0: inds.append(hsv(300,1,1))
        if self.speed>0: inds.append(hsv(120,1,1))
        if self.laser>0: inds.append(pal.laser_c(self.laser_type))
        if self.ghost>0: inds.append(hsv(280,1,1))
        if self.magnet>0: inds.append(hsv(330,1,1))
        if self.multi_shot>0: inds.append(hsv(60,1,1))
        for idx,ic in enumerate(inds):
            pygame.draw.circle(sf,ic,(int(self.pos[0])-10+idx*8,int(self.pos[1])+18),3)

# ──────────────────────────────────────
#  GAME
# ──────────────────────────────────────
class Game:
    def __init__(self):
        self.snd=make_sounds(); self.pal=Palette(); self.stars=StarField(250)
        self.neb=[NebulaCloud() for _ in range(5)]; self.sstars=[]; self.sst=0
        self.crt=create_crt(); self.crt_on=True
        self.fl=pygame.font.Font(None,72); self.fm=pygame.font.Font(None,42)
        self.fs=pygame.font.Font(None,28); self.ft=pygame.font.Font(None,22)
        self.fp=pygame.font.Font(None,30); self.fpu=pygame.font.Font(None,16)
        self.hi=load_hs(); self.state="menu"; self.paused=False; self.mus=True
        self.bgm=None
        try: self.bgm=gen_bgm()
        except: self.bgm=None
        self.bgm_ch=None; self.reset()

    def reset(self):
        self.ship=Ship(); self.asts=[]; self.buls=[]; self.ufobs=[]
        self.parts=[]; self.debr=[]; self.pups=[]; self.shoks=[]
        self.pops=[]; self.streaks=[]; self.ufos=[]; self.bhs=[]; self.boss=None
        self.score=0; self.lives=3; self.bombs=3; self.level=1
        self.scd=0; self.tcd=0; self.shake=0; self.shake_i=0
        self.cc=0; self.ct=0; self.cm=1; self.mxc=0; self.ls=0
        self.wat=0; self.wt=""; self.kills=0; self.shots=0
        self.ut=random.uniform(15,25); self.bht=random.uniform(45,75)
        self.nel=10000; self.di=0; self.ind=[]; self.spawn_ast(4)

    def play_bgm(self):
        if self.bgm and self.mus and self.bgm_ch is None: self.bgm_ch=self.bgm.play(loops=-1)
    def stop_bgm(self):
        if self.bgm_ch: self.bgm_ch.stop(); self.bgm_ch=None

    def spawn_ast(self,n):
        for _ in range(n):
            a=Asteroid(lv=self.level); att=0
            while vlen(vsub(a.pos,self.ship.pos))<150 and att<20: a=Asteroid(lv=self.level); att+=1
            self.asts.append(a)

    def spawn_boss(self):
        self.boss=BossAsteroid(self.level); self.wat=2; self.wt=f"!! BOSS LEVEL {self.level} !!"
        self.snd["wave_announce"].play(); self.pal.pulse((255,0,0),.8)

    def expl(self,pos,n=15,sp=120,sz=3):
        for _ in range(n):
            a=random.uniform(0,2*math.pi); s=random.uniform(sp*.3,sp)
            self.parts.append(Particle(pos,(math.cos(a)*s,math.sin(a)*s),None,random.uniform(.3,1),random.uniform(1,sz)))

    def debris(self,pos,n=5,sp=80):
        for _ in range(n):
            a=random.uniform(0,2*math.pi); s=random.uniform(sp*.3,sp)
            self.debr.append(Debris(pos,(math.cos(a)*s,math.sin(a)*s)))

    def shock(self,pos,r=60): self.shoks.append(Shockwave(pos,r))
    def popup(self,pos,t): self.pops.append(Popup(pos,t))

    def _find_nearest_target(self,pos,exclude_pos=None,max_dist=400):
        """Find nearest enemy for homing laser."""
        best=None; bd=max_dist
        targets=[]
        for a in self.asts:
            d=vlen(vsub(pos,a.pos))
            if d<bd: targets.append((d,a))
        for u in self.ufos:
            if u.alive:
                d=vlen(vsub(pos,u.pos))
                if d<bd: targets.append((d,u))
        if self.boss and self.boss.alive:
            d=vlen(vsub(pos,self.boss.pos))
            if d<bd: targets.append((d,self.boss))
        if exclude_pos:
            targets=[(d,t) for d,t in targets if t is not exclude_pos]
        if targets:
            targets.sort(key=lambda x:x[0])
            return targets[0][1]
        return None

    def _apply_freeze(self,target,dur=3.0):
        if hasattr(target,'slow_timer'): target.slow_timer=dur

    def _chain_lightning(self,pos,exclude,max_jumps=3):
        """Chain lightning: jump to nearby enemies, damage them."""
        jumped=0
        hit_targets=[]
        all_targets=[]
        for a in self.asts:
            if a is not exclude:
                d=vlen(vsub(pos,a.pos))
                if d<120: all_targets.append((d,a))
        for u in self.ufos:
            if u.alive and u is not exclude:
                d=vlen(vsub(pos,u.pos))
                if d<120: all_targets.append((d,u))
        if self.boss and self.boss.alive and self.boss is not exclude:
            d=vlen(vsub(pos,self.boss.pos))
            if d<120: all_targets.append((d,self.boss))
        all_targets.sort(key=lambda x:x[0])
        for d,t in all_targets[:max_jumps]:
            if t not in hit_targets:
                hit_targets.append(t)
                self.expl(t.pos,5,50,2)
                self.shock(t.pos,25)
                self.snd["chain_jump"].play()
                jumped+=1
                pos=t.pos
        # Score chain kills
        for t in hit_targets:
            if isinstance(t,Asteroid):
                self.score+={3:20,2:50,1:100}.get(t.size,20)
                self.asts.remove(t)
                self.kills+=1
            elif isinstance(t,UFO) and t.alive:
                t.alive=False; self.score+=t.pts; self.expl(t.pos,15,100,3)
                self.snd["ufo_die"].play()
            elif t is self.boss:
                self.boss.hp-=2; self.boss.flash=0.08; self.snd["boss_hit"].play()
                if self.boss.hp<=0:
                    self.boss.alive=False; self.score+=500*self.level
                    self.popup(self.boss.pos,f"+{500*self.level} BOSS CHAIN!")
                    self.expl(self.boss.pos,60,250,5); self.shock(self.boss.pos,150)
                    self.snd["boss_die"].play(); self.boss=None

    def _explosive_aoe(self,pos,radius):
        """Damage all enemies in radius."""
        for a in self.asts[:]:
            if vlen(vsub(pos,a.pos))<radius+a.radius:
                self.kills+=1; self.score+={3:20,2:50,1:100}.get(a.size,20)
                self.expl(a.pos,5+a.size*3,40+a.size*20,2)
                if a in self.asts: self.asts.remove(a)
        for u in self.ufos[:]:
            if u.alive and vlen(vsub(pos,u.pos))<radius:
                u.alive=False; self.score+=u.pts; self.expl(u.pos,15,100,3)
                self.snd["ufo_die"].play()
        if self.boss and self.boss.alive and vlen(vsub(pos,self.boss.pos))<radius+self.boss.r:
            self.boss.hp-=3; self.boss.flash=0.1
            if self.boss.hp<=0:
                self.boss.alive=False; self.score+=500*self.level
                self.expl(self.boss.pos,60,250,5); self.shock(self.boss.pos,150)
                self.snd["boss_die"].play(); self.boss=None
        self.shock(pos,radius)
        self.snd["explosive_aoe"].play()

    def shoot(self):
        if self.scd>0: return
        rad=math.radians(self.ship.angle); spd=500
        bv=(math.cos(rad)*spd+self.ship.vel[0]*.3,math.sin(rad)*spd+self.ship.vel[1]*.3)
        nose=(self.ship.pos[0]+math.cos(rad)*20,self.ship.pos[1]+math.sin(rad)*20)
        lt=self.ship.laser_type

        # Multi-shot: 8 bullets in a ring
        if self.multi_shot>0:
            for i in range(8):
                a=rad+math.pi*2*i/8
                mv=(math.cos(a)*spd*.8,math.sin(a)*spd*.8)
                self.buls.append(Bullet(nose,mv,multi=True))
            self.shcd=.12; self.snd["shoot_multi"].play(); self.shots+=8; return

        # Laser bullets
        if self.ship.laser>0 and lt:
            bullet=Bullet(nose,bv,laser_type=lt)
            if lt=="homing":
                bullet.homing_target=self._find_nearest_target(nose)
            self.buls.append(bullet)
            self.shots+=1
            if self.ship.spread>0:
                for off in [-15,15]:
                    sr=rad+math.radians(off)
                    sv=(math.cos(sr)*spd+self.ship.vel[0]*.2,math.sin(sr)*spd+self.ship.vel[1]*.2)
                    sb=Bullet(nose,sv,spread=True,laser_type=lt)
                    if lt=="homing": sb.homing_target=self._find_nearest_target(nose)
                    self.buls.append(sb)
            self.scd=.07 if self.ship.rapid>0 else .15
            self.snd[f"shoot_{lt}"].play(); return

        # Normal shot
        self.buls.append(Bullet(nose,bv))
        self.shots+=1
        if self.ship.spread>0:
            for off in [-15,15]:
                sr=rad+math.radians(off)
                sv=(math.cos(sr)*spd+self.ship.vel[0]*.2,math.sin(sr)*spd+self.ship.vel[1]*.2)
                self.buls.append(Bullet(nose,sv,spread=True))
        self.scd=.07 if self.ship.rapid>0 else .15
        self.snd["shoot_spread" if self.ship.spread>0 else "shoot"].play()

    def handle_collisions(self):
        if not self.ship.alive: return
        # Bullets vs Asteroids
        for b in self.buls:
            if not b.alive: continue
            for a in self.asts[:]:
                d=vlen(vsub(b.pos,a.pos))
                if d<a.radius:
                    # Pierce handling
                    if b.laser_type=="pierce" and b.pierce>0: b.pierce-=1
                    elif b.laser_type in ("explosive","freeze") and b.pierce>0: b.pierce-=1; b.alive=False
                    elif b.laser_type=="chain" and b.chain_hits<b.max_chain: b.chain_hits+=1; b.alive=False
                    else: b.alive=False

                    self.kills+=1; self.cc+=1; self.ct=2.0
                    if self.cc>=3: self.cm=min(8,1+self.cc//3)
                    if self.cc%3==0: self.snd["combo"].play()
                    # Streak check
                    ms={5:"KILLING SPREE!",10:"RAMPAGE!",15:"UNSTOPPABLE!",20:"GODLIKE!",30:"LEGENDARY!",50:"BEYOND GODLIKE!"}
                    for th,tx in sorted(ms.items()):
                        if self.cc==th and self.cc>self.ls:
                            self.streaks.append(StreakAnnounce(tx)); self.snd["streak"].play(); self.ls=self.cc; break

                    base={3:20,2:50,1:100}.get(a.size,20)
                    tm={"normal":1,"ice":1.5,"fire":1.2,"gold":2.0}.get(a.at,1)
                    pts=int(base*self.cm*tm); self.score+=pts
                    pop=f"+{pts}"+(f" x{self.cm}" if self.cm>1 else "")
                    if a.at=="gold": pop+=" GOLD!"
                    elif a.at=="ice": pop+=" ICE!"
                    self.popup(a.pos,pop)

                    # Explosive AoE
                    if b.laser_type=="explosive" and b.pierce<=0:
                        self._explosive_aoe(a.pos,b.aoe_radius)
                        self.asteroids_remove=a; continue
                    # Chain lightning
                    if b.laser_type=="chain" and b.chain_hits>=b.max_chain:
                        self._chain_lightning(a.pos,a)
                        continue
                    # Freeze
                    if b.laser_type=="freeze":
                        self._apply_freeze(a,b.freeze_dur)
                        self.snd["freeze_hit"].play()
                        self.popup(a.pos,"FROZEN!")

                    # Split
                    if a.at=="ice" and a.size>1:
                        for _ in range(3):
                            self.asts.append(Asteroid(a.pos[0],a.pos[1],a.size-1,(random.uniform(-100,100),random.uniform(-100,100)),"ice",self.level))
                    elif a.size>1:
                        for _ in range(2):
                            self.asts.append(Asteroid(a.pos[0],a.pos[1],a.size-1,(random.uniform(-100,100),random.uniform(-100,100)),a.at if a.at!="gold" else "normal",self.level))
                    self.expl(a.pos,8+a.size*5,60+a.size*30,2+a.size)
                    self.debris(a.pos,2+a.size,50+a.size*10); self.shock(a.pos,30+a.size*20)
                    if a.size>=2: self.snd["explode_small"].play(); self.shake=.08; self.shake_i=2+a.size
                    else:
                        sn="ice_hit" if a.at=="ice" else "fire_hit" if a.at=="fire" else "explode_small"
                        self.snd[sn].play()
                    drop=.08+.02*self.level
                    if a.at=="gold": drop=.5
                    if random.random()<drop: self.pups.append(PowerUp(a.pos))
                    if a in self.asts: self.asts.remove(a)
                    if not (b.laser_type in ("pierce","explosive","chain","freeze")): break

            # Bullets vs Boss
            if self.boss and self.boss.alive and b.alive:
                d=vlen(vsub(b.pos,self.boss.pos))
                if d<self.boss.r:
                    if b.laser_type=="pierce" and b.pierce>0: b.pierce-=1
                    elif b.laser_type in ("explosive","freeze") and b.pierce>0: b.pierce-=1; b.alive=False
                    elif b.laser_type=="chain" and b.chain_hits<b.max_chain: b.chain_hits+=1; b.alive=False
                    else: b.alive=False
                    dmg=2 if b.laser_type in ("pierce",) else 1
                    if b.laser_type=="explosive" and b.pierce<=0:
                        self._explosive_aoe(b.pos,b.aoe_radius)
                    if b.laser_type=="freeze": self._apply_freeze(self.boss,b.freeze_dur)
                    self.boss.hp-=dmg; self.boss.flash=.08; self.snd["boss_hit"].play()
                    self.shake=.05; self.shake_i=2; self.expl(b.pos,3,40,1)
                    if self.boss.hp<=0:
                        self.boss.alive=False; self.score+=500*self.level
                        self.popup(self.boss.pos,f"+{500*self.level} BOSS!")
                        self.expl(self.boss.pos,60,250,5); self.shock(self.boss.pos,150)
                        self.shock(self.boss.pos,100); self.snd["boss_die"].play()
                        self.shake=.6; self.shake_i=12; self.pal.pulse((255,200,50),1)
                        pt=random.choice(["shield","rapid","spread","laser_pierce","laser_homing","laser_explosive","laser_chain","laser_freeze","life"])
                        self.pups.append(PowerUp(self.boss.pos,pt)); self.boss=None

            # Bullets vs UFOs
            for u in self.ufos[:]:
                if not u.alive: continue
                d=vlen(vsub(b.pos,u.pos))
                if d<u.r:
                    if b.laser_type=="pierce" and b.pierce>0: b.pierce-=1
                    elif b.laser_type in ("explosive","freeze") and b.pierce>0: b.pierce-=1; b.alive=False
                    elif b.laser_type=="chain" and b.chain_hits<b.max_chain: b.chain_hits+=1; b.alive=False
                    else: b.alive=False
                    u.hp-=1; u.flash=.08
                    if u.hp<=0:
                        u.alive=False; self.score+=u.pts; self.popup(u.pos,f"+{u.pts} UFO!")
                        self.expl(u.pos,25,150,3); self.shock(u.pos,50); self.snd["ufo_die"].play()
                        self.shake=.15; self.shake_i=5
                        if random.random()<.3: self.pups.append(PowerUp(u.pos))
                    break

        # Ship vs Asteroids
        if self.ship.invuln<=0:
            for a in self.asts[:]:
                d=vlen(vsub(self.ship.pos,a.pos))
                hd=a.radius+25 if a.at=="fire" else a.radius+10
                if d<hd:
                    if self.ship.has_shield:
                        self.ship.shield=0; self.ship.invuln=1.5; self.snd["shield_hit"].play()
                        self.shock(self.ship.pos,50)
                        if a in self.asts: self.asts.remove(a); self.expl(a.pos,10,80,2)
                    elif self.ship.ghost>0:
                        pass  # phase through
                    else:
                        self.ship_die()
                    break

        # Ship vs Boss
        if self.boss and self.boss.alive and self.ship.invuln<=0:
            if vlen(vsub(self.ship.pos,self.boss.pos))<self.boss.r+10:
                if self.ship.has_shield:
                    self.ship.shield=0; self.ship.invuln=1.5; self.snd["shield_hit"].play(); self.shock(self.ship.pos,50)
                elif self.ship.ghost>0: pass
                else: self.ship_die()

        # UFO bullets vs Ship
        if self.ship.invuln<=0:
            for ub in self.ufobs[:]:
                d=vlen(vsub(self.ship.pos,ub.pos))
                if d<12:
                    ub.alive=False
                    if self.ship.has_shield:
                        self.ship.shield=0; self.ship.invuln=1.5; self.snd["shield_hit"].play(); self.shock(self.ship.pos,40)
                    elif self.ship.ghost>0: pass
                    else: self.ship_die()
                    break

        # Black holes
        for bh in self.bhs:
            if vlen(vsub(self.ship.pos,bh.pos))<bh.r+5 and not self.ship.dashing:
                if not self.ship.ghost>0: self.ship_die()

        # Ship vs Power-ups
        for pu in self.pups[:]:
            d=vlen(vsub(self.ship.pos,pu.pos))
            if d<25:
                pu.alive=False; self.snd["powerup"].play(); self.pal.pulse(self.pal.pu_c(pu.pt),.5)
                if pu.pt=="shield": self.ship.shield=PU_DUR["shield"]; self.popup(pu.pos,"SHIELD!")
                elif pu.pt=="rapid": self.ship.rapid=PU_DUR["rapid"]; self.popup(pu.pos,"RAPID FIRE!")
                elif pu.pt=="spread": self.ship.spread=PU_DUR["spread"]; self.popup(pu.pos,"SPREAD SHOT!")
                elif pu.pt=="speed": self.ship.speed=PU_DUR["speed"]; self.popup(pu.pos,"SPEED BOOST!")
                elif pu.pt=="life":
                    self.lives+=1; self.snd["extra_life"].play(); self.popup(pu.pos,"EXTRA LIFE!")
                elif pu.pt in PU_DUR:
                    if pu.pt.startswith("laser_"):
                        lt=pu.pt.replace("laser_","")
                        self.ship.laser=PU_DUR[pu.pt]; self.ship.laser_type=lt
                        self.popup(pu.pos,f"{LASER_NAMES[pu.pt]}!")
                    elif pu.pt=="magnet":
                        self.ship.magnet=PU_DUR["magnet"]; self.popup(pu.pos,"MAGNET!")
                        self.snd["magnet_pickup"].play()
                    elif pu.pt=="ghost":
                        self.ship.ghost=PU_DUR["ghost"]; self.popup(pu.pos,"GHOST MODE!")
                        self.snd["ghost_phase"].play()
                    elif pu.pt=="multi":
                        self.ship.multi_shot=PU_DUR["multi"]; self.popup(pu.pos,"MULTI-SHOT!")
                self.expl(pu.pos,12,60,2); self.pups.remove(pu)

    @property
    def asteroids_remove(self):
        pass  # dummy for chain/explosive inline remove

    def ship_die(self):
        self.ship.alive=False; self.ship.death_t=2.5; self.lives-=1
        self.expl(self.ship.pos,50,220,4); self.shock(self.ship.pos,80)
        self.snd["player_death"].play(); self.shake=.5; self.shake_i=10
        self.pal.pulse((255,50,50),1.0); self.cc=0; self.cm=1; self.ls=0
        for p in ["shield","rapid","spread","speed","laser","magnet","ghost","multi_shot"]:
            setattr(self.ship,p,0)
        self.ship.laser_type=None

    def check_level(self):
        if len(self.asts)==0 and (self.boss is None or not self.boss.alive):
            if self.level%5==0 and self.boss is None:
                self.level+=1; self.spawn_boss()
            else:
                self.level+=1; self.snd["level_up"].play()
                self.spawn_ast(min(4+self.level,14))
                self.wat=2; self.wt=f"WAVE {self.level}"
                self.ship.invuln=2.0; self.pal.pulse((100,200,255),.6)

    def check_extra_life(self):
        if self.score>=self.nel:
            self.lives+=1; self.snd["extra_life"].play(); self.nel+=10000
            self.popup(self.ship.pos,"EXTRA LIFE!")

    def compute_danger(self):
        if not self.ship.alive: self.di=0; return
        md=9999
        for a in self.asts:
            d=vlen(vsub(a.pos,self.ship.pos))
            if d<md: md=d
        for u in self.ufos:
            d=vlen(vsub(u.pos,self.ship.pos))
            if d<md: md=d
        if self.boss and self.boss.alive:
            d=vlen(vsub(self.boss.pos,self.ship.pos))
            if d<md: md=d
        self.di=max(0,1-md/120) if md<120 else 0

    def update_offscreen(self):
        self.ind=[]
        if not self.ship.alive: return
        tg=[(a.pos,a.r,"ast") for a in self.asts]
        if self.boss and self.boss.alive: tg.append((self.boss.pos,self.boss.r,"boss"))
        tg+=[(p.pos,12,"pu") for p in self.pups]
        tg+=[(u.pos,u.r,"ufo") for u in self.ufos if u.alive]
        mg=30
        for pos,r,k in tg:
            if mg<pos[0]<WIDTH-mg and mg<pos[1]<HEIGHT-mg: continue
            dx,dy=pos[0]-self.ship.pos[0],pos[1]-self.ship.pos[1]
            a=math.atan2(dy,dx)
            ix=max(mg,min(WIDTH-mg,self.ship.pos[0]+math.cos(a)*300))
            iy=max(mg,min(HEIGHT-mg,self.ship.pos[1]+math.sin(a)*300))
            cm={"ast":(180,180,180),"boss":(255,80,80),"pu":(100,255,100),"ufo":(255,150,50)}
            self.ind.append((ix,iy,a,cm.get(k,(150,150,150))))

    def draw_danger_border(self,sf,pal):
        if self.di<=0: return
        a=int(self.di*100*(.7+.3*math.sin(pal.t*8)))
        c=hsv((pal.t*60)%60,1,1)
        bd=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); t=6
        pygame.draw.rect(bd,(*c,a),(0,0,WIDTH,t))
        pygame.draw.rect(bd,(*c,a),(0,HEIGHT-t,WIDTH,t))
        pygame.draw.rect(bd,(*c,a),(0,0,t,HEIGHT))
        pygame.draw.rect(bd,(*c,a),(WIDTH-t,0,t,HEIGHT))
        sf.blit(bd,(0,0))

    def draw_minimap(self,sf):
        mm=120; mx,my=WIDTH-mm-15,HEIGHT-mm-15; sx,sy=mm/WIDTH,mm/HEIGHT
        ms=pygame.Surface((mm,mm),pygame.SRCALPHA)
        pygame.draw.rect(ms,(0,0,0,80),(0,0,mm,mm))
        pygame.draw.rect(ms,(80,80,80,120),(0,0,mm,mm),1)
        for a in self.asts:
            px,py=int(a.pos[0]*sx),int(a.pos[1]*sy)
            if 0<=px<mm and 0<=py<mm:
                c=(100,150,255) if a.at=="ice" else (255,100,100) if a.at=="fire" else (255,215,0) if a.at=="gold" else (180,180,180)
                if a.slow_timer>0: c=(100,180,255)
                pygame.draw.circle(ms,(*c,150),(px,py),max(1,a.size))
        for u in self.ufos:
            if u.alive:
                px,py=int(u.pos[0]*sx),int(u.pos[1]*sy)
                if 0<=px<mm and 0<=py<mm: pygame.draw.circle(ms,(255,150,50,200),(px,py),2)
        if self.boss and self.boss.alive:
            px,py=int(self.boss.pos[0]*sx),int(self.boss.pos[1]*sy)
            pygame.draw.circle(ms,(255,60,60,200),(px,py),3)
        for bh in self.bhs:
            px,py=int(bh.pos[0]*sx),int(bh.pos[1]*sy)
            pygame.draw.circle(ms,(150,0,255,200),(px,py),3)
        for p in self.pups:
            px,py=int(p.pos[0]*sx),int(p.pos[1]*sy)
            pygame.draw.circle(ms,(100,255,100,200),(px,py),2)
        if self.ship.alive:
            px,py=int(self.ship.pos[0]*sx),int(self.ship.pos[1]*sy)
            pygame.draw.circle(ms,(255,255,255,255),(px,py),2)
        sf.blit(ms,(mx,my))
        sf.blit(self.ft.render("RADAR",True,(80,80,80)),(mx+mm//2-20,my-16))

    def draw_offscreen(self,sf,pal):
        for ix,iy,a,c in self.ind:
            s=8; pts=[(ix+math.cos(a)*s,iy+math.sin(a)*s),(ix+math.cos(a+2.5)*s*.6,iy+math.sin(a+2.5)*s*.6),(ix+math.cos(a-2.5)*s*.6,iy+math.sin(a-2.5)*s*.6)]
            al=int(150+80*math.sin(pal.t*4))
            ins=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
            pygame.draw.polygon(ins,(*c,al),[(int(p[0]),int(p[1]))for p in pts])
            sf.blit(ins,(0,0))

    def draw_pu_bar(self,sf):
        x,y=20,95; bars=[]
        if self.ship.shield>0: bars.append(("SHIELD",self.ship.shield,PU_DUR["shield"],self.pal.pu_c("shield")))
        if self.ship.rapid>0: bars.append(("RAPID",self.ship.rapid,PU_DUR["rapid"],self.pal.pu_c("rapid")))
        if self.ship.spread>0: bars.append(("SPREAD",self.ship.spread,PU_DUR["spread"],self.pal.pu_c("spread")))
        if self.ship.speed>0: bars.append(("SPEED",self.ship.speed,PU_DUR["speed"],self.pal.pu_c("speed")))
        if self.ship.laser>0 and self.ship.laser_type:
            lt=self.ship.laser_type
            bars.append((LASER_NAMES[f"laser_{lt}"],self.ship.laser,PU_DUR[f"laser_{lt}"],self.pal.pu_c(f"laser_{lt}")))
        if self.ship.magnet>0: bars.append(("MAGNET",self.ship.magnet,PU_DUR["magnet"],self.pal.pu_c("magnet")))
        if self.ship.ghost>0: bars.append(("GHOST",self.ship.ghost,PU_DUR["ghost"],self.pal.pu_c("ghost")))
        if self.ship.multi_shot>0: bars.append(("MULTI",self.ship.multi_shot,PU_DUR["multi"],self.pal.pu_c("multi")))
        for label,tl,mt,c in bars:
            r=tl/mt; t=self.ft.render(label,True,c); sf.blit(t,(x,y))
            bx=x+60; pygame.draw.rect(sf,(40,40,40),(bx,y+2,80,10))
            pygame.draw.rect(sf,c,(bx,y+2,int(80*r),10))
            pygame.draw.rect(sf,(100,100,100),(bx,y+2,80,10),1); y+=18

    def draw_hud(self,sf):
        sf.blit(self.fs.render(f"SCORE: {self.score}",True,self.pal.txt_c()),(20,15))
        if self.cm>1:
            sf.blit(self.fs.render(f"COMBO x{self.cm} ({self.cc})",True,hsv((self.pal.t*100)%360,1,1)),(20,38))
        sf.blit(self.fs.render(f"LEVEL {self.level}",True,self.pal.txt_c()),(WIDTH//2-self.fs.size(f"LEVEL {self.level}")[0]//2,15))
        sf.blit(self.fs.render(f"HI: {self.hi}",True,(150,150,150)),(WIDTH-self.fs.size(f"HI: {self.hi}")[0]-20,15))
        sf.blit(self.ft.render(f"BOMBS: {self.bombs} [B]",True,(200,200,100)),(WIDTH-self.ft.size(f"BOMBS: {self.bombs} [B]")[0]-20,74))
        if self.ship.dash_cd>0:
            sf.blit(self.ft.render(f"DASH: {self.ship.dash_cd:.1f}s",True,(100,100,100)),(WIDTH-160,92))
        else:
            sf.blit(self.ft.render("DASH: READY [SHIFT]",True,(100,255,200)),(WIDTH-160,92))
        sf.blit(self.ft.render(f"MUSIC: {'ON' if self.mus else 'OFF'} [M]",True,(100,100,100)),(WIDTH-160,42))
        sf.blit(self.ft.render(f"CRT: {'ON' if self.crt_on else 'OFF'} [C]",True,(100,100,100)),(WIDTH-160,58))
        # Laser type display (center)
        if self.ship.laser>0 and self.ship.laser_type:
            lt=self.ship.laser_type; lc=self.pal.laser_c(lt)
            lt_text=f">>> {LASER_NAMES[f'laser_{lt}']} <<"
            lt_surf=self.fm.render(lt_text,True,lc)
            lt_surf.set_alpha(int(180+75*math.sin(self.pal.t*4)))
            sf.blit(lt_surf,(WIDTH//2-lt_surf.get_width()//2,HEIGHT-20))
        for i in range(self.lives):
            lx,ly=30+i*28,HEIGHT-30; c=self.pal.ship_c()
            pygame.draw.polygon(sf,c,[(lx+10,ly),(lx-5,ly+12),(lx+5,ly+12)],2)
        self.draw_pu_bar(sf); self.draw_minimap(sf)
        if self.wat>0:
            a=min(1.0,self.wat)*255; c=hsv((self.pal.t*60)%360,1,1)
            wt=self.fl.render(self.wt,True,c); wt.set_alpha(int(a))
            sf.blit(wt,(WIDTH//2-wt.get_width()//2,HEIGHT//2-80))

    def draw_menu(self,sf):
        self.stars.draw(sf,self.pal)
        for n in self.neb: n.draw(sf,self.pal)
        th=(self.pal.t*30)%360; tc=hsv(th,.9,1); t2c=hsv((th+60)%360,.9,1)
        gs=pygame.Surface((WIDTH,140),pygame.SRCALPHA)
        gs.blit(self.fl.render("PSYCHEDELIC",True,(*tc,50)),(WIDTH//2-self.fl.size("PSYCHEDELIC")[0]//2,2))
        gs.blit(self.fl.render("ASTEROIDS",True,(*t2c,50)),(WIDTH//2-self.fl.size("ASTEROIDS")[0]//2,72))
        sf.blit(gs,(0,120),special_flags=pygame.BLEND_ADD)
        sf.blit(self.fl.render("PSYCHEDELIC",True,tc),(WIDTH//2-self.fl.size("PSYCHEDELIC")[0]//2,120))
        sf.blit(self.fl.render("ASTEROIDS",True,t2c),(WIDTH//2-self.fl.size("ASTEROIDS")[0]//2,190))
        sf.blit(self.ft.render("v4.0 LASER ARSENAL",True,(120,120,120)),(WIDTH//2-self.ft.size("v4.0 LASER ARSENAL")[0]//2,260))
        if int(self.pal.t*2)%2:
            sf.blit(self.fm.render("PRESS ENTER TO START",True,self.pal.txt_c()),(WIDTH//2-self.fm.size("PRESS ENTER TO START")[0]//2,300))
        ctrls=[
            "< > or A D  Rotate    UP or W  Thrust    SPACE  Shoot",
            "B  Bomb    LSHIFT  Dash    H  Hyperspace    P  Pause",
            "M  Music    C  CRT Effect    ESC  Quit",
            "",
            "POWER-UPS: [S]hield  [R]apid  [W]ide Shot  [F]ast  [+] Life",
            "[M]agnet  [G]host  [*]Multi-Shot  [+Extra Lasers: P H E C Z]",
            "",
            "LASER TYPES:  [P]ierce  [H]oming  [E]xplosive  [C]hain  [Z] Freeze",
            "ASTEROIDS: Normal / Ice(splits 3) / Fire(danger) / Gold(2x pts)",
            "UFO enemies!  Bosses shoot back!  Black holes!  Kill streaks!",
        ]
        for i,line in enumerate(ctrls):
            c=(160,160,160) if i<3 else (110,110,110)
            sf.blit(self.ft.render(line,True,c),(WIDTH//2-self.ft.size(line)[0]//2,360+i*22))
        if self.hi>0:
            sf.blit(self.fs.render(f"HIGH SCORE: {self.hi}",True,(200,200,100)),(WIDTH//2-self.fs.size(f"HIGH SCORE: {self.hi}")[0]//2,560))

    def draw_game_over(self,sf):
        ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,120)); sf.blit(ov,(0,0))
        p=.7+.3*math.sin(self.pal.t*3)
        sf.blit(self.fl.render("GAME OVER",True,hsv(0,p,1)),(WIDTH//2-self.fl.size("GAME OVER")[0]//2,150))
        sf.blit(self.fm.render(f"SCORE: {self.score}",True,self.pal.txt_c()),(WIDTH//2-self.fm.size(f"SCORE: {self.score}")[0]//2,240))
        nh=self.score>=self.hi and self.score>0
        ht=f"{'NEW ' if nh else ''}HIGH SCORE: {self.hi}"; hc=(255,255,0) if nh else (255,255,100)
        sf.blit(self.fm.render(ht,True,hc),(WIDTH//2-self.fm.size(ht)[0]//2,290))
        stats=[f"Level: {self.level}",f"Kills: {self.kills}",f"Max Combo: x{self.mxc}",
               f"Shots: {self.shots}",f"Accuracy: {self.kills/max(1,self.shots)*100:.1f}%"]
        for i,s in enumerate(stats):
            sf.blit(self.fs.render(s,True,(160,160,160)),(WIDTH//2-self.fs.size(s)[0]//2,360+i*28))
        if int(self.pal.t*2)%2:
            sf.blit(self.fm.render("PRESS ENTER TO RESTART",True,self.pal.txt_c()),(WIDTH//2-self.fm.size("PRESS ENTER TO RESTART")[0]//2,520))

    def draw_pause(self,sf):
        ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,100)); sf.blit(ov,(0,0))
        sf.blit(self.fl.render("PAUSED",True,self.pal.txt_c()),(WIDTH//2-self.fl.size("PAUSED")[0]//2,HEIGHT//2-40))
        sf.blit(self.fs.render("Press P to resume",True,(150,150,150)),(WIDTH//2-self.fs.size("Press P to resume")[0]//2,HEIGHT//2+30))

    def update(self,dt):
        self.pal.update(dt)
        self.sst-=dt
        if self.sst<=0:
            if len(self.sstars)<3: self.sstars.append(ShootingStar())
            self.sst=random.uniform(2,6)
        for s in self.sstars: s.update(dt)
        self.sstars=[s for s in self.sstars if s.alive]
        for n in self.neb: n.update(dt)
        if self.state!="playing" or self.paused: return
        keys=pygame.key.get_pressed()
        if self.scd>0: self.scd-=dt
        if self.tcd>0: self.tcd-=dt
        if self.shake>0: self.shake-=dt
        if self.wat>0: self.wat-=dt
        if self.ct>0: self.ct-=dt
        else:
            if self.cc>0: self.mxc=max(self.mxc,self.cc)
            self.cc=0; self.cm=1; self.ls=0
        if self.ship.alive and self.ship.thrusting and self.tcd<=0:
            self.snd["thrust"].play(); self.tcd=.13
        # Black hole gravity on ship
        if self.ship.alive:
            for bh in self.bhs:
                p=bh.pull(self.ship.pos)
                self.ship.vel[0]+=p[0]*dt; self.ship.vel[1]+=p[1]*dt
        self.ship.update(dt,keys)
        # Magnet: attract powerups
        if self.ship.magnet>0:
            for pu in self.pups:
                d=vlen(vsub(self.ship.pos,pu.pos))
                if d<200:
                    dx,dy=self.ship.pos[0]-pu.pos[0],self.ship.pos[1]-pu.pos[1]
                    force=300/(d+10)
                    pu.pos[0]+=dx/d*force*dt; pu.pos[1]+=dy/d*force*dt
        # Update asteroids
        for a in self.asts[:]:
            r=a.update(dt,self.bhs)
            if r=="absorbed":
                self.expl(a.pos,8,60,2); self.asts.remove(a)
        for b in self.buls: b.update(dt)
        for ub in self.ufobs: ub.update(dt)
        for p in self.parts: p.update(dt)
        for d in self.debr: d.update(dt)
        for pu in self.pups: pu.update(dt)
        for s in self.shoks: s.update(dt)
        for p in self.pops: p.update(dt)
        for s in self.streaks: s.update(dt)
        for u in self.ufos: u.update(dt,self.ship.pos)
        for bh in self.bhs: bh.update(dt)
        if self.boss and self.boss.alive:
            self.boss.update(dt)
            for bpos,bvel in self.boss.try_shoot(dt,self.ship.pos):
                self.ufobs.append(UFOBullet(bpos,bvel)); self.snd["ufo_shoot"].play()
        # Update homing laser targets
        for b in self.buls:
            if b.laser_type=="homing" and b.alive and b.homing_target:
                t=b.homing_target
                if hasattr(t,'alive') and not t.alive: b.homing_target=self._find_nearest_target(b.pos)
        # Clean
        self.buls=[b for b in self.buls if b.alive]
        self.ufobs=[b for b in self.ufobs if b.alive]
        self.parts=[p for p in self.parts if p.alive]
        self.debr=[d for d in self.debr if d.alive]
        self.pups=[p for p in self.pups if p.alive]
        self.shoks=[s for s in self.shoks if s.alive]
        self.pops=[p for p in self.pops if p.alive]
        self.streaks=[s for s in self.streaks if s.alive]
        self.ufos=[u for u in self.ufos if u.alive]
        self.bhs=[b for b in self.bhs if b.alive]
        self.handle_collisions()
        if not self.ship.alive and self.ship.death_t<=0:
            if self.lives>0: self.ship=Ship()
            else:
                self.state="game_over"; self.mxc=max(self.mxc,self.cc)
                if self.score>self.hi: self.hi=self.score; save_hs(self.hi)
                self.stop_bgm()
        self.check_level()
        if self.ship.alive: self.check_extra_life()
        self.compute_danger(); self.update_offscreen()

    def draw(self,sf):
        bg=self.pal.bg(); sf.fill(bg)
        sx,sy=0,0
        if self.shake>0:
            self.shake_i*=.95; si=int(self.shake_i)
            sx,sy=random.randint(-si,si),random.randint(-si,si)
        gs=pygame.Surface((WIDTH,HEIGHT)); gs.fill(bg)
        if self.state=="menu":
            self.draw_menu(gs)
        else:
            for n in self.neb: n.draw(gs,self.pal)
            self.stars.draw(gs,self.pal)
            for ss in self.sstars: ss.draw(gs,self.pal)
            for bh in self.bhs: bh.draw(gs,self.pal)
            for d in self.debr: d.draw(gs,self.pal)
            for a in self.asts: a.draw(gs,self.pal)
            if self.boss and self.boss.alive: self.boss.draw(gs,self.pal)
            for u in self.ufos: u.draw(gs,self.pal)
            for pu in self.pups: pu.draw(gs,self.pal)
            for b in self.buls: b.draw(gs,self.pal)
            for ub in self.ufobs: ub.draw(gs,self.pal)
            self.ship.draw(gs,self.pal)
            for p in self.parts: p.draw(gs,self.pal)
            for s in self.shoks: s.draw(gs,self.pal)
            for p in self.pops: p.draw(gs,self.pal,self.fp)
            for s in self.streaks: s.draw(gs,self.pal,self.fm)
            self.draw_offscreen(gs,self.pal); self.draw_danger_border(gs,self.pal)
            self.draw_hud(gs)
            if self.paused: self.draw_pause(gs)
            if self.state=="game_over": self.draw_game_over(gs)
        sf.blit(gs,(sx,sy))
        if self.crt_on: sf.blit(self.crt,(0,0))

    def handle_event(self,ev):
        if ev.type==pygame.KEYDOWN:
            if ev.key==pygame.K_ESCAPE:
                if self.state=="playing": self.state="menu"; self.stop_bgm(); self.paused=False
                else: pygame.quit(); sys.exit()
            if self.state=="menu":
                if ev.key==pygame.K_RETURN:
                    self.state="playing"; self.reset(); self.snd["select"].play(); self.play_bgm()
            elif self.state=="playing" and not self.paused:
                if ev.key==pygame.K_SPACE and self.ship.alive: self.shoot()
                if ev.key==pygame.K_b and self.ship.alive: self.use_bomb()
                if ev.key==pygame.K_LSHIFT and self.ship.alive:
                    if self.ship.start_dash(): self.snd["dash"].play()
                if ev.key==pygame.K_h and self.ship.alive:
                    self.ship.pos=[random.randint(50,WIDTH-50),random.randint(50,HEIGHT-50)]
                    self.ship.vel=[0,0]; self.ship.invuln=2.0
                    self.expl(tuple(self.ship.pos),20,80,2); self.snd["hyperspace"].play()
                if ev.key==pygame.K_p: self.paused=not self.paused; self.snd["pause"].play()
                if ev.key==pygame.K_m:
                    self.mus=not self.mus
                    if self.mus: self.play_bgm()
                    else: self.stop_bgm()
                if ev.key==pygame.K_c: self.crt_on=not self.crt_on
            elif self.state=="playing" and self.paused:
                if ev.key==pygame.K_p: self.paused=False; self.snd["pause"].play()
            elif self.state=="game_over":
                if ev.key==pygame.K_RETURN:
                    self.state="playing"; self.reset(); self.snd["select"].play(); self.play_bgm()


def main():
    game=Game(); running=True
    while running:
        dt=min(clock.tick(FPS)/1000.0,.05)
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: running=False
            game.handle_event(ev)
        game.update(dt); game.draw(screen); pygame.display.flip()
    pygame.quit(); sys.exit()

if __name__=="__main__":
    main()