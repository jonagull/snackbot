import network, socket, time, gc
from drive import drive, stop, set_trim, get_trim
import secrets

PAGE = """<!DOCTYPE html><html><head>
<meta name=viewport content="width=device-width,initial-scale=1,user-scalable=no">
<style>
body{font-family:system-ui;background:#111;color:#eee;margin:0;padding:16px;
     -webkit-user-select:none;user-select:none;touch-action:manipulation}
#g{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;max-width:340px;margin:auto}
button{height:80px;font-size:20px;border:0;border-radius:12px;background:#2a2a2a;color:#eee}
button:active,button.on{background:#4a7}
.stop{background:#722}
.sp{grid-column:1/4;font-size:14px;color:#aaa;margin-top:6px}
input{width:100%}
</style></head><body>
<div id=g>
<button></button><button data-c=w>&#9650;</button><button></button>
<button data-c=a>&#9664;</button><button class=stop data-c=x>STOP</button><button data-c=d>&#9654;</button>
<button></button><button data-c=s>&#9660;</button><button></button>
<div class=sp>Speed <span id=v>60</span>%<input id=sl type=range min=20 max=100 value=60></div>
<div class=sp>Trim <span id=tv>0</span><input id=tr type=range min=-50 max=50 value=0></div>
</div>
<script>
let t=null,sp=60,cur=null;
const sl=document.getElementById('sl');
sl.oninput=()=>{sp=+sl.value;document.getElementById('v').textContent=sp};
const tr=document.getElementById('tr');
tr.oninput=()=>{
  document.getElementById('tv').textContent=tr.value;
  fetch('/t?v='+tr.value).catch(()=>{});
};
function send(c){fetch('/c?d='+c+'&s='+sp).catch(()=>{})}
function hold(c){
  if(cur===c)return;
  cur=c;send(c);clearInterval(t);t=setInterval(()=>send(c),250);
  const b=document.querySelector('button[data-c="'+c+'"]');
  if(b)b.classList.add('on');
}
function rel(){
  cur=null;clearInterval(t);t=null;send('x');
  document.querySelectorAll('button.on').forEach(b=>b.classList.remove('on'));
}
document.querySelectorAll('button[data-c]').forEach(b=>{
  const c=b.dataset.c;
  if(c==='x'){b.onclick=()=>send('x');return}
  b.addEventListener('pointerdown',e=>{e.preventDefault();hold(c)});
  b.addEventListener('pointerup',rel);
  b.addEventListener('pointerleave',rel);
  b.addEventListener('pointercancel',rel);
});
const K={ArrowUp:'w',ArrowDown:'s',ArrowLeft:'a',ArrowRight:'d',
         w:'w',s:'s',a:'a',d:'d',W:'w',S:'s',A:'a',D:'d'};
addEventListener('keydown',e=>{
  if(e.key===' '){e.preventDefault();rel();return}
  const c=K[e.key];
  if(c){e.preventDefault();hold(c)}
});
addEventListener('keyup',e=>{const c=K[e.key];if(c&&cur===c)rel()});
addEventListener('blur',rel);
</script></body></html>"""

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.config(pm=0xa11140)          # disable wifi power save
wlan.connect(secrets.SSID, secrets.PASSWORD)

for _ in range(40):
    if wlan.isconnected():
        break
    time.sleep(0.5)

if not wlan.isconnected():
    print("wifi failed")
    raise SystemExit

print("http://%s/" % wlan.ifconfig()[0])

srv = socket.socket()
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("0.0.0.0", 80))
srv.listen(5)
srv.settimeout(0.02)

last = time.ticks_ms()
moving = False

def do(cmd, sp):
    global last, moving
    last = time.ticks_ms()
    lvl = sp / 100.0
    if   cmd == 'w': drive( lvl,  lvl); moving = True
    elif cmd == 's': drive(-lvl, -lvl); moving = True
    elif cmd == 'a': drive(-lvl,  lvl); moving = True
    elif cmd == 'd': drive( lvl, -lvl); moving = True
    else:            stop();            moving = False

def ok(cl, body=b"ok"):
    cl.send(b"HTTP/1.1 200 OK\r\nContent-Length: %d\r\nConnection: close\r\n\r\n" % len(body))
    cl.send(body)

def handle(cl):
    try:
        cl.settimeout(1.0)
        req = cl.recv(512).decode()
        line = req.split("\r\n")[0]
        path = line.split(" ")[1] if " " in line else "/"

        if path.startswith("/c?"):
            p = dict(kv.split("=") for kv in path.split("?", 1)[1].split("&") if "=" in kv)
            do(p.get("d", "x"), int(p.get("s", 60)))
            ok(cl)
        elif path.startswith("/t?"):
            p = dict(kv.split("=") for kv in path.split("?", 1)[1].split("&") if "=" in kv)
            set_trim(int(p.get("v", 0)) / 100.0)
            ok(cl, b"%d" % int(get_trim() * 100))
        elif path == "/":
            cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n")
            cl.send(PAGE)
        else:
            cl.send(b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
    except Exception as e:
        print("req err", e)
    finally:
        cl.close()

tick = 0
while True:
    if not wlan.isconnected():
        stop(); moving = False
        print("wifi lost, reconnecting")
        wlan.connect(secrets.SSID, secrets.PASSWORD)
        time.sleep(1)
        continue

    while True:                       # drain the whole backlog
        try:
            cl, _ = srv.accept()
        except OSError:
            break
        handle(cl)

    if moving and time.ticks_diff(time.ticks_ms(), last) > 500:
        stop()
        moving = False

    tick += 1
    if tick >= 50:
        tick = 0
        gc.collect()
    time.sleep_ms(5)