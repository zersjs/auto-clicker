# Pro Otomatik Tıklayıcı

Pro Otomatik Tıklayıcı, gelişmiş özelliklere sahip bir otomatik fare ve klavye kontrol programıdır. Oyunlarda, form doldurma işlemlerinde veya tekrarlayan görevlerde kullanılabilecek güçlü bir araçtır.

## Özellikler

- **Otomatik Tıklama**: Belirli aralıklarla sol, sağ veya orta fare tuşuyla tıklama
- **Çoklu Konum Tıklama**: Birden fazla noktada sırayla tıklama
- **Makro Kaydetme ve Oynatma**: Fare ve klavye hareketlerinizi kaydedip istediğiniz zaman tekrar oynatma
- **Ekran Renk Algılama**: Ekranda belirli bir renk tespit edildiğinde otomatik tıklama
- **Anti-AFK Sistemi**: Oyunlarda AFK (Away From Keyboard) kalmamak için rastgele tuşlara basma
- **Hızlı Kısayollar**: Programı klavye kısayollarıyla kontrol etme
- **Zamanlı Durdurma**: Belirli bir süre sonra otomatik durdurma

## Kullanım

### Otomatik Tıklayıcı

1. **Tıklama Sekmesi**: Tıklama türünü, hızını ve sayısını ayarlayın
2. **Başlat/Durdur**: F6 tuşu ile başlatın, F7 tuşu ile durdurun (değiştirilebilir)
3. **Ayarlar**: İstenilen tıklama sayısını veya sonsuz tıklama seçeneğini belirleyin

### Çoklu Konum Tıklama

1. **Konumlar Sekmesi**: "Konumları Kaydet" tuşuna basarak istediğiniz yerlere tıklayın
2. **Kaydetmeyi Durdur**: İşlem tamamlandığında "Kaydetmeyi Durdur" tuşuna basın
3. **Başlat**: Ana sekmeden "Başlat" tuşuna basarak sırayla tıklamaları başlatın

### Makro Kaydedici

1. **Makro Sekmesi**: "Makro Kaydet" tuşuna basarak kaydı başlatın
2. **İşlemleri Yapın**: Kaydetmek istediğiniz fare ve klavye hareketlerini gerçekleştirin
3. **Durdur**: "Kaydetmeyi Durdur" tuşuna basarak kaydı tamamlayın
4. **Makroyu Kaydet**: Makroya isim vererek kaydedin
5. **Oynat**: Kaydedilen makroyu "Oynat" tuşuna basarak çalıştırın

### Ekran Renk Algılama

1. **Ekran Algılama Sekmesi**: "Bölge Seç" tuşuna basarak taranacak ekran bölgesini belirleyin
2. **Renk Seç**: "Renk Seç" tuşuna basıp algılanacak rengi seçin
3. **Başlat**: "Taramayı Başlat" tuşuna basarak renk algılamayı başlatın

## Kurulum

### Hazır EXE Kullanımı
1. En yeni sürümü indirin ve çalıştırın
   - Exe dosyası tek başına çalışır, kurulum gerektirmez
   - Windows Defender uyarı verebilir, "Daha fazla bilgi" > "Yine de çalıştır" seçeneğini kullanın

### Python İle Kullanım
Geliştiriciler için Python kodunu çalıştırma:
```
pip install -r requirements.txt
python main.py
```

### EXE Dosyası Oluşturma
Kendi exe dosyanızı oluşturmak için:

1. Gerekli paketleri yükleyin:
   ```
   pip install pyinstaller pillow customtkinter pynput
   ```

2. İkon indirin (veya kendi ikonunuzu kullanın):
   ```
   curl -o icon.png https://cdn.iconscout.com/icon/premium/png-256-thumb/mouse-click-1830550-1554513.png
   ```

3. Tek dosyalı EXE oluşturun:
   ```
   pyinstaller --onefile --windowed --icon=icon.png --name="Pro Otomatik Tiklayici" main.py
   ```

4. **İLERİ DÜZEY**: Daha hızlı çalışan ve daha gizli bir exe için aşağıdaki komut satırını kullanın:
   ```
   pyinstaller --onefile --windowed --icon=icon.png --noconsole --clean --add-data "icon.png;." --hidden-import PIL._tkinter_finder --name="Pro Otomatik Tiklayici" main.py
   ```

5. Oluşturulan exe dosyası `dist` klasöründe bulunacaktır.

## İstek ve Öneriler

Yeni özellikler veya geliştirmeler için iletişime geçebilirsiniz.

---

## Telif Hakkı ve Lisans

**© 2024 Created by ZERS. Tüm Hakları Saklıdır.**

Bu yazılım, ZERS'e aittir ve telif hakları ile korunmaktadır. İzinsiz kopyalanması, dağıtılması veya değiştirilmesi yasaktır.

---

**Not**: Bu program eğitim ve kişisel kullanım amaçlıdır. Kötüye kullanımdan kullanıcı sorumludur. 
