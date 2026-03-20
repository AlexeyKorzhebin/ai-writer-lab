# World & Locations — Спецификация

Дата: 2026-03-20
Статус: Draft

---

## 1. Проблема

### Текущее состояние

`WorldSpec` в `domain/narrative.py`:
```python
@dataclass
class WorldSpec:
    world_type: str = "realistic"
    rules: str = ""
    time_period: str = ""
    power_structures: str = ""
    atmosphere: str = ""
```

`SceneSpec` — нет поля `location`:
```python
@dataclass
class SceneSpec:
    # ...
    participants: list[str]   # есть
    # location — НЕТ
```

### Что теряется
- Нет структурированных локаций → AI может описать один и тот же замок по-разному в разных сценах
- Нет связи "сцена ↔ локация" → невозможно проверить географическую консистентность
- Нет иерархии мест → нельзя понять "комната в замке, который стоит на горе"
- Нет эволюции локаций → после пожара замок всё ещё описывается как "величественный"
- Нет шаблонов миров → пользователь каждый раз описывает заново

---

## 2. Доменная модель

### 2.1 LocationSpec

```python
@dataclass
class LocationSpec:
    id: Optional[int] = None
    name: str = ""
    location_type: str = ""          # "region", "city", "building", "room", "natural", "road"
    parent_id: Optional[int] = None  # иерархия: комната → здание → город → регион
    
    # Описание
    description: str = ""            # общее описание
    visual_details: str = ""         # как выглядит (для генерации текста и иллюстраций)
    atmosphere: str = ""             # настроение, запахи, звуки
    significance: str = ""           # сюжетное значение этого места
    
    # Мир
    climate: str = ""                # климат / погода
    inhabitants: list[str] = field(default_factory=list)  # кто здесь живёт
    notable_features: list[str] = field(default_factory=list)  # ключевые объекты
    
    # Навигация
    connected_to: list[str] = field(default_factory=list)  # соседние локации
    travel_notes: str = ""           # как добраться, сколько времени
    
    # Эволюция
    states: list[LocationState] = field(default_factory=list)
    
    # Метаданные
    tags: list[str] = field(default_factory=list)  # ["опасно", "священное", "заброшенное"]
    first_appearance: Optional[int] = None  # номер сцены первого появления


@dataclass
class LocationState:
    """Состояние локации в определённый момент истории."""
    after_scene: int = 0              # после какой сцены изменилось
    description_override: str = ""    # новое описание
    change_reason: str = ""           # почему изменилось ("пожар", "осада", "прошло 10 лет")
```

### 2.2 Расширение WorldSpec

```python
@dataclass
class WorldSpec:
    world_type: str = "realistic"
    rules: str = ""
    time_period: str = ""
    power_structures: str = ""
    atmosphere: str = ""
    
    # НОВОЕ
    locations: list[LocationSpec] = field(default_factory=list)
    geography_overview: str = ""     # общая география мира
    cultural_notes: str = ""         # культурные особенности
    technology_level: str = ""       # уровень технологий
    languages: list[str] = field(default_factory=list)  # языки мира
    calendar: str = ""               # система летоисчисления
    currency: str = ""               # денежная система
    religions: str = ""              # верования
    history_summary: str = ""        # краткая история мира
```

### 2.3 Расширение SceneSpec

```python
@dataclass
class SceneSpec:
    # ... существующие поля ...
    location: str = ""               # НОВОЕ: имя локации (ссылка на LocationSpec.name)
    time_context: str = ""           # НОВОЕ: время суток, сезон, погода
```

---

## 3. Иерархия локаций

Локации образуют дерево:

```
Средиземье (world)
├── Шир (region)
│   ├── Хоббитон (city)
│   │   ├── Бэг-Энд (building)
│   │   │   ├── Кабинет Бильбо (room)
│   │   │   └── Сад (natural)
│   │   └── Зелёный Дракон (building)
│   └── Бакленд (city)
├── Ривенделл (city)
│   ├── Зал Совета (room)
│   └── Библиотека (room)
├── Мория (region)
│   ├── Ворота Мории (building)
│   ├── Мост Казад-Дума (building)
│   └── Подземные залы (room)
└── Мордор (region)
    ├── Ородруин (natural)
    └── Барад-дур (building)
```

### UI дерева локаций

```
┌─ Locations ────────────────────────────────┐
│                                            │
│  🔍 Search locations...                    │
│                                            │
│  ▼ 🌍 Средиземье                          │
│    ▼ 🏘️ Шир                               │
│      ▼ 🏠 Хоббитон                         │
│          🏰 Бэг-Энд                        │
│          🍺 Зелёный Дракон                  │
│      ► 🏘️ Бакленд                          │
│    ► 🏰 Ривенделл                          │
│    ► ⛏️ Мория                               │
│    ► 🌋 Мордор                              │
│                                            │
│  [+ Add Location]  [🤖 Generate Locations] │
└────────────────────────────────────────────┘
```

---

## 4. World Presets (шаблоны миров)

### 4.1 Концепция

Предзаготовленные миры с локациями, правилами, культурой. Пользователь
выбирает пресет, который заполняет WorldSpec + набор LocationSpec.
Затем можно редактировать, удалять, добавлять.

### 4.2 Формат хранения

Файлы: `app/data/world_presets/*.yaml`

### 4.3 Примеры пресетов

**`middle_earth.yaml`** — Средиземье (толкиеновское фэнтези)

```yaml
key: middle_earth
name: "Средиземье"
name_en: "Middle-earth"
category: fantasy
era: "Третья Эпоха"
description: |
  Обширный мир с различными расами: эльфы, гномы, хоббиты, люди, орки.
  Магия существует, но редка и доступна немногим (Истари, эльфы).
  Мир находится в состоянии угасания — великие эпохи уходят.

world_spec:
  world_type: fantasy
  time_period: "Третья Эпоха Средиземья"
  atmosphere: |
    Мир древний и величественный, пронизанный ощущением уходящей эпохи.
    Красота соседствует с угрозой. Природа жива и одушевлена.
    Тёмные силы нарастают на Востоке.
  rules: |
    Магия существует, но не повсеместна. Великие кольца Власти —
    главный магический артефакт. Бессмертные эльфы покидают мир.
    Мёртвые могут быть призваны заклятием. Палантиры позволяют
    видеть на расстоянии. Гномы искусны в работе с камнем и металлом.
  power_structures: |
    Разрозненные королевства людей (Гондор, Рохан).
    Эльфийские убежища (Ривенделл, Лотлориэн).
    Тёмный властелин Саурон в Мордоре.
    Истари (маги) как советники, но не правители.
  technology_level: "Средневековый с магическими элементами"
  cultural_notes: |
    Каждая раса имеет свою культуру, язык, архитектуру.
    Хоббиты — уют, еда, земледелие.
    Эльфы — искусство, мудрость, печаль.
    Гномы — ремесло, золото, подземные чертоги.
    Люди — амбиции, смертность, героизм.
  languages: ["Всеобщий (Вестрон)", "Синдарин (эльфийский)", "Кхуздул (гномий)", "Чёрная речь"]
  religions: "Валар — божества, создатели мира. Почитаются, но не поклоняются формально."
  history_summary: |
    Мир создан Илуватаром через музыку Айнур. Моргот (первый тёмный
    властелин) побеждён в конце Первой Эпохи. Саурон, его слуга,
    создал Кольцо Всевластья. Последний Союз победил Саурона в конце
    Второй Эпохи, но Кольцо не уничтожено.

locations:
  - name: "Шир"
    type: region
    description: |
      Зелёная, плодородная земля хоббитов на западе Средиземья.
      Холмистые луга, аккуратные огороды, круглые двери в холмах.
    visual_details: "Зелёные холмы с круглыми дверями, цветущие сады, извилистые тропинки"
    atmosphere: "Уют, мир, простота, запах свежего хлеба и трубочного табака"
    climate: "Мягкий, умеренный. Тёплое лето, снежная зима"
    inhabitants: ["Хоббиты"]
    notable_features: ["Водяная мельница", "Мост через Брендивин", "Партийное дерево"]
    tags: ["мирное", "начало пути", "дом"]
    children:
      - name: "Хоббитон"
        type: city
        description: "Главное поселение Шира. Норы в холме Хоббитон-Хилл."
        children:
          - name: "Бэг-Энд"
            type: building
            description: |
              Самая роскошная нора в Хоббитоне. Круглая зелёная дверь,
              длинные коридоры с паркетом, библиотека, кладовые с едой.
            visual_details: "Круглая зелёная дверь, тёплый свет из окон, дым из трубы"
            atmosphere: "Уют, книги, запах чая и старых карт"
            inhabitants: ["Бильбо Бэггинс", "Фродо Бэггинс"]
            significance: "Начало и конец путешествия. Символ дома."

  - name: "Ривенделл"
    type: city
    description: |
      Последний Домашний Приют к востоку от Моря. Эльфийское убежище
      в глубокой долине, окружённой водопадами.
    visual_details: "Изящные мосты, башни среди водопадов, золотой свет сквозь листву"
    atmosphere: "Покой, мудрость, неуловимая печаль, звуки арф и пения"
    climate: "Вечная осень, мягкий свет"
    inhabitants: ["Эльфы", "Элронд"]
    notable_features: ["Зал Совета", "Библиотека", "Обломки Нарсила"]
    significance: "Место принятия ключевых решений. Перекрёсток народов."
    tags: ["священное", "безопасное", "мудрость"]
    children:
      - name: "Зал Совета Элронда"
        type: room
        description: "Открытая терраса с видом на долину, где проходят важнейшие советы"

  - name: "Мордор"
    type: region
    description: |
      Чёрная земля на востоке, окружённая непроходимыми горами.
      Царство Саурона. Выжженная пустыня под вечным дымом.
    visual_details: "Чёрные скалы, красное зарево, пепел, трещины в земле с лавой"
    atmosphere: "Отчаяние, удушье, жар, непроглядный мрак"
    climate: "Вулканический: жар, пепел, дым"
    inhabitants: ["Орки", "Назгулы", "Саурон"]
    notable_features: ["Роковая Гора", "Барад-дур", "Чёрные Врата"]
    tags: ["опасно", "зло", "финал"]
    children:
      - name: "Ородруин (Роковая Гора)"
        type: natural
        description: "Действующий вулкан, в котором было выковано Кольцо. Единственное место его уничтожения."
        significance: "Конечная цель квеста. Место кульминации."
```

**`russia_14th_century.yaml`** — Русь XIV века

```yaml
key: russia_14th
name: "Русь XIV века"
name_en: "Medieval Russia (14th century)"
category: historical
era: "XIV век, Московская Русь под ордынским игом"
description: |
  Русские княжества под властью Золотой Орды. Борьба за объединение
  вокруг Москвы. Религия как центральная сила. Лес, зима, бескрайние
  просторы. Время Сергия Радонежского и Дмитрия Донского.

world_spec:
  world_type: historical
  time_period: "XIV век, Русь"
  atmosphere: |
    Суровый, лесной мир. Деревянные города среди бескрайних лесов.
    Зимние дороги, колокольный звон, запах ладана и дыма.
    Напряжение между покорностью Орде и стремлением к свободе.
  rules: |
    Княжества формально подчинены хану Золотой Орды.
    Ярлык на великое княжение — документ от хана.
    Церковь — главная объединяющая сила.
    Вече в некоторых городах. Дружина — военная элита.
    Торговые пути по рекам. Зимой — санный путь.
  power_structures: |
    Великий князь Московский (стремится к объединению).
    Хан Золотой Орды (верховная власть, дань).
    Митрополит (духовная власть, объединительная роль).
    Удельные князья (Тверь, Суздаль, Рязань — соперники).
    Бояре (знать, советники).
    Новгород (торговая республика, особый статус).
  technology_level: "Раннесредневековый. Дерево, лошади, мечи, луки. Каменное строительство для храмов."
  cultural_notes: |
    Православие — центр жизни. Монастыри — центры культуры.
    Иконопись (Андрей Рублёв — конец XIV в.). Летописание.
    Устная традиция: былины, сказания. Скоморохи.
    Быт: изба, печь, квас, каша, мёд. Баня. Охота.
  languages: ["Древнерусский (старославянский литературный)", "Тюркские языки (общение с Ордой)", "Церковнославянский"]
  currency: "Серебряные гривны, деньги (монеты), мех как валюта"
  religions: "Православное христианство. Языческие пережитки в быту. Ислам в Орде."
  calendar: "От сотворения мира. 6800-е годы = ~1300-е от Р.Х."
  history_summary: |
    1237–1240: Монгольское нашествие, разорение Руси.
    1325: Иван Калита — начало возвышения Москвы.
    1340-е: Москва — центр митрополии.
    1359: Дмитрий Иванович (Донской) — великий князь.
    1378: Битва на Воже — первая крупная победа над Ордой.
    1380: Куликовская битва.

locations:
  - name: "Москва"
    type: city
    description: |
      Растущий город на Москве-реке. Деревянный кремль на холме,
      посады вокруг. Торговые ряды. Звон колоколов.
    visual_details: "Деревянные стены кремля, золотые купола, дым из изб, река подо льдом зимой"
    atmosphere: "Суета торговли, колокольный звон, запах дыма и хлеба, грязные улицы весной"
    climate: "Суровая зима (-20°), грязная весна, жаркое короткое лето, золотая осень"
    inhabitants: ["Великий князь и двор", "Бояре", "Купцы", "Ремесленники", "Монахи"]
    notable_features: ["Кремль (деревянный, с 1367 — белокаменный)", "Успенский собор", "Торг"]
    tags: ["столица", "политический центр", "растущий"]
    children:
      - name: "Московский Кремль"
        type: building
        description: |
          Крепость на Боровицком холме. До 1367 — дубовые стены,
          затем белокаменные (первый каменный кремль).
        visual_details: "Белые каменные стены, башни, княжеский терем, соборы внутри"
        atmosphere: "Власть, сила, запах воска из храмов, лязг оружия стражи"
        significance: "Центр власти. Символ объединения."
        children:
          - name: "Княжеский терем"
            type: room
            description: "Деревянные хоромы великого князя внутри кремля. Горница, трапезная, сени."
          - name: "Успенский собор"
            type: building
            description: "Главный храм. Здесь благословляют на великое княжение."
            significance: "Духовный центр. Место ключевых церемоний."

  - name: "Троице-Сергиева лавра"
    type: building
    description: |
      Монастырь, основанный Сергием Радонежским в лесу к северу от Москвы.
      Деревянные кельи, храм, пасека, огороды. Место паломничества.
    visual_details: "Деревянная ограда в лесу, маленькая церковь, дым от кузницы, тропинки в снегу"
    atmosphere: "Тишина, молитва, запах ладана и свежего дерева, пение птиц"
    inhabitants: ["Сергий Радонежский", "Монахи"]
    significance: "Духовный центр Руси. Сергий благословляет Дмитрия на Куликовскую битву."
    tags: ["священное", "тихое", "мудрость"]

  - name: "Куликово поле"
    type: natural
    description: |
      Широкое поле при слиянии Дона и Непрядвы.
      Место решающей битвы с Мамаем (1380).
    visual_details: "Бескрайнее поле, туман с реки, серое небо, дубрава на краю"
    atmosphere: "Напряжение перед битвой. Запах мокрой земли и реки. Тишина перед бурей."
    climate: "Начало осени. Туман утром, прохлада."
    significance: "Место кульминации — Куликовская битва."
    tags: ["кульминация", "историческое", "поле битвы"]
    states:
      - after_scene: 0  # до битвы
        description_override: "Мирное поле, покрытое травой. Тишина. Две реки сливаются."
      - after_scene: 15  # после битвы
        description_override: |
          Поле усеяно телами. Знамёна втоптаны в грязь.
          Стоны раненых. Вороны кружат. Реки окрашены кровью.
        change_reason: "Куликовская битва"

  - name: "Золотая Орда (Сарай)"
    type: city
    description: |
      Столица Золотой Орды на Нижней Волге. Богатый город с базарами,
      мечетями, дворцами. Пёстрая смесь народов.
    visual_details: "Шатры и каменные дворцы, верблюды, пёстрые базары, минареты"
    atmosphere: "Жара, пыль, запах пряностей и конского пота, крики торговцев"
    inhabitants: ["Хан", "Мурзы", "Торговцы", "Рабы"]
    tags: ["чужое", "опасное", "богатое"]

  - name: "Дорога в Орду"
    type: road
    description: |
      Долгий путь на юго-восток через степи. Недели пути верхом.
      Опасности: разбойники, непогода, неизвестность.
    visual_details: "Бескрайняя степь, ковыль до горизонта, одинокий путник на коне"
    atmosphere: "Одиночество, тревога, ветер, бесконечное пространство"
    travel_notes: "2-3 недели верхом из Москвы. Через Рязанские земли и степь."
    tags: ["путешествие", "опасно"]
```

**`victorian_london.yaml`** — Викторианский Лондон

```yaml
key: victorian_london
name: "Викторианский Лондон"
name_en: "Victorian London"
category: historical
era: "Вторая половина XIX века"
description: |
  Столица Британской империи на пике могущества.
  Контрасты: блеск аристократии и нищета трущоб.
  Туман, газовые фонари, кэбы, Темза.

world_spec:
  world_type: historical
  time_period: "Викторианская эпоха, 1870–1890-е"
  atmosphere: |
    Густой туман (smog), газовые фонари, цоканье копыт по булыжнику.
    Блеск салонов Мэйфэра и мрак переулков Уайтчепела.
    Эпоха прогресса и социальных контрастов.
  rules: |
    Жёсткая классовая система. Колониальная империя.
    Промышленная революция. Железные дороги. Телеграф.
    Полиция (Scotland Yard, с 1829). Газовое освещение.

locations:
  - name: "Бейкер-стрит 221Б"
    type: building
    description: "Знаменитая квартира. Камин, два кресла, химическая лаборатория, скрипка."
    tags: ["детектив", "уют", "начало расследования"]
  - name: "Доки Лаймхаус"
    type: region
    description: "Портовый район. Опиумные притоны, моряки, контрабандисты. Запах дёгтя и гнили."
    tags: ["опасно", "ночное", "преступность"]
  - name: "Вест-Энд"
    type: region
    description: "Аристократический район. Театры, клубы, роскошные особняки."
    tags: ["богатое", "светское"]
```

### 4.4 Каталог пресетов

| Пресет | Категория | Локаций | Описание |
|--------|-----------|---------|----------|
| `middle_earth` | Fantasy | 15+ | Средиземье Толкиена |
| `russia_14th` | Historical | 10+ | Русь XIV века, Куликовская битва |
| `victorian_london` | Historical | 12+ | Лондон Шерлока Холмса |
| `hogwarts_world` | Fantasy | 10+ | Мир Гарри Поттера |
| `cyberpunk_city` | Sci-Fi | 8+ | Неон, корпорации, подземный мир |
| `ancient_rome` | Historical | 10+ | Рим эпохи империи |
| `japan_sengoku` | Historical | 8+ | Япония эпохи Сэнгоку |
| `space_station` | Sci-Fi | 6+ | Космическая станция, корабли |
| `american_frontier` | Historical | 8+ | Дикий Запад, 1870-е |
| `empty` | — | 0 | Пустой мир (с нуля) |

---

## 5. Import World — импорт мира из описания или источника

### 5.1 Концепция

Пользователь хочет использовать известный вымышленный мир (Средиземье, Белория,
Хогвартс) или историческую эпоху (Русь XIV века, Викторианский Лондон)
без ручного заполнения. Функция Import позволяет:

- **Import by Name** — ввести название мира ("Белория, Ольга Громыко") → AI + web search восстанавливает мир
- **Import by Text** — вставить описание мира текстом → AI структурирует в WorldSpec + LocationSpec
- **Import from File** — загрузить MD/TXT файл с описанием мира

### 5.2 User Flow

```
1. В Story Wizard Step 2 (World) → кнопка [Import World]
2. Открывается modal:
   ┌─ Import World ──────────────────────────────────┐
   │                                                  │
   │  ○ By name — укажите произведение / мир          │
   │  ○ By text — вставьте описание                   │
   │  ○ From file — загрузите файл .md / .txt         │
   │                                                  │
   │  ──────────────────────────────────────────────  │
   │                                                  │
   │  [By name selected]                              │
   │                                                  │
   │  World / Source:                                  │
   │  [Белория, Ольга Громыко "Профессия: ведьма"]    │
   │                                                  │
   │  What to import:                                 │
   │  ☑ World rules & atmosphere                      │
   │  ☑ Locations (geography)                         │
   │  ☑ Races & peoples                               │
   │  ☑ Power structures                              │
   │  ☐ Characters (import as templates)              │
   │  ☑ Magic system / technology                     │
   │  ☑ Cultural details                              │
   │                                                  │
   │  [🤖 Import]                                     │
   └──────────────────────────────────────────────────┘

3. AI генерирует структурированное описание (loading state)
4. Результат показывается для review:
   ┌─ Import Preview ────────────────────────────────┐
   │                                                  │
   │  ✅ World Spec                          [Edit ▾] │
   │    Type: Fantasy                                 │
   │    Period: Средневековье с магией                │
   │    Atmosphere: Юмористическое фэнтези...        │
   │                                                  │
   │  ✅ Locations (8 found)                 [Edit ▾] │
   │    🏰 Стармин (столица)                         │
   │    🏫 Школа Чародеев, Пифий и Травниц          │
   │    🧛 Догева (долина вампиров)                   │
   │    🧛 Арлисс (островная долина)                  │
   │    🌲 Яснёвый Град (эльфийский лес)             │
   │    ⛰️ Гребенчатые горы                          │
   │    🏚️ Пустоши                                   │
   │    🌊 Озёрный край                               │
   │                                                  │
   │  ✅ Magic System                        [Edit ▾] │
   │    Школа: 4 факультета, 10 лет обучения         │
   │    Ковен магов — межрасовая организация          │
   │    Магические ранги: адепт → магистр → архимаг   │
   │                                                  │
   │  ✅ Races (6 found)                     [Edit ▾] │
   │    Люди, Вампиры, Тролли, Эльфы,               │
   │    Гномы, Оборотни                              │
   │                                                  │
   │  ⚠ Note: AI-reconstructed. Verify details.      │
   │                                                  │
   │  [Apply to Project]  [Edit Before Apply]  [Cancel] │
   └──────────────────────────────────────────────────┘

5. Пользователь может отредактировать каждую секцию перед применением
6. [Apply to Project] — заполняет WorldSpec + создаёт LocationSpec
```

### 5.3 Backend: Import Pipeline

```
POST /projects/{id}/world/import
Body: {
  "mode": "by_name" | "by_text" | "by_file",
  "source": "Белория, Ольга Громыко",   // or text content
  "options": {
    "import_locations": true,
    "import_races": true,
    "import_magic": true,
    "import_culture": true,
    "import_characters": false
  }
}
```

**Pipeline:**

```
1. [By Name] → AI формирует поисковый запрос
2. (Optional) Web search / RAG для дополнительного контекста
3. AI структурирует данные в JSON:
   {
     "world_spec": { ... },
     "locations": [ ... ],
     "races": [ ... ],
     "magic_system": "...",
     "notes": "..."
   }
4. Return preview for user review
5. User confirms → Apply to NarrativeSpec
```

### 5.4 AI промпт для импорта

```
You are a world-building expert. Reconstruct the fictional world from the
following source.

Source: {source_name_or_text}

Extract and structure the following:

1. WORLD OVERVIEW:
   - World type (fantasy / sci-fi / historical / etc)
   - Time period equivalent
   - Atmosphere and tone
   - Rules (magic, physics, social)
   - Power structures
   - Technology level
   - Currency, calendar, languages
   - Religions

2. LOCATIONS (as a hierarchical tree):
   For each location:
   - Name
   - Type (region / city / building / room / natural / road)
   - Parent location
   - Description (2-3 sentences)
   - Visual details
   - Atmosphere
   - Key inhabitants
   - Notable features
   - Significance for the story
   - Connected locations

3. RACES & PEOPLES:
   For each:
   - Name
   - Key traits
   - Culture
   - Abilities
   - Relations with other races

4. MAGIC/TECHNOLOGY SYSTEM:
   - How it works
   - Who can use it
   - Limitations
   - Key institutions

Return as structured JSON.
Mark uncertain details with "uncertain": true.
```

### 5.5 Import Location (отдельная функция)

Помимо импорта целого мира, можно импортировать одну локацию:

```
User: "Добавь в мой проект Хогвартс из Гарри Поттера"

→ AI восстанавливает:
  - Хогвартс (building)
    - Большой зал (room)
    - Башня Гриффиндора (building)
    - Подземелья Слизерина (room)
    - Запретный лес (natural)
    - Озеро (natural)
    - Квиддичное поле (building)
    - Выручай-комната (room)

→ User reviews, edits, applies
```

Endpoint:
```
POST /projects/{id}/locations/import
Body: {
  "source": "Хогвартс, Harry Potter",
  "mode": "by_name"
}
```

### 5.6 "Import by Text" — пример

Пользователь вставляет свой текст:

```
Мой мир — система плавучих островов в бесконечном небе.
Каждый остров — это кусок суши диаметром от 100 метров до 50 км,
парящий на разных высотах. Между островами перемещаются на
летучих кораблях. Магии нет, но есть технология "гравитонов" —
кристаллов, управляющих гравитацией. Общество разделено на
Верхних (богатые острова наверху, ближе к солнцу) и Нижних
(бедные острова внизу, в тумане).
```

AI структурирует → WorldSpec + начальные локации (Верхний остров, Нижний остров, Торговый узел, и т.д.)

### 5.7 Предупреждения и disclaimer

При импорте известных миров показывать:

```
⚠ Импортированный мир основан на произведениях Ольги Громыко.
  Детали восстановлены AI и могут содержать неточности.
  Рекомендуется проверить и отредактировать перед использованием.
  
  Если вы пишете фанфик — это нормально.
  Если вы пишете оригинальное произведение — используйте как
  вдохновение и измените ключевые детали.
```

---

## 6. Story Wizard — шаг "World" (переработка)

### 5.1 Текущий Step 2 (World)

Сейчас: 4 текстовых поля (world_type, rules, time_period, atmosphere).

### 5.2 Новый Step 2 (World & Locations)

Разбить на два подшага или один расширенный:

```
┌─────────────────────────────────────────────────────┐
│  Step 2 — World & Locations                         │
│                                                     │
│  ┌─ Quick Start ──────────────────────────────────┐ │
│  │  Use a world preset:                           │ │
│  │                                                │ │
│  │  [🗡️ Средиземье]  [🏰 Русь XIV в.]             │ │
│  │  [🔍 Вик. Лондон]  [🚀 Cyberpunk]              │ │
│  │  [⚔️ Древний Рим]  [🌸 Япония Сэнгоку]         │ │
│  │  [📝 С нуля]                                   │ │
│  └────────────────────────────────────────────────┘ │
│                                                     │
│  (после выбора пресета или "С нуля" →)              │
│                                                     │
│  ┌─ World Overview ───────────────────────────────┐ │
│  │  Type: [Fantasy ▾]   Period: [Третья Эпоха  ]  │ │
│  │  Atmosphere:                                   │ │
│  │  [_________________________________________]   │ │
│  │  Rules of the World:                           │ │
│  │  [_________________________________________]   │ │
│  │  Technology: [_____]  Culture: [_____________]  │ │
│  │                                                │ │
│  │  [🤖 Expand Description]  [🤖 Suggest Rules]   │ │
│  └────────────────────────────────────────────────┘ │
│                                                     │
│  ┌─ Locations ────────────────────────────────────┐ │
│  │                                                │ │
│  │  ▼ 🌍 Средиземье                              │ │
│  │    ▼ 🏘️ Шир                                   │ │
│  │        🏠 Хоббитон         [Edit] [Delete]    │ │
│  │        🏠 Бакленд          [Edit] [Delete]    │ │
│  │    ► 🏰 Ривенделл                             │ │
│  │    ► ⛏️ Мория                                  │ │
│  │    ► 🌋 Мордор                                │ │
│  │                                                │ │
│  │  [+ Add Location]  [🤖 Generate Locations]     │ │
│  └────────────────────────────────────────────────┘ │
│                                                     │
│           [← Back]                    [Next →]      │
└─────────────────────────────────────────────────────┘
```

### 5.3 Редактор локации (modal)

При нажатии Edit или Add:

```
┌─ Edit Location ──────────────────────────────────┐
│                                                  │
│  Name: [Хоббитон                            ]    │
│  Type: [City ▾]    Parent: [Шир ▾]              │
│                                                  │
│  Description:                                    │
│  [Главное поселение Шира. Норы в холме...   ]    │
│                                                  │
│  Visual Details: (для текста и иллюстраций)      │
│  [Зелёные холмы с круглыми дверями...       ]    │
│                                                  │
│  Atmosphere: (запахи, звуки, настроение)         │
│  [Уют, запах свежего хлеба, пение птиц...   ]    │
│                                                  │
│  Climate: [Мягкий, умеренный               ]     │
│                                                  │
│  Notable Features:                               │
│  [Партийное дерево] [Водяная мельница] [+]       │
│                                                  │
│  Inhabitants:                                    │
│  [Хоббиты] [+]                                   │
│                                                  │
│  Connected to:                                   │
│  [Бакленд] [Бри] [+]                            │
│                                                  │
│  Significance: (для сюжета)                      │
│  [Начало и конец путешествия. Символ дома.  ]    │
│                                                  │
│  Tags: [мирное] [начало пути] [дом] [+]          │
│                                                  │
│  [🤖 Expand Description]  [🤖 Suggest Details]   │
│                                                  │
│  [Cancel]                      [Save Location]   │
└──────────────────────────────────────────────────┘
```

---

## 6. Story Workspace — интеграция локаций

### 6.1 Left Panel: секция Locations

```
┌─ Left Panel ──────────────────┐
│                               │
│  ► Characters (3)             │
│  ▼ Locations (8)              │
│    🏘️ Хоббитон               │
│    🏰 Ривенделл  ← текущая   │
│    ⛏️ Мория                   │
│    🌋 Мордор                  │
│    ...                        │
│  ► World                      │
│  ► Scenes (12)                │
│                               │
└───────────────────────────────┘
```

При клике на локацию → показать превью:

```
┌─ Ривенделл ──────────────────────┐
│  Последний Домашний Приют к       │
│  востоку от Моря...               │
│                                   │
│  Scenes here: Scene 4, Scene 7    │
│  Characters: Элронд, Гэндальф    │
│                                   │
│  [Open in Editor] [📌 Pin to Chat]│
└───────────────────────────────────┘
```

### 6.2 Scene Editor: поле Location

В редакторе сцены добавить:

```
┌─ Scene: Совет Элронда ───────────────────┐
│                                          │
│  Location: [🏰 Зал Совета Элронда ▾]     │
│  Time:     [Утро, ясное осеннее      ]   │
│                                          │
│  [текст сцены...]                        │
└──────────────────────────────────────────┘
```

Dropdown Location — выбор из дерева локаций с поиском.

### 6.3 Контекст для AI Chat

Локация становится частью `@`-ссылок:
- `@location:Ривенделл` — полное описание локации
- `@location:current` — локация текущей сцены
- `@locations:all` — список всех локаций (краткий)

---

## 7. Location Consistency Agent

### 7.1 Назначение

Проверяет, что:
- Одна и та же локация описана одинаково в разных сценах
- Расстояния и время перемещения реалистичны
- Эволюция локаций учитывается (после пожара замок не "величественный")
- Детали не противоречат (цвет двери, этажность здания)
- Персонажи не телепортируются (если герой в Мории, он не может быть в Шире в следующей сцене без перемещения)

### 7.2 Промпт для агента

```
You are a location consistency editor. Analyze the following scenes
and check for geographical and environmental consistency.

World: {world_spec}

Locations:
{locations_with_descriptions}

Scenes:
{scene_list_with_locations}

Check for:
1. Description consistency — same location described differently?
2. Travel logic — can characters get from A to B in the time implied?
3. Location evolution — are changes (damage, weather) reflected?
4. Detail conflicts — doors, colors, layout contradictions?
5. Atmosphere drift — does the mood of a location stay consistent?

Return JSON:
{
  "score": 0-10,
  "issues": [
    {
      "type": "description_conflict" | "travel_logic" | "evolution_missed" | "detail_conflict" | "atmosphere_drift",
      "scenes": [3, 7],
      "location": "Ривенделл",
      "description": "...",
      "suggestion": "..."
    }
  ]
}
```

### 7.3 UI результатов

В Book Analytics и в правой панели Workspace:

```
┌─ Location Consistency ────────────────┐
│  Score: [7.2] 🟡                      │
│                                       │
│  ⚠ Шир описан по-разному             │
│    Scene 1: "зелёные холмы"          │
│    Scene 9: "серые холмы"            │
│    → Если не было сезонной смены,     │
│      уточните описание                │
│    [Go to Scene 1] [Go to Scene 9]   │
│                                       │
│  ⚠ Телепортация: Арагорн             │
│    Scene 5: Мория → Scene 6: Лориэн  │
│    → Нет сцены перехода               │
│    [Add Transition Scene]             │
│                                       │
│  ✅ Мордор: consistent across scenes   │
│  ✅ Ривенделл: consistent              │
└───────────────────────────────────────┘
```

---

## 8. AI-генерация локаций

### 8.1 Generate Locations (в Wizard)

Кнопка "Generate Locations" в Step 2 Wizard:

```
POST /projects/{id}/narrative-spec/generate-locations
Body: {
  "world_spec": { ... },
  "core_idea": { ... },
  "characters": [ ... ],
  "count": 5-10
}
Response: {
  "locations": [
    {
      "name": "...",
      "type": "...",
      "description": "...",
      "visual_details": "...",
      "atmosphere": "...",
      "significance": "...",
      "connected_to": ["..."],
      "children": [...]
    }
  ]
}
```

AI учитывает жанр, конфликт и персонажей для создания релевантных локаций.

### 8.2 Suggest Location for Scene

При создании/генерации сцены AI предлагает подходящую локацию:

```
AI: Для сцены "Тайная встреча" подходят:
  1. 🏠 Бэг-Энд (intimate, safe)
  2. 🌲 Лес за Хоббитоном (secretive)
  3. 🆕 New: Заброшенная мельница (atmospheric)
  
  [Use 1] [Use 2] [Create 3] [Other...]
```

### 8.3 Expand Location

Для существующей локации: "AI, расскажи больше про это место":

```
POST /projects/{id}/narrative-spec/expand-location/{location_id}
Response: {
  "expanded_description": "...",
  "suggested_visual_details": "...",
  "suggested_atmosphere": "...",
  "suggested_features": ["...", "..."],
  "historical_context": "..."  // для исторических миров
}
```

---

## 9. Location Map (визуализация)

### 9.1 Простая карта связей

В Left Panel или отдельной вкладке — граф локаций:

```
┌─ Location Map ──────────────────────────────┐
│                                             │
│         [Шир] ——— [Бри] ——— [Ривенделл]   │
│                                ↓            │
│                             [Мория]         │
│                                ↓            │
│                           [Лотлориэн]       │
│                                ↓            │
│         [Рохан] ——— [Гондор] ← [Мордор]   │
│                                             │
│  Legend:                                    │
│  ● Visited  ○ Not yet  ★ Current scene     │
│                                             │
└─────────────────────────────────────────────┘
```

Реализация: SVG или Canvas, простая force-directed layout.
Альтернатива на первом этапе: текстовый список связей.

### 9.2 Цветовая кодировка

- Зелёный — сцены написаны в этой локации
- Серый — локация определена, но сцен нет
- Жёлтый — текущая сцена
- Красный — есть проблемы консистентности

---

## 10. Эволюция локаций

### 10.1 Концепция

Локации меняются по ходу сюжета. Примеры:
- Замок сгорел → описание должно измениться
- Прошла зима → ландшафт другой
- Город захвачен → новые обитатели

### 10.2 UI: Location Timeline

```
┌─ Хоббитон — Timeline ─────────────────────┐
│                                            │
│  ● Scene 1: Мирный, зелёный, праздник     │
│  │                                         │
│  ● Scene 5: Без изменений                 │
│  │                                         │
│  ⚡ Scene 12: CHANGE                       │
│  │  Шаркун захватил Шир.                   │
│  │  Деревья вырублены, мельница разрушена. │
│  │                                         │
│  ● Scene 15: Разорённый, серый, печальный  │
│  │                                         │
│  ⚡ Scene 18: CHANGE                       │
│  │  Шир восстановлен. Новые деревья.       │
│                                            │
│  [+ Add State Change]                      │
└────────────────────────────────────────────┘
```

### 10.3 Автоматическое отслеживание

При генерации сцены AI получает **актуальное состояние локации** на момент
этой сцены (учитывая все LocationState с `after_scene < current_scene`).

---

## 11. Backend: новые endpoints

```
GET  /projects/{id}/locations                    → список всех локаций (дерево)
POST /projects/{id}/locations                    → создать локацию
PUT  /projects/{id}/locations/{loc_id}           → обновить локацию
DELETE /projects/{id}/locations/{loc_id}          → удалить

POST /projects/{id}/locations/generate           → AI-генерация локаций по WorldSpec
POST /projects/{id}/locations/{loc_id}/expand     → AI-расширение описания
POST /projects/{id}/locations/consistency-check   → проверка консистентности

GET  /world-presets                              → список доступных пресетов
GET  /world-presets/{key}                        → полный пресет с локациями
POST /projects/{id}/apply-world-preset           → применить пресет к проекту
```

---

## 12. DB Schema (новые таблицы)

```sql
CREATE TABLE locations (
    id INTEGER PRIMARY KEY,
    narrative_spec_id INTEGER REFERENCES narrative_specs(id),
    parent_id INTEGER REFERENCES locations(id),
    name TEXT NOT NULL,
    location_type TEXT,       -- 'region', 'city', 'building', 'room', 'natural', 'road'
    description TEXT,
    visual_details TEXT,
    atmosphere TEXT,
    significance TEXT,
    climate TEXT,
    inhabitants TEXT,         -- JSON array
    notable_features TEXT,    -- JSON array
    connected_to Text,       -- JSON array of location names
    travel_notes TEXT,
    tags TEXT,                -- JSON array
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE location_states (
    id INTEGER PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    after_scene INTEGER,     -- scene order after which this state applies
    description_override TEXT,
    change_reason TEXT
);
```

Расширить `scenes`:
```sql
ALTER TABLE scenes ADD COLUMN location TEXT DEFAULT '';
ALTER TABLE scenes ADD COLUMN time_context TEXT DEFAULT '';
```

---

## 13. Интеграция с другими модулями

### 13.1 С генерацией текста (WriterPipeline)

При генерации сцены в промпт включается:
- Описание локации (актуальное с учётом LocationState)
- Visual details (для описательных пассажей)
- Atmosphere (для тона)
- Соседние локации (для понимания географии)

### 13.2 С Illustration Prompt Generator

`visual_details` и `atmosphere` локации автоматически подставляются
в `{{setting}}` промпта для иллюстрации.

### 13.3 С AI Chat (@-ссылки)

`@location:Name` подтягивает полное описание с учётом текущего состояния.

### 13.4 С ConsistencyAgent

Локации включаются в анализ book-level consistency.

### 13.5 С Author Style Presets

World preset может быть связан с author style preset:
"Средиземье" → стиль Толкиена, "Русь XIV в." → стиль а-ля летопись.
