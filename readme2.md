
# Implementační dokumentace k 2. úloze do IPP 2019/2020
- Jméno a příjmení: Petr Volf
- Login: xvolfp00

## interpret.py

### Typický běh interpretu

Hlavní funkce interpretu je funkce `main`.  Jako první se vyhodnotí argumenty funkcí `parse_args`. Tato funkce nastaví vstupy na kód a na uživatelský vstup a vyhodnotí statistické argumenty.  Následně se přečte vstupní XML soubor. Ten je zkontrolován ve funkci `check_xml`. Pokud je XML strom validní, předá se třídě `Program` a je následně interpretován.

### `Program`

Jádrem interpretu je třída `Program`. Tato třída se stará o vykonávání zadaných instrukcí. Implementuje iterátor, takže průchod programem je možný pomocí konstrukce `for`.  V každém kroku se tak načte instrukce, najde se odpovídající metoda a instrukce se vykoná. V konstruktoru třídy je slovník s metodami. Každí instrukce má svoji metodu. Slovník slouží k tomu, aby nemusela existovat zbytečně dlouhá a složitá konstrukce `if elif ... else` se všemi instrukcemi.

Kvůli odstranění některých případů duplicity jsou instrukce, které jsou si podobné (`ADD`, `SUB`,  atd.) implementovány v jedné metodě. Rozlišují se pomocí výčtových typů předaných parametrem do společné metody. Protože slovník s metodami má jako hodnoty ukazatele na metody a v případě předání parametrů se metody volají, jsou u těchto metod použity anonymní funkce které volají metody s parametry. 

Třída `Program` obsahuje také několik pomocných metod. Tyto metody pracují se zásobníkem a extrahují proměnné z XML stromu.  Instrukce a jejich argumenty jsou uloženy v paměti po celou dobu běhu jako XML strom.

#### Rámce

Rámce jsou uloženy jako slovníky.  Zásobník lokálních rámců je implementován jako list. Globální rámec se inicializuje v konstruktoru. 

### `Var`, `VarType`

Proměnné jsou v interpretu uloženy jako instance třídy `Var`. Tato třída si ukládá zvlášť hodnotu a typ.  Typ proměnných je uložen jako výčtový typ `VarType`. Díky tomu je možné určit jestli už proměnná byla definována.


### Chyby

Chybové hodnoty jsou uloženy jako výčtový typ `Error`. Tato třída obsahuje pomocnou metodu `exit`, která vypíše chybovou hlášku a ukončí program s daným chybovým kódem. Tato třída je dostupná odkudkoliv.

### Ostatní

Interpret obsahuje pomocnou funkci `unescape_string`, která nahradí zakódované znaky za jejich ekvivalent v `UTF-8`. Funkce `eprint` je podobná vestavěné funkci `print`, jen vypisuje na standardní chybový výstup. bez dodatečného parametru.

### Rozšíření `STACK`

Zásobník byl v interpretu i před rozšířením, akorát jsou přidány varianty existujících instrukcí na práci s ním. Tyto instrukce se liší od svých ne-zásobníkových variant pouze způsobem získání parametrů. Díky tomu je možné znovu použít většinu kódu.

### Rozšíření `FLOAT`

Byla přidána varianta do typu `VarType` a podpora v instrukcích na výstup, výstup a aritmetiku. Dále se přidaly instrukce na konverzi a podpora v kontrole XML.

### Rozšíření `STATI`

Díky tomu, že je třída `Program` iterátor, stačilo přidat sběr statistik do metody `__next__`. Statistiky se vypisují při konci interpretace a při instrukci `EXIT`. Statistiky jsou uloženy v paměti jako instance třídy `Stats`. 

## test.php

Hlavní funkce programu je `main`. Zde se volají funkce na vyhodnocení argumentů, vyhledání testů, spuštění testů a výpis HTML. 

Vyhodnocení argumentů je vyřešeno pomocí iterace konstrukcí `foreach`. Každý argument se kontroluje na správný tvar, existenci cesty k souboru/složce a exkluzivitu s jinými argumenty. Výstupem kontroly argumentů je instance třídy `TestOpts`, která obsahuje veškeré informace o testovacím prostředí. 

Testy se poté vyhledají podle nastavení.  Jeden po druhém se spustí a jejich výsledky se ukládají do pole pro pozdější využití. Kvůli porovnávání výstupů se vytváří nový soubor se jménem `jmeno_testu.temp` kde temp nahrazuje příponu `src`. Tento soubor je poté smazán.

Řetězce s HTML hlavičkou, styly a další jsou uloženy v modulu `html_strings`. HTML stránka obsahuje tabulku s výsledky testů, procentem úspěšných testů a možností filtrovat testy. Filtrace je řešena pomocí `JavaScriptu`. 

### Kompatibilita s Merlinem

Na mé instalaci linuxu jsou php a python dostupné jako příkazy `php` a `python`. Aby testovací skript fungoval i na merlinovi, kontroluje se, kde skript běží. Pokud skript nenajde soubor `env` ve stejné složce jako je skript, tak nahradí příkazy na spuštění za `php7.4` a `python3.8`.

### Chyby

Modul s chybovými hodnotami a hlášeními je sdílený s `parse.php` z první části. Byly přidány nové chybové stavy a jsou nyní uloženy jako konstanty ve třídě `Err`. Díky tomu neznečisťují jmenný prostor.

### Rozšíření `FILES`

Toto rozšíření přidává jiný způsob vyhledávání testů. Vyhledané testy je možné filtrovat pomocí regulárního výrazu.