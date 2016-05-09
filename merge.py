#!/usr/bin/python3 

import apsw
from tkinter import *
import time
import ast
import os

INIT=True

if INIT:
  os.unlink("burbeer.sqlite")

conn = apsw.Connection("burbeer.sqlite")
conn.cursor().execute("PRAGMA synchronous=off")


conn.cursor().execute("create table if not exists sources(srcid, srcfile, prefix)")
conn.cursor().execute("create unique index if not exists srcs_index ON sources (srcid)")
if INIT:
  conn.cursor().execute("insert into sources values (1, 'pilot.dat', '')")
  conn.cursor().execute("insert into sources values (2, 'spectorg_q.dat', 'S-')")


SRCDATA_FIELDS=("xid", "name", "img", "price", "pack", "bulk", "year", "code", "barcode", "descr", 
                "manuf", "avail", "grp", "net_weight", "volume")

conn.cursor().execute("create table if not exists src_data(src_exists, srcid, goodid, " +
          ", ".join(SRCDATA_FIELDS)+")")
conn.cursor().execute("create unique index if not exists src_index ON src_data (srcid, xid)")

conn.cursor().execute("create table if not exists goods(goodid INTEGER PRIMARY KEY AUTOINCREMENT, name, description, volume, manufacturer, year, code, pic)")

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

def new_srcrec(conn, gui, src_record):
  "returns goodid if assignment succeful"
  1/0

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
for srcid, srcfile, prefix in sources:
  for l in open(srcfile):
    xid, name, img, price, pack,bulk, year,code,barcode,descr,manuf,avail,group,net_weight = \
      ast.literal_eval(l.strip())
    volume=None # currently no source contains this field
    #print(xid, name)
    existing_data = list(cs.execute("select * from src_data where srcid=? and xid=?", (srcid, xid)))
    if existing_data:
      #print("src", srcid, "same record", xid)
      cs.execute("update src_data set src_exists=? where srcid=? and xid=?", (True,srcid, xid))
      #..compare
      db_name, db_img, db_price, db_pack, db_bulk, db_year, db_code, db_barcode, db_descr,\
        db_manuf, db_avail, db_group, db_net_weight, db_volume = \
        list(cs.execute("select name, img, price, pack,bulk, year,code,barcode,descr,manuf,avail,grp,net_weight,volume "
        "from src_data where srcid=? and xid=?", (srcid, xid)))[0]
      #.. if manuf or year or code differs - drop relation as its different good (except for None --> value)
      if db_manuf and db_manuf!=manuf or db_year and db_year!=year or db_code and db_code!=code:
        print("record", srcid, xid, "identication changed, dropping")
        # delete relation to good - recreate record
        deletions.append([srcid, xid])
        new_recs[(srcid, xid)]=(name, img, price, pack,bulk, year,code,barcode,descr,manuf,avail,group,net_weight,volume)

      elif name!=db_name or img!=db_img or pack!=db_pack or bulk!=db_bulk or barcode!=db_barcode or \
        descr!=db_descr or group!=db_group or net_weight!=db_net_weight or volume!=db_volume:
        print("record", srcid, xid, "updated")
        print(db_name, db_img, db_pack, db_bulk, db_barcode, db_descr, db_group, db_net_weight, db_volume)
        print(name, img, pack, bulk, barcode, descr, group, net_weight, volume)

        changes[(srcid, xid)]=[
          (db_name, db_img, db_pack, db_bulk, db_barcode, db_descr, db_group, db_net_weight, db_volume), 
          (name, img, pack, bulk, barcode, descr, group, net_weight, volume)]
      else:
#        print("record", srcid, xid, "no changes")
        pass
    else:
      print("src", srcid, "new record", xid)
      new_recs[(srcid, xid)]=(name, img, price, pack,bulk, year,code,barcode,descr,manuf,avail,group,net_weight,volume)

  print(srcfile, "done")

deletions = list(cs.execute("select srcid, xid from src_data where src_exists=?", (False,)))

print("new records:", len(new_recs))
print("updated:", len(changes))
print("deleted:", len(deletions))

print("END SOURCES ANALYZIS")

# --- database operations ---

def get_srcdata(conn, srcid, goodid):
    l=list(conn.cursor().execute("select xid, name, img, price, pack, bulk, year, code, barcode, descr, manuf, "
    "avail, grp, net_weight, volume from src_data where srcid=? and goodid=?", (srcid, goodid)))
    if len(l)==0:
      raise Exception("No src_data for %s in source %s"%(repr(goodid), repr(srcid)))
    if len(l)>1:
      raise Exception("Multiple src_data for %s in source %s"%(repr(goodid), repr(srcid)))
    return l[0]

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
  for goodid, name, description, volume, manufacturer, year, code, pic in cursor1.execute("select * from goods"):
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
  print("reading translations.dat...")
  trans = {}
  for l in open("translations.dat"):
    xid, name, descr, vol = ast.literal_eval(l.strip())
    trans[xid] = (name, descr, vol)

  m={}
  for srcid, xid in new_recs.keys():
    name, img, price, pack,bulk, year,code,barcode,descr,manuf,avail,group,net_weight,volume = new_recs[(srcid, xid)]
    if srcid==1:
      #print("adding xid", xid)
      #..create good, get data from translations
      if xid in trans:
        tr=trans[xid]
        g_name=tr[0] or name
        g_descr=tr[1] or descr
        g_volume=tr[2] or volume
        print(xid, "is known, adding as good")
        cs.execute("insert into goods values (NULL, ?, ?, ?, ?, ?, ?, ?)", (g_name, g_descr, g_volume, manuf, year, code, img))
        goodid = conn.last_insert_rowid()
        cs.execute("insert into src_data values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
          (True, srcid, goodid, xid, name, img, price, pack,bulk,year,code,barcode,descr,manuf,avail,group,net_weight,volume))
        new_recs.pop([srcid, xid])
      else:
        print(xid, "not in translations, skipping")

    else:
      print(srcid, name, manuf, code)
      if code:
        e=list(cs.execute("select * from goods where code=?", (code,)))
        if e:
          #m[(manuf, e[0][4])]=m.get((manuf, e[0][4]), 0) + 1
          m.setdefault((manuf, e[0][4]), []).append(code)

  open("m","w").write(repr(m))
# --- END INIT ---

#print(get_srcdata(conn, 1,10))
#export_goods(conn)
#exit()



#3 set availability in unverified to 0 -- generate on export
#4 review updated objects
#41 reset updated flag after review

# -----------------------
# process deletions
for srcid, xid in deletions:
  print("deleting",srcid,xid)
  cs.execute("delete from src_data where srcid=? and xid=?", (srcid, xid))
  # no more actions as unsources good are not exported due to no source with non-zero availability

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

for gi, gn in cs.execute("select goodid, name from goods"):
  goods.insert(END, "%d %s"%(gi,gn))

delgood = Button(goodslist, text="удалить товар")
delgood.grid(row=4)

exportgoods = Button(goodslist, text="Выгрузить")
exportgoods.grid(row=5)
exportgoods.config(command=lambda: export_goods(conn))


goodinfo = Frame(fgoods)
goodinfo.grid(row=0, column=1)

pic = Canvas(goodinfo, width=256, height=256)
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

def refresher(goods, i):
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
      goodid=int(goods.get(sel[0]).split(' ',1)[0])
      print("goodid=",goodid)
      gname, gdescription, gvolume, gmanufacturer, gyear, gcode, gpic = \
        list(cs.execute("select name, description, volume, manufacturer, year, code, pic from goods where goodid=?", (goodid,)))[0]
      i[0].insert(0, gname or '')
      i[1].insert(0, gdescription or '')
      i[2].insert(0, gvolume or '')
      i[3].insert(0, gmanufacturer or '')
      i[4].insert(0, gyear or '')
      i[5].insert(0, gcode or '')
      i[6].create_text((128,128), text='figa.jpg')
      print("selected goodid=", repr(goodid))
      gsrcs=list(cs.execute("select srcid, xid "
        #"src_exists, srcid, goodid, xid, name, "
        #"img, price, pack, bulk, year, code, barcode, descr, manuf, avail, grp, net_weight, volume"
        " from src_data where goodid=?",
        (int(goodid),)))
      for gsrcid, gxid in gsrcs:
        gsrcname=list(cs.execute("select srcfile from sources where srcid=?", (int(gsrcid),)))[0][0]
        i[7].insert(END, "source %s %s"%(gsrcid, gsrcname))

      i[7].oldsel=i[7].curselection() # essentially no selection

    goods.oldselection=sel


  # check selection in sources listbox
  if sel and i[7].curselection()!=i[7].oldsel:
      "if good is selected, check for reselected source"
      print(i[7].curselection(), i[7].oldsel)
      goodid=int(goods.get(sel[0]).split(' ',1)[0])
      src_selection = i[7].curselection()
      if src_selection:
        src_selected = i[7].get(src_selection[0])
        sel_srcid=int(src_selected.split(' ',2)[1])
        sel_srcrec=get_srcdata(conn,sel_srcid,goodid)
        sel_xid=sel_srcrec[0]
        i[8].insert(END, "%s goodid: %d\n"%(src_selected, goodid))
        sel_changes = changes.get((sel_srcid, sel_xid))
        if sel_changes:
          i[8].insert(END, "changes: "+repr(changes)) ### MAKE READABLE
        else:
          i[8].insert(END, "no changes\n")
        for item_name, sel_srcrec_item in zip(SRCDATA_FIELDS, sel_srcrec):
          if sel_srcrec_item:
            i[8].insert(END, "%s: %s\n"%(item_name, sel_srcrec_item))
      else:
        i[8].delete("0.0", END)
      i[7].oldsel=i[7].curselection()
    
  goods.after(200, lambda: refresher(goods, i))

def good_updater(goods, i):
  sel=goods.curselection()
  if sel:
    goodid=int(goods.get(sel[0]).split(' ',1)[0])
    cs.execute("update goods set name=?, description=?, volume=?, manufacturer=?, year=?, code=? "
      "where goodid=?", (i[0].get(), i[1].get(), i[2].get(), i[3].get(), i[4].get(), i[5].get(), goodid))
    print(goodid, "updated")

update_good.config(command=lambda: good_updater(goods, goodinfofields))


goods.oldselection=None
goods.after(1000, lambda: refresher(goods, goodinfofields))


unbindsrc = Button(goodinfo, text="отвязать выбранный источник")
unbindsrc.grid(row=8, column=0, columnspan=2)

# --- sources

fsuppliers = LabelFrame(root, text="Прайслисты")
fsuppliers.grid(row=0, column=1)

sources = Listbox(fsuppliers, height=3)
sources.pack()

srcrecs = Listbox(fsuppliers)
srcrecs.pack()

searchgood = Button(fsuppliers, text="найти подходящие товары")
searchgood.pack()

assignrec = Button(fsuppliers, text="привязать к выбранному товару")
assignrec.pack()

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
