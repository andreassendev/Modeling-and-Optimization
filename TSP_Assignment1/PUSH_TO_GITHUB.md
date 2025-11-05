# Push til GitHub

Følg disse stegene for å pushe prosjektet til GitHub:

## 1. Lag repository på GitHub (hvis ikke allerede opprettet)

Gå til: https://github.com/andreassendev/Modeling-and-Optimization

Hvis repositoriet er tomt, kan du følge instruksjonene nedenfor.

## 2. Legg til remote og push

```bash
cd MA2-INF170

# Legg til remote repository
git remote add origin https://github.com/andreassendev/Modeling-and-Optimization.git

# Push til GitHub
git branch -M main
git push -u origin main
```

## Alternativt: Hvis du vil pushe til en subdirectory

Hvis du vil pushe dette til en subdirectory i repositoriet:

```bash
# Flytt filene til en subdirectory først (hvis nødvendig)
# Eller bruk git subtree eller sparse checkout

git remote add origin https://github.com/andreassendev/Modeling-and-Optimization.git
git push -u origin main
```

## Notat

Hvis repositoriet allerede har innhold, må du kanskje:
1. Først pull eksisterende innhold: `git pull origin main --allow-unrelated-histories`
2. Deretter push: `git push -u origin main`

Eller hvis du vil pushe til en spesifikk branch:
```bash
git push -u origin main:Q1-TSP
```

