# CLAUDE.md — Sakin Akış

Bu dosya, Claude Code'un bu proje üzerinde çalışırken ihtiyaç duyacağı bağlamı içerir.

## Proje nedir, neden var

Kullanıcı X (Twitter)'ı taraflı/anlamsız/toxic ragebait içerik yüzünden kullanmayı bıraktı ve
kendi haber+oyun güncellemesi takip aracını yaptı: **Sakin Akış**. Amaç: algoritma yok,
reklam yok, kronolojik sıra, kullanıcı kontrolünde filtreleme. "Sakin" isim/marka kimliği
ciddiye alınmalı — her yeni özellik bu sakinlik felsefesine (gürültü azaltma, kullanıcı
kontrolü, şeffaflık) uygun olmalı.

**Canlı site:** https://olymei.github.io/sakin-akis/
**Repo:** github.com/olymei/sakin-akis (public)

## Mimari — büyük resim

Tek bir Python dosyası (`sakin_akis.py`) her şeyi yapar:

1. RSS/Steam feed'lerinden haber ve oyun güncellemelerini çeker
2. Python tarafında temizlik/kümeleme/AI-özet ön işlemesi yapar
3. Tek bir **statik HTML dosyası** üretir — içine gömülü vanilla JS (framework yok) ve CSS ile
4. Bu HTML dosyası GitHub Pages üzerinden yayınlanır, GitHub Actions saatte bir otomatik yeniden üretir

**Neden bu mimari:** İlk deneme claude.ai artifact'ı (tarayıcı sandbox'ı) içindi ama sandbox'ın
dış ağ isteklerini engellemesi yüzünden çalışmadı (CORS/network kısıtı — bkz. "Denenip
vazgeçilen yollar"). Sonra yerel Python script'e geçildi, sonra kullanıcı her cihazından
erişebilmek istediği için GitHub Pages + Actions'a taşındı.

### Çalışma modları (kritik ayrım)

Script `os.environ.get("GITHUB_ACTIONS") == "true"` ile hangi ortamda çalıştığını anlar:

- **Yerel (kullanıcının bilgisayarında, elle çalıştırınca):** Hızlı kalması için görsel arama
  (Wikipedia sorguları) ATLANIR, direkt placeholder monogram kullanılır. Çıktı:
  `sakin_akis_ciktisi.html`, otomatik tarayıcıda açılır (`webbrowser.open`).
- **CI (GitHub Actions, arka planda, kullanıcı beklemiyor):** Görsel arama VE AI özet üretimi
  burada çalışır çünkü kullanıcı yavaşlığı hissetmiyor. Çıktı: `dist/index.html` (Pages
  artifact olarak yüklenir).

Bu ayrım bilinçli bir tasarım kararı — yerelde hız, CI'da tam özellik.

## Kaynaklar (`SOURCES` listesi)

İki kategori: `"haber"` ve `"oyun"`. Her kaynağın `id`, `name`, `category`, `rss` (URL)
alanları var. Eskiden bir de `color` (hex, marka rengi) alanı vardı -- kaynak
toggle'larındaki, kart üstündeki ve kümedeki swatch noktalarında kullanılıyordu; kullanıcı
"gerek yok" deyip kaldırttı, aynı anda site tamamen siyah-beyaza geçti (bkz. "Tema").

**Haberler (23):** Reuters, AP, BBC (EN), BBC Türkçe, Cumhuriyet, Bianet, TRT Haber,
Anadolu Ajansı, Sözcü, Habertürk, NTV, Hürriyet, Sabah, Halk TV, T24, DW Türkçe,
Al Jazeera English, The Guardian, Euronews, NPR, CNN Türk, Yeni Şafak, The Economist —
bilinçli olarak siyasi yelpazede dengeli (devlet: TRT/AA; pro-hükümet: Sabah/Habertürk/
Yeni Şafak/CNN Türk; muhalefet: Sözcü/Cumhuriyet/Halk TV; bağımsız: Bianet/T24/Hürriyet;
uluslararası: Reuters/AP/BBC/Al Jazeera/Guardian/Euronews/NPR/DW/Economist), kullanıcı
açıkça bunu istedi. 9'dan 22'ye genişletildi -- kullanıcı "büyük kaynakların hepsi olsun"
dedi, TR + İngilizce/uluslararası karışımı özellikle istendi. Sonra The Economist tek
başına eklendi (kullanıcı "bu son olsun" dedi -- 23'te durulacak, bilinçli bir sınır:
daha fazlası kaynak listesinin kendisini gürültüye çevirir).

**Oyunlar (11):** Deadlock, Bodycam, Project Zomboid, Minecraft, TFT, Valorant,
League of Legends, Rainbow Six Siege, Counter-Strike 2, Dota 2, Büyük Oyun Haberleri (genel)

**RSS kaynak stratejisi:**
- Steam'de olan oyunlar (Deadlock, Bodycam, Zomboid, R6 Siege, CS2, Dota2) →
  `https://store.steampowered.com/feeds/news/app/{appid}/` — resmi ve güvenilir
- Kendi RSS'i olan (BBC, Habertürk, NTV, Hürriyet, Sabah, Halk TV, Al Jazeera English,
  The Guardian, Euronews, NPR, CNN Türk, Yeni Şafak) → direkt kullanılıyor
- Geri kalan HERKES (Reuters, AP, Cumhuriyet, Bianet, TRT, AA, Sözcü, T24, DW Türkçe,
  Minecraft, TFT, Valorant, LoL, genel oyun haberleri) → Google News search RSS
  (`news.google.com/rss/search?q=...`) çünkü ya resmi RSS'leri yok ya da denendi/kırık çıktı
  (T24'ün `/rss` yolu 404 dönüyor; DW Türkçe'nin resmi feed'i RSS 1.0/RDF formatında,
  parser'ın desteklemediği format — Google News fallback'e düşürüldü)

⚠️ **Atom format bug'ı (NTV eklenirken bulundu):** `parse_items` içinde Atom dalı
(`is_atom`), `<title>` etiketini namespace'siz arıyordu (`node.find("title")`) ama Atom'da
title `{http://www.w3.org/2005/Atom}title` namespace'inde -- bu yüzden tüm Atom kaynakları
SESSİZCE 0 haber döndürüyordu (başlık boş çıkıp `if title and link and dt` filtresine
takılıyordu). O ana kadar hiçbir kaynak Atom formatında olmadığı için fark edilmemişti.
Düzeltme: title de link/date gibi `is_atom` dalında `atom:title` ile aranıyor artık. Yeni
bir kaynak eklerken "0 haber" görürsen önce format'ı kontrol et (RSS 2.0 / Atom / RDF hepsi
farklı davranır).

⚠️ **Ayni namespace bug'i gorsel icin de vardi:** NTV'nin Atom feed'inde item basina
gercek `<enclosure type="image/jpeg" url="...">` vardi ama `node.find("enclosure")`
namespace'siz aradigi icin Atom'da hic eslesmiyordu (23 kaynagi kontrol ederken bulundu --
kullanici "yeni kaynaklarda gorsel yok" diye fark etti). Duzeltme: `is_atom` ise once
`atom:enclosure` deneniyor, sonra namespace'siz "enclosure"e duesuyor. Ayrica CNN Türk
standart-disi duz bir `<image>URL</image>` etiketi kullaniyor (ne enclosure ne media:*) --
bu da gorsel zincirine (enclosure -> media:content -> media:thumbnail -> description/
content:encoded icindeki img -> duz `<image>`) son adim olarak eklendi. Ikisi de artik
kendi RSS'inden %100 gercek gorsel aliyor (once Wikipedia fallback'ine duesup ~%5-10
kapsama alaniyordu). Yeni bir kaynak eklerken gorsel oranı dusukse (Wikipedia baseline'i
~%8-14, bkz. Cumhuriyet/Bianet/TRT/AA/Sözcü) ama kaynak KENDI RSS'ini kullaniyorsa (Google
News degil), feed'in ham XML'ini kontrol et -- standart-disi bir gorsel alani olabilir.

**Riot Games (Valorant/LoL/TFT) — patch notes'a özel sorgu:** İlk hali genel oyun adı
sorgusuydu ("Valorant", "League of Legends" vb.) ve bu sadece esports/kozmetik/roster
haberleri döndürüyordu, gerçek yama notu HİÇ gelmiyordu (kullanıcı bunu fark edip bildirdi).
Çözüm: sorguyu `"<Oyun> Patch Notes" site:<resmi-site> -Archive when:Nd` şekline daraltmak
(Valorant: `site:playvalorant.com`, `when:30d`; LoL: `site:leagueoflegends.com`,
`-"Wild Rift"` ile kardeş oyunu eleme, `when:14d`; TFT: site kısıtı olmadan `"patch notes"`
ifadesi yeterli oldu, `when:14d`). `when` penceresi her oyunun yama sıklığına gore ayarlandı
(LoL/TFT ~2 haftada bir, Valorant ~6 haftada bir). Gerçek Google News sorgularıyla
(tarayıcıda canlı test edilerek) doğrulandı -- artık en güncel yama notu ilk sıralarda
geliyor. Hâlâ biraz gürültü var (wiki sayfaları, ilgili haber analizleri) ama kabul
edilebilir seviyede.

## Haber temizleme ve kümeleme — iki farklı katman

Bunları birbirine KARIŞTIRMAMAK önemli, ikisi de var ve farklı amaçlara hizmet ediyor:

### 1. Aynı kaynak içi tekilleştirme (Python, `parse_items` içinde)
Google News bazen aynı haberi aynı kaynaktan birden fazla kez listeliyor (örn.
"GÜNCELLEME 1-Başlık" varyasyonları). `normalize_title_words` + `title_word_similarity`
ile bulanık eşleştirme yapılıyor: en az 2 ortak kelime VE oran ≥0.6, 48 saat penceresi.
`STOPWORDS_TR` içinde medya-kendine-referans kelimeler de var ("haber", "başlık" gibi).
Bu katman değişmedi.

### 2. Çapraz kaynak kümeleme — artık AI DOĞRULAMALI, build zamanında (Python, CI)

⚠️ **Mimari değişti (önemli):** Kümeleme kararının kendisi artık tarayıcıda (JS) değil,
build zamanında Python'da, Claude'un doğrulamasıyla veriliyor. Eskiden JS'de dinamik
`clusterItems`/`isSimilarTitle` sezgisel benzerlik hesaplıyordu (kelime oranı + özel isim
eşleşmesi, aşağıdaki evrim notlarına bak) — ama kullanıcı tekrar tekrar yanlış eşleştirme
("bu kartlarda hep bir hata var") bildirdi. Sezgisel kelime/özel-isim eşleştirmesi
temelden kusurlu: "aynı kelimeyi/kişiyi geçiyorlar" ile "aynı OLAYI anlatıyorlar" arasında
ayrım yapamıyor. Bu, tam olarak bir LLM'in iyi olduğu bir yargı işi.

**Yeni akış (`main()` içinde):**
1. `cluster_items_for_summary` (Python) hâlâ var ama artık NİHAİ karar değil, sadece
   ADAY grup üretiyor (eski sezgisel mantıkla — kelime oranı + özel isim + 36 saat
   penceresi, kasıtlı olarak gevşek/permissive).
2. `validate_and_summarize_clusters_with_ai` her aday grubu (title + source ile) TEK bir
   toplu API çağrısında Claude'a gönderiyor. Her grup için Claude: (a) o gruptaki
   başlıklardan HANGİLERİ gerçekten aynı spesifik olayı anlatıyor (`"keep"` — index
   listesi, sıfırdan başlar) belirliyor, (b) `keep` 2+ ise tarafsız bir özet cümlesi
   yazıyor. Yani AI hem kümeleme kararını DOĞRULUYOR (adaydan yanlış üyeleri atabiliyor)
   hem de özeti aynı anda üretiyor — iki ayrı adım değil.
3. Sonuç: her ogeye kalıcı bir `cluster_id` (int) ve varsa `ai_summary` ataniyor,
   `clusterId`/`aiSummary` olarak client'a gönderiliyor.
4. JS tarafında `clusterItems` artık SADECE bu `clusterId`'ye göre gruplama yapıyor —
   hiçbir benzerlik hesabı yok. Filtre/sekme değiştiğinde hâlâ dinamik olarak yeniden
   gruplanıyor (filtrelenmiş ögeler arasında hangi clusterId'ler hayatta kaldıysa onlara
   göre) ama HANGİ ögelerin aynı kümeye ait olduğu kararı artık sabit (build zamanında
   verildi, filtre değişince yeniden hesaplanmıyor).

**Eski sezgisel mantığın (adaylık için hâlâ kullanılan) geçirdiği evrim (tarihsel not):**
1. İlk hali: sadece kelime oranı → çok gevşekti, "su gibi" (Erdoğan metaforu) ile "yağış"
   haberini yanlış birleştirdi
2. Özel isim (büyük harf) tabanlı hale getirildi → bu sefer "Trump" gibi çok sık geçen bir
   isim, birbirinden tamamen alakasız Trump haberlerini (Çin ile / İrlanda ile) yanlış
   birleştirdi
3. Frekans eşiği eklendi (`COMMON_NAME_THRESHOLD`) → yaygın isimler tek başına yetmiyor,
   nadir isimler tek başına yetiyor
4. Bigram (iki kelimelik tam isim) önceliği eklendi
5. **Bu sezgisel adımlar hâlâ tamamen yanlış eşleştirmeleri engelleyemedi** (kullanıcı
   şikayeti) → AI doğrulama katmanı eklendi (yukarıdaki yeni akış). Sezgisel mantık artık
   sadece ADAY üretiyor, son sözü Claude söylüyor.

**Fallback (AI mevcut değilse veya çağrı başarısız olursa):** Sezgisel aday gruplar
DOĞRULANMADAN, oldukları gibi `cluster_id` alıyor (eski davranışla birebir aynı sonuç) —
hiçbir şey kırılmıyor, sadece kalite eskiye döner. Yerelde (`ANTHROPIC_API_KEY` yok) hep bu
yola düşülür; local dev testi için yeterli.

**Aynı sourceId'den gelen haberler asla aynı kümede birleşmiyor** (farklı kaynakların aynı
olayı yazmasını kümelemek amaç, tek kaynağın kendi tekrarını değil — o zaten katman 1'de
temizleniyor). Bu kural hem aday üretiminde hem AI promptunda geçerli.

`extract_proper_nouns`: artık SADECE Python'da var (JS'deki paralel kopyası
`extractProperNouns` silindi -- JS artık kümeleme mantığı taşımıyor, "ikisini birden
güncellemeyi unutma" derdi ortadan kalktı).

⚠️ **Oyunlar sekmesinde kümeleme tamamen kapalı** — kullanıcı özellikle istedi. Python
tarafında da sadece `category == "haber"` ogeleri aday kümelemeye sokuluyor (oyun ogeleri
hiç AI'a gönderilmiyor, gereksiz maliyet yok).

## AI özet + kümeleme doğrulama (Claude Haiku)

Sadece aday kümelenmiş (2+ kaynaklı, sezgisel) haberler için, TEK bir toplu API çağrısında
(maliyet/hız için — her aday grup için ayrı çağrı değil) `claude-haiku-4-5-20251001`
modeline gönderiliyor. Bu tek çağrı hem kümeleme doğrulamasını hem özeti üretiyor (bkz.
yukarıdaki "Çapraz kaynak kümeleme" bölümü).

- `ANTHROPIC_API_KEY` GitHub Secret olarak saklı, sadece CI'da kullanılıyor (client-side'a
  ASLA sızmamalı — bu güvenlik açısından kritik, API anahtarını client JS'e gömmek olmaz)
- Anahtar yoksa veya API başarısız olursa: sessizce sezgisel aday kümeler doğrulanmadan
  kullanılır (`ai_summary` atanmaz, kart başlığında kümedeki en kısa/en sade başlık
  gösterilir) — hiçbir şey kırılmaz
- Kart başlığında AI özeti varsa o gösterilir, yoksa kümedeki en kısa/en sade başlık

## Görseller

Üç katmanlı sistem, öncelik sırasıyla:

1. **RSS'in kendi verdiği görsel** (BBC, Steam feed'leri gerçek görsel veriyor)
2. **Wikipedia REST API** (`fetch_entity_image` / `fetch_wikipedia_thumbnail`) — ücretsiz,
   anahtarsız. Başlıktaki özel isimlerden (bigram öncelikli) Wikipedia'da arama yapılıyor,
   `originalimage.source` (TAM çözünürlük) tercih ediliyor. Bulunamazsa `opensearch` API'siyle
   bulanık arama denenir. Oyun kaynakları için kaynak başına TEK sorgu (`GAME_WIKI_TITLES`
   ile cache'lenir, makale başına değil).
3. **Placeholder monogram** (`make_placeholder_image`) — SVG, sabit koyu gri zemin (`#2B2B2B`)
   + baş harfi (kaynak rengi YOK, site siyah-beyaza geçtiğinde kaldırıldı), kart oranına
   (2.2:1) eşit viewBox, harf üstte/soluk (metnin oturacağı alt kısmı boş bırakır). Sabit gri
   kullanılıyor çünkü bu SVG data URI olarak gömülü, sayfanın light/dark CSS değişkenlerine
   erişemiyor.

⚠️ **Denenip vazgeçilen yöntem:** `og:image` meta etiketini makale sayfasından kazımak —
hem yavaştı hem güvenilmez çıktı (Google News ara yönlendirme sayfaları yüzünden). Bu yola
GERİ DÖNÜLMEMELİ, kullanıcı açıkça "bu yol çalışmıyor, başka yönteme geçmemiz şart" dedi.

⚠️ **`originalimage` vs `thumbnail`:** İlk denemede sadece `thumbnail.source` kullanılmıştı
ve URL'deki "NNNpx-" kısmını büyütme numarası (`upsize_thumbnail_url`) yeterli olmadı,
görseller hâlâ bulanıktı. Gerçek çözüm: API'nin verdiği `originalimage.source` alanını
DOĞRUDAN kullanmak (tam çözünürlük, hiç URL numarası oynamaya gerek yok).

### Kart üstü metin okunabilirliği

Görsel üstte (2.2:1), altında koyu gradient + başlık overlay (sol alt). Görselin alt %45'inin
ortalama parlaklığı canvas ile ölçülüp (`sampleImageBrightness`) 165 eşiğine göre metin
rengi otomatik siyah/beyaz seçiliyor (`.overlay.on-light` class'ı).

⚠️ **`crossorigin="anonymous"` GÖRÜNEN `<img class="thumb">` üzerinde OLMAMALI.** Önceki
hali görünen img'e `crossorigin="anonymous"` koyuyordu (canvas okuma için gerekli sanılmıştı)
+ `onerror="this.remove();"`. Bu, CORS header'ı göndermeyen HERHANGİ bir sunucudan (CNN
Türk'ün CDN'i böyle çıktı, canlıda bulundu -- kullanıcı "site bozuk" diye bildirdi) gelen
görseli TAMAMEN reddetmesine sebep oluyordu (crossorigin=anonymous, sadece canvas okumayı
değil, tarayıcının görseli hiç göstermesini de CORS'a bağlıyor). `onerror` görseli DOM'dan
siliyordu, `.media` div'inin tek normal-flow içeriği o img olduğu için yükseklik 0'a
düşüyordu, kart çöküyordu -- 25 karttan 15'i bu şekilde bozulmuştu.

**Düzeltme:** Görünen img artık `crossorigin` TAŞIMIYOR (her zaman normal `<img>` gibi
yükleniyor, CORS header'ı olsun olmasın). Parlaklık ölçümü için `applyOverlayContrast`
içinde AYRI, DOM'a hiç eklenmeyen bir "probe" `Image()` oluşturuluyor -- SADECE bu probe
`crossOrigin='anonymous'` taşıyor. Probe CORS'a takılırsa (nadir, Wikipedia genelde izin
verir) sessizce varsayılana (koyu zemin varsayımı, açık metin) düşülüyor ama görünen görseli
hiç etkilemiyor. Yeni bir görsel-ilişkili degisiklik yaparken görünen `<img>`'e ASLA
`crossorigin` ekleme.

## Sekmeler ve state yönetimi

**"Haberler" / "Oyunlar"** iki bağımsız sekme. Her ikisi de kendi filtre state'ine sahip
(ayrı localStorage anahtarları: `sakinakis_hide_haber` vs `sakinakis_hide_oyun` gibi —
sekmeye göre dinamik key üreten `hideStorageKey()` fonksiyonlarına bak). Bunu SEKME
BAĞIMSIZ tutmayı unutma, bir önceki hata buydu (kutular paylaşılıyordu).

**Oyunlar sekmesinde de kaynak toggle'ı VAR ama Haberler'den FARKLI** -- 11 ayrı oyun
yerine 3 GRUP butonu (`OYUN_SOURCE_GROUPS`): "Riot Games" (valorant/lol/tft), "Steam"
(deadlock/bodycam/zomboid/r6siege/cs2/dota2), "Diğer" (minecraft/game_news). Bir gruba
tıklamak o gruptaki TÜM sourceId'leri birlikte `activeSources`'a ekler/çıkarır -- alttaki
filtre mekanizması (`activeSources.has(it.sourceId)`) Haberler ile birebir aynı, sadece
Oyunlar'da UI'da gruplu gösteriliyor. Başta (tek tek kaynaklar da dahil) tamamen
kaldırılmıştı ("kategoriler kaldırılsın, hepsi gösterilsin"), sonra Riot Games sorguları
patch notes'a daraltılınca (bkz. yukarısı) bu kaynaklar 879 oyun haberi içinde ~23 taneye
düşüp kayboldu -- kullanıcı önce Haberler'deki gibi tek tek kaynak listesi istedi, sonra
11 buton fazla geldi, 3 gruba indirgendi. Varsayılan KAPALI (genişlet düğmesiyle açılıyor,
`sourcesExpanded` state, her iki sekmede ortak).

**Haberler sekmesinde kaynak listesi de ikiye bölünüyor:** "Türkçe kaynaklar" / "Yabancı
kaynaklar" (`L.sourcesLangTr` / `L.sourcesLangForeign`) alt başlıkları altında, ama
Oyunlar'ın aksine kaynaklar GRUPLANMIYOR -- her kaynak hâlâ kendi ayrı toggle butonu,
sadece iki başlık altında sıralanıyor (tek tek acma/kapama kontrolü korunuyor). Her
kaynağın Python tarafında `SOURCES` içinde `"lang": "tr"` veya `"lang": "en"` alanı var
(`sources_meta` ile JS'e geçiyor); `buildSourceToggles` bu alana göre iki grup render
ediyor (CSS: `.sources-subgroup-label{{flex-basis:100%}}` ile ayni flex-wrap konteyner
icinde satir kaydiriyor, ekstra wrapper div yok). 23 kaynaktan 15'i Türkçe (BBC Türkçe ve
DW Türkçe dahil -- bunlar yabancı kuruluşların Türkçe yayını ama dil/hedef kitleye göre
Türkçe grubuna kondu), 8'i yabancı (Reuters, AP, BBC EN, Al Jazeera English, Guardian,
Euronews, NPR, The Economist).

**Konu chip'leri (`TOPIC_SYNONYMS`, `TOPIC_KEYS_BY_TAB`):** Sekmeye göre farklı chip seti.
- Haberler: Futbol, Spor, Ekonomi, Siyaset, Magazin, Teknoloji
- Oyunlar: Güncelleme Notları (`patchnotes`), Diğer (`digeroyun` — turnuva+yeni içerik+indirim
  kelimelerinin birleşimi)

Chip'e tıklamak, o anahtar kelimeyi gizle/sadece-göster/önemli kutusuna yazar (mevcut metin
tabanlı filtre mekanizmasını kullanır, ayrı bir sistem değil).

## localStorage anahtarları (hepsi `sakinakis_` önekli)

`lang`, `theme`, `hide_{tab}`, `only_{tab}`, `important_{tab}`, `sources`, `sortmode`, `tab`,
`seen`

## Diğer önemli özellikler

- **"Gördüm" işaretleme:** Göz ikonu tıklanınca kümenin TÜM üyeleri birlikte işaretlenir
  (tek bir link değil), kart listenin en altına iner, localStorage'da kalıcı, tekrar
  tıklayınca geri alınabilir.
- **Sayfalama:** 25 küme/sayfa, Başa Dön/Önceki/Sonraki/Sona Git. Filtre/sekme/sıralama
  değişince sayfa 1'e döner.
- **Sıralama modları:** Kronolojik (varsayılan) / Önem sırasına göre (kapsam sayısı +
  "önemli" kutusundaki kelime eşleşmesi).
- **Dark mode varsayılan**, `:root` dark değerleri tutuyor, `html.light` class'ı override
  ediyor. Dil düğmesinin yanında ☀/☾ ile geçiş, localStorage'da kalıcı.
- **Tema tamamen siyah-beyaz (monokrom).** Kullanıcı kaynak renklerini kaldırttıktan hemen
  sonra tüm temayı da siyah-beyaza çevirtti. `:root` (dark): `--paper:#000000` (saf siyah,
  "black is heavier" dendi), `--ink:#FFFFFF`. `html.light`: `--paper:#FFFFFF`,
  `--ink:#000000` — dark modun tam tersi. `--accent` artık ayrı bir renk değil, `--ink` ile
  aynı deger (dark'ta beyaz, light'ta siyah) — eskiden turuncu/kiremit tonuydu. Kart üstü
  overlay gradyanı ve metni de (`--paper`/`--ink`'ten bağımsız, sabit hardcode) saf
  siyah/beyaza çevrildi (`rgba(0,0,0,...)` / `rgba(255,255,255,...)`), favicon da aynı
  şekilde. Yeni bir renk/hex eklerken bu kısıtı unutma — hiçbir yerde renkli (hue'lu) bir
  ton olmamalı, sadece siyah/beyaz/gri.
- **Türkçe karakterler:** Tüm arayüz gerçek Türkçe alfabeyle (ş,ı,ğ,ü,ö,ç) — "Sakin Akis"
  değil "Sakin Akış" gibi. Yeni metin eklerken buna dikkat et.
- Tarih gösterimi: hem göreceli ("3sa", "2g") hem mutlak ("14 Eyl") birlikte gösteriliyor.
- Küme kaynak listesi (bir kartın "diğer kaynaklar bunu nasıl yazdı" listesi) varsayılan
  KAPALI, "N kaynakta daha oku" düğmesiyle açılıyor.

## GitHub Actions kurulumu

`.github/workflows/build.yml`:
- Tetikleyiciler: `cron: "0 * * * *"` (saatte bir), `workflow_dispatch` (elle), `push` (main)
- `ANTHROPIC_API_KEY` secret olarak Settings → Secrets and variables → Actions altında
- Pages source: "GitHub Actions" (branch değil!)
- `actions/upload-pages-artifact` + `actions/deploy-pages` ile modern deploy yöntemi

## Test yaklaşımı (Claude Code'un bilmesi gereken)

Bu proje boyunca değişiklikler şöyle doğrulandı (gerçek network erişimi sandbox'ta yok):
- `python3 -m py_compile` ile söz dizimi kontrolü
- Python fonksiyonları mock'lanmış `urllib.request.urlopen` ile test edildi
- JS mantığı **jsdom** ile gerçek DOM/tıklama senaryoları simüle edilerek test edildi
  (`npm install jsdom` gerekiyor, kalıcı değil her seferinde kurulabilir)
- Canvas/piksel analizi için `npm install canvas` (native derleme gerektirir ama bu ortamda
  çalıştı) kullanılıp gerçek RGB verisiyle parlaklık testi yapıldı
- Wikipedia API format varsayımları web search ile resmi dokümantasyondan doğrulandı (ilk
  seferde yanlış varsayılmıştı, `originalimage` alanı gözden kaçmıştı — dikkatli ol,
  üçüncü parti API'lerin gerçek response formatını varsaymadan önce doğrula)

**Gerçek prod ortamında (gerçek RSS feed'leri, gerçek Wikipedia sorguları, gerçek GitHub
Actions run'ı) hiçbir şey Claude tarafından uçtan uca test edilmedi** — kullanıcı her
değişiklikten sonra GitHub'a push edip Actions'ı çalıştırarak kendisi doğruluyor. Bu
döngüde birkaç kez ("görsel gelmiyor", "hâlâ bulanık" gibi) geri bildirimle iyileştirme
yapıldı. Yeni bir değişiklik yaparken bu geri bildirim döngüsünü göz önünde bulundur —
iddialı olma, "büyük ihtimalle çalışır" de, kesin "çalışıyor" deme.

## Mevcut iş akışı (Claude Code ile değişecek olan kısım)

Şu ana kadar: Claude (bu sohbet) dosyayı düzenliyor → kullanıcıya tam `sakin_akis.py`
veriliyor → kullanıcı GitHub'a elle yükleyip eskisinin üzerine yazıyor ("Replace") →
Actions sekmesinden workflow'u elle tetikliyor. Kullanıcının Claude Code Pro planı yok,
bu yüzden şu ana kadar gerçek repo erişimi hiç olmadı. Claude Code ile bu değişecek:
repoyu klonlayıp doğrudan commit/push yapılabilir hale gelecek.

## Bilinen sınırlamalar / gözden geçirilmesi gerekenler

- Bazı haberler için Wikipedia'da eşleşme bulunamayabilir (soyut/genel konular) — bu normal,
  placeholder'a düşer
- Canvas brightness analizi teorik olarak CORS engeline takılabilir (Wikipedia genelde
  izin veriyor ama garanti değil)
- `game_news` (genel oyun haberleri) kaynağı Google News'in geniş bir sorgusu, gürültülü
  olabilir, zamanla daraltma gerekebilir
