# GnuCash SIE4 export (i Python3)

Skapa SIE4-export (https://sie.se) från GnuCash. CSV-filer med transaktioner, resultat och balans skapas också.
NOTE: SIE4 innehåller endast transaktionerna och *inte* ingående eller utgående balanser eller någon annan info.

1. Spara GnuCash bokföring i sqlite format, t.ex. `ftgabc.sqlit`
2. Kopiera `company_header.se` till `ftgabc_header.se`
3. Öppna `ftgabc_header.se` i en text editor och uppdatera (fälten borde vara självförklarande)
4. Kör python scriptet: `python3 reports.py ftgabc.sqlite ftgabc 2022` (Kör scriptet utan argument så visas en enkel hjälp: `python3 reports.py`)

SIE-filen har testats i Bokio och kan importeras där, men några omfattande tester har inte gjorts. All feedback är välkommen, skapa en issue
här i Github om du stöter på problem.

