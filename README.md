# GnuCash SIE4 export tool

SIE4 is the standard swedish financial file format used for all financial company data exchange (tax, company declarations, ...) .
See https://sie.se/in-english/ for more info.
There you can also find a PDF with the SIE4 format specifications.

This tool creates an SIE4 export file from existing GnuCash company data to help you with reporting.

With this tool the author successfully sold an existing Swedish compay (Aktiebolag) and transferred the company books to the new owner.

For this case GnuCash version 4.13 was used (check out more recent versions for compatibility).

## Install & Quickstart

1. Give your company a short abbreviation

Here we assume `aa` is used.

2. Create a header file for your company

The file name is `aa_header.se` if company abbreviation is `aa`.

See `company_header.se` for a base template (copy it to your file name and adapt it).

3. Export GnuCash data in sqlite format

- Open your company data in GnuCash
- Go to `File` -> `Save As...`
- Select `sqlite` as `Data Format` in the opened dialogue box
- Choose destination file name (preferably already in the folder of this tool)
- Click `Save As`

4. Run python SIE4 tool

- Choose the reporting year (here: `2023`)

```bash
$ python main.py aa.gnucash aa 2023
```

5. Use the generated SIE4 export file according to your needs

Created SIE4 file is named `aa_2024.se` .
More intermediate files are created to help you (e.g. moms, balans, resultat) .


# This was originally cloned from a now non-existing GitHub Repo

https://github.com/colmsjo/GnuCash-SIE4-export.git

So unfortunately I can't fork it to give the original author credits.
Please contact me if you are the original author to improve the situation (and many thanks already for creating the initial tool skeleton).


# Original README below (in swedish):

## GnuCash SIE4 export (i Python3)

Skapa SIE4-export (https://sie.se) från GnuCash. CSV-filer med transaktioner, resultat, balans och MOMS-redovisning skapas också.
Verifikationen med Nr 1 används för att sätta ingående balanser.

1. Spara GnuCash bokföring i sqlite format, t.ex. `ftgabc.gnucash`
2. Kopiera `company_header.se` till `ftgabc_header.se`
3. Öppna `ftgabc_header.se` i en text editor och uppdatera (fälten borde vara självförklarande)
4. Kör python scriptet: `python3 reports.py ftgabc.gnucash ftgabc 2022` (kör scriptet utan argument så visas en enkel hjälp: `python3 main.py`)

SIE-filen har testats i Bokio och kan importeras där men några omfattande tester har inte gjorts. All feedback är välkommen, skapa en issue
här i Github om du stöter på problem eller har frågor.
