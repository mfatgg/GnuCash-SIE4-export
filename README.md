# GnuCash SIE4 export (i Python3)

Skapa SIE4-export (https://sie.se) från GnuCash. CSV-filer med transaktioner, resultat, balans och MOMS-redovisning skapas också.
Verifikationen med Nr 1 används för att sätta ingående balanser.

1. Spara GnuCash bokföring i sqlite format, t.ex. `ftgabc.gnucash`
2. Kopiera `company_header.se` till `ftgabc_header.se`
3. Öppna `ftgabc_header.se` i en text editor och uppdatera (fälten borde vara självförklarande)
4. Kör python scriptet: `python3 reports.py ftgabc.gnucash ftgabc 2022` (kör scriptet utan argument så visas en enkel hjälp: `python3 main.py`)

SIE-filen har testats i Bokio och kan importeras där men några omfattande tester har inte gjorts. All feedback är välkommen, skapa en issue
här i Github om du stöter på problem eller har frågor.
