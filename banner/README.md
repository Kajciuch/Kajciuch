# banner

Baner z profilowego README (`pliki/hero-panda.gif`) jest generowany, nie
rysowany ręcznie. Licznik technologii to prawdziwe liczby z API GitHuba —
bajty rozpoznane przez linguist we wszystkich publicznych repozytoriach.

```
render.sh          # przelicza statystyki i składa gif
fetch_stats.py     # bajty na język + liczba repozytoriów -> stats.json
make_banner.py     # podpis i panel jako warstwa nakładana na każdą klatkę
source.mp4         # przycięty materiał źródłowy (6 s, 1010x342)
```

Odświeżenie ręczne:

```bash
./banner/render.sh
```

Poza tym `.github/workflows/banner.yml` robi to samo w każdy poniedziałek i
commituje gif, jeśli liczby się zmieniły.

Panel z licznikiem jest domalowany do płótna gifa, a nie wstawiony jako drugi
obrazek pod banerem — GitHub wstawia między dwa obrazki odstęp i szew byłby
widoczny.
