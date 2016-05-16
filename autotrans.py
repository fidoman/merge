# -*- coding: utf-8 -*-

import re
re_NAMEDIV = re.compile("(\\.|\\s|\\+)\\s*(?!-)")

FIXNAME = {
"Сков.": "Сковорода",
"Сков-лавашница": "Сковорода-лавашница",
"Кастр.": "Кастрюля",
"Ем-сть": "Ёмкость",
"Емкость": "Ёмкость",
"Хлеб-ца": "Хлебница",
"Горш": "Горшок",
"Держ-ль": "Держатель",
'Жаров': 'Жаровня',
'Кaзaн': 'Казан', 
'Кaзан': 'Казан',
'Кaрниз': 'Карниз', 
'Каpниз': 'Карниз',
'Кастр': 'Кастрюля',
'Кастр-ковш': 'Кастрюля-ковш',
'Кастр.-ковш': 'Кастрюля-ковш',
'Кастр.-жаровня': 'Кастрюля-жаровня',
'Компл': 'Комплект',
'Конт-р': 'Контейнер',
'Сков': 'Сковорода', 
'Сков.-гриль': 'Сковорода-гриль',
'Сковорода -жаровня': 'Сковорода-жаровня',
'Сков.-сотейник': 'Сковорода-сотейник',
'Манг': 'Мангал',
'Манты/казан': 'Манты-казан',
'Маш': 'Машинка',
'Н-р': 'Набор', 
'Набоp': 'Набор',
'Подстав': 'Подставка',
'Суш-ка': 'Сушилка',
'Тарелкa': 'Тарелка',
'Теркa': 'Тёрка',
'Терка': 'Тёрка',
}

word_f={"Аптечка", "Банка" , "Блинница", "Бульонница", "Бумага", "Бутылка",
"Ваза", "Ванна", "Ванночка", "Варенечница", "Вареничница", "Вешалка", "Вилка", "Воронка", "Вставка", 
"Гастроемкость", "Губка", "Гусятница", 
"Доска", 
"Ёмкость", 
"Жаровня", "Запаска",
"Канистра", "Картофелемялка", "Кастрюля", "Кисточка", "Кнопка", "Кокотница", 
"Коптильня", "Корзина", "Кофеварка", "Кружка", 
"Крынка", "Крышка", 
"Лейка", "Ложка", "Лопата", "Лопатка", "Лопаточка", 
"Мантоварка", "Масленка", "Машинка", "Метелка", "Метла", "Миниформа", "Миска", "Молоковарка", "Мыльница", "Мусорка", "Мясорубка", 
"Накладка", "Насадка", "Ножеточка",
"Овощеварка", "Овощекашеварка", "Овощерезка", "Овощечистка", 
"Пара чайная", "Пароварка", "Пельменница", "Пепельница", "Пленка", "Подставка", "Полка", "Прихватка", "Пробка",
"Рукоятка",
"Салфетка", "Сетка", "Скалка", "Сковорода", "Скороварка", "Соковарка", 
"Соковыжималка",
"Супница", "Сушилка", 
"Тарелка", "Тёрка", "Термокружка", "Толкушка", "Тортница", "Тренога", "Трубка", "Турка",
"Утятница",
"Фляга", "Фляжка", "Фольга", "Форма", "Хлебница", "Цедилка",
"Чаша", "Швабра", "Шумовка", 
"Шинковка",
"Щетка", "Этажерка"}

word_m={"Котёл", "Котел", "Бидон", "Дуршлаг", "Поддон", "Противень", "Совок", "Ковш", "Таз", "Казан", "Манты-казан", "Набор", "Лоток", "Чайник", "Горшок",
    "Набор", "Контейнер", "Бак", "Сотейник", 
    "Салатник", "Котелок", "Рукомойник", "Грохот", "Термос", "Шампур", "Нож", "Пресс", "Черпак", "Молоток", "Штопор", "Поднос", "Кофейник", "Держатель", "Минипарник", "Судок",
    "Ящик",
"Баранчик",
"Брусок",
"Брызгогаситель",
"Бутылкооткрыватель",
"Венчик",
"Винт",
"Вок",
"Джиггер",
"Ёршик",
"Кант",
"Карниз",
"Ключ",
"Коврик",
"Комод",
"Комплект",
"Консервовскрыватель",
"Консервооткрыватель",
"Кувшин",
"Ланч-бокс",
"Мангал",
"Манты-казан",
"Мешок",
"Опрыскиватель",
"Отлив",
"Подойник",
"Подстаканник",
"Прибор",
"Рукав",
"Стакан",
"Стык",
"Топор",
"Угол",
"Уголок",
"Умывальник",
"Учаг",
"Фонарь"
}

word_x={"Ведро","Сито", "Блюдо", "Ситечко", "Ограждение", "Приспособление", "Кольцо", "Корыто", "Сиденье"}

word_a={"Пакетики", "Пакеты", "Перчатки", "Прищепки", "Щипцы", "Ножницы"}

def gender(s):
  if s in word_f:
    return "f"
  if s in word_m:
    return "m"
  if s in word_x:
    return "x"
  if s in word_a:
    return "a"
  s=s.split("-")[0]
  if s in word_f:
    return "f"
  if s in word_m:
    return "m"
  if s in word_x:
    return "x"
  if s in word_a:
    return "a"
  s=s.split("/")[0]
  if s in word_f:
    return "f"
  if s in word_m:
    return "m"
  if s in word_x:
    return "x"
  if s in word_a:
    return "a"
  return "?"

by_gender = {
  ("алюминиевая", "f"): "алюминиевая",
  ("алюминиевая", "m"): "алюминиевый",
  ("алюминиевая", "x"): "алюминиевое",

  ("эмалированная", "f"): "эмалированная",
  ("эмалированная", "m"): "эмалированный",
  ("эмалированная", "x"): "эмалированное",

  ("фарфоровая", "f"): "фарфоровая",
  ("фарфоровая", "m"): "фарфоровый",
  ("фарфоровая", "x"): "фарфоровое",

  ("керамическая", "f"): "керамическая",
  ("керамическая", "m"): "керамический",
  ("керамическая", "x"): "керамическое",

  ("чугунная", "f"): "чугунная",
  ("чугунная", "m"): "чугунный",
  ("чугунная", "x"): "чугунное",

  ("нержавеющая", "f"): "нержавеющая",
  ("нержавеющая", "m"): "нержавеющий",
  ("нержавеющая", "x"): "нержавеющее",
  ("нержавеющая", "a"): "нержавеющие",

  ("деревянная", "f"): "деревянная",
  ("деревянная", "m"): "деревянный",
  ("деревянная", "x"): "деревянное",

  ("стеклянная", "f"): "стеклянная",
  ("стеклянная", "m"): "стеклянный",
  ("стеклянная", "x"): "стеклянное",

  ("пластмассовая", "f"): "пластмассовая",
  ("пластмассовая", "m"): "пластмассовый",
  ("пластмассовая", "x"): "пластмассовое",
  ("пластмассовая", "a"): "пластмассовые",

  ("антипригарная", "f"): "антипригарная",
  ("антипригарная", "m"): "антипригарный",
  ("антипригарная", "x"): "антипригарное",

  ("медная", "f"): "медная",
  ("медная", "m"): "медный",
  ("медная", "x"): "медное",
  ("медная", "a"): "медные",

}



def is_material(s):
  if s=="ал" or s=="aл" or s=="алюм" or s=="aлюм" or s=="алюмин":
    return "алюминиевая", 1

  if s=="медн":
    return "медная", None

  if s=="эм" or s=="эмал":
    return "эмалированная", 3

  if s=="фар" or s=="фарф" or s=="фарфор":
    return  "фарфоровая", None

  if s=="кер" or s=="керам":
    return "керамическая", 7

  if s=="чуг" or s=="чугун":
    return "чугунная", 10

  if s=="нерж":
    return "нержавеющая", 4

  if s=="дер":
    return "деревянная", None

  if s=="ст" or s=="стек" or s=="стекл":
    return "стеклянная", 6

  if s=="пл" or s=="плас" or s=="пласт":
    return "пластмассовая", 8

  if s=="а/пр":
    return "антипригарная", 2

  return None, None

xtrans = {
  "тефл": "тефлон",
  "д/запек": "для запекания",
  "бор": "с бортиком",
  "борт": "с бортиком",
  "с/р": "с рисунком",
  "б/кр": "без крышки",
  "с/кр": "с крышкой",
  "б/с": "белый-синий",
  "о/с": "оранжевый-синий",
  "с/з": "серый-зеленый",
  "с/к": "серый-красный",
  "с/с": "серый-синий",
  "о/з": "оранжевый-зеленый",
  "чет-ая": "четырёхгранная",

}


re_VOLUME=re.compile("(\\d+([.,]\\d+)?\\s*(м)?л)\\.?(\s|$)")

def autotrans(a, code, group):
  code = code or ''
  group = group or ''

  aname = ''
  code_removed = False
  m_pos = None

  x = re_NAMEDIV.split(a.strip())
  extra = None
  attrib = None
  if x[0] in {"BOSSA", 'LEELAWADEE', 'Al', 'AЛ'}:
    #print ("drop!", x[0])
    extra=x[0]
    x=x[2:]
  if x[0].startswith("Закаточн") or x[0].startswith("Гладильн") or x[0].startswith("Магнитн") or x[0].startswith("Кухонн") or x[0].startswith("Детск"):
    attrib=x[0]
    x=x[2:]
  if x[0][-1]=="-": # join
    #print ("append [%s]"%x[2], x)
    x[0]+=x[2]
    del x[1], x[2]
  if x[0]=='Пара': # join with space
    #print ("append [ %s]"%x[2], x)
    x[0]+=" " + x[2]
    del x[1], x[2]
#  if x[0]==' ':
#    print ("Empty!", x)
  if x[0][0]=='_':
    x[0]=x[0][1:]
    
  name = x[0].capitalize()
  name = FIXNAME.get(name, name)
  aname+=extra+' ' if extra else ''
  aname+=name
  p=2
  material, owngroup = None, None
  while p<len(x):
    if material:
      m=None # lock out after firts found
    else:
      m, owngroup=is_material(x[p])
    if m:
      material = m
      m_pos = len(aname)
      del x[p]
      try: 
        del x[p]
      except:
        pass
      continue
#    if x[p]==code:
 #     #print ("-"+x[p], end=' ')
#      code_removed = True
#      del x[p]
#      try: 
#        del x[p]
#      except:
#        pass
#      continue
    if x[p] in xtrans:
      x[p]=xtrans[x[p]]
      try:
        x[p+1]=' '
      except:
        pass
    
    p=p+2
    
  body = ''.join(x[2:])
  volume_m = re_VOLUME.search(body)
  if volume_m:
    v=volume_m.group(1)
    body = re_VOLUME.sub(' ', body)
  else:
    v = ''

  if attrib:
    aname+=" "+attrib
    
  if material: # and group!=owngroup:
    g = gender(name)
    if g == '?':
      raise Exception("cannot determine gender: %s"%repr(a))

    aname += " "+ by_gender[(material, g)]

    m_pos = None
  
  body = body.strip()
  if body:
    aname += " "+body
  #print(name, end=';')
  return aname, v, code_removed, (m_pos, by_gender[(material, gender(name))]) if m_pos else None

if __name__=="__main__":
  a="Сков-лавашница а/пр 350мм с ручк. сл350а"
  print(a)
  print(autotrans(a, None, None))
