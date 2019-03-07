#!/usr/bin/python3

import zipfile
import xml.sax

import os
import urllib

import sys
import ast
import re

.. add fields volume and dimensions

class TableGrouper:
  def __init__(self):
    self.rows=[]
    self.dump = open("tdump", "w", encoding="utf-8")
    self.limit=100
    self.groups=[]

  def __del__(self):
    if self.dump:
      self.dump.close()
    pass

  def row(self, r, rlinks):
    """ add row to table 
        second field for all row hyperlinks"""
#    print("name>", r[2])
#    print("quantity>", r[3])
#    print("code_seller>", r[4])
#    print("code_manuf>", r[5])
    self.rows.append([self.groups.copy(), r, rlinks])

#    self.dump.write("|".join(self.groups)+"\t")
#    self.dump.write("\t".join(map(lambda x: "|".join(x), r)))
    #self.dump.write(repr(self.rows[-1]))
    #self.dump.write("\n")
    #self.limit -= 1
    if not self.limit:
      print("LIMIT!")
      exit()
    pass

  def group_begin(self):
    """ get row description from last row.
        make it added to all rows in the group """
    if self.dump: self.dump.write("group begin\n")
    g_row = self.rows.pop()
    if self.dump: self.dump.write(repr(g_row)+"\n")
    g_cells = g_row[1]
    if g_cells:
      grp = ''.join(g_cells[1])
    else:
      grp = ''
    self.groups.append(grp)
    pass

  def group_end(self):
    """ drop group from the addition to rows """
    if self.dump: self.dump.write("group end\n")
    self.groups.pop()
    pass

class Cell:
  def __init__(self):
    self.data=[]
    self.repeat=1
    self.links=[]

class ODSDecoder(xml.sax.ContentHandler):
  def __init__(self, tablebuilder):
    self.t = tablebuilder

  def startDocument(self):
    self.level = 0
    #self.table = []
    self.row = []
    self.cell = None
    self.skip = 0
    self.skiptag = None
    #self.group_enter = False
    #self.groupstack = []

  def endDocument(self):
    pass

  def startElement(self, name, attrs):
    if self.skip:
      if name == self.skiptag:
        self.skip+=1
      return
#    print(" "*self.level, name)
#    for k in attrs.keys():
#      print(" "*self.level,'-',k,'=',attrs[k])
    self.level+=1
    if name=="office:automatic-styles":
      self.skip=1
      self.skiptag=name
    if name=="table:table-cell":
      self.cell=Cell()
      self.cell.repeat = int(attrs.get("table:number-columns-repeated", "1"))
    if name=="table:table-row-group":
      #print("-"*20)
      #self.group_enter = True
      self.t.group_begin()
    if name=="text:a":
      #print(attrs.keys(), attrs.values())
      self.cell.links.append(attrs['xlink:href'])

  def characters(self, content):
    if not self.skip:
      #print(" "*self.level, content)
      self.cell.data.append(content)

  def endElement(self, name):
    if self.skip:
      if name==self.skiptag:
        self.skip-=1
    if not self.skip: 
      self.level-=1
      if name=="table:table-cell":
        self.row.append(self.cell)
        self.cell = None
      if name=="table:table-row":
        """ drop empty trailing cells """
        while self.row and self.row[-1].data == []:
          self.row.pop()
        r=[]
        rlinks=[]
        for c in self.row:
          r.extend([c.data]*c.repeat)
          rlinks+=c.links
        self.t.row(r, rlinks)
        self.row = []
      if name=="table:table-row-group":
        self.t.group_end() 

# *** SPECTORG ***

def read_spectorg_quantities():
  z=zipfile.ZipFile(r"spectorg_q.ods")
  f=z.open("content.xml")
  parser = xml.sax.make_parser()
  t = TableGrouper()
  o = ODSDecoder(t)
  parser.setContentHandler(o)
  parser.parse(f)
  f.close()
  z.close()

  descf = open("spectorg.dat", encoding="utf-8")
  desc = {}
  for d in descf:
    xid,name,code,pack1,pack2,img_f,material,manuf,grouping = ast.literal_eval(d.strip())
    desc[xid]=[name,code,pack1,pack2,img_f,material,manuf,grouping]
  descf.close()

  of = open("spectorg_q.dat", "w", encoding="utf-8")
  first=True
  for grouping, cells, hrefs in t.rows:
    if len(cells)<8:
      continue
    if first:
      first=False
      continue
    
    xid = ''.join(cells[0])
    price = ''.join(cells[5])
    avail = ''.join(cells[7])
    if xid in desc:
      name,code,pack1,pack2,img_f,material,manuf,grouping = desc[xid]
      of.write(repr([xid, name, img_f, price, pack1, pack2, None, code, None, material, manuf, avail, '/'.join(grouping), None]) + "\n")
    else:
      print("no info for", xid)
  of.close()


def read_spectorg():
  z=zipfile.ZipFile(r"spectorg.ods")
  f=z.open("content.xml")
  parser = xml.sax.make_parser()
  t = TableGrouper()
  o = ODSDecoder(t)
  parser.setContentHandler(o)
  parser.parse(f)
  f.close()
  z.close()

  imgs = {}
  for f in os.listdir("spectorg_images"):
    imgs[os.path.splitext(f)[0].lower()] = f
    # use lowercase name without extension as key to find file

  #material=set()
  #manuf=set()

  f = open("spectorg.dat", "w", encoding="utf-8")
  #f.write(repr(['Группа', 'Пусто1', 'Наименование', 'Идентификатор', 'Артикул', 'Упаковка1', 'Упаковка2', 'Изображение', 'Материал', 'Производитель', 'Цена'])+'\n')
  for grouping, cells, hrefs in t.rows:
    if not grouping:
      continue
  #f.write(u"\t".join(map(lambda x: u"|".join(x), r)))
#    f.write(u"\u200b".join(c)+u"\t")
#    if len(u"\u200b".join(c)+u"\t")>200:
#      exit()

    name=''.join(cells[1]).strip()
    xid=''.join(cells[2]).strip()
    code=''.join(cells[3]).strip()
    pack1=''.join(cells[4]).strip()
    pack2=''.join(cells[5]).strip()

    if cells[6]:
      img_id = ''.join(cells[6]).lower().strip()
      img_f=imgs.get(img_id)

    material=''.join(cells[7]).strip()
    manuf=''.join(cells[8]).strip()

    f.write(repr([xid, name, code, pack1, pack2, img_f, material, manuf, grouping])+"\n")
    
#    f.write(repr([xid.encode("utf-8"),
#		(name or '').encode("utf-8"), 
#		(code or '').encode("utf-8"),
#		(pack1 or '').encode("utf-8"), 
#		(pack2 or '').encode("utf-8"),
#		(img_f or '').encode("utf-8"),
#		(material or '').encode("utf-8"),
#		(manuf or '').encode("utf-8"),
#		grouping])+"\n")

  f.close()

#  open("material", "w").write('\n'.join(list(material)))
#  open("manuf", "w").write('\n'.join(list(manuf)))



# *** PILOT MS ***

def de_esc(s):
  if not s:
    return ""
  if s[0]=='"' and s[-1]=='"':
    return s[1:-1].replace('""', '"')
  else:
    return s.strip()

def split_tsv(s):
  return map(de_esc, s.rstrip("\n").split("\t"))


def read_pilot_groups():
  print("PILOT: Reading groups")
  groups={}
  for l in open("pilot_groups.tsv", encoding="utf-8"):
    g_id, g_name, g_file, g_export, g_displayname, g_manuffilter = split_tsv(l)
    groups[g_name] = {"displayname": g_displayname, "manuffilter": g_manuffilter, "export": True if g_export=="True" else False}
    if g_file:
      g_fn="pilot_groups/"+g_file[:-4]+".ods"
      print("Reading", g_fn)
      data = {}
#      try:
      if True:
        z=zipfile.ZipFile(g_fn)
        f=z.open("content.xml")
        parser = xml.sax.make_parser()
        t = TableGrouper()
        o = ODSDecoder(t)
        parser.setContentHandler(o)
        parser.parse(f)
        f.close()
        z.close()
        g_info = groups[g_name]["data"] = {}
        for grouping, cells, hrefs in t.rows:
          if len(cells)<14:
            continue
          g_info[''.join(cells[0]).strip()] = {"net": ''.join(cells[13])}

#      except:
#        print("Failed:", g_fn)
#        continue
  of = open("pilot_groups.dat", "w", encoding="utf-8")
  of.write(repr(groups))
  of.close()


pilot_img_prefix="http://www.pilotms.ru/bin.aspx?ID="
pilot_img_dir="pilot_images"
def pilot_img(url):
  if url.startswith(pilog_img_prefix):
        uid=url[len(pilog_img_prefix):]
        fn=os.path.join(pilot_img_dir, uid+".jpg")
        if not os.path.exists(fn):
          print("downloading", url, "->", fn)
          #q=urllib.request.urlopen(url)
          try:
            q=urllib.urlopen(url)
            #data=q.readall()
            data=q.read()
            f=open(fn, "wb")
            f.write(data)
            f.close()
          except:
            print("failed")
            faillog = open("pilog_img_fail", "a", encoding="utf-8")
            faillog.write("%s\t%s\n"%(xid, url))
            faillog.close()
  else:
        print ("bad url", url, "for", name)

def read_pilot():
  groups = ast.literal_eval(open("pilot_groups.dat", encoding="utf-8").read())

  z=zipfile.ZipFile(r"pilot.ods")
  f=z.open("content.xml")
  parser = xml.sax.make_parser()
  t = TableGrouper()
  o = ODSDecoder(t)
  parser.setContentHandler(o)
  parser.parse(f)
  f.close()
  z.close()

  of=open("pilot.dat", "w", encoding="utf-8")
  first = True
  for grouping, cells, hrefs in t.rows:
    if len(cells)<12:
      continue
    if first:
      first = False
      continue

    url=hrefs[0] if hrefs else None
    xid=''.join(cells[0])
    name=''.join(cells[1])
    price=''.join(cells[2])
    pack=''.join(cells[3])
    bulk=''.join(cells[4])
    code=''.join(cells[5])
    barcode=''.join(cells[6])
    descr=''.join(cells[7])
    manuf=''.join(cells[8])
    avail=''.join(cells[9])
    group=''.join(cells[11])
    
    g_info = groups.get(group)
    if g_info is None:
      print("group is unknown", group)
    group = g_info["displayname"] or group
    manuffilter = g_info["manuffilter"]
    export = g_info["export"]
    data = g_info.get("data")

    if manuffilter:
      print(manuf, manuffilter, re.match(manuffilter, manuf))
      if not re.match(manuffilter, manuf):
        print(" - skip", name)
        continue

    net_weight = None
    if data:
      x = data.get(xid)
      if x:
        net_weight=x.get("net")

    if export:
      of.write(repr([xid,name,url,price,pack,bulk,None,code,barcode,descr,manuf,avail,group,net_weight])+"\n")
    else:
      print("skip", name)
  of.close()

# *  *  *  *  *

if True:
  z=zipfile.ZipFile("translations.ods")
  f=z.open("content.xml")
  parser = xml.sax.make_parser()
  t = TableGrouper()
  o = ODSDecoder(t)
  parser.setContentHandler(o)
  parser.parse(f)
  f.close()
  z.close()
  of=open("translations.dat", "w", encoding="utf-8")
  for r in t.rows:
    text = r[1]
    if not text:
      continue
    xid=''.join(text[0])
    name=''.join(text[2])
    vol=''.join(text[3])
    if len(text)>7:
      descr=''.join(text[7])
    else:
      descr=None
    of.write(repr([xid,name,descr,vol])+'\n')
  of.close()
#  exit()


read_spectorg()
read_spectorg_quantities()
read_pilot_groups()
read_pilot()
