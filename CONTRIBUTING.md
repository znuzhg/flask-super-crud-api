# Contributing to Flask Super CRUD API

🎉 Öncelikle katkıda bulunmayı düşündüğün için teşekkürler!  
Bu proje, topluluk katkılarını memnuniyetle kabul eder. Aşağıdaki rehber, projeye nasıl katkı sağlayabileceğin konusunda net bir yol haritası sunar.

---

## 🧭 Katkı Türleri

Aşağıdaki katkı türlerine açıksın:

- 🐛 **Bug fix**  
- ✨ **Yeni özellik ekleme**  
- 📚 **Dokümantasyon iyileştirmesi**  
- 🧪 **Test ekleme**  
- ⚙️ **Refactoring / iyileştirme**  
- 🛠 **DevOps / CI/CD geliştirmesi**

Her katkı değerlidir.

---

## 📝 Başlamadan Önce

1. **Issue aç** (yeni özellik veya bug için)  
2. **Tartışma başlat** (karar gerektiren değişiklikler için)  
3. Birisi üzerinde çalışıyorsa *duplicate* olmasın diye kontrol et  
4. Uygun etiketle:  
   - `bug`
   - `enhancement`
   - `documentation`
   - `help wanted`
   - `good first issue`

---

## 🛠 Geliştirme Ortamını Kurma

Bu repo aşağıdaki teknolojileri kullanır:

- Python 3.11+
- Flask
- SQLAlchemy
- Redis (optional)
- MySQL (prod) / SQLite (test)

### 1️⃣ Repo klonla

```bash
git clone https://github.com/znuzhg/flask-super-crud-api.git
cd flask-super-crud-api

2️⃣ Virtual environment oluştur

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

3️⃣ Bağımlılıkları yükle

pip install -r requirements.txt

4️⃣ .env oluştur

cp .env.example .env

🧪 Test Çalıştırma

pytest -q   # Test için SQLite veritabanı otomatik kullanılır.

📐 Kod Kalite Kuralları
Bu proje aşağıdaki araçları kullanır:

ruff (lint)

black (format)

isort (import düzeni)

mypy (type checking)

Otomatik düzeltme için:

make format
make lint
make typecheck

Commit atmadan önce tümünün geçmesi zorunludur.

🔀 Branch Kuralları
main → production branch

feature/* → yeni özellik

fix/* → bug fix

docs/* → dokümantasyon

Örnek:

feature/jwt-claims
fix/user-etag
docs/readme-update

✔️ Pull Request Kuralları
Bir PR açmadan önce:

Kod tüm testlerden geçmeli

black, ruff, isort, mypy temiz olmalı

Her yeni özellik için test yazılmalı

PR açıklaması açık ve anlaşılır olmalı

“Ne değişti?” + “Neden değişti?” mutlaka belirtilmeli

Büyük PR’lar yerine küçük, odaklı PR’lar açılmalı

📣 İletişim
Soruların için issue açabilir veya tartışma başlatabilirsin.
Geliştirici: znuzhg (Mahmut Balıkçı)
GitHub: https://github.com/znuzhg

🙌 Teşekkürler!
Katkı sağladığın her PR, bu projeyi daha iyi bir hale getirir.
Topluluk adına teşekkür ederiz! 🌟
