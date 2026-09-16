#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sakin Akış - algoritmasız, kronolojik haber okuyucu.

Bu script bilgisayarından doğrudan RSS kaynaklarına bağlanır
(tarayıcı sandbox'ı değil, senin gerçek internet bağlantın),
haberleri zaman sırasına göre bir HTML sayfasında toplar ve
otomatik olarak tarayıcıda açar.

Kullanım:
    python sakin_akis.py

Sadece Python'un kendi kütüphaneleri kullanılır, ek kurulum (pip) gerekmez.
"""

import urllib.request
import urllib.parse
import ssl
import re
import json
import base64
import concurrent.futures
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import webbrowser
import os
import sys

SOURCES = [
    {"id": "reuters", "name": "Reuters", "category": "haber", "lang": "en",
     "rss": "https://news.google.com/rss/search?q=site:reuters.com+when:3d&hl=en-US&gl=US&ceid=US:en"},
    {"id": "ap", "name": "AP", "category": "haber", "lang": "en",
     "rss": "https://news.google.com/rss/search?q=site:apnews.com+when:3d&hl=en-US&gl=US&ceid=US:en"},
    {"id": "bbc_en", "name": "BBC (EN)", "category": "haber", "lang": "en",
     "rss": "http://feeds.bbci.co.uk/news/world/rss.xml"},
    {"id": "bbc_tr", "name": "BBC Türkçe", "category": "haber", "lang": "tr",
     "rss": "https://feeds.bbci.co.uk/turkce/rss.xml"},
    {"id": "cumhuriyet", "name": "Cumhuriyet", "category": "haber", "lang": "tr",
     "rss": "https://news.google.com/rss/search?q=site:cumhuriyet.com.tr+when:3d&hl=tr&gl=TR&ceid=TR:tr"},
    {"id": "bianet", "name": "Bianet", "category": "haber", "lang": "tr",
     "rss": "https://news.google.com/rss/search?q=site:bianet.org+when:3d&hl=tr&gl=TR&ceid=TR:tr"},
    {"id": "trt_haber", "name": "TRT Haber", "category": "haber", "lang": "tr",
     "rss": "https://news.google.com/rss/search?q=site:trthaber.com+when:3d&hl=tr&gl=TR&ceid=TR:tr"},
    {"id": "aa", "name": "Anadolu Ajansı", "category": "haber", "lang": "tr",
     "rss": "https://news.google.com/rss/search?q=site:aa.com.tr+when:3d&hl=tr&gl=TR&ceid=TR:tr"},
    {"id": "sozcu", "name": "Sözcü", "category": "haber", "lang": "tr",
     "rss": "https://news.google.com/rss/search?q=site:sozcu.com.tr+when:3d&hl=tr&gl=TR&ceid=TR:tr"},
    {"id": "haberturk", "name": "Habertürk", "category": "haber", "lang": "tr",
     "rss": "https://www.haberturk.com/rss"},
    {"id": "ntv", "name": "NTV", "category": "haber", "lang": "tr",
     "rss": "https://www.ntv.com.tr/gundem.rss"},
    {"id": "hurriyet", "name": "Hürriyet", "category": "haber", "lang": "tr",
     "rss": "https://www.hurriyet.com.tr/rss/anasayfa"},
    {"id": "sabah", "name": "Sabah", "category": "haber", "lang": "tr",
     "rss": "https://www.sabah.com.tr/rss/anasayfa.xml"},
    {"id": "halktv", "name": "Halk TV", "category": "haber", "lang": "tr",
     "rss": "https://halktv.com.tr/rss"},
    {"id": "t24", "name": "T24", "category": "haber", "lang": "tr",
     "rss": "https://news.google.com/rss/search?q=site:t24.com.tr+when:3d&hl=tr&gl=TR&ceid=TR:tr"},
    {"id": "dw_tr", "name": "DW Türkçe", "category": "haber", "lang": "tr",
     "rss": "https://news.google.com/rss/search?q=site:dw.com/tr+when:3d&hl=tr&gl=TR&ceid=TR:tr"},
    {"id": "aljazeera_en", "name": "Al Jazeera English", "category": "haber", "lang": "en",
     "rss": "https://www.aljazeera.com/xml/rss/all.xml"},
    {"id": "guardian", "name": "The Guardian", "category": "haber", "lang": "en",
     "rss": "https://www.theguardian.com/world/rss"},
    {"id": "euronews", "name": "Euronews", "category": "haber", "lang": "en",
     "rss": "https://www.euronews.com/rss?level=theme&name=news"},
    {"id": "npr", "name": "NPR", "category": "haber", "lang": "en",
     "rss": "https://feeds.npr.org/1001/rss.xml"},
    {"id": "cnnturk", "name": "CNN Türk", "category": "haber", "lang": "tr",
     "rss": "https://www.cnnturk.com/feed/rss/turkiye/news"},
    {"id": "yenisafak", "name": "Yeni Şafak", "category": "haber", "lang": "tr",
     "rss": "https://www.yenisafak.com/rss?xml=gundem"},
    {"id": "economist", "name": "The Economist", "category": "haber", "lang": "en",
     "rss": "https://www.economist.com/international/rss.xml"},
    {"id": "deadlock", "name": "Deadlock", "category": "oyun",
     "rss": "https://store.steampowered.com/feeds/news/app/1422450/?cc=us&l=english"},
    {"id": "bodycam", "name": "Bodycam", "category": "oyun",
     "rss": "https://store.steampowered.com/feeds/news/app/2406770/?cc=us&l=english"},
    {"id": "zomboid", "name": "Project Zomboid", "category": "oyun",
     "rss": "https://store.steampowered.com/feeds/news/app/108600/?cc=us&l=english"},
    {"id": "minecraft", "name": "Minecraft", "category": "oyun",
     "rss": "https://news.google.com/rss/search?q=minecraft+update+when:7d&hl=en-US&gl=US&ceid=US:en"},
    {"id": "tft", "name": "TFT", "category": "oyun",
     "rss": "https://news.google.com/rss/search?q=%22Teamfight+Tactics%22+%22patch+notes%22+when:14d&hl=en-US&gl=US&ceid=US:en"},
    {"id": "valorant", "name": "Valorant", "category": "oyun",
     "rss": "https://news.google.com/rss/search?q=%22VALORANT+Patch+Notes%22+site:playvalorant.com+-Archive+when:30d&hl=en-US&gl=US&ceid=US:en"},
    {"id": "lol", "name": "League of Legends", "category": "oyun",
     "rss": "https://news.google.com/rss/search?q=%22League+of+Legends%22+%22patch+notes%22+site:leagueoflegends.com+-%22Wild+Rift%22+when:14d&hl=en-US&gl=US&ceid=US:en"},
    {"id": "r6siege", "name": "Rainbow Six Siege", "category": "oyun",
     "rss": "https://store.steampowered.com/feeds/news/app/359550/?cc=us&l=english"},
    {"id": "cs2", "name": "Counter-Strike 2", "category": "oyun",
     "rss": "https://store.steampowered.com/feeds/news/app/730/?cc=us&l=english"},
    {"id": "dota2", "name": "Dota 2", "category": "oyun",
     "rss": "https://store.steampowered.com/feeds/news/app/570/?cc=us&l=english"},
    {"id": "game_news", "name": "Buyuk Oyun Haberleri", "category": "oyun",
     "rss": "https://news.google.com/rss/search?q=(trailer+OR+announcement+OR+reveal)+game+when:3d&hl=en-US&gl=US&ceid=US:en"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


def fetch_feed(url):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        return resp.read()


def parse_date(text):
    if not text:
        return None
    try:
        dt = parsedate_to_datetime(text)
    except Exception:
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except Exception:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


IMG_TAG_RE = None  # set below after import


def find_image_in_html(text):
    if not text:
        return None
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', text)
    return m.group(1) if m else None


def extract_entity_candidates(title):
    """Basliktaki BUYUK HARFLE baslayan kelimelerden Wikipedia adaylari
    cikarir. Once ardisik iki kelimelik tam isim adaylarini dener (orn.
    "Mansur Yavas") -- bunlar tek kelimeden cok daha isabetli eslesir.
    Ilk kelimede kesme isareti (ek) varsa bir sonrakiyle birlestirmiyoruz,
    cunku bu genelde farkli bir kisiye/varliga gecis anlamina gelir
    ("Erdogan'dan Mansur Yavas'a" -> Erdogan ile Mansur ayri kisiler)."""
    raw_words = title.split()
    parsed = []
    for w in raw_words:
        parts = re.split(r"['\u2019]", w, maxsplit=1)
        stem = re.sub(r"[^\w]", "", parts[0], flags=re.UNICODE)
        has_suffix = len(parts) > 1
        is_cap = len(stem) >= 3 and stem[0].isupper()
        parsed.append((stem, has_suffix, is_cap))

    candidates = []
    for i in range(len(parsed) - 1):
        stem1, suf1, cap1 = parsed[i]
        stem2, suf2, cap2 = parsed[i + 1]
        if cap1 and cap2 and not suf1:
            candidates.append(f"{stem1} {stem2}")

    singles = [stem for stem, suf, cap in parsed if cap]
    singles.sort(key=len, reverse=True)
    candidates.extend(singles)

    seen = set()
    unique = []
    for c in candidates:
        key = c.lower()
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


WIKIPEDIA_HEADERS = {
    "User-Agent": "SakinAkis/1.0 (kisisel haber okuyucu scripti; "
                  "https://github.com/olymei/sakin-akis)",
    "Accept": "application/json",
}

# Wikipedia varsayilan olarak kucuk (~320px) bir onizleme gorseli dondurur;
# bunu tam genislikte kartta gostermek bulaniklastirir. URL'deki genislik
# degerini (orn. ".../320px-Isim.jpg") daha buyuk bir sayiyla degistirip
# daha net bir versiyon istiyoruz.
THUMBNAIL_TARGET_WIDTH = 1400

# Kart 2.2:1 oranla ve en fazla 640px genislikte gosteriliyor. Bundan daha
# dar bir gorsel (orn. dikey portre fotograflar) object-fit:cover ile
# buyutulup bulaniklasir -- bu yuzden yeterince genis olmayan gorselleri
# reddedip bir sonraki adaya (ya da placeholder'a) dusuyoruz.
MIN_IMAGE_WIDTH = 500


def upsize_thumbnail_url(url):
    if not url:
        return url
    return re.sub(r"/(\d+)px-", f"/{THUMBNAIL_TARGET_WIDTH}px-", url)


# BBC'nin ichef CDN'i, URL yolundaki genislik degerini degistirerek ayni
# gorselin daha buyuk bir versiyonunu verir (orn. ".../standard/240/..." ->
# ".../standard/976/..."). RSS feed'i varsayilan olarak kucuk (240px) bir
# versiyon veriyor, kartta (max ~640px genislik) bulaniklasiyordu.
def upsize_bbc_thumbnail_url(url):
    if not url or "ichef.bbci.co.uk" not in url:
        return url
    return re.sub(r"/standard/\d+/", "/standard/976/", url)


def fetch_wikipedia_thumbnail(title, lang="tr"):
    """Wikipedia'nin ucretsiz, anahtar gerektirmeyen ozet API'sinden bir
    sayfanin kapak/tanitim gorselini ceker. Once ORIJINAL (tam cozunurluklu)
    gorseli tercih ediyoruz -- URL buyutme numarasindan (regex ile "NNNpx-"
    degistirmek) cok daha guvenilir, cunku API bize dogrudan orijinal
    dosyanin linkini veriyor. Cok dar (MIN_IMAGE_WIDTH altinda) gorseller
    kartta bulaniklastigi icin reddedilir. Sayfa yoksa veya uygun gorseli
    yoksa None doner."""
    try:
        safe_title = urllib.parse.quote(title.replace(" ", "_"))
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{safe_title}"
        req = urllib.request.Request(url, headers=WIKIPEDIA_HEADERS)
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=6, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        orig_info = data.get("originalimage") or {}
        if orig_info.get("source") and orig_info.get("width", 0) >= MIN_IMAGE_WIDTH:
            return orig_info["source"]
        thumb_info = data.get("thumbnail") or {}
        if thumb_info.get("source") and thumb_info.get("width", 0) >= MIN_IMAGE_WIDTH:
            return upsize_thumbnail_url(thumb_info["source"])
        return None
    except Exception:
        return None


def wikipedia_search_title(query, lang="tr"):
    """Tam baslik eslesmesi basarisiz olursa (orn. 'Merkez Bankasi' gibi
    kisaltilmis/kismi bir isim), Wikipedia'nin arama API'siyle en yakin
    gercek sayfa basligini bulur (bulanik eslesme)."""
    try:
        url = (
            f"https://{lang}.wikipedia.org/w/api.php?action=opensearch"
            f"&search={urllib.parse.quote(query)}&limit=1&namespace=0&format=json"
        )
        req = urllib.request.Request(url, headers=WIKIPEDIA_HEADERS)
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=6, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        titles = data[1] if len(data) > 1 else []
        return titles[0] if titles else None
    except Exception:
        return None


def fetch_entity_image(title):
    """Basliktaki ozel isim adaylarindan (once iki kelimelik tam isimler,
    sonra tekiller) ilk basarili Wikipedia gorselini bulur. Once Turkce,
    sonra Ingilizce Wikipedia denenir. Tam baslik eslesmesi basarisiz
    olursa, en iyi aday icin arama API'si ile bulanik eslesme denenir.
    Gercek makale fotografi degil ama ilgili ve gercek bir gorsel."""
    candidates = extract_entity_candidates(title)[:3]
    for candidate in candidates:
        for lang in ("tr", "en"):
            img = fetch_wikipedia_thumbnail(candidate, lang=lang)
            if img:
                return img

    if candidates:
        best = candidates[0]
        for lang in ("tr", "en"):
            found_title = wikipedia_search_title(best, lang=lang)
            if found_title:
                img = fetch_wikipedia_thumbnail(found_title, lang=lang)
                if img:
                    return img
    return None


# Oyun kaynaklari sabit bir konuya (oyunun kendisine) karsilik geldigi icin,
# her kaynak icin TEK BIR Wikipedia sorgusuyla (cache'lenerek) kapak gorseli
# alinip o kaynagin tum haberlerinde kullanilabilir -- makale basina sorgu
# gerekmez, cok daha hizli.
GAME_WIKI_TITLES = {
    "deadlock": "Deadlock (video game)",
    "bodycam": "Bodycam (video game)",
    "zomboid": "Project Zomboid",
    "minecraft": "Minecraft",
    "tft": "Teamfight Tactics",
    "valorant": "Valorant",
    "lol": "League of Legends",
    "r6siege": "Rainbow Six Siege",
    "cs2": "Counter-Strike 2",
    "dota2": "Dota 2",
}

# TFT'nin Wikipedia sayfasinda infobox gorseli yok (API None donuyor,
# dogrulandi), bu yuzden o tek kaynak icin Wikimedia Commons'taki resmi
# logo dosyasina dogrudan sabit bir yedek veriyoruz.
GAME_FALLBACK_IMAGES = {
    "tft": "https://upload.wikimedia.org/wikipedia/commons/1/1e/Teamfight_Tactics_logo.png",
}


def make_placeholder_image(source_name):
    """RSS'te gorsel gelmeyen (cogunlukla Google News uzerinden gelen) haberler
    icin aninda, network'e gitmeden bir monogram gorseli uretir: notr gri bir
    zemin + adin ilk harfi (siyah-beyaz tema, kaynak rengi yok). Kartin kendi
    oranina (2.2:1) esit bir viewBox kullanilir ki object-fit:cover kirpma
    yapmasin; harf ustte/soluk tutulur cunku kartin alt kismi baslik yazisi
    icin ayrilmis. Bu SVG data URI olarak gomulu oldugu icin sayfanin
    light/dark tema degiskenlerine erisemiyor -- bu yuzden sabit bir gri ton
    kullanilir, ikisinde de okunabilir."""
    letter = (source_name.strip()[0].upper() if source_name.strip() else "?")
    letter = letter.replace("&", "&amp;").replace("<", "&lt;")
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 100">'
        f'<rect width="220" height="100" fill="#2B2B2B"/>'
        f'<text x="110" y="40" font-family="Georgia, serif" font-size="34" '
        f'font-weight="600" fill="#FFFFFF" fill-opacity="0.55" text-anchor="middle" '
        f'dominant-baseline="middle">{letter}</text>'
        f'</svg>'
    )
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


STOPWORDS_TR = {
    "icin", "ile", "oldu", "olan", "yeni", "diye", "gibi", "kadar", "sonra", "once",
    "daha", "cok", "yer", "aldi", "etti", "yapti", "dedi", "ancak", "fakat", "ama",
    "veya", "iken", "uzere", "var", "bir", "bu", "su", "da", "de", "ki", "mi", "mu",
    "ne", "nin", "nun", "tan", "ten", "dan", "den", "the", "and", "for", "with",
    "from", "that", "this", "have", "has", "was", "were", "been", "will", "says",
    "said", "after", "before", "over", "into", "about", "their", "they", "what",
    "when", "update", "guncelleme", "guncellendi", "haber", "haberi", "haberler",
    "basligi", "baslik", "manset", "aciklamasi", "aciklama",
}


def normalize_title_words(title):
    text = re.sub(r"[^\w\s]", " ", title.lower(), flags=re.UNICODE)
    return {w for w in text.split() if len(w) >= 3 and w not in STOPWORDS_TR}


def title_word_similarity(wordsA, wordsB):
    if not wordsA or not wordsB:
        return 0.0
    common = len(wordsA & wordsB)
    return common / min(len(wordsA), len(wordsB))


def parse_items(xml_bytes, src):
    items = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return items

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "media": "http://search.yahoo.com/mrss/",
        "content": "http://purl.org/rss/1.0/modules/content/",
    }
    nodes = root.findall(".//item")
    is_atom = False
    if not nodes:
        nodes = root.findall(".//atom:entry", ns)
        is_atom = True

    for node in nodes:
        if is_atom:
            title_el = node.find("atom:title", ns)
            title = (title_el.text or "").strip() if title_el is not None else ""
            link_el = node.find("atom:link", ns)
            link = link_el.get("href") if link_el is not None else ""
            date_el = node.find("atom:published", ns)
            if date_el is None:
                date_el = node.find("atom:updated", ns)
            date_text = date_el.text if date_el is not None else ""
        else:
            title_el = node.find("title")
            title = (title_el.text or "").strip() if title_el is not None else ""
            link_el = node.find("link")
            link = (link_el.text or "").strip() if link_el is not None else ""
            date_el = node.find("pubDate")
            date_text = date_el.text if date_el is not None else ""

        dt = parse_date(date_text)

        # gorsel arama sirasi: enclosure -> media:content -> media:thumbnail ->
        # aciklama icindeki <img> -> duz <image> etiketi (bazi yayincilarin
        # standart-disi kullandigi item-seviyesi kucuk resim alani)
        image = None
        # Atom'da <entry> varsayilan Atom namespace'ini devraliyor, bu yuzden
        # namespace'siz "enclosure" aramasi Atom feed'lerinde hicbir zaman
        # eslesmiyor (NTV'de bulundu -- ayni title/link/date namespace bug'inin
        # bir varyasyonu). Once dogru namespace'te dene, sonra namespace'siz.
        enclosure = node.find("atom:enclosure", ns) if is_atom else None
        if enclosure is None:
            enclosure = node.find("enclosure")
        if enclosure is not None:
            enc_type = enclosure.get("type", "")
            if "image" in enc_type or not enc_type:
                image = enclosure.get("url")

        if not image:
            media_content = node.find("media:content", ns)
            if media_content is not None and media_content.get("url"):
                image = media_content.get("url")

        if not image:
            media_thumb = node.find("media:thumbnail", ns)
            if media_thumb is not None and media_thumb.get("url"):
                image = media_thumb.get("url")

        if not image:
            desc_el = node.find("description")
            if desc_el is not None:
                image = find_image_in_html(desc_el.text)

        if not image:
            content_el = node.find("content:encoded", ns)
            if content_el is not None:
                image = find_image_in_html(content_el.text)

        if not image:
            image_el = node.find("image")
            if image_el is not None and (image_el.text or "").strip():
                image = image_el.text.strip()

        image = upsize_bbc_thumbnail_url(image)

        if title and link and dt:
            items.append({
                "title": title,
                "link": link,
                "date": dt,
                "source": src["name"],
                "sourceId": src["id"],
                "category": src["category"],
                "image": image,
            })

    # Ayni kaynagin feed'i icinde ayni haberin farkli versiyonlarini (ornegin
    # "Haber X" ve "GUNCELLEME: Haber X" gibi kucuk baslik degisiklikleriyle)
    # birden fazla kez listelemesi mumkun -- ozellikle Google News uzerinden
    # gelenlerde sikca goruluyor. Tam metin eslesmesi bunu yakalayamadigi icin
    # kelime bazli bulanik benzerlige geciyoruz. Kumeleme mantigi ayni kaynaktan
    # gelenleri kasten birlestirmez (farkli kaynaklarin ayni olayi yazmasini
    # kumelemek icindir), o yuzden bu temizlik burada, kaynagin kendi listesi
    # icinde erkenden yapilmali.
    deduped = []
    word_sets = []
    for it in items:
        it_words = normalize_title_words(it["title"])
        is_dup = False
        for idx, prev in enumerate(deduped):
            if abs((it["date"] - prev["date"]).total_seconds()) > 48 * 3600:
                continue
            common = len(it_words & word_sets[idx])
            if common >= 2 and title_word_similarity(it_words, word_sets[idx]) >= 0.6:
                is_dup = True
                break
        if not is_dup:
            deduped.append(it)
            word_sets.append(it_words)
    return deduped


def extract_proper_nouns(title):
    """Basliktaki BUYUK HARFLE baslayan kelimeleri (muhtemelen kisi/yer/kurum
    adlari) cikarir. Ilk kelimeyi de dahil ediyoruz -- Turkce haber basliklari
    siklikla dogrudan ozel isimle baslar ("Yavas kabul edildi..." gibi).
    Cumle basinda tesadufen buyuk harfle baslayan sozcuklerin (ozel isim
    olmayan) yanlis pozitif yaratma riski, ad sikligi esigiyle (bkz.
    COMMON_NAME_THRESHOLD) zaten sinirlaniyor. Sadece ADAY kume uretmek icin
    kullanilir -- nihai kumeleme karari artik AI dogrulamasindan geciyor
    (bkz. validate_and_summarize_clusters_with_ai), bu yuzden burasi
    kasitli olarak gevsek/permissive kalabilir."""
    raw_words = title.split()
    proper = set()
    for w in raw_words:
        stem = re.split(r"['’]", w)[0]
        stem = re.sub(r"[^\w]", "", stem, flags=re.UNICODE)
        if len(stem) < 3:
            continue
        if stem[0].isupper():
            proper.add(stem.lower())
    return proper


def build_name_frequency(proper_sets):
    freq = {}
    for s in proper_sets:
        for w in s:
            freq[w] = freq.get(w, 0) + 1
    return freq


COMMON_NAME_THRESHOLD = 4


def is_similar_title_for_summary(words_a, words_b, proper_a, proper_b, name_freq):
    if not words_a or not words_b:
        return False
    common = words_a & words_b
    if len(common) >= 2 and len(common) / min(len(words_a), len(words_b)) >= 0.3:
        return True
    if not proper_a or not proper_b:
        return False
    shared = proper_a & proper_b
    if len(shared) >= 2:
        return True
    if len(shared) == 1:
        name = next(iter(shared))
        return name_freq.get(name, 0) <= COMMON_NAME_THRESHOLD
    return False


def cluster_items_for_summary(items):
    """Kelime/ozel-isim orakalimasiyla ADAY kumeler uretir (nihai karar
    degil) -- bu adaylar validate_and_summarize_clusters_with_ai'a
    gonderilip Claude'un gercekten ayni olay olan alt-kumeyi secmesi icin
    kullanilir. AI mevcut degilse (anahtar yok/cagri basarisiz), bu
    adaylar dogrulanmadan oldugu gibi kullanilir (eski davranis)."""
    items_sorted = sorted(items, key=lambda x: x["date"], reverse=True)
    word_sets = [normalize_title_words(it["title"]) for it in items_sorted]
    proper_sets = [extract_proper_nouns(it["title"]) for it in items_sorted]
    name_freq = build_name_frequency(proper_sets)
    n = len(items_sorted)
    assigned = [False] * n
    clusters = []
    for i in range(n):
        if assigned[i]:
            continue
        cluster = [items_sorted[i]]
        assigned[i] = True
        dt_i = items_sorted[i]["date"]
        for j in range(i + 1, n):
            if assigned[j] or items_sorted[j]["sourceId"] == items_sorted[i]["sourceId"]:
                continue
            dt_j = items_sorted[j]["date"]
            if abs((dt_i - dt_j).total_seconds()) > 36 * 3600:
                continue
            if is_similar_title_for_summary(
                word_sets[i], word_sets[j], proper_sets[i], proper_sets[j], name_freq
            ):
                cluster.append(items_sorted[j])
                assigned[j] = True
        clusters.append(cluster)
    return clusters


# Tek cagrida kac aday grup gonderilecegi. Ilk denemede TUM adaylari (209)
# tek cagriya gonderdik -- API cagrisi basariyla donuyor ama Claude'un
# cevabi eleman sayisi bakimindan giris grubuyla UYUSMUYORDU (muhtemelen bu
# kadar uzun bir listede pozisyon-birebir eslesmeyi tam koruyamiyor; canli
# CI'da dogrulandi, bkz. CLAUDE.md). Kucuk gruplar halinde gondermek bu
# riski buyuk olcude azaltiyor.
CLUSTER_VALIDATION_BATCH_SIZE = 25


def validate_and_summarize_clusters_with_ai(candidate_groups, api_key):
    """Sezgisel eslestirme (cluster_items_for_summary) sadece ADAY gruplar
    uretir -- kelime/ozel-isim orakalimasi bazen alakasiz basliklari yanlislikla
    ayni gruba sokar (bkz. CLAUDE.md'deki "su gibi"/"Trump" ornekleri). Bu
    fonksiyon her aday grubu Claude'a gonderip GERCEKTEN ayni olay olan
    alt-kumeyi ("keep" indeksleri) ve o alt-kume icin tarafsiz bir ozet
    cumlesi istiyor -- boylece kumeleme kararinin kendisi de AI tarafindan
    dogrulanmis oluyor, sadece ozet degil. Adaylari CLUSTER_VALIDATION_BATCH_SIZE
    boyutunda gruplar halinde, ayri API cagrilariyla gonderir (tek dev cagri
    yerine -- nedeni yukarida). Bir batch basarisiz olursa SADECE o batch'teki
    gruplar icin None doner (caller onlari sezgisel/dogrulanmamis olarak
    kullanir); diger batch'lerin gercek AI sonucu kaybolmaz. api_key hic
    yoksa veya candidate_groups bossa (AI hic denenmedi), tum fonksiyon None
    doner."""
    if not api_key or not candidate_groups:
        return None

    all_results = []
    for start in range(0, len(candidate_groups), CLUSTER_VALIDATION_BATCH_SIZE):
        batch = candidate_groups[start:start + CLUSTER_VALIDATION_BATCH_SIZE]
        batch_results = _validate_cluster_batch(batch, api_key)
        if batch_results is None:
            # Bu batch basarisiz oldu -- sadece bu batch'teki gruplar icin
            # None koyuyoruz (caller bunlari dogrulanmamis/sezgisel olarak
            # ele alacak), diger basarili batch'lerin sonucu kaybolmuyor.
            batch_results = [None] * len(batch)
        all_results.extend(batch_results)
    return all_results


def _validate_cluster_batch(candidate_groups, api_key):
    """Tek bir batch icin gercek API cagrisini yapar. Basarili olursa
    candidate_groups ile ayni uzunlukta bir liste doner (her eleman
    {"keep": [...], "summary": str|None}), aksi halde None."""
    prompt_lines = []
    for idx, group in enumerate(candidate_groups, 1):
        titles = " | ".join(f'{it["source"]}: {it["title"]}' for it in group)
        prompt_lines.append(f"{idx}. {titles}")

    user_content = (
        "Asagida numarali gruplar var. Her grupta, FARKLI kaynaklarin AYNI "
        "haber OLAYINI yazdigi TAHMIN EDILEN basliklar bulunuyor -- ama bu "
        "kesin degil, bazen alakasiz basliklar yanlislikla ayni gruba "
        "dusebilir (orn. sadece ayni kisinin adini gecirdikleri icin, "
        "aslinda farkli olaylar olabilirler).\n\n"
        "Her grup icin SIRASIYLA:\n"
        "1. O gruptaki basliklardan HANGILERI GERCEKTEN ayni SPESIFIK olayi "
        "anlatiyor (sadece ayni genel konu/kisi degil, ayni olay) belirle. "
        "0'dan baslayan pozisyon numaralarini 'keep' alanina yaz. Hicbiri "
        "gercekten eslesmiyorsa (hepsi farkli olaylardan bahsediyorsa) bos "
        "dizi [] yaz.\n"
        "2. 'keep' alaninda 2 veya daha fazla index varsa, o olayi TARAFSIZ "
        "ve SADE bir dille anlatan, TEK CUMLELIK, en fazla 18 kelimelik bir "
        "ozet cumle yaz ('summary' alani, yorum/dramatize etme/taraf tutma "
        "YOK). 'keep' 2'den azsa summary null olsun.\n\n"
        f"Sonucta TAM OLARAK {len(candidate_groups)} eleman olmali -- her "
        "girdi grubuna birebir karsilik gelen bir eleman, ne eksik ne "
        "fazla, birlestirme/atlama YOK. Sonucu SADECE bir JSON dizisi "
        "olarak dondur -- aciklama, markdown, kod blogu YOK. Dizideki her "
        "eleman sirasiyla bir gruba karsilik gelsin, format: "
        '{"keep": [0,1], "summary": "..." veya null}\n\n'
        + "\n".join(prompt_lines)
    )

    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 8000,
        "messages": [{"role": "user", "content": user_content}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = "".join(
            block.get("text", "") for block in data.get("content", [])
            if block.get("type") == "text"
        ).strip()
        text = re.sub(r"^```(json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
        results = json.loads(text)
        if isinstance(results, list) and len(results) == len(candidate_groups):
            cleaned = []
            for r in results:
                if not isinstance(r, dict):
                    cleaned.append({"keep": [], "summary": None})
                    continue
                keep_raw = r.get("keep")
                keep = [i for i in keep_raw if isinstance(i, int)] if isinstance(keep_raw, list) else []
                summary = r.get("summary")
                cleaned.append({
                    "keep": keep,
                    "summary": str(summary).strip() if summary else None,
                })
            return cleaned
        print(f"  [AI kumeleme uyarisi] beklenmeyen format ({len(candidate_groups)} grup gonderildi, "
              f"{len(results) if isinstance(results, list) else type(results).__name__} dondu)")
    except Exception as e:
        print(f"  [AI kumeleme hatasi] {e}")
    return None


def date_label(dt, now):
    if dt.date() == now.date():
        return "bugun"
    if (now.date() - dt.date()).days == 1:
        return "dun"
    aylar = ["Ocak","Subat","Mart","Nisan","Mayis","Haziran",
             "Temmuz","Agustos","Eylul","Ekim","Kasim","Aralik"]
    return f"{dt.day} {aylar[dt.month-1]}"


def build_html(all_items):
    now = datetime.now(timezone.utc)
    all_items.sort(key=lambda x: x["date"], reverse=True)

    favicon_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        '<rect width="32" height="32" fill="#FFFFFF"/>'
        '<rect x="6" y="8" width="20" height="3" fill="#000000"/>'
        '<rect x="6" y="14.5" width="14" height="3" fill="#000000"/>'
        '<rect x="6" y="21" width="9" height="3" fill="#000000"/>'
        '<circle cx="25" cy="22.5" r="2.6" fill="#000000"/>'
        '</svg>'
    )
    favicon_b64 = base64.b64encode(favicon_svg.encode("utf-8")).decode("ascii")
    data = [{
        "title": it["title"],
        "link": it["link"],
        "date": it["date"].isoformat(),
        "source": it["source"],
        "sourceId": it["sourceId"],
        "category": it["category"],
        "image": it.get("image") or make_placeholder_image(it["source"]),
        "aiSummary": it.get("ai_summary"),
        "clusterId": it.get("cluster_id"),
    } for it in all_items]

    sources_meta = [{"id": s["id"], "name": s["name"], "category": s["category"], "lang": s.get("lang", "")} for s in SOURCES]

    generated = now.strftime("%d.%m.%Y %H:%M UTC")

    return f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,{favicon_b64}">
<title>Sakin Akış</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,400;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap');
:root{{--paper:#000000;--paper-raised:#161616;--ink:#FFFFFF;--ink-soft:#999999;--rule:#333333;--accent:#FFFFFF;}}
html.light{{--paper:#FFFFFF;--paper-raised:#F0F0F0;--ink:#000000;--ink-soft:#666666;--rule:#DDDDDD;--accent:#000000;}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);
font-family:'Source Serif 4',Georgia,serif;position:relative;transition:background 0.15s ease,color 0.15s ease}}
.wrap{{max-width:640px;margin:0 auto;padding:32px 20px 80px}}
.top-toggles{{position:fixed;top:18px;right:18px;display:flex;gap:8px;z-index:10}}
.theme-toggle,.lang-toggle{{font-family:'IBM Plex Mono',monospace;
font-size:12px;background:var(--paper);border:1px solid var(--ink);color:var(--ink);
padding:6px 12px;cursor:pointer}}
.theme-toggle:hover,.lang-toggle:hover{{background:var(--ink);color:var(--paper)}}
.tabs{{display:flex;margin:20px 0 4px;border-bottom:1px solid var(--rule)}}
.tab-btn{{flex:1;text-align:center;font-family:'IBM Plex Mono',monospace;font-size:13px;
background:none;border:none;color:var(--ink-soft);padding:8px 4px;cursor:pointer;
border-bottom:2px solid transparent;position:relative;top:1px}}
.tab-btn.active{{color:var(--ink);border-bottom-color:var(--accent);font-weight:600}}
.filters{{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0 8px}}
.filter-field{{flex:1;min-width:200px}}
.filter-field label{{display:block;font-family:'IBM Plex Mono',monospace;font-size:10.5px;
color:var(--ink-soft);margin-bottom:4px}}
.filter-field input{{width:100%;font-family:'IBM Plex Mono',monospace;font-size:12.5px;
color:var(--ink);background:var(--paper-raised);border:1px solid var(--rule);
padding:8px 10px}}
.filter-field input:focus{{outline:none;border-color:var(--ink)}}
.topic-chips{{display:flex;flex-wrap:wrap;gap:5px;margin-top:6px}}
.topic-chip{{font-family:'IBM Plex Mono',monospace;font-size:11px;background:none;
border:1px solid var(--rule);color:var(--ink-soft);padding:3px 9px;cursor:pointer}}
.topic-chip:hover{{border-color:var(--ink)}}
.topic-chip.active{{background:var(--ink);color:var(--paper);border-color:var(--ink)}}
.sort-toggle{{display:inline-block;margin:4px 0 18px;font-family:'IBM Plex Mono',monospace;
font-size:12px;background:none;border:1px solid var(--ink);color:var(--ink);
padding:7px 14px;cursor:pointer}}
.sort-toggle:hover{{background:var(--ink);color:var(--paper)}}
.sort-toggle.active{{background:var(--accent);color:var(--paper);border-color:var(--accent)}}
.coverage-badge{{color:var(--accent);font-weight:600}}
.sources-toggle-btn{{display:flex;align-items:center;gap:5px;margin-top:10px;
background:none;border:none;padding:0;cursor:pointer;font-family:'IBM Plex Mono',monospace;
font-size:11.5px;color:var(--ink-soft)}}
.sources-toggle-btn:hover{{color:var(--ink)}}
.sources-toggle-btn .chevron{{display:inline-block;transition:transform 0.15s ease;font-size:9px}}
.sources-toggle-btn.open .chevron{{transform:rotate(90deg)}}
.cluster-sources{{display:none;margin-top:10px;padding-left:12px;border-left:2px solid var(--rule)}}
.cluster-sources.open{{display:block}}
.cluster-source-row{{display:flex;align-items:baseline;gap:8px;font-family:'IBM Plex Mono',monospace;
font-size:12px;color:var(--ink-soft);padding:6px 0;border-bottom:1px solid var(--rule)}}
.cluster-source-row:last-child{{border-bottom:none}}
.cluster-source-name{{flex-shrink:0;min-width:70px;color:var(--ink-soft)}}
.cluster-source-row a{{color:var(--ink-soft);text-decoration:none;font-family:'Source Serif 4',Georgia,serif;
font-size:13.5px;line-height:1.4}}
.cluster-source-row a:hover{{color:var(--accent)}}
.pagination{{display:flex;flex-wrap:wrap;align-items:center;justify-content:center;
gap:10px 12px;margin:36px 0 10px;font-family:'IBM Plex Mono',monospace;font-size:12px}}
.page-btn{{background:none;border:1px solid var(--ink);color:var(--ink);
padding:7px 12px;cursor:pointer}}
.page-btn:hover:not(:disabled){{background:var(--ink);color:var(--paper)}}
.page-btn:disabled{{opacity:0.3;cursor:default;border-color:var(--rule);color:var(--ink-soft)}}
.page-indicator{{color:var(--ink-soft)}}
.filter-status{{font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--ink-soft);
margin:4px 0 6px}}
.filter-hint{{font-family:'IBM Plex Mono',monospace;font-size:10.5px;color:var(--ink-soft);
margin:0 0 18px;font-style:italic}}
.sources-label{{font-family:'IBM Plex Mono',monospace;font-size:10.5px;color:var(--ink-soft);
margin:18px 0 8px;background:none;border:none;padding:0;cursor:pointer;
display:flex;align-items:center;gap:5px}}
.sources-label:hover{{color:var(--ink)}}
.sources-label .chevron{{display:inline-block;transition:transform 0.15s ease;font-size:9px}}
.sources-label.expanded .chevron{{transform:rotate(90deg)}}
.sources{{display:flex;flex-wrap:wrap;gap:6px 14px;margin-bottom:6px}}
.sources-subgroup-label{{flex-basis:100%;font-family:'IBM Plex Mono',monospace;font-size:10.5px;
color:var(--ink-soft);margin:8px 0 2px}}
.sources-subgroup-label:first-child{{margin-top:0}}
.src-toggle{{display:flex;align-items:center;gap:6px;font-family:'IBM Plex Mono',monospace;
font-size:12.5px;cursor:pointer;user-select:none;padding:3px 0;
border-bottom:1px solid transparent;color:var(--ink-soft);background:none;border-top:none;
border-left:none;border-right:none}}
.src-toggle.active{{color:var(--ink);border-bottom-color:var(--ink)}}
.date-divider{{font-family:'IBM Plex Mono',monospace;font-size:11.5px;color:var(--ink-soft);
margin:30px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--rule)}}
.item{{padding:0 0 22px;margin-bottom:22px;border-bottom:1px solid var(--rule);
display:flex;flex-direction:column}}
.item.seen{{opacity:0.5}}
.media{{position:relative;width:100%}}
.thumb{{width:100%;aspect-ratio:2.2/1;object-fit:cover;background:var(--rule);display:block}}
.overlay{{position:absolute;left:0;right:0;bottom:0;padding:34px 14px 12px;
background:linear-gradient(to top, rgba(0,0,0,0.92) 0%, rgba(0,0,0,0.72) 55%, rgba(0,0,0,0) 100%)}}
.overlay .item-meta{{display:flex;align-items:center;gap:7px;font-family:'IBM Plex Mono',monospace;
font-size:12px;color:rgba(255,255,255,0.85);margin-bottom:6px}}
.overlay h2{{font-size:20px;line-height:1.32;font-weight:600;margin:0;
text-shadow:0 1px 5px rgba(0,0,0,0.55)}}
.overlay h2 a{{color:#FFFFFF;text-decoration:none}}
.overlay h2 a:hover{{color:#fff}}
.overlay .eye-btn{{color:rgba(255,255,255,0.85)}}
.overlay .eye-btn:hover{{color:#fff}}
.overlay.on-light{{background:linear-gradient(to top, rgba(255,255,255,0.92) 0%, rgba(255,255,255,0.72) 55%, rgba(255,255,255,0) 100%)}}
.overlay.on-light .item-meta{{color:rgba(0,0,0,0.85)}}
.overlay.on-light h2{{text-shadow:0 1px 5px rgba(255,255,255,0.5)}}
.overlay.on-light h2 a{{color:#000000}}
.overlay.on-light h2 a:hover{{color:#000}}
.overlay.on-light .eye-btn{{color:rgba(0,0,0,0.85)}}
.overlay.on-light .eye-btn:hover{{color:#000}}
.eye-btn{{background:none;border:none;padding:0;margin:0;cursor:pointer;
color:var(--ink-soft);display:inline-flex;align-items:center;line-height:0}}
.eye-btn:hover{{color:var(--accent)}}
.eye-btn svg{{width:14px;height:14px}}
.empty{{font-family:'IBM Plex Mono',monospace;font-size:13px;color:var(--ink-soft);
padding:40px 0;text-align:center}}
footer{{font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--ink-soft);
margin-top:40px;padding-top:16px;border-top:1px solid var(--rule)}}
</style></head><body>
<div class="top-toggles">
  <button class="theme-toggle" id="themeToggle">☀</button>
  <button class="lang-toggle" id="langToggle">EN</button>
</div>
<div class="wrap">
<div class="tabs" id="mainTabs"></div>
<button class="sources-label" id="sourcesLabel">kaynaklar</button>
<div class="sources" id="sourceToggles"></div>
<div class="filters">
  <div class="filter-field">
    <label id="hideLabel" for="hideInput">gizle (virgülle ayır)</label>
    <input type="text" id="hideInput">
    <div class="topic-chips" id="hideTopicChips"></div>
  </div>
  <div class="filter-field">
    <label id="onlyLabel" for="onlyInput">sadece göster (virgülle ayır)</label>
    <input type="text" id="onlyInput">
    <div class="topic-chips" id="onlyTopicChips"></div>
  </div>
  <div class="filter-field">
    <label id="importantLabel" for="importantInput">önemli (virgülle ayır)</label>
    <input type="text" id="importantInput">
    <div class="topic-chips" id="importantTopicChips"></div>
  </div>
</div>
<button class="sort-toggle" id="sortToggle"></button>
<div class="filter-status" id="filterStatus"></div>
<div class="filter-hint" id="filterHint"></div>
<div id="feed"></div>
<div class="pagination" id="pagination"></div>
<footer id="pageFooter"></footer>
</div>
<script>
const DATA = {json.dumps(data, ensure_ascii=False)};
const SOURCES_META = {json.dumps(sources_meta, ensure_ascii=False)};
const GENERATED = "{generated}";

function clusterItems(items){{
  // Kumeleme karari artik build zamaninda Python tarafinda (AI dogrulamali)
  // veriliyor -- her ogeye kalici bir clusterId ataniyor. Burada tarayicida
  // sadece bu id'ye gore GRUPLAMA yapiliyor, benzerlik hesaplanmiyor. Ayni
  // clusterId'yi paylasmayan (ya da clusterId'si olmayan, yani AI/sezgisel
  // eslesme hic bulamamis) her oge kendi tek-elemanli kumesinde kalir.
  const groups = new Map();
  const singles = [];
  items.forEach(it => {{
    if (it.clusterId != null){{
      if (!groups.has(it.clusterId)) groups.set(it.clusterId, []);
      groups.get(it.clusterId).push(it);
    }} else {{
      singles.push([it]);
    }}
  }});
  return [...groups.values(), ...singles];
}}

const I18N = {{
  tr: {{
    today: "bugün", yesterday: "dün",
    months: ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"],
    relMin: "dk", relHour: "sa", relDay: "g",
    empty: "Hiç haber çekilemedi.",
    footer: t => `Oluşturulma: ${{t}} \\u00b7 yenilemek için scripti tekrar çalıştır`,
    toggleLabel: "EN",
    hideLabel: "gizle (virgülle ayır)",
    onlyLabel: "sadece göster (virgülle ayır)",
    filterStatus: (shown, total) => `${{shown}} / ${{total}} haber gösteriliyor`,
    readFull: "kaynakta aç",
    sourcesLabel: "kaynaklar",
    sourcesLangTr: "türkçe kaynaklar",
    sourcesLangForeign: "yabancı kaynaklar",
    expandedHint: words => `genişletilmiş eşleşme: ${{words.join(', ')}} de dahil`,
    importantLabel: "önemli (virgülle ayır)",
    sortToChrono: "kronolojik göster",
    sortToImportance: "önem sırasına gör",
    coverageBadge: n => `${{n}} kaynakta`,
    sourcesToggle: n => `${{n}} kaynakta daha oku`,
    tabNews: "Haberler",
    tabGames: "Oyunlar",
    oyunOtherLabel: "Diğer",
    markSeen: "gördüm olarak işaretle",
    markUnseen: "tekrar yukarı çıkar",
    prevPage: "Önceki",
    nextPage: "Sonraki",
    firstPage: "Başa Dön",
    lastPage: "Sona Git",
    pageIndicator: (cur, total) => `Sayfa ${{cur}} / ${{total}}`
  }},
  en: {{
    today: "today", yesterday: "yesterday",
    months: ["January","February","March","April","May","June","July","August","September","October","November","December"],
    relMin: "m", relHour: "h", relDay: "d",
    empty: "No articles could be fetched.",
    footer: t => `Generated: ${{t}} \\u00b7 rerun the script to refresh`,
    toggleLabel: "TR",
    hideLabel: "hide (comma-separated)",
    onlyLabel: "only show (comma-separated)",
    filterStatus: (shown, total) => `showing ${{shown}} / ${{total}} articles`,
    readFull: "open source",
    sourcesLabel: "sources",
    sourcesLangTr: "turkish sources",
    sourcesLangForeign: "international sources",
    expandedHint: words => `expanded match includes: ${{words.join(', ')}}`,
    importantLabel: "important (comma-separated)",
    sortToChrono: "show chronological",
    sortToImportance: "sort by importance",
    coverageBadge: n => `in ${{n}} sources`,
    sourcesToggle: n => `read in ${{n}} more sources`,
    tabNews: "News",
    tabGames: "Games",
    oyunOtherLabel: "Other",
    markSeen: "mark as seen",
    markUnseen: "move back to top",
    prevPage: "Previous",
    nextPage: "Next",
    firstPage: "First",
    lastPage: "Last",
    pageIndicator: (cur, total) => `Page ${{cur}} of ${{total}}`
  }}
}};

let lang = "tr";
let theme = "dark";
let activeSources = new Set(SOURCES_META.map(s => s.id));
let sortMode = "chrono";
let currentTab = "haber";
let seenLinks = new Set();
let currentPage = 1;
const PAGE_SIZE = 25;
let sourcesExpanded = false;

const EYE_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>';
const EYE_OFF_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.94 10.94 0 0 1 12 20c-7 0-11-8-11-8a18.66 18.66 0 0 1 5.06-5.94"></path><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>';

function buildTabs(){{
  const L = I18N[lang];
  const el = document.getElementById('mainTabs');
  el.innerHTML = '';
  [['haber', L.tabNews], ['oyun', L.tabGames]].forEach(([id, label]) => {{
    const btn = document.createElement('button');
    btn.className = 'tab-btn' + (currentTab === id ? ' active' : '');
    btn.textContent = label;
    btn.addEventListener('click', () => {{
      currentTab = id;
      currentPage = 1;
      try {{ localStorage.setItem('sakinakis_tab', currentTab); }} catch(e) {{}}
      loadFilterInputsForTab();
      render();
    }});
    el.appendChild(btn);
  }});
}}

// Oyunlar sekmesinde 11 ayri kaynak yerine 3 grup gosterilir -- kullanici
// tek tek oyun degil, "nereden" (Riot / Steam / digeri) diye dusunuyor.
// Grup butonuna tiklamak, o gruptaki TUM sourceId'leri birlikte ac/kapat.
// "Riot Games" ve "Steam" marka isimleri, dile gore degismez; "Diger" ise
// L.oyunOtherLabel ile cevriliyor (asagida buildSourceToggles icinde).
const OYUN_SOURCE_GROUPS = [
  {{ id: 'riot', label: 'Riot Games', sourceIds: ['valorant', 'lol', 'tft'] }},
  {{ id: 'steam', label: 'Steam', sourceIds: ['deadlock', 'bodycam', 'zomboid', 'r6siege', 'cs2', 'dota2'] }},
  {{ id: 'other', label: null, sourceIds: ['minecraft', 'game_news'] }},
];

function buildSourceToggles(){{
  const L = I18N[lang];
  const wrapEl = document.getElementById('sourcesLabel');
  const el = document.getElementById('sourceToggles');
  wrapEl.style.display = '';

  if (currentTab === 'oyun'){{
    const activeGroupCount = OYUN_SOURCE_GROUPS.filter(g => g.sourceIds.every(id => activeSources.has(id))).length;
    wrapEl.innerHTML = `<span class="chevron">&#9656;</span><span>${{L.sourcesLabel}} (${{activeGroupCount}}/${{OYUN_SOURCE_GROUPS.length}})</span>`;
    wrapEl.classList.toggle('expanded', sourcesExpanded);
    wrapEl.onclick = () => {{
      sourcesExpanded = !sourcesExpanded;
      render();
    }};
    el.style.display = sourcesExpanded ? '' : 'none';
    el.innerHTML = '';
    OYUN_SOURCE_GROUPS.forEach(g => {{
      const allActive = g.sourceIds.every(id => activeSources.has(id));
      const btn = document.createElement('button');
      btn.className = 'src-toggle' + (allActive ? ' active' : '');
      const label = g.label || L.oyunOtherLabel;
      btn.textContent = label;
      btn.addEventListener('click', () => {{
        if (allActive) g.sourceIds.forEach(id => activeSources.delete(id));
        else g.sourceIds.forEach(id => activeSources.add(id));
        currentPage = 1;
        try {{ localStorage.setItem('sakinakis_sources', JSON.stringify([...activeSources])); }} catch(e) {{}}
        render();
      }});
      el.appendChild(btn);
    }});
    return;
  }}

  const tabSources = SOURCES_META.filter(s => s.category === currentTab);
  const activeCount = tabSources.filter(s => activeSources.has(s.id)).length;
  wrapEl.innerHTML = `<span class="chevron">&#9656;</span><span>${{L.sourcesLabel}} (${{activeCount}}/${{tabSources.length}})</span>`;
  wrapEl.classList.toggle('expanded', sourcesExpanded);
  wrapEl.onclick = () => {{
    sourcesExpanded = !sourcesExpanded;
    render();
  }};
  el.style.display = sourcesExpanded ? '' : 'none';
  el.innerHTML = '';

  function appendGroup(groupLabel, sources){{
    if (!sources.length) return;
    const heading = document.createElement('div');
    heading.className = 'sources-subgroup-label';
    heading.textContent = groupLabel;
    el.appendChild(heading);
    sources.forEach(s => {{
      const btn = document.createElement('button');
      btn.className = 'src-toggle' + (activeSources.has(s.id) ? ' active' : '');
      btn.textContent = s.name;
      btn.addEventListener('click', () => {{
        if (activeSources.has(s.id)) activeSources.delete(s.id);
        else activeSources.add(s.id);
        currentPage = 1;
        try {{ localStorage.setItem('sakinakis_sources', JSON.stringify([...activeSources])); }} catch(e) {{}}
        render();
      }});
      el.appendChild(btn);
    }});
  }}

  appendGroup(L.sourcesLangTr, tabSources.filter(s => s.lang === 'tr'));
  appendGroup(L.sourcesLangForeign, tabSources.filter(s => s.lang !== 'tr'));
}}

function dateLabel(dt, now, L){{
  const sameDay = dt.toDateString() === now.toDateString();
  if (sameDay) return L.today;
  const y = new Date(now); y.setDate(now.getDate()-1);
  if (dt.toDateString() === y.toDateString()) return L.yesterday;
  return `${{dt.getDate()}} ${{L.months[dt.getMonth()]}}`;
}}

function relTime(dt, now, L){{
  const mins = Math.round((now - dt) / 60000);
  if (mins < 60) return Math.max(mins,0) + L.relMin;
  const hrs = Math.round(mins/60);
  if (hrs < 24) return hrs + L.relHour;
  return Math.round(hrs/24) + L.relDay;
}}

function absDate(dt, L){{
  return `${{dt.getDate()}} ${{L.months[dt.getMonth()].slice(0,3)}}`;
}}

// Basligin oturdugu bolgenin (gorselin alt ~%45'i) ortalama parlakligini
// olcer, boylece acik renkli gorsellerde beyaz yerine koyu metin kullanabiliriz.
// Farkli-kaynakli (cross-origin) gorsellerde CORS engeli varsa (Wikipedia
// genelde izin verir ama garanti degil) analiz sessizce basarisiz olur ve
// varsayilan (koyu zemin ustune acik metin, guclu gradient sayesinde zaten
// okunakli) davranista kalinir -- hicbir sey bozulmaz.
function sampleImageBrightness(img, callback){{
  try {{
    const sw = img.naturalWidth || img.width;
    const sh = img.naturalHeight || img.height;
    if (!sw || !sh) {{ callback(null); return; }}
    const canvas = document.createElement('canvas');
    const w = 32, h = 16;
    canvas.width = w; canvas.height = h;
    const ctx = canvas.getContext('2d');
    const sampleH = Math.max(1, Math.round(sh * 0.45));
    ctx.drawImage(img, 0, sh - sampleH, sw, sampleH, 0, 0, w, h);
    const data = ctx.getImageData(0, 0, w, h).data;
    let total = 0, count = 0;
    for (let i = 0; i < data.length; i += 4){{
      total += 0.299 * data[i] + 0.587 * data[i+1] + 0.114 * data[i+2];
      count++;
    }}
    callback(count > 0 ? total / count : null);
  }} catch(e) {{
    callback(null);
  }}
}}

function applyOverlayContrast(imgEl, overlayEl){{
  // Gorunen <img> artik crossorigin="anonymous" TASIMIYOR -- boylece CORS
  // header'i olmayan sunuculardan (orn. CNN Turk CDN'i) gelen gorseller de
  // normal sekilde yuklenir. Parlaklik olcumu icin ayri, gorunmez bir "probe"
  // Image() olusturuyoruz; SADECE bu probe crossOrigin='anonymous' kullaniyor.
  // Probe CORS'a takilirsa (onerror) sessizce varsayilan (koyu zemin) stile
  // duesuyor -- gorunen gorseli hic etkilemiyor.
  function analyze(){{
    const probe = new Image();
    probe.crossOrigin = 'anonymous';
    probe.onload = () => {{
      sampleImageBrightness(probe, (brightness) => {{
        if (brightness !== null && brightness > 165){{
          overlayEl.classList.add('on-light');
        }} else {{
          overlayEl.classList.remove('on-light');
        }}
      }});
    }};
    probe.src = imgEl.src;
  }}
  if (imgEl.complete && imgEl.naturalWidth > 0){{
    analyze();
  }} else {{
    imgEl.addEventListener('load', analyze);
  }}
}}

const TOPIC_SYNONYMS = {{
  "futbol": ["galatasaray","fenerbahçe","beşiktaş","trabzonspor","süper lig","transfer","gol","maç","uefa","şampiyonlar ligi","milli takım","futbolcu","football","soccer"],
  "spor": ["futbol","basketbol","voleybol","galatasaray","fenerbahçe","beşiktaş","milli takım","euroleague","sport"],
  "ekonomi": ["dolar","euro","enflasyon","borsa","faiz","tcmb","merkez bankası","ihracat","ithalat","economy","market"],
  "siyaset": ["chp","akp","mhp","iyi parti","meclis","bakan","cumhurbaşkanı","seçim","parti","politics"],
  "magazin": ["ünlü","oyuncu","şarkıcı","dizi","influencer","boşandı","evlendi","celebrity"],
  "teknoloji": ["yapay zeka","yazılım","uygulama","telefon","apple","google","microsoft","tech","ai"],
  "patchnotes": ["patch","update","yama","sürüm","hotfix","düzeltme","bug fix","balance","sürüm notları","patch notes"],
  "digeroyun": ["tournament","championship","şampiyona","esports","e-spor","major","worlds","playoffs","lig","turnuva",
                "dlc","yeni harita","yeni ajan","yeni şampiyon","yeni karakter","genişleme","expansion","yeni mod",
                "new content","reveal","yeni silah","yeni sezon","season","sale","discount","indirim","kampanya",
                "fırsat","ücretsiz","free weekend"]
}};

const TOPIC_LABELS = {{
  tr: {{futbol:"futbol", spor:"spor", ekonomi:"ekonomi", siyaset:"siyaset", magazin:"magazin", teknoloji:"teknoloji",
        patchnotes:"güncelleme notları", digeroyun:"diğer"}},
  en: {{futbol:"football", spor:"sports", ekonomi:"economy", siyaset:"politics", magazin:"celebrity", teknoloji:"tech",
        patchnotes:"patch notes", digeroyun:"other"}}
}};

const TOPIC_KEYS_BY_TAB = {{
  haber: ["futbol","spor","ekonomi","siyaset","magazin","teknoloji"],
  oyun: ["patchnotes","digeroyun"]
}};

function hideStorageKey(){{ return 'sakinakis_hide_' + currentTab; }}
function onlyStorageKey(){{ return 'sakinakis_only_' + currentTab; }}
function importantStorageKey(){{ return 'sakinakis_important_' + currentTab; }}

function loadFilterInputsForTab(){{
  try {{
    hideInputEl.value = localStorage.getItem(hideStorageKey()) || '';
    onlyInputEl.value = localStorage.getItem(onlyStorageKey()) || '';
    importantInputEl.value = localStorage.getItem(importantStorageKey()) || '';
  }} catch(e) {{ /* localStorage yoksa sessizce devam */ }}
}}

function getWordsArray(inputEl){{
  return inputEl.value.split(',').map(w => w.trim()).filter(w => w.length > 0);
}}

function toggleTopicChip(inputEl, topic, storageKey){{
  const words = getWordsArray(inputEl).map(w => w.toLocaleLowerCase('tr'));
  const idx = words.indexOf(topic);
  if (idx >= 0) words.splice(idx, 1); else words.push(topic);
  inputEl.value = words.join(', ');
  currentPage = 1;
  try {{ localStorage.setItem(storageKey, inputEl.value); }} catch(e) {{}}
  render();
}}

function buildTopicChips(containerId, inputEl, storageKey){{
  const el = document.getElementById(containerId);
  el.innerHTML = '';
  const activeWords = getWordsArray(inputEl).map(w => w.toLocaleLowerCase('tr'));
  const keys = TOPIC_KEYS_BY_TAB[currentTab] || Object.keys(TOPIC_SYNONYMS);
  keys.forEach(topic => {{
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'topic-chip' + (activeWords.includes(topic) ? ' active' : '');
    btn.textContent = TOPIC_LABELS[lang][topic] || topic;
    btn.addEventListener('click', () => toggleTopicChip(inputEl, topic, storageKey));
    el.appendChild(btn);
  }});
}}

function expandWords(words){{
  const expanded = new Set(words);
  words.forEach(w => {{
    if (TOPIC_SYNONYMS[w]) {{
      TOPIC_SYNONYMS[w].forEach(syn => expanded.add(syn.toLocaleLowerCase('tr')));
    }}
  }});
  return [...expanded];
}}

function parseWords(text){{
  return text.split(',').map(w => w.trim().toLocaleLowerCase('tr')).filter(w => w.length > 0);
}}

function matchesFilter(text, hideWords, onlyWords){{
  const t = text.toLocaleLowerCase('tr');
  if (onlyWords.length > 0 && !onlyWords.some(w => t.includes(w))) return false;
  if (hideWords.some(w => t.includes(w))) return false;
  return true;
}}

function render(){{
  const L = I18N[lang];
  document.documentElement.lang = lang;
  document.getElementById('langToggle').textContent = L.toggleLabel;
  document.documentElement.classList.toggle('light', theme === 'light');
  document.getElementById('themeToggle').textContent = theme === 'dark' ? '☀' : '☾';
  document.getElementById('pageFooter').textContent = L.footer(GENERATED);
  document.getElementById('hideLabel').textContent = L.hideLabel;
  document.getElementById('onlyLabel').textContent = L.onlyLabel;
  document.getElementById('importantLabel').textContent = L.importantLabel;

  const sortBtn = document.getElementById('sortToggle');
  sortBtn.textContent = sortMode === 'chrono' ? L.sortToImportance : L.sortToChrono;
  sortBtn.classList.toggle('active', sortMode === 'importance');

  buildTabs();
  buildTopicChips('hideTopicChips', hideInputEl, hideStorageKey());
  buildTopicChips('onlyTopicChips', onlyInputEl, onlyStorageKey());
  buildTopicChips('importantTopicChips', importantInputEl, importantStorageKey());
  buildSourceToggles();

  const hideRaw = parseWords(document.getElementById('hideInput').value);
  const onlyRaw = parseWords(document.getElementById('onlyInput').value);
  const importantRaw = parseWords(document.getElementById('importantInput').value);
  const hideWords = expandWords(hideRaw);
  const onlyWords = expandWords(onlyRaw);
  const importantWords = expandWords(importantRaw);
  let filtered = DATA.filter(it =>
    it.category === currentTab &&
    activeSources.has(it.sourceId) &&
    matchesFilter(it.title, hideWords, onlyWords)
  );

  const extras = [...new Set([...hideWords, ...onlyWords, ...importantWords])]
    .filter(w => !hideRaw.includes(w) && !onlyRaw.includes(w) && !importantRaw.includes(w));
  document.getElementById('filterHint').textContent = extras.length > 0 ? L.expandedHint(extras) : '';

  document.getElementById('filterStatus').textContent = L.filterStatus(filtered.length, DATA.length);

  const now = new Date();
  const feed = document.getElementById('feed');
  if (filtered.length === 0){{
    feed.innerHTML = `<div class="empty">${{L.empty}}</div>`;
    return;
  }}

  function sortClustersByMode(arr){{
    if (sortMode === 'importance'){{
      return arr.map(cluster => {{
        const primary = cluster[0];
        const t = primary.title.toLocaleLowerCase('tr');
        const keywordHit = importantWords.some(w => t.includes(w));
        const score = (cluster.length - 1) + (keywordHit ? 1000 : 0);
        return {{ cluster, score }};
      }}).sort((a, b) => b.score - a.score || (new Date(b.cluster[0].date) - new Date(a.cluster[0].date)))
        .map(x => x.cluster);
    }}
    return [...arr].sort((a, b) => new Date(b[0].date) - new Date(a[0].date));
  }}

  function isClusterSeen(cluster){{
    return cluster.every(it => seenLinks.has(it.link));
  }}

  const sortedForClustering = [...filtered].sort((a, b) => new Date(b.date) - new Date(a.date));
  // Oyunlar sekmesinde kumeleme yok -- her haber kendi kartinda kalir
  const allClusters = currentTab === 'oyun'
    ? sortedForClustering.map(it => [it])
    : clusterItems(sortedForClustering);
  const unseenClusters = sortClustersByMode(allClusters.filter(c => !isClusterSeen(c)));
  const seenClusters = sortClustersByMode(allClusters.filter(c => isClusterSeen(c)));
  const orderedClusters = [...unseenClusters, ...seenClusters];

  const totalPages = Math.max(1, Math.ceil(orderedClusters.length / PAGE_SIZE));
  if (currentPage > totalPages) currentPage = totalPages;
  if (currentPage < 1) currentPage = 1;
  const pageStart = (currentPage - 1) * PAGE_SIZE;
  const pageClusters = orderedClusters.slice(pageStart, pageStart + PAGE_SIZE);

  let html = '';
  let lastLabel = null;
  pageClusters.forEach(cluster => {{
    const newest = cluster[0];
    const isMulti = cluster.length > 1;
    const isSeen = isClusterSeen(cluster);
    const dt = new Date(newest.date);
    if (sortMode === 'chrono'){{
      const dl = dateLabel(dt, now, L);
      if (dl !== lastLabel){{
        html += `<div class="date-divider">${{dl}}</div>`;
        lastLabel = dl;
      }}
    }}

    const aiSummaryItem = cluster.find(m => m.aiSummary);
    const shortest = isMulti ? [...cluster].sort((a, b) => a.title.length - b.title.length)[0] : newest;
    const headlineLink = aiSummaryItem || shortest;
    const headlineText = aiSummaryItem ? aiSummaryItem.aiSummary : shortest.title;

    const thumb = newest.image
      ? `<img class="thumb" src="${{newest.image}}" alt="" loading="lazy" onerror="this.remove();">`
      : '';
    const eyeBtn = `<button class="eye-btn" title="${{isSeen ? L.markUnseen : L.markSeen}}">${{isSeen ? EYE_OFF_ICON : EYE_ICON}}</button>`;

    const metaHtml = isMulti
      ? `<span class="coverage-badge">${{L.coverageBadge(cluster.length)}}</span><span>&middot;</span><span>${{relTime(dt, now, L)}}</span><span>&middot;</span><span>${{absDate(dt, L)}}</span>`
      : `<span>${{newest.source}}</span><span>&middot;</span><span>${{relTime(dt, now, L)}}</span><span>&middot;</span><span>${{absDate(dt, L)}}</span>`;

    const sourcesListHtml = isMulti
      ? `<button class="sources-toggle-btn"><span class="chevron">&#9656;</span><span>${{L.sourcesToggle(cluster.length)}}</span></button>
         <div class="cluster-sources">` + cluster.map(m => `
          <div class="cluster-source-row">
            <span class="cluster-source-name">${{m.source}}</span>
            <a href="${{m.link}}" target="_blank" rel="noopener">${{m.title}}</a>
          </div>`).join('') + `</div>`
      : '';

    html += `
      <div class="item${{isSeen ? ' seen' : ''}}">
        <div class="media">
          ${{thumb}}
          <div class="overlay">
            <div class="item-meta">
              ${{metaHtml}}
              <span>&middot;</span>${{eyeBtn}}
            </div>
            <h2><a href="${{headlineLink.link}}" target="_blank" rel="noopener">${{headlineText}}</a></h2>
          </div>
        </div>
        ${{sourcesListHtml}}
      </div>`;
  }});
  feed.innerHTML = html;

  const pagEl = document.getElementById('pagination');
  if (totalPages > 1){{
    pagEl.innerHTML = `
      <button class="page-btn" id="firstPageBtn" ${{currentPage === 1 ? 'disabled' : ''}}>${{L.firstPage}}</button>
      <button class="page-btn" id="prevPageBtn" ${{currentPage === 1 ? 'disabled' : ''}}>${{L.prevPage}}</button>
      <span class="page-indicator">${{L.pageIndicator(currentPage, totalPages)}}</span>
      <button class="page-btn" id="nextPageBtn" ${{currentPage === totalPages ? 'disabled' : ''}}>${{L.nextPage}}</button>
      <button class="page-btn" id="lastPageBtn" ${{currentPage === totalPages ? 'disabled' : ''}}>${{L.lastPage}}</button>`;
    document.getElementById('firstPageBtn').addEventListener('click', () => {{
      currentPage = 1;
      render();
      window.scrollTo({{ top: 0, behavior: 'instant' }});
    }});
    document.getElementById('prevPageBtn').addEventListener('click', () => {{
      currentPage--;
      render();
      window.scrollTo({{ top: 0, behavior: 'instant' }});
    }});
    document.getElementById('nextPageBtn').addEventListener('click', () => {{
      currentPage++;
      render();
      window.scrollTo({{ top: 0, behavior: 'instant' }});
    }});
    document.getElementById('lastPageBtn').addEventListener('click', () => {{
      currentPage = totalPages;
      render();
      window.scrollTo({{ top: 0, behavior: 'instant' }});
    }});
  }} else {{
    pagEl.innerHTML = '';
  }}

  const itemEls = feed.querySelectorAll('.item');
  itemEls.forEach((el, idx) => {{
    const cluster = pageClusters[idx];
    const eyeBtn = el.querySelector('.eye-btn');
    eyeBtn.addEventListener('click', (e) => {{
      e.preventDefault();
      const shouldMark = !isClusterSeen(cluster);
      cluster.forEach(it => {{
        if (shouldMark) seenLinks.add(it.link); else seenLinks.delete(it.link);
      }});
      try {{ localStorage.setItem('sakinakis_seen', JSON.stringify([...seenLinks])); }} catch(err) {{}}
      render();
    }});

    const thumbImg = el.querySelector('.thumb');
    const overlayEl = el.querySelector('.overlay');
    if (thumbImg && overlayEl){{
      applyOverlayContrast(thumbImg, overlayEl);
    }}

    const sourcesToggleBtn = el.querySelector('.sources-toggle-btn');
    if (sourcesToggleBtn){{
      const sourcesListEl = el.querySelector('.cluster-sources');
      sourcesToggleBtn.addEventListener('click', () => {{
        const isOpen = sourcesListEl.classList.toggle('open');
        sourcesToggleBtn.classList.toggle('open', isOpen);
      }});
    }}
  }});
}}

document.getElementById('langToggle').addEventListener('click', () => {{
  lang = lang === 'tr' ? 'en' : 'tr';
  try {{ localStorage.setItem('sakinakis_lang', lang); }} catch(e) {{}}
  render();
}});

document.getElementById('themeToggle').addEventListener('click', () => {{
  theme = theme === 'dark' ? 'light' : 'dark';
  try {{ localStorage.setItem('sakinakis_theme', theme); }} catch(e) {{}}
  render();
}});

const hideInputEl = document.getElementById('hideInput');
const onlyInputEl = document.getElementById('onlyInput');
const importantInputEl = document.getElementById('importantInput');

try {{
  lang = localStorage.getItem('sakinakis_lang') || 'tr';
  theme = localStorage.getItem('sakinakis_theme') || 'dark';
  currentTab = localStorage.getItem('sakinakis_tab') || 'haber';
  hideInputEl.value = localStorage.getItem(hideStorageKey()) || '';
  onlyInputEl.value = localStorage.getItem(onlyStorageKey()) || '';
  importantInputEl.value = localStorage.getItem(importantStorageKey()) || '';
  const savedSources = localStorage.getItem('sakinakis_sources');
  if (savedSources) activeSources = new Set(JSON.parse(savedSources));
  sortMode = localStorage.getItem('sakinakis_sortmode') || 'chrono';
  const savedSeen = localStorage.getItem('sakinakis_seen');
  if (savedSeen) seenLinks = new Set(JSON.parse(savedSeen));
}} catch(e) {{ /* localStorage yoksa sessizce devam */ }}

document.getElementById('sortToggle').addEventListener('click', () => {{
  sortMode = sortMode === 'chrono' ? 'importance' : 'chrono';
  currentPage = 1;
  try {{ localStorage.setItem('sakinakis_sortmode', sortMode); }} catch(e) {{}}
  render();
}});

let filterDebounce;
function onFilterInput(){{
  clearTimeout(filterDebounce);
  filterDebounce = setTimeout(() => {{
    try {{
      localStorage.setItem(hideStorageKey(), hideInputEl.value);
      localStorage.setItem(onlyStorageKey(), onlyInputEl.value);
      localStorage.setItem(importantStorageKey(), importantInputEl.value);
    }} catch(e) {{ /* yoksay */ }}
    currentPage = 1;
    render();
  }}, 250);
}}
hideInputEl.addEventListener('input', onFilterInput);
onlyInputEl.addEventListener('input', onFilterInput);
importantInputEl.addEventListener('input', onFilterInput);

render();
</script>
</body></html>"""



def main():
    is_ci = os.environ.get("GITHUB_ACTIONS") == "true"

    print("Kaynaklar çekiliyor...")
    all_items = []
    for src in SOURCES:
        try:
            raw = fetch_feed(src["rss"])
            items = parse_items(raw, src)
            all_items.extend(items)
            print(f"  [OK] {src['name']}: {len(items)} haber")
        except Exception as e:
            print(f"  [HATA] {src['name']}: {e}")

    # Gorsel arama: yerelde (kullanicinin kendi bilgisayarinda, tarayicida
    # acilmayi bekledigi durumda) yavasligi onlemek icin atlanir, sadece
    # placeholder kullanilir. GitHub Actions'ta ise kullanici beklemedigi
    # icin (arka planda calisiyor) Wikipedia uzerinden ilgili gorselleri
    # aramaya deger -- og:image kazima yontemi guvenilir calismadigi icin
    # tamamen birakildi.
    if is_ci:
        missing = [it for it in all_items if not it.get("image")]
        if missing:
            # Oyun kaynaklari: sabit konu, kaynak basina TEK sorgu (cache'lenir)
            game_missing = [it for it in missing if it["sourceId"] in GAME_WIKI_TITLES]
            other_missing = [it for it in missing if it["sourceId"] not in GAME_WIKI_TITLES]

            if game_missing:
                print(f"\n{len(set(it['sourceId'] for it in game_missing))} oyun kaynağı için Wikipedia kapak görseli aranıyor...")
                game_image_cache = {}
                for sid in set(it["sourceId"] for it in game_missing):
                    img = fetch_wikipedia_thumbnail(GAME_WIKI_TITLES[sid], lang="en")
                    game_image_cache[sid] = img or GAME_FALLBACK_IMAGES.get(sid)
                for it in game_missing:
                    img = game_image_cache.get(it["sourceId"])
                    if img:
                        it["image"] = img

            if other_missing:
                print(f"\nGörseli olmayan {len(other_missing)} haber için Wikipedia'da ilgili görsel aranıyor...")
                with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                    future_to_item = {executor.submit(fetch_entity_image, it["title"]): it for it in other_missing}
                    for future in concurrent.futures.as_completed(future_to_item):
                        it = future_to_item[future]
                        try:
                            img = future.result()
                            if img:
                                it["image"] = img
                        except Exception:
                            pass

            found = sum(1 for it in missing if it.get("image"))
            print(f"  {found}/{len(missing)} haber için görsel bulundu")

    # Kumeleme artik AI tarafindan DOGRULANIYOR (sadece ozetlenmiyor).
    # Sezgisel eslestirme (cluster_items_for_summary) sadece ADAY gruplar
    # uretir; Claude bu adaylardan hangi basliklarin GERCEKTEN ayni olay
    # oldugunu belirleyip ozetliyor. Sonuc, her ogeye kalici bir cluster_id
    # olarak atanip client'a gonderiliyor -- boylece tarayicida (JS) artik
    # hicbir kumeleme mantigi calismiyor, sadece bu id'ye gore gruplama var.
    # Oyunlar sekmesinde kumeleme zaten kapali oldugu icin sadece haber
    # kategorisindeki ogeler adaylandiriliyor.
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    haber_items = [it for it in all_items if it["category"] == "haber"]
    candidate_groups = cluster_items_for_summary(haber_items)
    multi_candidates = [c for c in candidate_groups if len(c) >= 2]
    cluster_counter = 0
    if multi_candidates:
        validations = None
        if api_key:
            print(f"\n{len(multi_candidates)} aday küme AI ile doğrulanıyor...")
            validations = validate_and_summarize_clusters_with_ai(multi_candidates, api_key)

        if validations:
            confirmed = 0
            unvalidated = 0
            for group, result in zip(multi_candidates, validations):
                if result is None:
                    # Bu grubun batch'i basarisiz oldu -- sezgisel grubu
                    # oldugu gibi (dogrulanmamis) kullan, diger gruplar
                    # etkilenmedi.
                    unvalidated += 1
                    cluster_counter += 1
                    for it in group:
                        it["cluster_id"] = cluster_counter
                    continue
                keep_items = [group[i] for i in result["keep"] if 0 <= i < len(group)]
                if len(keep_items) >= 2:
                    cluster_counter += 1
                    confirmed += 1
                    for it in keep_items:
                        it["cluster_id"] = cluster_counter
                        if result["summary"]:
                            it["ai_summary"] = result["summary"]
            validated_total = len(multi_candidates) - unvalidated
            suffix = f" ({unvalidated} grup dogrulanamadi, sezgisel kullanildi)" if unvalidated else ""
            print(f"  {confirmed}/{validated_total} aday küme AI tarafından onaylandı{suffix}")
        else:
            if api_key:
                print("  AI doğrulaması alınamadı, sezgisel kümeler doğrulanmadan kullanılıyor")
            else:
                print(
                    f"\n{len(multi_candidates)} aday küme var ama ANTHROPIC_API_KEY "
                    "tanımlı değil, sezgisel kümeler doğrulanmadan kullanılacak"
                )
            for group in multi_candidates:
                cluster_counter += 1
                for it in group:
                    it["cluster_id"] = cluster_counter

    html = build_html(all_items)

    if is_ci:
        out_dir = "dist"
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "index.html")
    else:
        out_dir = os.path.dirname(os.path.abspath(__file__))
        out_path = os.path.join(out_dir, "sakin_akis_ciktisi.html")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\nHazır: {out_path}")
    if not is_ci:
        webbrowser.open("file://" + out_path)


if __name__ == "__main__":
    sys.exit(main())
