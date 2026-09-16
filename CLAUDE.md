# CLAUDE.md — Sakin Akış

Bu dosya, Claude Code'un bu proje üzerinde çalışırken ihtiyaç duyacağı bağlamı içerir.

## Proje nedir, neden var

Kullanıcı X (Twitter)'ı taraflı/anlamsız/toxic ragebait içerik yüzünden kullanmayı bıraktı ve
kendi haber takip aracını yaptı: **Sakin Akış**. Amaç: algoritma yok, reklam yok, kronolojik
sıra, kullanıcı kontrolünde filtreleme. "Sakin" isim/marka kimliği ciddiye alınmalı — her
yeni özellik bu sakinlik felsefesine (gürültü azaltma, kullanıcı kontrolü, şeffaflık) uygun
olmalı.

⚠️ **Tek sekme, tek akış.** Başta "Haberler" / "Oyunlar" diye iki ayrı sekme vardı (oyun
sekmesinde tek tek oyunların yama notları takip ediliyordu). Kullanıcı sonradan Oyunlar
sekmesini TAMAMEN kaldırttı: yama notu takibi bitti, bunun yerine büyük oyun sektörü
haberleri (büyük oyun çıkışları, fragmanlar, Game Awards gibi büyük etkinlikler) normal
haber akışına bir KAYNAK olarak karıştı (bkz. "Oyun Dünyası" aşağıda). Artık `category`
alanı her zaman `"haber"` -- `"oyun"` kategorisi yok, sekme UI'ı yok, `currentTab` sabit
`"haber"`.

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

Tek kategori: her kaynağın `category` alanı hep `"haber"`. Her kaynağın `id`, `name`,
`category`, `lang` (`"tr"`/`"en"`, kaynak listesinde "Türkçe kaynaklar"/"Yabancı kaynaklar"
bölmesi için), `rss` (URL) alanları var. Eskiden bir de `color` (hex, marka rengi) alanı
vardı -- kaynak toggle'larındaki, kart üstündeki ve kümedeki swatch noktalarında
kullanılıyordu; kullanıcı "gerek yok" deyip kaldırttı, aynı anda site tamamen siyah-beyaza
geçti (bkz. "Tema").

**Kaynaklar (24):** Reuters, AP, BBC (EN), BBC Türkçe, Cumhuriyet, Bianet, TRT Haber,
Anadolu Ajansı, Sözcü, Habertürk, NTV, Hürriyet, Sabah, Halk TV, T24, DW Türkçe,
Al Jazeera English, The Guardian, Euronews, NPR, CNN Türk, Yeni Şafak, The Economist,
**Oyun Dünyası** — ilk 23'ü bilinçli olarak siyasi yelpazede dengeli (devlet: TRT/AA;
pro-hükümet: Sabah/Habertürk/Yeni Şafak/CNN Türk; muhalefet: Sözcü/Cumhuriyet/Halk TV;
bağımsız: Bianet/T24/Hürriyet; uluslararası: Reuters/AP/BBC/Al Jazeera/Guardian/Euronews/
NPR/DW/Economist), kullanıcı açıkça bunu istedi. 9'dan 22'ye genişletildi -- kullanıcı
"büyük kaynakların hepsi olsun" dedi, TR + İngilizce/uluslararası karışımı özellikle
istendi. Sonra The Economist eklendi (23'te durulacaktı, bilinçli bir sınır), sonra
Oyunlar sekmesi kaldırılınca yerine "Oyun Dünyası" (24.) eklendi.

**"Oyun Dünyası"** (`id: oyun_dunyasi`, `lang: en`) — Oyunlar sekmesi kaldırılınca eklendi.
Eski Riot Games/Steam yama notu takibinin YERİNE GEÇMİYOR (o tamamen bitti) -- bunun yerine
büyük oyun sektörü haberlerini (büyük oyun çıkışları, yeni fragmanlar, Game Awards gibi
büyük etkinlikler) normal Haberler akışına bir kaynak olarak katıyor. Sorgu:
`("official trailer" OR "release date" OR "game awards" OR "goty") game -"Hunger Games"
when:4d`. Canlı test edilerek kalibre edildi (birkaç sürüm denendi -- ilk hali spor/film
gürültüsü içeriyordu, `-"Hunger Games"` filmi dışlamak icin eklendi çünkü başlığında "Games"
geçiyor ve genel "trailer" sorgusuna yanlışlıkla giriyordu).

⚠️ **Kaynak adı çevirisi istisnası.** Diğer TÜM kaynak adları gerçek marka/yayın adı
olduğu için dile göre hiç değişmiyor (Reuters İngilizce modda da "Reuters"). "Oyun
Dünyası" gerçek bir yayın adı değil, bizim uydurduğumuz bir kategori etiketi -- İngilizce
modda "Oyun Dünyası" görünmesi kullanıcı tarafından hata olarak bildirildi. Düzeltme: JS'de
`SOURCE_NAME_OVERRIDES` (sourceId → {{tr, en}}) + `sourceDisplayName(sourceId, fallback)`
helper'ı eklendi, `lang`'a göre çeviriyor, override yoksa `fallback`'e (SOURCES'taki sabit
ad) düşüyor. Item verisi build zamanında sabit bir "source" string'i taşıdığı için (dile
göre değişmiyor), bu helper HER YERDE kullanılmalı: kaynak toggle butonu
(`buildSourceToggles`), tekil kart meta satırı (`newest.source`), küme kaynak listesi
(`m.source`). Yeni bir kategori-etiketi kaynak eklersen (gerçek bir yayın değilse)
`SOURCE_NAME_OVERRIDES`'a ekle, `s.name`/`.source`'u doğrudan render etme.

**RSS kaynak stratejisi:**
- Kendi RSS'i olan (BBC, Habertürk, NTV, Hürriyet, Sabah, Halk TV, Al Jazeera English,
  The Guardian, Euronews, NPR, CNN Türk, Yeni Şafak) → direkt kullanılıyor
- Geri kalan HERKES (Reuters, AP, Cumhuriyet, Bianet, TRT, AA, Sözcü, T24, DW Türkçe,
  Oyun Dünyası) → Google News search RSS (`news.google.com/rss/search?q=...`) çünkü ya
  resmi RSS'leri yok ya da denendi/kırık çıktı (T24'ün `/rss` yolu 404 dönüyor; DW
  Türkçe'nin resmi feed'i RSS 1.0/RDF formatında, parser'ın desteklemediği format —
  Google News fallback'e düşürüldü)

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

⚠️ **Riot Games/Steam yama notu takibi (Valorant/LoL/TFT/Deadlock/Bodycam/Zomboid/R6/CS2/
Dota2/Minecraft) TAMAMEN KALDIRILDI.** Bir süre per-oyun patch notes takibi vardı (özel
Google News sorguları, `GAME_WIKI_TITLES` ile Wikipedia kapak görselleri, `OYUN_SOURCE_GROUPS`
ile "Riot Games"/"Steam"/"Diğer" gruplu kaynak toggle'ları) ama kullanıcı Oyunlar sekmesini
tamamen kaldırttı: "yama notu artık olmayacak", yerine genel oyun sektörü haberi geldi (bkz.
yukarıda "Oyun Dünyası"). Eğer eski bir commit'te `GAME_WIKI_TITLES`, `OYUN_SOURCE_GROUPS`,
`isSimilarTitle`'ın oyun-özel kullanımı gibi şeyler görürsen, bunlar kasıtlı olarak silindi
-- geri getirme, kullanıcı bunu istemiyor.

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
2. `validate_and_summarize_clusters_with_ai` her aday grubu (title + source ile) Claude'a
   gönderiyor. Her grup için Claude: (a) o gruptaki başlıklardan HANGİLERİ gerçekten aynı
   spesifik olayı anlatıyor (`"keep"` — index listesi, sıfırdan başlar) belirliyor, (b)
   `keep` 2+ ise tarafsız bir özet cümlesi yazıyor. Yani AI hem kümeleme kararını
   DOĞRULUYOR (adaydan yanlış üyeleri atabiliyor) hem de özeti aynı anda üretiyor — iki
   ayrı adım değil.

   ⚠️ **TEK dev API çağrısı değil, `CLUSTER_VALIDATION_BATCH_SIZE` (25) boyutunda
   batch'ler.** İlk hali tüm adayları (canlıda 209 grup) TEK çağrıda gönderiyordu --
   çağrı başarıyla dönüyordu ama Claude'un cevabı giriş grup sayısıyla EŞLEŞMİYORDU
   (muhtemelen bu kadar uzun bir listede pozisyon-birebir eşlemeyi tam koruyamıyor).
   Kullanıcı canlı CI log'unu paylaşıp doğruladı: `"[AI kumeleme uyarisi] beklenmeyen
   format..."`. Çözüm: adaylar 25'erlik gruplar halinde ayrı çağrılarla gönderiliyor
   (~209 grup için ~9 çağrı, ek maliyet ihmal edilebilir -- sabit prompt talimatı
   tekrarı birkaç bin token). Bir batch başarısız olursa SADECE o batch'in grupları
   sezgisel/doğrulanmamış kalıyor (`None` olarak işaretlenir), diğer batch'lerin gerçek
   AI sonucu kaybolmuyor -- eskiden tek batch hatası TÜM build'i doğrulamasız
   bırakıyordu, artık kısmi başarı korunuyor. `_validate_cluster_batch` tek bir batch'in
   ham API çağrısını yapar; `validate_and_summarize_clusters_with_ai` bunu döngüyle
   çağırıp sonuçları birleştirir.
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

Not: `category == "haber"` filtresi hâlâ Python'da duruyor (`haber_items = [...]`) ama
artık no-op -- tüm SOURCES ögeleri zaten `"haber"`, Oyunlar kategorisi silindiğinden beri
başka değer yok.

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

1. **RSS'in kendi verdiği görsel** (BBC, Habertürk, NTV, Hürriyet vb. kendi RSS'i olan
   kaynaklar gerçek görsel veriyor -- bkz. "Atom format bug'ı" notları)
2. **Wikipedia REST API** (`fetch_entity_image` / `fetch_wikipedia_thumbnail`) — ücretsiz,
   anahtarsız. Başlıktaki özel isimlerden (bigram öncelikli) Wikipedia'da arama yapılıyor,
   `originalimage.source` (TAM çözünürlük) tercih ediliyor. Bulunamazsa `opensearch` API'siyle
   bulanık arama denenir. (Eskiden oyun kaynakları için kaynak başına TEK sorguyla
   cache'lenen `GAME_WIKI_TITLES` vardı -- Oyunlar sekmesiyle birlikte silindi.)
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

## Sekme yok, tek akış, state yönetimi

⚠️ **Sekme UI'ı tamamen kaldırıldı.** Eskiden "Haberler" / "Oyunlar" iki bağımsız sekme
vardı (`buildTabs()`, `.tabs`/`.tab-btn` CSS, `<div class="tabs" id="mainTabs">`, sekmeye
göre gruplu kaynak toggle'ı). Oyunlar sekmesi kullanıcı isteğiyle tamamen kaldırılınca artık
tek sekme kalmadığı için sekme değiştirme UI'ının kendisi de anlamsızlaşıp silindi.
`currentTab` değişkeni JS'de hâlâ var (kod tabanında minimum değişiklik için) ama artık
SABİT `"haber"` -- hiçbir yerde değişmiyor, `buildTabs()`/`loadFilterInputsForTab()`/
`sakinakis_tab` localStorage anahtarı gibi onu değiştiren her şey silindi. Bu yüzden
`hideStorageKey()` gibi fonksiyonlar hâlâ `currentTab`'a göre key üretiyor ama pratikte
hep aynı sabit key'i döndürüyorlar (`sakinakis_hide_haber` vb.) -- kasıtlı, kullanıcının
eski localStorage verisiyle uyumluluk için böyle bırakıldı, silmeye gerek yok.

**Kaynak listesi ikiye bölünüyor:** "Türkçe kaynaklar" / "Yabancı kaynaklar"
(`L.sourcesLangTr` / `L.sourcesLangForeign`) alt başlıkları altında, her kaynak kendi ayrı
toggle butonu (gruplanmıyor -- eski Oyunlar sekmesinin 3-grup-buton yaklaşımı
(`OYUN_SOURCE_GROUPS`: "Riot Games"/"Steam"/"Diğer") o sekmeyle birlikte silindi). Her
kaynağın Python tarafında `SOURCES` içinde `"lang": "tr"` veya `"lang": "en"` alanı var
(`sources_meta` ile JS'e geçiyor); `buildSourceToggles` bu alana göre iki grup render ediyor
(CSS: `.sources-subgroup-label{{flex-basis:100%}}` ile ayni flex-wrap konteyner icinde satir
kaydiriyor, ekstra wrapper div yok). Varsayılan KAPALI (genişlet düğmesiyle açılıyor,
`sourcesExpanded` state). 24 kaynaktan 15'i Türkçe (BBC Türkçe ve DW Türkçe dahil -- bunlar
yabancı kuruluşların Türkçe yayını ama dil/hedef kitleye göre Türkçe grubuna kondu), 9'u
yabancı (Reuters, AP, BBC EN, Al Jazeera English, Guardian, Euronews, NPR, The Economist,
Oyun Dünyası).

**Konu chip'leri (`TOPIC_SYNONYMS`, `TOPIC_KEYS_BY_TAB`):** Futbol, Spor, Ekonomi, Siyaset,
Magazin, Teknoloji. (Eskiden Oyunlar sekmesine özel "Güncelleme Notları"/`patchnotes` ve
"Diğer"/`digeroyun` chip'leri de vardı, sekmeyle birlikte silindi.)

Chip'e tıklamak, o anahtar kelimeyi gizle/sadece-göster/önemli kutusuna yazar (mevcut metin
tabanlı filtre mekanizmasını kullanır, ayrı bir sistem değil).

## localStorage anahtarları (hepsi `sakinakis_` önekli)

`lang`, `theme`, `hide_haber` (fonksiyon adı hâlâ `hideStorageKey()`, `{{tab}}` yer tutucusu
artık hep `haber`), `only_haber`, `important_haber`, `sources`, `sortmode`, `seen`.
`tab` artık YOK (sekme kaldırılınca silindi).

## Diğer önemli özellikler

- **"Gördüm" işaretleme:** Göz ikonu tıklanınca kümenin TÜM üyeleri birlikte işaretlenir
  (tek bir link değil), kart listenin en altına iner, localStorage'da kalıcı, tekrar
  tıklayınca geri alınabilir.
  ⚠️ **`isClusterSeen` `every` değil `some` kullanmalı.** Kümeler build'ler arasında
  SABİT değil -- her 6 saatte bir yeniden kümeleniyor, bu yüzden "gördüm" işaretlenen
  2-kaynaklı bir haber sonraki build'de 3. bir kaynak kazanabilir. `every` kullanmak
  (eski hali), o hiç görülmemiş yeni üyeyi içeren kümeyi TÜMDEN "görülmemiş"e geri
  düşürüyordu -- kullanıcı "işaretlediğim şey geri geliyor" diye bildirdi, localStorage
  kalıcılığının kendisi bozuk DEĞİLDİ (canlı sitede doğrulandı: fresh reload sonrası
  `seenLinks` doğru geri yükleniyor). `some` ile kümenin herhangi bir önceki halini
  görmüş olmak yeterli; tamamen yeni bir küme (hiç örtüşme yok) hâlâ "görülmemiş"
  sayılır. Simüle edilerek doğrulandı (gerçek DATA'dan bir kümeye sahte yeni üye
  eklenip `every` vs `some` karşılaştırıldı).
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
- Tetikleyiciler: `cron: "0 */6 * * *"` (6 saatte bir -- eskiden saatlikti, AI kümeleme
  doğrulaması eklenince (Claude Haiku, her build'de gerçek ücret) RSS pencereleri
  (`when:3d` vb.) büyük ölçüde örtüştüğü için saatlik çalıştırmak aynı adayları sürekli
  tekrar faturalandırıyordu (~$35/ay). 6 saatte bir ile ~$0.20/gün, $5 kredi ~1 ay
  yetiyor -- kullanıcının bilinçli tercihi), `workflow_dispatch` (elle), `push` (main)
- `ANTHROPIC_API_KEY` secret olarak Settings → Secrets and variables → Actions altında
  -- kullanıcı henüz satın almadı (bu proje AI kümeleme doğrulaması eklenene kadar
  gerek yoktu), $5 kredi ile başlıyor
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
- "Oyun Dünyası" kaynağı Google News'in bir sorgusu, canlıda tek seferlik kontrol edildi
  (temiz çıktı, bkz. yukarıda) ama uzun vadede gürültü artarsa sorgu tekrar ayarlanabilir
- AI kümeleme doğrulaması (`validate_and_summarize_clusters_with_ai`) ~25'lik batch'ler
  halinde çalışıyor ama ara sıra tek bir batch başarısız olabiliyor (canlıda görüldü, 9
  batch'ten 1'i) -- kullanıcı birkaç build boyunca izlemeyi istedi, düzeni bir kalıp
  oluşturuyorsa (sürekli aynı batch pozisyonu vb.) daha derin araştırma gerekebilir
