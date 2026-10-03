import sys,os,tty,termios,json,time
fd=sys.stdin.fileno();old=termios.tcgetattr(fd)
try:
 tty.setraw(fd)
 sys.stdout.write('\x1b[2J\x1b[H\x1b[?1002h\x1b[?1006hCua native background input probe\r\n');sys.stdout.flush()
 with open(sys.argv[1],'ab',buffering=0) as out:
  out.write(b'READY\n')
  while True:
   data=os.read(fd,4096)
   if not data:break
   out.write(json.dumps({'ns':time.monotonic_ns(),'hex':data.hex()}).encode()+b'\n')
finally:
 sys.stdout.write('\x1b[?1002l\x1b[?1006l');sys.stdout.flush()
 termios.tcsetattr(fd,termios.TCSADRAIN,old)
