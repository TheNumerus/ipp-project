# Implementační dokumentace k 1. úloze do IPP 2019/2020
- Jméno a příjmení: Petr Volf
- Login: xvolfp00 

## Funkce programu
### `main`
Hlavní funkce skriptu. Existuje kvůli přehlednosti, kód by jinak byl na globální úrovni. Pokud program narazí na chybný vstup, ukončí se s určitou návratovou hodnotoou a vypíše chybu. V opačném případě vypíše xml strom zadaného programu. Na tvorbu a výpis XML stromu je použita třída `SimpleXMLElement`.
### `check_var`, `check_symb`, `check_label` a `check_type`
Funkce na parsování tokenů. Upravují xml strom.
### `print_help`
Funkce tiskne info o programu.
### `return_err`
Vypíše chybu a ukončí program. Chybové hodnoty jsou uložené v konstantách.

## Vytvořené třídy
Program obashuje dvě třídy: `Stats` a `StatsOpt`. `Stats` slouží k uložení statistik a zdrojovém souboru a jejich výpisu do souboru. `StastOpt` slouží k parsování a uložení parametrů výpisu. Instrukce nejsou zakódovany v programu jako třída, protože jazyk PHP nepodporuje tvobu enumů.
