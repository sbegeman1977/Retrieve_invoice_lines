# FUNCTIONEEL ONTWERP - PIVD-7043

**Story:** Retrieve invoice lines for a specific invoice of a contact person via Public API

**Status:** Approved by Product Owner  
**Date:** 2026-04-08

---

## BUSINESSDOEL

Een externe applicatie (developer) moet via de Public API alle regelitems van een specifieke factuur van een gegeven contactpersoon kunnen ophalen. Dit stelt de contactpersoon in staat om in de portal of app de gedetailleerde uitsplitsing van hun factuur in te zien.

---

## REQUIREMENTS

### REQ001 - Invoice Lines Retrieval

API-endpoint moet alle factuurregels ophalen voor een specifieke factuur van een gegeven contactpersoon

- **Type:** Functioneel
- **Toetsbaar:** GET `/invoices/{invoiceId}/lines` met contactPersonId validatie
- **Acceptance:** Returneer alle regelitems voor geldige combinatie invoice + contactperson

### REQ002 - Invoice Line Data Structure

Factuurregels moeten minstens deze velden bevatten: artikel, hoeveelheid, eenheidsprijs, totaalprijs, BTW-percentage, beschrijving

- **Type:** Gegevenstructuur
- **Velden:**
  - `lineId`: Unieke identifier
  - `articleCode`: Artikelnummer
  - `description`: Beschrijving van artikel
  - `quantity`: Hoeveelheid
  - `unitPrice`: Prijs per eenheid
  - `taxPercentage`: BTW-percentage
  - `totalPrice`: Totaalbedrag inclusief BTW
  - `lineOrder`: Volgorde in factuur

### REQ003 - Authorization Check

Alleen factuurregels van de huidige (ingelogde) contactpersoon mogen zichtbaar zijn

- **Type:** Beveiliging
- **Rule:** AuthZ check per contactperson
- **Enforcement:** Database + application layer validation
- **Consequence:** 403 Forbidden of 404 Not Found als niet geautoriseerd

### REQ004 - Line Ordering

Factuurregels moeten gesorteerd zijn op volgorde zoals gegenereerd in de factuur

- **Type:** Gedrag
- **Sorting:** ORDER BY `line_order` ASC
- **Validation:** Order moet exact matchen met originele factuur

### REQ005 - Invoice Not Found Error

API moet HTTP 404 retourneren als factuur niet bestaat of niet toebehoort aan contactpersoon

- **Type:** Foutafhandeling
- **Status Code:** 404
- **Message:** Duidelijk, privacy-safe foutbericht
- **Content:** Geen details die exposure veroorzaken

### REQ006 - Authentication Required

API moet HTTP 401 retourneren bij ontbrekende/ongeldige authenticatie

- **Type:** Beveiliging
- **Status Code:** 401 Unauthorized
- **Check:** Bearer token validatie
- **Message:** Duidelijke authenticatie error

### REQ007 - Pagination Support

API moet maximaal 10.000 factuurregels per call kunnen retourneren (paginering voor grotere sets)

- **Type:** Performantie
- **Max Result Size:** 10.000
- **Pagination:** Limit-Offset pattern
- **Default Page Size:** 100
- **Max Page Size:** 10.000

### REQ008 - Response Time SLA

Response time moet onder 500ms liggen (P95) voor standaard factuur (<100 regels)

- **Type:** Performantie
- **SLA:** P95 < 500ms
- **Scope:** Standaard factuur (1-100 regels)
- **Measurement:** Production monitoring

---

## ACCEPTATIECRITERIA

- [ ] AC001: GET endpoint geeft alle factuurregels terug voor geldige factuur + contactperson
- [ ] AC002: Factuurregels bevatten alle verplichte velden zonder null-waarden (behalve optionele opmerkingen)
- [ ] AC003: Contactpersoon kan ALLEEN de factuurregels van zichzelf zien (geen cross-contact exposure)
- [ ] AC004: Factuurregels volgen dezelfde sortering als op de PDF/print-versie van de factuur
- [ ] AC005: 404-fout wordt gegeven met duidelijke message als factuur niet gevonden/niet toegankelijk
- [ ] AC006: API vereist geldige Bearer token (Authorization header)
- [ ] AC007: Paginering werkt correct voor facturen met >10.000 regels
- [ ] AC008: Responstijd blijft onder 500ms voor normale facturen

---

## RANDVOORWAARDEN

1. **Authenticatie:** Developer moet met geldige API-key/Bearer token communiceren
2. **Autorisatie:** Contactpersoon mag alleen eigen factuurgegevens ophalen
3. **Gegevensmodel:** Factuur- en regelinformatie bestaat al in systeem
4. **API-versie:** Deel van Public API v1
5. **Backward compatibility:** Bestaande API-endpoints niet wijzigen

---

## UITZONDERINGSSITUATIES

| Situatie | Gedrag | HTTP Status |
|----------|--------|------------|
| Factuur niet gevonden | Foutbericht + fout-code | 404 |
| Factuur hoort niet bij contactperson | Foutbericht (privacy-safe) | 403/404 |
| Geen authenticatie | Unauth foutbericht | 401 |
| Ongeldige API-key | Unauth foutbericht | 401 |
| Factuur heeft nul regelitems | Lege array retourneren | 200 |
| Overbelasting (rate limit) | Throttle bericht | 429 |

---

## FOUTSCENARIO'S

1. **Null-pointer scenario:** Factuur bestaat in database maar regelitems zijn null → moet lege array geven, niet error
2. **Concurrency:** Factuur wordt verwijderd terwijl ophalen plaatsvindt → moet 404 geven
3. **Verouderde sessie:** ContactPerson-context is verlopen → moet 401 geven
4. **Grote facturen:** >100.000 regels → moet paginering + timeout protection hebben
5. **Corrupte data:** Regelitem mist verplicht veld in database → moet gracefully handled worden

---

## PRIORITEIT

**Priority:** HIGH

**Rationale:**
- Essentieel voor contactpersoon experience (invoice transparency)
- Blokkerend voor externe app-integratie
- Deel van core Public API feature set

---

## OPEN PUNTEN (Architect)

- Paginering details: Limit-offset of cursor-based? (RESOLVED: Limit-offset)
- Filtering: Moeten factuurregels gefilterd kunnen worden?
- Sorting opties: Alleen op volgorde of ook op andere velden?
- Dataformaat: ISO 8601 voor datums? Decimal precision voor prijzen?
- Corruptie handling: Wat als regelitem in DB ontbrekende velden heeft?
- Archivering: Kunnen gearchiveerde/verwijderde facturen nog opgehaald worden?

