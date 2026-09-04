from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import date

app = Flask(__name__)

DB = "servistakibi.db"


def veritabani_olustur():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS servisler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            soyad TEXT,
            telefon TEXT,
            ilce TEXT,
            adres TEXT,
            hizmet TEXT,
            tarih TEXT,
            saat TEXT,
            ucret REAL DEFAULT 0,
            odeme TEXT DEFAULT 'Bekliyor',
            durum TEXT DEFAULT 'Bekliyor',
            aciklama TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS islemler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tip TEXT NOT NULL,
            aciklama TEXT,
            miktar REAL DEFAULT 0,
            tarih TEXT
        )
    """)

    conn.commit()
    conn.close()


def db():
    return sqlite3.connect(DB)


@app.route("/")
def ana_sayfa():

    conn = db()
    cursor = conn.cursor()

    bugun = date.today().isoformat()

    cursor.execute("""
        SELECT COALESCE(SUM(ucret), 0)
        FROM servisler
        WHERE tarih = ?
    """, (bugun,))

    gelir = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(miktar), 0)
        FROM islemler
        WHERE tip='gider' AND tarih=?
    """, (bugun,))

    gider = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM servisler
        WHERE tarih=?
    """, (bugun,))

    servis_sayisi = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(DISTINCT telefon)
        FROM servisler
        WHERE telefon IS NOT NULL AND telefon != ''
    """)

    musteri_sayisi = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            id,
            ad,
            soyad,
            telefon,
            ilce,
            hizmet,
            tarih,
            saat,
            ucret,
            odeme,
            durum
        FROM servisler
        ORDER BY id DESC
        LIMIT 10
    """)

    servisler = cursor.fetchall()

    conn.close()

    return render_template(
        "index.html",
        gelir=gelir,
        gider=gider,
        net=gelir-gider,
        servis_sayisi=servis_sayisi,
        musteri_sayisi=musteri_sayisi,
        servisler=servisler
    )


@app.route("/servisler")
def servisler():

    arama = request.args.get("q", "").strip()
    ilce = request.args.get("ilce", "").strip()
    hizmet = request.args.get("hizmet", "").strip()
    durum = request.args.get("durum", "").strip()

    conn = db()
    cursor = conn.cursor()

    sorgu = """
        SELECT
            id,
            ad,
            soyad,
            telefon,
            ilce,
            adres,
            hizmet,
            tarih,
            saat,
            ucret,
            odeme,
            durum,
            aciklama
        FROM servisler
        WHERE 1=1
    """

    parametreler = []

    if arama:
        sorgu += """
            AND (
                ad LIKE ?
                OR soyad LIKE ?
                OR telefon LIKE ?
            )
        """

        arama_degeri = f"%{arama}%"

        parametreler.extend([
            arama_degeri,
            arama_degeri,
            arama_degeri
        ])

    if ilce:
        sorgu += " AND ilce = ?"
        parametreler.append(ilce)

    if hizmet:
        sorgu += " AND hizmet = ?"
        parametreler.append(hizmet)

    if durum:
        sorgu += " AND durum = ?"
        parametreler.append(durum)

    sorgu += " ORDER BY id DESC"

    cursor.execute(
        sorgu,
        parametreler
    )

    liste = cursor.fetchall()

    cursor.execute("""
        SELECT DISTINCT ilce
        FROM servisler
        WHERE ilce IS NOT NULL
        AND ilce != ''
        ORDER BY ilce
    """)

    ilceler = [
        row[0]
        for row in cursor.fetchall()
    ]

    cursor.execute("""
        SELECT DISTINCT hizmet
        FROM servisler
        WHERE hizmet IS NOT NULL
        AND hizmet != ''
        ORDER BY hizmet
    """)

    hizmetler = [
        row[0]
        for row in cursor.fetchall()
    ]

    conn.close()

    return render_template(
        "servisler.html",
        servisler=liste,
        ilceler=ilceler,
        hizmetler=hizmetler,
        arama=arama,
        secili_ilce=ilce,
        secili_hizmet=hizmet,
        secili_durum=durum
    )


@app.route("/musteriler")
def musteriler():

    arama = request.args.get("q", "").strip()

    conn = db()
    cursor = conn.cursor()

    sorgu = """
        SELECT
            telefon,
            MAX(ad),
            MAX(soyad),
            MAX(ilce),
            COUNT(*),
            COALESCE(SUM(ucret), 0),
            MAX(id)
        FROM servisler
        WHERE telefon IS NOT NULL
        AND telefon != ''
    """

    parametreler = []

    if arama:
        sorgu += """
            AND (
                ad LIKE ?
                OR soyad LIKE ?
                OR telefon LIKE ?
            )
        """

        arama_degeri = f"%{arama}%"

        parametreler.extend([
            arama_degeri,
            arama_degeri,
            arama_degeri
        ])

    sorgu += """
        GROUP BY telefon
        ORDER BY MAX(id) DESC
    """

    cursor.execute(
        sorgu,
        parametreler
    )

    liste = cursor.fetchall()

    conn.close()

    return render_template(
        "musteriler.html",
        musteriler=liste,
        arama=arama
    )


@app.route("/raporlar")
def raporlar():

    conn = db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(ucret), 0)
        FROM servisler
    """)

    toplam_gelir = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(miktar), 0)
        FROM islemler
        WHERE tip='gider'
    """)

    toplam_gider = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM servisler
    """)

    toplam_servis = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM servisler
        WHERE durum='Tamamlandı'
    """)

    tamamlanan_servis = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM servisler
        WHERE durum='Bekliyor'
    """)

    bekleyen_servis = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "raporlar.html",
        toplam_gelir=toplam_gelir,
        toplam_gider=toplam_gider,
        net=toplam_gelir-toplam_gider,
        toplam_servis=toplam_servis,
        tamamlanan_servis=tamamlanan_servis,
        bekleyen_servis=bekleyen_servis
    )


@app.route("/servis-ekle", methods=["POST"])
def servis_ekle():

    conn = db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO servisler
        (
            ad,
            soyad,
            telefon,
            ilce,
            adres,
            hizmet,
            tarih,
            saat,
            ucret,
            odeme,
            durum,
            aciklama
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        request.form.get("ad"),
        request.form.get("soyad"),
        request.form.get("telefon"),
        request.form.get("ilce"),
        request.form.get("adres"),
        request.form.get("hizmet"),
        request.form.get("tarih"),
        request.form.get("saat"),
        request.form.get("ucret") or 0,
        request.form.get("odeme") or "Bekliyor",
        request.form.get("durum") or "Bekliyor",
        request.form.get("aciklama")
    ))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/gelir-ekle", methods=["POST"])
def gelir_ekle():

    conn = db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO islemler
        (tip, aciklama, miktar, tarih)
        VALUES ('gelir', ?, ?, ?)
    """, (
        request.form.get("aciklama"),
        request.form.get("miktar") or 0,
        request.form.get("tarih") or date.today().isoformat()
    ))

    conn.commit()
    conn.close()

    return redirect("/finans")


@app.route("/gider-ekle", methods=["POST"])
def gider_ekle():

    conn = db()
    cursor = conn.cursor()

    kategori = request.form.get("kategori")

    aciklama = request.form.get("aciklama")

    if kategori:
        aciklama = kategori + " - " + aciklama

    cursor.execute("""
        INSERT INTO islemler
        (tip, aciklama, miktar, tarih)
        VALUES ('gider', ?, ?, ?)
    """, (
        aciklama,
        request.form.get("miktar") or 0,
        request.form.get("tarih") or date.today().isoformat()
    ))

    conn.commit()
    conn.close()

    return redirect("/finans")


@app.route("/servis-sil/<int:id>", methods=["POST"])
def servis_sil(id):

    conn = db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM servisler WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/servisler")


@app.route("/servis-duzenle/<int:id>", methods=["GET", "POST"])
def servis_duzenle(id):

    conn = db()
    cursor = conn.cursor()

    if request.method == "POST":

        cursor.execute("""
            UPDATE servisler
            SET
                ad=?,
                soyad=?,
                telefon=?,
                ilce=?,
                adres=?,
                hizmet=?,
                tarih=?,
                saat=?,
                ucret=?,
                odeme=?,
                durum=?,
                aciklama=?
            WHERE id=?
        """, (
            request.form.get("ad"),
            request.form.get("soyad"),
            request.form.get("telefon"),
            request.form.get("ilce"),
            request.form.get("adres"),
            request.form.get("hizmet"),
            request.form.get("tarih"),
            request.form.get("saat"),
            request.form.get("ucret") or 0,
            request.form.get("odeme") or "Bekliyor",
            request.form.get("durum") or "Bekliyor",
            request.form.get("aciklama"),
            id
        ))

        conn.commit()
        conn.close()

        return redirect("/servisler")

    cursor.execute("""
        SELECT
            id, ad, soyad, telefon, ilce, adres,
            hizmet, tarih, saat, ucret, odeme, durum, aciklama
        FROM servisler
        WHERE id=?
    """, (id,))

    servis = cursor.fetchone()

    conn.close()

    if not servis:
        return "Servis bulunamadı", 404

    return render_template(
        "servis_duzenle.html",
        servis=servis
    )


@app.route("/musteri/<telefon>")
def musteri_detay(telefon):

    conn = db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            ad,
            soyad,
            telefon,
            ilce,
            adres,
            hizmet,
            tarih,
            saat,
            ucret,
            odeme,
            durum,
            aciklama
        FROM servisler
        WHERE telefon=?
        ORDER BY id DESC
    """, (telefon,))

    servisler = cursor.fetchall()

    conn.close()

    if not servisler:
        return "Müşteri bulunamadı", 404

    musteri = servisler[0]

    return render_template(
        "musteri_detay.html",
        musteri=musteri,
        servisler=servisler
    )


@app.route("/finans")
def finans():

    conn = db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, tip, aciklama, miktar, tarih
        FROM islemler
        ORDER BY id DESC
    """)

    islemler = cursor.fetchall()

    cursor.execute("""
        SELECT COALESCE(SUM(miktar), 0)
        FROM islemler
        WHERE tip='gelir'
    """)

    toplam_gelir = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(miktar), 0)
        FROM islemler
        WHERE tip='gider'
    """)

    toplam_gider = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "finans.html",
        islemler=islemler,
        toplam_gelir=toplam_gelir,
        toplam_gider=toplam_gider,
        net=toplam_gelir - toplam_gider
    )


@app.route("/islem-sil/<int:id>", methods=["POST"])
def islem_sil(id):

    conn = db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM islemler WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/finans")


if __name__ == "__main__":
    veritabani_olustur()
    app.run(debug=True)
