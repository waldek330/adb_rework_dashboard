from flask import Flask, render_template
import pandas as pd
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)

# Konfiguracja bazy danych PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:C3T0r2019@172.16.4.90/ADB_reworks'
db = SQLAlchemy(app)

# Model danych dla tabeli st6840_vmi_cosmetic_data
class VmiCosmeticData(db.Model):
    __tablename__ = 'st6840_vmi_cosmetic_data'
    serial_number = db.Column(db.String(255), primary_key=True)
    top_cover = db.Column(db.String(255))
    karton = db.Column(db.String(255))
    rj_11 = db.Column(db.String(255))
    rj_45 = db.Column(db.String(255))
    psu = db.Column(db.String(255))
    power_cord = db.Column(db.String(255))
    ulotka = db.Column(db.String(255))
    bottom_cover = db.Column(db.String(255))
    stand = db.Column(db.String(255))
    etykieta = db.Column(db.String(255))
    gift_box_etykieta = db.Column(db.String(255))

# Model danych dla tabeli st6840_test_data
class TestData(db.Model):
    __tablename__ = 'st6840_test_data'
    serial = db.Column(db.String(255), primary_key=True)
    mac = db.Column(db.String(255))
    software = db.Column(db.String(255))
    powerup = db.Column(db.String(255))
    lan = db.Column(db.String(255))
    wifi = db.Column(db.String(255))
    dsl = db.Column(db.String(255))
    telephone = db.Column(db.String(255))
    leds = db.Column(db.String(255))
    usb = db.Column(db.String(255))
    buttons = db.Column(db.String(255))
    softwaretest = db.Column(db.String(255))
    factorymodereset = db.Column(db.String(255))
    sfp = db.Column(db.String(255))
    factoryreset = db.Column(db.String(255))

@app.route('/')
def index():
    # Pobierz dane z bazy danych

    query_vmi_cosmetic = text("""
    WITH LatestVmiCosmetic AS (
        SELECT
            "Serial Number" AS Serial_Number,
            CASE
                WHEN COUNT(*) = 0 THEN 'Brak testu'
                WHEN COUNT(*) = COUNT(CASE WHEN "VMI urzadzenia [Top Cover]" = 'PASS' THEN 1 END)
                    AND COUNT(*) = COUNT(CASE WHEN "VMI GIFT-BOX [Karton]" = 'PASS' THEN 1 END)
                    AND COUNT(*) = COUNT(CASE WHEN "VMI Akcesoria [RJ-11]" = 'PASS' THEN 1 END)
                    AND COUNT(*) = COUNT(CASE WHEN "VMI Akcesoria [RJ-45]" = 'PASS' THEN 1 END)
                    AND COUNT(*) = COUNT(CASE WHEN "VMI Akcesoria [PSU]" = 'PASS' THEN 1 END)
                    AND COUNT(*) = COUNT(CASE WHEN "VMI Akcesoria [Power cord]" = 'PASS' THEN 1 END)
                    AND COUNT(*) = COUNT(CASE WHEN "VMI Akcesoria [Ulotka]" = 'PASS' THEN 1 END)
                    AND COUNT(*) = COUNT(CASE WHEN "VMI urzadzenia [Bottom Cover]" = 'PASS' THEN 1 END)
                    AND COUNT(*) = COUNT(CASE WHEN "VMI urzadzenia [Stand]" = 'PASS' THEN 1 END)
                    AND COUNT(*) = COUNT(CASE WHEN "VMI urzadzenia [Etykieta]" = 'PASS' THEN 1 END)
                    AND COUNT(*) = COUNT(CASE WHEN "VMI GIFT-BOX [Etykieta]" = 'PASS' THEN 1 END)
                THEN 'PASS'
                ELSE 'FAIL'
            END AS "VMICosmetic"
        FROM public.st6840_vmi_cosmetic_data
        WHERE "Serial Number" IS NOT NULL
        GROUP BY "Serial Number"
    )
    SELECT Serial_Number, "VMICosmetic" AS "VMI/Cosmetic"
    FROM LatestVmiCosmetic;
    """)

    query_test_data = text("""
WITH LatestTestData AS (
    SELECT DISTINCT ON ("serial")
        "serial" AS Serial_Number,
        CASE
            WHEN "failinfo" IS NOT NULL AND TRIM("failinfo") <> '' THEN 'FAIL'
            ELSE 'PASS'
        END AS "Wynik testu"
    FROM public.st6840_test_data
    WHERE "failinfo" IS NOT NULL 
    ORDER BY "serial", "time_stamp" DESC
)

SELECT Serial_Number, "Wynik testu"
FROM LatestTestData;

    """)

    # Rozpocznij sesję i wykonaj zapytania
    session = db.session()
    result_vmi_cosmetic = session.execute(query_vmi_cosmetic)
    data_vmi_cosmetic = result_vmi_cosmetic.fetchall()

    result_test_data = session.execute(query_test_data)
    data_test_data = result_test_data.fetchall()

    # Przekształć dane na DataFrame
    combined_df_vmi_cosmetic = pd.DataFrame(data_vmi_cosmetic, columns=['Serial_Number', 'VMI/Cosmetic'])
    combined_df_test_data = pd.DataFrame(data_test_data, columns=['Serial_Number', 'Wynik testu'])

    # Analizuj dane i generuj dane do wykresów
    vmi_cosmetic_counts = combined_df_vmi_cosmetic['VMI/Cosmetic'].value_counts()
    test_result_counts = combined_df_test_data['Wynik testu'].value_counts()

    # Suma serial_number dla kategorii "VMI/Cosmetic" i "Wynik testu"
    vmi_cosmetic_total_qty = vmi_cosmetic_counts.sum()
    test_result_total_qty = test_result_counts.sum()

    # Procenty dla VMI/Cosmetic
    vmi_cosmetic_percent = (vmi_cosmetic_counts / vmi_cosmetic_total_qty) * 100

    # Procenty dla Wyniku testu
    test_result_percent = (test_result_counts / test_result_total_qty) * 100

    # Generuj dashboard
    session.close()
    return render_template('dashboard.html', vmi_cosmetic_counts=vmi_cosmetic_counts.to_dict(), test_result_counts=test_result_counts.to_dict(), vmi_cosmetic_total_qty=vmi_cosmetic_total_qty, test_result_total_qty=test_result_total_qty, vmi_cosmetic_percent=vmi_cosmetic_percent.to_dict(), test_result_percent=test_result_percent.to_dict())

if __name__ == '__main__':
    app.run(debug=True)
