import socket,json,subprocess,pathlib,os,time,concurrent.futures
if os.environ.get('CUA_NATIVE_TEST') != '1':
 raise SystemExit('Opt-in only: set CUA_NATIVE_TEST=1 in a disposable Hyprland session')
base=pathlib.Path(os.environ['CUA_NATIVE_TEST_DIR'])
instance=os.environ['HYPRLAND_INSTANCE_SIGNATURE']
env=dict(os.environ,XDG_RUNTIME_DIR=os.environ['XDG_RUNTIME_DIR'],WAYLAND_DISPLAY=os.environ['WAYLAND_DISPLAY'],HYPRLAND_INSTANCE_SIGNATURE=instance,LD_AUDIT='',LD_LIBRARY_PATH='')
def ctl(*args):return subprocess.check_output(['hyprctl',*args],env=env,text=True)
expected_pid=int(os.environ['CUA_NATIVE_TEST_COMPOSITOR_PID'])
instances=json.loads(ctl('instances','-j'))
assert any(i['instance']==instance and i['pid']==expected_pid and i['wl_socket']==env['WAYLAND_DISPLAY'] for i in instances), 'Exact disposable compositor identity required'
def evaluate(code):assert ctl('eval',code).strip()=='ok'
evaluate('hl.dispatch(hl.dsp.focus({window="title:^Cua human$"}))')
clients=json.loads(ctl('-j','clients'));human=next(c for c in clients if c['title']=='Cua human')
evaluate('hl.dispatch(hl.dsp.cursor.move({x='+str(human['at'][0]+50)+',y='+str(human['at'][1]+70)+'}))')
targets=[next(c for c in clients if c['title']==f'Cua {name}') for name in ['one','two']]
def state():
 return {key:json.loads(ctl('-j',key)) for key in ['activewindow','cursorpos','activeworkspace']}
def received(name):
 p=base/f'terminal-{name}.jsonl'
 return b''.join(bytes.fromhex(json.loads(line)['hex']) for line in p.read_text().splitlines() if line!='READY')
class Lane:
 def __init__(self,lane,target):
  self.target=target;self.sequence=0;self.actions=[]
  self.s=socket.socket(socket.AF_UNIX,socket.SOCK_SEQPACKET);self.s.settimeout(4)
  self.s.connect(f"{env['XDG_RUNTIME_DIR']}/hypr/{instance}/cua-input-v3"+('' if lane==0 else '-2')+'.sock')
  assert self.req('HELLO')['protocol']==3
  assert self.req('CLAIM')['ok']
 def req(self,packet):
  self.s.send(packet.encode());return json.loads(self.s.recv(4096))
 def action(self,op,cap,args):
  c=self.target;r=self.req(f"TARGET {c['pid']} {c['address'][2:]} {cap}");assert r['ok'],r
  self.sequence+=1
  result=self.req(f"{op} {self.sequence} {r['target']} {r['revision']} {args}")
  if result.get('phase')=='started':result=json.loads(self.s.recv(4096))
  self.actions.append({'operation':op,'result':result});assert result['ok'],result
  return result
old={name:received(name) for name in ['one','two','human']}
# Publish the virtual primary keyboard before taking the isolation baseline.
# It exercises the compositor's ordinary primary input path in this disposable desktop.
p=subprocess.Popen(['wtype','-s','800','-d','35','HUMAN','-s','1800'],env=env)
time.sleep(.3)
lanes=[Lane(i,c) for i,c in enumerate(targets)]
before=state()
for lane in lanes:
 lane.action('KEY',2,'30 0')
 lane.action('KEY',2,'48 1')
 lane.action('CLICK',1,'50 100 272 1')
 lane.action('SCROLL',4,'50 100 0 15')
with concurrent.futures.ThreadPoolExecutor(2) as pool:
 results=list(pool.map(lambda lane:lane.action('DRAG',8,'50 100 180 150 1400'),lanes))
after=state()
time.sleep(.1)
new={name:received(name)[len(old[name]):] for name in old}
receipt={'app_executable':os.readlink(f"/proc/{targets[0]['pid']}/exe"),'off_workspace_targets':[c['workspace'] for c in targets],
 'primary_unchanged':before==after,'before':before,'after':after,'actions':[lane.actions for lane in lanes],
 'delivered':{name:{'hex':data.hex(),'text':data.decode(errors='replace')} for name,data in new.items()}}
(base/'terminal-qualification.json').write_text(json.dumps(receipt,indent=2))
for lane in lanes:lane.req('STOP');lane.s.close()
p.wait(timeout=4)
print(json.dumps({k:v for k,v in receipt.items() if k not in ['before','after']},indent=2))
assert receipt['primary_unchanged']
assert new['human']==b'HUMAN',new['human']
for name in ['one','two']:
 assert new[name].startswith(b'aB'),(name,new[name])
 assert b'\x1b[<0;' in new[name] and b'\x1b[<32;' in new[name],(name,new[name])
 assert b'\x1b[<65;' in new[name],(name,new[name])
