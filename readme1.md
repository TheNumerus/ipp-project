# Implementační dokumentace k 1. úloze do IPP 2019/2020
- Jméno a příjmení: Petr Volf
- Login: xvolfp00 

## Funkce programu
### `main`
Hlavní funkce skriptu. Existuje kvůli přehlednosti, kód by jinak byl na globální úrovni. Jako první zkontroluje zadané argumenty přes příkazovou řádku. Následně zadaný vstupní program po řádcích. V každém řádku se hledá komentář, který když je nalezen, se odstřihne. Poté se řádky zbaví bílých znaků na začátku a konci. Řádky se rozdělí na sekvence tokeny oddělené bílými znaky. Následně se podle prvního tokenu určí o jakou instrukci jde. Ostatní slova v řádku poté projdou kontrolou zápisu v určitém formátu. 

Pokud program narazí na chybný nebo neočekávaný vstup, ukončí se s určitou návratovou hodnotou a vypíše chybu na standartní chybový výstup. V opačném případě vypíše XML strom zadaného programu. Na tvorbu a výpis XML stromu je použita třída `SimpleXMLElement`.

### `check_var`, `check_symb`, `check_label` a `check_type`
Funkce na analyzování tokenů. Správný výraz je kontrolován pomocí regulárních výrazů. Upravují XML strom.
### `print_help`
Funkce tiskne info o programu.
### `return_err`
Vypíše chybu a ukončí program. Chybové hodnoty jsou uložené v konstantách, protože jazyk PHP nepodporuje tvorbu výčtových typů.

## Vytvořené třídy
Program obsahuje dvě třídy: `Stats` a `StatsOpt`. `Stats` slouží k uložení statistik a zdrojovém souboru a jejich výpisu do souboru. `StastOpt` slouží k analýze a uložení parametrů výpisu. 

Statistiky o programu jsou sbírány i v případě že není zadán výstupní soubor, v tom případě se pouze nevypíší. 