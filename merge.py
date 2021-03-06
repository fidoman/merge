#!/usr/bin/python3

import apsw
from tkinter import *
import time
import ast
import os
import re
import autotrans

#INIT = True
INIT = False

if INIT:
  os.unlink("burbeer.sqlite")

conn = apsw.Connection("burbeer.sqlite")
conn.cursor().execute("PRAGMA synchronous=off")


conn.cursor().execute("create table if not exists sources(srcid, srcfile, prefix, picbase)")
conn.cursor().execute("create unique index if not exists srcs_index ON sources (srcid)")
if INIT:
  conn.cursor().execute("insert into sources values (1, 'pilot.dat', '', '')")
  conn.cursor().execute(r"insert into sources values (2, 'spectorg_q.dat', 'S-', 'C:\SPECTORG\')")


SRCDATA_FIELDS=("xid", "name", "img", "price", "pack", "bulk", "year", "code", "barcode", "descr", 
                "manuf", "avail", "grp", "net_weight", "volume", "dimensions")

conn.cursor().execute("create table if not exists src_data(src_exists, ignored, srcid, goodid, " +
          ", ".join(SRCDATA_FIELDS)+")")
conn.cursor().execute("create unique index if not exists src_index ON src_data (srcid, xid)")

conn.cursor().execute("create table if not exists "
   "goods(goodid INTEGER PRIMARY KEY AUTOINCREMENT, name, description, volume, dimensions, manufacturer, year, code, pic)")

# events: 
#   attribute change
#   position addition
#   position removal

# addition
#   try to match with existing good
#   update availability if ok
#   else create new good

# removal
#   if not last update availability
#   if last set availability to zero

# attribute change
#   mark good for review

# OR do not store price and availability, fetch on export from src_data table


root = Tk()

cs = conn.cursor()

print("SOURCES ANALYZIS")
# no database changes during analysis
# changes must be reviewed and then processed

#1 mark all src_data records as unverified
cs.execute("update src_data set src_exists=?", (False,))

#2 walk new sources
#21 mark record as verified if they are present in source
#211 mark matching object for review if data changed
#22 if source record is new start object add/assign to existing procedure

changes = {}
new_recs = {}
deletions = []

sources = list(cs.execute("select * from sources"))
for srcid, srcfile, prefix, imgpath in sources:
  for l in open(srcfile, encoding="utf-8"):
    xid, name, img, price, pack,bulk, year,code,barcode,descr,manuf,avail,group, net_weight, volume, dimensions = \
      ast.literal_eval(l.strip())
    if img is not None:
      img = imgpath + img
    #print(xid, name)
    existing_data = list(cs.execute("select "+",".join(SRCDATA_FIELDS)+" from src_data where srcid=? and xid=?", 
       (srcid, xid)))
    if existing_data:
      #print("src", srcid, "same record", xid)
      cs.execute("update src_data set src_exists=? where srcid=? and xid=?", (True,srcid, xid))
      #..compare
      db_xid, db_name, db_img, db_price, db_pack, db_bulk, db_year, db_code, db_barcode, db_descr,\
        db_manuf, db_avail, db_group, db_net_weight, db_volume, db_dimensions = existing_data[0]
      #.. if manuf or year or code differs - drop relation as its different good (except for None --> value)
      if db_manuf and db_manuf!=manuf or db_year and db_year!=year or db_code and db_code!=code:
        print("record", srcid, xid, "identication changed, dropping")
        # delete relation to good - recreate record
        deletions.append([srcid, xid])
        new_recs[(srcid, xid)]=(name, img, price, pack, bulk, year, code, barcode, descr, manuf, avail, group, net_weight, volume, dimensions)

      elif name!=db_name or img!=db_img or pack!=db_pack or bulk!=db_bulk or barcode!=db_barcode or \
        descr!=db_descr or group!=db_group or net_weight!=db_net_weight or volume!=db_volume or dimensions!=db_dimensions:
        print("record", srcid, xid, "updated")
        print(db_name, db_img, db_pack, db_bulk, db_barcode, db_descr, db_group, db_net_weight, db_volume, db_dimensions)
        print(name, img, pack, bulk, barcode, descr, group, net_weight, volume, dimensions)

        changes[(srcid, xid)]=[
          (db_name, db_img, db_pack, db_bulk, db_barcode, db_descr, db_group, db_net_weight, db_volume, db_dimensions), 
          (name, img, pack, bulk, barcode, descr, group, net_weight, volume, dimensions)]
      else:
#        print("record", srcid, xid, "no changes")
        pass
    else:
      print("src", srcid, "new record", xid)
      new_recs[(srcid, xid)]=(name, img, price, pack,bulk, year,code,barcode,descr,manuf,avail,group,net_weight, volume, dimensions)

  print(srcfile, "done")

deletions = list(cs.execute("select srcid, xid from src_data where src_exists=?", (False,)))

print("new records:", len(new_recs))
print("updated:", len(changes))
print("deleted:", len(deletions))

print("END SOURCES ANALYZIS")

cs.close()
del cs

# --- database operations ---

def export_goods(conn):
  """ will export:
  Код, Наименование, Группа, Штрихкод, Производитель, Характеристика, Артикул, Веснетто, Изображение, 
  Цена, Доступно, Объём"""
  cursor1 = conn.cursor()

  out1 = open("price_CP1251.tsv", "w", encoding="CP1251")
  out2 = open("price_UTF-8.tsv", "w", encoding="UTF-8")

  prefixes = {}
  for srcid, prefix in cursor1.execute("select srcid, prefix from sources"):
    prefixes[srcid] = prefix
    #print(repr(srcid), repr(prefix))

  cursor2 = conn.cursor()
  for goodid, name, description, volume, dimensions, manufacturer, year, code, pic in cursor1.execute("select * from goods"):
    # get price and availability from src_data
    for s, p, a, x, g, b, w, v in cursor2.execute("select srcid, price, avail, xid, grp, barcode, "
            "net_weight, volume from src_data where goodid=? order by srcid", (goodid,)):
      if int(avail)<2:
        continue # go to next source if this do not have supplies
      outstr = "\t".join((prefixes[s]+x, name or '', g or '', b or '', manufacturer or '', 
                          description or '', code or '', w or '', pic or '', p or '', a or '', v or ''))+"\n"
      out1.write(outstr)
      out2.write(outstr)
      break # no more sources necessary

  out1.close()
  out2.close()
  print("Saved")

# ---

# deletions - drop from sources
# new records - match with goods (with code, name, or manual selection)
# updated (and newly matched) - mark for review


# --- INIT ---
# INITIALIZATION
# 1) load first source
# 2) create good for each its record
# 3) update goods with data from translations.ods
# 4) second source process with manual matching
if INIT:
  cs = conn.cursor()

  print("reading translations.dat...")
  trans = {}
  for l in open("translations.dat", encoding="utf-8"):
    xid, name, descr, vol = ast.literal_eval(l.strip())
    trans[xid] = (name, descr, vol)

  m={}
  print("Processing source #1")
  for srcid, xid in list(new_recs.keys()):
    name, img, price, pack,bulk, year,code,barcode,descr,manuf,avail,group,net_weight,volume = new_recs[(srcid, xid)]
    if srcid==1:
      #print("adding xid", xid)
      #..create good, get data from translations
      if xid in trans:
        tr=trans[xid]
        g_name=tr[0] or name
        g_descr=tr[1] or descr
        g_volume=tr[2] or volume
        #print(xid, "is known, adding as good")
        cs.execute("insert into goods values (NULL, ?, ?, ?, ?, ?, ?, ?)", (g_name, g_descr, g_volume, manuf, year, code, img))
        goodid = conn.last_insert_rowid()
        cs.execute("insert into src_data values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
          (True, False, srcid, goodid, xid, name, img, price, pack,bulk,year,code,barcode,descr,manuf,avail,group,net_weight,volume))
        new_recs.pop((srcid, xid))
      else:
        #print(xid, "not in translations, skipping")
        pass

  print("Processing other sources")
  for srcid, xid in list(new_recs.keys()):
    if srcid==1:
      continue # no reason to try again
    name, img, price, pack,bulk, year,code,barcode,descr,manuf,avail,group,net_weight,volume = new_recs[(srcid, xid)]
    #print(srcid, name, manuf, code)
    if code:
        e=list(cs.execute("select * from goods where code=?", (code,)))
        if len(e)==1:
          #m[(manuf, e[0][4])]=m.get((manuf, e[0][4]), 0) + 1
          goodid = e[0][0]
          try:
            print(srcid, name, manuf, "code=%s"%code, "goodid=%d"%goodid)
          except:
            pass
          print("Found unique good with same code")
          # attach to good: set goodid and remove from new_recs
          cs.execute("insert into src_data values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (True, False, srcid, goodid, xid, name, img, price, pack,bulk,year,code,barcode,descr,manuf,avail,group,net_weight,volume))
          new_recs.pop((srcid, xid))
          m.setdefault((manuf, e[0][4]), []).append(code)

  open("m","w", encoding="utf-8").write(repr(m))
  print("new records after INIT:", len(new_recs))

  cs.close()
  del cs
  
# --- END INIT ---

# adding new records to database

cs=conn.cursor()
for srcid, xid in list(new_recs.keys()):
  name, img, price, pack,bulk, year,code,barcode,descr,manuf,avail,group,net_weight,volume = new_recs[(srcid, xid)]
  cs.execute("insert into src_data values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
    (True, False, srcid, None, xid, name, img, price, pack,bulk,year,code,barcode,descr,manuf,avail,group,net_weight,volume))
cs.close()
del cs

del new_recs

#export_goods(conn)
#exit()

#3 set availability in unverified to 0 -- generate on export
#4 review updated objects
#41 reset updated flag after review

# -----------------------
# process deletions - DO NOTHING. Keep it as "no src" as the record may reappear
#for srcid, xid in deletions:
#  print("deleting",srcid,xid)
#  cs.execute("delete from src_data where srcid=? and xid=?", (srcid, xid))
#  # no more actions as unsources good are not exported due to no source with non-zero availability

# new records
#for srcid, xid, name, img, price, pack,bulk, year,code,barcode,descr,manuf,avail,group,net_weight in new_recs:
#  print("new_rec", srcid, xid)
#exit()

# -----------------------


#main window

#list of goods with filter/search
#  + filter for updated
#for selected good the following is shown:
#  pic
#  attributes
#  source data
#  old source data (for updated)

#  delete good button
#  remove source button for each assigned source

#tabs for all sources:
#  list of unassigned records
#  button "assign" to assign to currently selected good if has not already assigned record from this source


fgoods = LabelFrame(root, text="Товары")
fgoods.grid(row=0, column=0)

goodslist = Frame(fgoods)
goodslist.grid(row=0, column=0)

goodfilter = Entry(goodslist)
goodfilter.grid(row=0, sticky=N)

gfapply = Button(goodslist, text="Фильтр")
gfapply.grid(row=1)

gfchanged = Button(goodslist, text="Изменённые")
gfchanged.grid(row=2)

goods = Listbox(goodslist, exportselection=0)
goods.grid(row=3, sticky=S+N)

def update_goods(conn, goods, goods_filter):
  goods.delete(0, END)
  goods.oldselection = None
  gf = re.compile(goods_filter, re.I)
  for gi, gn, gd, gm, gc in conn.cursor().execute("select goodid, name, description, manufacturer, code from goods"):
    if gf.search(gn) or gf.search(gd) or gf.search(gm) or gf.search(gc):
      goods.insert(END, "%d %s"%(gi,gn))

update_goods(conn, goods, '')

def set_goods_filter(coon, goods, goodfilter):
  update_goods(conn, goods, goodfilter.get())

gfapply.config(command=lambda: set_goods_filter(conn, goods, goodfilter))

def update_goods_only_changes(conn, goods):
  goods.delete(0, END)
  goods.oldselection = None
  cs1=conn.cursor()
  cs2=conn.cursor()
  for srcid, xid in changes.keys():
    gi=list(cs1.execute("select goodid from src_data where srcid=? and xid=?", (srcid, xid)))
    if gi[0][0] is not None:
      gi=gi[0][0]
      gn = list(cs2.execute("select name from goods where goodid=?", (gi,)))[0][0]
      goods.insert(END, "%d %s"%(gi,gn))

gfchanged.config(command = lambda: update_goods_only_changes(conn, goods))

def update_goods_for_code(conn, goods, code):
  """ filter goods with similar code (same beginning """
  goods.delete(0, END)
  goods.oldselection = None
  code=code.upper()
  for gi, gn, gd, gm, gc in conn.cursor().execute("select goodid, name, description, manufacturer, code from goods"):
    gc=gc.upper()
    if gc and code and (code.startswith(gc) or gc.startswith(code)):
      goods.insert(END, "%d %s"%(gi,gn))


delgood = Button(goodslist, text="удалить товар")
delgood.grid(row=4)
# set goodid to none in src_recs
# delete from goods
# //add to new_recs
# refresh source listboxes


def delete_good(conn, goods, src_info):
  cs=conn.cursor()
  sel = goods.curselection()
  if not sel: 
    return
  goodid = int(goods.get(sel[0]).split(" ", 2)[0])
  print("del good", goodid)

#  save_recs = list(cs.execute("select srcid, xid, name, img, price, pack, bulk, year, code, barcode, descr, manuf, avail, "
#      "grp, net_weight,volume from src_data where goodid=?", (goodid,)))

  cs.execute("update src_data set goodid=NULL where goodid=?", (goodid,))
  cs.execute("delete from goods where goodid=?", (goodid,))
  goods.delete(sel[0])
  goods.oldselection = None

#  for r in save_recs:
#    new_recs[(r[0], r[1])]=tuple(r[2:])

  src_info[0] = True


exportgoods = Button(goodslist, text="Выгрузить")
exportgoods.grid(row=5)
exportgoods.config(command=lambda: export_goods(conn))


goodinfo = Frame(fgoods)
goodinfo.grid(row=0, column=1)

pic = Canvas(goodinfo, width=128, height=128)
pic.grid(row=0, column=2, rowspan=8)

name = Entry(goodinfo, width=40)
name.grid(row=0, column=0, columnspan=2)

descr = Entry(goodinfo, width=40)
descr.grid(row=1, column=0, columnspan=2)

volume = Entry(goodinfo, width=40)
volume.grid(row=2, column=0, columnspan=2)

manuf = Entry(goodinfo, width=40)
manuf.grid(row=3, column=0, columnspan=2)

year = Entry(goodinfo, width=40)
year.grid(row=4, column=0, columnspan=2)

code = Entry(goodinfo, width=40)
code.grid(row=5, column=0, columnspan=2)

update_good = Button(goodinfo, text="Обновить поля")
update_good.grid(row=6, column=0, columnspan=2)

# list of connected sources
goodsources = Listbox(goodinfo, exportselection=0)
goodsources.grid(row=7, column=0)

# source data in text form, available for copying
# if source if changed, modification is shown here as 
# NEW: and OLD: separate lines
goodsourcedata = Text(goodinfo, width=30, height=10)
goodsourcedata.grid(row=7, column=1)

goodinfofields = [name, descr, volume, manuf, year, code, pic, goodsources, goodsourcedata]

def refresher(conn, goods, i):
  "refresh selected good's info"

  sel=goods.curselection()
  if sel!=goods.oldselection:
    i[0].delete(0, END)
    i[1].delete(0, END)
    i[2].delete(0, END)
    i[3].delete(0, END)
    i[4].delete(0, END)
    i[5].delete(0, END)
    i[7].delete(0, END)
    i[7].oldsel=i[7].curselection()
    i[8].delete("0.0", END)

    if sel:
      cs = conn.cursor()
      goodid=int(goods.get(sel[0]).split(' ',1)[0])
      print("selected good", goodid)
      gname, gdescription, gvolume, gmanufacturer, gyear, gcode, gpic = \
        list(cs.execute("select name, description, volume, manufacturer, year, code, pic from goods where goodid=?", (goodid,)))[0]
      i[0].insert(0, gname or '')
      i[1].insert(0, gdescription or '')
      i[2].insert(0, gvolume or '')
      i[3].insert(0, gmanufacturer or '')
      i[4].insert(0, gyear or '')
      i[5].insert(0, gcode or '')
      i[6].create_text((64,64), text='figa.jpg')
      print("selected goodid=", repr(goodid))
      gsrcs=list(cs.execute("select srcid, xid "
        #"src_exists, srcid, goodid, xid, name, "
        #"img, price, pack, bulk, year, code, barcode, descr, manuf, avail, grp, net_weight, volume"
        " from src_data where goodid=?",
        (goodid,)))
      for gsrcid, gxid in gsrcs:
        gsrcname=list(cs.execute("select srcfile from sources where srcid=?", (gsrcid,)))[0][0]
        i[7].insert(END, "%d %s %s"%(gsrcid, gxid, gsrcname))

      i[7].oldsel=i[7].curselection() # essentially no selection

    goods.oldselection=sel


  # check selection in sources listbox
  if sel and i[7].curselection()!=i[7].oldsel:
      i[8].delete("0.0", END) # cleanup textbox
      "if good is selected, check for reselected source"
      print(i[7].curselection(), i[7].oldsel)
      goodid=int(goods.get(sel[0]).split(' ',1)[0])
      src_selection = i[7].curselection()
      if src_selection:
        src_selected = i[7].get(src_selection[0])
        sel_srcid = int(src_selected.split(' ', 2)[0])
        sel_xid = src_selected.split(' ', 2)[1]
        sel_srcrec=list(conn.cursor().execute("select " + ",".join(SRCDATA_FIELDS) +
           " from src_data where srcid=? and xid=?", (sel_srcid, sel_xid)))[0]
        i[8].insert(END, "%s goodid: %d\n"%(src_selected, goodid))
        sel_changes = changes.get((sel_srcid, sel_xid))
        if sel_changes:
          #i[8].insert(END, "changes: "+repr(changes)) ### MAKE READABLE
          for c_src, c_val in changes.items():
            for c_i in range(len(c_val[0])): # len should be same with c_val[1]
              if c_val[0][c_i] != c_val[1][c_i]:
                i[8].insert(END, "OLD: %s\n"%c_val[0][c_i])
                i[8].insert(END, "NEW: %s\n"%c_val[1][c_i])
        else:
          i[8].insert(END, "no changes\n")
        for item_name, sel_srcrec_item in zip(SRCDATA_FIELDS, sel_srcrec):
          if sel_srcrec_item:
            i[8].insert(END, "%s: %s\n"%(item_name, sel_srcrec_item))
      else:
        i[8].delete("0.0", END)
      i[7].oldsel=i[7].curselection()

  goods.after(200, lambda: refresher(conn, goods, i))

def good_updater(conn, goods, i):
  sel=goods.curselection()
  if sel:
    cs = conn.cursor()
    cs2 = conn.cursor()
    goodid=int(goods.get(sel[0]).split(' ',1)[0])
    cs.execute("update goods set name=?, description=?, volume=?, manufacturer=?, year=?, code=? "
      "where goodid=?", (i[0].get(), i[1].get(), i[2].get(), i[3].get(), i[4].get(), i[5].get(), goodid))
    # update src_data if changes exist and delete change
    for srcid, xid in cs.execute("select srcid, xid from src_data where goodid=?", (goodid,)):
      print("updating src_data for %d %s"%(srcid, xid))
      if (srcid, xid) in changes:
        # name, img, pack, bulk, barcode, descr, group, net_weight, volume
        cs2.execute("update src_data set name=?, img=?, pack=?, bulk=?, barcode=?, descr=?, grp=?, "
          "net_weight=?, volume=? where srcid=? and xid=?", changes[(srcid, xid)][1]+(srcid, xid))
        changes.pop((srcid, xid))
    print(goodid, "updated")

update_good.config(command=lambda: good_updater(conn, goods, goodinfofields))


goods.oldselection=None
goods.after(1000, lambda: refresher(conn, goods, goodinfofields))


unbindsrc = Button(goodinfo, text="отвязать выбранный источник")
unbindsrc.grid(row=8, column=0, columnspan=2)

def unbind_source(conn, goods, goodsources, src_info):
  sel_good = goods.curselection()
  if not sel_good:
    print("good is not selected")
    return
  sel_src = goodsources.curselection()
  if not sel_src:
    print("source is not selected")
    return
  goodid = int(goods.get(sel_good[0]).split(" ", 2)[0])
  srcid = int(goodsources.get(sel_src[0]).split(" ", 2)[0])
  xid = goodsources.get(sel_src[0]).split(" ", 2)[1]
  conn.cursor().execute("update src_data set goodid=NULL where srcid=? and xid=?", (srcid, xid))
  goods.oldselection = None
  src_info[0] = True



# --- sources

fsuppliers = LabelFrame(root, text="Прайслисты")
fsuppliers.grid(row=0, column=1)

sources = Listbox(fsuppliers, height=3, exportselection=0)
sources.pack()

srcrecs = Listbox(fsuppliers, exportselection=0)
srcrecs.pack()

srcrec_text = Text(fsuppliers, width=30, height=10)
srcrec_text.pack()

def update_sources_list(conn, sources):
  sources.delete(0, END)
  for srcid, srcfile in conn.cursor().execute("select srcid, srcfile from sources"):
    sources.insert(END, "%d %s"%(srcid, srcfile))


def update_srcrecs_list(conn, sources, srcrecs):
  # list of unassigned source records
  srcrecs.delete(0, END)
  srcrecs.oldselection = None
  if sources.curselection():
    sel = sources.get(sources.curselection()[0])
    sel_srcid = int(sel.split(" ",2)[0])
#    for srcid, xid in new_recs.keys():
    for srcid, xid, name in conn.cursor().execute("select srcid, xid, name from src_data where goodid is NULL"):
      if srcid == sel_srcid:
        #name = new_recs[(srcid, xid)][0]
        srcrecs.insert(END, xid+" "+name)

def update_srcrec_text(conn, sources, srcrecs, record):
  record.delete("0.0", END)
  if sources.curselection():
    sel = sources.get(sources.curselection()[0])
    sel_srcid = int(sel.split(" ",2)[0])
  else:
    return
  if srcrecs.curselection():
    sel = srcrecs.get(srcrecs.curselection()[0])
    sel_xid = sel.split(" ",2)[0]
  else:
    return
  #record.insert(END, "%d %s\n"%(sel_srcid, sel_xid))
  rec = list(conn.cursor().execute("select "+",".join(SRCDATA_FIELDS)+" from src_data where srcid=? and xid=?",
       (sel_srcid, sel_xid)))[0]
  for n, v in zip(SRCDATA_FIELDS, rec):
    record.insert(END, "%s: %s\n"%(n, v))

src_info = [False, sources, srcrecs, srcrec_text]
# first field is 'force refresh'

# must be here as it must trigger refresh of sources
delgood.config(command = lambda: delete_good(conn, goods, src_info))
unbindsrc.config(command = lambda: unbind_source(conn, goods, goodsources, src_info))

# обновление данных о товаре при изменении selection
# обновление виджетов при изменении списка новых (непривязанных) позиций

def src_refresher(conn, src_info):
  sources = src_info[1]
  force_update = src_info[0]
#  if force_update:
#    print("refreshing sources")
#    update_sources_list(conn, sources)
#    src_info[0] = False
  #
  srcrecs = src_info[2]
  record = src_info[3]
  if sources.curselection() != sources.oldselection or force_update:
    src_info[0] = False
    print("refresh source recs")
    update_srcrecs_list(conn, sources, srcrecs)
    sources.oldselection=sources.curselection()
  if srcrecs.curselection() != srcrecs.oldselection:
    print("refresh record")
    update_srcrec_text(conn, sources, srcrecs, record)
    srcrecs.oldselection = srcrecs.curselection()
  sources.after(201, lambda: src_refresher(conn, src_info))

update_sources_list(conn, sources)
sources.oldselection = None
sources.after(1000, lambda: src_refresher(conn, src_info))

searchgood = Button(fsuppliers, text="найти подходящие товары")
searchgood.pack()

def search_goods_for_code(conn, goods, src_info):
  sources = src_info[1]
  srcrecs = src_info[2]

  if sources.curselection():
    sel = sources.get(sources.curselection()[0])
    sel_srcid = int(sel.split(" ",2)[0])
  else:
    print("source not selected")
    return
  if srcrecs.curselection():
    sel = srcrecs.get(srcrecs.curselection()[0])
    sel_xid = sel.split(" ",2)[0]
  else:
    print("record not selected")
    return

  code=list(conn.cursor().execute("select code from src_data where srcid=? and xid=?", (sel_srcid, sel_xid)))[0][0]
  print("filtering for code", code)
  update_goods_for_code(conn, goods, code)

searchgood.config(command = lambda: search_goods_for_code(conn, goods, src_info))

assignrec = Button(fsuppliers, text="привязать к выбранному товару")
assignrec.pack()

def bind_source(conn, goods, src_info):
  sel_good = goods.curselection()
  if not sel_good:
    print("good is not selected")
    return
  goodid = int(goods.get(sel_good[0]).split(" ", 2)[0])

  sources = src_info[1]
  srcrecs = src_info[2]
  if sources.curselection():
    sel = sources.get(sources.curselection()[0])
    sel_srcid = int(sel.split(" ",2)[0])
  else:
    print("source is not selected")
    return
  if srcrecs.curselection():
    sel = srcrecs.get(srcrecs.curselection()[0])
    sel_xid = sel.split(" ",2)[0]
  else:
    print("record is not selected")
    return

  conn.cursor().execute("update src_data set goodid=? where srcid=? and xid=?", (goodid, sel_srcid, sel_xid))
  goods.oldselection = None
  src_info[0] = True

assignrec.config(command = lambda: bind_source(conn, goods, src_info))

newgood = Button(fsuppliers, text="добавить как новый товар")
newgood.pack()

#SRCDATA_FIELDS=("xid", "name", "img", "price", "pack", "bulk", "year", "code", "barcode", "descr", 
#                "manuf", "avail", "grp", "net_weight", "volume")


def to_new_good(conn, goods, src_info):
  cs=conn.cursor()

  # get info from selected source
  sources = src_info[1]
  srcrecs = src_info[2]
  if sources.curselection():
    sel = sources.get(sources.curselection()[0])
    sel_srcid = int(sel.split(" ",2)[0])
  else:
    print("source is not selected")
    return
  if srcrecs.curselection():
    sel = srcrecs.get(srcrecs.curselection()[0])
    sel_xid = sel.split(" ",2)[0]
  else:
    print("record is not selected")
    return

  rec = list(conn.cursor().execute("select "+",".join(SRCDATA_FIELDS)+" from src_data where srcid=? and xid=?",
       (sel_srcid, sel_xid)))[0]

  name = rec[1]
  code = rec[7]
  group = rec[12]
  print(name)
  # pass autotrans
  auto = autotrans.autotrans(name, code, group)
  name = auto[0]
  volume = auto[1] or rec[14]
  descr = rec[9]
  manuf = rec[10]
  year = rec[6]
  img = rec[2]

  # add to list of goods
  cs.execute("insert into goods values (NULL, ?, ?, ?, ?, ?, ?, ?)", (name, descr, volume, manuf, year, code, img))
  # as sqlite does not have 'returning goodid', try to re-find added good
  
  checks=[]
  q=[]
  if manuf is not None:
    checks.append(manuf)
    q.append("manufacturer=?")
  else:
    q.append("manufacturer is NULL")

  checks.append(name)
  q.append("name=?")

  if year is not None:
    checks.append(year)
    q.append("year=?")
  else:
    q.append("year is NULL")

  if code is not None:
    checks.append(code)
    q.append("code=?")
  else:
    q.append("code is NULL")

  added_good = list(cs.execute("select goodid from goods where "+" and ".join(q), tuple(checks)))
  if len(added_good)!=1:
    print("added good is lost! (matching records count=%d)"%len(added_good))
    return
  goodid = added_good[0][0]
  goods.insert(END, "%d %s"%(goodid, name))
  goods.oldselection = None
  goods.selection_set(END)
  goods.see(END)

  # bind
  cs.execute("update src_data set goodid=? where srcid=? and xid=?", (goodid, sel_srcid, sel_xid))
  src_info[0] = True
  # select new good for instant editing

newgood.config(command = lambda: to_new_good(conn, goods, src_info))

#w = Label(root, text="preparing...")
#w.pack()
root.mainloop()

# 'attribute changed' window
# Good - frame. attributes, pic
# sources - table. chnaged attribute will be marked red
# buttons:
# Accept
#   edits of good are saved
#   source data is updated
# Later
#   edits of good are saved
#   source data is NOT updates
# Quit
#   quit immediately

# 'new source' window
# merge with existing good
# data from source is shown
# list of goods.
# 1) filtered. only matching with source data
# 2) full list. search, filter
# preview selected good
# buttons:
#  merge - merge with selected good
#  new - new good (goto 'new good' window)


# 'new good' window
# is the same
# good data is prefilled by auto-generated data from source

conn.close(True)
