# WorkFlow

<img width="1919" height="1079" alt="Zrzut ekranu 2025-10-05 113302" src="https://github.com/user-attachments/assets/457c5ff7-24c9-4baa-8c3e-2787968878da" />


## Aby uruchomić projekt z repozytorium, wykonaj poniższe kroki:

---

### 1. Sklonuj repozytorium

Otwórz terminal i wykonaj polecenie:

```bash

git clone https://github.com/AntoniTrzebuniak/Hackaton.git
cd Hackaton

```

---

### 2. Utwórz i aktywuj środowisko Conda

Upewnij się, że masz zainstalowanego Conda. Następnie utwórz środowisko:

```bash

conda env create -f environment.yml
conda activate workflow1

```

---

### 3. Zainstaluj brakujące pakiety

Jeśli po aktywacji środowiska pojawią się błędy związane z brakującymi pakietami, zainstaluj je za pomocą pip:

```bash

pip install ...

```

---

### 4. Uruchom aplikację

W katalogu głównym projektu uruchom aplikację:

```bash

python APP.py

```

#### Aplikacja wykonuje się w czasie rzyczywistym, zbiera aktywność użytkowników zarówno na stronie webowej jak aplikacji okienkowych. Program przedstawia szereg wykresów, szukając możliwość zautomatyzowania procesów które wykonujemy ale są bardzo powtarzalne, albo zauważyć czynności które zabierają nam czas który powinniśmy wykonać w inny sposób.
---

