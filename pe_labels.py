"""Version-pinned PE display-string patch; no game executable is distributed."""
import struct

def patch_executable(source, rows):
    b=bytearray(source)
    def u16(o):return struct.unpack_from('<H',b,o)[0]
    def u32(o):return struct.unpack_from('<I',b,o)[0]
    def u64(o):return struct.unpack_from('<Q',b,o)[0]
    def align(x,a):return (x+a-1)//a*a
    pe=u32(60);assert b[pe:pe+4]==b'PE\0\0'
    coff=pe+4;opt=pe+24;assert u16(opt)==0x20b
    n=u16(coff+2);sht=opt+u16(coff+16);sections=[]
    for i in range(n):
     o=sht+i*40;vs,va,rs,rp=struct.unpack_from('<IIII',b,o+8);sections.append((b[o:o+8].rstrip(b'\0'),vs,va,rs,rp))
    image=u64(opt+24);sa=u32(opt+32);fa=u32(opt+36)
    assert u32(opt+112+4*8)==0,'Signed executable must not be modified by this patch'
    assert align(sht+(n+1)*40,fa)<=min(s[4] for s in sections if s[3])
    assert not any(b[sht+n*40:sht+(n+1)*40]),'No spare section-header slot'
    def raw(rva):
     for name,vs,va,rs,rp in sections:
      if va<=rva<va+rs:return rp+rva-va
     raise ValueError(hex(rva))
    def rva(rawp):
     for name,vs,va,rs,rp in sections:
      if rp<=rawp<rp+rs:return va+rawp-rp
     raise ValueError(hex(rawp))
    # Every modified pointer must already participate in ASLR relocation.
    relva,relsize=struct.unpack_from('<II',b,opt+112+5*8);pos=raw(relva);end=pos+relsize;relocs=set()
    while pos<end:
     page,size=struct.unpack_from('<II',b,pos);assert size>=8 and size%2==0
     for q in range(pos+8,pos+size,2):
      v=u16(q)
      if v>>12==10:relocs.add(page+(v&4095))
     pos+=size
    translations={row['label']:row['chinese'] for row in rows}
    assert len(rows)==173 and u64(rows[-1]['pointer_offset']+8)==0
    payload=bytearray();updates=[]
    newva=align(max(va+max(vs,rs) for _,vs,va,rs,rp in sections),sa)
    newraw=align(len(b),fa)
    for row in rows:
     off=row['pointer_offset'];assert u64(off)==row['original_va'];assert rva(off) in relocs
     labeloff=raw(row['original_va']-image);orig=b[labeloff:b.index(0,labeloff)].decode('utf-8');assert orig==row['label']
     text=orig+' ('+translations[orig]+')'
     value=image+newva+len(payload);payload.extend(text.encode('utf-8')+b'\0')
     struct.pack_into('<Q',b,off,value);updates.append({'offset':off,'original':row['original_va'],'replacement':value,'text':text})
    rs=align(len(payload),fa);header=struct.pack('<8sIIIIIIHHI',b'.xploc\0\0',len(payload),newva,rs,newraw,0,0,0,0,0x40000040)
    b[sht+n*40:sht+(n+1)*40]=header
    struct.pack_into('<H',b,coff+2,n+1)
    struct.pack_into('<I',b,opt+8,u32(opt+8)+rs)
    struct.pack_into('<I',b,opt+56,align(newva+len(payload),sa))
    struct.pack_into('<I',b,opt+60,max(u32(opt+60),align(sht+(n+1)*40,fa)))
    struct.pack_into('<I',b,opt+64,0)
    b.extend(b'\0'*(newraw-len(b)));b.extend(payload);b.extend(b'\0'*(rs-len(payload)))
    # PE checksum; no signature or protection bypass.
    checksum=0
    for off in range(0,len(b),2):
     value=int.from_bytes(b[off:off+2],'little');checksum+=value;checksum=(checksum&0xffff)+(checksum>>16)
    checksum=(checksum&0xffff)+(checksum>>16);checksum+=len(b)
    struct.pack_into('<I',b,opt+64,checksum)
    # Prove that modifications are confined to header metadata and the 173 pointer cells.
    allowed=set(range(coff+2,coff+4))|set(range(opt+8,opt+12))|set(range(opt+56,opt+64))|set(range(opt+64,opt+68))|set(range(sht+n*40,sht+(n+1)*40))
    for row in rows:allowed.update(range(row['pointer_offset'],row['pointer_offset']+8))
    diffs=[i for i,(x,y) in enumerate(zip(source,b)) if x!=y];assert all(i in allowed for i in diffs)
    textsec=next(s for s in sections if s[0]==b'.text');assert b[textsec[4]:textsec[4]+textsec[3]]==source[textsec[4]:textsec[4]+textsec[3]]
    return bytes(b)
