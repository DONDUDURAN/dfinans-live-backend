# -*- coding: utf-8 -*-
"""
2000 yılından günümüze dünyadaki büyük gelişmelere (savaş, petrol krizi, ABD
seçimleri, kıtlık/tarım şokları, banka/finans krizleri, pandemi, doğal afet,
para politikası dönüm noktaları, teknoloji/kripto balonları) piyasaların
GERÇEKTE nasıl tepki verdiğini özetleyen tarihsel senaryo veri tabanı.

Kullanicinin talebi: 'benim için 2000 yılının başından beri dünyadaki
gelişmelere piyasaların nasıl tepki verdiğini analiz eden senaryolara yaz,
mesela petrol krizi, ABD seçimleri, savaş, kıtlık gibi en az yüz adet
senaryo olsun.'

Bu dosya, dfinans_live_backend.py içindeki _SECTOR_SCENARIO_PLAYBOOK'tan
(genel/soyut şablon senaryolar) FARKLIDIR: burada anlatılanlar GERÇEKTEN
YAŞANMIŞ, tarihi belli olaylardır - amaç hem kullanıcıya eğitici bir
referans sağlamak hem de ileride (istenirse) 'şu anki durum hangi tarihsel
örneğe benziyor' tarzı bir karşılaştırma/analiz özelliğine temel oluşturmak.

Her senaryo şu alanları içerir:
  id              : benzersiz kısa kimlik
  date            : olayın tarihi/dönemi (YYYY-MM veya YYYY-MM..YYYY-MM)
  title           : olayın başlığı
  category        : kategori (Savaş/Jeopolitik, Petrol Krizi, ABD Seçimleri,
                    Finans Krizi, Pandemi/Salgın, Doğal Afet, Kıtlık/Tarım
                    Şoku, Para Politikası, Teknoloji/Kripto Balonu, Ticaret/
                    Jeopolitik-Ekonomi)
  event           : ne oldu (kısa özet)
  market_reaction : piyasaların (borsa, tahvil, dolar, altın, petrol, kripto
                    vb.) o olaya GERÇEKTE nasıl tepki verdiği
"""

from typing import Any, Dict, List

HISTORICAL_MARKET_SCENARIOS: List[Dict[str, Any]] = [
    # ---------------------------------------------------------------
    # 2000-2003: Dot-com çöküşü, 11 Eylül, Enron, Irak Savaşı
    # ---------------------------------------------------------------
    {
        "id": "dotcom_crash_2000",
        "date": "2000-03..2002-10",
        "title": "Dot-com (İnternet) Balonu Patlaması",
        "category": "Teknoloji/Kripto Balonu",
        "event": (
            "Nasdaq, kâr etmeyen internet şirketlerinin aşırı değerlenmesiyle Mart 2000'de "
            "zirve yaptı (5.048 puan), ardından 2002 Ekim'ine kadar sürekli düştü."
        ),
        "market_reaction": (
            "Nasdaq zirveden dibe %78 çöktü (5.048 -> ~1.114). Pets.com, Webvan gibi yüzlerce "
            "şirket iflas etti. Değerli/kazançlı 'eski ekonomi' hisseleri (tüketim, sağlık) görece "
            "dayanıklı kaldı. Fed faiz indirimlerine başladı (2001'de %6.5 -> %1.75). Altın bu "
            "dönemde yatay/hafif yükseldi, güvenli liman talebi henüz zayıftı."
        ),
    },
    {
        "id": "sept_11_2001",
        "date": "2001-09",
        "title": "11 Eylül Terör Saldırıları",
        "category": "Savaş/Jeopolitik",
        "event": "New York'ta İkiz Kuleler ve Pentagon'a terör saldırıları düzenlendi; NYSE 4 gün kapandı.",
        "market_reaction": (
            "Borsalar yeniden açıldığında S&P 500 tek günde %-4.9, haftada %-11.6 düştü (o zamana "
            "kadarki en kötü haftalık performanslardan biri). Havayolları/sigorta hisseleri sert "
            "vuruldu (%-40'a varan düşüşler). Altın ve ABD tahvilleri güvenli liman talebiyle "
            "yükseldi. Petrol kısa süreli sıçrama yaptı. Fed hızla faiz indirdi ve likidite pompaladı; "
            "piyasalar birkaç ay içinde büyük ölçüde toparlandı."
        ),
    },
    {
        "id": "enron_worldcom_2001_2002",
        "date": "2001-12..2002-07",
        "title": "Enron ve WorldCom Muhasebe Skandalları",
        "category": "Finans Krizi",
        "event": "Enron (Aralık 2001) ve WorldCom (Temmuz 2002) muhasebe hileleriyle iflas etti.",
        "market_reaction": (
            "Kurumsal güven sarsıldı, S&P 500 2002'de %-23 kaybetti (dot-com çöküşüyle birleşerek). "
            "Sarbanes-Oxley yasası (2002) çıkarılarak şirket denetimi sıkılaştırıldı. Kredi "
            "spreadleri genişledi, özellikle telekom sektörü hisseleri çöktü."
        ),
    },
    {
        "id": "iraq_war_2003",
        "date": "2003-03",
        "title": "ABD'nin Irak'ı İşgali",
        "category": "Savaş/Jeopolitik",
        "event": "ABD öncülüğünde koalisyon güçleri Mart 2003'te Irak'a girdi.",
        "market_reaction": (
            "Savaş öncesi belirsizlikle petrol yükseldi, savaşın hızlı başlamasıyla (Saddam rejiminin "
            "çabuk çökeceği beklentisiyle) petrol geriledi ve borsalar rahatladı - 'belirsizliğin "
            "sona ermesi' klasik tepkisi: S&P 500 savaşın ilk haftalarında %+8 toparlandı. Altın "
            "gerilemişti (savaş riski fiyatlanmıştı)."
        ),
    },
    {
        "id": "sars_2003",
        "date": "2003-02..2003-07",
        "title": "SARS Salgını",
        "category": "Pandemi/Salgın",
        "event": "Çin merkezli SARS koronavirüsü Asya'da hızla yayıldı, seyahat kısıtlamaları getirildi.",
        "market_reaction": (
            "Asya borsaları (Hong Kong Hang Seng %-10'a varan) ve havayolu/turizm hisseleri sert "
            "düştü; salgın kontrol altına alınınca birkaç ay içinde toparlandı - kısa süreli, "
            "bölgesel şok örneği."
        ),
    },
    # ---------------------------------------------------------------
    # 2004-2007: Faiz artışları, konut balonu, emtia yükselişi
    # ---------------------------------------------------------------
    {
        "id": "fed_rate_hikes_2004_2006",
        "date": "2004-06..2006-06",
        "title": "Fed'in Kademeli Faiz Artış Döngüsü",
        "category": "Para Politikası",
        "event": "Fed, 2004-2006 arasında faizi %1'den %5.25'e 17 kez ardışık olarak yükseltti.",
        "market_reaction": (
            "Borsalar döngü boyunca genelde yükseldi (ekonomi güçlüydü), ancak konut sektörü kredi "
            "maliyeti artışıyla yavaşlamaya başladı - sonraki konut balonu patlamasının tohumları "
            "burada atıldı. Dolar döngü sonunda güçlendi."
        ),
    },
    {
        "id": "us_election_2004",
        "date": "2004-11",
        "title": "ABD Başkanlık Seçimi - Bush Yeniden Seçildi",
        "category": "ABD Seçimleri",
        "event": "George W. Bush, John Kerry'ye karşı ikinci dönem için yeniden seçildi.",
        "market_reaction": (
            "Piyasa tepkisi sınırlıydı (belirsizlik zaten düşüktü, anketler Bush'u gösteriyordu); "
            "S&P 500 seçim sonrası haftada %+3.6 yükseldi - 'süreklilik' fiyatlandı, sonrasında yıl "
            "sonuna kadar ralli devam etti (Kasım-Aralık rallisi)."
        ),
    },
    {
        "id": "hurricane_katrina_2005",
        "date": "2005-08",
        "title": "Kasırga Katrina",
        "category": "Doğal Afet",
        "event": "Katrina kasırgası ABD Körfez Kıyısı'nı vurdu, New Orleans'ı sular altında bıraktı; bölgedeki petrol rafinerileri durdu.",
        "market_reaction": (
            "Petrol fiyatı ABD'de rafineri kapasitesi düşüşüyle kısa sürede varil başına $70'in "
            "üzerine sıçradı (o dönem için rekor). Sigorta şirketleri hisseleri sert düştü ($40 "
            "milyar+ hasar). Enerji hisseleri (rafinaj darboğazı nedeniyle) kısa vadede yükseldi."
        ),
    },
    {
        "id": "china_wto_2001_effect",
        "date": "2001-12..2007",
        "title": "Çin'in Dünya Ticaret Örgütü'ne (WTO) Girişi",
        "category": "Ticaret/Jeopolitik-Ekonomi",
        "event": "Çin Aralık 2001'de WTO'ya katıldı, sonraki yıllarda küresel imalatın merkezi haline geldi.",
        "market_reaction": (
            "Emtia süper döngüsünü tetikledi - bakır, demir cevheri, petrol talebi patladı, emtia "
            "ihracatçısı ülkeler (Avustralya, Brezilya) ve maden şirketleri 2000'lerin ortasında "
            "büyük ralli yaşadı. Küresel enflasyon ise ucuz Çin imalatı sayesinde uzun süre düşük "
            "kaldı ('Çin deflasyonu')."
        ),
    },
    {
        "id": "iphone_launch_2007",
        "date": "2007-06",
        "title": "İlk iPhone'un Piyasaya Sürülmesi",
        "category": "Teknoloji/Kripto Balonu",
        "event": "Apple, akıllı telefon pazarını yeniden tanımlayan ilk iPhone'u tanıttı.",
        "market_reaction": (
            "Apple hissesi sonraki 15 yılda binlerce yüzde değer kazandı; mobil uygulama/yarı iletken "
            "ekosistemi (ARM, TSMC, Qualcomm) yeni bir büyüme döngüsüne girdi - teknoloji sektörünün "
            "S&P 500 içindeki ağırlığını kalıcı olarak artıran yapısal bir dönüm noktası."
        ),
    },
    # ---------------------------------------------------------------
    # 2007-2009: Küresel Finans Krizi
    # ---------------------------------------------------------------
    {
        "id": "subprime_crisis_2007",
        "date": "2007-02..2007-12",
        "title": "Subprime Mortgage (Riskli Konut Kredisi) Krizinin Başlaması",
        "category": "Finans Krizi",
        "event": "Düşük kaliteli konut kredilerinde temerrütler artmaya başladı, New Century Financial iflas etti.",
        "market_reaction": (
            "Kredi piyasalarında ilk çatlaklar görüldü, banka hisseleri (özellikle mortgage'a maruz "
            "olanlar) düşmeye başladı; genel borsa henüz zirveye yakındı (S&P 500 Ekim 2007'de "
            "tarihi zirve yaptı) - piyasanın krizi henüz tam fiyatlamadığı bir 'sessizlik öncesi' "
            "dönemiydi."
        ),
    },
    {
        "id": "bear_stearns_2008",
        "date": "2008-03",
        "title": "Bear Stearns'ün Çöküşü",
        "category": "Finans Krizi",
        "event": "Yatırım bankası Bear Stearns likidite krizine girdi, JPMorgan tarafından Fed destekli hisse başına $2'ye satın alındı.",
        "market_reaction": (
            "Finans sektörü hisseleri sert düştü, sistemik risk endişesi arttı; Fed'in müdahalesi "
            "kısa vadeli paniği yatıştırdı ancak asıl krizin öncü sinyaliydi."
        ),
    },
    {
        "id": "oil_spike_2008",
        "date": "2008-01..2008-07",
        "title": "Petrol Fiyatının Tarihi Zirvesi ($147)",
        "category": "Petrol Krizi",
        "event": "Ham petrol (WTI) Temmuz 2008'de varil başına $147.27'ye ulaştı - talep tahminleri ve spekülasyon zirvedeydi.",
        "market_reaction": (
            "Enerji hisseleri (XLE) yılın ilk yarısında güçlü performans gösterdi; havayolları ve "
            "otomotiv sektörü yakıt maliyeti nedeniyle baskı altında kaldı. GFC'nin patlak vermesiyle "
            "petrol aynı yıl içinde $32'ye çökecekti - klasik 'talep yıkımı' örneği."
        ),
    },
    {
        "id": "lehman_brothers_2008",
        "date": "2008-09-15",
        "title": "Lehman Brothers'ın İflası",
        "category": "Finans Krizi",
        "event": "158 yıllık yatırım bankası Lehman Brothers, ABD tarihinin en büyük iflasını açıkladı.",
        "market_reaction": (
            "Dow Jones tek günde %-4.4, hafta içinde küresel borsalar %-20'ye varan kayıplar yaşadı. "
            "Kredi piyasaları dondu (LIBOR-OIS spread rekor seviyeye çıktı), para piyasası fonları "
            "'break the buck' riskiyle karşılaştı. VIX 80'in üzerine fırladı. Altın güvenli liman "
            "olarak yükseldi, ABD tahvilleri sert ralli yaptı."
        ),
    },
    {
        "id": "aig_bailout_2008",
        "date": "2008-09",
        "title": "AIG'nin Kurtarılması",
        "category": "Finans Krizi",
        "event": "Sigorta devi AIG, kredi temerrüt takası (CDS) pozisyonları nedeniyle Fed tarafından $85 milyar ile kurtarıldı.",
        "market_reaction": (
            "Sistemik risk endişesi zirveye çıktı, finans sektörü genel çapta çöktü; hükümet "
            "müdahalelerinin (bailout) sürekli genişlemesi piyasada 'ne kadar derin?' belirsizliğini "
            "artırdı, VIX yüksek seyretmeye devam etti."
        ),
    },
    {
        "id": "tarp_2008",
        "date": "2008-10",
        "title": "TARP (Sorunlu Varlık Kurtarma Programı)",
        "category": "Para Politikası",
        "event": "ABD Kongresi, bankaları kurtarmak için $700 milyarlık TARP paketini onayladı.",
        "market_reaction": (
            "İlk oylamanın reddedilmesi (29 Eylül) Dow'da tek günde %-7 düşüşe (777 puan, o zamana "
            "kadarki en büyük puansal düşüş) yol açtı; paket onaylandıktan sonra da piyasalar "
            "toparlanamadı, Kasım-Mart 2009 arası düşüş devam etti - 'kurtarma paketi' tek başına "
            "yeterli güven sağlamadı."
        ),
    },
    {
        "id": "gfc_bottom_2009",
        "date": "2009-03",
        "title": "Küresel Finans Krizi Dip Noktası",
        "category": "Finans Krizi",
        "event": "S&P 500, 9 Mart 2009'da 666 puanla krizin dibini gördü (zirveden %-57).",
        "market_reaction": (
            "Fed'in QE1 açıklaması (Mart 2009) ve banka 'stres testleri'nin beklenenden iyi çıkması "
            "ile piyasa döndü; sonraki 10+ yıl süren tarihin en uzun boğa piyasalarından biri "
            "buradan başladı. Bu, 'maksimum karamsarlıkta dip yapma' teziinin klasik örneğidir."
        ),
    },
    {
        "id": "us_election_2008",
        "date": "2008-11",
        "title": "ABD Başkanlık Seçimi - Obama Seçildi (Kriz Ortasında)",
        "category": "ABD Seçimleri",
        "event": "Barack Obama, finansal krizin tam ortasında seçimi kazandı.",
        "market_reaction": (
            "Seçim sonucu piyasada ikincil bir faktördü - asıl hareketi GFC belirliyordu; S&P 500 "
            "seçimden itibaren Mart 2009 dibine kadar düşüşe devam etti, seçim tek başına yön "
            "değiştirici olmadı."
        ),
    },
    {
        "id": "qe1_2008_2009",
        "date": "2008-11..2010-03",
        "title": "Fed'in İlk Niceliksel Genişlemesi (QE1)",
        "category": "Para Politikası",
        "event": "Fed, mortgage destekli menkul kıymet ve hazine tahvili alımlarına başladı ($1.75 trilyon).",
        "market_reaction": (
            "Risk iştahını canlandırdı, borsalar 2009 dip sonrası güçlü toparlandı; altın QE "
            "döneminde enflasyon/para basımı endişesiyle yükseldi (2011'de $1.900'e kadar)."
        ),
    },
    # ---------------------------------------------------------------
    # 2010-2013: Avrupa borç krizi, Arap Baharı, Flash Crash
    # ---------------------------------------------------------------
    {
        "id": "greek_debt_crisis_2010",
        "date": "2010-04..2010-05",
        "title": "Yunanistan Borç Krizi",
        "category": "Finans Krizi",
        "event": "Yunanistan'ın kredi notu 'çöp' seviyesine indirildi, AB/IMF kurtarma paketi gerekti.",
        "market_reaction": (
            "Euro dolar karşısında sert değer kaybetti, Avrupa bankacılık hisseleri düştü, Yunan "
            "tahvil faizleri fırladı (%10'un üzerine); küresel risk iştahı bozuldu, S&P 500 Nisan-"
            "Mayıs 2010'da %-14 düzeltme yaşadı."
        ),
    },
    {
        "id": "flash_crash_2010",
        "date": "2010-05-06",
        "title": "'Flash Crash' - Ani Çöküş",
        "category": "Finans Krizi",
        "event": "Algoritmik/yüksek frekanslı işlemler nedeniyle Dow Jones dakikalar içinde ~1.000 puan (%-9) düştü, sonra hızla toparlandı.",
        "market_reaction": (
            "Piyasa mikroyapısının kırılganlığını gösterdi; SEC/CFTC yeni 'circuit breaker' (devre "
            "kesici) kuralları getirdi. Bazı hisseler bir anlığına $0.01'e düştü/hatalı işlem gördü - "
            "sonrasında bu işlemler iptal edildi."
        ),
    },
    {
        "id": "eurozone_debt_crisis_2011_2012",
        "date": "2011-01..2012-09",
        "title": "Avrupa Egemen Borç Krizi (Portekiz, İrlanda, İtalya, Yunanistan, İspanya)",
        "category": "Finans Krizi",
        "event": "Birçok Avro Bölgesi ülkesinin borç sürdürülebilirliği sorgulandı, Euro'nun dağılma riski konuşuldu.",
        "market_reaction": (
            "Avrupa borsaları ve Euro sert baskı altında kaldı; ABD/Alman tahvilleri güvenli liman "
            "olarak ralli yaptı (Almanya negatif faize yaklaştı). Kriz, ECB Başkanı Draghi'nin "
            "Temmuz 2012'deki 'whatever it takes' (ne gerekiyorsa yaparız) açıklamasıyla döndü - "
            "tek bir söylemin piyasayı nasıl çevirebileceğinin klasik örneği."
        ),
    },
    {
        "id": "arab_spring_2011",
        "date": "2010-12..2011-12",
        "title": "Arap Baharı",
        "category": "Savaş/Jeopolitik",
        "event": "Tunus'ta başlayıp Mısır, Libya, Suriye, Yemen'e yayılan halk ayaklanmaları/rejim değişiklikleri.",
        "market_reaction": (
            "Petrol arzı endişesiyle Brent petrol $100'ün üzerine, kısa süreliğine $126'ya kadar "
            "yükseldi (Libya üretiminin durması). Altın güvenli liman talebiyle yükseldi. Mısır "
            "borsası geçici olarak kapatıldı."
        ),
    },
    {
        "id": "us_credit_downgrade_2011",
        "date": "2011-08",
        "title": "S&P'nin ABD Kredi Notunu İlk Kez İndirmesi",
        "category": "Finans Krizi",
        "event": "S&P, ABD'nin AAA kredi notunu AA+'ya indirdi (borç tavanı krizinin ardından).",
        "market_reaction": (
            "Paradoksal olarak, ABD tahvilleri (indirilen varlığın ta kendisi) güvenli liman "
            "talebiyle RALLİ yaptı (faizler düştü); borsalar ise S&P 500 tek günde %-6.7 ile sert "
            "düştü. Altın rekor kırdı ($1.900+)."
        ),
    },
    {
        "id": "fukushima_2011",
        "date": "2011-03",
        "title": "Fukushima Depremi/Tsunamisi ve Nükleer Felaket",
        "category": "Doğal Afet",
        "event": "Japonya'da 9.0 büyüklüğünde deprem ve tsunami, Fukushima nükleer santralinde erimeye yol açtı.",
        "market_reaction": (
            "Nikkei tek günde %-6, iki gün içinde toplam %-16 düştü (o zamana kadarki en büyük "
            "düşüşlerden biri). Küresel tedarik zincirleri (özellikle otomotiv/elektronik parça) "
            "kesintiye uğradı. Nükleer enerji hisseleri çöktü, doğalgaz/LNG talebi arttı (Japonya "
            "nükleeri kapatıp fosil yakıta yöneldi)."
        ),
    },
    {
        "id": "thailand_floods_2011",
        "date": "2011-07..2011-12",
        "title": "Tayland Sel Felaketi (Tedarik Zinciri Şoku)",
        "category": "Doğal Afet",
        "event": "Tayland'daki büyük seller, küresel sabit disk (HDD) ve otomotiv parça üretimini durdurdu.",
        "market_reaction": (
            "Sabit disk fiyatları küresel çapta %2 katına kadar yükseldi (arz şoku), teknoloji "
            "donanım şirketleri (Western Digital, Seagate) kısa vadede fiyatlama gücü kazandı, "
            "bilgisayar üreticileri maliyet artışı yaşadı."
        ),
    },
    {
        "id": "us_election_2012",
        "date": "2012-11",
        "title": "ABD Başkanlık Seçimi - Obama Yeniden Seçildi",
        "category": "ABD Seçimleri",
        "event": "Barack Obama, Mitt Romney'e karşı ikinci dönem için yeniden seçildi.",
        "market_reaction": (
            "S&P 500 seçim sonrası ilk iki günde %-2.4 düştü ('mali uçurum' - fiscal cliff - "
            "endişesiyle vergi/harcama belirsizliği fiyatlandı), ancak yıl sonunda uzlaşma "
            "sağlanınca piyasa toparlandı."
        ),
    },
    {
        "id": "taper_tantrum_2013",
        "date": "2013-05..2013-09",
        "title": "'Taper Tantrum' - Fed'in QE Azaltma Sinyali Paniği",
        "category": "Para Politikası",
        "event": "Fed Başkanı Bernanke, tahvil alımlarının (QE) azaltılabileceğini ima etti.",
        "market_reaction": (
            "ABD 10 yıllık tahvil faizi kısa sürede %1.6'dan %3'e fırladı; gelişen piyasa para "
            "birimleri (Hindistan rupisi, Endonezya rupiahı, Türk lirası, Brezilya reali) sert "
            "değer kaybetti ('Kırılgan Beşli' - Fragile Five tabiri burada doğdu). Altın da bu "
            "dönemde geriledi."
        ),
    },
    {
        "id": "cyprus_bailin_2013",
        "date": "2013-03",
        "title": "Kıbrıs Banka Krizi ve Mevduat 'Bail-in'i",
        "category": "Finans Krizi",
        "event": "Kıbrıs'ın banka kurtarma paketi, büyük mevduat sahiplerinin (bail-in) zarara ortak edilmesini içerdi.",
        "market_reaction": (
            "Avrupa bankacılık hisseleri baskı altında kaldı, mevduat güvenliği tartışması yeniden "
            "alevlendi; Bitcoin bu dönemde ilk büyük ilgi dalgasını yaşadı ('banka sisteminden "
            "bağımsız varlık' anlatısı güçlendi, BTC 2013'te $1.000'i ilk kez gördü)."
        ),
    },
    # ---------------------------------------------------------------
    # 2014-2017: Petrol çöküşü, Kırım, Çin devalüasyonu, Brexit, Trump
    # ---------------------------------------------------------------
    {
        "id": "crimea_annexation_2014",
        "date": "2014-02..2014-03",
        "title": "Rusya'nın Kırım'ı İlhakı",
        "category": "Savaş/Jeopolitik",
        "event": "Rusya, Ukrayna'ya ait Kırım'ı ilhak etti; Batı ülkeleri Rusya'ya yaptırım uyguladı.",
        "market_reaction": (
            "Rus borsası (RTS Endeksi) ve ruble sert düştü (%-10'a varan tek günlük kayıplar); "
            "küresel piyasalar sınırlı etkilendi (bölgesel/coğrafi kriz), altın hafif güvenli liman "
            "talebi gördü."
        ),
    },
    {
        "id": "shale_oil_price_war_2014_2016",
        "date": "2014-06..2016-02",
        "title": "OPEC-ABD Şeyl Petrolü Fiyat Savaşı ve Petrol Çöküşü",
        "category": "Petrol Krizi",
        "event": "OPEC, ABD şeyl petrolü üreticilerini piyasadan silmek için üretim kısıntısı yapmayı reddetti; arz fazlası oluştu.",
        "market_reaction": (
            "Brent petrol $115'ten (Haziran 2014) $27'ye (Ocak 2016) çöktü - %-77. Enerji sektörü "
            "hisseleri (XLE) ve yüksek borçlu şeyl üreticileri sert vuruldu, birçok küçük şirket "
            "iflas etti. Petrol ihracatçısı ülke para birimleri (Rus rublesi, Norveç kronu, "
            "Kazak tengesi) devalüe oldu. Tüketici/havayolu sektörleri düşük yakıt maliyetinden "
            "faydalandı."
        ),
    },
    {
        "id": "swiss_franc_unpeg_2015",
        "date": "2015-01",
        "title": "İsviçre Frangı'nın Euro Sabitinin Kaldırılması",
        "category": "Finans Krizi",
        "event": "İsviçre Merkez Bankası (SNB), frangın Euro'ya karşı 1.20 sabitini ani şekilde kaldırdı.",
        "market_reaction": (
            "Frank dakikalar içinde Euro'ya karşı %30'a varan sıçrama yaptı - modern döviz "
            "piyasası tarihinin en sert 'ani şok' hareketlerinden biri. Birçok forex broker'ı "
            "iflas etti (müşteri zararlarını karşılayamadı). İsviçre borsası (ihracatçı şirketler "
            "güçlü frank nedeniyle) %-10'dan fazla düştü."
        ),
    },
    {
        "id": "china_yuan_devaluation_2015",
        "date": "2015-08",
        "title": "Çin Yuanı'nın Sürpriz Devalüasyonu",
        "category": "Finans Krizi",
        "event": "Çin Merkez Bankası, yuanı iki günde %3'e yakın devalüe etti; büyüme endişeleri yeniden alevlendi.",
        "market_reaction": (
            "Küresel borsalarda 'Kara Pazartesi' (24 Ağustos 2015) yaşandı - Dow Jones açılışta "
            "1.000 puandan fazla düştü, S&P 500 günü %-3.9 kapattı. Emtia fiyatları (bakır, petrol) "
            "Çin talebi endişesiyle geriledi, gelişen piyasalar sert satış gördü."
        ),
    },
    {
        "id": "china_stock_crash_2015",
        "date": "2015-06..2015-08",
        "title": "Çin Borsası Çöküşü",
        "category": "Finans Krizi",
        "event": "Şangay Bileşik Endeksi, kredili işlem (marjin) balonunun patlamasıyla iki ayda %-40'a yakın çöktü.",
        "market_reaction": (
            "Çin hükümeti işlem durdurma, kısa satış yasağı gibi olağanüstü önlemler aldı; küresel "
            "emtia ve gelişen piyasa borsaları Çin büyüme endişesiyle satış baskısı gördü."
        ),
    },
    {
        "id": "oil_negative_and_recovery_note",
        "date": "2016-01..2016-06",
        "title": "Petrol Fiyatlarının Dipten (~$27) Toparlanması",
        "category": "Petrol Krizi",
        "event": "OPEC üretim kısıntısı sinyalleri ve talebin istikrar kazanmasıyla petrol dipten döndü.",
        "market_reaction": (
            "Brent $27'den yıl sonunda ~$57'ye toparlandı (+%111); enerji hisseleri 2016'nın en "
            "iyi performans gösteren S&P 500 sektörü oldu (XLE +%23), yüksek borçlu şeyl "
            "şirketlerinin bir kısmı ise iflastan kurtulamadı."
        ),
    },
    {
        "id": "brexit_referendum_2016",
        "date": "2016-06-23",
        "title": "Brexit Referandumu",
        "category": "Savaş/Jeopolitik",
        "event": "Birleşik Krallık, referandumda AB'den ayrılma kararı aldı (%52 Leave).",
        "market_reaction": (
            "İngiliz sterlini dolar karşısında tek günde %-8 ile 1985'ten beri en büyük düşüşünü "
            "yaşadı. FTSE 100 açılışta sert düştü ama gün içinde (zayıf sterlinin ihracatçı "
            "şirketlere faydası nedeniyle) toparlandı. Küresel borsalar 2 gün içinde satış gördü, "
            "sonra hızla toparlandı - 'beklenmedik siyasi şok, kısa vadeli panik, hızlı toparlanma' "
            "modelinin örneği. Altın güvenli liman talebiyle yükseldi."
        ),
    },
    {
        "id": "us_election_2016_trump",
        "date": "2016-11",
        "title": "ABD Başkanlık Seçimi - Trump'ın Sürpriz Zaferi",
        "category": "ABD Seçimleri",
        "event": "Donald Trump, anketlerin aksine seçimi kazandı.",
        "market_reaction": (
            "Vadeli işlemler seçim gecesi sonuç netleşirken %-5 sert düştü (belirsizlik), ancak "
            "ertesi gün piyasalar toparlanıp 'Trump rallisi'ne döndü - vergi indirimi/deregülasyon "
            "beklentisiyle S&P 500 yıl sonuna kadar +%+6 yükseldi. Küçük şirket endeksi (Russell "
            "2000) yerel odaklı politika beklentisiyle daha da güçlü ralli yaptı (+%+13). Dolar "
            "ve tahvil faizleri (mali genişleme beklentisiyle) yükseldi, altın geriledi."
        ),
    },
    {
        "id": "italian_banking_crisis_2016",
        "date": "2016-07..2016-12",
        "title": "İtalyan Bankacılık Krizi",
        "category": "Finans Krizi",
        "event": "Monte dei Paschi başta olmak üzere İtalyan bankaları takipteki kredi (NPL) yükü altında ezildi.",
        "market_reaction": (
            "İtalyan banka hisseleri %-50'ye varan kayıplar yaşadı; Aralık 2016'daki anayasa "
            "referandumunun kaybedilmesi (Renzi istifası) belirsizliği artırdı ama piyasa şaşırtıcı "
            "şekilde sınırlı tepki verdi (beklenti zaten olumsuzdu)."
        ),
    },
    {
        "id": "bitcoin_2017_bull_run",
        "date": "2017-01..2017-12",
        "title": "Bitcoin'in İlk Büyük Boğa Piyasası (~$20.000)",
        "category": "Teknoloji/Kripto Balonu",
        "event": "Bitcoin, ICO (jeton arzı) çılgınlığı ve perakende ilgisiyle yıl içinde $1.000'den $20.000'e fırladı.",
        "market_reaction": (
            "Kripto piyasası toplam değeri $800 milyara ulaştı; 2018 başında balon patladı, BTC "
            "%-84 çökerek ~$3.200'e geriledi ('kripto kışı' - crypto winter dönemi başladı)."
        ),
    },
    {
        "id": "north_korea_missile_tests_2017",
        "date": "2017-07..2017-11",
        "title": "Kuzey Kore Füze/Nükleer Denemeleri",
        "category": "Savaş/Jeopolitik",
        "event": "Kuzey Kore, ABD'yi hedef alabilecek menzilde füze denemeleri ve 6. nükleer denemesini yaptı.",
        "market_reaction": (
            "Jeopolitik gerginlik zirvelerinde VIX kısa süreli sıçramalar yaptı, Güney Kore "
            "(KOSPI) ve Japon borsaları hafif satış gördü; altın güvenli liman talebiyle yükseldi. "
            "Ancak etkiler geçiciydi, tam ölçekli çatışma gerçekleşmedi."
        ),
    },
    # ---------------------------------------------------------------
    # 2018-2019: Ticaret savaşı, Fed sıkılaşması, repo krizi
    # ---------------------------------------------------------------
    {
        "id": "us_china_trade_war_2018",
        "date": "2018-03..2019-12",
        "title": "ABD-Çin Ticaret Savaşı",
        "category": "Ticaret/Jeopolitik-Ekonomi",
        "event": "Trump yönetimi Çin ithalatına kademeli olarak yüzlerce milyar dolarlık tarife uyguladı, Çin karşılık verdi.",
        "market_reaction": (
            "Tarife açıklamaları/tweet'leri her seferinde borsalarda ani %-1 ila %-3 düşüşlere yol "
            "açtı (özellikle sanayi/tarım/teknoloji hisseleri). Soya fasulyesi fiyatları Çin'in "
            "misilleme tarifeleriyle çöktü, ABD çiftçileri devlet desteğine muhtaç kaldı. Yuan "
            "zayıfladı. Genel borsa 2018-2019 boyunca ticaret haberlerine göre yüksek volatilite "
            "yaşadı ('tweet riski' kavramı yerleşti)."
        ),
    },
    {
        "id": "turkey_lira_crisis_2018",
        "date": "2018-08",
        "title": "Türkiye Lirası Krizi",
        "category": "Finans Krizi",
        "event": "ABD ile diplomatik kriz ve cari açık endişeleriyle Türk lirası dolar karşısında çöktü.",
        "market_reaction": (
            "TRY/USD tek günde %-18'e varan kayıplar yaşadı, Türkiye borsası ve tahvilleri sert "
            "satış gördü; bulaşma etkisiyle diğer gelişen piyasa para birimleri (Güney Afrika "
            "randı, Arjantin pesosu) de baskı altında kaldı."
        ),
    },
    {
        "id": "fed_hikes_dec_2018_selloff",
        "date": "2018-10..2018-12",
        "title": "Fed'in Sıkılaşması ve 'Aralık 2018 Çöküşü'",
        "category": "Para Politikası",
        "event": "Fed faiz artırmaya ve bilanço küçültmeye (QT) devam etti; Powell 'otopilot' sıkılaşma sinyali verdi.",
        "market_reaction": (
            "S&P 500, Aralık 2018'de %-9 düşerek 1931'den beri en kötü Aralık ayını yaşadı ('Noel "
            "Arifesi Katliamı' - Christmas Eve Massacre); Fed'in Ocak 2019'da şahin duruşundan "
            "vazgeçip 'sabırlı' olacağını açıklamasıyla piyasa yıl içinde en güçlü toparlanmalardan "
            "birini yaşadı (+%+29, 2019 tam yıl)."
        ),
    },
    {
        "id": "repo_crisis_2019",
        "date": "2019-09",
        "title": "Repo Piyasası Krizi",
        "category": "Finans Krizi",
        "event": "Bankalar arası gecelik repo faizleri %10'a fırladı (banka sisteminde likidite sıkışıklığı).",
        "market_reaction": (
            "Fed acil repo operasyonlarına ve bilanço genişletmeye (teknik olarak 'QE değil' denen "
            "ama etkisi benzer bir programa) geri döndü; genel borsa etkisi sınırlı kaldı ama "
            "bankacılık sektöründe likidite yönetimi endişesi arttı."
        ),
    },
    # ---------------------------------------------------------------
    # 2020: COVID-19 pandemisi
    # ---------------------------------------------------------------
    {
        "id": "covid_crash_2020",
        "date": "2020-02-20..2020-03-23",
        "title": "COVID-19 Pandemi Çöküşü",
        "category": "Pandemi/Salgın",
        "event": "COVID-19'un küresel yayılması ve ülkelerin karantinaya girmesiyle ekonomik aktivite durdu.",
        "market_reaction": (
            "S&P 500, 33 günde %-34 çöktü (tarihin en hızlı bear market'lerinden biri). VIX 82'ye "
            "fırladı (rekor). Petrol talebi çöktü (uçuşlar durdu), WTI Nisan 2020'de tarihte ilk "
            "kez NEGATİF fiyata (-$37) düştü. Altın ilk şokta (likidite ihtiyacıyla) düştü, sonra "
            "hızla toparlanıp yeni zirveler yaptı. Havayolları/otel/enerji sektörü %-60'a varan "
            "kayıplar yaşadı; e-ticaret/bulut/ilaç şirketleri (Amazon, Zoom, Moderna) yükseldi."
        ),
    },
    {
        "id": "fed_zero_rate_qe_infinity_2020",
        "date": "2020-03",
        "title": "Fed'in Acil Faiz İndirimi ve 'QE Sonsuz'",
        "category": "Para Politikası",
        "event": "Fed, faizi acilen sıfıra indirdi ve sınırsız tahvil alım programı (QE Infinity) açıkladı.",
        "market_reaction": (
            "23 Mart 2020, S&P 500 için pandemi dibi oldu; sonrasında tarihin en hızlı "
            "toparlanmalarından biri yaşandı (S&P 500, 2020 sonunda +%+16 ile yılı POZİTİF kapattı - "
            "dipten zirveye 5 ayda önceki tüm kaybı telafi etti). Teknoloji hisseleri (Nasdaq) "
            "özellikle güçlü ralli yaptı."
        ),
    },
    {
        "id": "oil_negative_price_2020",
        "date": "2020-04-20",
        "title": "Petrolün Negatif Fiyatlanması",
        "category": "Petrol Krizi",
        "event": "WTI vadeli kontratı, depolama kapasitesi dolması nedeniyle tarihte ilk kez -$37.63'e düştü.",
        "market_reaction": (
            "Enerji şirketleri (özellikle şeyl üreticileri) üretim kesintisine gitti, birçok küçük "
            "üretici iflas etti; OPEC+ tarihin en büyük üretim kesintisi anlaşmasını (günlük 9.7 "
            "milyon varil) yaptı - petrol sonraki 2 yılda kademeli olarak $130'a kadar toparlanacaktı."
        ),
    },
    {
        "id": "us_election_2020",
        "date": "2020-11",
        "title": "ABD Başkanlık Seçimi - Biden'ın Zaferi",
        "category": "ABD Seçimleri",
        "event": "Joe Biden, Donald Trump'a karşı seçimi kazandı; sonuç günlerce netleşmedi.",
        "market_reaction": (
            "Belirsizliğe rağmen piyasa 'mavi dalga' olmaması (Senato'nun Cumhuriyetçilerde "
            "kalması ihtimali) beklentisiyle rahatladı, S&P 500 seçim haftasında +%+7.3 yükseldi - "
            "'bölünmüş hükümet = daha az radikal politika değişikliği' teziyle piyasa dostu "
            "algılandı."
        ),
    },
    {
        "id": "covid_vaccine_rally_2020",
        "date": "2020-11-09",
        "title": "Pfizer/BioNTech Aşı Etkinlik Haberi",
        "category": "Pandemi/Salgın",
        "event": "Pfizer-BioNTech, aşısının %90'ın üzerinde etkili olduğunu açıkladı.",
        "market_reaction": (
            "'Yeniden açılma' (reopening) hisseleri (havayolları, oteller, enerji) tek günde %+10-20 "
            "sıçradı; buna karşılık 'evde kal' kazananları (Zoom, Peloton) düştü - keskin bir "
            "sektörel rotasyon (rotation) örneği."
        ),
    },
    # ---------------------------------------------------------------
    # 2021: Meme hisseler, Suez, Evergrande, tedarik krizi
    # ---------------------------------------------------------------
    {
        "id": "gamestop_short_squeeze_2021",
        "date": "2021-01",
        "title": "GameStop/AMC 'Meme Hisse' Kısa Sıkıştırması",
        "category": "Finans Krizi",
        "event": "Reddit topluluğu (WallStreetBets), kurumsal kısa satıcılara karşı GameStop hissesini koordineli alarak sıkıştırdı.",
        "market_reaction": (
            "GameStop hissesi bir ayda %+1.700'e varan artış gösterdi; bazı hedge fonlar (Melvin "
            "Capital) milyarlarca dolar zarar edip kapandı. Robinhood gibi aracı kurumlar alım "
            "kısıtlaması getirdi, SEC soruşturma başlattı - perakende yatırımcı gücünün ilk büyük "
            "gösterisi."
        ),
    },
    {
        "id": "suez_canal_blockage_2021",
        "date": "2021-03",
        "title": "Süveyş Kanalı Tıkanması (Ever Given)",
        "category": "Kıtlık/Tarım Şoku",
        "event": "Dev konteyner gemisi Ever Given, Süveyş Kanalı'nı 6 gün boyunca tıkadı; küresel ticaretin %12'si buradan geçiyordu.",
        "market_reaction": (
            "Petrol fiyatları kısa süreli sıçrama yaptı (tanker gecikmeleri), navlun (freight) "
            "maliyetleri fırladı; olay tek başına küçük ama zaten kırılgan olan küresel tedarik "
            "zincirinin sembolü haline geldi."
        ),
    },
    {
        "id": "evergrande_crisis_2021",
        "date": "2021-08..2021-12",
        "title": "Evergrande (Çin Emlak Devi) Borç Krizi",
        "category": "Finans Krizi",
        "event": "Çin'in en büyük emlak geliştiricilerinden Evergrande, $300 milyarın üzerinde borçla temerrüde düştü.",
        "market_reaction": (
            "Çin emlak/finans hisseleri sert düştü, küresel piyasalarda 'Çin'in Lehman anı mı?' "
            "endişesi yayıldı (Eylül 2021'de S&P 500 %-1.7 tek günlük düşüş yaşadı); Çin hükümetinin "
            "kontrollü tasfiye yaklaşımıyla sistemik bir küresel krize dönüşmedi ama Çin emlak "
            "sektöründe çok yıllı bir durgunluk başlattı."
        ),
    },
    {
        "id": "global_supply_chain_crisis_2021",
        "date": "2021-06..2022-06",
        "title": "Küresel Tedarik Zinciri Krizi",
        "category": "Kıtlık/Tarım Şoku",
        "event": "Pandemi sonrası talep patlaması, liman tıkanıklıkları ve konteyner kıtlığı tedarik zincirlerini kilitledi.",
        "market_reaction": (
            "Navlun maliyetleri 10 kata kadar arttı, enflasyon 'geçici değil kalıcı' olduğu "
            "anlaşıldı - bu durum sonraki agresif Fed faiz artış döngüsünün temel nedenlerinden "
            "biri oldu. Otomotiv üreticileri çip kıtlığı nedeniyle üretim durdurdu."
        ),
    },
    {
        "id": "chip_shortage_2020_2022",
        "date": "2020-12..2022-12",
        "title": "Küresel Çip (Yarı İletken) Kıtlığı",
        "category": "Kıtlık/Tarım Şoku",
        "event": "Pandemi kaynaklı talep kaymaları ve fabrika kapanmaları küresel çip arzını daralttı.",
        "market_reaction": (
            "Yarı iletken üreticileri (TSMC, NVIDIA, AMD) fiyatlama gücü kazanıp OLUMLU etkilendi; "
            "otomotiv üreticileri (Ford, GM, Toyota) üretim durdurmak zorunda kaldı, milyonlarca "
            "araç üretilemedi - sektörler arası tam ters etki örneği."
        ),
    },
    # ---------------------------------------------------------------
    # 2022: Rusya-Ukrayna savaşı, enflasyon, Fed sıkılaşması, kripto çöküşü
    # ---------------------------------------------------------------
    {
        "id": "russia_ukraine_war_2022",
        "date": "2022-02-24",
        "title": "Rusya'nın Ukrayna'yı İşgali",
        "category": "Savaş/Jeopolitik",
        "event": "Rusya, Ukrayna'ya tam ölçekli işgal başlattı; Batı ağır yaptırımlar (SWIFT'ten çıkarma dahil) uyguladı.",
        "market_reaction": (
            "Brent petrol $139'a fırladı (2008'den beri en yüksek), doğalgaz Avrupa'da rekor "
            "kırdı. Buğday/mısır fiyatları (Rusya-Ukrayna küresel buğdayın %30'unu sağlıyordu) "
            "%+50'ye varan sıçrama yaptı - küresel gıda güvenliği krizi endişesi. Rus borsası "
            "işlemleri durduruldu, ruble çöktü (sonra sermaye kontrolleriyle toparlandı). Savunma "
            "sanayi hisseleri (Lockheed Martin, Rheinmetall) yükseldi. Altın güvenli liman "
            "talebiyle ralli yaptı."
        ),
    },
    {
        "id": "ukraine_grain_export_crisis_2022",
        "date": "2022-02..2022-07",
        "title": "Ukrayna Tahıl İhracat Krizi ve Karadeniz Tahıl Koridoru",
        "category": "Kıtlık/Tarım Şoku",
        "event": "Rusya'nın Karadeniz limanlarını abluka altına almasıyla Ukrayna tahıl ihracatı durdu, Temmuz 2022'de BM/Türkiye arabuluculuğunda koridor anlaşması sağlandı.",
        "market_reaction": (
            "Buğday vadeli fiyatları savaşın ilk haftalarında rekor seviyelere ($13/bushel) "
            "ulaştı; Afrika/Orta Doğu'daki gıda ithalatçısı ülkelerde enflasyon ve sosyal "
            "huzursuzluk riski arttı. Koridor anlaşmasıyla fiyatlar kademeli geriledi."
        ),
    },
    {
        "id": "inflation_surge_2022",
        "date": "2022-01..2022-06",
        "title": "ABD Enflasyonunun 40 Yılın Zirvesine Çıkması (%9.1)",
        "category": "Para Politikası",
        "event": "ABD TÜFE Haziran 2022'de yıllık %9.1'e ulaştı - 1981'den beri en yüksek seviye.",
        "market_reaction": (
            "Her enflasyon verisi açıklaması piyasada %-2 ila %-4'e varan ani düşüşlere yol açtı; "
            "büyüme/teknoloji hisseleri iskonto oranı artışıyla en çok etkilenen grup oldu (Nasdaq "
            "2022'de %-33 kaybetti, S&P 500 %-19)."
        ),
    },
    {
        "id": "fed_aggressive_hikes_2022_2023",
        "date": "2022-03..2023-07",
        "title": "Fed'in Agresif Faiz Artış Döngüsü (%0 -> %5.5)",
        "category": "Para Politikası",
        "event": "Fed, enflasyonla mücadele için 40 yılın en hızlı faiz artış döngüsünü uyguladı (11 artış).",
        "market_reaction": (
            "2022, hem hisse senedi hem tahvil piyasasının aynı yıl düştüğü nadir yıllardan biri "
            "oldu ('60/40 portföyün en kötü yılı'). Dolar endeksi (DXY) 20 yılın zirvesine çıktı. "
            "Büyüme hisseleri ve kripto sert düştü; 2023'te enflasyonun yavaşladığı sinyalleriyle "
            "borsa güçlü toparlandı (S&P 500 2023'te +%+24)."
        ),
    },
    {
        "id": "terra_luna_collapse_2022",
        "date": "2022-05",
        "title": "Terra/Luna Kripto Ekosisteminin Çöküşü",
        "category": "Teknoloji/Kripto Balonu",
        "event": "Algoritmik stabilcoin UST, sabitini kaybetti; kardeş jetonu LUNA günler içinde $80'den neredeyse $0'a çöktü.",
        "market_reaction": (
            "~$40 milyar piyasa değeri silindi; kripto piyasası genelinde güven sarsıldı, Bitcoin "
            "$40.000'lardan $20.000'lerin altına düştü. Bu olay, sonraki kripto şirket "
            "iflaslarının (Celsius, Voyager, Three Arrows Capital) da tetikleyicisi oldu."
        ),
    },
    {
        "id": "uk_minibudget_crisis_2022",
        "date": "2022-09",
        "title": "İngiltere 'Mini Bütçe' Krizi (Truss Hükümeti)",
        "category": "Finans Krizi",
        "event": "Başbakan Liz Truss'ın finansmanı belirsiz büyük vergi indirimi paketi piyasada güven krizine yol açtı.",
        "market_reaction": (
            "İngiliz sterlini tarihi dip seviyeye ($1.03) çöktü, İngiliz tahvil (gilt) faizleri "
            "fırladı - emeklilik fonlarının LDI (liability-driven investment) stratejileri "
            "nedeniyle marjin çağrısı sarmalına girdi. Bank of England acil tahvil alım "
            "programıyla müdahale etti. Truss, tarihin en kısa süreli (49 gün) İngiliz "
            "başbakanı olarak istifa etti."
        ),
    },
    {
        "id": "ftx_collapse_2022",
        "date": "2022-11",
        "title": "FTX Kripto Borsasının Çöküşü",
        "category": "Teknoloji/Kripto Balonu",
        "event": "Dünyanın 2. büyük kripto borsası FTX, müşteri fonlarının kötüye kullanıldığının ortaya çıkmasıyla günler içinde iflas etti.",
        "market_reaction": (
            "Bitcoin $21.000'den $15.500'e çöktü (kripto piyasasının 2022 dip noktası); FTX'in "
            "kendi jetonu FTT değersizleşti, kurucu Sam Bankman-Fried sonradan dolandırıcılıktan "
            "mahkum oldu. Kripto piyasasında kurumsal güven yıllarca yara aldı."
        ),
    },
    # ---------------------------------------------------------------
    # 2023: Banka krizleri, borç tavanı, İsrail-Hamas, AI patlaması
    # ---------------------------------------------------------------
    {
        "id": "svb_collapse_2023",
        "date": "2023-03-10",
        "title": "Silicon Valley Bank (SVB) İflası",
        "category": "Finans Krizi",
        "event": "Girişim sermayesi odaklı SVB, tahvil portföyü zararları ve banka hücumu (bank run) sonucu 2008'den beri en büyük ABD banka iflasını yaşadı.",
        "market_reaction": (
            "Bölgesel banka hisseleri (KRE endeksi) %-30'a varan kayıplar yaşadı; FDIC/Fed tüm "
            "mevduatları (limit üstü dahil) garanti altına alarak bulaşmayı sınırladı. Kripto "
            "piyasası (USDC stabilcoin'i SVB'de fon tuttuğu için) kısa süreli sabit değerini "
            "kaybetti."
        ),
    },
    {
        "id": "credit_suisse_collapse_2023",
        "date": "2023-03-19",
        "title": "Credit Suisse'in UBS Tarafından Kurtarılması",
        "category": "Finans Krizi",
        "event": "167 yıllık İsviçre bankası Credit Suisse, güven krizi sonucu İsviçre hükümeti destekli şekilde UBS'e devredildi.",
        "market_reaction": (
            "Avrupa bankacılık hisseleri sert düştü; Credit Suisse'in AT1 (koşullu sermaye) "
            "tahvilleri sıfırlandı ($17 milyar), bu da global AT1 tahvil piyasasında güven "
            "sarsıntısına yol açtı. Küresel sistemik risk endişesi kısa sürede yatıştı."
        ),
    },
    {
        "id": "us_debt_ceiling_2023",
        "date": "2023-01..2023-06",
        "title": "ABD Borç Tavanı Krizi",
        "category": "Finans Krizi",
        "event": "ABD Hazinesi'nin borç tavanına ulaşması ve Kongre'nin anlaşma sağlayamaması temerrüt riskini gündeme getirdi.",
        "market_reaction": (
            "Kısa vadeli hazine bonosu (T-bill) faizleri anormal şekilde yükseldi, CDS (temerrüt "
            "sigortası) maliyetleri arttı; Haziran 2023'te son anda anlaşma sağlanınca piyasa "
            "rahatladı - benzer 2011 krizinden farklı olarak bu kez kredi notu indirimi hemen "
            "gelmedi (Fitch Ağustos 2023'te indirdi)."
        ),
    },
    {
        "id": "ai_boom_chatgpt_nvidia_2023",
        "date": "2022-11..2024-12",
        "title": "Yapay Zeka (AI) Yatırım Patlaması - ChatGPT ve Nvidia Rallisi",
        "category": "Teknoloji/Kripto Balonu",
        "event": "OpenAI'nin ChatGPT'yi tanıtması (Kasım 2022) küresel AI yatırım yarışını başlattı.",
        "market_reaction": (
            "Nvidia hissesi 2023-2024'te birkaç kat değer kazanarak dünyanın en değerli "
            "şirketlerinden biri oldu (yapay zeka çipi talebi patlaması); 'Muhteşem Yedili' "
            "(Magnificent Seven: Apple, Microsoft, Google, Amazon, Nvidia, Meta, Tesla) S&P 500 "
            "getirisinin büyük kısmını tek başına sürükledi - endeks içi yoğunlaşma riski "
            "(konsantrasyon) tartışması gündeme geldi."
        ),
    },
    {
        "id": "israel_hamas_war_2023",
        "date": "2023-10-07",
        "title": "İsrail-Hamas Savaşı",
        "category": "Savaş/Jeopolitik",
        "event": "Hamas'ın İsrail'e saldırısı ve ardından İsrail'in Gazze'ye kara/hava operasyonu başlattı.",
        "market_reaction": (
            "Petrol fiyatları bölgesel yayılma endişesiyle kısa süreli %+4-5 sıçradı (ama bölgesel "
            "petrol arzı doğrudan etkilenmediği için kalıcı olmadı); altın güvenli liman talebiyle "
            "yükseldi. Savunma sanayi hisseleri (Lockheed Martin, RTX) yükseldi. Genel küresel "
            "borsa etkisi sınırlı kaldı (bölgesel/coğrafi olarak izole kriz)."
        ),
    },
    {
        "id": "first_republic_collapse_2023",
        "date": "2023-05",
        "title": "First Republic Bank'ın İflası",
        "category": "Finans Krizi",
        "event": "First Republic, SVB krizinin ardından mevduat kaçışı yaşadı ve JPMorgan tarafından devralındı - 2023'ün en büyük banka iflası.",
        "market_reaction": (
            "Bölgesel banka hisseleri yeniden baskı altına girdi; JPMorgan'ın devralması piyasada "
            "'en kötüsü geride kaldı' algısını güçlendirdi, bankacılık krizi daha fazla yayılmadı."
        ),
    },
    # ---------------------------------------------------------------
    # 2024-2025: Seçim, faiz indirimleri, yen carry trade, BTC ETF, savaşlar
    # ---------------------------------------------------------------
    {
        "id": "bitcoin_etf_approval_2024",
        "date": "2024-01-10",
        "title": "ABD'de Spot Bitcoin ETF'lerinin Onaylanması",
        "category": "Teknoloji/Kripto Balonu",
        "event": "SEC, BlackRock (IBIT) dahil 11 spot Bitcoin ETF başvurusunu onayladı - kurumsal erişimde dönüm noktası.",
        "market_reaction": (
            "Bitcoin, kurumsal talep akışıyla 2024 boyunca kademeli yükselerek Mart 2024'te ilk "
            "kez $73.000'i, Aralık 2024'te ise $100.000'i aştı; ETF'lere toplam onlarca milyar "
            "dolar giriş oldu - kripto piyasasının kurumsallaşmasında dönüm noktası kabul edilir."
        ),
    },
    {
        "id": "iran_israel_strikes_2024",
        "date": "2024-04",
        "title": "İran'ın İsrail'e Doğrudan Füze/Drone Saldırısı",
        "category": "Savaş/Jeopolitik",
        "event": "İran, Şam'daki konsolosluğuna yapılan saldırıya karşılık İsrail'e doğrudan yüzlerce füze/drone fırlattı.",
        "market_reaction": (
            "Petrol kısa süreli %+3 sıçradı, altın rekor yakınında güvenli liman talebi gördü; "
            "saldırının büyük ölçüde savunma sistemleriyle engellenmesi ve tam ölçekli bölgesel "
            "savaşa dönüşmemesi piyasa tepkisini sınırlı/geçici tuttu."
        ),
    },
    {
        "id": "yen_carry_trade_unwind_2024",
        "date": "2024-07-31..2024-08-05",
        "title": "Yen Carry Trade'in Çözülmesi (5 Ağustos 2024 Çöküşü)",
        "category": "Finans Krizi",
        "event": "Japonya Merkez Bankası'nın (BOJ) beklenmedik faiz artışı, düşük faizli yen borçlanıp yüksek getirili varlıklara (ABD hisseleri, kripto) yatırım yapan 'carry trade' pozisyonlarının aniden kapatılmasına yol açtı.",
        "market_reaction": (
            "Japon Nikkei endeksi 5 Ağustos 2024'te tek günde %-12.4 ile 1987'den beri en büyük "
            "düşüşünü yaşadı. Bitcoin %-15'e varan ani düşüş gösterdi, Nasdaq %-6'ya yakın satış "
            "gördü. Yen tek haftada dolar karşısında sert değer kazandı. Birkaç gün içinde "
            "piyasalar büyük ölçüde toparlandı - kaldıraçlı pozisyonların hızlı tasfiyesinin "
            "(deleveraging) klasik örneği."
        ),
    },
    {
        "id": "fed_pivot_rate_cuts_2024",
        "date": "2024-09",
        "title": "Fed'in Faiz İndirim Döngüsüne Başlaması",
        "category": "Para Politikası",
        "event": "Fed, Eylül 2024'te enflasyonun yavaşlaması nedeniyle 4 yıl aradan sonra ilk faiz indirimini (0.50 puan) yaptı.",
        "market_reaction": (
            "S&P 500 yeni zirveler yaptı ('yumuşak iniş' - soft landing - senaryosu fiyatlandı); "
            "küçük şirket hisseleri (Russell 2000) düşük faiz beklentisiyle güçlü tepki verdi. "
            "Altın rekor seviyelere ($2.600+) yükseldi."
        ),
    },
    {
        "id": "us_election_2024_trump",
        "date": "2024-11",
        "title": "ABD Başkanlık Seçimi - Trump'ın İkinci Kez Seçilmesi",
        "category": "ABD Seçimleri",
        "event": "Donald Trump, Kamala Harris'e karşı ikinci başkanlık dönemi için seçildi; Cumhuriyetçiler Kongre'nin her iki kanadını da kazandı.",
        "market_reaction": (
            "'Trump ticareti' (Trump trade) hızla fiyatlandı: küçük şirketler (Russell 2000) "
            "vergi indirimi/deregülasyon beklentisiyle sıçradı, banka hisseleri düzenleme "
            "gevşemesi beklentisiyle yükseldi, Bitcoin kripto-dostu politika beklentisiyle "
            "kısa sürede $100.000'i aştı. Dolar ve tahvil faizleri (mali genişleme/tarife "
            "enflasyonu beklentisiyle) yükseldi. Meksika/Çin'e maruz kalan şirketler (tarife "
            "riski) baskı gördü."
        ),
    },
    {
        "id": "trump_tariffs_2025",
        "date": "2025-01..2025-04",
        "title": "Trump'ın Kapsamlı Tarife Uygulamaları ('Kurtuluş Günü')",
        "category": "Ticaret/Jeopolitik-Ekonomi",
        "event": "Trump yönetimi, Kanada/Meksika/Çin başta olmak üzere tüm ticaret ortaklarına kapsamlı yeni tarifeler açıkladı.",
        "market_reaction": (
            "S&P 500, Nisan 2025 tarife açıklamasının ardından birkaç gün içinde %-12'ye varan "
            "sert düşüş yaşadı (2020'den beri en hızlı düşüşlerden biri); tahvil piyasasında da "
            "olağandışı satış görülmesi (genelde risk-off döneminde tahvil ralli yapar) piyasada "
            "'ABD varlıklarına güven sorgulanıyor' endişesi yarattı. Kısmi tarife ertelemeleri "
            "açıklanınca piyasa hızla toparlandı - yüksek volatilite/politika belirsizliği "
            "dönemi örneği."
        ),
    },
    {
        "id": "bitcoin_120k_to_60k_cycle_2025",
        "date": "2025-01..2025-06",
        "title": "Bitcoin'in $120.000 Zirvesinden Sert Düzeltmesi",
        "category": "Teknoloji/Kripto Balonu",
        "event": "Bitcoin, kurumsal ETF girişleri ve 'Trump rallisi' ile $120.000 civarı yeni bir zirve yaptıktan sonra makro likidite sıkılaşması ve kâr realizasyonuyla sert düzeltmeye girdi.",
        "market_reaction": (
            "BTC zirveden %-50'ye varan bir düzeltmeyle $60.000'ler bölgesine geriledi - kripto "
            "piyasasının klasik 'coşku zirvesi -> sert düzeltme -> uzun konsolidasyon' döngüsünün "
            "yeni bir örneği. Kaldıraçlı pozisyonların tasfiyesi (likidasyon) düşüşü hızlandırdı; "
            "önceki döngülerde (2018, 2022) olduğu gibi dip sonrası uzun bir yatay/toparlanma "
            "sürecinin başlangıcı olarak değerlendirilir."
        ),
    },
    # ---------------------------------------------------------------
    # Ek senaryolar: Latin Amerika/gelişen piyasa krizleri, enerji/altyapı
    # şokları, doğal afetler, siber saldırılar, tekil şirket/piyasa olayları
    # ---------------------------------------------------------------
    {
        "id": "argentina_default_2001",
        "date": "2001-12",
        "title": "Arjantin'in Devlet Borcu Temerrüdü",
        "category": "Finans Krizi",
        "event": "Arjantin, dolar sabitinin (convertibility) çöküşü ve ekonomik krizle $100 milyarın üzerinde dış borcunda temerrüde düştü - o zamana kadarki en büyük egemen temerrüt.",
        "market_reaction": (
            "Arjantin pesosu dolar sabitinden koparılıp %-70'e varan değer kaybetti, banka "
            "mevduatlarına 'corralito' (mevduat dondurma) uygulandı; Latin Amerika borsalarında "
            "bulaşma etkisiyle satış görüldü, ülke yıllarca uluslararası sermaye piyasalarından "
            "dışlandı."
        ),
    },
    {
        "id": "euro_cash_launch_2002",
        "date": "2002-01",
        "title": "Euro'nun Fiziki Para Birimi Olarak Tedavüle Girmesi",
        "category": "Para Politikası",
        "event": "12 Avrupa ülkesi, ulusal para birimlerini bırakıp ortak Euro banknot/madeni parasını kullanmaya başladı.",
        "market_reaction": (
            "Uzun vadeli yapısal bir değişimdi - Euro, doların yanında ikinci büyük rezerv para "
            "birimi haline geldi; kısa vadeli piyasa etkisi sınırlıydı ama Avrupa'da tek para "
            "politikasının (ECB) tüm üye ülkelere uygulanması sonraki borç krizlerinin (2010-2012) "
            "yapısal zeminini oluşturdu."
        ),
    },
    {
        "id": "dubai_world_debt_crisis_2009",
        "date": "2009-11",
        "title": "Dubai World Borç Krizi",
        "category": "Finans Krizi",
        "event": "Dubai'nin devlet şirketi Dubai World, $59 milyar borcunda ödeme erteleme talep etti.",
        "market_reaction": (
            "Küresel borsalarda kısa süreli satış baskısı oluştu (Dubai borsası %-7 düştü); Abu "
            "Dabi'nin mali destek sağlamasıyla kriz büyümeden kontrol altına alındı, etkisi "
            "bölgesel kaldı."
        ),
    },
    {
        "id": "deepwater_horizon_spill_2010",
        "date": "2010-04",
        "title": "Deepwater Horizon Petrol Sızıntısı (BP)",
        "category": "Doğal Afet",
        "event": "BP'nin Meksika Körfezi'ndeki Deepwater Horizon platformu patladı, tarihin en büyük deniz petrol sızıntısına yol açtı.",
        "market_reaction": (
            "BP hissesi birkaç ay içinde %-55 çöktü (temizlik maliyeti, tazminat ve ceza "
            "riskiyle); ABD, derin deniz sondaj faaliyetlerine geçici moratoryum getirdi, "
            "offshore sondaj şirketleri (Transocean) de sert düştü."
        ),
    },
    {
        "id": "greek_referendum_2015",
        "date": "2015-07",
        "title": "Yunanistan'ın Kurtarma Paketi Referandumu ('Oxi')",
        "category": "Finans Krizi",
        "event": "Yunan halkı referandumda AB/IMF'in önerdiği kemer sıkma koşullarını reddetti ('Oxi' - Hayır), Grexit (Yunanistan'ın Euro'dan çıkışı) riski gündeme geldi.",
        "market_reaction": (
            "Yunan borsası ve bankaları haftalarca kapalı kaldı, mevduat çekimlerine günlük "
            "€60 limiti getirildi; küresel piyasalarda kısa süreli risk iştahı azaldı, ancak "
            "birkaç hafta sonra üçüncü bir kurtarma paketiyle Grexit önlendi."
        ),
    },
    {
        "id": "puerto_rico_debt_crisis_2015",
        "date": "2015-06..2017-05",
        "title": "Porto Riko Borç Krizi",
        "category": "Finans Krizi",
        "event": "ABD toprağı Porto Riko, $70 milyarın üzerinde borcunu 'ödenemez' ilan etti - ABD belediye tahvili tarihinin en büyük iflası.",
        "market_reaction": (
            "Porto Riko belediye tahvilleri değerinin büyük kısmını kaybetti, bu tahvillere maruz "
            "yatırım fonları zarar yazdı; genel ABD piyasasına bulaşma etkisi sınırlı kaldı "
            "(izole/bölgesel kriz)."
        ),
    },
    {
        "id": "india_demonetization_2016",
        "date": "2016-11",
        "title": "Hindistan'ın Ani Banknot Tedavülden Kaldırması (Demonetizasyon)",
        "category": "Finans Krizi",
        "event": "Hindistan hükümeti, kayıt dışı ekonomi/sahte parayla mücadele için en büyük iki banknotu (%86 nakit) bir gecede geçersiz ilan etti.",
        "market_reaction": (
            "Hindistan borsası (Sensex) kısa süreli %-6 düştü, nakit yoğun küçük işletmeler ve "
            "kırsal ekonomi sert etkilendi, büyüme bir çeyrek yavaşladı; dijital ödeme "
            "şirketleri (Paytm gibi) talep patlaması yaşadı."
        ),
    },
    {
        "id": "hurricane_harvey_2017",
        "date": "2017-08",
        "title": "Kasırga Harvey (Teksas Rafineri Kesintisi)",
        "category": "Doğal Afet",
        "event": "Harvey kasırgası Teksas Körfez Kıyısı'nı ve Houston'ı vurdu, ABD petrol rafinaj kapasitesinin ~%20'sini geçici olarak durdurdu.",
        "market_reaction": (
            "Benzin fiyatları rafineri kapanmalarıyla kısa sürede %+15'e varan sıçrama yaptı; ham "
            "petrol talebi düşüşüyle (rafineriler işlemediği için) hafif geriledi - 'ürün krizi, "
            "ham madde bolluğu' tersine ayrışma örneği."
        ),
    },
    {
        "id": "hurricane_maria_puerto_rico_2017",
        "date": "2017-09",
        "title": "Kasırga Maria ve Porto Riko'nun Elektriksiz Kalması",
        "category": "Doğal Afet",
        "event": "Maria kasırgası Porto Riko'yu vurdu, adanın tamamı aylarca elektriksiz kaldı (tarihin en uzun elektrik kesintisi).",
        "market_reaction": (
            "Sigorta/reasürans şirketleri büyük hasar ödemeleriyle karşılaştı; zaten borç krizinde "
            "olan Porto Riko ekonomisi derinden etkilendi, adadan göç hızlandı."
        ),
    },
    {
        "id": "qatar_blockade_2017",
        "date": "2017-06",
        "title": "Katar Diplomatik Krizi ve Ablukası",
        "category": "Savaş/Jeopolitik",
        "event": "Suudi Arabistan, BAE, Bahreyn ve Mısır, Katar'la diplomatik ilişkileri kesip kara/hava/deniz ablukası uyguladı.",
        "market_reaction": (
            "Katar borsası kısa süreli %-7 düştü, Katar riyali baskı gördü; LNG (sıvılaştırılmış "
            "doğalgaz) piyasasında arz endişesi kısa süreli fiyat oynaklığına yol açtı, kriz 2021'de "
            "diplomatik çözümle sona erdi."
        ),
    },
    {
        "id": "beirut_port_explosion_2020",
        "date": "2020-08",
        "title": "Beyrut Limanı Patlaması",
        "category": "Doğal Afet",
        "event": "Beyrut limanında usulsüz depolanan amonyum nitrat patladı, kenti harap etti ve zaten kriz içindeki Lübnan ekonomisini derinden vurdu.",
        "market_reaction": (
            "Lübnan lirası zaten çökmekte olan değerini daha da hızlı kaybetti, ülke birkaç ay "
            "sonra egemen borcunda temerrüde düştü; etkisi büyük ölçüde ülke-içi/bölgesel kaldı."
        ),
    },
    {
        "id": "colonial_pipeline_ransomware_2021",
        "date": "2021-05",
        "title": "Colonial Pipeline Fidye Yazılımı Saldırısı",
        "category": "Ticaret/Jeopolitik-Ekonomi",
        "event": "ABD Doğu Kıyısı'nın akaryakıtının %45'ini taşıyan Colonial Pipeline, siber saldırı (fidye yazılımı) nedeniyle günlerce durduruldu.",
        "market_reaction": (
            "ABD Güneydoğusu'nda benzin istasyonlarında panik alımı ve kıtlık yaşandı, bölgesel "
            "benzin fiyatları %+3'e varan artış gösterdi; şirket saldırganlara $4.4 milyon fidye "
            "ödedi (bir kısmı FBI tarafından geri alındı) - kritik altyapı siber güvenliği "
            "tartışmasını alevlendirdi."
        ),
    },
    {
        "id": "archegos_collapse_2021",
        "date": "2021-03",
        "title": "Archegos Capital'in Çöküşü",
        "category": "Finans Krizi",
        "event": "Aile ofisi Archegos Capital, aşırı kaldıraçlı hisse pozisyonlarında marjin çağrısını karşılayamayınca bankalar milyarlarca dolarlık pozisyonu aniden tasfiye etti.",
        "market_reaction": (
            "ViacomCBS, Discovery gibi hisseler günler içinde %-30'a varan düşüşler yaşadı; "
            "Credit Suisse ve Nomura bu olaydan $5-10 milyar arası zarar yazdı - Credit Suisse'in "
            "2023'teki nihai çöküşünün itibar/sermaye açısından öncü darbelerinden biri oldu."
        ),
    },
    {
        "id": "meta_stock_crash_2022",
        "date": "2022-02-03",
        "title": "Meta (Facebook) Hissesinin Tarihi Tek Günlük Çöküşü",
        "category": "Teknoloji/Kripto Balonu",
        "event": "Meta, kullanıcı sayısında ilk kez düşüş bildirdi ve zayıf gelir tahmini verdi.",
        "market_reaction": (
            "Meta hissesi tek günde %-26.4 düştü, piyasa değerinden ~$232 milyar silindi - o "
            "zamana kadarki ABD borsa tarihinin tek şirkette görülen en büyük tek günlük piyasa "
            "değeri kaybıydı (rekor daha sonra 2024'te yine Meta ve Nvidia tarafından geçildi)."
        ),
    },
    {
        "id": "netflix_stock_crash_2022",
        "date": "2022-04",
        "title": "Netflix'in Abone Kaybı Şoku",
        "category": "Teknoloji/Kripto Balonu",
        "event": "Netflix, 10 yıldan fazla süredir ilk kez abone kaybettiğini açıkladı ve gelecek çeyrek için daha büyük kayıp öngördü.",
        "market_reaction": (
            "Hisse tek günde %-35 çöktü; 'pandemi döneminin evde-kal kazananları' anlatısının "
            "sona erdiğinin sembolü oldu, streaming sektöründe rekabet/doygunluk endişesini "
            "gündeme getirdi."
        ),
    },
    {
        "id": "nord_stream_pipeline_explosion_2022",
        "date": "2022-09",
        "title": "Nord Stream Doğalgaz Boru Hattı Patlamaları",
        "category": "Savaş/Jeopolitik",
        "event": "Rusya'dan Almanya'ya doğalgaz taşıyan Nord Stream 1 ve 2 boru hatlarında Baltık Denizi'nde sabotaj sonucu patlamalar meydana geldi.",
        "market_reaction": (
            "Avrupa doğalgaz fiyatları (TTF) kısa süreli sıçrama yaptı; olay zaten devam eden "
            "Avrupa enerji krizinin (Rusya'nın gaz akışını kademeli kesmesi) sembolik zirvesi "
            "oldu, Avrupa'nın enerji tedarikini çeşitlendirme (LNG ithalatı) çabalarını hızlandırdı."
        ),
    },
    {
        "id": "european_energy_crisis_2022",
        "date": "2022-06..2022-12",
        "title": "Avrupa Enerji Krizi (Rus Gaz Kesintisi)",
        "category": "Petrol Krizi",
        "event": "Rusya, Ukrayna savaşı sonrası yaptırımlara karşılık Avrupa'ya doğalgaz akışını kademeli olarak durdurdu.",
        "market_reaction": (
            "Avrupa doğalgaz fiyatları (TTF) yaz aylarında normalin ~15 katına çıktı; Almanya "
            "başta olmak üzere enerji yoğun sanayi (kimya, gübre, cam) üretim kesintisine gitti, "
            "Euro dolar karşısında paritenin altına indi. Ilıman kış ve LNG ithalatının hızla "
            "artmasıyla fiyatlar 2023'te büyük ölçüde normalleşti."
        ),
    },
    {
        "id": "jackson_hole_powell_2022",
        "date": "2022-08-26",
        "title": "Powell'ın Şahin Jackson Hole Konuşması",
        "category": "Para Politikası",
        "event": "Fed Başkanı Powell, Jackson Hole sempozyumunda 'ekonomik acıya rağmen' enflasyonla mücadeleye devam edileceğini net biçimde vurguladı.",
        "market_reaction": (
            "S&P 500 konuşma sonrası tek günde %-3.4, hafta içinde %-4'ün üzerinde düştü - piyasanın "
            "umduğu 'Fed pivotu' (gevşemeye erken dönüş) beklentisinin sert biçimde kırıldığı an "
            "olarak hatırlanır."
        ),
    },
    {
        "id": "musk_twitter_acquisition_2022",
        "date": "2022-10",
        "title": "Elon Musk'ın Twitter'ı Satın Alması",
        "category": "Teknoloji/Kripto Balonu",
        "event": "Elon Musk, aylar süren hukuki çekişmenin ardından Twitter'ı (sonra X) $44 milyara satın aldı.",
        "market_reaction": (
            "Tesla hissesi, Musk'ın hisse satarak finansman sağlaması ve dikkatinin dağılması "
            "endişesiyle satın alma sonrası aylarda %-50'ye varan düşüş yaşadı; reklam gelirleri "
            "içerik moderasyonu tartışmalarıyla geriledi, şirket değeri satın alma sonrası ciddi "
            "oranda küçüldü."
        ),
    },
    {
        "id": "sri_lanka_default_2022",
        "date": "2022-04",
        "title": "Sri Lanka'nın Egemen Borç Temerrüdü",
        "category": "Finans Krizi",
        "event": "Sri Lanka, döviz rezervlerinin tükenmesiyle tarihinde ilk kez dış borcunda temerrüde düştü; yakıt/gıda kıtlığı halk ayaklanmasına yol açtı.",
        "market_reaction": (
            "Sri Lanka rupisi çöktü, enflasyon %70'e dayandı; siyasi kriz cumhurbaşkanının "
            "istifasıyla sonuçlandı - küçük/kırılgan gelişen piyasa ekonomilerinde döviz "
            "rezervi tükenmesinin sistemik krize dönüşme riskinin örneği."
        ),
    },
    {
        "id": "china_property_crisis_2023",
        "date": "2023-08",
        "title": "Çin Emlak Krizinin Derinleşmesi (Country Garden)",
        "category": "Finans Krizi",
        "event": "Evergrande'den sonra Çin'in en büyük emlak geliştiricisi Country Garden da tahvil ödemelerinde temerrüde düştü.",
        "market_reaction": (
            "Çin/Hong Kong borsaları ve emlak sektörü hisseleri sert düştü; küresel emtia "
            "(demir cevheri, bakır) talebi endişesiyle geriledi, Çin hükümeti teşvik paketleriyle "
            "müdahale etmeye çalıştı ancak emlak sektöründeki durgunluk yıllarca sürdü."
        ),
    },
    {
        "id": "opec_surprise_cut_2023",
        "date": "2023-04",
        "title": "OPEC+'ın Sürpriz Üretim Kesintisi",
        "category": "Petrol Krizi",
        "event": "Suudi Arabistan liderliğindeki OPEC+ üyeleri, piyasayı desteklemek için günlük 1.16 milyon varil ek üretim kesintisini beklenmedik şekilde açıkladı.",
        "market_reaction": (
            "Brent petrol açıklama sonrası tek günde %+6'ya varan sıçrama yaptı; enerji hisseleri "
            "kısa vadede yükseldi, ancak küresel talep endişeleri nedeniyle fiyat artışı kalıcı "
            "olmadı, yıl içinde geriledi."
        ),
    },
    {
        "id": "boj_negative_rate_exit_2024",
        "date": "2024-03",
        "title": "Japonya Merkez Bankası'nın Negatif Faizden Çıkışı",
        "category": "Para Politikası",
        "event": "BOJ, 17 yıl sonra ilk kez faiz artırarak 8 yıllık negatif faiz politikasını sonlandırdı.",
        "market_reaction": (
            "Yen başlangıçta zayıf kaldı (artış küçüktü, faiz farkı hâlâ büyüktü) ama piyasada "
            "'yen carry trade'in sonunun başlangıcı' olarak okundu - birkaç ay sonra Ağustos "
            "2024'teki daha büyük hızlı çözülmenin (bkz. yen_carry_trade_unwind_2024) zeminini "
            "hazırladı."
        ),
    },
    {
        "id": "panama_canal_drought_2023_2024",
        "date": "2023-08..2024-05",
        "title": "Panama Kanalı Kuraklığı ve Geçiş Kısıtlamaları",
        "category": "Kıtlık/Tarım Şoku",
        "event": "Rekor kuraklık, Panama Kanalı'ndaki su seviyesini düşürdü; yönetim günlük gemi geçiş sayısını ciddi oranda kısıtladı.",
        "market_reaction": (
            "Navlun maliyetleri ve teslimat süreleri arttı, bazı gemiler alternatif (daha uzun, "
            "daha pahalı) rotalara yönlendi; küresel tedarik zinciri maliyetlerinde ek bir baskı "
            "unsuru oldu (Kızıldeniz krizine paralel zamanlarda gerçekleşti)."
        ),
    },
    {
        "id": "red_sea_houthi_attacks_2023_2024",
        "date": "2023-11..2024-12",
        "title": "Kızıldeniz'de Husi Saldırıları ve Deniz Ticareti Krizi",
        "category": "Savaş/Jeopolitik",
        "event": "Yemen merkezli Husiler, İsrail-Hamas savaşına tepki olarak Kızıldeniz/Süveyş güzergahındaki ticari gemilere füze/drone saldırıları düzenledi.",
        "market_reaction": (
            "Büyük nakliye şirketleri (Maersk, MSC) gemilerini Süveyş yerine Afrika'yı dolaşan "
            "(Ümit Burnu) çok daha uzun rotaya yönlendirdi; navlun maliyetleri %+100'ün üzerinde "
            "arttı, sigorta primleri fırladı - Süveyş'ten geçen küresel ticaretin önemli bir kısmı "
            "aylarca aksadı."
        ),
    },
    {
        "id": "argentina_milei_2023",
        "date": "2023-11..2024-01",
        "title": "Javier Milei'nin Arjantin'de Şok Ekonomik Reformları",
        "category": "Finans Krizi",
        "event": "Liberter iktisatçı Javier Milei, Arjantin devlet başkanlığını kazandıktan sonra pesoyu %50'nin üzerinde devalüe etti ve sert kemer sıkma/deregülasyon paketini uygulamaya koydu.",
        "market_reaction": (
            "Arjantin'in dolar cinsi tahvilleri ve Merval borsası reform beklentisiyle güçlü ralli "
            "yaptı (Merval 2024'te dünyanın en iyi performans gösteren borsalarından biri oldu); "
            "enflasyon kısa vadede yükselse de yıl içinde hızla düşüşe geçti."
        ),
    },
    {
        "id": "deepseek_ai_shock_2025",
        "date": "2025-01-27",
        "title": "DeepSeek Şoku - Çin Yapay Zekasının Nvidia'yı Sarsması",
        "category": "Teknoloji/Kripto Balonu",
        "event": "Çinli DeepSeek, ABD modellerine yakın performansı çok daha düşük maliyetle sunan bir yapay zeka modelini açıkladı; bu, ABD'nin AI çip üstünlüğü/devasa yatırım anlatısını sorguya açtı.",
        "market_reaction": (
            "Nvidia hissesi tek günde %-17 düşerek ~$593 milyar piyasa değeri kaybetti - ABD "
            "borsa tarihinde tek şirkette görülen en büyük tek günlük dolar bazlı kayıp rekoru; "
            "diğer AI/veri merkezi/enerji hisseleri (Microsoft, enerji şirketleri) de sert satış "
            "gördü, birkaç gün içinde kısmi toparlanma yaşandı."
        ),
    },
    {
        "id": "silvergate_signature_crypto_banks_2023",
        "date": "2023-03",
        "title": "Silvergate ve Signature Bank'ın (Kripto Bankaları) Çöküşü",
        "category": "Finans Krizi",
        "event": "Kripto sektörüne özel bankacılık hizmeti veren Silvergate ve Signature Bank, SVB krizinin hemen ardından/eş zamanlı olarak kapandı.",
        "market_reaction": (
            "Kripto piyasasında banka erişimi endişesi arttı, Bitcoin kısa süreli oynaklık yaşadı "
            "ama SVB'nin aksine hızla toparlandı; düzenleyicilerin kripto şirketlerine bankacılık "
            "hizmetini kısıtladığı iddiası ('Operation Choke Point 2.0') sektörde uzun süre "
            "tartışma konusu oldu."
        ),
    },
    {
        "id": "fitch_us_downgrade_2023",
        "date": "2023-08",
        "title": "Fitch'in ABD Kredi Notunu İndirmesi",
        "category": "Finans Krizi",
        "event": "Fitch Ratings, mali yönetişimin bozulması ve borç tavanı krizlerinin tekrarlanması gerekçesiyle ABD'nin AAA notunu AA+'ya indirdi (S&P'den 12 yıl sonra ikinci indirim).",
        "market_reaction": (
            "2011'deki S&P indirimine benzer şekilde borsa kısa süreli satış gördü (S&P 500 "
            "birkaç günde %-3), ancak ABD tahvil faizleri üzerindeki etki sınırlı kaldı - piyasa "
            "'haber zaten biliniyordu' tepkisi verdi."
        ),
    },
    {
        "id": "venezuela_hyperinflation_oil_crisis",
        "date": "2016-01..2019-12",
        "title": "Venezuela Hiperenflasyonu ve Petrol Üretim Çöküşü",
        "category": "Petrol Krizi",
        "event": "Petrol fiyatlarının 2014-2016 çöküşü ve yönetim krizi, dünyanın en büyük petrol rezervine sahip Venezuela'da hiperenflasyona (yıllık milyonlarca yüzde) ve petrol üretiminin çöküşüne yol açtı.",
        "market_reaction": (
            "Venezuela bolivarı pratik olarak değersizleşti, ülke ekonomisi %-75'e varan küçülme "
            "yaşadı, milyonlarca kişi ülkeyi terk etti; ABD'nin ek petrol yaptırımları (2019) "
            "üretim çöküşünü derinleştirdi - küresel petrol arzından günlük milyonlarca varil "
            "kalıcı olarak eksildi."
        ),
    },
    # ---------------------------------------------------------------
    # Ek senaryolar: ABD vergi/tarife kararları, yasal düzenlemeler, batan
    # şirketler, siyasi krizler, iklim kararları, Brexit süreci, Meksika,
    # Venezuela askeri baskını, Hindistan-Pakistan gerilimi, Tayland krizi
    # ---------------------------------------------------------------
    {
        "id": "bush_tax_cuts_2001_2003",
        "date": "2001-06..2003-05",
        "title": "Bush Vergi İndirimleri (EGTRRA/JGTRRA)",
        "category": "Para Politikası",
        "event": "ABD Kongresi, gelir/sermaye kazancı/temettü vergilerini kademeli olarak düşüren iki büyük vergi indirim paketini onayladı.",
        "market_reaction": (
            "Temettü vergisinin %39.6'dan %15'e indirilmesi (2003) sonrası şirketler temettü "
            "dağıtımını belirgin şekilde artırdı, borsa 2003-2007 boğa piyasasında bu teşvikten "
            "faydalandı; bütçe açığı ise genişledi, uzun vadeli mali sürdürülebilirlik "
            "tartışmasını başlattı."
        ),
    },
    {
        "id": "sarbanes_oxley_2002",
        "date": "2002-07",
        "title": "Sarbanes-Oxley Yasası (Kurumsal Denetim Reformu)",
        "category": "Finans Krizi",
        "event": "Enron/WorldCom skandallarının ardından ABD Kongresi, halka açık şirketler için sıkı finansal raporlama ve iç denetim standartları getiren Sarbanes-Oxley yasasını çıkardı.",
        "market_reaction": (
            "Uyum maliyetleri (özellikle küçük şirketler için) arttı, bazı şirketler halka açık "
            "kalmak yerine özelleşmeyi tercih etti; uzun vadede kurumsal raporlama güvenilirliğini "
            "artırarak yatırımcı güvenine katkı sağladığı değerlendirilir."
        ),
    },
    {
        "id": "dodd_frank_2010",
        "date": "2010-07",
        "title": "Dodd-Frank Finansal Reform Yasası",
        "category": "Finans Krizi",
        "event": "2008 krizine tepki olarak ABD, bankalara sermaye/likidite şartları, Volcker Kuralı (öz-hesap ticaretinin kısıtlanması) ve tüketici koruma kurumu (CFPB) getiren kapsamlı Dodd-Frank yasasını çıkardı.",
        "market_reaction": (
            "Büyük bankalar (JPMorgan, Goldman Sachs) uyum/sermaye maliyetleri nedeniyle kısa "
            "vadede kârlılık baskısı yaşadı, banka hisseleri düzenleme belirsizliği döneminde "
            "geride kaldı; sistemin krizlere karşı dayanıklılığı uzun vadede arttı (2020 ve "
            "2023 şoklarında bankacılık sistemi 2008'e göre çok daha sağlam kaldı)."
        ),
    },
    {
        "id": "steel_aluminum_tariffs_2018",
        "date": "2018-03",
        "title": "ABD'nin Çelik ve Alüminyum Tarifeleri (Section 232)",
        "category": "Ticaret/Jeopolitik-Ekonomi",
        "event": "Trump yönetimi, 'ulusal güvenlik' gerekçesiyle ithal çeliğe %25, alüminyuma %10 tarife koydu; AB/Kanada/Meksika dahil müttefikler de kapsama alındı.",
        "market_reaction": (
            "ABD çelik üreticileri (US Steel, Nucor) hisseleri kısa vadede yükseldi; çelik "
            "kullanan sektörler (otomotiv, inşaat, konserve gıda) girdi maliyeti artışıyla "
            "OLUMSUZ etkilendi. AB ve Kanada karşı tarifelerle (Harley-Davidson, viski, kot "
            "pantolon gibi sembolik ürünlere) misilleme yaptı - daha büyük ticaret savaşının "
            "provası oldu."
        ),
    },
    {
        "id": "tcja_corporate_tax_cut_2017",
        "date": "2017-12",
        "title": "Trump Vergi Reformu (TCJA) - Kurumlar Vergisinin %21'e İndirilmesi",
        "category": "Para Politikası",
        "event": "ABD Kongresi, kurumlar vergisini %35'ten %21'e indiren ve yurt dışı kârların vergisiz/düşük vergiyle ülkeye getirilmesine (repatriation) izin veren Tax Cuts and Jobs Act'i (TCJA) yasalaştırdı.",
        "market_reaction": (
            "S&P 500 şirketleri 2018'de rekor düzeyde hisse geri alımı (buyback, ~$1 trilyon) "
            "yaptı; büyük teknoloji şirketleri (Apple dahil) yurt dışında biriken yüz milyarlarca "
            "doları ABD'ye getirdi. Borsa yasanın geçmesiyle güçlü tepki verdi, ancak bütçe açığını "
            "genişlettiği için uzun vadeli mali sürdürülebilirlik eleştirisi aldı."
        ),
    },
    {
        "id": "eu_gdpr_2018",
        "date": "2018-05",
        "title": "AB'nin GDPR (Genel Veri Koruma Tüzüğü) Yürürlüğe Girmesi",
        "category": "Ticaret/Jeopolitik-Ekonomi",
        "event": "Avrupa Birliği, kullanıcı verisi işleyen tüm şirketlere (global cironun %4'üne kadar ceza riskiyle) sıkı veri koruma kuralları getiren GDPR'yi yürürlüğe soktu.",
        "market_reaction": (
            "Büyük teknoloji/reklam şirketleri (Google, Meta, Amazon) uyum maliyeti ve olası "
            "cezalarla karşı karşıya kaldı, küçük reklam teknolojisi şirketleri bazı pazarlardan "
            "çekildi; uzun vadede küresel veri gizliliği düzenlemelerine (Kaliforniya CCPA dahil) "
            "örnek teşkil etti."
        ),
    },
    {
        "id": "huawei_entity_list_2019",
        "date": "2019-05",
        "title": "ABD'nin Huawei'yi Yasaklı Ticaret Listesine (Entity List) Alması",
        "category": "Ticaret/Jeopolitik-Ekonomi",
        "event": "ABD Ticaret Bakanlığı, ulusal güvenlik gerekçesiyle Çinli telekom devi Huawei'yi ABD teknolojisi/yazılımı satın alamayacağı 'Entity List'e ekledi.",
        "market_reaction": (
            "Huawei'ye çip/yazılım satan ABD şirketleri (Qualcomm, Google - Android lisansı) "
            "gelir kaybı riskiyle karşılaştı; Huawei akıllı telefon pazar payını küresel çapta "
            "kaybetti, Çin bu olayı kendi yarı iletken bağımsızlığı (self-sufficiency) "
            "yatırımlarını hızlandırmak için gerekçe olarak kullandı - sonraki yıllarda ABD-Çin "
            "'çip savaşının' başlangıç noktalarından biri oldu."
        ),
    },
    {
        "id": "chip_export_controls_2022_2023",
        "date": "2022-10..2023-10",
        "title": "ABD'nin Çin'e İleri Çip/Yarı İletken Ekipmanı İhracat Yasakları",
        "category": "Ticaret/Jeopolitik-Ekonomi",
        "event": "ABD, gelişmiş yapay zeka çiplerinin ve üretim ekipmanının Çin'e satışını kapsamlı şekilde kısıtlayan ihracat kontrolleri açıkladı (Nvidia'nın en gelişmiş çiplerini kapsayacak şekilde).",
        "market_reaction": (
            "Nvidia ve yarı iletken ekipman üreticileri (ASML, Applied Materials, Lam Research) "
            "Çin pazarı gelir kaybı riskiyle kısa süreli düşüş yaşadı; Nvidia, Çin için özel "
            "olarak düşürülmüş performanslı çip modelleri (A800/H800 gibi) geliştirerek uyum "
            "sağladı. Çin, kendi yarı iletken sanayine devasa devlet yatırımını hızlandırdı."
        ),
    },
    {
        "id": "eu_ai_act_2024",
        "date": "2024-03..2024-08",
        "title": "AB Yapay Zeka Yasası'nın (AI Act) Kabul Edilmesi",
        "category": "Ticaret/Jeopolitik-Ekonomi",
        "event": "Avrupa Parlamentosu, dünyanın ilk kapsamlı yapay zeka düzenlemesini (risk bazlı sınıflandırma, yüksek riskli AI sistemleri için sıkı uyum şartları) onayladı.",
        "market_reaction": (
            "Büyük AI şirketleri (OpenAI, Google, Meta) uyum maliyeti ve bazı ürünlerin AB "
            "pazarına gecikmeli sunulması riskiyle karşılaştı; piyasa etkisi kademeli/uzun "
            "vadeli oldu (tek günlük şok yaratan bir olay değil), düzenleyici belirsizlik "
            "primi olarak AI hisselerinde arka planda fiyatlandı."
        ),
    },
    {
        "id": "eu_carbon_border_tax_2023",
        "date": "2023-10",
        "title": "AB Sınırda Karbon Düzenleme Mekanizması (CBAM)",
        "category": "Ticaret/Jeopolitik-Ekonomi",
        "event": "AB, yüksek karbon ayak izine sahip ithal ürünlere (çelik, çimento, alüminyum, gübre, elektrik) kademeli karbon vergisi uygulamaya başladı.",
        "market_reaction": (
            "AB'ye ihracat yapan karbon-yoğun sanayiler (özellikle Çin, Hindistan, Türkiye çelik/"
            "çimento üreticileri) maliyet artışı riskiyle karşılaştı; Avrupalı 'temiz' üreticiler "
            "göreceli rekabet avantajı kazandı - iklim politikasının doğrudan ticaret/rekabet "
            "etkisine dönüştüğü örneklerden biri."
        ),
    },
    {
        "id": "paris_agreement_2015_2017",
        "date": "2015-12..2017-06",
        "title": "Paris İklim Anlaşması ve ABD'nin Çekilme Kararı",
        "category": "Ticaret/Jeopolitik-Ekonomi",
        "event": "196 ülke Aralık 2015'te Paris İklim Anlaşması'nı imzaladı; Trump yönetimi Haziran 2017'de ABD'nin anlaşmadan çekileceğini açıkladı (Biden 2021'de yeniden katıldı).",
        "market_reaction": (
            "Yenilenebilir enerji hisseleri anlaşma imzalandığında olumlu, ABD çekilme kararında "
            "kısa süreli negatif tepki verdi; fosil yakıt şirketleri çekilme kararını kısa vadede "
            "olumlu karşıladı. Uzun vadede küresel yeşil enerji yatırımları (güneş/rüzgar/EV) "
            "anlaşmadan bağımsız olarak yapısal büyüme trendini sürdürdü."
        ),
    },
    {
        "id": "ira_inflation_reduction_act_2022",
        "date": "2022-08",
        "title": "ABD Enflasyonu Azaltma Yasası (IRA) - İklim/Enerji Yatırımları",
        "category": "Para Politikası",
        "event": "ABD Kongresi, temiz enerji/elektrikli araç/yarı iletken üretimine $370 milyarın üzerinde teşvik içeren IRA yasasını çıkardı.",
        "market_reaction": (
            "Güneş paneli, rüzgar enerjisi, batarya ve elektrikli araç üreticileri (First Solar, "
            "Tesla, batarya tedarik zinciri şirketleri) teşvik beklentisiyle güçlü ralli yaptı; "
            "ABD'de temiz enerji fabrika yatırımları yasadan sonraki 2 yılda önemli ölçüde arttı."
        ),
    },
    {
        "id": "california_wildfires_pge_2019",
        "date": "2019-01..2020-12",
        "title": "Kaliforniya Orman Yangınları ve PG&E'nin İflası",
        "category": "Doğal Afet",
        "event": "Kaliforniya'da art arda yaşanan yıkıcı orman yangınlarının (Camp Fire dahil) elektrik şirketi PG&E'nin ekipmanından kaynaklandığının belirlenmesi, şirketi milyarlarca dolarlık tazminat sorumluluğuyla karşı karşıya bıraktı.",
        "market_reaction": (
            "PG&E hissesi yangın sorumluluğu ortaya çıktıkça %-90'a varan çöküş yaşadı ve Ocak "
            "2019'da iflas başvurusu yaptı - iklim değişikliğinin bir kamu hizmeti (utility) "
            "şirketini doğrudan iflasa sürüklediği ilk büyük örneklerden biri oldu. Diğer batı "
            "eyaleti elektrik şirketleri de benzer yangın/sorumluluk riskiyle yeniden "
            "fiyatlandı."
        ),
    },
    {
        "id": "australia_bushfires_2019_2020",
        "date": "2019-09..2020-02",
        "title": "Avustralya Orman Yangınları ('Kara Yaz')",
        "category": "Doğal Afet",
        "event": "Avustralya'da rekor kuraklık ve sıcaklıklar, tarihin en yıkıcı orman yangın sezonlarından birine (milyonlarca hektar) yol açtı.",
        "market_reaction": (
            "Turizm ve tarım sektörü bölgesel olarak olumsuz etkilendi, sigorta hasar tahminleri "
            "milyarlarca dolara ulaştı; küresel piyasa etkisi sınırlı kaldı ama iklim "
            "değişikliğinin sigorta/reasürans fiyatlamasına kalıcı etkisini artıran örneklerden "
            "biri oldu."
        ),
    },
    {
        "id": "wework_ipo_failure_2019",
        "date": "2019-08..2019-09",
        "title": "WeWork'ün IPO Girişiminin Çöküşü",
        "category": "Finans Krizi",
        "event": "Ofis paylaşım şirketi WeWork, halka arz öncesi açıkladığı finansallarda dev zararlar ve yönetişim sorunları (kurucu Adam Neumann'ın çıkar çatışmaları) ortaya çıkınca halka arzını iptal etmek zorunda kaldı.",
        "market_reaction": (
            "Şirketin özel piyasa değerlemesi $47 milyardan aylar içinde $8 milyarın altına "
            "çöktü, ana yatırımcı SoftBank milyarlarca dolar zarar yazdı; 'unicorn' (tek boynuzlu "
            "at, $1 milyar+ değerlemeli girişim) şirketlerin kârlılık/yönetişim standartlarının "
            "sorgulanmasına yol açan sembolik bir olay oldu."
        ),
    },
    {
        "id": "silicon_valley_layoffs_2022_2023",
        "date": "2022-11..2023-06",
        "title": "Büyük Teknoloji Şirketlerinde Kitlesel İşten Çıkarmalar",
        "category": "Teknoloji/Kripto Balonu",
        "event": "Meta, Amazon, Google, Microsoft, Twitter/X gibi şirketler faiz artışı/talep yavaşlaması sonrası art arda on binlerce çalışanı işten çıkardı (Meta tek seferde 11.000, Amazon 18.000+).",
        "market_reaction": (
            "İşten çıkarma duyuruları çoğunlukla 'maliyet disiplini' sinyali olarak piyasada "
            "OLUMLU karşılandı (hisseler genelde yükseldi) - pandemi döneminin aşırı istihdam "
            "genişlemesinin düzeltilmesi olarak yorumlandı, kâr marjlarının iyileşmesi "
            "beklentisini güçlendirdi."
        ),
    },
    {
        "id": "brexit_process_2016_2020",
        "date": "2016-06..2020-01",
        "title": "Brexit Süreci - AB'den Resmi Çıkış (İngiltere)",
        "category": "Savaş/Jeopolitik",
        "event": "2016 referandumundan sonraki 3.5 yıl boyunca İngiltere'nin AB'den çıkış şartları müzakere edildi (Madde 50 tetiklenmesi Mart 2017, çok sayıda parlamento oylaması/erteleme), İngiltere resmen 31 Ocak 2020'de AB'den ayrıldı.",
        "market_reaction": (
            "Süreç boyunca sterlin, her kilit oylama/müzakere haberine göre %+/-2-4 dalgalandı "
            "('Brexit belirsizlik primi'); İngiliz şirketlerinin yatırım kararları yıllarca "
            "ertelendi. Nihai çıkış (Ocak 2020) ve ardından geçiş dönemi sonu (Aralık 2020, "
            "ticaret anlaşmasıyla) piyasada büyük ölçüde önceden fiyatlandığı için sınırlı "
            "ek tepki yarattı - 'uzun süreli belirsizlik, haber akışına duyarlı kademeli "
            "fiyatlama' modelinin örneği."
        ),
    },
    {
        "id": "mexico_peso_crisis_note_1994_legacy",
        "date": "1994-12",
        "title": "Meksika Peso Krizi ('Tekila Etkisi') - Tarihsel Referans",
        "category": "Finans Krizi",
        "event": "2000 öncesi yaşanmış olsa da (Aralık 1994), Meksika'nın pesoyu devalüe etmesi ve ardından gelen sermaye kaçışı, sonraki yıllarda gelişen piyasa kriz yönetiminin (IMF/ABD destekli kurtarma paketleri) referans noktası oldu.",
        "market_reaction": (
            "Peso birkaç ayda %-50 değer kaybetti, kriz Arjantin/Brezilya'ya bulaştı ('Tekila "
            "Etkisi'); ABD'nin $50 milyarlık kurtarma paketi krizi durdurdu - bu olay 2000 "
            "sonrası tüm gelişen piyasa para birimi krizlerinin (Türkiye 2001/2018, Arjantin "
            "2001/2018, Rusya 1998) değerlendirilme çerçevesini oluşturdu."
        ),
    },
    {
        "id": "mexico_amlo_energy_policy_2019_2021",
        "date": "2019-12..2021-12",
        "title": "Meksika'nın Enerji Sektörü Milliyetçiliği (AMLO Reformları)",
        "category": "Ticaret/Jeopolitik-Ekonomi",
        "event": "Devlet Başkanı López Obrador (AMLO), devlet petrol/elektrik şirketlerini (Pemex, CFE) özel/yabancı yatırıma karşı öncelikli kılan yasal düzenlemeler getirdi.",
        "market_reaction": (
            "Meksika'ya yatırım yapan yabancı enerji/yenilenebilir enerji şirketleri belirsizlik "
            "nedeniyle yeni yatırımları erteledi; Pemex'in kredi notu (zaten yüksek borç yükü "
            "nedeniyle) uluslararası derecelendirme kuruluşlarınca aşağı yönlü baskı gördü, "
            "Meksika pesosu döngüsel olarak politika belirsizliğine duyarlı kaldı."
        ),
    },
    {
        "id": "usmca_nafta_replacement_2018_2020",
        "date": "2018-09..2020-07",
        "title": "USMCA'nın (NAFTA'nın Yerine) Yürürlüğe Girmesi",
        "category": "Ticaret/Jeopolitik-Ekonomi",
        "event": "ABD, Kanada ve Meksika, 1994'ten beri yürürlükte olan NAFTA'yı yenileyerek USMCA (ABD-Meksika-Kanada Anlaşması) adlı yeni ticaret anlaşmasını imzaladı ve Temmuz 2020'de yürürlüğe soktu.",
        "market_reaction": (
            "Otomotiv sektörü için bölgesel içerik/işçilik şartlarının sıkılaştırılması "
            "(Meksika'da üretim yapan otomotiv üreticileri için ek maliyet riski) piyasada "
            "dikkatle izlendi; genel olarak müzakere süreci boyunca belirsizlik primi "
            "oluşturdu, anlaşmanın nihai imzalanması piyasada rahatlama yarattı (üç ülke "
            "ticaretinin öngörülebilirliği korunmuş oldu)."
        ),
    },
    {
        "id": "venezuela_us_military_pressure_2019_2020",
        "date": "2019-01..2020-03",
        "title": "ABD'nin Venezuela'da Maduro'ya Karşı Askeri/Diplomatik Baskısı",
        "category": "Savaş/Jeopolitik",
        "event": "ABD, Ocak 2019'da muhalefet lideri Juan Guaidó'yu 'geçici başkan' olarak tanıdı, Maduro hükümetine kapsamlı petrol yaptırımları uyguladı ve bölgeye deniz kuvveti/askeri varlık gönderdi; Mart 2020'de Adalet Bakanlığı Maduro'yu uyuşturucu kaçakçılığından suçladı ve başına ödül koydu.",
        "market_reaction": (
            "Venezuela'nın zaten çökmüş petrol üretimi yaptırımlarla daha da geriledi (günlük "
            "üretim 3 milyon varilden 400 binlerin altına indi); küresel petrol arzından kalıcı "
            "bir kayıp olarak fiyatlandı ama Venezuela'nın küresel üretimdeki payı küçüldüğü "
            "için etkisi sınırlı kaldı. Bölgesel jeopolitik gerginlik Karayipler'deki deniz "
            "taşımacılığı sigortasında risk primini artırdı."
        ),
    },
    {
        "id": "india_pakistan_pulwama_2019",
        "date": "2019-02..2019-03",
        "title": "Hindistan-Pakistan Gerginliği (Pulwama Saldırısı ve Karşılık)",
        "category": "Savaş/Jeopolitik",
        "event": "Keşmir'de bir Hindistan askeri konvoyuna yapılan Pulwama saldırısının (40+ ölü) ardından Hindistan, Pakistan sınırları içinde hava saldırısı (Balakot) düzenledi; iki nükleer güç arasında hava muharebesi yaşandı.",
        "market_reaction": (
            "Hindistan borsası (Sensex/Nifty) ve Pakistan borsası (KSE-100) gerginlik zirvesinde "
            "kısa süreli %-2-3 satış gördü; tam ölçekli savaşa dönüşmemesi ve hızlı "
            "de-eskalasyon (esir pilotun iadesi) ile piyasalar günler içinde toparlandı - "
            "'nükleer caydırıcılık altında sınırlı çatışma' modelinin piyasa tepkisi tipik "
            "olarak kısa ömürlü olur."
        ),
    },
    {
        "id": "india_pakistan_kashmir_2025",
        "date": "2025-04..2025-05",
        "title": "Hindistan-Pakistan Gerginliği (Keşmir - Pahalgam Sonrası)",
        "category": "Savaş/Jeopolitik",
        "event": "Keşmir'de turistlere yönelik bir saldırının ardından Hindistan ve Pakistan arasında sınır ötesi füze/hava saldırıları ve yoğun topçu çatışması yaşandı; taraflar birbirini askeri tesisleri vurmakla suçladı.",
        "market_reaction": (
            "Hindistan (Nifty 50) ve Pakistan (KSE-100) borsaları çatışmanın en yoğun günlerinde "
            "sert günlük dalgalanmalar yaşadı, savunma sanayi hisseleri (Hindustan Aeronautics "
            "gibi) yükseldi; ABD arabuluculuğuyla ateşkes sağlanınca her iki borsa da hızla "
            "toparlandı - bölgesel/nükleer gerilim risklerinin piyasada 'ateşkes haberiyle hızlı "
            "normalleşme' örüntüsünü tekrarladığı bir vaka."
        ),
    },
    {
        "id": "thailand_political_crisis_2013_2014",
        "date": "2013-11..2014-05",
        "title": "Tayland Siyasi Krizi ve Askeri Darbe",
        "category": "Savaş/Jeopolitik",
        "event": "Aylarca süren hükümet karşıtı sokak gösterilerinin ardından Tayland ordusu Mayıs 2014'te yönetime el koydu (askeri darbe).",
        "market_reaction": (
            "Tayland borsası (SET Endeksi) ve baht, siyasi belirsizlik döneminde baskı altında "
            "kaldı, turizm geliri (ülkenin GSYH'sinin önemli bir kısmı) gösteriler/darbe "
            "döneminde geçici olarak düştü; ordu yönetiminin istikrarı sağlamasıyla (yatırımcılar "
            "için öngörülebilirlik artışı) borsa birkaç ay içinde toparlandı - 'siyasi "
            "istikrarsızlık kısa vadede olumsuz, askeri/otoriter istikrar sağlanması bazen "
            "piyasa tarafından ödüllendirilir' paradoksal örneği."
        ),
    },
    {
        "id": "thailand_covid_tourism_collapse_2020_2021",
        "date": "2020-03..2021-12",
        "title": "Tayland'da COVID-19 Kaynaklı Turizm Çöküşü",
        "category": "Pandemi/Salgın",
        "event": "Tayland ekonomisinin GSYH'sinin ~%20'sini oluşturan turizm sektörü, pandemi sınır kapanışlarıyla neredeyse tamamen durdu (yabancı turist sayısı %-99'a varan düşüş yaşadı).",
        "market_reaction": (
            "Tayland baIt'ı ve borsası (SET) bölgedeki en sert GSYH daralmalarından birini "
            "yaşayan ülke olarak baskı altında kaldı; havayolu/otel/perakende hisseleri sert "
            "düştü, hükümetin 'balon' (karantinasız turist bölgeleri, Phuket Sandbox 2021) "
            "programlarıyla kademeli toparlanma başladı."
        ),
    },
    {
        "id": "thailand_baht_crisis_1997_legacy",
        "date": "1997-07",
        "title": "Tayland Baht Krizi ve Asya Finansal Krizi - Tarihsel Referans",
        "category": "Finans Krizi",
        "event": "2000 öncesi yaşanmış olsa da (Temmuz 1997), Tayland'ın baht'ın dolar sabitini bırakması tüm Asya'ya yayılan finansal krizi (Endonezya, Güney Kore, Malezya dahil) başlattı ve sonraki gelişen piyasa kriz analizlerinin temel referans noktası oldu.",
        "market_reaction": (
            "Baht aylar içinde %-50'den fazla değer kaybetti, bölge borsaları çöktü, IMF çok "
            "sayıda ülkeye kurtarma paketi sağladı; bu kriz sonrasında Asya ülkeleri devasa "
            "döviz rezervi biriktirme stratejisine yöneldi - 2000 sonrası dönemde Asya'nın "
            "krizlere karşı görece dayanıklılığının (2008 GFC'de Asya'nın Batı'ya göre daha "
            "az hasar görmesi) temel nedeni budur."
        ),
    },
    # ---------------------------------------------------------------
    # Ek: Rusya-Ukrayna savaşının ayrıntılı zaman çizelgesi, Epstein davası,
    # geçmişte doğru çıkan büyük kurum/düşünce kuruluşu raporları, önemli
    # davalar/tekel soruşturmaları
    # ---------------------------------------------------------------
    {
        "id": "russia_ukraine_invasion_full_scale_2022",
        "date": "2022-02-24",
        "title": "Rusya'nın Ukrayna'yı Tam Kapsamlı İşgali",
        "category": "Savaş/Jeopolitik",
        "event": "Rusya, 24 Şubat 2022'de Ukrayna'ya çok cepheli tam kapsamlı bir askeri işgal başlattı; Batı ülkeleri Rusya'ya karşı tarihin en kapsamlı yaptırım paketlerinden birini (SWIFT'ten çıkarma, merkez bankası varlıklarının dondurulması, enerji ithalat kısıtlamaları) uyguladı.",
        "market_reaction": (
            "Küresel borsalar savaşın ilk günü %-3-5 sattı, Brent petrol $139'a fırladı (2008'den "
            "beri en yüksek), doğalgaz Avrupa'da rekor kırdı, buğday/mısır fiyatları (Rusya-"
            "Ukrayna küresel tahıl ihracatının ~%25-30'unu karşılıyor) %+40'a varan sıçrama "
            "yaptı; savunma sanayi hisseleri (Lockheed Martin, Rheinmetall) güçlü ralli yaptı, "
            "ruble geçici olarak çöktü ama Rusya Merkez Bankası'nın sermaye kontrolleri/faiz "
            "artışıyla (%9.5'ten %20'ye) stabilize edildi."
        ),
    },
    {
        "id": "russia_sanctions_energy_embargo_2022_2023",
        "date": "2022-06..2023-02",
        "title": "AB'nin Rus Petrolü/Gazına Ambargo Kararları",
        "category": "Petrol Krizi",
        "event": "AB, Rus petrolüne deniz yoluyla ithalat yasağı (Aralık 2022) ve G7 fiyat tavanı uygulamasını, ardından rafine ürünlere ambargoyu (Şubat 2023) yürürlüğe koydu; Rusya karşılığında Avrupa'ya doğalgaz akışını büyük ölçüde kesti (Nord Stream).",
        "market_reaction": (
            "Avrupa doğalgaz fiyatları 2022 yazında rekor seviyelere (normalin 10 katından "
            "fazla) fırladı, enerji yoğun Avrupa sanayi üretimi (özellikle Almanya'da kimya/"
            "metal) daraldı; Rusya petrolünü Hindistan/Çin'e iskontolu satarak ihracat hacmini "
            "büyük ölçüde korudu - ambargonun 'fiyat etkisi güçlü, hacim etkisi sınırlı' "
            "kaldığı, küresel petrol piyasasının yeniden yönlendirildiği bir örnek oldu."
        ),
    },
    {
        "id": "russia_ukraine_ceasefire_prospect_scenario",
        "date": "2024-2026 (senaryo)",
        "title": "Öngörü: Rusya-Ukrayna Savaşının Sona Ermesi/Ateşkes İhtimali",
        "category": "Öngörü/Senaryo",
        "event": (
            "Olası bir kalıcı ateşkes/barış anlaşması senaryosu: Batı yaptırımlarının kademeli "
            "gevşetilmesi, Rus enerji/tahıl ihracatının normalleşmesi ve yeniden yapılanma "
            "(Ukrayna) yatırımlarının başlaması."
        ),
        "market_reaction": (
            "TAHMİN (2008 Gürcistan savaşı sonrası normalleşme ve 2015 Minsk ateşkesi "
            "analojilerine dayanarak): Ateşkes haberi anında küresel petrol/gaz/tahıl "
            "fiyatlarında %-5-15 sert düşüş, Avrupa borsalarında (özellikle Almanya DAX, enerji "
            "yoğun sanayi) güçlü ralli, ruble ve Rus varlıklarında toparlanma, inşaat/yeniden "
            "yapılanma temalı hisselerde (çimento, ağır makine) ilgi artışı beklenir. Ancak "
            "yaptırımların TAMAMEN kaldırılması yıllar sürebileceğinden etkinin kademeli "
            "olacağı, kalıcı olmayan bir ateşkesin (2015 Minsk gibi) ise kısa süreli rallinin "
            "ardından fiyatların savaş-öncesi seviyelere kısmen geri dönmesine yol açabileceği "
            "değerlendirilir. Bu bir TAHMİNDİR, kesinlik taşımaz."
        ),
    },
    {
        "id": "russia_embargo_permanent_scenario",
        "date": "2025+ (senaryo)",
        "title": "Öngörü: Rusya Ambargolarının Kalıcı Hale Gelmesi Durumunda Etkisi",
        "category": "Öngörü/Senaryo",
        "event": (
            "Varsayımsal senaryo: Batı'nın Rusya'ya uyguladığı enerji/finans yaptırımlarının "
            "savaş sona erse dahi kaldırılmayıp uzun vadede (İran/Küba modeli gibi) kalıcı "
            "hale gelmesi."
        ),
        "market_reaction": (
            "TAHMİN (İran'a 1979'dan beri süren yaptırımlar ve Küba ambargosu analojilerine "
            "dayanarak): Rusya enerji ihracatını Çin/Hindistan/Global South'a kalıcı olarak "
            "yönlendirir, ruble/yuan ticareti yapısallaşır, Batılı enerji şirketleri Rusya "
            "pazarından tamamen çekilmiş olarak kalır. Avrupa enerji fiyatları LNG (ABD/Katar "
            "kaynaklı) ile yeni bir denge seviyesinde (savaş öncesine göre yapısal olarak daha "
            "yüksek) sabitlenir. Küresel petrol/gaz ticareti iki bloklu (Batı vs. Rusya-Çin "
            "ekseni) bir yapıya kademeli evrilir - bu, dolar dışı ticaretin (yuan/ruble takası) "
            "büyümesini hızlandırabilecek yapısal bir trend olarak değerlendirilir. Bu bir "
            "TAHMİNDİR, kesinlik taşımaz ve jeopolitik gelişmelere göre değişebilir."
        ),
    },
    {
        "id": "epstein_case_2019_arrest_death",
        "date": "2019-07..2019-08",
        "title": "Jeffrey Epstein'ın Tutuklanması ve Cezaevinde Ölümü",
        "category": "Yasal Süreç/Dava",
        "event": "Milyarder Jeffrey Epstein, çocuklara yönelik cinsel istismar/kaçakçılık suçlamasıyla Temmuz 2019'da tutuklandı; Ağustos 2019'da New York'ta cezaevinde ölü bulundu (intihar olarak açıklandı).",
        "market_reaction": (
            "Doğrudan bir 'piyasa endeksi' hareketi yaratmadı, ancak Epstein ile iş bağlantısı "
            "olan büyük finans kurumları (JPMorgan, Deutsche Bank) için itibar/hukuki risk "
            "primi oluştu; bu kurumlar sonraki yıllarda mağdurlarla milyonlarca-yüz milyonlarca "
            "dolarlık uzlaşma ödemeleri yaptı (JPMorgan ~$290M, Deutsche Bank ~$75M, 2023). "
            "Olay, bankaların 'yüksek riskli müşteri' (high-risk client) durum tespiti (KYC/AML) "
            "süreçlerinin düzenleyici denetimini artırdı."
        ),
    },
    {
        "id": "epstein_estate_lawsuits_2020_2024",
        "date": "2020-01..2024-12",
        "title": "Epstein Davası Sonrası Kurumsal Uzlaşmalar ve Dosyaların Açıklanması",
        "category": "Yasal Süreç/Dava",
        "event": "Epstein'ın mağdurları, onunla finansal/kurumsal bağlantısı olan bankalara ve kişilere karşı seri davalar açtı; mahkeme kararıyla binlerce sayfalık dosya/isim listesi kademeli olarak kamuoyuna açıklandı (2024).",
        "market_reaction": (
            "İlgili bankaların hisseleri her yeni uzlaşma/dosya açıklaması haberinde kısa süreli "
            "hafif baskı gördü ama etkiler kurumsal ölçekte (trilyon dolarlık bilançolar) "
            "sınırlı kaldı; olayın asıl piyasa etkisi, büyük bankaların 'ünlü/yüksek profilli "
            "müşteri' ilişkilerinde uyum (compliance) harcamalarını kalıcı olarak artırması "
            "şeklinde oldu - dolaylı ve uzun vadeli bir maliyet etkisi."
        ),
    },
    {
        "id": "michael_burry_subprime_short_2007",
        "date": "2005-2007",
        "title": "Michael Burry'nin Subprime Mortgage Krizini Doğru Öngörmesi",
        "category": "Öngörü/Rapor",
        "event": "Scion Capital'in kurucusu Michael Burry, 2005'te ABD konut kredisi piyasasındaki balonu tespit ederek CDS (kredi temerrüt takası) yoluyla subprime mortgage tahvillerine karşı milyarlarca dolarlık kısa pozisyon açtı; bu bahis 2007-2008'de krizin patlamasıyla doğrulandı ve fonuna %+489 getiri sağladı.",
        "market_reaction": (
            "DOĞRU ÇIKAN ÖNGÖRÜ: 2007 ortasına kadar piyasa ve derecelendirme kuruluşları (Moody's/"
            "S&P) subprime tahvillere AAA notu vermeye devam etti, Burry'nin uyarıları büyük "
            "ölçüde göz ardı edildi; Ağustos 2007'de Bear Stearns'ün iki hedge fonunun çökmesiyle "
            "başlayan kriz, 2008'de Lehman'a kadar genişledi - erken ve doğru teşhis konulan "
            "sistemik risklerin piyasa/düzenleyiciler tarafından uzun süre göz ardı "
            "edilebileceğinin klasik örneği olarak kabul edilir."
        ),
    },
    {
        "id": "roubini_dr_doom_2006_prediction",
        "date": "2006-09",
        "title": "Nouriel Roubini'nin IMF Konuşmasında 2008 Krizini Öngörmesi",
        "category": "Öngörü/Rapor",
        "event": "Ekonomist Nouriel Roubini, Eylül 2006'da IMF'de yaptığı konuşmada ABD konut balonunun patlayacağını, bunun bankacılık sistemini ve reel ekonomiyi resesyona sürükleyeceğini net biçimde öngördü; o dönem çoğu ekonomist tarafından alaycı bir tavırla karşılandı ('Dr. Doom' lakabı buradan geldi).",
        "market_reaction": (
            "DOĞRU ÇIKAN ÖNGÖRÜ: 2007-2009 Küresel Finans Krizi tam olarak Roubini'nin tarif "
            "ettiği şekilde gerçekleşti (konut balonu → bankacılık krizi → küresel resesyon); "
            "bu olay sonrasında makro-ihtiyatlı (macroprudential) risk analizinin merkez "
            "bankaları ve IMF tarafından ciddiye alınmasını hızlandırdı."
        ),
    },
    {
        "id": "goldman_sachs_brics_report_2001",
        "date": "2001-11",
        "title": "Goldman Sachs'ın BRIC Raporu (Jim O'Neill)",
        "category": "Öngörü/Rapor",
        "event": "Goldman Sachs baş ekonomisti Jim O'Neill, Kasım 2001'de yayınladığı raporda Brezilya, Rusya, Hindistan ve Çin'in (BRIC) önümüzdeki on yıllarda küresel büyümenin ana motoru olacağını öngördü; terim daha sonra yaygın bir yatırım/jeopolitik kategorisi haline geldi.",
        "market_reaction": (
            "BÜYÜK ÖLÇÜDE DOĞRU ÇIKAN ÖNGÖRÜ: 2001-2010 arasında BRIC ülkeleri gerçekten de "
            "küresel GSYH büyümesinin orantısız büyük bir bölümünü oluşturdu, gelişen piyasa "
            "yatırım fonları (BRIC ETF'leri) devasa büyüdü; 2008 sonrası Çin'in yavaşlaması ve "
            "Rusya/Brezilya'nın emtia bağımlılığı nedeniyle tez kısmen zayıfladı, ancak Çin ve "
            "Hindistan'ın küresel ekonomideki ağırlık artışı öngörüsü büyük ölçüde doğrulandı."
        ),
    },
    {
        "id": "imf_financial_stability_warnings_2007",
        "date": "2007-04",
        "title": "IMF'nin Küresel Finansal İstikrar Raporu'nda Kredi Riski Uyarıları",
        "category": "Öngörü/Rapor",
        "event": "IMF, Nisan 2007 Global Financial Stability Report'unda subprime mortgage piyasasındaki kredi kalitesi bozulmasına ve yapılandırılmış kredi ürünlerinin (CDO) şeffaflık eksikliğine dikkat çekti, ancak sistemik risk seviyesini 'yönetilebilir' olarak değerlendirdi.",
        "market_reaction": (
            "KISMEN DOĞRU ÇIKAN ÖNGÖRÜ: IMF riskin varlığını doğru tespit etti ama büyüklüğünü "
            "hafife aldı; birkaç ay sonra (Ağustos 2007) kriz IMF'nin öngördüğünden çok daha "
            "şiddetli patladı. Bu olay sonrasında IMF'nin risk değerlendirme metodolojisini "
            "(stres testleri, sistemik risk endeksleri) kökten gözden geçirmesine yol açtı."
        ),
    },
    {
        "id": "world_bank_china_2030_report_2012",
        "date": "2012-02",
        "title": "Dünya Bankası'nın 'China 2030' Raporu",
        "category": "Öngörü/Rapor",
        "event": "Dünya Bankası ve Çin Devlet Konseyi Kalkınma Araştırma Merkezi'nin ortak hazırladığı 'China 2030' raporu, Çin'in yatırım/ihracat odaklı büyüme modelinden tüketim odaklı modele geçmesi gerektiğini, aksi halde 'orta gelir tuzağına' düşme riski taşıdığını öngördü.",
        "market_reaction": (
            "BÜYÜK ÖLÇÜDE DOĞRU ÇIKAN ÖNGÖRÜ: 2015 sonrası Çin büyümesi kademeli olarak yavaşladı "
            "(%10+'dan %5-6'ya), emlak sektörüne aşırı bağımlılık (Evergrande krizi 2021'de "
            "somutlaştı) ve tüketim odaklı dönüşümün öngörülenden yavaş ilerlemesi, raporun "
            "uyarılarının isabetli olduğunu gösterdi; Çin hisse senedi piyasaları 2021 "
            "sonrasında bu yapısal sorunlar nedeniyle küresel emsallerine göre düşük performans "
            "gösterdi."
        ),
    },
    {
        "id": "imf_world_bank_2008_recession_forecast_lag",
        "date": "2008-10",
        "title": "IMF/Dünya Bankası'nın Küresel Resesyon Tahminini Geç Güncellemesi",
        "category": "Öngörü/Rapor",
        "event": "IMF, Ekim 2008'de (Lehman'ın çöküşünden sadece bir ay sonra) küresel büyüme tahminini sert biçimde aşağı çekerek 2009 için resesyon öngördü; bu, krizin boyutunun kurumlar tarafından ancak gerçekleştikten sonra tam olarak kabul edildiğinin bir örneğiydi.",
        "market_reaction": (
            "TAHMİNLERİN GECİKMELİ DOĞRULANMASI: IMF'nin nihai tahmini (küresel resesyon) doğru "
            "çıktı ama uyarı krizin patlak vermesinden SONRA geldiği için piyasa için önleyici "
            "değeri sınırlı kaldı; bu durum sonraki yıllarda IMF/Dünya Bankası'nın öncü "
            "gösterge (leading indicator) bazlı erken uyarı sistemlerine daha fazla yatırım "
            "yapmasına yol açtı."
        ),
    },
    {
        "id": "bis_ray_dalio_debt_cycle_warnings_2018_2019",
        "date": "2018-2019",
        "title": "Ray Dalio (Bridgewater) ve BIS'in Borç Döngüsü/Balon Uyarıları",
        "category": "Öngörü/Rapor",
        "event": "Dünyanın en büyük hedge fonu Bridgewater'ın kurucusu Ray Dalio, 'Büyük Borç Krizleriyle Başa Çıkmak' (2018) kitabında ve BIS (Uluslararası Ödemeler Bankası) yıllık raporlarında düşük faiz ortamının yarattığı aşırı borçlanma ve varlık fiyatı şişkinliğinin bir düzeltmeye yol açacağı konusunda tekrarlanan uyarılar yaptı.",
        "market_reaction": (
            "KISMEN DOĞRU ÇIKAN ÖNGÖRÜ: 2020 COVID çöküşü (dış şok kaynaklı olsa da) ve "
            "2022 Fed faiz artış döngüsünün tetiklediği tahvil/kripto/teknoloji hisse "
            "çöküşleri, düşük faiz döneminde biriken kaldıraç/değerleme risklerinin gerçekten "
            "patlak verdiği örnekler oldu; zamanlama tam öngörüldüğü gibi olmasa da (öngörülen "
            "tetikleyici değil dış şok/politika değişimi oldu) temel tez (aşırı borç → "
            "kırılganlık) doğrulandı."
        ),
    },
    {
        "id": "jeremy_grantham_bubble_calls_2021_2022",
        "date": "2021-01..2022-06",
        "title": "Jeremy Grantham'ın (GMO) 'Süper Balon' Uyarısı",
        "category": "Öngörü/Rapor",
        "event": "Efsanevi yatırımcı Jeremy Grantham, Ocak 2021'de ABD hisse senedi/tahvil/emtia/konut piyasalarının aynı anda 'süper balon' (tarihte sadece 3-4 kez görülen türden) durumunda olduğunu ilan etti ve sert bir düzeltme öngördü.",
        "market_reaction": (
            "BÜYÜK ÖLÇÜDE DOĞRU ÇIKAN ÖNGÖRÜ: Nasdaq 2022'de zirvesinden %-35'e varan, Bitcoin "
            "%-75'e varan, yüksek büyüme/kârsız teknoloji hisseleri %-70-90 arası çöküşler "
            "yaşadı; Grantham'ın zamanlaması (uyarı Ocak 2021, zirve Kasım 2021, çöküş 2022) "
            "yaklaşık 10-12 ay erken olsa da yön ve büyüklük tahmini büyük ölçüde doğrulandı."
        ),
    },
    {
        "id": "microsoft_antitrust_case_1998_2001",
        "date": "1998-05..2001-11",
        "title": "ABD v. Microsoft Tekel Davası",
        "category": "Yasal Süreç/Dava",
        "event": "ABD Adalet Bakanlığı ve 20 eyalet, Microsoft'un Windows'a Internet Explorer'ı entegre ederek tekel gücünü kötüye kullandığı gerekçesiyle dava açtı; ilk kararda şirketin ikiye bölünmesi istendi, temyizde bu karar bozuldu ve 2001'de daha hafif bir uzlaşmayla sonuçlandı.",
        "market_reaction": (
            "Dava süresince (özellikle bölünme kararının açıklandığı Haziran 2000) Microsoft "
            "hissesi sert düşüşler yaşadı, teknoloji sektöründe genel bir 'düzenleyici risk "
            "primi' oluştu; nihai hafif uzlaşma piyasada rahatlama yarattı - büyük teknoloji "
            "tekel davalarının 'süreç boyunca belirsizlik primi, hafif sonuçla rahatlama' "
            "örüntüsünün ilk büyük vakası oldu (2020'ler Google/Meta/Amazon davalarına emsal "
            "teşkil etti)."
        ),
    },
    {
        "id": "google_antitrust_search_ruling_2024",
        "date": "2024-08",
        "title": "ABD v. Google Arama Tekeli Davası Kararı",
        "category": "Yasal Süreç/Dava",
        "event": "Bir ABD federal mahkemesi, Ağustos 2024'te Google'ın arama motoru pazarında (Apple/Samsung gibi cihaz üreticilerine milyarlarca dolar ödeyerek varsayılan arama motoru olma anlaşmaları yoluyla) yasa dışı tekel oluşturduğuna hükmetti; yaptırım (remedy) aşaması 2025'te devam etti.",
        "market_reaction": (
            "Alphabet (Google) hissesi karar günü hafif baskı gördü ama olası yaptırımların "
            "(Chrome'un satılması gibi radikal seçenekler dahil) belirsizliği nedeniyle piyasa "
            "tepkisi ölçülü kaldı; Apple hissesi de Google'dan aldığı yıllık ~$20 milyar "
            "'varsayılan arama motoru' ödemesinin risk altında olması nedeniyle izlendi - "
            "büyük teknoloji tekel davalarının kâr modeli üzerindeki dolaylı etkisinin "
            "piyasada nasıl fiyatlandığına örnek."
        ),
    },
    {
        "id": "ftc_meta_amazon_antitrust_2020s",
        "date": "2020-12..2025",
        "title": "FTC'nin Meta ve Amazon'a Karşı Tekel Davaları",
        "category": "Yasal Süreç/Dava",
        "event": "ABD Federal Ticaret Komisyonu (FTC), Meta'ya karşı (Instagram/WhatsApp satın almalarının rekabeti bastırmak için yapıldığı iddiasıyla, 2020) ve Amazon'a karşı (fiyatlandırma/satıcı platformu uygulamaları nedeniyle, 2023) ayrı tekel davaları açtı.",
        "market_reaction": (
            "Her iki şirketin hisseleri dava haberlerinde kısa süreli baskı gördü, ancak Meta/"
            "Amazon'un piyasa değeri trilyon dolar ölçeğinde olduğundan davaların 'olası "
            "sonuç' belirsizliği (bölünme ihtimali düşük görülüyor) piyasada sınırlı fiyatlandı; "
            "yatırımcılar bu tür davaların yıllarca sürdüğünü ve genellikle uzlaşma/hafif "
            "yaptırımla sonuçlandığını (Microsoft 2001 emsali) dikkate alarak temkinli ama "
            "panik yapmayan bir tutum sergiledi."
        ),
    },
    {
        "id": "boeing_737max_lawsuits_2019_2021",
        "date": "2019-03..2021-01",
        "title": "Boeing 737 MAX Kazaları Sonrası Davalar ve Uçuş Yasağı",
        "category": "Yasal Süreç/Dava",
        "event": "İki ölümcül 737 MAX kazasının (Lion Air 2018, Ethiopian Airlines 2019) ardından uçak tipi küresel çapta 20 ay boyunca uçuştan men edildi; Boeing yüzlerce dava, düzenleyici cezalar ve DOJ ile $2.5 milyarlık ceza anlaşması ile karşılaştı.",
        "market_reaction": (
            "Boeing hissesi uçuş yasağı döneminde %-25'e varan düşüş yaşadı, üretim durdurma "
            "kararları tedarik zincirini (Spirit AeroSystems gibi) olumsuz etkiledi; şirketin "
            "itibar kaybı ve yasal maliyetler yıllarca sürdü, rakip Airbus pazar payı kazandı - "
            "güvenlik/yasal krizlerin bir şirketin uzun vadeli rekabet pozisyonunu kalıcı "
            "olarak değiştirebildiği örneklerden biri."
        ),
    },
    # ---------------------------------------------------------------
    # Ek: AB Emisyon Ticaret Sistemi (ETS), sınırda karbon uygulaması,
    # rejim değişiklikleri, İsrail'e bakış açısı/jeopolitik konumu
    # ---------------------------------------------------------------
    {
        "id": "eu_ets_launch_2005",
        "date": "2005-01",
        "title": "AB Emisyon Ticaret Sistemi'nin (EU ETS) Başlatılması",
        "category": "Ticaret/Jeopolitik-Ekonomi",
        "event": "Avrupa Birliği, dünyanın ilk büyük çaplı 'karbon emisyonu al-sat' (cap-and-trade) piyasasını (EU ETS) 2005'te yürürlüğe soktu; enerji-yoğun sanayilere emisyon tavanı ve karbon kredisi ticareti getirildi.",
        "market_reaction": (
            "Karbon kredisi fiyatları başlangıçta aşırı tahsis (over-allocation) nedeniyle "
            "çöktü (Faz 1, 2006-2007'de neredeyse sıfıra indi), sistemin güvenilirliği "
            "sorgulandı; sonraki fazlarda (Faz 2-4) arz kısıtlanarak fiyat mekanizması "
            "güçlendirildi. Kömür santralleri ve ağır sanayi için karbon maliyeti kademeli "
            "olarak operasyonel gider kalemi haline geldi, temiz enerjiye geçişi teşvik etti."
        ),
    },
    {
        "id": "eu_ets_phase4_price_surge_2021",
        "date": "2021-01..2021-12",
        "title": "AB Karbon Kredisi Fiyatlarının Rekor Seviyeye Çıkması (EU ETS Faz 4)",
        "category": "Ticaret/Jeopolitik-Ekonomi",
        "event": "EU ETS'in dördüncü fazında emisyon tavanının sıkılaştırılması ve 'Yeşil Mutabakat' (Green Deal) hedefleriyle uyumlu reform beklentisi, karbon kredisi (EUA) fiyatını 2021'de tonu €30'dan €90'a fırlattı.",
        "market_reaction": (
            "Kömürle çalışan enerji şirketleri ve çimento/çelik üreticileri için maliyet baskısı "
            "belirgin biçimde arttı, bazı sanayiler üretimi Avrupa dışına kaydırma ('karbon "
            "kaçağı') riskini gündeme getirdi - bu durum doğrudan CBAM (sınırda karbon "
            "düzenleme mekanizması, 2023) tasarımının gerekçesi oldu; yenilenebilir enerji ve "
            "düşük karbonlu teknoloji şirketleri göreceli rekabet avantajı kazandı."
        ),
    },
    {
        "id": "regime_change_afghanistan_taliban_2021",
        "date": "2021-08",
        "title": "Afganistan'da Taliban'ın Yönetimi Ele Geçirmesi",
        "category": "Savaş/Jeopolitik",
        "event": "ABD'nin 20 yıllık askeri varlığını sonlandırıp çekilmesinin ardından Taliban, Ağustos 2021'de Kabil dahil ülkenin tamamını hızla ele geçirdi; hükümet çöktü.",
        "market_reaction": (
            "Küresel piyasalarda sınırlı doğrudan etki oldu (Afganistan küresel ticaret/"
            "sermaye akışında marjinal), ancak savunma sanayi hisseleri ABD'nin gelecekteki "
            "askeri harcama önceliklerine dair tartışmalarla karışık tepki verdi; olay, uzun "
            "süreli askeri müdahalelerin/rejim değişikliği projelerinin ani ve düzensiz "
            "sona erebileceğinin, bu tür 'ani rejim çöküşü' senaryolarının bölgesel para "
            "birimlerinde/emtia güzergahlarında (örn. Orta Asya boru hatları) risk primi "
            "yaratabileceğinin bir hatırlatıcısı oldu."
        ),
    },
    {
        "id": "regime_change_sri_lanka_2022",
        "date": "2022-07",
        "title": "Sri Lanka'da Halk Ayaklanması ile Rajapaksa Rejiminin Devrilmesi",
        "category": "Savaş/Jeopolitik",
        "event": "Ekonomik çöküş ve döviz krizi sonrası kitlesel protestolar, Temmuz 2022'de Cumhurbaşkanı Rajapaksa'nın ülkeyi terk edip istifa etmesiyle sonuçlandı; ülke tarihinin en ağır ekonomik/siyasi krizini yaşadı.",
        "market_reaction": (
            "Sri Lanka'nın egemen tahvilleri zaten temerrütteydi (Nisan 2022'de ilan edilmişti), "
            "rejim değişikliği IMF ile kurtarma paketi müzakerelerinin hızlanmasına zemin "
            "hazırladı; yeni yönetimin IMF programını (Mart 2023) kabul etmesiyle piyasa "
            "güveni kademeli olarak toparlandı - 'ekonomik çöküşün siyasi rejim değişikliğini "
            "tetiklemesi, ardından IMF programıyla istikrar' örüntüsünün tipik bir vakası "
            "(Arjantin, Yunanistan ile benzer)."
        ),
    },
    {
        "id": "abraham_accords_2020",
        "date": "2020-08..2020-12",
        "title": "İbrahim Anlaşmaları (Abraham Accords) - İsrail'in BAE/Bahreyn/Fas/Sudan ile Normalleşmesi",
        "category": "Savaş/Jeopolitik",
        "event": "ABD arabuluculuğunda İsrail, sırasıyla BAE, Bahreyn, Sudan ve Fas ile diplomatik ilişkileri normalleştiren anlaşmalar imzaladı - onlarca yıllık Arap-İsrail çatışma çerçevesinde önemli bir kırılma.",
        "market_reaction": (
            "İsrail borsası (TA-35) ve BAE/Bahreyn piyasaları anlaşmalar açıklandıkça olumlu "
            "tepki verdi, İsrail-Körfez ülkeleri arasında teknoloji/savunma/turizm işbirliği "
            "beklentisi arttı; bölgesel jeopolitik risk priminin azalacağı yönünde iyimserlik "
            "oluştu - ancak 2023 Gaza savaşı bu normalleşme sürecinin (özellikle Suudi "
            "Arabistan'la olası genişlemenin) kırılganlığını da gösterdi."
        ),
    },
    {
        "id": "israel_gaza_war_market_perception_2023_2025",
        "date": "2023-10..2025",
        "title": "İsrail-Gazze Savaşı Sonrası Küresel Yatırımcı Algısı ve Bölgesel Risk Primi",
        "category": "Savaş/Jeopolitik",
        "event": "Ekim 2023'te başlayan İsrail-Hamas savaşının uzaması, bölgesel yayılma riski (Hizbullah/Lübnan, Husi/Kızıldeniz saldırıları, İran ile doğrudan çatışma 2024), uluslararası kamuoyunda kutuplaşma ve bazı kurumsal/devlet yatırım fonlarının İsrail'e yönelik boykot/elden çıkarma (divestment) baskılarına yol açtı.",
        "market_reaction": (
            "İsrail şekeli (ILS) savaşın ilk aylarında %-5'e varan değer kaybetti, TA-35 "
            "endeksi baskı gördü; İsrail Merkez Bankası döviz rezervi satışıyla müdahale etti. "
            "Kızıldeniz'deki Husi saldırıları küresel deniz taşımacılığı maliyetlerini kalıcı "
            "olarak artırdı (Süveyş yerine Ümit Burnu güzergahı). Uzun süreli bölgesel "
            "çatışmaların 'ana küresel endekslere sınırlı, bölgesel varlıklara ve taşımacılık "
            "maliyetlerine yoğunlaşmış etki' örüntüsünü doğruladığı, ancak İran ile doğrudan "
            "çatışma riskinin (Nisan/Ekim 2024 karşılıklı füze saldırıları) petrol fiyatlarında "
            "geçici sıçramalara yol açtığı bir dönem oldu."
        ),
    },
    {
        "id": "analog_pattern_matching_note",
        "date": "Sürekli/Metodoloji",
        "title": "Yöntem Notu: Benzer Olaylarda Benzer Piyasa Tepkisi Beklentisi",
        "category": "Öngörü/Senaryo",
        "event": (
            "Bu veri tabanındaki senaryolar, yeni bir jeopolitik/ekonomik olay yaşandığında "
            "geçmişteki BENZER olaylarla (aynı kategori: savaş/jeopolitik, petrol krizi, "
            "merkez bankası politika şoku, pandemi, doğal afet, tekel davası vb.) "
            "karşılaştırılarak olası piyasa tepkisi yönü (risk-off/risk-on, hangi varlık "
            "sınıflarının etkileneceği) hakkında bir ön fikir (temel oran / base rate) "
            "oluşturmak için kullanılabilir."
        ),
        "market_reaction": (
            "YÖNTEM: (1) Yeni olayı kategori ve anahtar kelimelerle bu veri tabanındaki "
            "geçmiş senaryolarla eşleştir (search_historical_scenarios). (2) En benzer 2-3 "
            "analogun piyasa tepkisini incele. (3) Analogların ortak yönü aynıysa (örn. tüm "
            "ani jeopolitik şoklar kısa süreli risk-off + petrol/altın ralli + hızlı "
            "toparlanma göstermiş) benzer yönde ama TEYİTSİZ/düşük güven ağırlıklı bir pozisyon "
            "sinyali üretilebilir. (4) Bu sadece istatistiksel bir temel orandır (base rate), "
            "kesin sonuç garantisi değildir - her olay kendi bağlamında (büyüklük, süre, "
            "piyasanın önceden fiyatlayıp fiyatlamadığı) farklılık gösterebilir, bu nedenle "
            "pozisyon büyüklüğü küçük tutulmalı ve gerçek zamanlı teyit (fiyat/hacim "
            "onayı) aranmalıdır."
        ),
    },
    # ---------------------------------------------------------------
    # Ek: ABD enflasyon verisi sürprizi (13 Eylül 2022) ve büyük şirket
    # bilanço/kâr uyarısı şokları
    # ---------------------------------------------------------------
    {
        "id": "us_cpi_shock_sept13_2022",
        "date": "2022-09-13",
        "title": "ABD Ağustos 2022 Enflasyon (CPI) Verisinin Beklentilerin Üzerinde Gelmesi",
        "category": "Para Politikası",
        "event": "13 Eylül 2022'de açıklanan ABD Ağustos ayı TÜFE verisi yıllık %8.3 (beklenti %8.1) ve çekirdek TÜFE aylık %0.6 (beklenti %0.3) ile piyasanın 'enflasyon zirveyi gördü, Fed yavaşlayacak' beklentisini tamamen bozdu.",
        "market_reaction": (
            "S&P 500 tek günde %-4.32, Nasdaq %-5.16, Dow Jones %-3.94 düştü - 2020 COVID "
            "çöküşünden bu yana en kötü tek günlük performans; tahvil getirileri sert yükseldi "
            "(2 yıllık ABD tahvili %3.75'in üzerine çıktı), dolar endeksi güçlendi, kripto "
            "paralar %-8-10 arası sert düştü. Olay, piyasanın 'iyi haber = Fed şahin kalır = "
            "kötü haber' tersine dönmüş tepki mekanizmasının (enflasyon verisi beklenenden "
            "yüksek → faiz artışı beklentisi büyür → risk varlıkları satılır) ders kitabı "
            "niteliğinde bir örneği oldu. Sonraki aylarda benzer CPI sürprizlerinde piyasa "
            "aynı örüntüyü (veri açıklanmadan önce oynaklık artışı, veri sonrası sert tek "
            "yönlü hareket) tekrarladı."
        ),
    },
    {
        "id": "us_cpi_cooling_surprise_nov_2022",
        "date": "2022-11-10",
        "title": "ABD Ekim 2022 Enflasyon Verisinin Beklentilerin Altında Gelmesi (Ters Yönlü CPI Şoku)",
        "category": "Para Politikası",
        "event": "10 Kasım 2022'de açıklanan Ekim ayı TÜFE verisi yıllık %7.7 (beklenti %8.0) ile piyasanın umduğundan daha düşük geldi; bu, Eylül'deki şokun tam tersi yönde bir 'sürpriz' oldu.",
        "market_reaction": (
            "S&P 500 tek günde %+5.54, Nasdaq %+7.35 yükseldi (2020'den beri en güçlü günlerden "
            "biri), tahvil getirileri sert düştü, dolar endeksi %-2'nin üzerinde geriledi, "
            "kripto paralar ralli yaptı; bu olay CPI verisinin -yön ne olursa olsun- piyasada "
            "en yüksek etkili makro veri noktalarından biri haline geldiğini gösterdi - hem "
            "yukarı hem aşağı sürprizlerin tek günde %5+ endeks hareketi yaratabildiği "
            "kanıtlandı."
        ),
    },
    {
        "id": "earnings_shock_meta_feb_2022",
        "date": "2022-02-03",
        "title": "Meta'nın Kullanıcı Kaybı ve Zayıf Kâr Beklentisi Açıklaması",
        "category": "Şirket Bilançosu Şoku",
        "event": "Meta (Facebook), tarihinde ilk kez günlük aktif kullanıcı sayısında düşüş bildirdi ve Apple'ın gizlilik değişikliklerinin (ATT) reklam gelirine $10 milyar zarar vereceğini açıkladı.",
        "market_reaction": (
            "Hisse tek günde %-26.4 çöktü - ABD borsa tarihinde bir şirketin tek günde kaybettiği "
            "en yüksek piyasa değeri (~$230 milyar); diğer sosyal medya/reklam şirketleri "
            "(Snap, Pinterest, Twitter) de benzer risklere maruz kaldığı için domino etkisiyle "
            "sert düştü - tek bir şirketin bilanço uyarısının tüm bir sektörü aynı gün "
            "yeniden fiyatlandırabildiğinin klasik örneği."
        ),
    },
    {
        "id": "earnings_shock_amazon_q1_2022",
        "date": "2022-04-28",
        "title": "Amazon'un Beklenmedik Zarar Açıklaması (Q1 2022)",
        "category": "Şirket Bilançosu Şoku",
        "event": "Amazon, pandemi sonrası aşırı büyütülmüş lojistik kapasitesi, artan işçilik/yakıt maliyetleri ve Rivian yatırımındaki değer kaybı nedeniyle 2015'ten beri ilk kez çeyreklik net zarar açıkladı.",
        "market_reaction": (
            "Hisse tek günde %-14 düştü, e-ticaret segmentinin kâr marjı erimesi yatırımcıları "
            "şaşırttı; benzer 'pandemi döneminde aşırı kapasite artırıp şimdi daralan' sorunu "
            "yaşayan diğer e-ticaret/lojistik şirketlerinde de (Shopify, FedEx) satış baskısı "
            "gözlendi - pandemi sonrası 'talep normalleşmesi' temasının bilançolara yansıdığı "
            "dönemin sembol olaylarından biri."
        ),
    },
    {
        "id": "earnings_shock_snap_q2_2022",
        "date": "2022-05-23",
        "title": "Snap Inc.'in Ani Kâr Uyarısı (Beklenmedik Profit Warning)",
        "category": "Şirket Bilançosu Şoku",
        "event": "Snap, çeyrek sonu gelmeden düzenlediği yatırımcı toplantısında makroekonomik ortamın beklenenden hızlı kötüleştiğini, gelir/kâr hedeflerini tutturamayacağını açıkladı.",
        "market_reaction": (
            "Snap hissesi tek günde %-43 çöktü (halka arzından beri en kötü günü); reklam "
            "gelirine bağımlı tüm dijital reklam sektörü (Meta %-7.6, Pinterest %-23, Alphabet "
            "%-5) aynı gün sert satıldı - bir şirketin 'sektörün öncü göstergesi' (bellwether) "
            "olarak algılanmasının, tek başına açıklamasının tüm bir sektörü aşağı "
            "çekebildiğinin örneği."
        ),
    },
    {
        "id": "earnings_shock_fedex_sept_2022",
        "date": "2022-09-15",
        "title": "FedEx'in Gelir Tahminini Geri Çekmesi (Küresel Talep Uyarısı)",
        "category": "Şirket Bilançosu Şoku",
        "event": "FedEx, küresel taşımacılık hacimlerinin özellikle Asya ve Avrupa'da beklenenden hızlı zayıfladığını belirterek yıllık kâr tahminini geri çekti ve CEO 'küresel resesyona giriyoruz' uyarısında bulundu.",
        "market_reaction": (
            "FedEx hissesi tek günde %-21 düştü (1980'lerden beri en kötü günü); UPS ve diğer "
            "lojistik/nakliye şirketleri de düşüşe katıldı, S&P 500 sanayi sektörü genelinde "
            "baskı oluştu - FedEx'in küresel ticaret hacminin öncü göstergesi olarak "
            "görülmesi nedeniyle açıklama tek bir şirketin ötesinde makro resesyon endişesini "
            "tetikledi."
        ),
    },
    {
        "id": "earnings_shock_target_walmart_2022",
        "date": "2022-05-17..2022-05-18",
        "title": "Target ve Walmart'ın Enflasyon Kaynaklı Kâr Marjı Çöküşü",
        "category": "Şirket Bilançosu Şoku",
        "event": "Walmart ve Target, tüketicilerin gıda/yakıta harcama kaydırması nedeniyle giyim/elektronik gibi yüksek marjlı ürünlerde stok fazlası oluştuğunu ve nakliye/işçilik maliyetlerinin marjları eritiğini açıkladı.",
        "market_reaction": (
            "Walmart hissesi %-6.8, Target hissesi %-24.9 düştü (Target'ın 1987'den beri en "
            "kötü günü); perakende sektörü genelinde satış dalgası yaşandı - enflasyonun "
            "tüketici harcama alışkanlıklarını değiştirerek büyük perakendecilerin kâr "
            "marjlarını beklenmedik şekilde nasıl sıkıştırabildiğinin göstergesi oldu."
        ),
    },
    {
        "id": "earnings_shock_intel_2022_2023",
        "date": "2022-07..2023-01",
        "title": "Intel'in Art Arda Gelen Zayıf Bilançoları ve Pazar Payı Kaybı",
        "category": "Şirket Bilançosu Şoku",
        "event": "Intel, PC/sunucu çip talebinin daralması ve AMD/Nvidia'ya karşı pazar payı kaybı nedeniyle art arda çeyreklerde beklenti altı gelir, marj daralması ve temettü kesintisi (2023) açıkladı.",
        "market_reaction": (
            "Intel hissesi 2022 Temmuz bilançosunda tek günde %-8.6, sonraki çeyreklerde de "
            "tekrarlayan düşüşler yaşadı, hisse 2022'de yıllık %-49 ile Dow Jones'un en kötü "
            "performans gösteren bileşeni oldu; bir zamanlar sektör lideri olan bir şirketin "
            "art arda gelen zayıf bilançolarla yatırımcı güveninin kademeli ve kalıcı biçimde "
            "aşınmasının örneği."
        ),
    },
    {
        "id": "earnings_shock_boeing_2019_2024",
        "date": "2019-2024",
        "title": "Boeing'in Tekrarlayan Üretim/Kalite Sorunları Kaynaklı Bilanço Zararları",
        "category": "Şirket Bilançosu Şoku",
        "event": "Boeing, 737 MAX krizi (2019), pandemi kaynaklı uçak talebi çöküşü (2020) ve Ocak 2024'teki Alaska Airlines kapı paneli olayı sonrası üretim yavaşlatmaları nedeniyle yıllarca art arda milyarlarca dolarlık zarar açıkladı.",
        "market_reaction": (
            "Hisse her yeni kalite/güvenlik olayında (2019 uçuş yasağı, Ocak 2024 kapı paneli "
            "olayında tek günde %-8) tekrar sert düşüş yaşadı; şirketin serbest nakit akışı "
            "yıllarca negatif kaldı, kredi notu yatırım yapılabilir seviyenin sınırında kaldı - "
            "tekrarlayan operasyonel/kalite krizlerinin bir şirketin bilançosunu YILLARCA "
            "kalıcı olarak zayıflatabildiğinin uzun soluklu örneği."
        ),
    },
    {
        "id": "earnings_shock_nvidia_2023_2025_beats",
        "date": "2023-05..2025",
        "title": "Nvidia'nın Art Arda Beklentileri Fazlasıyla Aşan Bilançoları (Ters Yönlü Örnek)",
        "category": "Şirket Bilançosu Şoku",
        "event": "Nvidia, yapay zeka çip talebindeki patlama nedeniyle 2023'ten itibaren art arda çeyreklerde analist beklentilerini büyük farkla aşan gelir/kâr açıkladı (bazı çeyreklerde gelir bir önceki yıla göre %2-3 katına çıktı).",
        "market_reaction": (
            "Her bilanço açıklamasında hisse %+10-25 arası sıçradı, şirket piyasa değeri "
            "olarak dünyanın en değerli şirketleri arasına girdi; bu, 'kötü bilanço = sert "
            "düşüş' örüntüsünün TAM TERSİ - beklenti fazlasıyla aşan bilançoların da tek "
            "başına bir hisseyi ve ilişkili tüm tedarik zincirini (TSMC, SK Hynix, Micron) "
            "aynı gün nasıl yukarı çekebildiğinin örneği."
        ),
    },
    # ---------------------------------------------------------------
    # Ek: İşsizlik/istihdam (NFP) veri sürprizleri ve siyasetçi/etkili
    # kişi (ör. Elon Musk) açıklamalarının piyasaya etkisi
    # ---------------------------------------------------------------
    {
        "id": "nfp_shock_jan_2023_blowout",
        "date": "2023-02-03",
        "title": "ABD Ocak 2023 Tarım Dışı İstihdam (NFP) Verisinin Beklentileri Fazlasıyla Aşması",
        "category": "Para Politikası",
        "event": "ABD Ocak 2023 tarım dışı istihdam verisi 517.000 kişi artışla açıklandı (beklenti ~185.000), işsizlik oranı %3.4 ile 1969'dan beri en düşük seviyeye geriledi.",
        "market_reaction": (
            "'İyi haber = kötü haber' mekanizması devreye girdi: çok güçlü istihdam verisi "
            "Fed'in faizleri daha uzun süre yüksek tutacağı endişesini artırdığı için S&P 500 "
            "%-1, Nasdaq %-1.6 düştü, tahvil getirileri sert yükseldi, dolar güçlendi; "
            "işsizlik/istihdam verilerinin ekonomik açıdan 'iyi' olmasının borsa için her "
            "zaman olumlu olmadığının (Fed politikası beklentisi üzerinden ters işleyebildiğinin) "
            "tipik bir örneği."
        ),
    },
    {
        "id": "nfp_shock_aug_2024_weak_recession_fear",
        "date": "2024-08-02",
        "title": "ABD Temmuz 2024 İstihdam Verisinin Beklenti Altı Gelmesi ve Resesyon Korkusu",
        "category": "Para Politikası",
        "event": "ABD Temmuz 2024 tarım dışı istihdam verisi sadece 114.000 (beklenti ~175.000) ile geldi, işsizlik oranı %4.3'e yükselerek 'Sahm Kuralı' (işsizlikte hızlı artışın resesyon sinyali sayıldığı ekonomik gösterge) tetiklendi.",
        "market_reaction": (
            "Zayıf istihdam verisi, aynı hafta içindeki BOJ faiz artışıyla birleşerek "
            "5 Ağustos 2024'teki yen carry trade çözülmesi/küresel satış dalgasının ana "
            "tetikleyicilerinden biri oldu (Nikkei tek günde %-12.4, S&P 500 %-3); bu olay "
            "zayıf istihdam verisinin -tıpkı güçlü veri gibi- ama bu kez 'resesyon riski "
            "büyüyor' kanalıyla piyasayı sarsabildiğini gösterdi. Fed birkaç hafta sonra "
            "(Eylül 2024) faiz indirim döngüsüne 50 baz puanlık büyük bir adımla başladı."
        ),
    },
    {
        "id": "elon_musk_funding_secured_tweet_2018",
        "date": "2018-08-07",
        "title": "Elon Musk'ın 'Funding Secured' (Finansman Sağlandı) Tweet'i",
        "category": "Açıklama/İfade Şoku",
        "event": "Elon Musk, Tesla'yı hisse başına $420'dan özelleştirmeyi düşündüğünü ve 'finansmanın sağlandığını' Twitter'da duyurdu; iddia sonradan doğru çıkmadı, SEC bu açıklamayı yatırımcı yanıltma (piyasa manipülasyonu) olarak değerlendirdi.",
        "market_reaction": (
            "Tesla hissesi tweet sonrası saatler içinde %+11 sıçradı, işlem durdurulmak zorunda "
            "kaldı; birkaç hafta sonra planın gerçek olmadığı ortaya çıkınca hisse geri düştü, "
            "SEC Musk ve Tesla'ya toplam $40 milyon ceza kesti ve Musk'ın 'yönetim kurulu "
            "başkanlığını 3 yıl bırakması + finansal açıklamaların önceden onaylanması' "
            "şartını getirdi - tek bir yöneticinin sosyal medya paylaşımının SEC düzenlemesini "
            "tetikleyebildiği ilk büyük örneklerden biri oldu."
        ),
    },
    {
        "id": "elon_musk_dogecoin_tweets_2021",
        "date": "2021-01..2021-05",
        "title": "Elon Musk'ın Dogecoin Tweet'leri ve Kripto Fiyat Oynaklığı",
        "category": "Açıklama/İfade Şoku",
        "event": "Elon Musk, 2021 boyunca Twitter'da tekrar tekrar Dogecoin'e (esprili/meme amaçlı başlayan bir kripto para) atıfta bulunan paylaşımlar yaptı (ör. 'Dogecoin is the people's crypto', SNL performansı öncesi/sonrası paylaşımlar).",
        "market_reaction": (
            "Dogecoin, Musk'ın her tweet'inde dakikalar içinde %+20-50 arası sert yükselişler "
            "yaşadı, bazı günlerde piyasa değeri onlarca milyar dolar arttı/azaldı; SNL "
            "programındaki 'It's a hustle' esprisinden sonra ise %-30'a varan ani düşüş "
            "yaşandı - tek bir kişinin sosyal medya paylaşımlarının, düşük likiditeli bir "
            "varlık sınıfında (meme kripto paralar) kurumsal analiz/bilançodan bağımsız "
            "olarak fiyatı doğrudan hareket ettirebildiğinin aşırı örneği."
        ),
    },
    {
        "id": "tesla_bitcoin_purchase_and_reversal_2021",
        "date": "2021-02-08..2021-05-12",
        "title": "Tesla'nın Bitcoin Alımı ve Sonra Ödeme Kabulünü İptal Etmesi",
        "category": "Açıklama/İfade Şoku",
        "event": "Tesla, Şubat 2021'de $1.5 milyarlık Bitcoin satın aldığını ve araç ödemelerinde BTC kabul edeceğini açıkladı; Mayıs 2021'de Musk, madencilik nedeniyle artan fosil yakıt kullanımı endişesiyle BTC ödemesini durdurduklarını duyurdu.",
        "market_reaction": (
            "İlk açıklamada Bitcoin fiyatı %+20 sıçrayarak ilk kez $44.000'i gördü (kurumsal "
            "benimseme anlatısını güçlendirdi); Mayıs'taki geri adım açıklamasında ise BTC "
            "tek günde %-15'e varan düşüş yaşadı - büyük/tanınmış bir şirketin kripto "
            "para pozisyonuna dair açıklamalarının, gerçek arz/talep temellerinden bağımsız "
            "olarak fiyatı yönlendirebildiğinin kurumsal ölçekli bir örneği."
        ),
    },
    {
        "id": "trump_china_tariff_tweets_2019",
        "date": "2019-05-05",
        "title": "Trump'ın Twitter'da Ani Çin Tarife Artışı Duyurusu",
        "category": "Açıklama/İfade Şoku",
        "event": "Ticaret müzakerelerinin olumlu gittiği izlenimi varken, Trump 5 Mayıs 2019'da Twitter'da $200 milyarlık Çin mallarına uygulanan tarifeyi %10'dan %25'e çıkaracağını aniden duyurdu.",
        "market_reaction": (
            "S&P 500 açıklama sonrası günlerde %-2'nin üzerinde düştü, Çin misilleme tarifeleriyle "
            "karşılık verdi, küresel piyasalar 'ticaret savaşı yeniden alevleniyor' korkusuyla "
            "satıldı; bu olay, tek bir sosyal medya paylaşımının haftalarca süren müzakere "
            "sürecinin kazanımlarını bir günde tersine çevirebildiğinin ve ABD-Çin ticaret "
            "savaşı döneminde piyasanın Trump'ın Twitter hesabını neredeyse resmi bir "
            "ekonomik veri kaynağı gibi izlediğinin göstergesi oldu."
        ),
    },
    {
        "id": "draghi_whatever_it_takes_2012",
        "date": "2012-07-26",
        "title": "Draghi'nin 'Whatever It Takes' (Ne Gerekirse) Konuşması",
        "category": "Açıklama/İfade Şoku",
        "event": "Avrupa Merkez Bankası Başkanı Mario Draghi, Euro'nun dağılma riskinin konuşulduğu bir dönemde Londra'da yaptığı konuşmada 'ECB, yetkisi dahilinde Euro'yu korumak için gerekeni yapacaktır... ve inanın bana, bu yeterli olacaktır' dedi - somut bir program açıklamadan sadece SÖZLÜ bir taahhütle.",
        "market_reaction": (
            "İtalyan/İspanyol tahvil getirileri (o dönem kriz seviyesinde yüksekti) konuşma "
            "sonrası günlerde sert düştü, Euro güçlendi, Avrupa borsaları ralli yaptı; hiçbir "
            "somut mekanizma açıklanmamış olmasına rağmen tek bir cümlenin piyasadaki Euro "
            "bölgesi dağılma korkusunu kalıcı olarak azaltabildiğinin - 'sözlü müdahalenin' "
            "(verbal intervention) bazen trilyon dolarlık somut programlardan daha etkili "
            "olabildiğinin merkez bankacılığı tarihindeki en çarpıcı örneği."
        ),
    },
    {
        "id": "erdogan_interest_rate_comments_2018_2021",
        "date": "2018-08..2021-11",
        "title": "Erdoğan'ın Faiz Karşıtı Açıklamaları ve Türkiye Lirası Çöküşleri",
        "category": "Açıklama/İfade Şoku",
        "event": "Cumhurbaşkanı Erdoğan'ın tekrarlayan şekilde 'faiz sebep enflasyon sonuçtur' görüşünü kamuoyunda dile getirmesi ve buna paralel merkez bankası başkanlarını görevden alması (2019, 2020, 2021), TL'nin faiz artışlarıyla desteklenmemesi beklentisini güçlendirdi.",
        "market_reaction": (
            "Kasım 2021'de Erdoğan'ın faiz indirimi çağrılarının ardından TCMB'nin enflasyon "
            "yüksekken faiz indirmesi, lirayı birkaç hafta içinde dolar karşısında %-45'e "
            "varan çöküşe sürükledi; siyasi liderin para politikasına doğrudan kamuoyu önünde "
            "müdahale söyleminin, merkez bankası bağımsızlığı algısını zedeleyerek bir ulusal "
            "para biriminde nasıl kalıcı güven kaybına yol açabildiğinin güçlü bir örneği."
        ),
    },
    {
        "id": "powell_unscripted_comments_market_moves",
        "date": "2018-10..2023",
        "title": "Powell'ın Basın Toplantılarındaki Doğaçlama Sözlerinin Piyasayı Hareket Ettirmesi",
        "category": "Açıklama/İfade Şoku",
        "event": "Fed Başkanı Powell'ın çeşitli basın toplantılarında sarf ettiği tek cümlelik ifadeler (ör. Ekim 2018'de faizlerin nötr seviyeden 'uzun bir yol var' demesi, Aralık 2018'de faiz sıkılaştırmasının 'otomatik pilotta' olduğunu söylemesi) piyasada anlık sert tepkilere yol açtı.",
        "market_reaction": (
            "Ekim 2018'deki 'uzun yol var' yorumunun ardından S&P 500 o çeyrekte %-14 düşen "
            "sert satış dalgasının parçası oldu; piyasanın FOMC metninden çok, başkanın soru-"
            "cevap bölümündeki doğaçlama ton/kelime seçimine anlık tepki verdiği tekrarlayan "
            "bir örüntü haline geldi - bu nedenle 2019 sonrası Fed iletişiminde 'forward "
            "guidance' (ileriye dönük yönlendirme) dilinin çok daha dikkatli/ölçülü "
            "kurgulanmasına yol açtı."
        ),
    },
    {
        "id": "musk_political_statements_tesla_stock_2022_2024",
        "date": "2022-10..2024-11",
        "title": "Elon Musk'ın Siyasi Açıklamaları/Trump Desteği ve Tesla Hissesine Etkisi",
        "category": "Açıklama/İfade Şoku",
        "event": "Musk'ın Twitter'ı (X) satın alıp yönetmesi ve giderek daha fazla siyasi/parti taraftarı açıklamalar yapması (2024'te Trump'a açık destek ve seçim kampanyasına aktif katılım) yatırımcıların 'CEO'nun dikkati dağılıyor' endişesini artırdı; Trump'ın seçilmesinin ardından Musk hükümette 'Verimlilik Bakanlığı' (DOGE) rolü üstlendi.",
        "market_reaction": (
            "Twitter satın alma sürecinde Musk'ın Tesla hisselerini satarak finansman sağlaması "
            "Tesla hissesinde 2022 sonunda %-65'e varan yıllık düşüşe katkıda bulundu; 2024 "
            "seçim sonrası ise Musk'ın hükümete yakınlığının Tesla'ya düzenleyici avantaj "
            "sağlayacağı beklentisiyle hisse %+40'a varan ralli yaptı - aynı kişinin siyasi "
            "açıklamalarının döneme göre hem sert negatif hem sert pozitif fiyatlamaya yol "
            "açabildiğinin örneği (2025'te Musk-Trump ilişkisinin bozulması söylentileriyle "
            "hisse yeniden sert oynaklık yaşadı)."
        ),
    },
    # ---------------------------------------------------------------
    # Ek: Büyük şirket birleşmeleri/satın almaları, iptal edilen anlaşmalar,
    # fabrika kapatmaları ve ülke terki/üretim taşıma kararları
    # ---------------------------------------------------------------
    {
        "id": "aol_time_warner_merger_2000_2009",
        "date": "2000-01..2009-12",
        "title": "AOL-Time Warner Birleşmesi ve Sonraki Çöküşü",
        "category": "Şirket Kararları (Birleşme/Kapanma/Taşınma)",
        "event": "Ocak 2000'de açıklanan $165 milyarlık AOL-Time Warner birleşmesi, dot-com balonunun zirvesinde gerçekleşen tarihin en büyük şirket birleşmesiydi; balonun patlamasıyla birlikte birleşme değer yaratmak yerine dev zarara dönüştü, 2009'da şirketler tekrar ayrıldı.",
        "market_reaction": (
            "Birleşme açıklandığında her iki hisse de yükseldi ('internet çağının geleceği' "
            "olarak pazarlandı), ancak 2002'de birleşik şirket $99 milyar değer düşüklüğü "
            "(o zamanki ABD kurumsal tarihinin en büyük tek seferlik zararı) açıkladı; hisse "
            "zirvesinden %-90'a varan çöküş yaşadı - balon döneminde yapılan hisse-takas "
            "birleşmelerinin (stock-for-stock merger) balon patladığında nasıl kalıcı değer "
            "yıkımına dönüşebildiğinin ders kitabı örneği oldu."
        ),
    },
    {
        "id": "att_time_warner_merger_battle_2016_2018",
        "date": "2016-10..2018-06",
        "title": "AT&T'nin Time Warner'ı Satın Alması ve DOJ Karşı Davası",
        "category": "Şirket Kararları (Birleşme/Kapanma/Taşınma)",
        "event": "AT&T'nin $85 milyarlık Time Warner satın alma teklifi, ABD Adalet Bakanlığı tarafından rekabeti azaltacağı gerekçesiyle mahkemeye taşındı; AT&T davayı kazanarak birleşmeyi 2018'de tamamladı (ancak 2022'de WarnerMedia'yı ayırıp Discovery ile birleştirerek stratejiden geri döndü).",
        "market_reaction": (
            "Dava süresince AT&T hissesi belirsizlik primi taşıdı, mahkeme zaferi sonrası kısa "
            "süreli ralli yaptı; ancak birleşmenin öngörülen sinerjiler yaratamaması nedeniyle "
            "AT&T 2022'de WarnerMedia'yı elden çıkarıp temettüsünü kesti - hisse yıllar içinde "
            "%-50'nin üzerinde değer kaybetti. Büyük 'dikey birleşmelerin' (içerik+dağıtım) "
            "vaat edilen sinerjiyi her zaman sağlayamayabileceğinin örneği."
        ),
    },
    {
        "id": "qualcomm_broadcom_blocked_2018",
        "date": "2018-03",
        "title": "Trump'ın Broadcom'un Qualcomm'u Satın Almasını Ulusal Güvenlik Gerekçesiyle Engellemesi",
        "category": "Şirket Kararları (Birleşme/Kapanma/Taşınma)",
        "event": "Singapur merkezli Broadcom'un $117 milyarlık Qualcomm satın alma teklifi, Trump yönetimi tarafından '5G teknolojisinde Çin'e (Huawei) rekabet avantajı kaybı' ulusal güvenlik gerekçesiyle CFIUS kararıyla veto edildi.",
        "market_reaction": (
            "Qualcomm hissesi veto haberiyle %-4 düştü (satın alma priminin kaybolması), "
            "Broadcom hissesi ise sınırlı tepki verdi; olay, yarı iletken sektöründeki büyük "
            "sınır ötesi birleşmelerin artık salt finansal değil JEOPOLİTİK (ulusal güvenlik/"
            "teknoloji üstünlüğü) mercekten değerlendirildiğinin - 2018 sonrası ABD-Çin çip "
            "rekabetinin habercisi olan - erken bir örneği oldu."
        ),
    },
    {
        "id": "nvidia_arm_deal_collapse_2022",
        "date": "2020-09..2022-02",
        "title": "Nvidia'nın Arm Satın Alma Teklifinin Düzenleyici Engellerle Çökmesi",
        "category": "Şirket Kararları (Birleşme/Kapanma/Taşınma)",
        "event": "Nvidia'nın SoftBank'tan Arm'ı (çip mimarisi lisanslayan İngiliz şirket) $40 milyara satın alma teklifi, ABD/İngiltere/AB/Çin düzenleyicilerinin rekabet endişeleri (Arm'ın tarafsızlığının bozulacağı) nedeniyle 17 ay süren incelemenin ardından Şubat 2022'de resmen iptal edildi.",
        "market_reaction": (
            "Anlaşmanın çökmesiyle SoftBank, Arm'ı doğrudan halka arz etmeye (2023, Nasdaq'ta "
            "$54.5 milyar değerleme ile) yöneldi; Nvidia'nın hissesi anlaşma iptalinden "
            "büyük ölçüde etkilenmedi (zaten AI çip talebiyle güçlü büyüyordu) ama olay, "
            "yarı iletken sektöründeki büyük konsolidasyon girişimlerinin küresel düzenleyici "
            "'çoklu veto' riskiyle (dört ayrı otoritenin herhangi birinin reddetmesi yeterli) "
            "karşı karşıya olduğunu gösterdi."
        ),
    },
    {
        "id": "pfizer_allergan_inversion_collapse_2016",
        "date": "2015-11..2016-04",
        "title": "Pfizer-Allergan'ın $160 Milyarlık Vergi Kaçış (Inversion) Birleşmesinin İptali",
        "category": "Şirket Kararları (Birleşme/Kapanma/Taşınma)",
        "event": "Pfizer'ın İrlanda merkezli Allergan'ı satın alarak şirket merkezini vergi avantajı için İrlanda'ya taşımayı (tax inversion) planladığı anlaşma, ABD Hazine Bakanlığı'nın Nisan 2016'da yeni kurallarla bu tür 'vergi kaçış' birleşmelerini fiilen engellemesiyle iptal edildi.",
        "market_reaction": (
            "Allergan hissesi iptal haberiyle %-15 düştü (satın alma priminin kaybolması), "
            "Pfizer hissesi ise %+3 ile hafif olumlu tepki verdi (iptal etme ücreti ödemek "
            "zorunda kalsa da); olay, ABD hükümetinin düzenleyici gücünü kullanarak salt "
            "vergiden kaçınmak için tasarlanmış dev birleşmeleri geriye dönük olarak "
            "engelleyebildiğinin göstergesi oldu."
        ),
    },
    {
        "id": "foxconn_wisconsin_project_collapse_2018_2021",
        "date": "2018-07..2021-05",
        "title": "Foxconn'un Wisconsin Fabrika Projesinin Büyük Ölçüde İptali",
        "category": "Şirket Kararları (Birleşme/Kapanma/Taşınma)",
        "event": "Trump yönetiminin büyük tanıtımla duyurduğu (2018), Foxconn'un Wisconsin'de $10 milyarlık LCD ekran fabrikası ve 13.000 iş vaadi, eyalet teşviklerine ($3 milyar) rağmen kademeli olarak küçültüldü; nihai yatırım ve istihdam vaat edilenin çok altında (birkaç yüz kişi) kaldı.",
        "market_reaction": (
            "Doğrudan büyük bir hisse hareketi yaratmadı (Foxconn Tayvan borsasında işlem "
            "görüyor, ABD projesi görece küçük bir parçaydı), ancak olay ABD'de 'büyük "
            "üretim yatırımı teşvik paketlerinin' siyasi vaat ile gerçekleşen sonuç arasındaki "
            "farkın sembolü haline geldi - yerel ekonomiler ve eyalet bütçeleri için önemli "
            "bir ders (teşvik verilen yatırımların sözleşme şartlarına bağlanması gerektiği) "
            "oluşturdu."
        ),
    },
    {
        "id": "companies_exiting_russia_2022",
        "date": "2022-03..2022-12",
        "title": "Yüzlerce Küresel Şirketin Rusya'dan Çekilmesi/Faaliyeti Durdurması",
        "category": "Şirket Kararları (Birleşme/Kapanma/Taşınma)",
        "event": "Rusya'nın Ukrayna'yı işgalinin ardından McDonald's, Coca-Cola, Renault, Shell, BP, ExxonMobil, IKEA, Starbucks gibi yüzlerce küresel şirket Rusya'daki operasyonlarını durdurdu, sattı veya tamamen terk etti (McDonald's yerel varlıklarını Rus bir işadamına satarak 'Vkusno i tochka' markasına dönüştürdü).",
        "market_reaction": (
            "Çekilme kararı açıklayan şirketler (BP $25 milyar, Shell $5 milyar değer düşüklüğü "
            "açıkladı) tek seferlik büyük zarar yazdı ama hisseleri çoğunlukla sınırlı tepki "
            "verdi (yatırımcılar itibar riskinin azalmasını, Rusya gelirinin zaten küçük "
            "paya sahip olmasını olumlu karşıladı); bu olay, jeopolitik krizlerde şirketlerin "
            "'ESG/itibar baskısı' nedeniyle kısa vadeli finansal kaybı göze alarak hızlı "
            "çekilme kararı alabildiğinin - 2000 sonrası döneme özgü yeni bir davranış "
            "kalıbının - en büyük ölçekli örneği oldu."
        ),
    },
    {
        "id": "gm_plant_closures_2018_2019",
        "date": "2018-11..2019-03",
        "title": "General Motors'un Kuzey Amerika'da Beş Fabrikayı Kapatma Kararı",
        "category": "Şirket Kararları (Birleşme/Kapanma/Taşınma)",
        "event": "GM, sedan talebinin elektrikli/otonom araçlara kayan yatırım önceliği karşısında düşmesi nedeniyle ABD ve Kanada'da beş fabrikayı (Lordstown Ohio dahil) kapatacağını ve ~14.000 kişiyi işten çıkaracağını açıkladı; Trump bu kararı sert eleştirdi.",
        "market_reaction": (
            "GM hissesi kapatma duyurusuyla kısa vadede %+4 yükseldi (maliyet tasarrufu/"
            "verimlilik artışı olarak piyasada olumlu karşılandı - şirket bilançosu için "
            "iyi, yerel ekonomi için kötü haber ayrımının tipik örneği); Lordstown fabrikası "
            "sonradan elektrikli kamyon girişimcisi Lordstown Motors'a satıldı (bu şirket "
            "2023'te iflas etti) - eski üretim tesislerinin 'yeşil dönüşüm' anlatısıyla "
            "yeniden kullanılma girişimlerinin risklerini de gösteren bir örnek."
        ),
    },
    {
        "id": "ford_europe_restructuring_2024_2025",
        "date": "2024-01..2025-06",
        "title": "Ford'un Avrupa'da Fabrika Kapatma ve İşçi Çıkarma Kararları",
        "category": "Şirket Kararları (Birleşme/Kapanma/Taşınma)",
        "event": "Ford, Avrupa'da elektrikli araç talebinin beklenenden yavaş büyümesi ve Çinli üreticilerin (BYD gibi) fiyat rekabeti karşısında Almanya (Saarlouis) ve İngiltere'deki fabrikalarda kapatma/küçültme ve binlerce işçi çıkarma kararları aldı.",
        "market_reaction": (
            "Ford hissesi Avrupa restrukturizasyon maliyetleri nedeniyle bilanço açıklamalarında "
            "baskı gördü; olay, geleneksel Batılı otomotiv üreticilerinin elektrikli araca "
            "geçiş sürecinde Çinli rakiplere karşı rekabet gücü kaybettiğinin ve bunun "
            "somut istihdam/üretim kararlarına (Avrupa'da küçülme) yansıdığının güncel bir "
            "örneği oldu."
        ),
    },
    {
        "id": "apple_supply_chain_diversification_india_vietnam_2020_2024",
        "date": "2020-2024",
        "title": "Apple'ın Üretimi Çin'den Hindistan/Vietnam'a Kaydırması ('China+1' Stratejisi)",
        "category": "Şirket Kararları (Birleşme/Kapanma/Taşınma)",
        "event": "ABD-Çin ticaret gerginliği, COVID döneminde Çin'deki üretim kesintileri (Zhengzhou Foxconn fabrikasındaki 2022 protestoları dahil) ve jeopolitik risk azaltma isteğiyle Apple, iPhone üretiminin önemli bir kısmını Hindistan'a (Foxconn/Tata fabrikaları) ve bazı ürünlerini Vietnam'a kaydırmaya başladı.",
        "market_reaction": (
            "Apple hissesi doğrudan bu haberlerle sınırlı hareket etti (kademeli/uzun vadeli "
            "bir strateji, ani bir şok değil), ancak Hindistan'daki üretim ortakları (Foxconn "
            "Hindustan, Tata Electronics hisseleri Hindistan borsasında) ve Çin'deki eski "
            "tedarikçiler zıt yönde etkilendi; bu 'China+1' trendi 2020 sonrası küresel "
            "tedarik zinciri risk azaltma (de-risking) stratejisinin en görünür örneklerinden "
            "biri olarak, benzer coğrafi çeşitlendirme kararlarının diğer büyük teknoloji "
            "şirketlerinde de (Samsung, Google) tekrarlanmasına öncülük etti."
        ),
    },
    {
        "id": "toshiba_going_private_2023",
        "date": "2021-04..2023-12",
        "title": "Toshiba'nın Aktivist Yatırımcı Baskısıyla Özelleştirilmesi",
        "category": "Şirket Kararları (Birleşme/Kapanma/Taşınma)",
        "event": "Muhasebe skandalları (2015) ve yönetişim krizleriyle sarsılan Toshiba, yabancı aktivist yatırımcıların baskısı ve iç çekişmeler sonrası Japon bir konsorsiyum (Japan Industrial Partners) tarafından $14 milyara satın alınarak 2023'te 74 yıllık halka açıklık geçmişini sonlandırdı.",
        "market_reaction": (
            "Özelleştirme teklifleri sürecinde hisse belirsizlikle dalgalandı, nihai anlaşma "
            "duyurulduğunda hisse teklif fiyatına yakınsadı; olay, bir zamanlar Japonya'nın "
            "sanayi amiral gemilerinden birinin yönetişim skandalları ve aktivist yatırımcı "
            "baskısı nedeniyle nasıl borsadan çekilmeye kadar gidebildiğinin, Japonya'daki "
            "kurumsal yönetişim reformu (2010'lar sonrası) baskısının somut bir sonucu oldu."
        ),
    },
    # ---------------------------------------------------------------
    # Ek: Mülteci krizleri, ek ekonomik krizler, SEC/FINRA düzenleyici
    # kararları
    # ---------------------------------------------------------------
    {
        "id": "european_migrant_crisis_2015_2016",
        "date": "2015-04..2016-03",
        "title": "Avrupa Mülteci Krizi (Suriye İç Savaşı Kaynaklı Kitlesel Göç)",
        "category": "Mülteci/Göç Krizi",
        "event": "Suriye iç savaşı, Irak/Afganistan çatışmaları nedeniyle 2015'te bir milyondan fazla mülteci/sığınmacı Akdeniz üzerinden Avrupa'ya ulaştı; AB içinde sınır kapatma (Macaristan çit inşası), Almanya'nın 'açık kapı' politikası (Merkel) ve Mart 2016'daki AB-Türkiye mülteci anlaşması gibi kritik kararlar alındı.",
        "market_reaction": (
            "Doğrudan büyük bir borsa endeksi hareketi yaratmadı ama Euro, aşırı sağ/göç "
            "karşıtı partilerin yükselişine dair siyasi belirsizlik nedeniyle baskı gördü; "
            "Almanya'da entegrasyon/konut/güvenlik harcamaları kamu bütçesine ek yük "
            "getirdi, havayolu ve sınır turizm sektörleri (Yunan adaları) bölgesel olarak "
            "olumsuz etkilendi. Kriz, 2016 Brexit referandumunda 'göç kontrolü' temasının öne "
            "çıkmasına ve AB genelinde popülist/milliyetçi partilerin güçlenmesine zemin "
            "hazırlayarak dolaylı ama uzun soluklu bir siyasi risk primi yarattı."
        ),
    },
    {
        "id": "venezuela_migration_crisis_2015_2023",
        "date": "2015-2023",
        "title": "Venezuela Göç Krizi (Latin Amerika'nın En Büyük Kitlesel Göçü)",
        "category": "Mülteci/Göç Krizi",
        "event": "Venezuela'nın ekonomik/siyasi çöküşü nedeniyle 7 milyondan fazla Venezuelalı (nüfusun ~%25'i) başta Kolombiya, Peru, Ekvador, Şili olmak üzere komşu ülkelere göç etti - tarihte tek bir ülkeden yaşanan en büyük kitlesel göçlerden biri.",
        "market_reaction": (
            "Komşu ülkelerin (özellikle Kolombiya ve Peru) kamu hizmetleri/istihdam piyasası "
            "üzerinde baskı oluştu, bu ülkelerin para birimleri (Kolombiya pesosu) göç "
            "yükünün mali maliyetine dair endişelerle dönemsel baskı gördü; uzun vadede göçmen "
            "işgücünün ev sahibi ülke ekonomilerine (özellikle enformel sektörde) katkı "
            "sağladığı da IMF/Dünya Bankası raporlarında belirtildi - göç krizlerinin kısa "
            "vadede mali yük, uzun vadede işgücü arzı artışı şeklinde ikili etkisinin örneği."
        ),
    },
    {
        "id": "ukraine_refugee_crisis_2022",
        "date": "2022-02..2022-12",
        "title": "Ukrayna Mülteci Krizi (Rusya İşgali Sonrası)",
        "category": "Mülteci/Göç Krizi",
        "event": "Rusya'nın Şubat 2022 işgalinin ardından 8 milyondan fazla Ukraynalı (çoğunlukla kadın/çocuk) AB ülkelerine (Polonya, Almanya başta olmak üzere) sığındı; AB, Ukraynalı mültecilere normal sığınma prosedürünü atlayarak anında geçici koruma statüsü tanıyan tarihinde ilk kez uygulanan bir mekanizmayı devreye soktu.",
        "market_reaction": (
            "Polonya ve komşu ülkelerde kısa vadeli kamu harcaması artışı yaşandı ama AB'nin "
            "hızlı/koordineli mali destek mekanizması (2015 krizinin aksine) piyasada siyasi "
            "istikrarsızlık primi oluşturmadı; Polonya zlotisi ve bölge varlıkları esas olarak "
            "savaşın kendisinin jeopolitik riskiyle hareket etti, mülteci akışının kendisi "
            "ayrı bir piyasa şoku yaratmadı - 2015 krizine kıyasla çok daha hızlı/örgütlü "
            "kurumsal tepkinin piyasa güvenini koruduğu bir örnek."
        ),
    },
    {
        "id": "syrian_refugee_crisis_turkey_2011_2020",
        "date": "2011-2020",
        "title": "Suriyeli Mülteci Krizi ve Türkiye'nin En Büyük Mülteci Nüfusunu Barındırması",
        "category": "Mülteci/Göç Krizi",
        "event": "Suriye iç savaşı (2011 başlangıçlı) nedeniyle Türkiye, dünyada tek bir ülkede en fazla mülteci barındıran ülke konumuna geldi (zirvede ~3.6 milyon Suriyeli); AB-Türkiye Mart 2016 anlaşmasıyla Türkiye'ye mülteci yönetimi karşılığında mali destek ($6+ milyar) sağlandı.",
        "market_reaction": (
            "Türkiye ekonomisi için mülteci nüfusu hem kamu harcaması yükü hem de (özellikle "
            "sınır bölgelerinde) ek işgücü/tüketici tabanı olarak karma etki yarattı; TL "
            "üzerindeki asıl baskı 2018/2021 kur krizlerinden kaynaklandı (mülteci krizi "
            "doğrudan tetikleyici değildi), ancak AB ile mülteci konusundaki periyodik "
            "gerilimler (Yunanistan sınırındaki 2020 kriz gibi) Türkiye'nin AB ilişkilerine "
            "dair siyasi risk primini dönemsel olarak artırdı."
        ),
    },
    {
        "id": "lebanon_economic_collapse_2019_2023",
        "date": "2019-10..2023",
        "title": "Lübnan Ekonomik Çöküşü (Dünya Bankası'nın 'En Kötü 3 Kriz' Listesindeki Çöküş)",
        "category": "Finans Krizi",
        "event": "Lübnan lirası, on yıllarca sabit kurun ardından 2019'da çökmeye başladı; banka mevduatlarına fiili el konuldu (bankalar dolar çekimini engelledi), enflasyon yıllık binlerce yüzde seviyesine ulaştı, Dünya Bankası bu çöküşü 19. yüzyıldan beri dünyanın en kötü üç ekonomik krizinden biri olarak nitelendirdi.",
        "market_reaction": (
            "Lübnan lirası resmi kurdan (1 dolar = 1.507 LL) serbest piyasada 1 dolar = "
            "100.000+ LL seviyesine çöktü (%-98'in üzerinde değer kaybı); banka sistemi fiilen "
            "işlevini yitirdi, ülke IMF ile kurtarma paketi müzakerelerini yıllarca "
            "sonuçlandıramadı (siyasi kilitlenme nedeniyle) - 'reform yapılmadığı sürece IMF "
            "desteğinin gelmeyeceği ve krizin süresiz uzayabileceği' senaryosunun en somut "
            "örneği; Ağustos 2020 Beyrut patlamasıyla kriz daha da derinleşti."
        ),
    },
    {
        "id": "zimbabwe_hyperinflation_2007_2009",
        "date": "2007-2009",
        "title": "Zimbabve Hiperenflasyonu (Tarihin En Yüksek Enflasyon Oranlarından Biri)",
        "category": "Finans Krizi",
        "event": "Zimbabve'de tarımsal üretim çöküşü (toprak reformu politikaları) ve aşırı para basımı, 2008'de aylık enflasyonun %79.6 milyar (yıllık trilyonlarca yüzde) seviyesine ulaşmasına yol açtı; ülke 2009'da kendi para birimini tamamen terk ederek yabancı para birimlerine (ABD doları) geçti.",
        "market_reaction": (
            "Zimbabve doları pratik olarak değersizleşti (100 trilyon dolarlık banknotlar "
            "basıldı), yerel borsa (kağıt üzerinde) hiperenflasyon nedeniyle nominal olarak "
            "muazzam yükseldi ama reel (dolar bazında) değer sıfıra yakındı; olay, aşırı para "
            "basımının bir ulusal para birimini tamamen yok edebildiğinin ve 'dolarizasyon' "
            "(kendi para birimini terk etme) kararının hiperenflasyonu durdurmak için son "
            "çare olarak nasıl kullanıldığının klasik referans vakası oldu."
        ),
    },
    {
        "id": "sec_v_ripple_xrp_case_2020_2023",
        "date": "2020-12..2023-07",
        "title": "SEC'in Ripple'a (XRP) Karşı Menkul Kıymet Davası",
        "category": "Yasal Süreç/Dava",
        "event": "SEC, Aralık 2020'de Ripple Labs'ı XRP kripto parasını kayıtsız menkul kıymet olarak sattığı gerekçesiyle dava etti; Temmuz 2023'te federal mahkeme, XRP'nin borsalarda perakende yatırımcılara satışının menkul kıymet sayılmayacağına (kurumsal satışların ise sayılabileceğine) hükmetti - kripto sektöründe emsal niteliğinde kısmi bir zafer.",
        "market_reaction": (
            "Karar açıklandığında XRP fiyatı tek günde %+70'e varan sıçrama yaptı, diğer "
            "altcoin'ler de (SEC'in 'menkul kıymet' iddia ettiği Solana, Cardano gibi "
            "tokenlar) benzer emsal beklentisiyle ralli yaptı; olay, tek bir mahkeme kararının "
            "kripto piyasasının geniş bir kesimine aynı anda nasıl fiyat etkisi yapabildiğinin "
            "ve düzenleyici belirsizliğin kripto varlık fiyatlamasındaki merkezi rolünün "
            "göstergesi oldu."
        ),
    },
    {
        "id": "sec_binance_coinbase_lawsuits_2023",
        "date": "2023-06",
        "title": "SEC'in Binance ve Coinbase'e Karşı Art Arda Dava Açması",
        "category": "Yasal Süreç/Dava",
        "event": "SEC, Haziran 2023'te bir hafta arayla hem dünyanın en büyük kripto borsası Binance'e (kayıtsız menkul kıymet borsası işletmek, fonların karıştırılması) hem de ABD'nin en büyük halka açık kripto borsası Coinbase'e (kayıtsız aracı kurum/borsa/takas kurumu olarak faaliyet) karşı dava açtı.",
        "market_reaction": (
            "Coinbase hissesi dava haberiyle %-12 düştü, Bitcoin/Ethereum %-5 ile geride "
            "kaldı, davalarda 'menkul kıymet' olarak nitelendirilen onlarca altcoin (Solana, "
            "Cardano, Polygon dahil) %-10-25 arası sert satıldı; bu olay ABD düzenleyici "
            "baskısının kripto piyasasının SADECE ilgili şirketleri değil, dava dilekçesinde "
            "adı geçen TÜM token'ları aynı anda nasıl etkileyebildiğini gösterdi (Coinbase "
            "davadan bir yıl sonra, 2024'te kısmi zafer kazandı)."
        ),
    },
    {
        "id": "wells_fargo_fake_accounts_scandal_2016",
        "date": "2016-09",
        "title": "Wells Fargo Sahte Hesap Skandalı",
        "category": "Yasal Süreç/Dava",
        "event": "Wells Fargo çalışanlarının satış hedeflerini tutturmak için müşteri onayı olmadan milyonlarca sahte banka/kredi kartı hesabı açtığı ortaya çıktı; CFPB/OCC/LA şehri toplam $185 milyon ceza kesti, CEO John Stumpf istifa etti, Fed banka üzerine benzeri görülmemiş bir 'varlık büyüklüğü tavanı' (asset cap) getirdi.",
        "market_reaction": (
            "Wells Fargo hissesi skandal haberiyle günler içinde %-10'a varan düşüş yaşadı, "
            "itibar kaybı yıllarca sürdü (hisse sonraki yıllarda sektör emsallerine göre "
            "düşük performans gösterdi); Fed'in getirdiği varlık tavanı (2018-2025 arası "
            "kaldırılamadı) bankanın büyüme kapasitesini yıllarca fiilen kısıtladı - "
            "düzenleyici cezaların bazen tek seferlik para cezasından çok daha kalıcı "
            "yapısal kısıtlamalara (büyüme tavanı gibi) dönüşebildiğinin örneği."
        ),
    },
    {
        "id": "finra_gamestop_robinhood_scrutiny_2021",
        "date": "2021-01..2021-02",
        "title": "GameStop Olayı Sonrası Robinhood'un İşlem Kısıtlaması ve FINRA/SEC İncelemesi",
        "category": "Yasal Süreç/Dava",
        "event": "Ocak 2021'deki GameStop kısa sıkıştırması sırasında Robinhood ve diğer aracı kurumlar, DTCC'nin (takas kurumu) teminat taleplerini karşılayamama riskiyle GameStop/AMC gibi hisselerde ALIM işlemlerini geçici olarak durdurdu; bu karar Kongre'de duruşmalara, FINRA/SEC soruşturmalarına ve 'perakende yatırımcının kurumlara karşı korunmadığı' tartışmasına yol açtı.",
        "market_reaction": (
            "Kısıtlama haberiyle GameStop hissesi tek günde %-44 düştü (alım durdurulup satış "
            "serbest bırakılınca fiyat baskısı tek yönlü oldu); Robinhood, IPO'sunda (2021 "
            "Temmuz) bu olayın itibar hasarını taşıdı ve FINRA Haziran 2021'de şirkete o "
            "zamana dek kesilen en yüksek cezalardan birini ($70 milyon) verdi. Olay, takas/"
            "teminat altyapısındaki (arka planda görünmeyen) kısıtların bir 'meme hisse' "
            "manisini aniden durdurabildiğinin ve düzenleyici kurumların (FINRA/SEC) piyasa "
            "yapısı sorunlarına odaklanmasına yol açtığının örneği oldu."
        ),
    },
    {
        "id": "sec_climate_disclosure_rule_2024",
        "date": "2024-03",
        "title": "SEC'in İklim Riski Açıklama Zorunluluğu Kuralı",
        "category": "Yasal Süreç/Dava",
        "event": "SEC, halka açık şirketlerin iklimle ilgili risklerini ve (bazı durumlarda) sera gazı emisyonlarını finansal raporlarında açıklamasını zorunlu kılan bir kural yayınladı; kural açıklanır açıklanmaz çok sayıda eyalet/iş dünyası grubu tarafından dava edildi ve SEC nisan 2024'te kuralın uygulanmasını kendi isteğiyle askıya aldı.",
        "market_reaction": (
            "Enerji/ağır sanayi şirketleri kuralın ek uyum maliyeti getireceği endişesiyle "
            "karşı çıktı, kuralın askıya alınması bu sektörlerde kısa vadeli rahatlama "
            "yarattı; olay, düzenleyici kurumların iklim/ESG alanındaki girişimlerinin ABD'de "
            "(AB'nin aksine) güçlü hukuki/siyasi dirençle karşılaştığının ve düzenleme "
            "sürecinin yıllarca mahkeme süreçlerinde tıkanabildiğinin örneği oldu."
        ),
    },
    # ---------------------------------------------------------------
    # Ek: Büyük halka arzlar (IPO) ve bunların piyasa likiditesi üzerindeki
    # 'emme etkisi' (capital soak-up effect)
    # ---------------------------------------------------------------
    {
        "id": "facebook_ipo_2012",
        "date": "2012-05-18",
        "title": "Facebook'un Halka Arzı ve İlk Hafta Teknik Aksaklıklar",
        "category": "Halka Arz (IPO)",
        "event": "Facebook, o zamana dek teknoloji şirketleri arasında en büyük halka arzlardan birini ($16 milyar) gerçekleştirdi; Nasdaq'ın işlem sisteminde yaşanan teknik aksaklıklar nedeniyle ilk gün işlemler gecikti, fiyat istikrarsız seyretti.",
        "market_reaction": (
            "Hisse, halka arz fiyatının ($38) altına düşerek ilk aylarda %-50'ye varan kayıp "
            "yaşadı (mobil reklam gelir modelinin henüz kanıtlanmamış olması endişesi); "
            "dev bir halka arzın piyasadan çektiği sermaye ve ardından gelen hayal kırıklığı, "
            "o dönem diğer 'yeni nesil internet' IPO'larına (Zynga, Groupon) yönelik "
            "iştahı da bir süre azalttı - hisse ancak 2013'te mobil reklam gelirini "
            "kanıtlayınca kalıcı toparlanmaya geçti."
        ),
    },
    {
        "id": "alibaba_ipo_2014",
        "date": "2014-09-19",
        "title": "Alibaba'nın Tarihin (O Zamana Dek) En Büyük Halka Arzı",
        "category": "Halka Arz (IPO)",
        "event": "Çinli e-ticaret devi Alibaba, New York Borsası'nda $25 milyar toplayarak tarihin en büyük halka arzını gerçekleştirdi; talep o kadar yüksekti ki arz büyüklüğü birkaç kez artırıldı.",
        "market_reaction": (
            "Hisse ilk gün %+38 yükseldi, işlem hacmi rekor kırdı; bu denli büyük bir tek "
            "işlemin piyasadan çektiği likidite, aynı hafta içindeki bazı küçük/orta ölçekli "
            "IPO'ların ertelenmesine yol açtı (yatırımcı sermayesinin geçici olarak dev "
            "arza yönlendiği gözlemlendi) - büyük IPO'ların kısa vadede 'sermaye emme etkisi' "
            "yaratarak eşzamanlı diğer halka arzların performansını/zamanlamasını "
            "etkileyebildiğinin örneği."
        ),
    },
    {
        "id": "saudi_aramco_ipo_2019",
        "date": "2019-12-11",
        "title": "Suudi Aramco'nun Tarihin En Büyük Halka Arzı ($25.6 Milyar)",
        "category": "Halka Arz (IPO)",
        "event": "Dünyanın en kârlı şirketi Suudi Aramco, sadece Suudi/Körfez borsasında (Tadawul) sınırlı bir halka arz yaparak $25.6 milyar topladı ve şirket değeri $1.7 trilyona ulaştı (dünyanın en değerli halka açık şirketi) - ancak arz esas olarak yerel/bölgesel yatırımcılara yönelikti, küresel borsalarda işlem görmedi.",
        "market_reaction": (
            "Tadawul borsasında halka arz sonrası hisse %+10 sınırıyla (borsa kuralı) yükseldi; "
            "arzın büyük ölçüde Suudi yerel bankalarının kredilendirdiği yerel yatırımcılara "
            "dayanması, Suudi bankacılık sistemindeki likiditeyi bir süre sıkılaştırdı - "
            "dev bir yerel IPO'nun küresel piyasalardan çok, kendi iç finansal sistemindeki "
            "likiditeyi 'emebileceğinin' bir örneği (küresel endekslere dahil edilmediği için "
            "uluslararası fon akışı sınırlı kaldı)."
        ),
    },
    {
        "id": "uber_ipo_2019",
        "date": "2019-05-10",
        "title": "Uber'in Halka Arzı ve Zayıf İlk Gün Performansı",
        "category": "Halka Arz (IPO)",
        "event": "Uber, $8.1 milyar toplayarak halka açıldı ancak kârlılık belirsizliği ve o dönem ABD-Çin ticaret savaşı gerginliğinin piyasayı geniş çapta baskılaması nedeniyle ilk gün hissesi %-7.6 düşerek kapandı - dönemin en büyük teknoloji IPO'larından biri için zayıf bir başlangıçtı.",
        "market_reaction": (
            "Zayıf performans, aynı yıl halka açılmayı planlayan diğer 'unicorn' şirketlerin "
            "(WeWork gibi) değerleme beklentilerini aşağı çekti; WeWork'ün birkaç ay sonra "
            "halka arzını tamamen iptal etmesinde (2019 Eylül) Uber'in soğuk karşılanmasının "
            "da dolaylı payı olduğu değerlendirilir - büyük bir IPO'nun zayıf performansının, "
            "'IPO penceresini' (yatırımcı iştahını) sonraki şirketler için de daraltabildiğinin "
            "örneği."
        ),
    },
    {
        "id": "rivian_ipo_2021",
        "date": "2021-11-10",
        "title": "Rivian'ın Halka Arzı (Kâr Öncesi Şirket İçin Dev Değerleme)",
        "category": "Halka Arz (IPO)",
        "event": "Elektrikli kamyon üreticisi Rivian, henüz anlamlı gelir üretmeden $13.7 milyar toplayarak halka açıldı ve piyasa değeri kısa süreliğine Ford'u geçerek $150 milyara ulaştı; bu, 2021'in en büyük IPO'suydu ve dönemin 'büyüme her şeydir' yatırımcı iştahının zirvesini simgeledi.",
        "market_reaction": (
            "Hisse halka arz sonrası ilk günlerde %+50'ye varan sıçrama yaptı, ancak 2022'deki "
            "Fed faiz artışları ve kârsız büyüme şirketlerinden kaçış dalgasıyla yıl sonuna "
            "kadar %-80'in üzerinde çöktü; dev IPO'nun piyasadan çektiği spekülatif sermaye "
            "(ve ardından gelen çöküş), 2021 sonu 'her şey balonunun' (everything bubble) "
            "zirve/dönüm noktalarından biri olarak değerlendirilir."
        ),
    },
    {
        "id": "arm_holdings_ipo_2023",
        "date": "2023-09-14",
        "title": "Arm Holdings'in Nasdaq'ta Halka Arzı (2023'ün En Büyük IPO'su)",
        "category": "Halka Arz (IPO)",
        "event": "SoftBank, Nvidia'nın satın alma teklifinin düzenleyicilerce engellenmesinin ardından Arm'ı doğrudan halka arz etti; $4.9 milyar toplayan arz, 2023'ün en büyük teknoloji IPO'suydu ve yapay zeka çip talebi anlatısıyla güçlü talep gördü.",
        "market_reaction": (
            "Hisse ilk gün %+25 yükseldi; büyük/başarılı bir IPO'nun piyasada 'IPO penceresinin "
            "yeniden açıldığı' sinyalini vermesiyle sonraki aylarda Instacart, Klaviyo gibi "
            "başka şirketler de halka arz planlarını hızlandırdı - başarılı dev IPO'ların "
            "sadece sermaye çekmekle kalmayıp, ardından gelen IPO dalgası için 'güven "
            "sinyali' işlevi de görebildiğinin örneği (Uber 2019'un tam tersi bir etki)."
        ),
    },
    {
        "id": "twitter_ipo_2013",
        "date": "2013-11-07",
        "title": "Twitter'ın Halka Arzı (Facebook'un Tersine Güçlü İlk Gün)",
        "category": "Halka Arz (IPO)",
        "event": "Twitter, $1.8 milyar toplayarak halka açıldı; Facebook'un 2012'deki sorunlu halka arzından ders çıkararak daha az agresif fiyatlama ve NYSE'de (Nasdaq yerine) işlem görme stratejisi izledi.",
        "market_reaction": (
            "Hisse ilk gün %+73 yükseldi (Facebook'un aksine); ancak şirket hiçbir zaman "
            "sürdürülebilir kâr üretemedi ve kullanıcı büyümesi yavaşladı, hisse yıllar "
            "içinde halka arz fiyatının çevresinde sıkışık kaldı - sonunda 2022'de Musk "
            "tarafından özelleştirildi (bkz. Musk'ın Twitter'ı satın alması) - güçlü bir "
            "ilk gün performansının uzun vadeli iş modeli sorunlarını telafi etmediğinin "
            "örneği."
        ),
    },
    {
        "id": "ipo_capital_soak_up_liquidity_effect_note",
        "date": "Sürekli/Metodoloji",
        "title": "Yöntem Notu: Dev Halka Arzların Piyasadan Sermaye/Likidite Çekmesi Etkisi",
        "category": "Halka Arz (IPO)",
        "event": (
            "Çok büyük ($5 milyar+) bir halka arz duyurulduğunda, kurumsal yatırımcılar "
            "(özellikle endeks/tema fonları) genellikle mevcut pozisyonlarından nakde geçerek "
            "yeni arza katılım payı ayırır; bu durum arz öncesi haftalarda ilgili sektördeki "
            "diğer hisselerde hafif satış baskısı, arz sonrası ise (kilitlenme süresi bitince, "
            "genelde 90-180 gün sonra) içerden satış baskısı yaratabilir."
        ),
        "market_reaction": (
            "GÖZLEM: Facebook (2012), Alibaba (2014) ve Rivian (2021) örneklerinde arz "
            "öncesi/sonrası dönemde teknoloji sektöründeki küçük-orta ölçekli hisselerde "
            "görece zayıf performans gözlemlenmiştir; kilitlenme süresi bitiminde (lock-up "
            "expiry) içeriden büyük hissedarların (kurucular, erken yatırımcılar) satışa "
            "geçmesi de o hisse için ayrı bir düşüş baskısı dönemi yaratır (genelde arzdan "
            "3-6 ay sonra). Bu nedenle çok büyük bir IPO haberi geldiğinde, aynı sektördeki "
            "diğer hisselerde kısa vadeli göreceli zayıflık ve arzın kendisinde kilitlenme "
            "bitiş tarihi civarında ek oynaklık beklenmesi mantıklı bir temel orandır (base "
            "rate) - kesinlik taşımaz, teyit gerektirir."
        ),
    },
]


def get_historical_market_scenarios() -> List[Dict[str, Any]]:
    """Tüm tarihsel piyasa senaryolarını döndürür."""
    return HISTORICAL_MARKET_SCENARIOS


def get_historical_scenarios_by_category(category: str) -> List[Dict[str, Any]]:
    """Belirli bir kategorideki (ör. 'Petrol Krizi', 'ABD Seçimleri', 'Savaş/Jeopolitik',
    'Kıtlık/Tarım Şoku', 'Finans Krizi', 'Pandemi/Salgın', 'Doğal Afet', 'Para Politikası',
    'Teknoloji/Kripto Balonu', 'Ticaret/Jeopolitik-Ekonomi') tüm senaryoları döndürür."""
    cat = str(category or "").strip().lower()
    return [s for s in HISTORICAL_MARKET_SCENARIOS if s.get("category", "").strip().lower() == cat]


def search_historical_scenarios(query: str) -> List[Dict[str, Any]]:
    """Başlık/olay/piyasa tepkisi metninde serbest metin arama yapar (basit
    büyük/küçük harf duyarsız alt-dize eşleşmesi)."""
    q = str(query or "").strip().lower()
    if not q:
        return []
    results = []
    for s in HISTORICAL_MARKET_SCENARIOS:
        haystack = " ".join([
            s.get("title", ""), s.get("category", ""), s.get("event", ""), s.get("market_reaction", "")
        ]).lower()
        if q in haystack:
            results.append(s)
    return results


def list_historical_scenario_categories() -> List[str]:
    """Mevcut tüm benzersiz kategori adlarını döndürür."""
    seen = []
    for s in HISTORICAL_MARKET_SCENARIOS:
        cat = s.get("category")
        if cat and cat not in seen:
            seen.append(cat)
    return seen
